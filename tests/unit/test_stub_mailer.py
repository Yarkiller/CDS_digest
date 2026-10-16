"""StubMailer honesty + SMTP fail-fast (D-15/D-16, MAIL-05)."""

from __future__ import annotations

import pytest

from backend.composition.config_error import ConfigurationError
from backend.composition.mailer_factory import resolve_mailer
from backend.composition.settings import Settings
from backend.infrastructure.stub_mailer import SmtpMailer, StubMailer


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
    assert result["delivered_count"] == 0
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
    """D-15: MAILER defaults to stub; live SMTP is an explicit ops flip."""
    settings = Settings.from_env({})
    assert settings.mailer == "stub"


def test_resolve_mailer_defaults_to_stub() -> None:
    assert isinstance(resolve_mailer(Settings()), StubMailer)


def test_resolve_mailer_stub_mode_returns_stub_mailer() -> None:
    assert isinstance(resolve_mailer(Settings(mailer="stub")), StubMailer)


def test_resolve_mailer_smtp_with_complete_settings_builds_smtp_mailer() -> None:
    """D-15: SmtpMailer is selected only when MAILER=smtp and SMTP_* are complete."""
    settings = Settings(
        mailer="smtp",
        smtp_host="relay.example.test",
        smtp_port=587,
        smtp_user="digest-bot",
        smtp_pass="s3cret",
        smtp_from="digest@knowledge-db.ru",
        smtp_from_name="Digest CDS",
    )

    mailer = resolve_mailer(settings)

    assert isinstance(mailer, SmtpMailer)


def test_resolve_mailer_smtp_without_required_fields_fails_fast() -> None:
    """D-16: incomplete SMTP_* with MAILER=smtp raises at resolve — never a stub fallback."""
    with pytest.raises(ConfigurationError, match="SMTP_HOST"):
        resolve_mailer(Settings(mailer="smtp"))


@pytest.mark.parametrize(
    ("missing_field", "blank"),
    [
        ("smtp_host", ""),
        ("smtp_port", None),
        ("smtp_user", ""),
        ("smtp_pass", ""),
        ("smtp_from", ""),
    ],
)
def test_resolve_mailer_smtp_requires_each_field(
    missing_field: str, blank: object
) -> None:
    """D-16: HOST/PORT/USER/PASS/FROM are each required for live SMTP."""
    complete: dict[str, object] = {
        "mailer": "smtp",
        "smtp_host": "relay.example.test",
        "smtp_port": 587,
        "smtp_user": "digest-bot",
        "smtp_pass": "s3cret",
        "smtp_from": "digest@knowledge-db.ru",
    }
    complete[missing_field] = blank

    with pytest.raises(ConfigurationError):
        resolve_mailer(Settings(**complete))  # type: ignore[arg-type]


def test_resolve_mailer_smtp_never_silently_returns_stub() -> None:
    """D-16 honesty tripwire: a misconfigured smtp mode must not produce a StubMailer."""
    settings = Settings(mailer="smtp", smtp_host="relay.example.test")

    with pytest.raises(ConfigurationError):
        resolve_mailer(settings)


def test_resolve_mailer_rejects_unknown_mode() -> None:
    with pytest.raises(ConfigurationError, match="MAILER"):
        resolve_mailer(Settings(mailer="sendmail"))


def test_resolve_mailer_smtp_rejects_invalid_tls_mode() -> None:
    """D-13: SMTP_TLS_MODE is constrained to starttls | ssl | none."""
    settings = Settings(
        mailer="smtp",
        smtp_host="relay.example.test",
        smtp_port=587,
        smtp_user="digest-bot",
        smtp_pass="s3cret",
        smtp_from="digest@knowledge-db.ru",
        smtp_tls_mode="implicit",
    )

    with pytest.raises(ConfigurationError, match="SMTP_TLS_MODE"):
        resolve_mailer(settings)


def test_settings_from_env_reads_smtp_fields_and_defaults_posture() -> None:
    """D-13/D-14: env supplies relay values; TLS defaults to starttls and timeouts are fixed."""
    settings = Settings.from_env(
        {
            "MAILER": "smtp",
            "SMTP_HOST": "relay.example.test",
            "SMTP_PORT": "587",
            "SMTP_USER": "digest-bot",
            "SMTP_PASS": "s3cret",
            "SMTP_FROM": "digest@knowledge-db.ru",
            "SMTP_FROM_NAME": "Digest CDS",
        }
    )

    assert settings.mailer == "smtp"
    assert settings.smtp_host == "relay.example.test"
    assert settings.smtp_port == 587
    assert settings.smtp_user == "digest-bot"
    assert settings.smtp_pass == "s3cret"
    assert settings.smtp_from == "digest@knowledge-db.ru"
    assert settings.smtp_from_name == "Digest CDS"
    assert settings.smtp_tls_mode == "starttls"
    assert settings.smtp_connect_timeout == 10.0
    assert settings.smtp_send_timeout == 30.0


def test_settings_smtp_fields_default_to_unset_when_env_absent() -> None:
    settings = Settings.from_env({})

    assert settings.smtp_host == ""
    assert settings.smtp_port is None
    assert settings.smtp_user == ""
    assert settings.smtp_pass == ""
    assert settings.smtp_from == ""
    assert settings.smtp_from_name == ""
    assert settings.smtp_tls_mode == "starttls"
    assert settings.smtp_connect_timeout == 10.0
    assert settings.smtp_send_timeout == 30.0


def test_settings_timeouts_are_not_env_driven() -> None:
    """D-14: timeouts are fixed Settings defaults — env cannot widen the DoS window."""
    settings = Settings.from_env(
        {
            "SMTP_CONNECT_TIMEOUT": "600",
            "SMTP_SEND_TIMEOUT": "600",
            "SMTP_TIMEOUT": "600",
        }
    )

    assert settings.smtp_connect_timeout == 10.0
    assert settings.smtp_send_timeout == 30.0


def test_settings_repr_never_leaks_the_smtp_password() -> None:
    """T-21-04: a logged Settings must not disclose the relay credential."""
    settings = Settings(mailer="smtp", smtp_pass="hunter2-relay-secret")

    assert "hunter2-relay-secret" not in repr(settings)
