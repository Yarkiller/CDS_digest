"""StubMailer — the default digest mailer double (D-15).

``SmtpMailer`` is re-exported from ``backend.infrastructure.smtp_mailer`` so the historical
import path stays stable; ``StubMailer`` remains the ``MAILER=stub`` implementation and the
in-memory test double (assumption-delta: live SMTP is added alongside, never instead).

Adapter selection (``resolve_mailer``) lives in ``backend.composition.mailer_factory``:
picking an adapter is wiring, and infrastructure must not depend on composition.
"""

from __future__ import annotations

import logging
from typing import Sequence

from backend.domain.recipient import Recipient
from backend.infrastructure.smtp_mailer import SmtpMailer

__all__ = ["SmtpMailer", "StubMailer"]

logger = logging.getLogger(__name__)


class StubMailer:
    """In-process mailer: logs body, returns delivery_status=stubbed (no SMTP)."""

    def __init__(self) -> None:
        self.last_batch_id: int | None = None
        self.last_issue_url: str | None = None
        self.last_subject: str | None = None
        self.last_body_text: str | None = None
        self.last_body_html: str | None = None
        self.last_recipient_count: int | None = None
        self.last_recipients: tuple[Recipient, ...] = ()

    def send_digest(
        self,
        *,
        batch_id: int,
        issue_url: str,
        subject: str,
        body_text: str,
        recipient_count: int,
        recipients: Sequence[Recipient] = (),
        body_html: str | None = None,
    ) -> dict[str, object]:
        self.last_batch_id = batch_id
        self.last_issue_url = issue_url
        self.last_subject = subject
        self.last_body_text = body_text
        self.last_body_html = body_html
        self.last_recipient_count = recipient_count
        self.last_recipients = tuple(recipients)
        logger.info(
            "stub_mailer digest batch_id=%s issue_url=%s recipient_count=%s\n%s",
            batch_id,
            issue_url,
            recipient_count,
            body_text,
        )
        return {
            "delivery_status": "stubbed",
            "recipient_count": recipient_count,
            "delivered_count": 0,
            "issue_url": issue_url,
        }
