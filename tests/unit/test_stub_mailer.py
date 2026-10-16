"""StubMailer honesty + SMTP fail-fast (ADMIN-07/08, D-87)."""

from __future__ import annotations

import pytest

from backend.composition.settings import Settings
from backend.infrastructure.stub_mailer import SmtpMailer, StubMailer, resolve_mailer


def test_stub_mailer_returns_stubbed_delivery_and_zero_recipients() -> None:
    """D-87: delivery_status=stubbed; recipient_count=0; body retains issue_url."""
    mailer = StubMailer()
    issue_url = "/issues/7"
    body = f"Читать выпуск: {issue_url}"

    result = mailer.send_digest(
        batch_id=42,
        issue_url=issue_url,
        subject="Digest CDS — выпуск 7",
        body_text=body,
        recipient_count=0,
    )

    assert result["delivery_status"] == "stubbed"
    assert result["recipient_count"] == 0
    assert result["issue_url"] == issue_url
    assert issue_url in mailer.last_body_text
    assert mailer.last_subject == "Digest CDS — выпуск 7"
    assert mailer.last_batch_id == 42


def test_smtp_mailer_import_path_is_stable_and_real() -> None:
    """Plan 02: the historical ``stub_mailer`` import path re-exports the real adapter."""
    assert SmtpMailer is not StubMailer
    mailer = SmtpMailer(
        host="relay.example.test",
        port=587,
        user="digest-bot",
        password="unused-in-constructor",
        from_addr="digest@knowledge-db.ru",
    )
    assert callable(mailer.send_digest)


def test_settings_mailer_defaults_to_stub() -> None:
    settings = Settings.from_env({})
    assert settings.mailer == "stub"


def test_resolve_mailer_smtp_fails_fast_at_startup() -> None:
    """D-87: MAILER=smtp → clear startup error; no send attempt."""
    settings = Settings.from_env({"MAILER": "smtp"})
    assert settings.mailer == "smtp"
    with pytest.raises(RuntimeError, match="SMTP не настроен"):
        resolve_mailer(settings.mailer)
