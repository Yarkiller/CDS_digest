"""Update authenticated user's display name via ProfileRepository."""

from __future__ import annotations

from backend.application.ports.profile_repository import ProfileRepository
from backend.domain.current_user import CurrentUser


def update_display_name(
    profiles: ProfileRepository,
    user_id: str,
    email: str,
    display_name: str,
) -> CurrentUser:
    """Ensure profile exists, then persist display_name (trimmed non-empty)."""
    profiles.get_or_upsert(user_id, email)
    return profiles.set_display_name(user_id, display_name.strip())
