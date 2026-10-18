"""RED→GREEN: YouTubeTranscriptAdapter mocked SDK (CAP-01/02, D-06…D-09, D-17)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout
from youtube_transcript_api import (
    AgeRestricted,
    CouldNotRetrieveTranscript,
    FailedToCreateConsentCookie,
    InvalidVideoId,
    IpBlocked,
    NoTranscriptFound,
    PoTokenRequired,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeDataUnparsable,
    YouTubeRequestFailed,
)
from youtube_transcript_api._errors import CookieInvalid


VIDEO_ID = "dQw4w9WgXcQ"


class _Snippet:
    def __init__(self, text: str) -> None:
        self.text = text


class _Track:
    def __init__(self, language_code: str, texts: list[str]) -> None:
        self.language_code = language_code
        self._texts = texts

    def fetch(self) -> list[_Snippet]:
        return [_Snippet(t) for t in self._texts]


class _FakeApi:
    def __init__(self, tracks: list[_Track]) -> None:
        self._tracks = tracks
        self.listed_ids: list[str] = []

    def list(self, video_id: str) -> list[_Track]:
        self.listed_ids.append(video_id)
        return list(self._tracks)


def test_adapter_prefers_ru_over_en_and_returns_transcript() -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter
    from data_collection.dto.transcript import Transcript

    api = _FakeApi(
        [
            _Track("en", ["hello"]),
            _Track("ru", ["привет"]),
        ]
    )
    adapter = YouTubeTranscriptAdapter(api)

    out = asyncio.run(adapter.get(VIDEO_ID))

    assert isinstance(out, Transcript)
    assert out.language == "ru"
    assert out.video_id == VIDEO_ID
    assert "привет" in out.text
    assert api.listed_ids == [VIDEO_ID]


def test_adapter_joins_multi_snippet_text_with_spaces() -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter

    api = _FakeApi([_Track("en", ["Hello", "world"])])
    adapter = YouTubeTranscriptAdapter(api)

    out = asyncio.run(adapter.get(VIDEO_ID))

    assert out.text == "Hello world"


def test_adapter_normalizes_ru_ru_dialect_to_ru() -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter

    api = _FakeApi([_Track("ru-RU", ["текст"])])
    adapter = YouTubeTranscriptAdapter(api)

    out = asyncio.run(adapter.get(VIDEO_ID))
    assert out.language == "ru"


def test_adapter_normalizes_en_us_dialect_to_en() -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter

    api = _FakeApi([_Track("en-US", ["text"])])
    adapter = YouTubeTranscriptAdapter(api)

    out = asyncio.run(adapter.get(VIDEO_ID))
    assert out.language == "en"


def test_adapter_rejects_rue_and_enm_as_no_preferred_language() -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter
    from data_collection.errors.captions import CaptionsNoPreferredLanguage

    api = _FakeApi(
        [
            _Track("rue", ["x"]),
            _Track("enm", ["y"]),
        ]
    )
    adapter = YouTubeTranscriptAdapter(api)

    with pytest.raises(CaptionsNoPreferredLanguage) as exc_info:
        asyncio.run(adapter.get(VIDEO_ID))

    err = exc_info.value
    assert err.video_id == VIDEO_ID
    assert "rue" in err.available_languages
    assert "enm" in err.available_languages


def test_adapter_raises_captions_empty_without_constructing_transcript() -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter
    from data_collection.errors.captions import CaptionsEmpty

    api = _FakeApi([_Track("ru", ["   ", "\n"])])
    adapter = YouTubeTranscriptAdapter(api)

    with patch(
        "data_collection.adapters.youtube_transcript.Transcript"
    ) as mock_transcript:
        with pytest.raises(CaptionsEmpty) as exc_info:
            asyncio.run(adapter.get(VIDEO_ID))
        mock_transcript.assert_not_called()

    assert exc_info.value.video_id == VIDEO_ID


def test_adapter_constructor_has_no_environ_reads() -> None:
    import inspect

    from data_collection.adapters import youtube_transcript as mod

    source = inspect.getsource(mod)
    assert "os.environ" not in source
    assert "os.getenv" not in source


class _RaisingApi:
    """Stub api whose list() raises a scripted exception (CAP-02 / D-12)."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def list(self, video_id: str) -> list[_Track]:
        raise self._exc


def _youtube_request_failed(video_id: str) -> YouTubeRequestFailed:
    return YouTubeRequestFailed(video_id, HTTPError())


def _no_transcript_found(video_id: str) -> NoTranscriptFound:
    return NoTranscriptFound(video_id, ["ru", "en"], MagicMock())


def _video_unplayable(video_id: str) -> VideoUnplayable:
    return VideoUnplayable(video_id, "unplayable", [])


