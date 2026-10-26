"""get_ballot use-case — leaders + empty shapes (VOTE-02/03/04, D-40…43, D-48…50)."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.application.use_cases.get_ballot import get_ballot
from backend.domain.vote import BallotLeader, BallotTopic
from backend.domain.voting_cycle import VotingCycle
from backend.tests_support.in_memory import InMemoryVoteRepository, InMemoryVotingCycleReader


def _open_cycle(*, cycle_id: str = "cycle-1") -> VotingCycle:
    return VotingCycle(
        id=cycle_id,
        status="open",
        opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
        closes_at=datetime(2026, 4, 16, 23, 59, 59, tzinfo=timezone.utc),
    )


def _closed_cycle(*, cycle_id: str = "cycle-1") -> VotingCycle:
    return VotingCycle(
        id=cycle_id,
        status="closed",
        opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
        closes_at=datetime(2026, 4, 16, 23, 59, 59, tzinfo=timezone.utc),
    )


def test_get_ballot_never_voted_returns_personal_vote_null_and_topics() -> None:
    cycle = _open_cycle()
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
    cycles = InMemoryVotingCycleReader([cycle])

    snapshot = get_ballot(votes, cycles, user_id="user-uuid-1")

    assert snapshot.cycle is not None
    assert snapshot.cycle.id == "cycle-1"
    assert snapshot.cycle.status == "open"
    assert snapshot.personal_vote is None
    assert [t.id for t in snapshot.topics] == ["topic-1", "topic-2"]
    assert all(not hasattr(t, "leading") for t in snapshot.topics)
    assert "leading" not in BallotTopic.__dataclass_fields__
    assert snapshot.leaders == ()


def test_get_ballot_hide_when_zero_leaders_empty_when_all_tallies_zero() -> None:
    """D-43: leader strip hidden when every topic has 0 votes."""
    cycle = _open_cycle()
    topics = [
        BallotTopic(
            id="topic-1",
            title="RAG в корпоративной среде",
            description="dek",
            materials_count=2,
            votes=0,
        ),
        BallotTopic(
            id="topic-2",
            title="Аномалии в логах",
            description="dek",
            materials_count=0,
            votes=0,
        ),
        BallotTopic(
            id="topic-3",
            title="Векторный поиск",
            description="dek",
            materials_count=1,
            votes=0,
        ),
    ]
    votes = InMemoryVoteRepository(topics_by_cycle={"cycle-1": topics})
    cycles = InMemoryVotingCycleReader([cycle])

    snapshot = get_ballot(votes, cycles, user_id="user-uuid-1")

    assert snapshot.leaders == ()
    assert len(snapshot.topics) == 3
    assert all(t.votes == 0 for t in snapshot.topics)
    assert "leading" not in BallotTopic.__dataclass_fields__


def test_get_ballot_computes_leaders_when_tallies_nonzero() -> None:
    """D-40: unique max → one BallotLeader (no topic.leading)."""
    cycle = _open_cycle()
    topics = [
        BallotTopic(
            id="topic-1",
            title="RAG в корпоративной среде",
            description="dek",
            materials_count=1,
            votes=3,
        ),
        BallotTopic(
            id="topic-2",
            title="Аномалии в логах",
            description="dek",
            materials_count=0,
            votes=1,
        ),
    ]
    votes = InMemoryVoteRepository(topics_by_cycle={"cycle-1": topics})
    cycles = InMemoryVotingCycleReader([cycle])

    snapshot = get_ballot(votes, cycles, user_id="user-uuid-1")

    assert len(snapshot.leaders) == 1
    assert snapshot.leaders[0] == BallotLeader(title="RAG в корпоративной среде", votes=3)
    assert all(not hasattr(t, "leading") for t in snapshot.topics)


def test_get_ballot_tie_includes_all_max_leaders() -> None:
    """D-42: two+ topics share max > 0 → all included in leaders[]."""
    cycle = _open_cycle()
    topics = [
        BallotTopic(
            id="topic-1",
            title="RAG в корпоративной среде",
            description="dek",
            materials_count=1,
            votes=5,
        ),
        BallotTopic(
            id="topic-2",
            title="Аномалии в логах",
            description="dek",
            materials_count=0,
            votes=5,
        ),
        BallotTopic(
            id="topic-3",
            title="Векторный поиск",
            description="dek",
            materials_count=2,
            votes=2,
        ),
    ]
    votes = InMemoryVoteRepository(topics_by_cycle={"cycle-1": topics})
    cycles = InMemoryVotingCycleReader([cycle])

    snapshot = get_ballot(votes, cycles, user_id="user-uuid-1")

    assert snapshot.leaders == (
        BallotLeader(title="RAG в корпоративной среде", votes=5),
        BallotLeader(title="Аномалии в логах", votes=5),
    )
    assert "leading" not in BallotTopic.__dataclass_fields__


def test_get_ballot_no_cycle_returns_null_cycle_empty_shape() -> None:
    """D-50: no active cycle → cycle null, topics [], leaders [], personal_vote null."""
    votes = InMemoryVoteRepository()
    cycles = InMemoryVotingCycleReader([])

    snapshot = get_ballot(votes, cycles, user_id="user-uuid-1")

    assert snapshot.cycle is None
    assert snapshot.topics == ()
    assert snapshot.leaders == ()
    assert snapshot.personal_vote is None


def test_get_ballot_open_cycle_zero_topics_empty_shape() -> None:
    """D-49: open cycle with zero topics → cycle present, topics [], leaders []."""
    cycle = _open_cycle()
    votes = InMemoryVoteRepository(topics_by_cycle={"cycle-1": []})
    cycles = InMemoryVotingCycleReader([cycle])

    snapshot = get_ballot(votes, cycles, user_id="user-uuid-1")

    assert snapshot.cycle is not None
    assert snapshot.cycle.id == "cycle-1"
    assert snapshot.cycle.status == "open"
    assert snapshot.topics == ()
    assert snapshot.leaders == ()
    assert snapshot.personal_vote is None


def test_get_ballot_closed_cycle_still_computes_tallies_and_leaders() -> None:
    """D-48: closed cycle with topics → status closed; tallies/leaders still computable."""
    cycle = _closed_cycle()
    topics = [
        BallotTopic(
            id="topic-1",
            title="RAG в корпоративной среде",
            description="dek",
            materials_count=1,
            votes=4,
        ),
        BallotTopic(
            id="topic-2",
            title="Аномалии в логах",
            description="dek",
            materials_count=0,
            votes=2,
        ),
    ]
    votes = InMemoryVoteRepository(topics_by_cycle={"cycle-1": topics})
    cycles = InMemoryVotingCycleReader([cycle])

    snapshot = get_ballot(
        votes,
        cycles,
        user_id="user-uuid-1",
        now=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )

    assert snapshot.cycle is not None
    assert snapshot.cycle.status == "closed"
    assert snapshot.cycle.progress_ratio == 1.0
    assert [t.id for t in snapshot.topics] == ["topic-1", "topic-2"]
    assert snapshot.topics[0].votes == 4
    assert snapshot.topics[1].votes == 2
    assert snapshot.leaders == (
        BallotLeader(title="RAG в корпоративной среде", votes=4),
    )
    assert "leading" not in BallotTopic.__dataclass_fields__
