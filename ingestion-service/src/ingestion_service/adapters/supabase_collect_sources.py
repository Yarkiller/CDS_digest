"""SupabaseCollectSourceReader — pipeline_ingest_sources + ingestion_schedule."""

from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any, Protocol

from ingestion_service.application.ports.collect_sources import (
    CollectSourceError,
    EnabledSource,
)
from ingestion_service.domain.schedule import IngestionSchedule

_TABLE = "pipeline_ingest_sources"
_SCHEDULE_TABLE = "ingestion_schedule"

_DEFAULT_SCHEDULE = IngestionSchedule(
    enabled=True,
    time_of_day=time(6, 0),
    days_of_week=(1, 2, 3, 4, 5, 6, 7),
    last_run_at=None,
)


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _row_to_enabled(row: dict[str, Any]) -> EnabledSource:
    raw_published = row.get("last_seen_published_at")
    return EnabledSource(
        id=int(row["id"]),
        kind=str(row["kind"]),
        source_id=str(row["source_id"]),
        last_seen_published_at=(
            _parse_dt(raw_published) if raw_published is not None else None
        ),
        last_seen_video_id=(
            str(row["last_seen_video_id"])
            if row.get("last_seen_video_id") is not None
            else None
        ),
    )


class SupabaseCollectSourceReader:
    """CollectSourceReader against pipeline_ingest_sources (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def list_enabled_sources(self) -> list[EnabledSource]:
        try:
            result = (
                self._client.table(_TABLE)
                .select(
                    "id,kind,source_id,last_seen_published_at,last_seen_video_id"
                )
                .eq("is_enabled", True)
                .order("created_at")
                .execute()
            )
        except CollectSourceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise CollectSourceError(
                f"pipeline_ingest_sources list_enabled failed: {exc}"
            ) from exc

        rows = getattr(result, "data", None) or []
        return [
            _row_to_enabled(row) for row in rows if isinstance(row, dict)
        ]

    def advance_cursor(
        self, source_pk: int, *, published: datetime, video_id: str
    ) -> None:
        try:
            (
                self._client.table(_TABLE)
                .update(
                    {
                        "last_seen_published_at": _iso(published),
                        "last_seen_video_id": video_id,
                    }
                )
                .eq("id", source_pk)
                .execute()
            )
        except CollectSourceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise CollectSourceError(
                f"pipeline_ingest_sources advance_cursor failed: {exc}"
            ) from exc

    def get_schedule(self) -> IngestionSchedule:
        try:
            result = (
                self._client.table(_SCHEDULE_TABLE)
                .select("enabled,time_of_day,days_of_week,last_run_at")
                .eq("id", 1)
                .execute()
            )
        except CollectSourceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise CollectSourceError(
                f"ingestion_schedule get_schedule failed: {exc}"
            ) from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return _DEFAULT_SCHEDULE
        row = rows[0]
        if not isinstance(row, dict):
            return _DEFAULT_SCHEDULE
        return _row_to_schedule(row)

    def stamp_last_run(self, at: datetime) -> None:
        try:
            (
                self._client.table(_SCHEDULE_TABLE)
                .upsert(
                    {
                        "id": 1,
                        "last_run_at": _iso(at),
                        "updated_at": _iso(at),
                    },
                    on_conflict="id",
                )
                .execute()
            )
        except CollectSourceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise CollectSourceError(
                f"ingestion_schedule stamp_last_run failed: {exc}"
            ) from exc


def _parse_time_of_day(value: Any) -> time:
    if isinstance(value, time):
        return value
    text = str(value)
    # Postgres may return "06:00:00" or "06:00".
    return time.fromisoformat(text)


def _row_to_schedule(row: dict[str, Any]) -> IngestionSchedule:
    raw_days = row.get("days_of_week") or ()
    days = tuple(int(d) for d in raw_days)
    raw_last = row.get("last_run_at")
    return IngestionSchedule(
        enabled=bool(row.get("enabled", True)),
        time_of_day=_parse_time_of_day(row.get("time_of_day", "06:00")),
        days_of_week=days if days else _DEFAULT_SCHEDULE.days_of_week,
        last_run_at=_parse_dt(raw_last) if raw_last is not None else None,
    )
