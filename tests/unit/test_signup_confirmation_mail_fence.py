"""MAIL-02 / Phase 20 — signup confirmation stays on GoTrue; SPA copy is honest (B)."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEB_SRC = REPO / "web" / "src"

# SPA surfaces that own signup identity / post-register copy (MAIL-02 criterion 3 + D-08).
_SIGNUP_SURFACES = (
    WEB_SRC / "pages" / "RegisterPage.jsx",
    WEB_SRC / "services" / "authApi.js",
    WEB_SRC / "main.jsx",
)

_HONEST_CONFIRM = "Регистрация завершена. Аккаунт активен — войдите."
_MAILER_FENCE = re.compile(
    r"\b(send_digest|StubMailer|SmtpMailer|MailerPort|resolve_mailer)\b"
)
_LETTER_CLAIM = re.compile(r"письм", re.IGNORECASE)


def test_signup_surfaces_never_route_confirmation_through_backend_mailer() -> None:
    """ROADMAP SC3 / T-20-02: GoTrue owns confirmation mail — no Mailer wiring in SPA signup."""
    for path in _SIGNUP_SURFACES:
        text = path.read_text(encoding="utf-8")
        assert _MAILER_FENCE.search(text) is None, (
            f"{path.relative_to(REPO)} must not reference backend Mailer / send_digest"
        )


def test_confirm_message_is_honest_autoconfirm_copy_without_letter_claim() -> None:
    """D-07 / D-10: CONFIRM_MESSAGE is path-(B) honest copy; no confirmation-letter promise."""
    register = (WEB_SRC / "pages" / "RegisterPage.jsx").read_text(encoding="utf-8")
    match = re.search(
        r"const CONFIRM_MESSAGE\s*=\s*\n?\s*['\"]([^'\"]+)['\"]",
        register,
    )
    assert match is not None, "CONFIRM_MESSAGE constant missing from RegisterPage.jsx"
    message = match.group(1)
    assert message == _HONEST_CONFIRM
    assert _LETTER_CLAIM.search(message) is None


def test_confirm_message_lives_only_in_register_page() -> None:
    """D-08: CONFIRM_MESSAGE constant is owned by RegisterPage; authApi mapping untouched."""
    auth_api = (WEB_SRC / "services" / "authApi.js").read_text(encoding="utf-8")
    assert "CONFIRM_MESSAGE" not in auth_api
    assert _HONEST_CONFIRM not in auth_api
