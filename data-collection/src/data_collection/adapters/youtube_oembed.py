"""YouTube oEmbed adapter — injected httpx client (D-21…D-23, D-17)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from data_collection.dto.video_metadata import VideoMetadata
from data_collection.errors.metadata import (
    MetadataError,
    MetadataInvalidResponse,
    MetadataNetworkError,
    MetadataUnavailable,
)

_OEMBED_ENDPOINT = "https://www.youtube.com/oembed"


def _canonical_watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _exception_class(exc: BaseException) -> str:
    return type(exc).__name__


class YouTubeOEmbedAdapter:
    """VideoMetadataProvider via YouTube oEmbed; builds canonical URL itself."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def get(self, video_id: str) -> VideoMetadata:
        canonical = _canonical_watch_url(video_id)
        try:
            response = await self._client.get(
                _OEMBED_ENDPOINT,
                params={"url": canonical, "format": "json"},
            )
        except MetadataError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise MetadataNetworkError(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except httpx.HTTPError as exc:
            raise MetadataNetworkError(
                video_id, exception_class=_exception_class(exc)
            ) from exc

        if response.status_code in (404, 403):
            raise MetadataUnavailable(
                video_id, status_code=response.status_code
            )

        if response.status_code == 429 or response.status_code >= 500:
            raise MetadataNetworkError(
                video_id, status_code=response.status_code
            )

        if response.status_code != 200:
            raise MetadataUnavailable(
                video_id, status_code=response.status_code
            )

        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            raise MetadataInvalidResponse(
                video_id, exception_class=_exception_class(exc)
            ) from exc

        if not isinstance(payload, dict):
            raise MetadataInvalidResponse(video_id)

        author_raw = payload.get("author_name")
        if not isinstance(author_raw, str) or not author_raw.strip():
            raise MetadataInvalidResponse(video_id)

        return VideoMetadata(
            video_id=video_id,
            source_url=canonical,
            author=author_raw.strip(),
            published_at=None,
        )
