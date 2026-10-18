"""Contract tests for SupabaseIngestionScheduleRepository (offline fake — no network).

ING-06 / D-14 — get defaults / upsert id=1 / PersistenceError mapping / __all__ export.
"""

from __future__ import annotations

from datetime import datetime, time, timezone
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
        self._table.ops.append("select")
        return self

    def insert(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "insert"
        self._payload = dict(payload)
        self._table.last_insert = dict(payload)
        self._table.ops.append("insert")
        return self

    def upsert(self, payload: dict[str, Any], *, on_conflict: str | None = None) -> "_FakeQuery":
        self._op = "upsert"
        self._payload = dict(payload)
        self._table.last_upsert = dict(payload)
        self._table.last_upsert_on_conflict = on_conflict
        self._table.ops.append("upsert")
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        return self

    def execute(self) -> _FakeExecuteResult:
        if self._table.raise_error is not None:
            error = self._table.raise_error
            self._table.raise_error = None
            raise error
        if self._table.fail_next:
            self._table.fail_next = False
            raise RuntimeError("boom")

        if self._op == "upsert":
            assert isinstance(self._payload, dict)
            existing = next(
                (r for r in self._table.rows if r.get("id") == self._payload.get("id")),
                None,
            )
            # Supabase upsert keeps columns it was not given (e.g. last_run_at).
            merged = {**(existing or {}), **self._payload}
            self._table.rows = [
                r for r in self._table.rows if r.get("id") != self._payload.get("id")
            ]
            if not self._table.drop_rows_after_upsert:
                self._table.rows.append(dict(merged))
            if self._table.upsert_returns_empty_data:
                return _FakeExecuteResult([])
            return _FakeExecuteResult([dict(merged)])

        if self._op == "insert":
            assert isinstance(self._payload, dict)
            self._table.rows.append(dict(self._payload))
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
        self.last_insert: dict[str, Any] | None = None
        self.last_upsert: dict[str, Any] | None = None
        self.last_upsert_on_conflict: str | None = None
        self.selected: str | None = None
        self.ops: list[str] = []
        # WR-06: script upsert responses that carry no representation.
        self.upsert_returns_empty_data = False
        self.drop_rows_after_upsert = False

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "ingestion_schedule": _FakeTable("ingestion_schedule"),
        }

    def table(self, name: str) -> _FakeQuery:
        if name not in self.tables:
            raise AssertionError(f"unexpected table: {name}")
        return self.tables[name].query()


def _repo_cls():
    try:
        from supabase_integration.ingestion_schedule_repository import (
            SupabaseIngestionScheduleRepository,
        )
    except ImportError as exc:  # pragma: no cover - RED until adapter ships
        pytest.fail(f"SupabaseIngestionScheduleRepository not importable: {exc}")
    return SupabaseIngestionScheduleRepository


def test_get_empty_returns_defaults_without_write() -> None:
    from backend.domain.ingestion_schedule import IngestionSchedule

    client = FakeSupabaseClient()
    repo = _repo_cls()(client)
    row = repo.get()
    assert isinstance(row, IngestionSchedule)
    assert row.enabled is True
    assert row.time_of_day == time(6, 0)
    assert row.days_of_week == (1, 2, 3, 4, 5, 6, 7)
    assert row.last_run_at is None
    assert row.updated_at is None
    assert "insert" not in client.tables["ingestion_schedule"].ops
    assert "upsert" not in client.tables["ingestion_schedule"].ops


def test_get_parses_row_and_normalizes_days() -> None:
    client = FakeSupabaseClient()
    client.tables["ingestion_schedule"].rows = [
        {
            "id": 1,
            "enabled": False,
            "time_of_day": "07:30:00",
            "days_of_week": [5, 1],
            "last_run_at": "2026-10-18T03:00:00+00:00",
            "updated_at": "2026-10-18T03:00:00+00:00",
        }
    ]
    repo = _repo_cls()(client)
    row = repo.get()
    assert row.enabled is False
    assert row.time_of_day == time(7, 30)
    assert row.days_of_week == (1, 5)
    assert row.last_run_at == datetime(2026, 10, 18, 3, 0, tzinfo=timezone.utc)
    assert row.updated_at == datetime(2026, 10, 18, 3, 0, tzinfo=timezone.utc)


