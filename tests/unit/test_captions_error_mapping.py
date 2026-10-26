"""RED→GREEN: CaptionsError → IngestError(stage=captions) locked reasons (CAP-02, D-10, D-13)."""

from __future__ import annotations

import pytest
from youtube_transcript_api import (
    AgeRestricted,
    CouldNotRetrieveTranscript,
    IpBlocked,
    NoTranscriptFound,
    PoTokenRequired,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeRequestFailed,
)

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


VIDEO_ID = "dQw4w9WgXcQ"

LOCKED_REASONS = frozenset(
    {
        "no_captions",
        "no_preferred_language",
        "captions_disabled",
        "video_unavailable",
        "youtube_blocked",
        "bot_challenge",
        "network_error",
        "empty_captions",
        "unknown_captions_error",
    }
)

SDK_EXCEPTION_NAMES = frozenset(
    {
        TranscriptsDisabled.__name__,
        NoTranscriptFound.__name__,
        VideoUnavailable.__name__,
        VideoUnplayable.__name__,
        AgeRestricted.__name__,
        IpBlocked.__name__,
        RequestBlocked.__name__,
        PoTokenRequired.__name__,
        YouTubeRequestFailed.__name__,
        CouldNotRetrieveTranscript.__name__,
    }
)


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (CaptionsUnavailable(VIDEO_ID), "no_captions"),
        (
            CaptionsNoPreferredLanguage(VIDEO_ID, ["de", "es"]),
            "no_preferred_language",
        ),
        (CaptionsDisabled(VIDEO_ID), "captions_disabled"),
        (CaptionsVideoUnavailable(VIDEO_ID), "video_unavailable"),
        (CaptionsBlocked(VIDEO_ID), "youtube_blocked"),
        (CaptionsBotChallenge(VIDEO_ID), "bot_challenge"),
        (CaptionsNetworkError(VIDEO_ID), "network_error"),
        (CaptionsEmpty(VIDEO_ID), "empty_captions"),
        (CaptionsError(VIDEO_ID), "unknown_captions_error"),
    ],
)
def test_map_captions_error_subtype_to_locked_reason(
    error: CaptionsError, reason: str
) -> None:
    from ingestion_service.mapping.captions import map_captions_error

    mapped = map_captions_error(error)

    assert mapped.stage == "captions"
    assert mapped.reason == reason
    assert mapped.message == f"captions {reason} for {VIDEO_ID}"
    assert mapped.context.get("video_id") == VIDEO_ID
    payload = mapped.to_dict()
    assert payload["ok"] is False
    assert payload["stage"] == "captions"
    assert payload["exit_code"] == 1
    assert payload["message"] == mapped.message


def test_locked_reason_set_equals_d10_exactly() -> None:
    from ingestion_service.mapping import captions as captions_mapping

    assert frozenset(captions_mapping.CAPTIONS_REASONS) == LOCKED_REASONS


def test_no_reason_equals_sdk_exception_class_name() -> None:
    from ingestion_service.mapping import captions as captions_mapping

    assert LOCKED_REASONS.isdisjoint(SDK_EXCEPTION_NAMES)
    assert frozenset(captions_mapping.CAPTIONS_REASONS).isdisjoint(SDK_EXCEPTION_NAMES)


def test_map_captions_error_redacts_credentialed_proxy_context() -> None:
    from ingestion_service.mapping.captions import map_captions_error

    error = CaptionsNetworkError(
        VIDEO_ID,
        exception_class="Timeout",
        proxy_url="socks5://user:secret@192.168.1.68:1080",
        YOUTUBE_PROXY_URL="socks5://user:secret@192.168.1.68:1080",
    )

    mapped = map_captions_error(error)
    payload = mapped.to_dict()

    assert mapped.context.get("video_id") == VIDEO_ID
    assert mapped.context.get("exception_class") == "Timeout"
    assert "proxy_url" not in mapped.context
    assert "YOUTUBE_PROXY_URL" not in mapped.context
    assert "secret" not in str(mapped.context)
    assert "socks5://" not in str(mapped.context)
    assert "secret" not in mapped.message
    assert "socks5://" not in mapped.message
    assert "secret" not in payload["message"]
    assert "socks5://" not in payload["message"]
    assert "secret" not in str(error)
    assert "socks5://" not in str(error)


def test_map_captions_error_cookie_invalid_message_is_reason_and_video_id_only() -> None:
    """D-01, D-03, D-04: CookieInvalid path → unknown_captions_error; SDK text discarded."""
    from ingestion_service.mapping.captions import map_captions_error

    sdk_leak = (
        "CookieInvalid: https://user:proxy-secret@192.168.1.68:1080 "
        "could not load cookies from /tmp/cookies.txt"
    )
    error = CaptionsError(
        VIDEO_ID,
        exception_class="CookieInvalid",
        sdk_message=sdk_leak,
        raw_url="https://user:proxy-secret@youtube.com/api",
    )

    mapped = map_captions_error(error)

    assert mapped.reason == "unknown_captions_error"
    assert mapped.message == f"captions unknown_captions_error for {VIDEO_ID}"
    assert mapped.context.get("exception_class") == "CookieInvalid"
    assert "sdk_message" not in mapped.context
    assert "raw_url" not in mapped.context
    assert "proxy-secret" not in mapped.message
    assert "proxy-secret" not in str(mapped.context)
    assert "cookies.txt" not in mapped.message
    assert "https://" not in mapped.message


def test_captions_context_allowlist_frozen() -> None:
    """D-02: captions diagnostic context allowlist stays Phase-7 locked."""
    from ingestion_service.mapping import captions as captions_mapping

    assert frozenset(captions_mapping._CONTEXT_ALLOWLIST) == frozenset(
        {
            "video_id",
            "available_languages",
            "exception_class",
        }
    )


def test_map_captions_error_forwards_available_languages() -> None:
    from ingestion_service.mapping.captions import map_captions_error

    error = CaptionsNoPreferredLanguage(VIDEO_ID, ["de", "es"])
    mapped = map_captions_error(error)
    assert mapped.context.get("available_languages") == ["de", "es"]


def test_roadmap_records_cap02_live_persist_spy_deferral() -> None:
    """CAP-02 / D-14 deferral lives on the archived v1.1 roadmap (not live ROADMAP)."""
    from pathlib import Path

    roadmap = Path(".planning/milestones/v1.1-ROADMAP.md").read_text(encoding="utf-8")
    phase9 = roadmap.split("### Phase 9:")[1].split("### Phase 10:")[0]
    assert "persist.calls == []" in phase9
    assert "CAP-02" in phase9 or "D-14" in phase9
