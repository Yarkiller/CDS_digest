"""PingRecorder adapter — inserts activity_events via injected service_role client."""

from __future__ import annotations

from typing import Any, Protocol

from backend.domain.errors import PersistenceError


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


class SupabasePingRecorder:
    """Persists platform pings to public.activity_events (kind=platform_ping)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def record(
        self,
        *,
        user_id: str | None,
        kind: str,
        payload: dict,
    ) -> str:
        row = {
            "user_id": user_id,
            "kind": kind,
            "payload": payload,
        }
        try:
            result = self._client.table("activity_events").insert(row).execute()
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"activity_events insert failed: {exc}") from exc

        data = getattr(result, "data", None) or []
        if not data:
            raise PersistenceError("activity_events insert returned no rows")
        recorded_id = data[0].get("id")
        if recorded_id is None:
            raise PersistenceError("activity_events insert missing id")
        return str(recorded_id)
