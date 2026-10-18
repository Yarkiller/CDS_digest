"""VideoListProvider port — recent-window listing for one channel/playlist (ING-02)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.video_ref import FeedListing


class VideoListProvider(Protocol):
    """Recent-window listing for one channel/playlist (ING-02, D-24)."""

    async def list_recent(self, *, kind: str, source_id: str) -> FeedListing: ...
