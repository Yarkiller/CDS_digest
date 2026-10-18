"""RED→GREEN: YouTubeOEmbedAdapter + MetadataError taxonomy (D-21…D-25, D-17)."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest


VIDEO_ID = "dQw4w9WgXcQ"
CANONICAL = f"https://www.youtube.com/watch?v={VIDEO_ID}"
OEMBED_URL = "https://www.youtube.com/oembed"


class _StubResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        payload: dict[str, Any] | None = None,
        text: str = "",
        json_error: bool = False,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self._json_error = json_error

    def json(self) -> dict[str, Any]:
        if self._json_error:
            raise json.JSONDecodeError("Expecting value", self.text or "x", 0)
        if self._payload is None:
            raise json.JSONDecodeError("Expecting value", "", 0)
        return self._payload


class _StubClient:
    def __init__(self, response: _StubResponse | BaseException) -> None:
        self._response = response
        self.calls: list[tuple[str, dict[str, str] | None]] = []

    async def get(self, url: str, params: dict[str, str] | None = None) -> _StubResponse:
        self.calls.append((url, params))
        if isinstance(self._response, BaseException):
            raise self._response
        return self._response


def test_happy_path_returns_video_metadata_with_canonical_url_and_none_published_at() -> None:
    from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
    from data_collection.dto.video_metadata import VideoMetadata

    client = _StubClient(
        _StubResponse(payload={"author_name": "Rick Astley", "title": "ignored"})
    )
    adapter = YouTubeOEmbedAdapter(client)

    out = asyncio.run(adapter.get(VIDEO_ID))

    assert isinstance(out, VideoMetadata)
    assert out.video_id == VIDEO_ID
    assert out.source_url == CANONICAL
    assert out.author == "Rick Astley"
    assert out.published_at is None
    assert client.calls == [(OEMBED_URL, {"url": CANONICAL, "format": "json"})]


@pytest.mark.parametrize("status_code", [404, 403])
def test_http_404_and_403_raise_metadata_unavailable(status_code: int) -> None:
    from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
    from data_collection.dto.video_metadata import VideoMetadata
    from data_collection.errors.metadata import MetadataUnavailable

    client = _StubClient(_StubResponse(status_code=status_code, text="blocked"))
    adapter = YouTubeOEmbedAdapter(client)

    with pytest.raises(MetadataUnavailable) as exc_info:
        asyncio.run(adapter.get(VIDEO_ID))

    err = exc_info.value
    assert err.video_id == VIDEO_ID
    assert err.context.get("status_code") == status_code
    assert not isinstance(err, VideoMetadata)


@pytest.mark.parametrize("status_code", [429, 500, 502, 503])
def test_http_5xx_and_429_raise_metadata_network_error(status_code: int) -> None:
    from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
    from data_collection.dto.video_metadata import VideoMetadata
    from data_collection.errors.metadata import MetadataNetworkError, MetadataUnavailable

    client = _StubClient(_StubResponse(status_code=status_code, text="upstream"))
    adapter = YouTubeOEmbedAdapter(client)

    with pytest.raises(MetadataNetworkError) as exc_info:
        asyncio.run(adapter.get(VIDEO_ID))

    err = exc_info.value
    assert err.video_id == VIDEO_ID
    assert err.context.get("status_code") == status_code
    assert not isinstance(err, MetadataUnavailable)
    assert not isinstance(err, VideoMetadata)


@pytest.mark.parametrize(
    "exc",
    [
        httpx.TimeoutException("timed out"),
        httpx.ConnectError("conn refused"),
    ],
)
def test_timeout_and_connect_raise_metadata_network_error(exc: BaseException) -> None:
    from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
    from data_collection.dto.video_metadata import VideoMetadata
    from data_collection.errors.metadata import MetadataNetworkError

    client = _StubClient(exc)
    adapter = YouTubeOEmbedAdapter(client)

    with pytest.raises(MetadataNetworkError) as exc_info:
        asyncio.run(adapter.get(VIDEO_ID))

    err = exc_info.value
    assert err.video_id == VIDEO_ID
    assert "exception_class" in err.context
    assert not isinstance(err, VideoMetadata)


def test_non_json_body_raises_metadata_invalid_response() -> None:
    from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
    from data_collection.dto.video_metadata import VideoMetadata
    from data_collection.errors.metadata import MetadataInvalidResponse

    client = _StubClient(
        _StubResponse(status_code=200, text="<html>", json_error=True)
    )
    adapter = YouTubeOEmbedAdapter(client)

    with pytest.raises(MetadataInvalidResponse) as exc_info:
        asyncio.run(adapter.get(VIDEO_ID))

    assert exc_info.value.video_id == VIDEO_ID
    assert not isinstance(exc_info.value, VideoMetadata)


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "no author"},
        {"author_name": ""},
        {"author_name": "   "},
    ],
)
def test_missing_or_blank_author_name_raises_metadata_invalid_response(
    payload: dict[str, Any],
) -> None:
    from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
    from data_collection.dto.video_metadata import VideoMetadata
    from data_collection.errors.metadata import MetadataInvalidResponse

    client = _StubClient(_StubResponse(payload=payload))
    adapter = YouTubeOEmbedAdapter(client)

    with pytest.raises(MetadataInvalidResponse) as exc_info:
        asyncio.run(adapter.get(VIDEO_ID))

    assert exc_info.value.video_id == VIDEO_ID
    assert not isinstance(exc_info.value, VideoMetadata)


def test_failure_paths_never_return_video_metadata() -> None:
    from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
    from data_collection.dto.video_metadata import VideoMetadata
    from data_collection.errors.metadata import (
        MetadataInvalidResponse,
        MetadataNetworkError,
        MetadataUnavailable,
    )

    cases: list[tuple[_StubResponse | BaseException, type[BaseException]]] = [
        (_StubResponse(status_code=404), MetadataUnavailable),
        (_StubResponse(status_code=403), MetadataUnavailable),
        (httpx.TimeoutException("t"), MetadataNetworkError),
        (_StubResponse(payload={"author_name": "  "}), MetadataInvalidResponse),
    ]
    for response, expected in cases:
        adapter = YouTubeOEmbedAdapter(_StubClient(response))
        with pytest.raises(expected) as exc_info:
            out = asyncio.run(adapter.get(VIDEO_ID))
            assert not isinstance(out, VideoMetadata)
        assert not isinstance(exc_info.value, VideoMetadata)


def test_video_metadata_provider_protocol_exists() -> None:
    from data_collection.ports.video_metadata_provider import VideoMetadataProvider
    from data_collection.ports import VideoMetadataProvider as PortsExport

    assert VideoMetadataProvider is PortsExport
    assert hasattr(VideoMetadataProvider, "get")


def test_adapter_accepts_async_mock_client() -> None:
    """Smoke: injected client shape matches httpx.AsyncClient.get."""
    from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
    from data_collection.dto.video_metadata import VideoMetadata

    response = _StubResponse(payload={"author_name": "Author"})
    client = AsyncMock()
    client.get = AsyncMock(return_value=response)
    adapter = YouTubeOEmbedAdapter(client)

    out = asyncio.run(adapter.get(VIDEO_ID))
    assert isinstance(out, VideoMetadata)
    client.get.assert_awaited_once()
