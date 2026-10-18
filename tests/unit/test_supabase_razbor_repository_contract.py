"""Contract tests for SupabaseRazborRepository (offline stubs — no network)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from backend.domain.errors import PersistenceError
from backend.domain.razbor import Razbor, RazborStatus


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]] | None = None) -> None:
        self.data = data if data is not None else []


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._filters: list[tuple[str, Any]] = []
        self._order: list[tuple[str, bool, str | None]] = []
        self._limit: int | None = None

    def select(self, *_a: Any, **_k: Any) -> "_FakeQuery":
        self._op = "select"
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        return self

    def order(self, column: str, *, desc: bool = False, nullsfirst: bool | None = None) -> "_FakeQuery":
        nulls = None
        if nullsfirst is True:
            nulls = "first"
        elif nullsfirst is False:
            nulls = "last"
        self._order.append((column, desc, nulls))
        return self

    def limit(self, n: int) -> "_FakeQuery":
        self._limit = n
        return self

    def execute(self) -> _FakeExecuteResult:
        if self._table.fail_next:
            self._table.fail_next = False
            raise RuntimeError("simulated supabase failure")
        matched = list(self._table.rows)
        for column, value in self._filters:
            matched = [r for r in matched if str(r.get(column)) == str(value)]
        # Lightweight order: meeting_at desc nulls last, then created_at desc
        for column, desc, nulls in reversed(self._order):
            def key(row: dict[str, Any], col: str = column, nf: str | None = nulls) -> tuple:
                val = row.get(col)
                is_null = val is None
                if nf == "last":
                    null_rank = 1 if is_null else 0
                elif nf == "first":
                    null_rank = 0 if is_null else 1
                else:
                    null_rank = 0
                return (null_rank, val or "")

            matched.sort(key=key, reverse=desc)
        if self._limit is not None:
            matched = matched[: self._limit]
        return _FakeExecuteResult(matched)


class _FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: list[dict[str, Any]] = []
        self.fail_next = False

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {"razbors": _FakeTable("razbors")}

    def table(self, name: str) -> _FakeQuery:
        return self.tables[name].query()


def _seed(client: FakeSupabaseClient) -> None:
    created = datetime(2026, 4, 1, tzinfo=timezone.utc).isoformat()
    client.tables["razbors"].rows = [
        {
            "id": 1,
            "title": "Announcement",
            "body_markdown": "",
            "meeting_at": "2026-05-05T15:00:00+00:00",
            "status": "announcement",
            "notebook_path": None,
            "created_at": created,
        },
        {
            "id": 2,
            "title": "Published with notebook",
            "body_markdown": "## Hello\n\nBody",
            "meeting_at": "2026-04-20T15:00:00+00:00",
            "status": "published",
            "notebook_path": "hybrid-retrieval.ipynb",
            "created_at": created,
        },
        {
            "id": 3,
            "title": "Overview",
            "body_markdown": "## Обзор\n\nNo metrics.",
            "meeting_at": None,
            "status": "published",
            "notebook_path": None,
            "created_at": created,
        },
    ]


def test_list_for_reader_returns_razbors_ordered() -> None:
    from supabase_integration.razbor_repository import SupabaseRazborRepository

    client = FakeSupabaseClient()
    _seed(client)
    repo = SupabaseRazborRepository(client)

    items = repo.list_for_reader()
    assert len(items) == 3
    assert all(isinstance(r, Razbor) for r in items)
    by_id = {r.id: r for r in items}
    assert by_id[1].status == RazborStatus.ANNOUNCEMENT
    assert by_id[2].notebook_path == "hybrid-retrieval.ipynb"
    assert by_id[3].status == RazborStatus.PUBLISHED
    assert by_id[3].meeting_at is None


def test_get_returns_razbor_or_none() -> None:
    from supabase_integration.razbor_repository import SupabaseRazborRepository

    client = FakeSupabaseClient()
    _seed(client)
    repo = SupabaseRazborRepository(client)

    found = repo.get(2)
    assert found is not None
    assert found.title == "Published with notebook"
    assert found.status == RazborStatus.PUBLISHED
    assert repo.get(999) is None


def test_list_maps_sdk_errors_to_persistence_error() -> None:
    from supabase_integration.razbor_repository import SupabaseRazborRepository

    client = FakeSupabaseClient()
    client.tables["razbors"].fail_next = True
    repo = SupabaseRazborRepository(client)

    with pytest.raises(PersistenceError, match="razbor"):
        repo.list_for_reader()
