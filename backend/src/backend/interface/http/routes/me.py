"""Authenticated identity endpoints.

GET /me returns profiles.app_role (employee|analyst|ds|admin), default employee (D-76).
Admin HTTP authorization lives on /admin via require_admin — never from JWT role claim.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from backend.application.use_cases.get_current_user import get_current_user
from backend.application.use_cases.record_platform_ping import record_platform_ping
from backend.application.use_cases.update_display_name import update_display_name
from backend.domain.auth_claims import AccessTokenClaims
from backend.interface.http.deps import get_principal

router = APIRouter(tags=["me"])


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: str
    role: str
    display_name: str | None = None


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=120)


class PingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    id: str


def _to_response(user) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        display_name=user.display_name,
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Current authenticated user",
    description=(
        "Returns the CurrentUser DTO for a valid ES256 Bearer token with an allowed "
        "corporate email. role is profiles.app_role (D-76); admin APIs gate via "
        "require_admin on /admin."
    ),
)
def read_me(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentUserResponse:
    container = request.app.state.container
    if container is None or getattr(container, "profiles", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="profiles_not_configured",
        )
    user = get_current_user(container.profiles, claims)
    return _to_response(user)


@router.patch(
    "/me",
    response_model=CurrentUserResponse,
    summary="Update current user display name",
    description="Persists profiles.display_name for the authenticated principal.",
)
def patch_me(
    body: UpdateMeRequest,
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentUserResponse:
    container = request.app.state.container
    if container is None or getattr(container, "profiles", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="profiles_not_configured",
        )
    user = update_display_name(
        container.profiles,
        claims.sub,
        claims.email,
        body.display_name,
    )
    return _to_response(user)


@router.post(
    "/me/ping",
    response_model=PingResponse,
    summary="Record platform ping",
    description=(
        "Records a platform_ping via PingRecorder for the authenticated principal. "
        "Live activity_events persistence is Plan 04; in-memory proves D-10 offline."
    ),
)
def post_me_ping(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> PingResponse:
    container = request.app.state.container
    if container is None or getattr(container, "pings", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pings_not_configured",
        )
    recorded_id = record_platform_ping(container.pings, claims.sub)
    return PingResponse(ok=True, id=recorded_id)
