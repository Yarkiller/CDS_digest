"""Contract tests for Supabase IssueRepository + MaterialRepository (offline stubs)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from backend.domain.errors import PersistenceError
from backend.domain.material import MaterialStatus


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._payload: dict[str, Any] | None = None
        self._filters: list[tuple[str, Any]] = []
        self._neq_filters: list[tuple[str, Any]] = []
        self._not_null: list[str] = []
        self._order: tuple[str, bool] | None = None
        self._limit: int | None = None
        self._select_cols: str = "*"

    def insert(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "insert"
        self._payload = dict(payload)
        return self

    def upsert(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "upsert"
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

    def neq(self, column: str, value: Any) -> "_FakeQuery":
        self._neq_filters.append((column, value))
        return self

    @property
    def not_(self) -> "_FakeNot":
        return _FakeNot(self)

    def order(self, column: str, *, desc: bool = False) -> "_FakeQuery":
        self._order = (column, desc)
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
            for column, value in self._neq_filters:
                matched = [r for r in matched if r.get(column) != value]
            for column in self._not_null:
                matched = [r for r in matched if r.get(column) is not None]
            if self._order is not None:
                col, desc = self._order
                matched.sort(key=lambda r: r.get(col) or "", reverse=desc)
            if self._limit is not None:
                matched = matched[: self._limit]
            # Nested select simulation: digest_issue_items with materials embed
            if "materials" in self._select_cols and self._table.name == "digest_issue_items":
                materials = self._table.client.tables["materials"].rows
                enriched = []
                for row in matched:
                    mat = next((m for m in materials if m["id"] == row["material_id"]), None)
                    enriched.append({**row, "materials": mat})
                return _FakeExecuteResult(enriched)
            if "material_tags" in self._select_cols and self._table.name == "materials":
                tags = self._table.client.tables["material_tags"].rows
                rels = self._table.client.tables["material_relations"].rows
                enriched = []
                for row in matched:
                    row_tags = [
                        {"tag_slug": t["tag_slug"], "tag_label": t["tag_label"]}
                        for t in tags
                        if t["material_id"] == row["id"]
                    ]
                    related = [
                        str(r["to_material_id"])
                        for r in rels
                        if r["from_material_id"] == row["id"]
                    ]
                    enriched.append(
                        {
                            **row,
                            "material_tags": row_tags,
                            "material_relations": [
                                {"to_material_id": int(rid)} for rid in related
                            ],
                        }
                    )
                return _FakeExecuteResult(enriched)
            return _FakeExecuteResult(matched)
        raise AssertionError(f"unknown op {self._op}")


class _FakeNot:
    def __init__(self, query: _FakeQuery) -> None:
        self._query = query

    def is_(self, column: str, value: str) -> _FakeQuery:
        # supabase .not_.is_("published_at", "null") → published_at IS NOT NULL
        if value == "null":
            self._query._not_null.append(column)
        return self._query


class _FakeTable:
    def __init__(self, name: str, client: "FakeSupabaseClient") -> None:
        self.name = name
        self.client = client
        self.rows: list[dict[str, Any]] = []
        self.fail_next = False

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    """Minimal stub of supabase Client.table(...).select/eq/order/limit chain."""

    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "digest_issues": _FakeTable("digest_issues", self),
            "digest_issue_items": _FakeTable("digest_issue_items", self),
            "materials": _FakeTable("materials", self),
            "material_tags": _FakeTable("material_tags", self),
            "material_relations": _FakeTable("material_relations", self),
        }

    def table(self, name: str) -> _FakeQuery:
        return self.tables[name].query()


def _seed_content(client: FakeSupabaseClient) -> None:
    client.tables["materials"].rows.extend(
        [
            {
                "id": 1,
                "slug": "rag-systems",
                "title": "Building Production RAG Systems",
                "dek": "dek",
                "body_markdown": "## Retrieval\n\nBody.",
                "format": "статья",
                "status": "ready",
                "reading_minutes": 8,
                "provenance_label": "внешний текстовый источник",
                "source_id": None,
                "roles": ["ds", "sva"],
                "published_at": "2026-03-20T12:00:00+00:00",
                "created_at": "2026-03-20T12:00:00+00:00",
                "updated_at": "2026-03-20T12:00:00+00:00",
            },
            {
                "id": 2,
                "slug": "sql-dashboards",
                "title": "SQL dashboards",
                "dek": "",
                "body_markdown": "## KPI\n\nBody.",
                "format": "статья",
                "status": "ready",
                "reading_minutes": 9,
                "provenance_label": "внутренний гайд",
                "source_id": None,
                "roles": ["analyst"],
                "published_at": "2026-03-15T12:00:00+00:00",
                "created_at": "2026-03-15T12:00:00+00:00",
                "updated_at": "2026-03-15T12:00:00+00:00",
            },
        ]
    )
    client.tables["material_tags"].rows.append(
        {"material_id": 1, "tag_slug": "rag", "tag_label": "RAG"}
    )
    client.tables["material_relations"].rows.append(
        {"from_material_id": 1, "to_material_id": 2, "kind": "related"}
    )
    client.tables["digest_issues"].rows.extend(
        [
            {
                "id": 13,
                "number": 13,
                "period_label": "10–16 марта 2026",
                "title": "Past",
                "published_at": "2026-03-10T12:00:00+00:00",
            },
            {
                "id": 14,
                "number": 14,
                "period_label": "17–23 марта 2026",
                "title": "Current",
                "published_at": "2026-03-17T12:00:00+00:00",
            },
        ]
    )
    client.tables["digest_issue_items"].rows.extend(
        [
            {"issue_id": 14, "material_id": 1, "position": 1},
            {"issue_id": 13, "material_id": 2, "position": 1},
        ]
    )


def test_public_exports_include_issue_and_material_adapters() -> None:
    from supabase_integration import SupabaseIssueRepository, SupabaseMaterialRepository

    assert SupabaseIssueRepository is not None
    assert SupabaseMaterialRepository is not None


def test_get_latest_published_orders_by_published_at_desc() -> None:
    from supabase_integration import SupabaseIssueRepository

    client = FakeSupabaseClient()
    _seed_content(client)
    repo = SupabaseIssueRepository(client)

    issue = repo.get_latest_published()

    assert issue is not None
    assert issue.number == 14
    assert issue.title == "Current"
    assert len(issue.items) == 1
    assert issue.items[0].slug == "rag-systems"
    assert issue.items[0].position == 1
    assert issue.published_at == datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc)


def test_get_latest_published_returns_none_when_empty() -> None:
    from supabase_integration import SupabaseIssueRepository

    repo = SupabaseIssueRepository(FakeSupabaseClient())
    assert repo.get_latest_published() is None


def test_get_by_number_loads_issue_with_items() -> None:
    from supabase_integration import SupabaseIssueRepository

    client = FakeSupabaseClient()
    _seed_content(client)
    repo = SupabaseIssueRepository(client)

    issue = repo.get_by_number(13)

    assert issue is not None
    assert issue.number == 13
    assert issue.items[0].slug == "sql-dashboards"


def test_list_past_published_excludes_current() -> None:
    from supabase_integration import SupabaseIssueRepository

    client = FakeSupabaseClient()
    _seed_content(client)
    repo = SupabaseIssueRepository(client)

    past = repo.list_past_published()

    numbers = [i.number for i in past]
    assert 14 not in numbers
    assert 13 in numbers


def test_issue_repo_maps_sdk_errors_to_persistence_error() -> None:
    from supabase_integration import SupabaseIssueRepository

    client = FakeSupabaseClient()
    client.tables["digest_issues"].fail_next = True
    repo = SupabaseIssueRepository(client)

    with pytest.raises(PersistenceError):
        repo.get_latest_published()


def test_get_by_slug_returns_ready_material_with_tags() -> None:
    from supabase_integration import SupabaseMaterialRepository

    client = FakeSupabaseClient()
    _seed_content(client)
    repo = SupabaseMaterialRepository(client)

    material = repo.get_by_slug("rag-systems")

    assert material is not None
    assert material.slug == "rag-systems"
    assert material.status == MaterialStatus.READY
    assert ("rag", "RAG") in material.tags or ("RAG", "rag") in {
        (label, slug) for slug, label in material.tags
    } or any(t[0] == "rag" for t in material.tags)
    assert "2" in material.related_material_ids or 2 in [
        int(x) for x in material.related_material_ids
    ]


def test_get_by_slug_returns_none_when_missing() -> None:
    from supabase_integration import SupabaseMaterialRepository

    repo = SupabaseMaterialRepository(FakeSupabaseClient())
    assert repo.get_by_slug("missing-slug") is None


def test_material_repo_maps_sdk_errors_to_persistence_error() -> None:
    from supabase_integration import SupabaseMaterialRepository

    client = FakeSupabaseClient()
    client.tables["materials"].fail_next = True
    repo = SupabaseMaterialRepository(client)

    with pytest.raises(PersistenceError):
        repo.get_by_slug("rag-systems")
