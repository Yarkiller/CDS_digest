"""Real SMTP digest delivery — stdlib ``smtplib`` behind the ``Mailer`` port (MAIL-01/04/05).

Locked phase-21 posture:

- **D-05**: exactly one message per recipient (a single ``To``) — never a shared Bcc blast.
- **D-07**: ``sent`` / ``partial`` / ``failed`` are derived from delivered-vs-planned counts.
- **D-08**: continue past a failure, stop after three *consecutive* failures, reset the streak
  on a success, and report ``stop_reason`` in the returned payload.
- **D-13**: ``starttls`` by default (relay port 587); ``ssl`` / ``none`` are operator overrides.
- **D-14**: bounded timeouts are injected primitives (connect ≈10s, per-send ≈30s), fixed in
  ``Settings`` — this module never reads the process environment (MAIL-05).
- **MAIL-04**: ``smtplib.SMTPException`` / ``OSError`` / ``TimeoutError`` become
  ``MailDeliveryError`` here, at the adapter boundary; no transport type escapes upward.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Protocol, Sequence

from backend.domain.errors import MailDeliveryError
from backend.domain.recipient import Recipient

logger = logging.getLogger(__name__)

CONSECUTIVE_FAILURE_LIMIT = 3
"""D-08: stop the per-recipient loop after this many consecutive transport failures."""

STOP_REASON_CONSECUTIVE_FAILURES = "consecutive_failures"
"""D-08: ``stop_reason`` value reported once the consecutive-failure limit trips."""


class SmtpConnection(Protocol):
    """The slice of ``smtplib.SMTP`` this adapter drives (test doubles implement it)."""

    sock: object

    def starttls(self, *, context: ssl.SSLContext) -> object: ...

    def login(self, user: str, password: str) -> object: ...

    def send_message(self, message: EmailMessage) -> object: ...

    def quit(self) -> object: ...


class SmtpFactory(Protocol):
    """Opens a transport for one digest run (injected in tests; stdlib by default)."""

    def __call__(
        self,
        host: str,
        port: int,
        timeout: float,
        *,
        use_ssl: bool,
    ) -> SmtpConnection: ...


def _default_smtp_factory(
    host: str,
    port: int,
    timeout: float,
    *,
    use_ssl: bool,
) -> SmtpConnection:
    """Stdlib transport — ``SMTP_SSL`` for implicit TLS, plain ``SMTP`` otherwise (D-13)."""
    if use_ssl:
        return smtplib.SMTP_SSL(host, port, timeout=timeout)
    return smtplib.SMTP(host, port, timeout=timeout)


def _delivery_status(delivered: int, planned: int) -> str:
    """D-07: ``sent`` (N=M) / ``partial`` (0<N<M) / ``failed`` (N=0); M=0 is honestly sent."""
    if planned <= 0:
        return "sent"
    if delivered <= 0:
        return "failed"
    if delivered >= planned:
        return "sent"
    return "partial"


class SmtpMailer:
    """Sync per-recipient SMTP delivery with D-08 stop policy and MAIL-04 error mapping."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        user: str,
        password: str,
        from_addr: str,
        tls_mode: str = "starttls",
        connect_timeout: float = 10.0,
        send_timeout: float = 30.0,
        from_name: str | None = None,
        smtp_factory: SmtpFactory | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from_addr = from_addr
        self._from_name = from_name or None
        self._tls_mode = tls_mode
        self._connect_timeout = connect_timeout
        self._send_timeout = send_timeout
        self._smtp_factory: SmtpFactory = smtp_factory or _default_smtp_factory

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
        """Deliver one message per recipient and report honest N-of-M delivery (D-05/D-07)."""
        audience = list(recipients)
        if not audience:
            # D-04 / RESEARCH Q3: an empty live audience is honestly ``sent`` with N=0.
            return {
                "delivery_status": "sent" if recipient_count == 0 else "failed",
                "recipient_count": recipient_count,
                "delivered_count": 0,
                "issue_url": issue_url,
            }

        connection = self._open_connection()
        delivered = 0
        consecutive_failures = 0
        stop_reason: str | None = None
        try:
            self._apply_send_timeout(connection)
            for recipient in audience:
                try:
                    # CR-01: building the message lives inside the guard — a malformed ``To``
                    # (stdlib ``ValueError`` on CR/LF) is ONE failed recipient (D-08), never a
                    # run-killer that escapes and 500s an already-published digest (D-88).
                    message = self._build_message(
                        recipient,
                        subject=subject,
                        body_text=body_text,
                        body_html=body_html,
                    )
                    connection.send_message(message)
                except (smtplib.SMTPException, OSError, TimeoutError, ValueError) as exc:
                    consecutive_failures += 1
                    logger.warning(
                        "smtp_mailer per-recipient failure batch_id=%s delivered=%s/%s "
                        "consecutive_failures=%s error=%s",
                        batch_id,
                        delivered,
                        recipient_count,
                        consecutive_failures,
                        exc,
                    )
                    if consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
                        stop_reason = STOP_REASON_CONSECUTIVE_FAILURES
                        break
                    continue
                delivered += 1
                consecutive_failures = 0
        finally:
            self._close(connection)

        status = _delivery_status(delivered, recipient_count)
        logger.info(
            "smtp_mailer digest batch_id=%s recipient_count=%s delivered_count=%s status=%s",
            batch_id,
            recipient_count,
            delivered,
            status,
        )
        result: dict[str, object] = {
            "delivery_status": status,
            "recipient_count": recipient_count,
            "delivered_count": delivered,
            "issue_url": issue_url,
        }
        if stop_reason is not None:
            result["stop_reason"] = stop_reason
        return result

    def _open_connection(self) -> SmtpConnection:
        """Connect + TLS + auth; any transport failure is a ``MailDeliveryError`` (MAIL-04)."""
        use_ssl = self._tls_mode == "ssl"
        try:
            connection = self._smtp_factory(
                self._host,
                self._port,
                self._connect_timeout,
                use_ssl=use_ssl,
            )
            if self._tls_mode == "starttls":
                connection.starttls(context=ssl.create_default_context())
            connection.login(self._user, self._password)
        except (smtplib.SMTPException, OSError, TimeoutError) as exc:
            raise MailDeliveryError(
                f"smtp connect/login failed for {self._host}:{self._port}: {exc}"
            ) from exc
        return connection

    def _apply_send_timeout(self, connection: SmtpConnection) -> None:
        """D-14: bound every individual send with the injected per-send timeout."""
        settimeout = getattr(getattr(connection, "sock", None), "settimeout", None)
        if settimeout is not None:
            settimeout(self._send_timeout)

    def _close(self, connection: SmtpConnection) -> None:
        try:
            connection.quit()
        except (smtplib.SMTPException, OSError, TimeoutError):
            logger.warning("smtp_mailer quit failed after digest run; connection dropped")

    def _build_message(
        self,
        recipient: Recipient,
        *,
        subject: str,
        body_text: str,
        body_html: str | None,
    ) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = (
            f"{self._from_name} <{self._from_addr}>" if self._from_name else self._from_addr
        )
        # D-05: exactly one addressee per message — no shared Bcc blast, no address leakage.
        message["To"] = recipient.email
        message.set_content(body_text)
        if body_html:
            message.add_alternative(body_html, subtype="html")
        return message
