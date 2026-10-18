"""RED→GREEN: cursor is_newer / advance_cursor / select_window (ING-05, D-07, D-05)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from data_collection.dto.video_ref import VideoRef

PUBLISHED = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)
EARLIER = datetime(2026, 10, 17, 8, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 10, 17, 10, 0, tzinfo=timezone.utc)
BASE = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)


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
