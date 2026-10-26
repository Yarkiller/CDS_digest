"""cast_vote use-case — confirm one vote, idempotent same-topic (VOTE-01, D-52)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.application.use_cases.cast_vote import cast_vote
from backend.domain.errors import InvalidVoteError, VoteConflictError, VotingCycleClosedError
from backend.domain.vote import BallotTopic
from backend.domain.voting_cycle import VotingCycle
from backend.tests_support.in_memory import InMemoryVoteRepository, InMemoryVotingCycleReader


def _open_cycle() -> VotingCycle:
    return VotingCycle(
        id="cycle-1",
        status="open",
        opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
        closes_at=datetime(2026, 4, 16, 23, 59, 59, tzinfo=timezone.utc),
    )


def _seeded() -> tuple[InMemoryVoteRepository, InMemoryVotingCycleReader]:
    topics = [
        BallotTopic(
            id="topic-1",
            title="RAG в корпоративной среде",
            description="Аудит применения RAG.",
            materials_count=2,
            votes=0,
        ),
        BallotTopic(
            id="topic-2",
            title="Аномалии в логах",
            description="Как искать аномалии.",
            materials_count=0,
            votes=0,
        ),
    ]
    votes = InMemoryVoteRepository(topics_by_cycle={"cycle-1": topics})
    cycles = InMemoryVotingCycleReader([_open_cycle()])
    return votes, cycles


def test_cast_vote_stores_exactly_one_vote_and_returns_snapshot() -> None:
    votes, cycles = _seeded()

    snapshot = cast_vote(
        votes,
        cycles,
        user_id="user-uuid-1",
        topic_id="topic-1",
        expected_updated_at=None,
    )

    assert snapshot.personal_vote is not None
    assert snapshot.personal_vote.topic_id == "topic-1"
    assert snapshot.topics[0].votes == 1
    assert votes.get_vote("cycle-1", "user-uuid-1") is not None
    assert votes.vote_count_for("cycle-1") == 1


def test_cast_vote_same_topic_repeat_is_idempotent() -> None:
    votes, cycles = _seeded()

    first = cast_vote(
        votes,
        cycles,
        user_id="user-uuid-1",
        topic_id="topic-1",
        expected_updated_at=None,
    )
    second = cast_vote(
        votes,
        cycles,
        user_id="user-uuid-1",
        topic_id="topic-1",
        expected_updated_at=first.personal_vote.updated_at.isoformat(),
    )

    assert second.personal_vote is not None
    assert second.personal_vote.topic_id == "topic-1"
    assert votes.vote_count_for("cycle-1") == 1
    assert second.topics[0].votes == 1


def test_cast_vote_unknown_topic_raises_invalid_vote() -> None:
    votes, cycles = _seeded()

    with pytest.raises(InvalidVoteError):
        cast_vote(
            votes,
            cycles,
            user_id="user-uuid-1",
            topic_id="topic-missing",
            expected_updated_at=None,
        )


def test_cast_vote_empty_topic_raises_invalid_vote() -> None:
    votes, cycles = _seeded()

    with pytest.raises(InvalidVoteError):
        cast_vote(
            votes,
            cycles,
            user_id="user-uuid-1",
            topic_id="  ",
            expected_updated_at=None,
        )


def test_cast_vote_topic_from_other_cycle_raises_invalid_vote() -> None:
    votes, cycles = _seeded()
    foreign = BallotTopic(
        id="foreign-topic",
        title="Другой цикл",
        description="не здесь",
        materials_count=0,
        votes=0,
    )
    votes.seed_topics("other-cycle", [foreign])

    with pytest.raises(InvalidVoteError):
        cast_vote(
            votes,
            cycles,
            user_id="user-uuid-1",
            topic_id="foreign-topic",
            expected_updated_at=None,
        )


def test_cast_vote_changes_topic_a_to_b_while_open() -> None:
    """VOTE-03: A→B upsert keeps one row; tallies move with personal_vote."""
    votes, cycles = _seeded()

    first = cast_vote(
        votes,
        cycles,
        user_id="user-uuid-1",
        topic_id="topic-1",
        expected_updated_at=None,
    )
    assert first.personal_vote is not None
    assert first.personal_vote.topic_id == "topic-1"
    assert first.topics[0].votes == 1
    assert first.topics[1].votes == 0

    second = cast_vote(
        votes,
        cycles,
        user_id="user-uuid-1",
        topic_id="topic-2",
        expected_updated_at=first.personal_vote.updated_at,
    )

    assert second.personal_vote is not None
    assert second.personal_vote.topic_id == "topic-2"
    assert votes.vote_count_for("cycle-1") == 1
    assert second.topics[0].votes == 0
    assert second.topics[1].votes == 1


def test_cast_vote_closed_cycle_raises_with_ballot() -> None:
    votes, cycles = _seeded()
    closed = VotingCycle(
        id="cycle-1",
        status="closed",
        opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
        closes_at=datetime(2026, 4, 16, 23, 59, 59, tzinfo=timezone.utc),
    )
    cycles = InMemoryVotingCycleReader([closed])

    with pytest.raises(VotingCycleClosedError) as exc_info:
        cast_vote(
            votes,
            cycles,
            user_id="user-uuid-1",
            topic_id="topic-1",
            expected_updated_at=None,
        )

    assert exc_info.value.cycle_id == "cycle-1"
    assert exc_info.value.ballot is not None
    assert exc_info.value.ballot.cycle is not None
    assert exc_info.value.ballot.cycle.status == "closed"
    assert len(exc_info.value.ballot.topics) == 2


def test_cast_vote_cas_mismatch_raises_vote_conflict_with_ballot() -> None:
    votes, cycles = _seeded()
    first = cast_vote(
        votes,
        cycles,
        user_id="user-uuid-1",
        topic_id="topic-1",
        expected_updated_at=None,
    )
    stale = datetime(2020, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(VoteConflictError) as exc_info:
        cast_vote(
            votes,
            cycles,
            user_id="user-uuid-1",
            topic_id="topic-2",
            expected_updated_at=stale,
        )

    assert exc_info.value.ballot is not None
    assert exc_info.value.ballot.personal_vote is not None
    assert exc_info.value.ballot.personal_vote.topic_id == "topic-1"
    assert votes.get_vote("cycle-1", "user-uuid-1").topic_id == "topic-1"
    # unused first binding keeps assert context for updated_at shape
    assert first.personal_vote.topic_id == "topic-1"
