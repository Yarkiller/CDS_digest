"""Build BallotSnapshot for the active voting cycle (VOTE-02, D-40…43)."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.application.ports.vote_repository import VoteRepository
from backend.application.ports.voting_cycle_reader import VotingCycleReader
from backend.application.use_cases.get_current_issue import select_active_voting_cycle
from backend.domain.vote import (
    BallotCycleView,
    BallotLeader,
    BallotSnapshot,
    BallotTopic,
)


def _compute_leaders(topics: list[BallotTopic]) -> tuple[BallotLeader, ...]:
    if not topics:
        return ()
    max_votes = max(t.votes for t in topics)
    if max_votes <= 0:
        return ()
    return tuple(
        BallotLeader(title=t.title, votes=t.votes) for t in topics if t.votes == max_votes
    )


def get_ballot(
    votes: VoteRepository,
    voting_cycles: VotingCycleReader,
    user_id: str,
    *,
    now: datetime | None = None,
) -> BallotSnapshot:
    cycle = select_active_voting_cycle(voting_cycles.list_cycles())
    if cycle is None:
        return BallotSnapshot(cycle=None, topics=(), personal_vote=None, leaders=())

    clock = now or datetime.now(timezone.utc)
    topics = votes.list_topics_with_counts(cycle.id)
    personal = votes.get_vote(cycle.id, user_id)
    return BallotSnapshot(
        cycle=BallotCycleView.from_cycle(cycle, now=clock),
        topics=tuple(topics),
        personal_vote=personal,
        leaders=_compute_leaders(topics),
    )
