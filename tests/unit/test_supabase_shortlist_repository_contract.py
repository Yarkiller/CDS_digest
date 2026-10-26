"""Contract tests for SupabaseShortlistRepository (offline stubs — no network).

ADMIN-02 / ADMIN-07 / D-81 / D-87 — get_current_batch, set_decision, claim_sent.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import pytest

from backend.domain.errors import AlreadySentError, PersistenceError, ShortlistNotFoundError


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._payload: Any = None
        self._filters: list[tuple[str, Any]] = []
        self._is_null: list[str] = []
        self._orders: list[tuple[str, bool]] = []
        self._limit: int | None = None
        self._select_cols: str = "*"

    def select(self, cols: str = "*") -> "_FakeQuery":
        self._select_cols = cols
        if self._op is None:
            self._op = "select"
        return self

    def insert(self, payload: Any) -> "_FakeQuery":
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "update"
        self._payload = dict(payload)
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        return self

    def is_(self, column: str, value: str) -> "_FakeQuery":
        if value == "null":
            self._is_null.append(column)
        return self

    def order(self, column: str, *, desc: bool = False) -> "_FakeQuery":
        self._orders.append((column, desc))
        return self

    def limit(self, n: int) -> "_FakeQuery":
        self._limit = n
        return self

    def execute(self) -> _FakeExecuteResult:
        assert self._op is not None
        if self._table.fail_next:
            self._table.fail_next = False
            raise RuntimeError("simulated supabase failure")

        if self._op == "select":
            matched = list(self._table.rows)
            for column, value in self._filters:
                matched = [r for r in matched if r.get(column) == value]
            for column in self._is_null:
                matched = [r for r in matched if r.get(column) is None]
            for column, desc in reversed(self._orders):
                matched.sort(key=lambda r, c=column: r.get(c) or "", reverse=desc)
            if self._limit is not None:
                matched = matched[: self._limit]
            if "materials" in self._select_cols and self._table.name == "digest_shortlist_items":
                materials = self._table.client.tables["materials"].rows
                enriched = []
                for row in matched:
                    mat = next((m for m in materials if m["id"] == row["material_id"]), None)
                    enriched.append({**row, "materials": mat})
                return _FakeExecuteResult(enriched)
            return _FakeExecuteResult(matched)

        if self._op == "update":
            assert isinstance(self._payload, dict)
            matched = list(self._table.rows)
            for column, value in self._filters:
                matched = [r for r in matched if r.get(column) == value]
            for column in self._is_null:
                matched = [r for r in matched if r.get(column) is None]
            for row in matched:
                row.update(self._payload)
            return _FakeExecuteResult([dict(r) for r in matched])

        if self._op == "insert":
            rows_in = self._payload if isinstance(self._payload, list) else [self._payload]
            out: list[dict[str, Any]] = []
            for payload in rows_in:
                row = dict(payload)
                if "id" not in row and self._table.name in (
                    "digest_shortlist_batches",
                    "digest_issues",
                ):
                    next_id = max((int(r.get("id") or 0) for r in self._table.rows), default=0) + 1
                    row["id"] = next_id
                self._table.rows.append(row)
                out.append(row)
            return _FakeExecuteResult(out)

        raise AssertionError(f"unknown op {self._op}")


class _FakeTable:
    def __init__(self, name: str, client: "FakeSupabaseClient") -> None:
        self.name = name
        self.client = client
        self.rows: list[dict[str, Any]] = []
        self.fail_next = False

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "digest_shortlist_batches": _FakeTable("digest_shortlist_batches", self),
            "digest_shortlist_items": _FakeTable("digest_shortlist_items", self),
            "materials": _FakeTable("materials", self),
            "digest_issues": _FakeTable("digest_issues", self),
            "digest_issue_items": _FakeTable("digest_issue_items", self),
        }

    def table(self, name: str) -> _FakeQuery:
        return self.tables[name].query()


def _seed_shortlist(client: FakeSupabaseClient) -> None:
    client.tables["materials"].rows = [
        {"id": 10, "slug": "rag-systems", "title": "RAG Systems", "status": "ready"},
        {"id": 11, "slug": "phase5-admin-draft", "title": "Draft Candidate", "status": "draft"},
    ]
    client.tables["digest_shortlist_batches"].rows = [
        {
            "id": 42,
            "week_start": "2026-09-15",
            "created_at": "2026-09-15T08:00:00+00:00",
            "sent_at": None,
            "delivery_status": None,
            "recipient_count": None,
            "published_issue_id": None,
            "issue_url": None,
        },
        {
            "id": 41,
            "week_start": "2026-09-08",
            "created_at": "2026-09-08T08:00:00+00:00",
            "sent_at": "2026-09-10T12:00:00+00:00",
            "delivery_status": "stubbed",
            "recipient_count": 0,
            "published_issue_id": 1,
            "issue_url": "/issues/1",
        },
    ]
    client.tables["digest_shortlist_items"].rows = [
        {
            "batch_id": 42,
            "material_id": 10,
            "rank": 1,
            "score": 0.92,
            "score_factors": {"релевантность": 0.9, "качество": 0.8},
            "decision": "pending",
            "decided_by": None,
            "decided_at": None,
        },
        {
            "batch_id": 42,
            "material_id": 11,
            "rank": 2,
            "score": 0.4,
            "score_factors": {},
            "decision": "pending",
            "decided_by": None,
            "decided_at": None,
        },
    ]


def test_get_current_batch_returns_latest_unsent_with_material_status() -> None:
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    repo = SupabaseShortlistRepository(client)

    batch = repo.get_current_batch()
    assert batch is not None
    assert batch.id == 42
    assert batch.week_start == date(2026, 9, 15)
    assert batch.sent_at is None
    assert len(batch.items) == 2
    by_id = {item.material_id: item for item in batch.items}
    assert by_id[10].material_status == "ready"
    assert by_id[10].title == "RAG Systems"
    assert by_id[11].material_status == "draft"


def test_get_current_batch_maps_non_numeric_reading_minutes_to_persistence_error() -> None:
    """W-5: a malformed joined `reading_minutes` must map to PersistenceError (contract),
    never escape as an unhandled ValueError -> HTTP 500."""
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    # Corrupt material 10's joined reading_minutes with a non-numeric value.
    client.tables["materials"].rows[0]["reading_minutes"] = "not-a-number"
    repo = SupabaseShortlistRepository(client)

    with pytest.raises(PersistenceError):
        repo.get_current_batch()


def test_get_current_batch_accepts_numeric_string_reading_minutes() -> None:
    """W-5 guard: a numeric string is valid input (PostgREST can return numeric-as-text)."""
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    client.tables["materials"].rows[0]["reading_minutes"] = "7"
    repo = SupabaseShortlistRepository(client)

    batch = repo.get_current_batch()
    assert batch is not None
    by_id = {item.material_id: item for item in batch.items}
    assert by_id[10].reading_minutes == 7


def test_get_current_batch_empty_when_no_unsent() -> None:
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    client.tables["digest_shortlist_batches"].rows = [
        {
            "id": 1,
            "week_start": "2026-09-01",
            "created_at": "2026-09-01T00:00:00+00:00",
            "sent_at": "2026-09-02T00:00:00+00:00",
        }
    ]
    repo = SupabaseShortlistRepository(client)
    assert repo.get_current_batch() is None


def test_set_decision_persists_and_returns_updated_batch() -> None:
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    repo = SupabaseShortlistRepository(client)
    decided_at = datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc)

    batch = repo.set_decision(
        batch_id=42,
        material_id=10,
        decision="approved",
        actor_user_id="11111111-1111-1111-1111-111111111111",
        decided_at=decided_at,
    )
    assert batch.items[0].decision == "approved" or any(
        i.material_id == 10 and i.decision == "approved" for i in batch.items
    )
    stored = next(
        r
        for r in client.tables["digest_shortlist_items"].rows
        if r["batch_id"] == 42 and r["material_id"] == 10
    )
    assert stored["decision"] == "approved"
    assert stored["decided_by"] == "11111111-1111-1111-1111-111111111111"


def test_set_decision_missing_material_raises() -> None:
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    repo = SupabaseShortlistRepository(client)
    with pytest.raises(ShortlistNotFoundError):
        repo.set_decision(
            batch_id=42,
            material_id=999,
            decision="approved",
            actor_user_id="11111111-1111-1111-1111-111111111111",
            decided_at=datetime.now(timezone.utc),
        )


def test_claim_sent_atomic_zero_rows_raises_already_sent() -> None:
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    # Pretend already claimed
    client.tables["digest_shortlist_batches"].rows[0]["sent_at"] = "2026-09-16T12:00:00+00:00"
    repo = SupabaseShortlistRepository(client)

    with pytest.raises(AlreadySentError):
        repo.claim_sent(
            batch_id=42,
            sent_at=datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc),
        )


def test_claim_sent_sets_sent_at_when_null() -> None:
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    repo = SupabaseShortlistRepository(client)
    sent_at = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)

    claimed = repo.claim_sent(batch_id=42, sent_at=sent_at)
    assert claimed.sent_at is not None
    assert client.tables["digest_shortlist_batches"].rows[0]["sent_at"] is not None


def test_get_latest_batch_returns_latest_regardless_of_sent_at() -> None:
    """WR-03 / D-89: get_latest_batch ignores the sent_at filter so send_digest can raise
    AlreadySentError when the most recent batch was already sent (sequential repeat send)."""
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    # Mark the latest (week 09-15) batch as sent — get_current_batch would now return None.
    client.tables["digest_shortlist_batches"].rows[0]["sent_at"] = "2026-09-16T12:00:00+00:00"
    repo = SupabaseShortlistRepository(client)

    assert repo.get_current_batch() is None
    latest = repo.get_latest_batch()
    assert latest is not None
    assert latest.id == 42
    assert latest.sent_at is not None


def test_release_claim_clears_sent_at_for_retry() -> None:
    """CR-01 compensation: release_claim resets sent_at to NULL so a failed publish can retry."""
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    client.tables["digest_shortlist_batches"].rows[0]["sent_at"] = "2026-09-16T12:00:00+00:00"
    repo = SupabaseShortlistRepository(client)

    repo.release_claim(batch_id=42)

    assert client.tables["digest_shortlist_batches"].rows[0]["sent_at"] is None
    # Batch is claimable again by get_current_batch (sent_at IS NULL).
    batch = repo.get_current_batch()
    assert batch is not None
    assert batch.id == 42


def test_release_claim_maps_sdk_failure_to_persistence_error() -> None:
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    client.tables["digest_shortlist_batches"].fail_next = True
    repo = SupabaseShortlistRepository(client)

    with pytest.raises(PersistenceError):
        repo.release_claim(batch_id=42)


def test_sdk_failure_maps_to_persistence_error() -> None:
    from supabase_integration.shortlist_repository import SupabaseShortlistRepository

    client = FakeSupabaseClient()
    _seed_shortlist(client)
    client.tables["digest_shortlist_batches"].fail_next = True
    repo = SupabaseShortlistRepository(client)

    with pytest.raises(PersistenceError):
        repo.get_current_batch()


def test_issue_publish_inserts_issue_and_items() -> None:
    from backend.domain.issue import IssueItem
    from supabase_integration.issue_repository import SupabaseIssueRepository

    client = FakeSupabaseClient()
    client.tables["materials"].rows = [
        {"id": 10, "slug": "rag-systems", "title": "RAG", "status": "ready", "format": "статья", "reading_minutes": 8, "dek": None},
    ]
    client.tables["digest_issues"].rows = [
        {"id": 1, "number": 3, "period_label": "2026-03", "title": "Old", "published_at": "2026-03-01T00:00:00+00:00"},
    ]
    repo = SupabaseIssueRepository(client)
    published = repo.publish(
        period_label="2026-09-15",
        title="Digest CDS — 2026-09-15",
        editor="Редакция Digest CDS",
        published_at=datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc),
        items=(
            IssueItem(
                slug="material-10",
                title="RAG",
                position=1,
                format="article",
                reading_minutes=5,
            ),
        ),
    )
    assert published.number == 4
    assert len(client.tables["digest_issue_items"].rows) == 1
    assert client.tables["digest_issue_items"].rows[0]["material_id"] == 10
