"""SmtpMailer — per-recipient send, D-08 consecutive stop, MAIL-04 error mapping.

All coverage uses an injected SMTP factory double: these tests never open a socket
(no real network). TLS/posture and timeout primitives arrive from Settings (D-13/D-14),
never from ``os.environ`` inside the adapter (MAIL-05).
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Sequence

import pytest

import backend
from backend.domain.errors import MailDeliveryError
from backend.domain.recipient import Recipient
from backend.infrastructure.smtp_mailer import SmtpMailer

ISSUE_URL = "/issues/7"
BODY_TEXT = f"Новый выпуск Digest CDS.\nЧитать: {ISSUE_URL}"
BODY_HTML = "<p>Новый выпуск Digest CDS</p>"


class FakeSock:
    """Minimal socket double — records the per-send timeout applied by the adapter."""

    def __init__(self) -> None:
        self.timeouts: list[float] = []

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)


class FakeSmtpConnection:
    """Scripted ``smtplib.SMTP`` double: one outcome per ``send_message`` attempt."""

    def __init__(self, outcomes: Sequence[Exception | None] = ()) -> None:
        self._outcomes = list(outcomes)
        self.attempts = 0
        self.sent_messages: list[EmailMessage] = []
        self.starttls_contexts: list[ssl.SSLContext] = []
        self.login_credentials: list[tuple[str, str]] = []
        self.sock = FakeSock()
        self.quit_called = False

    def starttls(self, *, context: ssl.SSLContext) -> None:
        self.starttls_contexts.append(context)

    def login(self, user: str, password: str) -> None:
        self.login_credentials.append((user, password))

    def send_message(self, message: EmailMessage) -> None:
        index = self.attempts
        self.attempts += 1
        outcome = self._outcomes[index] if index < len(self._outcomes) else None
        if isinstance(outcome, Exception):
            raise outcome
        self.sent_messages.append(message)

    def quit(self) -> None:
        self.quit_called = True


class FakeSmtpFactory:
    """Records factory calls and returns a scripted connection (or raises on connect)."""

    def __init__(
        self,
        connection: FakeSmtpConnection | None = None,
        *,
        error: Exception | None = None,
    ) -> None:
        self.connection = connection if connection is not None else FakeSmtpConnection()
        self.error = error
        self.calls: list[tuple[str, int, float, bool]] = []

    def __call__(self, host: str, port: int, timeout: float, *, use_ssl: bool):
        self.calls.append((host, port, timeout, use_ssl))
        if self.error is not None:
            raise self.error
        return self.connection


def _recipients(count: int) -> list[Recipient]:
    return [
        Recipient(email=f"user{i}@sberbank.ru", display_name=f"User {i}")
        for i in range(1, count + 1)
    ]


def _mailer(factory: FakeSmtpFactory, **overrides: object) -> SmtpMailer:
    kwargs: dict[str, object] = {
        "host": "relay.example.test",
        "port": 587,
        "user": "digest-bot",
        "password": "s3cret-relay-pass",
        "from_addr": "digest@knowledge-db.ru",
        "from_name": "Digest CDS",
        "tls_mode": "starttls",
        "connect_timeout": 10.0,
        "send_timeout": 30.0,
        "smtp_factory": factory,
    }
    kwargs.update(overrides)
    return SmtpMailer(**kwargs)  # type: ignore[arg-type]


def _send(mailer: SmtpMailer, recipients: Sequence[Recipient], **overrides: object):
    kwargs: dict[str, object] = {
        "batch_id": 42,
        "issue_url": ISSUE_URL,
        "subject": "Digest CDS — выпуск 7",
        "body_text": BODY_TEXT,
        "recipient_count": len(recipients),
        "recipients": list(recipients),
    }
    kwargs.update(overrides)
    return mailer.send_digest(**kwargs)  # type: ignore[arg-type]


# --- D-05 / D-07: honest per-recipient delivery -------------------------------------


def test_smtp_mailer_sends_one_message_per_recipient() -> None:
    """D-05: N messages for N recipients, each addressed to exactly one To."""
    recipients = _recipients(3)
    factory = FakeSmtpFactory(FakeSmtpConnection())
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "sent"
    assert result["recipient_count"] == 3
    assert result["delivered_count"] == 3
    assert result["issue_url"] == ISSUE_URL
    assert "stop_reason" not in result
    assert factory.connection.attempts == 3
    assert len(factory.connection.sent_messages) == 3
    for message, recipient in zip(factory.connection.sent_messages, recipients, strict=True):
        assert len(message["To"].addresses) == 1
        assert message["To"].addresses[0].addr_spec == recipient.email
        assert message["Bcc"] is None
        assert message["Subject"] == "Digest CDS — выпуск 7"
        assert "digest@knowledge-db.ru" in str(message["From"])
        assert ISSUE_URL in message.get_body(preferencelist=("plain",)).get_content()


def test_smtp_mailer_attaches_html_alternative_when_provided() -> None:
    factory = FakeSmtpFactory(FakeSmtpConnection())
    mailer = _mailer(factory)

    _send(mailer, _recipients(1), body_html=BODY_HTML)

    message = factory.connection.sent_messages[0]
    assert message.is_multipart()
    assert [part.get_content_type() for part in message.iter_parts()] == [
        "text/plain",
        "text/html",
    ]


def test_smtp_mailer_zero_recipients_reports_sent_with_zero_delivered() -> None:
    """D-04 / RESEARCH Q3: an empty live audience is honestly ``sent`` with N=0."""
    factory = FakeSmtpFactory(FakeSmtpConnection())
    mailer = _mailer(factory)

    result = _send(mailer, [], recipient_count=0)

    assert result["delivery_status"] == "sent"
    assert result["delivered_count"] == 0
    assert factory.calls == []
    assert factory.connection.attempts == 0


def test_smtp_mailer_partial_when_some_recipients_fail() -> None:
    """D-07: 0 < N < M → partial; sending continues past a lone failure."""
    recipients = _recipients(3)
    factory = FakeSmtpFactory(
        FakeSmtpConnection([None, smtplib.SMTPServerDisconnected("relay dropped"), None])
    )
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "partial"
    assert result["delivered_count"] == 2
    assert result["recipient_count"] == 3
    assert "stop_reason" not in result
    assert factory.connection.attempts == 3


def test_smtp_mailer_failed_when_all_recipients_fail() -> None:
    recipients = _recipients(2)
    factory = FakeSmtpFactory(
        FakeSmtpConnection([OSError("refused"), OSError("refused")])
    )
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "failed"
    assert result["delivered_count"] == 0
    assert "stop_reason" not in result


def test_smtp_mailer_counts_per_recipient_timeout_without_leaking_it() -> None:
    """A per-recipient TimeoutError is a counted failure, not an escaping transport type."""
    recipients = _recipients(1)
    factory = FakeSmtpFactory(FakeSmtpConnection([TimeoutError("send timed out")]))
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "failed"
    assert result["delivered_count"] == 0


def test_smtp_mailer_counts_malformed_recipient_address_as_one_failure() -> None:
    """CR-01/D-08/MAIL-04: a header-injection address is ONE failed recipient, never an escape.

    ``_build_message`` must run inside the per-recipient guard so the stdlib ``ValueError``
    for a CR/LF ``To`` is contained (D-88) instead of 500-ing an already-published digest.
    """
    recipients = [Recipient(email="victim@x.ru\r\nBcc: attacker@y.ru")]
    factory = FakeSmtpFactory(FakeSmtpConnection())
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "failed"
    assert result["delivered_count"] == 0
    # The malformed message never reached the wire; it was counted, not sent.
    assert factory.connection.attempts == 0


# --- D-08: consecutive-failure stop with streak reset --------------------------------


def test_smtp_mailer_stops_after_three_consecutive_failures() -> None:
    """D-08: three consecutive failures stop the loop — remaining recipients untouched."""
    recipients = _recipients(5)
    factory = FakeSmtpFactory(
        FakeSmtpConnection(
            [
                smtplib.SMTPException("boom"),
                smtplib.SMTPException("boom"),
                smtplib.SMTPException("boom"),
            ]
        )
    )
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert factory.connection.attempts == 3
    assert result["delivered_count"] == 0
    assert result["delivery_status"] == "failed"
    assert result["stop_reason"] == "consecutive_failures"


def test_smtp_mailer_streak_reset_on_success_continues_sending() -> None:
    """MAIL-03/D-08 boundary: a success resets the streak, so two fails + success continue."""
    recipients = _recipients(4)
    factory = FakeSmtpFactory(
        FakeSmtpConnection([smtplib.SMTPException("a"), None, smtplib.SMTPException("b"), None])
    )
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert factory.connection.attempts == 4
    assert result["delivered_count"] == 2
    assert result["delivery_status"] == "partial"
    assert "stop_reason" not in result


def test_smtp_mailer_streak_reset_then_stop_leaves_remaining_recipients_untouched() -> None:
    """A success between failures resets the streak; the next three failures then stop."""
    recipients = _recipients(6)
    factory = FakeSmtpFactory(
        FakeSmtpConnection(
            [
                smtplib.SMTPException("a"),
                None,
                smtplib.SMTPException("b"),
                smtplib.SMTPException("c"),
                smtplib.SMTPException("d"),
            ]
        )
    )
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert factory.connection.attempts == 5
    assert result["delivered_count"] == 1
    assert result["delivery_status"] == "partial"
    assert result["stop_reason"] == "consecutive_failures"
    assert factory.connection.quit_called


# --- MAIL-04: transport errors map to MailDeliveryError at the boundary --------------


def test_smtp_mailer_connect_failure_maps_to_mail_delivery_error() -> None:
    factory = FakeSmtpFactory(error=OSError("connection refused"))
    mailer = _mailer(factory)

    with pytest.raises(MailDeliveryError):
        _send(mailer, _recipients(2))


def test_smtp_mailer_starttls_failure_maps_to_mail_delivery_error() -> None:
    class UnsupportedTlsConnection(FakeSmtpConnection):
        def starttls(self, *, context: ssl.SSLContext) -> None:
            raise smtplib.SMTPNotSupportedError("STARTTLS not supported")

    factory = FakeSmtpFactory(UnsupportedTlsConnection())
    mailer = _mailer(factory)

    with pytest.raises(MailDeliveryError):
        _send(mailer, _recipients(1))


def test_smtp_mailer_authentication_failure_maps_to_mail_delivery_error() -> None:
    class RejectingConnection(FakeSmtpConnection):
        def login(self, user: str, password: str) -> None:
            raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

    factory = FakeSmtpFactory(RejectingConnection())
    mailer = _mailer(factory)

    with pytest.raises(MailDeliveryError):
        _send(mailer, _recipients(1))


def test_smtp_mailer_connect_timeout_maps_to_mail_delivery_error() -> None:
    factory = FakeSmtpFactory(error=TimeoutError("connect timed out"))
    mailer = _mailer(factory)

    with pytest.raises(MailDeliveryError):
        _send(mailer, _recipients(1))


# --- D-13 / D-14: TLS posture + fixed timeouts as injected primitives ----------------


def test_smtp_mailer_starttls_default_uses_default_context_and_connect_timeout() -> None:
    factory = FakeSmtpFactory(FakeSmtpConnection())
    mailer = _mailer(factory, tls_mode="starttls", connect_timeout=10.0)

    _send(mailer, _recipients(1))

    assert factory.calls == [("relay.example.test", 587, 10.0, False)]
    assert len(factory.connection.starttls_contexts) == 1
    assert isinstance(factory.connection.starttls_contexts[0], ssl.SSLContext)


def test_smtp_mailer_ssl_mode_uses_implicit_tls_transport() -> None:
    factory = FakeSmtpFactory(FakeSmtpConnection())
    mailer = _mailer(factory, tls_mode="ssl", port=465)

    _send(mailer, _recipients(1))

    assert factory.calls == [("relay.example.test", 465, 10.0, True)]
    assert factory.connection.starttls_contexts == []


def test_smtp_mailer_none_mode_skips_tls() -> None:
    factory = FakeSmtpFactory(FakeSmtpConnection())
    mailer = _mailer(factory, tls_mode="none")

    _send(mailer, _recipients(1))

    assert factory.calls == [("relay.example.test", 587, 10.0, False)]
    assert factory.connection.starttls_contexts == []


def test_smtp_mailer_applies_send_timeout_to_socket() -> None:
    """D-14: per-send timeout is a fixed injected primitive applied to the live socket."""
    factory = FakeSmtpFactory(FakeSmtpConnection())
    mailer = _mailer(factory, send_timeout=30.0)

    _send(mailer, _recipients(1))

    assert factory.connection.sock.timeouts == [30.0]


def test_smtp_mailer_send_timeout_failure_maps_to_mail_delivery_error() -> None:
    """WR-01 / MAIL-04: an ``OSError`` applying the send timeout maps at the adapter boundary.

    The timeout is applied during connection setup, so a stale/closed fd must surface as
    ``MailDeliveryError`` — never an escaping ``OSError`` that 500s a published digest.
    """
    class RefusingTimeoutSock:
        def settimeout(self, value: float) -> None:
            raise OSError("bad file descriptor")

    class RefusingTimeoutConnection(FakeSmtpConnection):
        def __init__(self) -> None:
            super().__init__()
            self.sock = RefusingTimeoutSock()

    factory = FakeSmtpFactory(RefusingTimeoutConnection())
    mailer = _mailer(factory, send_timeout=30.0)

    with pytest.raises(MailDeliveryError):
        _send(mailer, _recipients(1))


def test_smtp_mailer_logs_never_contain_the_relay_password(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T-21-04: credentials must not reach logs, even on transport failure."""
    factory = FakeSmtpFactory(
        FakeSmtpConnection([smtplib.SMTPException("boom"), smtplib.SMTPException("boom")])
    )
    mailer = _mailer(factory)

    with caplog.at_level(logging.DEBUG):
        _send(mailer, _recipients(2))

    assert "s3cret-relay-pass" not in caplog.text


# --- MAIL-04 / MAIL-05: architecture tripwires ---------------------------------------


def test_smtp_mailer_never_reads_process_environment() -> None:
    """MAIL-05: the adapter receives primitives only — no env reads in the module source."""
    source = Path(__file__).resolve().parents[2].joinpath(
        "backend/src/backend/infrastructure/smtp_mailer.py"
    ).read_text(encoding="utf-8")

    assert "os.environ" not in source
    assert "getenv" not in source
    assert "import os" not in source


def test_smtplib_import_stays_out_of_domain_and_application() -> None:
    """MAIL-04: use cases and domain must never import the transport library."""
    package_root = Path(backend.__file__).resolve().parent
    guarded = [package_root / "domain", package_root / "application"]
    offenders: list[str] = []
    for directory in guarded:
        for path in directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "import smtplib" in text or "from smtplib" in text:
                offenders.append(str(path.relative_to(package_root)))

    assert offenders == []
