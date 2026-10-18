"""get_current_issue use-case — D-24 latest published_at; D-33 voting_cycle stub (A2)."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.application.use_cases.get_current_issue import get_current_issue
from backend.domain.issue import Issue, IssueItem
from backend.domain.voting_cycle import VotingCycle
from backend.tests_support.in_memory import InMemoryIssueRepository, InMemoryVotingCycleReader


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
    published_at: datetime,
    items: tuple[IssueItem, ...] = (),
) -> Issue:
    return Issue(
        id=issue_id,
        number=number,
        period_label=f"week-{number}",
        title=f"Issue {number}",
        editor="Редакция Digest CDS",
        published_at=published_at,
        items=items,
    )


def _cycle(
    *,
    cycle_id: str,
    status: str,
    opens_at: datetime,
    closes_at: datetime,
) -> VotingCycle:
    return VotingCycle(
        id=cycle_id,
        status=status,
        opens_at=opens_at,
        closes_at=closes_at,
    )


def test_get_current_issue_returns_latest_published_by_published_at() -> None:
    older = _issue(
        issue_id="iss-13",
        number=13,
        published_at=datetime(2026, 3, 10, tzinfo=timezone.utc),
        items=(_item("old-mat", 1),),
    )
    newer = _issue(
        issue_id="iss-14",
        number=14,
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
        items=(_item("rag-systems", 1), _item("anomaly-detection", 2)),
    )
    repo = InMemoryIssueRepository([older, newer])

    current = get_current_issue(repo)

    assert current.issue is not None
    assert current.issue.number == 14
    assert current.issue.id == "iss-14"
    assert [i.slug for i in current.issue.items] == ["rag-systems", "anomaly-detection"]
    assert current.voting_cycle is None


def test_get_current_issue_returns_none_when_no_published() -> None:
    repo = InMemoryIssueRepository([])
    result = get_current_issue(repo)
    assert result.issue is None
    assert result.voting_cycle is None


def test_get_current_issue_returns_issue_with_empty_items() -> None:
    bare = _issue(
        issue_id="iss-15",
        number=15,
        published_at=datetime(2026, 3, 24, tzinfo=timezone.utc),
        items=(),
    )
    repo = InMemoryIssueRepository([bare])
    current = get_current_issue(repo)
    assert current.issue is not None
    assert current.issue.number == 15
    assert current.issue.items == ()


def test_get_current_issue_prefers_open_cycle_by_closes_at() -> None:
    """RESEARCH A2: prefer status=open ordered by closes_at (latest closes wins)."""
    issue = _issue(
        issue_id="iss-14",
        number=14,
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
        items=(_item("rag-systems", 1),),
    )
    earlier_open = _cycle(
        cycle_id="c-early",
        status="open",
        opens_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        closes_at=datetime(2026, 4, 10, tzinfo=timezone.utc),
    )
    later_open = _cycle(
        cycle_id="c-late",
        status="open",
        opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
        closes_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
    )
    closed = _cycle(
        cycle_id="c-closed",
        status="closed",
        opens_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        closes_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
    )
    result = get_current_issue(
        InMemoryIssueRepository([issue]),
        InMemoryVotingCycleReader([closed, earlier_open, later_open]),
    )
    assert result.voting_cycle is not None
    assert result.voting_cycle.id == "c-late"
    assert result.voting_cycle.status == "open"
    assert result.voting_cycle.closes_at == datetime(2026, 4, 16, tzinfo=timezone.utc)


def test_get_current_issue_falls_back_to_latest_closed_by_opens_at() -> None:
    """RESEARCH A2: when no open cycle, pick latest closed by opens_at."""
    issue = _issue(
        issue_id="iss-14",
        number=14,
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
        items=(_item("rag-systems", 1),),
    )
    older_closed = _cycle(
        cycle_id="c-old",
        status="closed",
        opens_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        closes_at=datetime(2026, 2, 14, tzinfo=timezone.utc),
    )
    newer_closed = _cycle(
        cycle_id="c-new",
        status="closed",
        opens_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        closes_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
    )
    result = get_current_issue(
        InMemoryIssueRepository([issue]),
        InMemoryVotingCycleReader([older_closed, newer_closed]),
    )
    assert result.voting_cycle is not None
    assert result.voting_cycle.id == "c-new"
    assert result.voting_cycle.status == "closed"


def test_get_current_issue_absent_cycle_when_reader_empty() -> None:
    issue = _issue(
        issue_id="iss-14",
        number=14,
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
        items=(_item("rag-systems", 1),),
    )
    result = get_current_issue(
        InMemoryIssueRepository([issue]),
        InMemoryVotingCycleReader([]),
    )
    assert result.issue is not None
    assert result.voting_cycle is None
