"""YouTube Atom feed adapter — injected httpx client, 1 MiB cap (ING-02, D-24…D-26)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET  # nosec B405 - DOCTYPE/ENTITY rejected before parsing.
from datetime import datetime, timezone
from typing import Any

import httpx

from data_collection.dto.video_ref import FeedListing, FeedSkip, VideoRef
from data_collection.errors.feed import FeedError

_FEED_ENDPOINT = "https://www.youtube.com/feeds/videos.xml"
_MAX_FEED_BYTES = 1024 * 1024  # D-26
_PARAMS = {"channel": "channel_id", "playlist": "playlist_id"}
_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_DTD_MARKERS = (b"<!DOCTYPE", b"<!ENTITY")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _exception_class(exc: BaseException) -> str:
    return type(exc).__name__


def _parse_rfc3339(text: str | None) -> datetime | None:
    if text is None or not text.strip():
        return None
    try:
        parsed = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def parse_feed(raw: bytes, *, source_id: str) -> FeedListing:
    head = raw[:4096].upper()
    if any(marker in head for marker in _DTD_MARKERS):
        raise FeedError(source_id, reason="feed_doctype")

    try:
        root = ET.fromstring(raw)  # nosec B314 - DTD markers rejected above; capped at 1 MiB.
    except ET.ParseError as exc:
        raise FeedError(source_id, reason="feed_invalid_xml") from exc

    videos: list[VideoRef] = []
    skipped: list[FeedSkip] = []
    for entry in root:
        if _local(entry.tag) != "entry":
            continue
        raw_id: str | None = None
        raw_published: str | None = None
        for child in entry:  # direct children only
            name = _local(child.tag)
            if name == "videoId" and child.text:
                raw_id = child.text.strip()
            elif name == "published" and child.text:
                raw_published = child.text.strip()
        if not raw_id or not _VIDEO_ID_RE.fullmatch(raw_id):
            skipped.append(FeedSkip(raw_id, "missing_video_id"))
            continue
        published = _parse_rfc3339(raw_published)
        if published is None:
            skipped.append(FeedSkip(raw_id, "invalid_published"))
            continue
        videos.append(VideoRef(video_id=raw_id, published=published))
    return FeedListing(videos=tuple(videos), skipped=tuple(skipped))


class YouTubeFeedAdapter:
    """VideoListProvider via YouTube Atom feeds/videos.xml."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def list_recent(self, *, kind: str, source_id: str) -> FeedListing:
        raw = await self._read_capped(kind, source_id)
        return parse_feed(raw, source_id=source_id)

    async def _read_capped(self, kind: str, source_id: str) -> bytes:
        if kind not in _PARAMS:
            raise FeedError(source_id, reason="unsupported_kind", kind=kind)
        params = {_PARAMS[kind]: source_id}
        try:
            async with self._client.stream(
                "GET", _FEED_ENDPOINT, params=params
            ) as response:
                if response.status_code != 200:
                    raise FeedError(
                        source_id,
                        reason="feed_status",
                        status_code=response.status_code,
                    )
                declared = response.headers.get("content-length")
                if (
                    declared
                    and declared.isdigit()
                    and int(declared) > _MAX_FEED_BYTES
                ):
                    raise FeedError(
                        source_id,
                        reason="feed_too_large",
                        declared=int(declared),
                    )
                buffer = bytearray()
                async for chunk in response.aiter_bytes():
                    buffer.extend(chunk)
                    if len(buffer) > _MAX_FEED_BYTES:
                        raise FeedError(
                            source_id,
                            reason="feed_too_large",
                            read=len(buffer),
                        )
                return bytes(buffer)
        except FeedError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise FeedError(
                source_id,
                reason="feed_network",
                exception_class=_exception_class(exc),
            ) from exc
        except httpx.HTTPError as exc:
            raise FeedError(
                source_id,
                reason="feed_network",
                exception_class=_exception_class(exc),
            ) from exc
