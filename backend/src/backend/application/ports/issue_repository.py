"""IssueRepository port — published digest issues for readers."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from backend.domain.issue import Issue, IssueItem


class IssueRepository(Protocol):
    def get_latest_published(self) -> Issue | None:
        """Return the published issue with the latest published_at (D-24), or None."""
        ...

    def get_by_number(self, number: int) -> Issue | None:
        """Return a published issue by number, or None."""
        ...

    def list_past_published(self) -> list[Issue]:
        """Published issues excluding the current (latest published_at) — D-31 readiness."""
        ...

    def publish(
        self,
        *,
        period_label: str,
        title: str,
        editor: str | None,
        published_at: datetime,
        items: Sequence[IssueItem],
    ) -> Issue:
        """Create a new published digest_issues row with attached items (D-88)."""
        ...
