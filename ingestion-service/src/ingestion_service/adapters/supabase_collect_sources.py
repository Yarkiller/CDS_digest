"""SupabaseCollectSourceReader — pipeline_ingest_sources via injected client."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from ingestion_service.application.ports.collect_sources import (
    CollectSourceError,
    EnabledSource,
)

_TABLE = "pipeline_ingest_sources"


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
