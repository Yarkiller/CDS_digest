"""Load a published digest issue by number — missing/unpublished → not found."""

from __future__ import annotations

from backend.application.ports.issue_repository import IssueRepository
from backend.domain.errors import IssueNotFoundError
from backend.domain.issue import Issue


def get_issue_by_number(issues: IssueRepository, number: int) -> Issue:
    issue = issues.get_by_number(number)
    if issue is None:
        raise IssueNotFoundError(number)
    return issue
