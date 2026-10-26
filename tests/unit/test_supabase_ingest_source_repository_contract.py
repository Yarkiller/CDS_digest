"""Contract tests for SupabaseIngestSourceRepository (offline fake client — no network).

SRC-03 / D-16 / D-17 — list/add/set_enabled/delete against pipeline_ingest_sources only;
SDK failures map to PersistenceError; export in __all__.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._payload: Any = None
        self._filters: list[tuple[str, Any]] = []
        self._order: list[tuple[str, bool]] = []

    def select(self, cols: str = "*") -> "_FakeQuery":
        if self._op is None:
            self._op = "select"
        self._table.selected = cols
        return self

    def insert(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "insert"
        self._payload = dict(payload)
        self._table.last_insert = dict(payload)
        return self

    def update(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "update"
        self._payload = dict(payload)
        self._table.last_update = dict(payload)
        return self

    def delete(self) -> "_FakeQuery":
        self._op = "delete"
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        return self

    def order(self, column: str, *, desc: bool = False) -> "_FakeQuery":
        self._order.append((column, desc))
        return self

    def execute(self) -> _FakeExecuteResult:
        if self._table.raise_error is not None:
            error = self._table.raise_error
            self._table.raise_error = None
            raise error
        if self._table.fail_next:
            self._table.fail_next = False
            raise RuntimeError("simulated supabase failure")

        if self._op == "insert":
            assert isinstance(self._payload, dict)
            row = dict(self._payload)
            if "id" not in row:
                row["id"] = self._table.next_id
                self._table.next_id += 1
            now = "2026-10-17T12:00:00Z"
            row.setdefault("created_at", now)
            row.setdefault("updated_at", now)
            row.setdefault("is_enabled", True)
            self._table.rows.append(row)
            return _FakeExecuteResult([dict(row)])

        if self._op == "update":
            assert isinstance(self._payload, dict)
            matched: list[dict[str, Any]] = []
            for index, row in enumerate(self._table.rows):
                if all(row.get(col) == val for col, val in self._filters):
                    updated = {**row, **self._payload}
                    self._table.rows[index] = updated
                    matched.append(dict(updated))
            return _FakeExecuteResult(matched)

        if self._op == "delete":
            kept: list[dict[str, Any]] = []
            removed: list[dict[str, Any]] = []
            for row in self._table.rows:
                if all(row.get(col) == val for col, val in self._filters):
                    removed.append(dict(row))
                else:
                    kept.append(row)
            self._table.rows = kept
            return _FakeExecuteResult(removed)

        rows = list(self._table.rows)
        for column, value in self._filters:
            rows = [r for r in rows if r.get(column) == value]
        for column, desc in reversed(self._order):
            rows = sorted(rows, key=lambda r: r.get(column), reverse=desc)
        return _FakeExecuteResult(rows)


class _FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: list[dict[str, Any]] = []
        self.next_id = 1
        self.fail_next = False
        self.raise_error: BaseException | None = None
        self.last_insert: dict[str, Any] | None = None
        self.last_update: dict[str, Any] | None = None
        self.selected: str | None = None

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "pipeline_ingest_sources": _FakeTable("pipeline_ingest_sources"),
        }

    def table(self, name: str) -> _FakeQuery:
        if name not in self.tables:
            raise AssertionError(f"unexpected table: {name}")
        return self.tables[name].query()


def test_list_returns_sources_ordered_by_created_at_then_id() -> None:
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    client = FakeSupabaseClient()
    client.tables["pipeline_ingest_sources"].rows = [
        {
            "id": 2,
            "kind": "playlist",
            "source_id": "PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "label": "Later",
            "is_enabled": True,
            "created_at": "2026-10-17T13:00:00Z",
            "updated_at": "2026-10-17T13:00:00Z",
        },
        {
            "id": 1,
            "kind": "channel",
            "source_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
            "label": "First",
            "is_enabled": False,
            "created_at": "2026-10-17T12:00:00Z",
            "updated_at": "2026-10-17T12:30:00Z",
        },
    ]
    repo = SupabaseIngestSourceRepository(client)

    rows = repo.list()
    assert [r.id for r in rows] == [1, 2]
    assert rows[0].kind == "channel"
    assert rows[0].is_enabled is False
    assert rows[0].created_at == datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


def test_add_inserts_into_pipeline_ingest_sources_and_returns_row() -> None:
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    client = FakeSupabaseClient()
    repo = SupabaseIngestSourceRepository(client)

    row = repo.add(
        kind="channel",
        source_id="UCxxxxxxxxxxxxxxxxxxxxxx",
        label="Demo",
        is_enabled=True,
    )

    assert row.id == 1
    assert row.kind == "channel"
    assert row.source_id == "UCxxxxxxxxxxxxxxxxxxxxxx"
    assert row.label == "Demo"
    assert row.is_enabled is True
    payload = client.tables["pipeline_ingest_sources"].last_insert
    assert payload is not None
    assert payload["kind"] == "channel"
    assert payload["source_id"] == "UCxxxxxxxxxxxxxxxxxxxxxx"
    assert payload["label"] == "Demo"
    assert payload["is_enabled"] is True


def test_set_enabled_updates_row() -> None:
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    client = FakeSupabaseClient()
    client.tables["pipeline_ingest_sources"].rows = [
        {
            "id": 7,
            "kind": "channel",
            "source_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
            "label": None,
            "is_enabled": True,
            "created_at": "2026-10-17T12:00:00Z",
            "updated_at": "2026-10-17T12:00:00Z",
        },
    ]
    repo = SupabaseIngestSourceRepository(client)

    updated = repo.set_enabled(7, is_enabled=False)

    assert updated.id == 7
    assert updated.is_enabled is False
    assert client.tables["pipeline_ingest_sources"].last_update is not None
    assert client.tables["pipeline_ingest_sources"].last_update["is_enabled"] is False


def test_set_enabled_missing_raises_key_error() -> None:
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    repo = SupabaseIngestSourceRepository(FakeSupabaseClient())
    with pytest.raises(KeyError):
        repo.set_enabled(999, is_enabled=False)


def test_delete_removes_row() -> None:
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    client = FakeSupabaseClient()
    client.tables["pipeline_ingest_sources"].rows = [
        {
            "id": 3,
            "kind": "playlist",
            "source_id": "PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "label": "X",
            "is_enabled": True,
            "created_at": "2026-10-17T12:00:00Z",
            "updated_at": "2026-10-17T12:00:00Z",
        },
    ]
    repo = SupabaseIngestSourceRepository(client)

    repo.delete(3)
    assert client.tables["pipeline_ingest_sources"].rows == []


def test_delete_missing_raises_key_error() -> None:
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    repo = SupabaseIngestSourceRepository(FakeSupabaseClient())
    with pytest.raises(KeyError):
        repo.delete(404)


def test_list_maps_sdk_failure_to_persistence_error() -> None:
    from backend.domain.errors import PersistenceError
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    client = FakeSupabaseClient()
    client.tables["pipeline_ingest_sources"].fail_next = True
    repo = SupabaseIngestSourceRepository(client)

    with pytest.raises(PersistenceError):
        repo.list()


def test_add_maps_sdk_failure_to_persistence_error() -> None:
    from backend.domain.errors import PersistenceError
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    client = FakeSupabaseClient()
    client.tables["pipeline_ingest_sources"].fail_next = True
    repo = SupabaseIngestSourceRepository(client)

    with pytest.raises(PersistenceError):
        repo.add(kind="channel", source_id="UCxxxxxxxxxxxxxxxxxxxxxx", label=None)


def test_existing_persistence_error_is_reraised_unchanged() -> None:
    from backend.domain.errors import PersistenceError
    from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository

    client = FakeSupabaseClient()
    sentinel = PersistenceError("already mapped")
    client.tables["pipeline_ingest_sources"].raise_error = sentinel
    repo = SupabaseIngestSourceRepository(client)

    with pytest.raises(PersistenceError) as excinfo:
        repo.list()
    assert excinfo.value is sentinel


def test_repository_is_exported_from_package() -> None:
    import supabase_integration

    assert "SupabaseIngestSourceRepository" in supabase_integration.__all__
    assert hasattr(supabase_integration, "SupabaseIngestSourceRepository")
