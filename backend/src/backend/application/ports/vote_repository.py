"""VoteRepository port — ballot topics, personal vote, upsert (not VotingCycleReader)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from backend.domain.vote import BallotTopic, PersonalVote


class VoteRepository(Protocol):
    def list_topics_with_counts(self, cycle_id: str) -> list[BallotTopic]: ...

    def get_vote(self, cycle_id: str, user_id: str) -> PersonalVote | None: ...

    def upsert_vote(
        self,
        *,
        cycle_id: str,
        user_id: str,
        topic_id: str,
        expected_updated_at: datetime | None,
    ) -> PersonalVote: ...
