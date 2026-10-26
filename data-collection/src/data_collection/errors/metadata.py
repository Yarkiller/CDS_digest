"""Metadata adapter errors — module-local taxonomy only (D-11, D-25)."""

from __future__ import annotations

from typing import Any


class MetadataError(Exception):
    """Base metadata failure at the adapter boundary."""

    def __init__(self, video_id: str, **context: Any) -> None:
        self.video_id = video_id
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)
        super().__init__(f"metadata error for {video_id}")


class MetadataUnavailable(MetadataError):
    """oEmbed returned 404/403 or the resource is blocked."""


class MetadataNetworkError(MetadataError):
    """Transport failure while fetching oEmbed (timeout / connection)."""


class MetadataInvalidResponse(MetadataError):
    """Non-JSON body or missing/blank author_name in oEmbed payload."""
