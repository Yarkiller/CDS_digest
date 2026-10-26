"""Select the current digest issue — latest published_at (D-24) + voting_cycle (D-33)."""

from __future__ import annotations

from dataclasses import dataclass

from backend.application.ports.issue_repository import IssueRepository
from backend.application.ports.voting_cycle_reader import VotingCycleReader
from backend.domain.issue import Issue
from backend.domain.voting_cycle import VotingCycle


@dataclass(frozen=True)
class CurrentIssueView:
    issue: Issue | None
    voting_cycle: VotingCycle | None = None


def select_active_voting_cycle(cycles: list[VotingCycle]) -> VotingCycle | None:
    """RESEARCH A2: prefer open by closes_at DESC; else latest closed by opens_at."""
    open_cycles = [c for c in cycles if c.status == "open"]
    if open_cycles:
        return max(open_cycles, key=lambda c: c.closes_at)
    closed = [c for c in cycles if c.status == "closed"]
    if closed:
        return max(closed, key=lambda c: c.opens_at)
    return None


def get_current_issue(
    issues: IssueRepository,
    voting_cycles: VotingCycleReader | None = None,
) -> CurrentIssueView:
    issue = issues.get_latest_published()
    cycle = None
    if voting_cycles is not None:
        cycle = select_active_voting_cycle(voting_cycles.list_cycles())
    return CurrentIssueView(issue=issue, voting_cycle=cycle)
