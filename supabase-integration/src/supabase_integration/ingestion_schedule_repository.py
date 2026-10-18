"""IngestionScheduleRepository adapter — singleton ingestion_schedule via injected client.

ING-06 / D-14 (migration 013): one global row ``id = 1``. Missing row → domain
defaults (no write). Updates upsert with ``on_conflict="id"`` and always set
``updated_at``. SDK failures map to ``PersistenceError`` at this boundary.
"""

from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any, Protocol

from backend.domain.errors import PersistenceError
from backend.domain.ingestion_schedule import (
    IngestionSchedule,
    default_ingestion_schedule,
)

_TABLE = "ingestion_schedule"
_SINGLETON_ID = 1


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time_of_day(value: Any) -> time:
    if isinstance(value, time):
        return value
    return time.fromisoformat(str(value))


def _row_to_schedule(row: dict[str, Any]) -> IngestionSchedule:
    raw_days = row.get("days_of_week") or ()
    days = tuple(sorted({int(d) for d in raw_days}))
    defaults = default_ingestion_schedule()
    return IngestionSchedule(
        enabled=bool(row.get("enabled", True)),
        time_of_day=_parse_time_of_day(row.get("time_of_day", "06:00")),
        days_of_week=days if days else defaults.days_of_week,
        last_run_at=_parse_dt(row.get("last_run_at")),
        updated_at=_parse_dt(row.get("updated_at")),
    )


class SupabaseIngestionScheduleRepository:
    """IngestionScheduleRepository against public.ingestion_schedule (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def get(self) -> IngestionSchedule:
        try:
            result = (
                self._client.table(_TABLE)
                .select("enabled,time_of_day,days_of_week,last_run_at,updated_at")
                .eq("id", _SINGLETON_ID)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError("Не удалось прочитать расписание ингеста") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return default_ingestion_schedule()
        row = rows[0]
        if not isinstance(row, dict):
            return default_ingestion_schedule()
        return _row_to_schedule(row)

    def update(
        self,
        *,
        enabled: bool,
        time_of_day: time,
        days_of_week: tuple[int, ...],
    ) -> IngestionSchedule:
        now = datetime.now(timezone.utc)
        normalized_days = tuple(sorted(set(days_of_week)))
        payload = {
            "id": _SINGLETON_ID,
            "enabled": enabled,
            "time_of_day": (
                f"{time_of_day.hour:02d}:{time_of_day.minute:02d}:"
                f"{time_of_day.second:02d}"
            ),
            "days_of_week": list(normalized_days),
            "updated_at": _iso(now),
        }
        try:
            result = (
                self._client.table(_TABLE)
                .upsert(payload, on_conflict="id")
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError("Не удалось сохранить расписание ингеста") from exc

        rows = getattr(result, "data", None) or []
        if rows and isinstance(rows[0], dict):
            return _row_to_schedule(rows[0])
        return IngestionSchedule(
            enabled=enabled,
            time_of_day=time(time_of_day.hour, time_of_day.minute),
            days_of_week=normalized_days,
            last_run_at=None,
            updated_at=now,
        )
