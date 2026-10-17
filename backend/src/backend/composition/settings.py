"""Env-backed settings for HTTP edge and later JWT/Supabase wiring."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from backend.composition.config_error import ConfigurationError


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _read_smtp_port(env: Mapping[str, str]) -> int | None:
    """D-16: ``SMTP_PORT`` must be an explicit in-range integer, otherwise it stays unset.

    IN-03: ``0`` (and anything outside 1..65535) is rejected here so an invalid port fails
    fast at startup instead of passing the completeness check and hot-looping at connect.
    """
    raw = (env.get("SMTP_PORT") or "").strip()
    if not raw:
        return None
    if not raw.isdigit():
        raise ConfigurationError(f"SMTP_PORT must be an integer, got {raw!r}")
    port = int(raw)
    if not (1 <= port <= 65535):
        raise ConfigurationError(f"SMTP_PORT must be in 1..65535, got {raw!r}")
    return port


@dataclass(frozen=True)
class Settings:
    api_cors_origins: str = ""
    allowed_email_domains: str = ""
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    supabase_jwks_url: str = ""
    supabase_jwt_issuer: str = ""
    # memory (default, unit tests) | live (Supabase adapters via composition/live.py)
    app_container: str = "memory"
    # Local filesystem root for authenticated .ipynb FileResponse (RAZB-03 / A5)
    notebook_root: str = ""
    # stub (default, D-15) | smtp (live relay) | haskimail (live HTTP API, ADR-0005)
    # resolve_mailer fails fast when the selected mode's config is incomplete (D-16).
    mailer: str = "stub"
    # Absolute site origin for email material links (D-11 / RESEARCH Q2)
    site_url: str = "http://127.0.0.1:5173"
    # --- Live SMTP relay (MAIL-05: read from the process env only in Settings.from_env) ---
    smtp_host: str = ""
    # None = "SMTP_PORT not configured"; D-16 requires an explicit value for MAILER=smtp.
    smtp_port: int | None = None
    smtp_user: str = ""
    # repr=False: a logged Settings must never disclose the relay credential (T-21-04).
    smtp_pass: str = field(default="", repr=False)
    smtp_from: str = ""
    smtp_from_name: str = ""
    # D-13: starttls (relay port 587) by default; operator may override with ssl | none.
    smtp_tls_mode: str = "starttls"
    # D-14: bounded timeouts are fixed here and injected as primitives — never env-driven.
    smtp_connect_timeout: float = 10.0
    smtp_send_timeout: float = 30.0
    # --- Live Haskimail HTTP API (ADR-0005; MAIL-05: read env only in from_env) ---
    # repr=False: a logged Settings must never disclose the server token.
    haskimail_api_key: str = field(default="", repr=False)
    # "" = use the adapter's canonical endpoint (https://api.haskimail.ru/email).
    haskimail_api_url: str = ""
    haskimail_from: str = ""
    haskimail_from_name: str = ""
    # Optional channel id; empty = the server's default transactional stream.
    haskimail_message_stream: str = ""
    # Fixed request timeout (D-14 analogue) — env cannot widen it.
    haskimail_request_timeout: float = 30.0

    @property
    def cors_origins(self) -> tuple[str, ...]:
        return _split_csv(self.api_cors_origins)

    @property
    def email_domains(self) -> tuple[str, ...]:
        return _split_csv(self.allowed_email_domains)

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        env = environ if environ is not None else os.environ
        mode = (env.get("APP_CONTAINER") or "memory").strip().lower() or "memory"
        if mode not in ("memory", "live"):
            mode = "memory"
        mailer = (env.get("MAILER") or "stub").strip().lower() or "stub"
        smtp_port = _read_smtp_port(env)
        default_site = "http://127.0.0.1:5173"
        site_url = (
            (env.get("SITE_URL") or "").strip()
            or (env.get("PUBLIC_SITE_URL") or "").strip()
            or default_site
        )
        return cls(
            api_cors_origins=env.get("API_CORS_ORIGINS", ""),
            allowed_email_domains=env.get("ALLOWED_EMAIL_DOMAINS", ""),
            supabase_url=env.get("SUPABASE_URL", ""),
            supabase_publishable_key=env.get("SUPABASE_PUBLISHABLE_KEY", ""),
            supabase_secret_key=env.get("SUPABASE_SECRET_KEY", ""),
            supabase_jwks_url=env.get("SUPABASE_JWKS_URL", ""),
            supabase_jwt_issuer=env.get("SUPABASE_JWT_ISSUER", ""),
            app_container=mode,
            notebook_root=env.get("NOTEBOOK_ROOT", ""),
            mailer=mailer,
            site_url=site_url,
            smtp_host=env.get("SMTP_HOST", ""),
            smtp_port=smtp_port,
            smtp_user=env.get("SMTP_USER", ""),
            smtp_pass=env.get("SMTP_PASS", ""),
            smtp_from=env.get("SMTP_FROM", ""),
            smtp_from_name=env.get("SMTP_FROM_NAME", ""),
            smtp_tls_mode=(env.get("SMTP_TLS_MODE") or "starttls").strip().lower()
            or "starttls",
            haskimail_api_key=env.get("HASKIMAIL_API_KEY", ""),
            haskimail_api_url=env.get("HASKIMAIL_API_URL", "").strip(),
            haskimail_from=env.get("HASKIMAIL_FROM", ""),
            haskimail_from_name=env.get("HASKIMAIL_FROM_NAME", ""),
            haskimail_message_stream=env.get("HASKIMAIL_MESSAGE_STREAM", ""),
        )
