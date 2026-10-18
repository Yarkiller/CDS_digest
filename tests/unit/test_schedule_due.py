"""RED→GREEN: cursor is_newer / advance_cursor (ING-05, D-07). Due checks land in 24-03."""

from __future__ import annotations

from datetime import datetime, timezone

PUBLISHED = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)
EARLIER = datetime(2026, 10, 17, 8, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 10, 17, 10, 0, tzinfo=timezone.utc)


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
