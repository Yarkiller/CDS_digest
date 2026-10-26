"""ES256 JWKS-based access-token verification (not domain / use-cases)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import jwt
from jwt import PyJWK, PyJWKClient

from backend.domain.auth_claims import AccessTokenClaims

SigningKeyResolver = Callable[[str], Mapping[str, Any] | PyJWK]


class TokenVerificationError(Exception):
    """Raised when the Bearer token cannot be verified as a valid access token."""


def verify_access_token(
    token: str,
    *,
    issuer: str,
    jwks_url: str | None = None,
    signing_key_resolver: SigningKeyResolver | None = None,
    audience: str = "authenticated",
) -> AccessTokenClaims:
    """Verify ES256 access token via injectable JWKS resolver or PyJWKClient(jwks_url)."""
    try:
        key_material = _resolve_signing_key(
            token,
            jwks_url=jwks_url,
            signing_key_resolver=signing_key_resolver,
        )
        payload = jwt.decode(
            token,
            key_material,
            algorithms=["ES256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "sub", "role"]},
        )
    except TokenVerificationError:
        raise
    except jwt.PyJWTError as exc:
        raise TokenVerificationError(str(exc)) from exc

    role = payload.get("role")
    email = payload.get("email")
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise TokenVerificationError("missing sub")
    if not isinstance(email, str) or not email:
        raise TokenVerificationError("missing email")
    if role != "authenticated":
        raise TokenVerificationError("invalid_role")

    return AccessTokenClaims(sub=sub, email=email, role=role)


def _resolve_signing_key(
    token: str,
    *,
    jwks_url: str | None,
    signing_key_resolver: SigningKeyResolver | None,
) -> Any:
    if signing_key_resolver is not None:
        try:
            resolved = signing_key_resolver(token)
            if isinstance(resolved, PyJWK):
                return resolved.key
            if isinstance(resolved, Mapping):
                return PyJWK.from_dict(dict(resolved)).key
            raise TokenVerificationError("invalid signing key resolver result")
        except TokenVerificationError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all key material failures
            raise TokenVerificationError(str(exc)) from exc

    if not jwks_url:
        raise TokenVerificationError("jwks_url or signing_key_resolver required")

    client = PyJWKClient(jwks_url)
    try:
        return client.get_signing_key_from_jwt(token).key
    except jwt.PyJWTError as exc:
        raise TokenVerificationError(str(exc)) from exc
