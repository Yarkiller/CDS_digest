"""CollectSourceReader port — sources, schedule, cursor, last_run (ING-02/05/06)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ingestion_service.domain.schedule import IngestionSchedule


@dataclass(frozen=True)
class EnabledSource:
    id: int
    kind: str
    source_id: str
    last_seen_published_at: datetime | None
    last_seen_video_id: str | None


class CollectSourceError(Exception):
    """SDK/DB failure at the collect-source adapter boundary."""


class CollectSourceReader(Protocol):
    def list_enabled_sources(self) -> list[EnabledSource]: ...

    def get_schedule(self) -> IngestionSchedule: ...

    def stamp_last_run(self, at: datetime) -> None: ...

    def advance_cursor(
        self, source_pk: int, *, published: datetime, video_id: str
    ) -> None: ...
