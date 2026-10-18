"""Contract tests for Supabase PingRecorder + ProfileRepository adapters (offline stubs)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from backend.domain.errors import PersistenceError
from supabase_integration import (
    SupabasePingRecorder,
    SupabaseProfileRepository,
    create_publishable_client,
    create_service_role_client,
)


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._payload: dict[str, Any] | None = None
        self._filters: list[tuple[str, str]] = []
        self._select_cols: str = "*"

    def insert(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "insert"
        self._payload = dict(payload)
        return self

    def upsert(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "upsert"
        self._payload = dict(payload)
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

    def eq(self, column: str, value: str) -> "_FakeQuery":
        self._filters.append((column, value))
        return self

    def execute(self) -> _FakeExecuteResult:
        assert self._op is not None
        if self._table.fail_next:
            self._table.fail_next = False
            raise RuntimeError("simulated supabase failure")
        if self._op == "insert":
            assert self._payload is not None
            row = dict(self._payload)
            row.setdefault("id", self._table.next_id)
            self._table.next_id += 1
            self._table.rows.append(row)
            self._table.last_insert = row
            return _FakeExecuteResult([row])
        if self._op == "upsert":
            assert self._payload is not None
            key = self._payload["id"]
            existing = next((r for r in self._table.rows if r.get("id") == key), None)
            if existing is None:
                row = {
                    "id": key,
                    "email": self._payload["email"],
                    "role": self._payload.get("role", "employee"),
                    "display_name": self._payload.get("display_name"),
                }
                self._table.rows.append(row)
                return _FakeExecuteResult([row])
            existing["email"] = self._payload["email"]
            if "role" in self._payload:
                existing["role"] = self._payload["role"]
            if "display_name" in self._payload:
                existing["display_name"] = self._payload["display_name"]
            return _FakeExecuteResult([existing])
        if self._op == "update":
            assert self._payload is not None
            matched = list(self._table.rows)
            for column, value in self._filters:
                matched = [r for r in matched if r.get(column) == value]
            for row in matched:
                row.update(self._payload)
            return _FakeExecuteResult(matched)
        if self._op == "select":
            matched = list(self._table.rows)
            for column, value in self._filters:
                matched = [r for r in matched if r.get(column) == value]
            return _FakeExecuteResult(matched)
        raise AssertionError(f"unknown op {self._op}")


class _FakeTable:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.next_id = 1
        self.last_insert: dict[str, Any] | None = None
        self.fail_next = False

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    """Minimal stub of supabase Client.table(...).insert/upsert/select chain."""

    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "activity_events": _FakeTable(),
            "profiles": _FakeTable(),
        }

    def table(self, name: str) -> _FakeQuery:
        return self.tables[name].query()


def test_public_exports_include_client_helpers_and_adapters() -> None:
    assert callable(create_publishable_client)
    assert callable(create_service_role_client)
    assert SupabasePingRecorder is not None
    assert SupabaseProfileRepository is not None


def test_ping_recorder_inserts_platform_ping_payload() -> None:
    client = FakeSupabaseClient()
    recorder = SupabasePingRecorder(client)

    recorded_id = recorder.record(
        user_id="11111111-1111-1111-1111-111111111111",
        kind="platform_ping",
        payload={"source": "unit"},
    )

    assert recorded_id == "1"
    inserted = client.tables["activity_events"].last_insert
    assert inserted is not None
    assert inserted["user_id"] == "11111111-1111-1111-1111-111111111111"
    assert inserted["kind"] == "platform_ping"
    assert inserted["payload"] == {"source": "unit"}


def test_ping_recorder_maps_sdk_errors_to_persistence_error() -> None:
    client = FakeSupabaseClient()
    client.tables["activity_events"].fail_next = True
    recorder = SupabasePingRecorder(client)

    with pytest.raises(PersistenceError):
        recorder.record(user_id=None, kind="platform_ping", payload={})


def test_profile_get_or_upsert_returns_app_role_shape() -> None:
    client = FakeSupabaseClient()
    repo = SupabaseProfileRepository(client)

    user = repo.get_or_upsert(
        "22222222-2222-2222-2222-222222222222",
        "alice@sberbank.ru",
    )

    assert user.id == "22222222-2222-2222-2222-222222222222"
    assert user.email == "alice@sberbank.ru"
    assert user.role == "employee"


def test_profile_get_or_upsert_is_idempotent_when_row_exists() -> None:
    client = FakeSupabaseClient()
    uid = "33333333-3333-3333-3333-333333333333"
    client.tables["profiles"].rows.append(
        {"id": uid, "email": "bob@omega.sbrf.ru", "role": "analyst"}
    )
    repo = SupabaseProfileRepository(client)

    first = repo.get_or_upsert(uid, "bob@omega.sbrf.ru")
    second = repo.get_or_upsert(uid, "bob@omega.sbrf.ru")

    assert first.role == "analyst"
    assert second.role == "analyst"
    assert len(client.tables["profiles"].rows) == 1


def test_profile_set_display_name_persists_and_returns_user() -> None:
    client = FakeSupabaseClient()
    uid = "44444444-4444-4444-4444-444444444444"
    repo = SupabaseProfileRepository(client)
    repo.get_or_upsert(uid, "carol@sberbank.ru")

    updated = repo.set_display_name(uid, "Каролина")

    assert updated.display_name == "Каролина"
    assert client.tables["profiles"].rows[0]["display_name"] == "Каролина"


def test_domain_and_use_cases_have_zero_supabase_imports() -> None:
    import backend.application.use_cases.get_current_user as me_uc
    import backend.application.use_cases.record_platform_ping as ping_uc
    import backend.domain.current_user as cu

    for mod in (ping_uc, me_uc, cu):
        assert mod.__file__ is not None
        source = Path(mod.__file__).read_text(encoding="utf-8")
        assert "supabase" not in source.lower()
