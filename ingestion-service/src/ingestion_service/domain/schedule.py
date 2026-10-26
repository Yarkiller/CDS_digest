"""Pure schedule/cursor helpers — due_decision + is_newer / advance / select_window.

ING-05/06. Timezone is injected (tzinfo); this module never imports the IANA
timezone provider and never reads the wall clock itself (D-22, Pitfall 24-3).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, time, tzinfo

from data_collection.dto.video_ref import VideoRef

Cursor = tuple[datetime, str]


@dataclass(frozen=True)
class IngestionSchedule:
    enabled: bool
    time_of_day: time
    days_of_week: tuple[int, ...]
    last_run_at: datetime | None


@dataclass(frozen=True)
class DueDecision:
    due: bool
    reason: str


def due_decision(
    schedule: IngestionSchedule,
    *,
    now_utc: datetime,
    tz: tzinfo,
) -> DueDecision:
    """D-21/D-22: due if enabled, allowed day, time reached, and not already stamped today.

    Check order: enabled → day → time → last_run_at < today's target.
    ``now_utc`` must be timezone-aware (naive → ValueError).
    """
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    if not schedule.enabled:
        return DueDecision(due=False, reason="disabled")
    local_now = now_utc.astimezone(tz)
    if local_now.isoweekday() not in schedule.days_of_week:
        return DueDecision(due=False, reason="day")
    # Europe/Moscow has no DST since 2014; combine is unambiguous for that zone.
    target = datetime.combine(local_now.date(), schedule.time_of_day, tzinfo=tz)
    if local_now < target:
        return DueDecision(due=False, reason="before_time")
    if schedule.last_run_at is None:
        return DueDecision(due=True, reason="ok")
    if schedule.last_run_at.astimezone(tz) < target:
        return DueDecision(due=True, reason="ok")
    return DueDecision(due=False, reason="already_ran")


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