@pytest.mark.parametrize(
    ("sdk_exc", "expected_type", "sdk_name"),
    [
        (TranscriptsDisabled(VIDEO_ID), "CaptionsDisabled", "TranscriptsDisabled"),
        (
            _no_transcript_found(VIDEO_ID),
            "CaptionsUnavailable",
            "NoTranscriptFound",
        ),
        (VideoUnavailable(VIDEO_ID), "CaptionsVideoUnavailable", "VideoUnavailable"),
        (InvalidVideoId(VIDEO_ID), "CaptionsVideoUnavailable", "InvalidVideoId"),
        (AgeRestricted(VIDEO_ID), "CaptionsVideoUnavailable", "AgeRestricted"),
        (
            _video_unplayable(VIDEO_ID),
            "CaptionsVideoUnavailable",
            "VideoUnplayable",
        ),
        (IpBlocked(VIDEO_ID), "CaptionsBlocked", "IpBlocked"),
        (RequestBlocked(VIDEO_ID), "CaptionsBlocked", "RequestBlocked"),
        (PoTokenRequired(VIDEO_ID), "CaptionsBotChallenge", "PoTokenRequired"),
        (
            _youtube_request_failed(VIDEO_ID),
            "CaptionsNetworkError",
            "YouTubeRequestFailed",
        ),
        (Timeout("timed out"), "CaptionsNetworkError", "Timeout"),
        (
            RequestsConnectionError("conn refused"),
            "CaptionsNetworkError",
            "ConnectionError",
        ),
        (
            YouTubeDataUnparsable(VIDEO_ID),
            "CaptionsError",
            "YouTubeDataUnparsable",
        ),
        (
            FailedToCreateConsentCookie(VIDEO_ID),
            "CaptionsError",
            "FailedToCreateConsentCookie",
        ),
        (
            CookieInvalid("bad-cookie-path"),
            "CaptionsError",
            "CookieInvalid",
        ),
    ],
)
def test_adapter_maps_sdk_exception_to_captions_subtype(
    sdk_exc: BaseException, expected_type: str, sdk_name: str
) -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter
    from data_collection.errors import captions as captions_errors

    expected_cls = getattr(captions_errors, expected_type)
    adapter = YouTubeTranscriptAdapter(_RaisingApi(sdk_exc))

    with patch(
        "data_collection.adapters.youtube_transcript.Transcript"
    ) as mock_transcript:
        with pytest.raises(expected_cls) as exc_info:
            asyncio.run(adapter.get(VIDEO_ID))
        mock_transcript.assert_not_called()

    err = exc_info.value
    assert err.video_id == VIDEO_ID
    assert err.context.get("exception_class") == sdk_name
    assert type(err) is expected_cls
    assert not isinstance(err, CouldNotRetrieveTranscript)
    assert not isinstance(err, RequestException)
    from youtube_transcript_api import YouTubeTranscriptApiException

    assert not isinstance(err, YouTubeTranscriptApiException)
    if expected_type == "CaptionsBlocked":
        assert not isinstance(err, captions_errors.CaptionsDisabled)
        assert not isinstance(err, captions_errors.CaptionsUnavailable)
        assert not isinstance(err, captions_errors.CaptionsBotChallenge)
    if expected_type == "CaptionsBotChallenge":
        assert not isinstance(err, captions_errors.CaptionsDisabled)
        assert not isinstance(err, captions_errors.CaptionsUnavailable)
        assert not isinstance(err, captions_errors.CaptionsBlocked)
    if expected_type == "CaptionsNetworkError":
        assert type(err) is captions_errors.CaptionsNetworkError


def test_adapter_empty_track_list_raises_captions_unavailable() -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter
    from data_collection.errors.captions import CaptionsUnavailable

    adapter = YouTubeTranscriptAdapter(_FakeApi([]))

    with patch(
        "data_collection.adapters.youtube_transcript.Transcript"
    ) as mock_transcript:
        with pytest.raises(CaptionsUnavailable) as exc_info:
            asyncio.run(adapter.get(VIDEO_ID))
        mock_transcript.assert_not_called()

    assert exc_info.value.video_id == VIDEO_ID


def test_adapter_none_language_code_maps_to_captions_error() -> None:
    from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter
    from data_collection.errors.captions import CaptionsError

    track = _Track("en", ["hello"])
    track.language_code = None  # type: ignore[assignment]
    adapter = YouTubeTranscriptAdapter(_FakeApi([track]))

    with pytest.raises(CaptionsError) as exc_info:
        asyncio.run(adapter.get(VIDEO_ID))

    err = exc_info.value
    assert err.video_id == VIDEO_ID
    assert not isinstance(err, AttributeError)


def test_captions_taxonomy_subtypes_inherit_and_store_video_id() -> None:
    from data_collection.errors.captions import (
        CaptionsBlocked,
        CaptionsBotChallenge,
        CaptionsDisabled,
        CaptionsEmpty,
        CaptionsError,
        CaptionsNetworkError,
        CaptionsNoPreferredLanguage,
        CaptionsUnavailable,
        CaptionsVideoUnavailable,
    )

    cases: list[tuple[type[CaptionsError], CaptionsError]] = [
        (CaptionsUnavailable, CaptionsUnavailable(VIDEO_ID)),
        (CaptionsDisabled, CaptionsDisabled(VIDEO_ID)),
        (CaptionsBlocked, CaptionsBlocked(VIDEO_ID)),
        (CaptionsBotChallenge, CaptionsBotChallenge(VIDEO_ID)),
        (CaptionsVideoUnavailable, CaptionsVideoUnavailable(VIDEO_ID)),
        (
            CaptionsNoPreferredLanguage,
            CaptionsNoPreferredLanguage(VIDEO_ID, ["de"]),
        ),
        (CaptionsNetworkError, CaptionsNetworkError(VIDEO_ID)),
        (CaptionsEmpty, CaptionsEmpty(VIDEO_ID)),
    ]
    for cls, instance in cases:
        assert isinstance(instance, CaptionsError)
        assert type(instance) is cls
        assert instance.video_id == VIDEO_ID
