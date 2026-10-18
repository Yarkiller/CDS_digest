"""Pure schedule/cursor helpers — is_newer / advance_cursor (ING-05, D-07)."""

from __future__ import annotations

from datetime import datetime


def is_newer(
    published: datetime,
    video_id: str,
    *,
    last_published: datetime | None,
    last_video_id: str | None,
) -> bool:
    """D-07: strict '>' on published, video_id as the same-second tie-break."""
    if last_published is None:
        return True
    if published > last_published:
        return True
    if published < last_published:
        return False
    if last_video_id is None:
        return True
    return video_id > last_video_id


def advance_cursor(
    current: tuple[datetime, str] | None,
    candidate: tuple[datetime, str],
) -> tuple[datetime, str]:
    """Monotonic: only forward (D-07). Same-second ties resolved by video_id."""
    if current is None:
        return candidate
    if candidate > current:
        return candidate
    return current
