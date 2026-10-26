"""VideoMetadataProvider port — provenance by video_id (D-21, D-22)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.video_metadata import VideoMetadata


class VideoMetadataProvider(Protocol):
    async def get(self, video_id: str) -> VideoMetadata: ...
