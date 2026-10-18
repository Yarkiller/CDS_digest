"""Closed audience-role set for ingestion drafts (D-14). Not a public export."""

from __future__ import annotations

from typing import Literal

RoleKind = Literal["employee", "analyst", "ds"]
VALID_ROLES: frozenset[str] = frozenset({"employee", "analyst", "ds"})


def normalize_roles(value: object) -> list[RoleKind]:
    """Filter unknown roles; empty or malformed input becomes ['employee']."""
    if not isinstance(value, list):
        return ["employee"]
    filtered: list[RoleKind] = [role for role in value if role in VALID_ROLES]
    return filtered or ["employee"]