def test_update_upserts_singleton_with_updated_at() -> None:
    client = FakeSupabaseClient()
    repo = _repo_cls()(client)
    returned = repo.update(
        enabled=False,
        time_of_day=time(7, 30),
        days_of_week=(5, 1),
    )
    payload = client.tables["ingestion_schedule"].last_upsert
    assert payload is not None
    assert client.tables["ingestion_schedule"].last_upsert_on_conflict == "id"
    assert payload["id"] == 1
    assert payload["enabled"] is False
    assert payload["time_of_day"] == "07:30:00"
    assert payload["days_of_week"] == [1, 5]
    assert isinstance(payload["updated_at"], str) and payload["updated_at"]
    assert returned.enabled is False
    assert returned.time_of_day == time(7, 30)
    assert returned.days_of_week == (1, 5)
    assert returned.updated_at is not None


def test_update_empty_upsert_data_preserves_last_run_at_via_follow_up_read() -> None:
    """WR-06: an empty upsert representation must not fabricate last_run_at=None."""
    client = FakeSupabaseClient()
    table = client.tables["ingestion_schedule"]
    table.rows = [
        {
            "id": 1,
            "enabled": True,
            "time_of_day": "06:00:00",
            "days_of_week": [1, 2, 3, 4, 5, 6, 7],
            "last_run_at": "2026-10-18T03:00:00+00:00",
            "updated_at": "2026-10-17T03:00:00+00:00",
        }
    ]
    table.upsert_returns_empty_data = True
    repo = _repo_cls()(client)

    returned = repo.update(
        enabled=False,
        time_of_day=time(7, 30),
        days_of_week=(5, 1),
    )

    assert returned.last_run_at == datetime(2026, 10, 18, 3, 0, tzinfo=timezone.utc)
    assert returned.enabled is False
    assert returned.time_of_day == time(7, 30)
    assert returned.days_of_week == (1, 5)
    assert "select" in table.ops


def test_update_empty_upsert_and_missing_row_raises_persistence_error() -> None:
    """WR-06: if the row is still missing after upsert, fail loudly."""
    from backend.domain.errors import PersistenceError

    client = FakeSupabaseClient()
    table = client.tables["ingestion_schedule"]
    table.upsert_returns_empty_data = True
    table.drop_rows_after_upsert = True
    repo = _repo_cls()(client)

    with pytest.raises(PersistenceError):
        repo.update(enabled=True, time_of_day=time(6, 0), days_of_week=(1,))


def test_sdk_errors_map_to_persistence_error_without_secrets() -> None:
    from backend.domain.errors import PersistenceError

    client = FakeSupabaseClient()
    client.tables["ingestion_schedule"].fail_next = True
    repo = _repo_cls()(client)
    with pytest.raises(PersistenceError) as exc_info:
        repo.get()
    msg = str(exc_info.value)
    assert "SUPABASE_SECRET_KEY" not in msg
    assert "https://" not in msg

    client.tables["ingestion_schedule"].fail_next = True
    with pytest.raises(PersistenceError) as exc_info:
        repo.update(enabled=True, time_of_day=time(6, 0), days_of_week=(1,))
    msg = str(exc_info.value)
    assert "SUPABASE_SECRET_KEY" not in msg


def test_repository_is_exported_from_package() -> None:
    import supabase_integration

    assert "SupabaseIngestionScheduleRepository" in supabase_integration.__all__
    assert hasattr(supabase_integration, "SupabaseIngestionScheduleRepository")
