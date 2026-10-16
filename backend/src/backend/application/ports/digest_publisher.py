"""DigestPublisher port — atomic claim + publish + delivery stamp (CR-01/WR-01, D-88/D-89).

Single-transaction operation backed on live by migration 005's ``claim_and_publish_digest``
RPC. Collapses the previously-split ``ShortlistRepository.claim_sent`` + ``IssueRepository.publish``
so a publish failure can never leave a batch stamped ``sent_at`` with no issue.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class DigestPublication:
    """Result of a successful atomic claim+publish (mirrors the RPC's jsonb payload)."""

    batch_id: int
    issue_number: int
    issue_url: str
    delivery_status: str
    recipient_count: int


class DigestPublisher(Protocol):
    def claim_and_publish(
        self,
        *,
        batch_id: int,
        sent_at: datetime,
        period_label: str,
        title: str,
        material_ids: list[int] | None = None,
        recipient_count: int = 0,
    ) -> DigestPublication:
        """Atomically claim the unsent batch (``sent_at IS NULL``), publish its approved∩ready
        issue, and stamp delivery columns — all in one transaction.

        When ``material_ids`` is provided, issue item positions follow that order (G-05-1)
        inside the same claim+publish transaction (live: ``p_material_ids`` on the RPC).

        ``recipient_count`` stamps the **planned** audience M (D-06 option i); actual N and the
        live status are reported on the API result / ``pings`` — never via ``update_delivery``.

        Raises:
            AlreadySentError: batch already claimed or missing (lost the race, D-89).
            EmptySendPoolError: no approved∩ready items to publish (ADMIN-07 safety net).
            PersistenceError: any other adapter/SDK failure mapped at the boundary.
        """
        ...
