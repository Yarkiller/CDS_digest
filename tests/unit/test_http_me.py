"""Authenticated GET /me and POST /me/ping — JWT gate (AUTH-01 / AUTH-03 / PLAT-03/04)."""

from __future__ import annotations

import json
import time
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

from backend.application.use_cases.record_platform_ping import PLATFORM_PING_KIND
from backend.composition.container import AppContainer, build_in_memory_container
from backend.composition.settings import Settings
from backend.interface.http.app import create_app


ISSUER = "https://auth.example/auth/v1"


def _public_jwk(private_key: ec.EllipticCurvePrivateKey) -> dict[str, Any]:
    data = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
    data["kid"] = "test-kid-1"
    data["alg"] = "ES256"
    data["use"] = "sig"
    return data


def _mint(
    private_key: ec.EllipticCurvePrivateKey,
    *,
    email: str,
    role: str = "authenticated",
) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "user-uuid-1",
            "email": email,
            "role": role,
            "aud": "authenticated",
            "iss": ISSUER,
            "exp": now + 3600,
            "iat": now,
        },
        private_key,
        algorithm="ES256",
        headers={"kid": "test-kid-1"},
    )


def _app_bundle(signing_jwk: dict[str, Any]) -> tuple[TestClient, AppContainer]:
    settings = Settings(
        api_cors_origins="http://127.0.0.1:5173",
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
        supabase_url="",
        supabase_publishable_key="",
        supabase_secret_key="",
        supabase_jwks_url="https://unused.example/jwks.json",
        supabase_jwt_issuer=ISSUER,
    )
    container = build_in_memory_container()
    app = create_app(
        settings,
        container=container,
        signing_key_resolver=lambda _token: signing_jwk,
    )
    return TestClient(app), container


def _client(signing_jwk: dict[str, Any]) -> TestClient:
    client, _container = _app_bundle(signing_jwk)
    return client


def test_me_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.get("/me")
    assert response.status_code == 401


def test_me_with_valid_corporate_jwt_returns_current_user() -> None:
    """GET /me.role is app_role (default employee), never JWT role claim (D-76)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "id": "user-uuid-1",
        "email": "alice@sberbank.ru",
        "role": "employee",
        "display_name": None,
    }


def test_me_with_seeded_admin_profile_returns_role_admin() -> None:
    """Seeded profiles.role=admin is returned on GET /me (D-76); JWT claim stays authenticated."""
    from backend.domain.current_user import CurrentUser

    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client, container = _app_bundle(jwk)
    container.profiles._by_id["user-uuid-1"] = CurrentUser(
        id="user-uuid-1",
        email="alice@sberbank.ru",
        role="admin",
        display_name=None,
    )
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_patch_me_sets_display_name_and_returns_updated_user() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk)
    token = _mint(private_key, email="alice@sberbank.ru")
    headers = {"Authorization": f"Bearer {token}"}

    patched = client.patch(
        "/me",
        headers=headers,
        json={"display_name": "Алиса Иванова"},
    )
    assert patched.status_code == 200
    assert patched.json() == {
        "id": "user-uuid-1",
        "email": "alice@sberbank.ru",
        "role": "employee",
        "display_name": "Алиса Иванова",
    }

    fetched = client.get("/me", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["display_name"] == "Алиса Иванова"


def test_me_with_disallowed_email_domain_returns_403() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk)
    token = _mint(private_key, email="alice@gmail.com")
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "domain_not_allowed"


def test_me_ping_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.post("/me/ping")
    assert response.status_code == 401


def test_me_ping_with_invalid_bearer_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.post(
        "/me/ping",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401


def test_me_ping_with_valid_corporate_jwt_records_platform_ping() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client, container = _app_bundle(jwk)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.post("/me/ping", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "id" in body
    entries = container.pings.entries_for("user-uuid-1")
    assert len(entries) == 1
    assert entries[0].kind == PLATFORM_PING_KIND
    assert entries[0].id == body["id"]
