"""Map CaptionsError → IngestError(stage=captions) with locked reasons (D-10, D-13)."""

from __future__ import annotations

from typing import Any

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
from ingestion_service.domain.errors import IngestError

CAPTIONS_REASONS: frozenset[str] = frozenset(
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

_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "video_id",
        "available_languages",
        "exception_class",
    }
)

_REASON_BY_TYPE: dict[type[CaptionsError], str] = {
    CaptionsUnavailable: "no_captions",
    CaptionsNoPreferredLanguage: "no_preferred_language",
    CaptionsDisabled: "captions_disabled",
    CaptionsVideoUnavailable: "video_unavailable",
    CaptionsBlocked: "youtube_blocked",
    CaptionsBotChallenge: "bot_challenge",
    CaptionsNetworkError: "network_error",
    CaptionsEmpty: "empty_captions",
}


def _forward_context(error: CaptionsError) -> dict[str, Any]:
    forwarded: dict[str, Any] = {"video_id": error.video_id}
    raw = dict(error.context)
    for key in _CONTEXT_ALLOWLIST:
        if key == "video_id":
            continue
        if key in raw:
            forwarded[key] = raw[key]
    return forwarded


def map_captions_error(error: CaptionsError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "unknown_captions_error")
    return IngestError(
        stage="captions",
        reason=reason,
        message=f"captions {reason} for {error.video_id}",
        context=_forward_context(error),
    )
