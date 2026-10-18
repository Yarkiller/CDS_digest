"""HTTP dependencies: Bearer JWT verify + corporate email gate + admin role gate."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWK

from backend.application.use_cases.get_current_user import get_current_user
from backend.domain.auth_claims import AccessTokenClaims
from backend.domain.auth_email import DEFAULT_ALLOWED_EMAIL_DOMAINS, is_allowed_corporate_email
from backend.domain.current_user import CurrentUser
from backend.infrastructure.auth_jwt import TokenVerificationError, verify_access_token

_bearer = HTTPBearer(auto_error=True)


def get_principal(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> AccessTokenClaims:
    settings = request.app.state.settings
    resolver: Callable[[str], Mapping[str, Any] | PyJWK] | None = getattr(
        request.app.state,
        "signing_key_resolver",
        None,
    )
    try:
        claims = verify_access_token(
            creds.credentials,
            issuer=settings.supabase_jwt_issuer,
            jwks_url=settings.supabase_jwks_url or None,
            signing_key_resolver=resolver,
        )
    except TokenVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

    domains = settings.email_domains or DEFAULT_ALLOWED_EMAIL_DOMAINS
    if not is_allowed_corporate_email(claims.email, allowed_domains=domains):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="domain_not_allowed",
        )
    return claims


def require_admin(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentUser:
    """Authorize admin from profiles.role only — never JWT role claim (D-74 / AUTH-03)."""
    container = request.app.state.container
    if container is None or getattr(container, "profiles", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="profiles_not_configured",
        )
    user = get_current_user(container.profiles, claims)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden",
        )
    return user
