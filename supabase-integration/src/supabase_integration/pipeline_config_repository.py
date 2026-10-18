"""PipelineConfigRepository adapter — singleton pipeline_config row via injected client.

PIPE-03 (D-08/D-10/D-11): the config is a single global row ``id = 1`` holding the raw
YAML document + ``updated_at``. Reads reuse the ``_parse_dt``/``_iso`` timestamp helpers
established in ``shortlist_repository`` (copied verbatim — no new timestamp format).
SDK failures are mapped to ``PersistenceError`` at this adapter boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from backend.domain.errors import PersistenceError
from backend.domain.pipeline_config import PipelineConfig

_CONFIG_ID = 1


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


class SupabasePipelineConfigRepository:
    """PipelineConfigRepository against the pipeline_config singleton (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def get(self) -> PipelineConfig | None:
        try:
            result = (
                self._client.table("pipeline_config")
                .select("yaml,updated_at")
                .eq("id", _CONFIG_ID)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"pipeline_config get failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        row = rows[0]
        return PipelineConfig(
            yaml=str(row.get("yaml") or ""),
            updated_at=_parse_dt(row.get("updated_at")),
        )

    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig:
        try:
            (
                self._client.table("pipeline_config")
                .upsert({"id": _CONFIG_ID, "yaml": yaml, "updated_at": _iso(updated_at)})
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"pipeline_config save failed: {exc}") from exc
        return PipelineConfig(yaml=yaml, updated_at=updated_at)
