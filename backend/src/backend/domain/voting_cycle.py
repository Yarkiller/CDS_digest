"""Voting cycle read-model for current-issue callout stub (D-33)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VotingCycle:
    id: str
    status: str  # "open" | "closed"
    opens_at: datetime
    closes_at: datetime
