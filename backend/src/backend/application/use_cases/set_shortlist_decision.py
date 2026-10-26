"""Persist Approve/Reject/pending on shortlist items (ADMIN-02, D-82, D-85)."""

from __future__ import annotations

from datetime import datetime, timezone

from backend.application.ports.shortlist_repository import ShortlistRepository
from backend.application.use_cases.get_admin_shortlist import get_admin_shortlist
from backend.domain.errors import InvalidShortlistDecisionError, ShortlistNotFoundError
from backend.domain.shortlist import AdminShortlist

_ALLOWED_DECISIONS = frozenset({"pending", "approved", "rejected"})


def set_shortlist_decision(
    shortlist: ShortlistRepository,
    *,
    material_id: int,
    decision: str,
    actor_user_id: str,
    now: datetime | None = None,
) -> AdminShortlist:
    """Write shortlist_decision and return AdminShortlist snapshot for SPA refresh.

    Approve is allowed on draft materials (D-85) — send-pool draft block is 05-03.
    """
    decision_key = (decision or "").strip()
    if decision_key not in _ALLOWED_DECISIONS:
        raise InvalidShortlistDecisionError(decision)

    batch = shortlist.get_current_batch()
    if batch is None:
        raise ShortlistNotFoundError()

    if not any(item.material_id == material_id for item in batch.items):
        raise ShortlistNotFoundError(batch_id=batch.id, material_id=material_id)

    clock = now or datetime.now(timezone.utc)
    shortlist.set_decision(
        batch_id=batch.id,
        material_id=material_id,
        decision=decision_key,
        actor_user_id=actor_user_id,
        decided_at=clock,
    )
    return get_admin_shortlist(shortlist)
