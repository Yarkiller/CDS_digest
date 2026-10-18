"""VotingCycleReader port — read-only cycle stub for current-issue DTO (D-32/D-33)."""

from __future__ import annotations

from typing import Protocol

from backend.domain.voting_cycle import VotingCycle


class VotingCycleReader(Protocol):
    def list_cycles(self) -> list[VotingCycle]: ...
