"""Ballot snapshot domain models for voting cycle (VOTE-01/02, D-40, D-52)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.domain.voting_cycle import VotingCycle


@dataclass(frozen=True)
class BallotTopic:
    id: str
    title: str
    description: str
    materials_count: int
    votes: int


@dataclass(frozen=True)
class PersonalVote:
    topic_id: str
    updated_at: datetime


@dataclass(frozen=True)
class BallotLeader:
    title: str
    votes: int


@dataclass(frozen=True)
class BallotCycleView:
    id: str
    status: str
    opens_at: datetime
    closes_at: datetime
    progress_ratio: float

    @classmethod
    def from_cycle(cls, cycle: VotingCycle, *, now: datetime | None = None) -> BallotCycleView:
        if cycle.status == "closed":
            ratio = 1.0
        elif now is None:
            ratio = 0.0
        else:
            span = (cycle.closes_at - cycle.opens_at).total_seconds()
            if span <= 0:
                ratio = 1.0
            else:
                elapsed = (now - cycle.opens_at).total_seconds()
                ratio = max(0.0, min(1.0, elapsed / span))
        return cls(
            id=cycle.id,
            status=cycle.status,
            opens_at=cycle.opens_at,
            closes_at=cycle.closes_at,
            progress_ratio=ratio,
        )


@dataclass(frozen=True)
class BallotSnapshot:
    cycle: BallotCycleView | None
    topics: tuple[BallotTopic, ...]
    personal_vote: PersonalVote | None
    leaders: tuple[BallotLeader, ...]
