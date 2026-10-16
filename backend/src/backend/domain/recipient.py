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
    """
    if not email or "@" not in email:
        return False
    local, _, domain = email.rpartition("@")
    return bool(local and domain)
