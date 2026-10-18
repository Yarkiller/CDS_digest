"""RED→GREEN: YouTube Atom feed adapter — parse + list_recent (ING-02, D-24…D-26)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
import pytest

CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSMdItQ"
VIDEO_ID = "dQw4w9WgXcQ"
PUBLISHED = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)

_ATOM_FEED = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/">
  <title>Example Channel</title>
  <entry>
    <id>yt:video:dQw4w9WgXcQ</id>
    <yt:videoId>dQw4w9WgXcQ</yt:videoId>
    <title>Never Gonna Give You Up</title>
    <published>2026-10-17T09:00:00+00:00</published>
    <media:group>
      <media:title>Nested title must not win</media:title>
    </media:group>
  </entry>
</feed>
"""


def test_parse_feed_happy_path_one_video() -> None:
    from data_collection.adapters.youtube_feed import parse_feed
    from data_collection.dto.video_ref import FeedListing, VideoRef

    listing = parse_feed(_ATOM_FEED, source_id=CHANNEL_ID)
    assert isinstance(listing, FeedListing)
    assert listing.skipped == ()
    assert listing.videos == (VideoRef(VIDEO_ID, PUBLISHED),)
    assert listing.videos[0].published.tzinfo is not None


def test_list_recent_channel_sends_channel_id_query() -> None:
    from data_collection.adapters.youtube_feed import YouTubeFeedAdapter
    from data_collection.dto.video_ref import VideoRef

    captured: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.url)
        return httpx.Response(200, content=_ATOM_FEED)

    async def _run() -> None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = YouTubeFeedAdapter(client)
            listing = await adapter.list_recent(kind="channel", source_id=CHANNEL_ID)
        assert listing.videos == (VideoRef(VIDEO_ID, PUBLISHED),)
        assert len(captured) == 1
        assert captured[0].host == "www.youtube.com"
        assert captured[0].path == "/feeds/videos.xml"
        assert captured[0].params.get("channel_id") == CHANNEL_ID
        assert "playlist_id" not in captured[0].params

    asyncio.run(_run())


def test_list_recent_playlist_sends_playlist_id_query() -> None:
    from data_collection.adapters.youtube_feed import YouTubeFeedAdapter

    playlist_id = "PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    captured: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.url)
        return httpx.Response(200, content=_ATOM_FEED)

    async def _run() -> None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = YouTubeFeedAdapter(client)
            await adapter.list_recent(kind="playlist", source_id=playlist_id)
        assert captured[0].params.get("playlist_id") == playlist_id
        assert "channel_id" not in captured[0].params

    asyncio.run(_run())


def test_list_recent_non_200_raises_feed_status() -> None:
    from data_collection.adapters.youtube_feed import YouTubeFeedAdapter
    from data_collection.errors.feed import FeedError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"not found")

    async def _run() -> None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = YouTubeFeedAdapter(client)
            with pytest.raises(FeedError) as exc_info:
                await adapter.list_recent(kind="channel", source_id=CHANNEL_ID)
        err = exc_info.value
        assert err.reason == "feed_status"
        assert err.status_code == 404
        assert err.source_id == CHANNEL_ID

    asyncio.run(_run())


def test_list_recent_unsupported_kind_raises() -> None:
    from data_collection.adapters.youtube_feed import YouTubeFeedAdapter
    from data_collection.errors.feed import FeedError

    async def _run() -> None:
        transport = httpx.MockTransport(lambda r: httpx.Response(200, content=_ATOM_FEED))
        async with httpx.AsyncClient(transport=transport) as client:
            adapter = YouTubeFeedAdapter(client)
            with pytest.raises(FeedError) as exc_info:
                await adapter.list_recent(kind="user", source_id="someone")
        assert exc_info.value.reason == "unsupported_kind"

    asyncio.run(_run())


def test_adapter_does_not_read_environ() -> None:
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "data-collection"
        / "src"
        / "data_collection"
        / "adapters"
        / "youtube_feed.py"
    )
    assert path.is_file(), "youtube_feed.py must exist"
    body = path.read_text(encoding="utf-8")
    assert "os.environ" not in body
    assert "os.getenv" not in body
