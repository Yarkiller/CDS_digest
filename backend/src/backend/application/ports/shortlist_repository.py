"""ShortlistRepository port — current unsent batch for admin triage (ADMIN-01/02, D-81/D-82)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from backend.domain.shortlist import ShortlistBatch


class ShortlistRepository(Protocol):
    def get_current_batch(self) -> ShortlistBatch | None:
        """Latest unsent batch (sent_at IS NULL), or None when empty (D-80/D-81)."""
        ...

    def get_latest_batch(self) -> ShortlistBatch | None:
        """Most recent batch regardless of sent_at, or None (D-89 already-sent signal, WR-03)."""
        ...

    def set_decision(
        self,
        *,
        batch_id: int,
        material_id: int,
        decision: str,
        actor_user_id: str,
        decided_at: datetime,
    ) -> ShortlistBatch:
        """Persist shortlist_decision for one material; return updated batch (D-82)."""
        ...

    def claim_sent(
        self,
        *,
        batch_id: int,
        sent_at: datetime,
    ) -> ShortlistBatch:
        """Atomic claim: set sent_at only when currently NULL (ADMIN-07, D-89)."""
        ...

    def release_claim(self, *, batch_id: int) -> None:
        """Compensating action: clear sent_at after a failed publish so retry is safe (CR-01)."""
        ...
