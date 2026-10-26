"""Current authenticated user DTO returned by profile port / GET /me."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    role: str = "employee"
    display_name: str | None = None
