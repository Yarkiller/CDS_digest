"""Corporate email domain policy (ADR-0003 / D-04)."""

from __future__ import annotations

DEFAULT_ALLOWED_EMAIL_DOMAINS: tuple[str, ...] = ("@sberbank.ru", "@omega.sbrf.ru")


def is_allowed_corporate_email(
    email: str,
    allowed_domains: tuple[str, ...] = DEFAULT_ALLOWED_EMAIL_DOMAINS,
) -> bool:
    """Return True when email ends with an allowed domain (case-insensitive)."""
    if not email or "@" not in email:
        return False
    local, _, domain = email.rpartition("@")
    if not local or not domain:
        return False
    normalized = f"@{domain.lower()}"
    allowed = tuple(d.lower() for d in allowed_domains)
    return normalized in allowed
