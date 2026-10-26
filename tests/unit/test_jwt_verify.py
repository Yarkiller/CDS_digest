"""Offline ES256 JWKS verification for Supabase-shaped access tokens."""

from __future__ import annotations

import json
import time
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from jwt.algorithms import ECAlgorithm

from backend.infrastructure.auth_jwt import AccessTokenClaims, TokenVerificationError, verify_access_token


def _public_jwk(private_key: ec.EllipticCurvePrivateKey) -> dict[str, Any]:
    data = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
    data["kid"] = "test-kid-1"
    data["alg"] = "ES256"
    data["use"] = "sig"
    return data


def _es256_keypair() -> tuple[ec.EllipticCurvePrivateKey, dict[str, Any]]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key, _public_jwk(private_key)


def _mint(
    private_key: ec.EllipticCurvePrivateKey,
    *,
    email: str = "user@sberbank.ru",
    role: str = "authenticated",
    aud: str = "authenticated",
    iss: str = "https://auth.example/auth/v1",
    exp_delta: int = 3600,
) -> str:
    now = int(time.time())
    payload = {
        "sub": "user-uuid-1",
        "email": email,
        "role": role,
        "aud": aud,
        "iss": iss,
        "exp": now + exp_delta,
        "iat": now,
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "test-kid-1"})


def test_verify_access_token_accepts_valid_es256_jwt() -> None:
    private_key, public_jwk = _es256_keypair()
    token = _mint(private_key)
    claims = verify_access_token(
        token,
        issuer="https://auth.example/auth/v1",
        signing_key_resolver=lambda _t: public_jwk,
    )
    assert isinstance(claims, AccessTokenClaims)
    assert claims.sub == "user-uuid-1"
    assert claims.email == "user@sberbank.ru"
    assert claims.role == "authenticated"


def test_verify_access_token_rejects_hs256() -> None:
    _private_key, public_jwk = _es256_keypair()
    token = jwt.encode(
        {
            "sub": "u1",
            "email": "user@sberbank.ru",
            "role": "authenticated",
            "aud": "authenticated",
            "iss": "https://auth.example/auth/v1",
            "exp": int(time.time()) + 60,
        },
        "shared-secret-at-least-32-bytes-long!!",
        algorithm="HS256",
    )
    try:
        verify_access_token(
            token,
            issuer="https://auth.example/auth/v1",
            signing_key_resolver=lambda _t: public_jwk,
        )
        raise AssertionError("expected TokenVerificationError")
    except TokenVerificationError:
        pass


def test_verify_access_token_rejects_expired() -> None:
    private_key, public_jwk = _es256_keypair()
    token = _mint(private_key, exp_delta=-10)
    try:
        verify_access_token(
            token,
            issuer="https://auth.example/auth/v1",
            signing_key_resolver=lambda _t: public_jwk,
        )
        raise AssertionError("expected TokenVerificationError")
    except TokenVerificationError:
        pass


def test_verify_access_token_rejects_wrong_audience() -> None:
    private_key, public_jwk = _es256_keypair()
    token = _mint(private_key, aud="anon")
    try:
        verify_access_token(
            token,
            issuer="https://auth.example/auth/v1",
            signing_key_resolver=lambda _t: public_jwk,
        )
        raise AssertionError("expected TokenVerificationError")
    except TokenVerificationError:
        pass
