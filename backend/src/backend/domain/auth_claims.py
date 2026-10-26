"""Verified access-token claims (typed principal after JWT edge verify)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessTokenClaims:
    sub: str
    email: str
    role: str
