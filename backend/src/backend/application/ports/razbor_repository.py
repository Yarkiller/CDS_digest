"""RazborRepository port — reader chronology + detail (RAZB-01)."""

from __future__ import annotations

from typing import Protocol

from backend.domain.razbor import Razbor


class RazborRepository(Protocol):
    def list_for_reader(self) -> list[Razbor]:
        """Return razbors ordered by meeting_at DESC NULLS LAST, then created_at DESC."""
        ...

    def get(self, razbor_id: int) -> Razbor | None:
        """Return a razbor by id, or None."""
        ...
