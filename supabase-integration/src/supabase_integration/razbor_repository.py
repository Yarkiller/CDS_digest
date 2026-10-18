"""RazborRepository adapter — list/get via injected service_role client."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from backend.domain.errors import PersistenceError
from backend.domain.razbor import Razbor, RazborStatus

_SELECT = "id,title,body_markdown,meeting_at,status,notebook_path,created_at"


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _require_dt(value: Any, field: str) -> datetime:
    parsed = _parse_dt(value)
    if parsed is None:
        raise PersistenceError(f"razbors row missing {field}")
    return parsed


def _row_to_razbor(row: dict[str, Any]) -> Razbor:
    status_raw = str(row.get("status") or "announcement")
    status = (
        RazborStatus.PUBLISHED
        if status_raw == "published"
        else RazborStatus.ANNOUNCEMENT
    )
    notebook = row.get("notebook_path")
    return Razbor(
        id=int(row["id"]),
        title=str(row["title"]),
        body_markdown=str(row.get("body_markdown") or ""),
        meeting_at=_parse_dt(row.get("meeting_at")),
        status=status,
        notebook_path=str(notebook) if notebook is not None else None,
        created_at=_require_dt(row.get("created_at"), "created_at"),
    )


class SupabaseRazborRepository:
    """Read-only RazborRepository against public.razbors (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def list_for_reader(self) -> list[Razbor]:
        try:
            result = (
                self._client.table("razbors")
                .select(_SELECT)
                .order("meeting_at", desc=True, nullsfirst=False)
                .order("created_at", desc=True)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"razbors list_for_reader failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        return [_row_to_razbor(row) for row in rows if isinstance(row, dict)]

    def get(self, razbor_id: int) -> Razbor | None:
        try:
            result = (
                self._client.table("razbors")
                .select(_SELECT)
                .eq("id", razbor_id)
                .limit(1)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"razbors get failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        return _row_to_razbor(rows[0])
