"""list_archive_issues excludes current latest-published (D-31)."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.application.use_cases.list_archive_issues import list_archive_issues
from backend.domain.issue import Issue, IssueItem
from backend.tests_support.in_memory import InMemoryIssueRepository


def test_list_archive_excludes_current_latest_published() -> None:
    """D-31: archive lists past published issues only — excludes current."""
    older = Issue(
        id="iss-13",
        number=13,
        period_label="week-13",
        title="Past",
        editor=None,
        published_at=datetime(2026, 3, 10, tzinfo=timezone.utc),
        items=(
            IssueItem(
                slug="past-a",
                title="Past A",
                position=1,
                format="Статья",
                reading_minutes=5,
            ),
        ),
    )
    current = Issue(
        id="iss-14",
        number=14,
        period_label="week-14",
        title="Current",
        editor=None,
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
        items=(),
    )
    repo = InMemoryIssueRepository([older, current])
    archive = list_archive_issues(repo)
    numbers = [i.number for i in archive]
    assert 14 not in numbers
    assert 13 in numbers
    assert len(archive) == 1
    assert archive[0].items[0].slug == "past-a"


def test_list_archive_empty_when_only_current_or_none() -> None:
    current = Issue(
        id="iss-14",
        number=14,
        period_label="week-14",
        title="Current",
        editor=None,
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
        items=(),
    )
    assert list_archive_issues(InMemoryIssueRepository([current])) == []
    assert list_archive_issues(InMemoryIssueRepository([])) == []
