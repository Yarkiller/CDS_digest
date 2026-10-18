"""get_issue_by_number — published issue by number; missing/unpublished → not found."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.application.use_cases.get_issue_by_number import get_issue_by_number
from backend.domain.errors import IssueNotFoundError
from backend.domain.issue import Issue, IssueItem
from backend.tests_support.in_memory import InMemoryIssueRepository


def _item(slug: str, position: int) -> IssueItem:
    return IssueItem(
        slug=slug,
        title=f"Title {slug}",
        position=position,
        format="Статья",
        reading_minutes=5,
        dek=None,
    )


def _issue(
    *,
    issue_id: str,
    number: int,
    published_at: datetime | None,
    items: tuple[IssueItem, ...] = (),
) -> Issue:
    return Issue(
        id=issue_id,
        number=number,
        period_label=f"week-{number}",
        title=f"Issue {number}",
        editor="Редакция Digest CDS",
        published_at=published_at,  # type: ignore[arg-type]
        items=items,
    )


def test_get_issue_by_number_returns_published_issue_with_items() -> None:
    issue = _issue(
        issue_id="iss-13",
        number=13,
        published_at=datetime(2026, 3, 10, tzinfo=timezone.utc),
        items=(_item("past-mat", 1),),
    )
    repo = InMemoryIssueRepository([issue])

    found = get_issue_by_number(repo, 13)

    assert found.number == 13
    assert found.id == "iss-13"
    assert [i.slug for i in found.items] == ["past-mat"]


def test_get_issue_by_number_missing_raises_not_found() -> None:
    repo = InMemoryIssueRepository([])
    with pytest.raises(IssueNotFoundError) as exc_info:
        get_issue_by_number(repo, 99999)
    assert exc_info.value.number == 99999


def test_get_issue_by_number_unpublished_raises_not_found() -> None:
    """Unpublished rows are not returned by the port — use-case maps None → not found."""
    # Seed only published; requesting a number that was never published → not found
    published = _issue(
        issue_id="iss-14",
        number=14,
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
    )
    repo = InMemoryIssueRepository([published])
    with pytest.raises(IssueNotFoundError):
        get_issue_by_number(repo, 13)
