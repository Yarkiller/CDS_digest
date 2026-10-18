"""List past published digest issues — excludes current (D-31)."""

from __future__ import annotations

from backend.application.ports.issue_repository import IssueRepository
from backend.domain.issue import Issue


def list_archive_issues(issues: IssueRepository) -> list[Issue]:
    """Return published issues excluding the latest-published current issue."""
    return issues.list_past_published()
