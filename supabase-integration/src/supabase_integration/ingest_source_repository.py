"""IngestSourceRepository adapter — pipeline_ingest_sources via injected client.

SRC-03 (D-16/D-17/D-21): admin-managed channel/playlist subscriptions live in
``public.pipeline_ingest_sources`` only — never ``ingestion_sources`` (D-16).
Timestamp helpers mirror ``pipeline_config_repository`` (``_parse_dt`` / ``_iso``).
SDK failures map to ``PersistenceError`` at this adapter boundary.
Missing rows on set_enabled/delete raise ``KeyError`` so use-cases map to
``IngestSourceNotFoundError``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from backend.domain.errors import PersistenceError
from backend.domain.ingest_source import IngestSource

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


def _row_to_source(row: dict[str, Any]) -> IngestSource:
    return IngestSource(
        id=int(row["id"]),
        kind=str(row["kind"]),
        source_id=str(row["source_id"]),
        label=row.get("label"),
        is_enabled=bool(row.get("is_enabled", True)),
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


class SupabaseIngestSourceRepository:
    """IngestSourceRepository against pipeline_ingest_sources (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def list(self) -> list[IngestSource]:
        try:
            result = (
                self._client.table(_TABLE)
                .select(
                    "id,kind,source_id,label,is_enabled,created_at,updated_at"
                )
                .order("created_at")
                .order("id")
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"pipeline_ingest_sources list failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        sources = [_row_to_source(row) for row in rows if isinstance(row, dict)]
        return sorted(sources, key=lambda s: (s.created_at, s.id))

    def add(
        self,
        *,
        kind: str,
        source_id: str,
        label: str | None,
        is_enabled: bool = True,
    ) -> IngestSource:
        now = datetime.now(timezone.utc)
        payload = {
            "kind": kind,
            "source_id": source_id,
            "label": label,
            "is_enabled": is_enabled,
            "created_at": _iso(now),
            "updated_at": _iso(now),
        }
        try:
            result = self._client.table(_TABLE).insert(payload).execute()
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"pipeline_ingest_sources add failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            raise PersistenceError("pipeline_ingest_sources insert returned no rows")
        return _row_to_source(rows[0])

    def set_enabled(self, source_id_pk: int, *, is_enabled: bool) -> IngestSource:
        now = datetime.now(timezone.utc)
        try:
            result = (
                self._client.table(_TABLE)
                .update({"is_enabled": is_enabled, "updated_at": _iso(now)})
                .eq("id", source_id_pk)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(
                f"pipeline_ingest_sources set_enabled failed: {exc}"
            ) from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            raise KeyError(f"ingest source {source_id_pk} not found")
        return _row_to_source(rows[0])

    def delete(self, source_id_pk: int) -> None:
        try:
            result = (
                self._client.table(_TABLE).delete().eq("id", source_id_pk).execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(
                f"pipeline_ingest_sources delete failed: {exc}"
            ) from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            raise KeyError(f"ingest source {source_id_pk} not found")
