"""Contract tests for SupabasePipelineConfigRepository (offline fake client — no network).

PIPE-03 / D-08 / D-11 — get() reads the id = 1 singleton (None when absent),
save() upserts {id: 1, yaml, updated_at}, and SDK failures map to PersistenceError.
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

    def select(self, cols: str = "*") -> "_FakeQuery":
        if self._op is None:
            self._op = "select"
        self._table.selected = cols
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        return self

    def upsert(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "upsert"
        self._payload = dict(payload)
        self._table.last_upsert = dict(payload)
        return self

    def execute(self) -> _FakeExecuteResult:
        if self._table.raise_error is not None:
            error = self._table.raise_error
            self._table.raise_error = None
            raise error
        if self._table.fail_next:
            self._table.fail_next = False
            raise RuntimeError("simulated supabase failure")

        if self._op == "upsert":
            assert isinstance(self._payload, dict)
            self._table.rows = [dict(self._payload)]
            return _FakeExecuteResult([dict(self._payload)])

        rows = list(self._table.rows)
        for column, value in self._filters:
            rows = [r for r in rows if r.get(column) == value]
        return _FakeExecuteResult(rows)


class _FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: list[dict[str, Any]] = []
        self.fail_next = False
        self.raise_error: BaseException | None = None
        self.last_upsert: dict[str, Any] | None = None
        self.selected: str | None = None

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "pipeline_config": _FakeTable("pipeline_config"),
        }

    def table(self, name: str) -> _FakeQuery:
        return self.tables[name].query()


def test_get_returns_config_parsed_from_iso_z() -> None:
    from supabase_integration.pipeline_config_repository import SupabasePipelineConfigRepository

    client = FakeSupabaseClient()
    client.tables["pipeline_config"].rows = [
        {"id": 1, "yaml": "template: lecture\n", "updated_at": "2026-10-04T10:00:00Z"},
    ]
    repo = SupabasePipelineConfigRepository(client)

    config = repo.get()
    assert config is not None
    assert config.yaml == "template: lecture\n"
    assert config.updated_at == datetime(2026, 10, 4, 10, 0, tzinfo=timezone.utc)


def test_get_returns_none_when_no_row() -> None:
    """D-11: an absent singleton row is the valid empty state, not an error."""
    from supabase_integration.pipeline_config_repository import SupabasePipelineConfigRepository

    repo = SupabasePipelineConfigRepository(FakeSupabaseClient())
    assert repo.get() is None


def test_save_upserts_singleton_payload_and_returns_config() -> None:
    from supabase_integration.pipeline_config_repository import SupabasePipelineConfigRepository

    client = FakeSupabaseClient()
    repo = SupabasePipelineConfigRepository(client)
    when = datetime(2026, 10, 4, 12, 30, tzinfo=timezone.utc)

    config = repo.save(yaml="template: podcast\n", updated_at=when)

    assert config.yaml == "template: podcast\n"
    assert config.updated_at == when
    payload = client.tables["pipeline_config"].last_upsert
    assert payload is not None
    assert payload["id"] == 1
    assert payload["yaml"] == "template: podcast\n"
    assert payload["updated_at"] == "2026-10-04T12:30:00Z"


def test_get_maps_sdk_failure_to_persistence_error() -> None:
    from backend.domain.errors import PersistenceError
    from supabase_integration.pipeline_config_repository import SupabasePipelineConfigRepository

    client = FakeSupabaseClient()
    client.tables["pipeline_config"].fail_next = True
    repo = SupabasePipelineConfigRepository(client)

    with pytest.raises(PersistenceError):
        repo.get()


def test_save_maps_sdk_failure_to_persistence_error() -> None:
    from backend.domain.errors import PersistenceError
    from supabase_integration.pipeline_config_repository import SupabasePipelineConfigRepository

    client = FakeSupabaseClient()
    client.tables["pipeline_config"].fail_next = True
    repo = SupabasePipelineConfigRepository(client)

    with pytest.raises(PersistenceError):
        repo.save(yaml="template: lecture\n", updated_at=datetime.now(timezone.utc))


def test_existing_persistence_error_is_reraised_unchanged() -> None:
    from backend.domain.errors import PersistenceError
    from supabase_integration.pipeline_config_repository import SupabasePipelineConfigRepository

    client = FakeSupabaseClient()
    sentinel = PersistenceError("already mapped")
    client.tables["pipeline_config"].raise_error = sentinel
    repo = SupabasePipelineConfigRepository(client)

    with pytest.raises(PersistenceError) as excinfo:
        repo.get()
    assert excinfo.value is sentinel


def test_repository_is_exported_from_package() -> None:
    import supabase_integration

    assert "SupabasePipelineConfigRepository" in supabase_integration.__all__
    assert hasattr(supabase_integration, "SupabasePipelineConfigRepository")
