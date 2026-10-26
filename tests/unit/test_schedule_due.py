"""RED→GREEN: cursor + due_decision (ING-05/06, D-07, D-05, D-21, D-22)."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from data_collection.dto.video_ref import VideoRef

PUBLISHED = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)
EARLIER = datetime(2026, 10, 17, 8, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 10, 17, 10, 0, tzinfo=timezone.utc)
BASE = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)

# Fixed UTC+3 stands in for Europe/Moscow (no DST) in pure unit tests.
MSK = timezone(timedelta(hours=3))
ALL_DAYS = (1, 2, 3, 4, 5, 6, 7)


def _schedule(
    *,
    enabled: bool = True,
    tod: time = time(6, 0),
    days: tuple[int, ...] = ALL_DAYS,
    last_run_at: datetime | None = None,
):
    from ingestion_service.domain.schedule import IngestionSchedule

    return IngestionSchedule(
        enabled=enabled,
        time_of_day=tod,
        days_of_week=days,
        last_run_at=last_run_at,
    )


def _msk_as_utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    """Build an aware UTC instant that is the given wall clock in MSK."""
    local = datetime(year, month, day, hour, minute, tzinfo=MSK)
    return local.astimezone(timezone.utc)


def _vid(n: int) -> str:
    """11-char YouTube-shaped id, lexicographically ordered by n."""
    return f"vid{n:08d}"


def _feed_15_desc() -> tuple[VideoRef, ...]:
    """15 entries newest-first (Atom order); ages 1..15 oldest→newest by hour."""
    asc = tuple(
        VideoRef(_vid(i), BASE + timedelta(hours=i)) for i in range(1, 16)
    )
    return tuple(reversed(asc))


def test_is_newer_first_run_with_none_cursor() -> None:
    from ingestion_service.domain.schedule import is_newer

    assert is_newer(PUBLISHED, "dQw4w9WgXcQ", last_published=None, last_video_id=None) is True


def test_is_newer_strict_greater_published() -> None:
    from ingestion_service.domain.schedule import is_newer

    assert (
        is_newer(LATER, "aaa", last_published=PUBLISHED, last_video_id="zzz") is True
    )
    assert (
        is_newer(EARLIER, "zzz", last_published=PUBLISHED, last_video_id="aaa") is False
    )


def test_is_newer_same_second_tie_break_by_video_id() -> None:
    from ingestion_service.domain.schedule import is_newer

    assert (
        is_newer(PUBLISHED, "zzz", last_published=PUBLISHED, last_video_id="aaa") is True
    )
    assert (
        is_newer(PUBLISHED, "aaa", last_published=PUBLISHED, last_video_id="zzz") is False
    )


def test_is_newer_same_second_none_tie_break_is_true() -> None:
    from ingestion_service.domain.schedule import is_newer

    assert (
        is_newer(PUBLISHED, "aaa", last_published=PUBLISHED, last_video_id=None) is True
    )


def test_advance_cursor_from_none_takes_candidate() -> None:
    from ingestion_service.domain.schedule import advance_cursor

    candidate = (PUBLISHED, "aaa")
    assert advance_cursor(None, candidate) == candidate


def test_advance_cursor_monotonic_rejects_older_tie_break() -> None:
    from ingestion_service.domain.schedule import advance_cursor

    current = (PUBLISHED, "zzz")
    older = (PUBLISHED, "aaa")
    assert advance_cursor(current, older) == current


def test_advance_cursor_advances_on_newer_candidate() -> None:
    from ingestion_service.domain.schedule import advance_cursor

    current = (PUBLISHED, "aaa")
    newer = (LATER, "bbb")
    assert advance_cursor(current, newer) == newer


def test_select_window_empty_cursor_limit_cuts_newest_tail() -> None:
    """D-05/D-08: first run sees oldest→newest; limit cuts the newest tail."""
    from ingestion_service.domain.schedule import select_window

    chosen, skipped = select_window(
        _feed_15_desc(), last_published=None, last_video_id=None, limit=5
    )
    assert [v.video_id for v in chosen] == [_vid(i) for i in range(1, 6)]
    assert skipped == 10


def test_select_window_cursor_on_tenth_takes_next_five() -> None:
    from ingestion_service.domain.schedule import select_window

    cursor_pub = BASE + timedelta(hours=10)
    chosen, skipped = select_window(
        _feed_15_desc(),
        last_published=cursor_pub,
        last_video_id=_vid(10),
        limit=5,
    )
    assert [v.video_id for v in chosen] == [_vid(i) for i in range(11, 16)]
    assert skipped == 0


def test_select_window_cursor_on_twelfth_limit_two_skips_one() -> None:
    from ingestion_service.domain.schedule import select_window

    cursor_pub = BASE + timedelta(hours=12)
    chosen, skipped = select_window(
        _feed_15_desc(),
        last_published=cursor_pub,
        last_video_id=_vid(12),
        limit=2,
    )
    assert [v.video_id for v in chosen] == [_vid(13), _vid(14)]
    assert skipped == 1


def test_select_window_same_second_tie_break_orders_by_video_id() -> None:
    from ingestion_service.domain.schedule import select_window

    a = VideoRef("aaaaaaaaaaa", PUBLISHED)
    z = VideoRef("zzzzzzzzzzz", PUBLISHED)
    # Unsorted input; window must order by (published, video_id).
    chosen, skipped = select_window(
        (z, a), last_published=None, last_video_id=None, limit=5
    )
    assert [v.video_id for v in chosen] == ["aaaaaaaaaaa", "zzzzzzzzzzz"]
    assert skipped == 0


def test_select_window_filters_older_and_same_second_smaller_id() -> None:
    from ingestion_service.domain.schedule import select_window

    older = VideoRef("bbbbbbbbbbb", EARLIER)
    same_smaller = VideoRef("aaaaaaaaaaa", PUBLISHED)
    newer = VideoRef("ccccccccccc", LATER)
    chosen, skipped = select_window(
        (older, same_smaller, newer),
        last_published=PUBLISHED,
        last_video_id="mmmmmmmmmmm",
        limit=5,
    )
    assert [v.video_id for v in chosen] == ["ccccccccccc"]
    assert skipped == 0


def test_select_window_non_positive_limit_returns_empty() -> None:
    from ingestion_service.domain.schedule import select_window

    chosen, skipped = select_window(
        _feed_15_desc(), last_published=None, last_video_id=None, limit=0
    )
    assert chosen == ()
    assert skipped == 0


# --- due_decision (ING-06, D-21/D-22) ---


def test_due_decision_before_time_of_day() -> None:
    from ingestion_service.domain.schedule import due_decision

    # 2026-10-19 is Monday (ISO 1). 05:59 MSK → before_time.
    decision = due_decision(
        _schedule(),
        now_utc=_msk_as_utc(2026, 10, 19, 5, 59),
        tz=MSK,
    )
    assert decision.due is False
    assert decision.reason == "before_time"


def test_due_decision_exactly_at_time_of_day() -> None:
    from ingestion_service.domain.schedule import due_decision

    decision = due_decision(
        _schedule(),
        now_utc=_msk_as_utc(2026, 10, 19, 6, 0),
        tz=MSK,
    )
    assert decision.due is True
    assert decision.reason == "ok"


def test_due_decision_disallowed_day() -> None:
    from ingestion_service.domain.schedule import due_decision

    # Monday only allowed; use a Tuesday.
    decision = due_decision(
        _schedule(days=(1,)),
        now_utc=_msk_as_utc(2026, 10, 20, 7, 0),  # Tuesday
        tz=MSK,
    )
    assert decision.due is False
    assert decision.reason == "day"


def test_due_decision_disabled() -> None:
    from ingestion_service.domain.schedule import due_decision

    decision = due_decision(
        _schedule(enabled=False),
        now_utc=_msk_as_utc(2026, 10, 19, 7, 0),
        tz=MSK,
    )
    assert decision.due is False
    assert decision.reason == "disabled"


def test_due_decision_already_ran_today() -> None:
    from ingestion_service.domain.schedule import due_decision

    target_local = datetime(2026, 10, 19, 6, 0, tzinfo=MSK)
    last = target_local + timedelta(minutes=15)
    decision = due_decision(
        _schedule(last_run_at=last.astimezone(timezone.utc)),
        now_utc=_msk_as_utc(2026, 10, 19, 8, 0),
        tz=MSK,
    )
    assert decision.due is False
    assert decision.reason == "already_ran"


def test_due_decision_catch_up_after_missed_days() -> None:
    """VM down two days: first allowed day after return → due once; after stamp → not."""
    from ingestion_service.domain.schedule import due_decision

    # last_run_at from Friday 2026-10-16 06:05 MSK; now Monday 2026-10-19 07:00.
    last = datetime(2026, 10, 16, 6, 5, tzinfo=MSK).astimezone(timezone.utc)
    now = _msk_as_utc(2026, 10, 19, 7, 0)
    first = due_decision(_schedule(last_run_at=last), now_utc=now, tz=MSK)
    assert first.due is True
    assert first.reason == "ok"

    stamped = due_decision(
        _schedule(last_run_at=now),
        now_utc=now,
        tz=MSK,
    )
    assert stamped.due is False
    assert stamped.reason == "already_ran"


def test_due_decision_idempotent_same_now() -> None:
    from ingestion_service.domain.schedule import due_decision

    schedule = _schedule()
    now = _msk_as_utc(2026, 10, 19, 7, 0)
    a = due_decision(schedule, now_utc=now, tz=MSK)
    b = due_decision(schedule, now_utc=now, tz=MSK)
    assert a == b


def test_due_decision_rejects_naive_now_utc() -> None:
    from ingestion_service.domain.schedule import due_decision

    try:
        due_decision(
            _schedule(),
            now_utc=datetime(2026, 10, 19, 7, 0),
            tz=MSK,
        )
    except ValueError as err:
        assert "timezone-aware" in str(err)
    else:
        raise AssertionError("expected ValueError for naive now_utc")


def test_schedule_module_has_no_zoneinfo_or_datetime_now() -> None:
    from pathlib import Path

    body = (
        Path("ingestion-service/src/ingestion_service/domain/schedule.py")
        .read_text(encoding="utf-8")
        .lower()
    )
    assert "zoneinfo" not in body
    assert "datetime.now" not in body
