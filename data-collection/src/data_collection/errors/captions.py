"""Captions adapter errors — module-local taxonomy only (D-11, D-12)."""

from __future__ import annotations

from typing import Any


class CaptionsError(Exception):
    """Base captions failure at the adapter boundary."""

    def __init__(self, video_id: str, **context: Any) -> None:
        self.video_id = video_id
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)
        super().__init__(f"captions error for {video_id}")


class CaptionsUnavailable(CaptionsError):
    """No caption tracks available for the video."""


class CaptionsDisabled(CaptionsError):
    """Subtitles are disabled on the video."""


class CaptionsBlocked(CaptionsError):
    """YouTube blocked the request (IP / request block)."""


class CaptionsBotChallenge(CaptionsError):
    """Bot challenge / PO token required (D-19)."""


class CaptionsVideoUnavailable(CaptionsError):
    """Video missing, invalid, age-restricted, or unplayable."""


class CaptionsNoPreferredLanguage(CaptionsError):
    """Tracks exist but none normalize to ru/en (D-09)."""

    def __init__(self, video_id: str, available_languages: list[str]) -> None:
        super().__init__(video_id, available_languages=list(available_languages))
        self.available_languages = list(available_languages)


class CaptionsNetworkError(CaptionsError):
    """Transport or YouTube HTTP failure while fetching captions."""


class CaptionsEmpty(CaptionsError):
    """Joined caption text is blank after strip (CAP-02)."""

    def __init__(self, video_id: str) -> None:
        super().__init__(video_id)
