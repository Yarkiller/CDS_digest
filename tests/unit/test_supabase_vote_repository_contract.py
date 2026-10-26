"""Contract tests for SupabaseVoteRepository (offline stubs — no network)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from backend.domain.errors import PersistenceError, VoteConflictError


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._payload: dict[str, Any] | None = None
        self._filters: list[tuple[str, Any]] = []
        self._select_cols: str = "*"
        self._on_conflict: str | None = None

    def insert(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "insert"
        self._payload = dict(payload)
        return self

    def upsert(self, payload: dict[str, Any], *, on_conflict: str | None = None) -> "_FakeQuery":
        self._op = "upsert"
        self._payload = dict(payload)
        self._on_conflict = on_conflict
        return self

    def update(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "update"
        self._payload = dict(payload)
        return self

    def select(self, cols: str = "*") -> "_FakeQuery":
        self._select_cols = cols
        if self._op is None:
            self._op = "select"
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        return self

    def execute(self) -> _FakeExecuteResult:
        assert self._op is not None
        if self._table.fail_next:
            self._table.fail_next = False
            raise RuntimeError("simulated supabase failure")

        if self._op == "select":
            matched = list(self._table.rows)
            for column, value in self._filters:
                matched = [r for r in matched if str(r.get(column)) == str(value)]
            return _FakeExecuteResult(matched)

        if self._op == "insert":
            assert self._payload is not None
            # PK (cycle_id, user_id) uniqueness
            for row in self._table.rows:
                if (
                    str(row.get("cycle_id")) == str(self._payload.get("cycle_id"))
                    and str(row.get("user_id")) == str(self._payload.get("user_id"))
                ):
                    raise RuntimeError("duplicate key value violates unique constraint")
            row = dict(self._payload)
            self._table.rows.append(row)
            return _FakeExecuteResult([row])

        if self._op == "update":
            assert self._payload is not None
            matched = list(self._table.rows)
            for column, value in self._filters:
                matched = [r for r in matched if str(r.get(column)) == str(value)]
            for row in matched:
                row.update(self._payload)
            return _FakeExecuteResult(matched)

        if self._op == "upsert":
            assert self._payload is not None
            key_cycle = str(self._payload["cycle_id"])
            key_user = str(self._payload["user_id"])
            existing = next(
                (
                    r
                    for r in self._table.rows
                    if str(r.get("cycle_id")) == key_cycle and str(r.get("user_id")) == key_user
                ),
                None,
            )
            if existing is None:
                row = dict(self._payload)
                self._table.rows.append(row)
                return _FakeExecuteResult([row])
            existing.update(self._payload)
            return _FakeExecuteResult([existing])

        raise AssertionError(f"unknown op {self._op}")


class _FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: list[dict[str, Any]] = []
        self.fail_next = False

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    """Minimal stub of supabase Client.table(...).select/insert/update chain."""

    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "topics": _FakeTable("topics"),
            "topic_materials": _FakeTable("topic_materials"),
            "votes": _FakeTable("votes"),
        }

    def table(self, name: str) -> _FakeQuery:
        return self.tables[name].query()


def _seed_ballot(client: FakeSupabaseClient) -> None:
    client.tables["topics"].rows = [
        {
            "id": 101,
            "cycle_id": 1,
            "name": "RAG в корпоративной среде",
            "description": "Корпоративный RAG: источники, доступы и контроль галлюцинаций.",
        },
        {
            "id": 102,
            "cycle_id": 1,
            "name": "AutoML для прогнозирования рисков",
            "description": "AutoML-пайплайны для оценки операционных и кредитных рисков.",
        },
        {
            "id": 103,
            "cycle_id": 1,
            "name": "LLM для анализа аудиторских данных",
            "description": "Проверка полноты выборок и аномалий в аудиторских данных с помощью LLM.",
        },
    ]
    # RAG has materials; AutoML has zero (VOTE-04)
    client.tables["topic_materials"].rows = [
        {"topic_id": 101, "material_id": 1},
        {"topic_id": 101, "material_id": 2},
        {"topic_id": 103, "material_id": 3},
    ]
    client.tables["votes"].rows = [
        {
            "cycle_id": 1,
            "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "topic_id": 101,
            "updated_at": "2026-04-05T12:00:00+00:00",
        },
        {
            "cycle_id": 1,
            "user_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "topic_id": 101,
            "updated_at": "2026-04-05T13:00:00+00:00",
        },
    ]


def test_public_export_includes_supabase_vote_repository() -> None:
    from supabase_integration import SupabaseVoteRepository

    assert SupabaseVoteRepository is not None


def test_list_topics_with_counts_includes_materials_and_vote_tallies() -> None:
    from supabase_integration import SupabaseVoteRepository

    client = FakeSupabaseClient()
    _seed_ballot(client)
    repo = SupabaseVoteRepository(client)

    topics = repo.list_topics_with_counts("1")

    by_title = {t.title: t for t in topics}
    assert by_title["RAG в корпоративной среде"].materials_count == 2
    assert by_title["RAG в корпоративной среде"].votes == 2
    assert by_title["AutoML для прогнозирования рисков"].materials_count == 0
    assert by_title["AutoML для прогнозирования рисков"].votes == 0
    assert by_title["LLM для анализа аудиторских данных"].materials_count == 1
    assert by_title["LLM для анализа аудиторских данных"].description


def test_get_vote_returns_personal_vote_or_none() -> None:
    from supabase_integration import SupabaseVoteRepository

    client = FakeSupabaseClient()
    _seed_ballot(client)
    repo = SupabaseVoteRepository(client)

    found = repo.get_vote("1", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert found is not None
    assert found.topic_id == "101"
    assert found.updated_at == datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

    missing = repo.get_vote("1", "cccccccc-cccc-cccc-cccc-cccccccccccc")
    assert missing is None


def test_upsert_insert_when_expected_updated_at_is_none() -> None:
    from supabase_integration import SupabaseVoteRepository

    client = FakeSupabaseClient()
    _seed_ballot(client)
    repo = SupabaseVoteRepository(client)

    personal = repo.upsert_vote(
        cycle_id="1",
        user_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        topic_id="102",
        expected_updated_at=None,
    )

    assert personal.topic_id == "102"
    assert personal.updated_at is not None
    rows = [
        r
        for r in client.tables["votes"].rows
        if r["user_id"] == "cccccccc-cccc-cccc-cccc-cccccccccccc"
    ]
    assert len(rows) == 1
    assert str(rows[0]["topic_id"]) == "102"


def test_upsert_cas_update_changes_topic_when_expected_matches() -> None:
    from supabase_integration import SupabaseVoteRepository

    client = FakeSupabaseClient()
    _seed_ballot(client)
    repo = SupabaseVoteRepository(client)
    expected = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

    personal = repo.upsert_vote(
        cycle_id="1",
        user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        topic_id="103",
        expected_updated_at=expected,
    )

    assert personal.topic_id == "103"
    row = next(
        r
        for r in client.tables["votes"].rows
        if r["user_id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )
    assert str(row["topic_id"]) == "103"


def test_upsert_cas_conflict_when_expected_mismatches() -> None:
    from supabase_integration import SupabaseVoteRepository

    client = FakeSupabaseClient()
    _seed_ballot(client)
    repo = SupabaseVoteRepository(client)
    stale = datetime(2026, 4, 1, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(VoteConflictError):
        repo.upsert_vote(
            cycle_id="1",
            user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            topic_id="103",
            expected_updated_at=stale,
        )


def test_upsert_maps_sdk_errors_to_persistence_error() -> None:
    from supabase_integration import SupabaseVoteRepository

    client = FakeSupabaseClient()
    _seed_ballot(client)
    client.tables["votes"].fail_next = True
    repo = SupabaseVoteRepository(client)

    with pytest.raises(PersistenceError, match="votes"):
        repo.upsert_vote(
            cycle_id="1",
            user_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
            topic_id="102",
            expected_updated_at=None,
        )


def test_adapter_source_has_no_fastapi_imports() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (
        root
        / "supabase-integration"
        / "src"
        / "supabase_integration"
        / "vote_repository.py"
    ).read_text(encoding="utf-8")
    assert "fastapi" not in source.lower()


def test_migration_003_seeds_topics_and_open_cycle_trigger() -> None:
    root = Path(__file__).resolve().parents[2]
    path = root / "supabase-integration" / "migrations" / "003_phase3_voting_ballot.sql"
    assert path.is_file()
    sql = path.read_text(encoding="utf-8")
    assert "RAG в корпоративной среде" in sql
    assert "WHERE NOT EXISTS" in sql.upper() or "where not exists" in sql
    assert "TRUNCATE" not in sql.upper()
    assert "BEFORE INSERT OR UPDATE" in sql.upper() or "before insert or update" in sql
    assert "votes" in sql
