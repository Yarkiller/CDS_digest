"""VideoRef / FeedListing DTOs — Atom feed listing results (ING-02)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VideoRef:
    video_id: str
    published: datetime  # tz-aware, normalized to UTC


@dataclass(frozen=True)
class FeedSkip:
    video_id: str | None
    reason: str


@dataclass(frozen=True)
class FeedListing:
    videos: tuple[VideoRef, ...]
    skipped: tuple[FeedSkip, ...]
