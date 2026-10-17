"""Haskimail HTTP API digest delivery behind the ``Mailer`` port (MAIL-01/04/05, ADR-0005).

Why an HTTP API instead of a corporate SMTP relay: see
``docs/adr/0005-haskimail-http-api-instead-of-smtp.md``. The port contract is unchanged —
this adapter implements the same ``send_digest`` shape and returns the same delivery
payload, so the use case and the HTTP edge need no change.

Transport is the official ``haskimail`` SDK (``ServerClient``), not a hand-rolled HTTP
client: the SDK owns the request envelope, the ``X-Haskimail-Server-Token`` header, and
the typed error hierarchy, so this module only maps outcomes onto the port contract.

Locked posture (mirrors the SMTP adapter it complements):

- **D-05**: exactly one request per recipient, one ``To``, never a shared ``Cc``/``Bcc`` blast.
- **D-07**: ``sent`` / ``partial`` / ``failed`` are derived from delivered-vs-planned counts.
- **D-08**: continue past a failure, stop after three *consecutive* failures, reset the streak
  on a success, and report ``stop_reason``.
- **MAIL-04**: SDK/transport errors are counted per recipient at this boundary; nothing
  escapes upward, so an already-published digest is never turned into a 500 (D-88).
- **MAIL-05**: the API token arrives as a constructor primitive, travels only inside the
  SDK's auth header, and this module never reads the process environment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol, Sequence

from haskimail import HaskimailError, HttpError, ServerClient

from backend.domain.errors import MailDeliveryError
from backend.domain.recipient import Recipient
from backend.infrastructure.delivery_policy import (
    CONSECUTIVE_FAILURE_LIMIT,
    STOP_REASON_CONSECUTIVE_FAILURES,
    delivery_status,
)

__all__ = [
    "CONSECUTIVE_FAILURE_LIMIT",
    "DEFAULT_HASKIMAIL_API_URL",
    "HASKIMAIL_SEND_PATH",
    "STOP_REASON_CONSECUTIVE_FAILURES",
    "HaskimailMailer",
    "HaskimailResponse",
    "HaskimailSession",
    "HaskimailSessionFactory",
]

logger = logging.getLogger(__name__)

DEFAULT_HASKIMAIL_API_URL = "https://api.haskimail.ru"
"""API host the SDK appends ``HASKIMAIL_SEND_PATH`` to."""

HASKIMAIL_SEND_PATH = "/email"
"""Single-send path the SDK posts to (``POST {api_url}/email``)."""

_CONTROL_CHARS = frozenset("\r\n\t\x00")
"""CR-01 analogue: an address carrying control characters is never put on the wire."""


@dataclass(frozen=True)
class HaskimailResponse:
    """Typed, transport-agnostic view of one Haskimail send outcome."""

    status_code: int
    message_id: str | None = None
    error_code: int | None = None
    error_message: str | None = None

    @property
    def delivered(self) -> bool:
        """Success is a 2xx status with ``ErrorCode`` absent or zero (API contract)."""
        return 200 <= self.status_code < 300 and self.error_code in (None, 0)


class HaskimailSession(Protocol):
    """One authenticated SDK client reused across a single digest run."""

    def send(self, payload: dict[str, object]) -> HaskimailResponse:
        """Send one message; SDK/transport failures are returned, never raised."""
        ...

    def close(self) -> None: ...


class HaskimailSessionFactory(Protocol):
    """Opens a session for one digest run (injected in tests; the SDK by default)."""

    def __call__(
        self,
        *,
        api_url: str,
        api_key: str,
        timeout: float,
    ) -> HaskimailSession: ...


def _response_from_body(body: object) -> HaskimailResponse:
    """Map a 200 body onto the response view (the SDK returns the parsed JSON object)."""
    message_id: str | None = None
    error_code: int | None = None
    error_message: str | None = None
    if isinstance(body, dict):
        raw_id = body.get("MessageID")
        if isinstance(raw_id, str) and raw_id.strip():
            message_id = raw_id.strip()
        raw_code = body.get("ErrorCode")
        if isinstance(raw_code, int) and not isinstance(raw_code, bool):
            error_code = raw_code
        raw_message = body.get("Message")
        if isinstance(raw_message, str) and raw_message.strip():
            error_message = raw_message.strip()
    return HaskimailResponse(
        status_code=200,
        message_id=message_id,
        error_code=error_code,
        error_message=error_message,
    )


def _response_from_error(exc: HaskimailError) -> HaskimailResponse:
    """Map an SDK exception onto a failed response view (status 0 = no HTTP response)."""
    if isinstance(exc, HttpError):
        return HaskimailResponse(
            status_code=exc.status_code,
            error_code=exc.error_code or None,
            error_message=exc.message or f"HTTP {exc.status_code}",
        )
    return HaskimailResponse(status_code=0, error_message=str(exc) or "haskimail error")


class _HaskimailServerSession:
    """Default session: the official ``ServerClient``, one per digest run."""

    def __init__(self, *, api_url: str, api_key: str, timeout: float) -> None:
        self._client = ServerClient(api_key, base_url=api_url, timeout=timeout)

    def send(self, payload: dict[str, object]) -> HaskimailResponse:
        try:
            return _response_from_body(self._client.send_email(payload))
        except HaskimailError as exc:
            return _response_from_error(exc)

    def close(self) -> None:
        self._client.close()


def _default_session_factory(
    *,
    api_url: str,
    api_key: str,
    timeout: float,
) -> HaskimailSession:
    return _HaskimailServerSession(api_url=api_url, api_key=api_key, timeout=timeout)


def _is_sendable_address(address: str) -> bool:
    """Reject control characters before they reach a JSON field (CR-01 analogue)."""
    return not any(char in address for char in _CONTROL_CHARS)


class HaskimailMailer:
    """Sync per-recipient Haskimail delivery with D-08 stop policy and MAIL-04 mapping."""

    def __init__(
        self,
        *,
        api_key: str,
        from_addr: str,
        api_url: str = DEFAULT_HASKIMAIL_API_URL,
        from_name: str | None = None,
        message_stream: str | None = None,
        request_timeout: float = 30.0,
        session_factory: HaskimailSessionFactory | None = None,
    ) -> None:
        self._api_key = api_key
        self._api_url = api_url or DEFAULT_HASKIMAIL_API_URL
        self._from_addr = from_addr
        self._from_name = (from_name or "").strip() or None
        self._message_stream = (message_stream or "").strip() or None
        self._request_timeout = request_timeout
        self._session_factory: HaskimailSessionFactory = (
            session_factory or _default_session_factory
        )

    @property
    def api_url(self) -> str:
        return self._api_url

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

        session = self._open_session()
        delivered = 0
        consecutive_failures = 0
        stop_reason: str | None = None
        try:
            for recipient in audience:
                try:
                    if not _is_sendable_address(recipient.email):
                        raise ValueError("recipient address contains control characters")
                    payload = self._build_payload(
                        recipient,
                        subject=subject,
                        body_text=body_text,
                        body_html=body_html,
                    )
                    response = session.send(payload)
                    if not response.delivered:
                        raise MailDeliveryError(self._describe_failure(response))
                except (MailDeliveryError, HaskimailError, OSError, TimeoutError, ValueError) as exc:
                    consecutive_failures += 1
                    logger.warning(
                        "haskimail_mailer per-recipient failure batch_id=%s delivered=%s/%s "
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
            self._close(session)

        status = delivery_status(delivered, recipient_count)
        logger.info(
            "haskimail_mailer digest batch_id=%s recipient_count=%s delivered_count=%s status=%s",
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

    def _open_session(self) -> HaskimailSession:
        """Open the run's session; any setup failure is a ``MailDeliveryError`` (MAIL-04)."""
        try:
            return self._session_factory(
                api_url=self._api_url,
                api_key=self._api_key,
                timeout=self._request_timeout,
            )
        except (HaskimailError, OSError, TimeoutError) as exc:
            raise MailDeliveryError(
                f"haskimail session setup failed for {self._api_url}: {exc}"
            ) from exc

    def _close(self, session: HaskimailSession) -> None:
        try:
            session.close()
        except (HaskimailError, OSError, TimeoutError):
            logger.warning("haskimail_mailer session close failed; dropping connection")

    def _from_display(self) -> str:
        if self._from_name:
            return f"{self._from_name} <{self._from_addr}>"
        return self._from_addr

    def _build_payload(
        self,
        recipient: Recipient,
        *,
        subject: str,
        body_text: str,
        body_html: str | None,
    ) -> dict[str, object]:
        """D-05: exactly one ``To`` per request — no shared ``Cc``/``Bcc`` blast."""
        payload: dict[str, object] = {
            "From": self._from_display(),
            "To": recipient.email,
            "Subject": subject,
            "TextBody": body_text,
        }
        if body_html:
            payload["HtmlBody"] = body_html
        if self._message_stream:
            payload["MessageStream"] = self._message_stream
        return payload

    @staticmethod
    def _describe_failure(response: HaskimailResponse) -> str:
        """Bounded, credential-free description of a rejected send."""
        detail = response.error_message or "no message"
        code = response.error_code if response.error_code is not None else "n/a"
        return (
            f"haskimail rejected the message: status={response.status_code} "
            f"error_code={code} message={detail}"
        )
