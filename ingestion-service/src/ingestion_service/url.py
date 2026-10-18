"""YouTube URL / bare-id → video_id (CAP-01, D-01…D-05)."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse, urlunparse

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_ALLOWED_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "www.youtu.be",
    }
)


def _safe_url_for_diagnostics(value: str) -> str:
    """Strip userinfo credentials from URL-like diagnostic values."""
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    if parsed.username is None and parsed.password is None:
        return value
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port is not None else ""
    netloc = f"{host}{port}"
    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )


class InvalidYouTubeUrl(Exception):
    """Raised when the input is not an allowlisted YouTube URL or bare id."""

    def __init__(self, reason: str, value: str, **context: object) -> None:
        safe_value = _safe_url_for_diagnostics(value)
        super().__init__(f"{reason}: {safe_value!r}")
        self.reason = reason
        self.value = safe_value
        safe_context = {
            key: _safe_url_for_diagnostics(val) if isinstance(val, str) else val
            for key, val in context.items()
        }
        self.context = {"value": safe_value, **safe_context}


def _id_from_short_link(path: str, value: str) -> str:
    stripped = path.strip("/")
    candidate = stripped.split("/")[0] if stripped else ""
    return _require_id(candidate, value)


def _id_from_watch(query: str, value: str) -> str:
    vids = parse_qs(query).get("v") or []
    if not vids or not vids[0]:
        raise InvalidYouTubeUrl("missing_video_id", value)
    return _require_id(vids[0], value)


def _id_from_youtube_path(path: str, query: str, value: str) -> str:
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        raise InvalidYouTubeUrl("missing_video_id", value)

    head = segments[0].lower()
    # D-02: deferred forms — reject explicitly (allowlist, not silent accept)
    if head in {"live", "v", "e"}:
        raise InvalidYouTubeUrl("not_a_youtube_url", value)
    if head == "watch":
        return _id_from_watch(query, value)
    if head in {"shorts", "embed"}:
        if len(segments) < 2:
            raise InvalidYouTubeUrl("missing_video_id", value)
        return _require_id(segments[1], value)
    # channel / @handle / user / playlist-without-v / unknown paths
    raise InvalidYouTubeUrl("not_a_youtube_url", value)


def extract_video_id(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise InvalidYouTubeUrl("invalid_video_id", value)
    if _ID_RE.fullmatch(raw):
        return raw

    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host not in _ALLOWED_HOSTS:
        raise InvalidYouTubeUrl("not_a_youtube_url", value)
    if host in {"youtu.be", "www.youtu.be"}:
        return _id_from_short_link(parsed.path or "", value)
    return _id_from_youtube_path(parsed.path or "", parsed.query, value)


def _require_id(candidate: str, value: str) -> str:
    if not _ID_RE.fullmatch(candidate):
        raise InvalidYouTubeUrl("invalid_video_id", value, candidate=candidate)
    return candidate
