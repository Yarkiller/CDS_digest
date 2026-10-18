"""Contract tests for SupabaseHealthProbe — offline, no network."""

from __future__ import annotations

from backend.application.ports.health_probe import ComponentHealth
from supabase_integration import SupabaseHealthProbe


class _FakeQuery:
    def __init__(self, fail: bool) -> None:
        self._fail = fail

    def select(self, columns: str = "*") -> "_FakeQuery":
        return self

    def limit(self, count: int) -> "_FakeQuery":
        return self

    def execute(self):
        if self._fail:
            raise RuntimeError("boom")
        return type("_Result", (), {"data": []})()


class _FakeClient:
    def __init__(self, fail: bool = False) -> None:
        self._fail = fail
        self.tables: list[str] = []

    def table(self, name: str) -> _FakeQuery:
        self.tables.append(name)
        return _FakeQuery(self._fail)


def test_health_probe_reports_healthy_on_success() -> None:
    probe = SupabaseHealthProbe(_FakeClient())
    result = probe.check()
    assert isinstance(result, ComponentHealth)
    assert result.name == "database"
    assert result.healthy is True


def test_health_probe_reports_unhealthy_on_sdk_error() -> None:
    probe = SupabaseHealthProbe(_FakeClient(fail=True))
    result = probe.check()
    assert result.healthy is False
    assert "boom" in result.detail


def test_health_probe_queries_a_table() -> None:
    client = _FakeClient()
    SupabaseHealthProbe(client).check()
    assert client.tables == ["activity_events"]
