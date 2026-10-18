"""Pure schedule/cursor helpers — is_newer / advance_cursor / select_window (ING-05)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from data_collection.dto.video_ref import VideoRef

Cursor = tuple[datetime, str]


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
    current: Cursor | None,
    candidate: Cursor,
) -> Cursor:
    """Monotonic: only forward (D-07). Same-second ties resolved by video_id."""
    if current is None:
        return candidate
    if candidate > current:
        return candidate
    return current


def select_window(
    videos: Sequence[VideoRef],
    *,
    last_published: datetime | None,
    last_video_id: str | None,
    limit: int,
) -> tuple[tuple[VideoRef, ...], int]:
    """D-05/D-08: sort oldest→newest, filter by cursor, limit cuts newest tail.

    Returns ``(chosen, skipped_by_limit)`` where ``skipped_by_limit`` counts
    records newer than the cursor that were cut by ``limit`` — not records
    filtered by the cursor itself. ``limit <= 0`` yields an empty window.
    """
    if limit <= 0:
        return (), 0
    ordered = sorted(videos, key=lambda v: (v.published, v.video_id))
    newer = tuple(
        v
        for v in ordered
        if is_newer(
            v.published,
            v.video_id,
            last_published=last_published,
            last_video_id=last_video_id,
        )
    )
    chosen = newer[:limit]
    skipped = max(0, len(newer) - limit)
    return tuple(chosen), skipped
