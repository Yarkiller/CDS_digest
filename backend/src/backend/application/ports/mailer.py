"""Mailer port — digest email delivery (ADMIN-07/08, D-87)."""

from __future__ import annotations

from typing import Protocol, Sequence

from backend.domain.recipient import Recipient


class Mailer(Protocol):
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
        """Deliver one message per recipient (D-05) and report honest delivery.

        Return keys: ``delivery_status`` (``stubbed`` | ``sent`` | ``partial`` | ``failed``),
        ``recipient_count`` (planned M echo, D-06), ``delivered_count`` (actual N, D-10),
        ``issue_url``, and an optional ``stop_reason`` (D-08). ``recipients`` and ``body_html``
        are additive keyword params so existing stub callers stay valid.
        """
        ...
