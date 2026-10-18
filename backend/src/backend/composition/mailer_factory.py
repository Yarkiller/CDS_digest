"""Mailer selection — the one place that maps Settings onto a stub or live adapter.

This lives in ``composition`` (not ``infrastructure``) because choosing an adapter **is**
wiring, and ``infrastructure`` must never depend on composition (``architecture.mdc``).
The adapters therefore stay environment-agnostic: ``SmtpMailer`` / ``HaskimailMailer``
receive ready primitives only, and no module outside composition reads ``SMTP_*`` or
``HASKIMAIL_*`` from the process environment.

Live transports (``MAILER=smtp`` | ``MAILER=haskimail``) fail fast on incomplete config —
never a silent ``StubMailer`` fallback (D-16). ADR-0005 records why the HTTP API is the
preferred live transport.
"""

from __future__ import annotations

from backend.composition.config_error import ConfigurationError
from backend.composition.settings import Settings
from backend.infrastructure.haskimail_mailer import HaskimailMailer
from backend.infrastructure.smtp_mailer import SmtpMailer
from backend.infrastructure.stub_mailer import StubMailer

ALLOWED_TLS_MODES = ("starttls", "ssl", "none")
"""D-13: starttls is the default; ssl (implicit TLS) and none are operator overrides."""

ALLOWED_MAILER_MODES = ("stub", "smtp", "haskimail")
"""D-15 / ADR-0005: stub (default) plus two live transports."""

_REQUIRED_SMTP_FIELDS = (
    ("SMTP_HOST", "smtp_host"),
    ("SMTP_PORT", "smtp_port"),
    ("SMTP_USER", "smtp_user"),
    ("SMTP_PASS", "smtp_pass"),
    ("SMTP_FROM", "smtp_from"),
)
"""D-16: minimum env set required before ``MAILER=smtp`` may construct a live transport."""

_REQUIRED_HASKIMAIL_FIELDS = (
    ("HASKIMAIL_API_KEY", "haskimail_api_key"),
    ("HASKIMAIL_FROM", "haskimail_from"),
)
"""D-16 analogue: the server token and a verified-domain sender are both mandatory."""


def resolve_mailer(settings: Settings) -> StubMailer | SmtpMailer | HaskimailMailer:
    """Wire the digest mailer from ``MAILER`` (D-15) with fail-fast config (D-16)."""
    mode = (settings.mailer or "stub").strip().lower() or "stub"
    if mode == "stub":
        return StubMailer()
    if mode == "smtp":
        return _build_smtp_mailer(settings)
    if mode == "haskimail":
        return _build_haskimail_mailer(settings)
    raise ConfigurationError(
        f"Unknown MAILER={mode!r}; use one of {', '.join(ALLOWED_MAILER_MODES)}"
    )


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


def _build_haskimail_mailer(settings: Settings) -> HaskimailMailer:
    """D-16 analogue: incomplete ``HASKIMAIL_*`` fails here — never a stub fallback.

    MAIL-05: the endpoint must be HTTPS. The server token travels in a request header,
    so a plaintext ``http://`` base URL would leak the credential on the wire.
    """
    missing = [
        env_name
        for env_name, attr in _REQUIRED_HASKIMAIL_FIELDS
        if getattr(settings, attr) in (None, "")
    ]
    if missing:
        raise ConfigurationError(
            "MAILER=haskimail requires "
            + ", ".join(missing)
            + " — refusing to fall back to stub (D-16)"
        )

    api_url = (settings.haskimail_api_url or "").strip()
    if api_url and not api_url.lower().startswith("https://"):
        raise ConfigurationError(
            f"HASKIMAIL_API_URL={api_url!r} must be an https:// URL — the server token "
            "must never travel over plaintext HTTP (MAIL-05)"
        )

    return HaskimailMailer(
        api_key=settings.haskimail_api_key,
        api_url=api_url,
        from_addr=settings.haskimail_from,
        from_name=settings.haskimail_from_name or None,
        message_stream=settings.haskimail_message_stream or None,
        request_timeout=settings.haskimail_request_timeout,
    )
