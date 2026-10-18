"""Recipient DTO — one digest addressee resolved from `profiles` (MAIL-01, D-01…D-03)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Recipient:
    """A single digest recipient — ``profiles.email`` only (D-03)."""

    email: str
    display_name: str | None = None


def is_usable_email(email: str) -> bool:
    """D-02 / RESEARCH A1: non-empty with a local part and a domain (auth_email-shaped).

    Deliberately does **not** re-apply the ADR-0003 corporate domain allow-list — registration
    already gates domains, and the list path must not silently under-count M.

    CR-01: the predicate is the audience boundary that keeps malformed addresses away from the
    SMTP adapter, so it also rejects CR/LF/control characters (header injection), surrounding
    and embedded whitespace, commas (which the stdlib would split into two ``To`` addresses,
    D-05), and anything that is not exactly one ``@``. Such rows are excluded + logged (D-02)
    and never reach ``_build_message``.
    """
    if not email or email.count("@") != 1:
        return False
    if email.strip() != email:
        return False
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in email):
        return False
    if any(ch.isspace() or ch == "," for ch in email):
        return False
    local, _, domain = email.rpartition("@")
    return bool(local and domain)
