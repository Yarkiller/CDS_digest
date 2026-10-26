"""Resolve CurrentUser from verified access-token claims via ProfileRepository."""

from __future__ import annotations

from backend.application.ports.profile_repository import ProfileRepository
from backend.domain.auth_claims import AccessTokenClaims
from backend.domain.current_user import CurrentUser


def get_current_user(profiles: ProfileRepository, claims: AccessTokenClaims) -> CurrentUser:
    return profiles.get_or_upsert(claims.sub, claims.email)
