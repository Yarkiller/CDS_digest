"""Mailer selection — the one place that maps Settings onto a stub or live SMTP adapter.

This lives in ``composition`` (not ``infrastructure``) because choosing an adapter **is**
wiring, and ``infrastructure`` must never depend on composition (``architecture.mdc``).
The adapters therefore stay environment-agnostic: ``SmtpMailer`` receives ready primitives
only, and no module outside composition reads ``SMTP_*`` from the process environment.
"""

from __future__ import annotations

from backend.composition.config_error import ConfigurationError
from backend.composition.settings import Settings
from backend.infrastructure.smtp_mailer import SmtpMailer
from backend.infrastructure.stub_mailer import StubMailer

ALLOWED_TLS_MODES = ("starttls", "ssl", "none")
"""D-13: starttls is the default; ssl (implicit TLS) and none are operator overrides."""

_REQUIRED_SMTP_FIELDS = (
    ("SMTP_HOST", "smtp_host"),
    ("SMTP_PORT", "smtp_port"),
    ("SMTP_USER", "smtp_user"),
    ("SMTP_PASS", "smtp_pass"),
    ("SMTP_FROM", "smtp_from"),
)
"""D-16: minimum env set required before ``MAILER=smtp`` may construct a live transport."""


def resolve_mailer(settings: Settings) -> StubMailer | SmtpMailer:
    """Wire the digest mailer from ``MAILER`` (D-15) with fail-fast config (D-16)."""
    mode = (settings.mailer or "stub").strip().lower() or "stub"
    if mode == "stub":
        return StubMailer()
    if mode == "smtp":
        return _build_smtp_mailer(settings)
    raise ConfigurationError(f"Unknown MAILER={mode!r}; use 'stub' or 'smtp'")


def _build_smtp_mailer(settings: Settings) -> SmtpMailer:
    """D-16: incomplete ``SMTP_*`` with ``MAILER=smtp`` fails here — never a stub fallback."""
    missing = [
        env_name
        for env_name, attr in _REQUIRED_SMTP_FIELDS
        if getattr(settings, attr) in (None, "")
    ]
    if missing:
        raise ConfigurationError(
            "MAILER=smtp requires "
            + ", ".join(missing)
            + " — refusing to fall back to stub (D-16)"
        )

    port = settings.smtp_port
    if not isinstance(port, int):  # narrowing guard; unreachable after the check above
        raise ConfigurationError(
            "MAILER=smtp requires SMTP_PORT — refusing to fall back to stub (D-16)"
        )

    tls_mode = (settings.smtp_tls_mode or "starttls").strip().lower() or "starttls"
    if tls_mode not in ALLOWED_TLS_MODES:
        raise ConfigurationError(
            f"SMTP_TLS_MODE={tls_mode!r} must be one of {', '.join(ALLOWED_TLS_MODES)}"
        )

    return SmtpMailer(
        host=settings.smtp_host,
        port=port,
        user=settings.smtp_user,
        password=settings.smtp_pass,
        from_addr=settings.smtp_from,
        from_name=settings.smtp_from_name or None,
        tls_mode=tls_mode,
        connect_timeout=settings.smtp_connect_timeout,
        send_timeout=settings.smtp_send_timeout,
    )
