"""VotingCycleReader adapter — read voting_cycles via injected service_role client."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from backend.domain.errors import PersistenceError
from backend.domain.voting_cycle import VotingCycle


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _row_to_cycle(row: dict[str, Any]) -> VotingCycle:
    return VotingCycle(
        id=str(row["id"]),
        status=str(row["status"]),
        opens_at=_parse_dt(row["opens_at"]),
        closes_at=_parse_dt(row["closes_at"]),
    )


class SupabaseVotingCycleReader:
    """Read-only VotingCycleReader against voting_cycles (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def list_cycles(self) -> list[VotingCycle]:
        try:
            result = (
                self._client.table("voting_cycles")
                .select("id,status,opens_at,closes_at")
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"voting_cycles list failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        return [_row_to_cycle(row) for row in rows]
