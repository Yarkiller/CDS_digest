"""YouTube captions adapter — injected SDK client (CAP-01, D-06…D-09, D-17)."""

from __future__ import annotations

import asyncio
from typing import Any

from requests.exceptions import RequestException
from youtube_transcript_api import (
    AgeRestricted,
    CouldNotRetrieveTranscript,
    InvalidVideoId,
    IpBlocked,
    NoTranscriptFound,
    PoTokenRequired,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeRequestFailed,
    YouTubeTranscriptApiException,
)

from data_collection.dto.transcript import Transcript
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


def _base_lang(code: object) -> str | None:
    if not isinstance(code, str) or not code:
        return None
    return code.split("-")[0].lower()


def _exception_class(exc: BaseException) -> str:
    return type(exc).__name__


class YouTubeTranscriptAdapter:
    """TranscriptProvider implementation via list-then-pick (ru → en)."""

    def __init__(self, api: Any) -> None:
        self._api = api

    async def get(self, video_id: str) -> Transcript:
        return await asyncio.to_thread(self._fetch, video_id)

    def _fetch(self, video_id: str) -> Transcript:
        try:
            return self._fetch_inner(video_id)
        except CaptionsError:
            raise
        except TranscriptsDisabled as exc:
            raise CaptionsDisabled(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except NoTranscriptFound as exc:
            raise CaptionsUnavailable(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except (VideoUnavailable, InvalidVideoId, AgeRestricted, VideoUnplayable) as exc:
            raise CaptionsVideoUnavailable(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except (IpBlocked, RequestBlocked) as exc:
            raise CaptionsBlocked(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except PoTokenRequired as exc:
            raise CaptionsBotChallenge(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except YouTubeRequestFailed as exc:
            raise CaptionsNetworkError(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except RequestException as exc:
            raise CaptionsNetworkError(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except CouldNotRetrieveTranscript as exc:
            raise CaptionsError(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except YouTubeTranscriptApiException as exc:
            raise CaptionsError(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except (AttributeError, TypeError) as exc:
            raise CaptionsError(
                video_id, exception_class=_exception_class(exc)
            ) from exc

    def _fetch_inner(self, video_id: str) -> Transcript:
        tracks = list(self._api.list(video_id))
        if not tracks:
            raise CaptionsUnavailable(video_id)

        chosen = None
        language = None
        for preferred in ("ru", "en"):
            for track in tracks:
                if _base_lang(getattr(track, "language_code", None)) == preferred:
                    chosen = track
                    language = preferred
                    break
            if chosen is not None:
                break

        if chosen is None or language is None:
            available = sorted(
                {
                    code
                    for t in tracks
                    if isinstance((code := getattr(t, "language_code", None)), str)
                }
            )
            raise CaptionsNoPreferredLanguage(
                video_id=video_id,
                available_languages=available,
            )

        snippets = chosen.fetch()
        joined = " ".join(getattr(s, "text", str(s)) for s in snippets)
        joined = " ".join(joined.split())
        if not joined:
            raise CaptionsEmpty(video_id=video_id)

        return Transcript(text=joined, language=language, video_id=video_id)
