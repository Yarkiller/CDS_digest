"""Readiness probe for Supabase/Postgres connectivity (monitoring / health checks)."""

from __future__ import annotations

from typing import Any, Protocol

from backend.application.ports.health_probe import ComponentHealth


class _SupabaseQuery(Protocol):
    def select(self, columns: str = "*") -> "_SupabaseQuery": ...
    def limit(self, count: int) -> "_SupabaseQuery": ...
    def execute(self) -> Any: ...


class _SupabaseClient(Protocol):
    def table(self, name: str) -> _SupabaseQuery: ...


class SupabaseHealthProbe:
    """Cheap `select id limit 1` against a low-traffic table.

    Uses the service_role client, so RLS does not block the probe. Any SDK/transport
    failure is mapped to an unhealthy component instead of propagating.
    """

    name = "database"

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def check(self) -> ComponentHealth:
        try:
            self._client.table("activity_events").select("id").limit(1).execute()
        except Exception as exc:  # noqa: BLE001 — readiness must never raise
            return ComponentHealth(name=self.name, healthy=False, detail=str(exc))
        return ComponentHealth(name=self.name, healthy=True, detail="ok")
