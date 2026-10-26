"""TranscriptProvider port — captions by video_id (D-15)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.transcript import Transcript


class TranscriptProvider(Protocol):
    async def get(self, video_id: str) -> Transcript: ...
