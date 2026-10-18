"""CollectSourceReader port — enabled ingest sources + cursor advance (ING-02/05)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


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

    def advance_cursor(
        self, source_pk: int, *, published: datetime, video_id: str
    ) -> None: ...
