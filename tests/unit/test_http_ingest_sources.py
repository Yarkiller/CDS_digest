"""RED→GREEN: GET/POST /admin/ingest-sources tracer — SRC-01/SRC-03, D-18/D-21.

Copies the ES256 JWT + container-attach harness style from
tests/unit/test_http_pipeline_config.py (D-23 PRESERVE — do not edit that file).

Imports of not-yet-shipped symbols are deferred inside helpers so collection
succeeds and failures are assertion-level RED (missing routes / wiring), not
import noise.
"""

from __future__ import annotations

import json
import time
from typing import Any

import jwt
import pytest
from backend.composition.container import AppContainer, build_in_memory_container
from backend.composition.settings import Settings
from backend.domain.current_user import CurrentUser
from backend.interface.http.app import create_app
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

ISSUER = "https://auth.example/auth/v1"
SOURCES_URL = "/admin/ingest-sources"

# D-14 valid channel: UC + 22 [A-Za-z0-9_-] = 24 chars total
VALID_CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSMdItQ"


def _ingest_repo_cls() -> type:
    try:
        from backend.tests_support.in_memory import InMemoryIngestSourceRepository
    except ImportError as exc:  # pragma: no cover - RED until fake ships
        pytest.fail(f"InMemoryIngestSourceRepository not importable: {exc}")
    return InMemoryIngestSourceRepository


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
    sub: str = "user-uuid-1",
    role: str = "authenticated",
) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": sub,
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


def _client(signing_jwk: dict[str, Any], container: AppContainer) -> TestClient:
    settings = Settings(
        api_cors_origins="http://127.0.0.1:5173",
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
        supabase_url="",
        supabase_publishable_key="",
        supabase_secret_key="",
        supabase_jwks_url="https://unused.example/jwks.json",
        supabase_jwt_issuer=ISSUER,
    )
    app = create_app(
        settings,
        container=container,
        signing_key_resolver=lambda _token: signing_jwk,
    )
    return TestClient(app)


def _seed_profile(container: AppContainer, *, user_id: str, email: str, role: str) -> None:
    container.profiles._by_id[user_id] = CurrentUser(
        id=user_id,
        email=email,
        role=role,
        display_name=None,
    )


def _admin_env(
    *,
    attach_repo: bool = True,
) -> tuple[TestClient, dict[str, str], Any]:
    """Admin-authenticated client with ingest-sources fake attached post-build."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    assert hasattr(container, "ingest_sources"), (
        "AppContainer.ingest_sources field missing (D-21)"
    )
    if attach_repo:
        container.ingest_sources = _ingest_repo_cls()()
    else:
        container.ingest_sources = None
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    return client, {"Authorization": f"Bearer {token}"}, container


def test_get_returns_empty_sources_list() -> None:
    """SRC-01 / D-18: empty repo → 200 with exactly {sources: []}."""
    client, headers, _container = _admin_env()

    response = client.get(SOURCES_URL, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body == {"sources": []}
    assert set(body.keys()) == {"sources"}


def test_post_channel_then_get_includes_row() -> None:
    """SRC-01 / D-01/D-18: POST valid channel → 201; following GET includes the row."""
    client, headers, _container = _admin_env()

    created = client.post(
        SOURCES_URL,
        headers=headers,
        json={
            "kind": "channel",
            "source_id": VALID_CHANNEL_ID,
            "label": None,
        },
    )

    assert created.status_code == 201
    row = created.json()
    assert row["kind"] == "channel"
    assert row["source_id"] == VALID_CHANNEL_ID
    assert row["is_enabled"] is True
    assert "id" in row

    listed = client.get(SOURCES_URL, headers=headers)
    assert listed.status_code == 200
    sources = listed.json()["sources"]
    assert len(sources) == 1
    assert sources[0]["source_id"] == VALID_CHANNEL_ID
    assert sources[0]["kind"] == "channel"
    assert sources[0]["is_enabled"] is True


def test_get_post_require_admin_unauth_401_and_employee_403() -> None:
    """T-23-01: both routes are admin-gated; 401 unauthenticated, 403 non-admin."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    repo_cls = _ingest_repo_cls()

    anon_container = build_in_memory_container()
    assert hasattr(anon_container, "ingest_sources")
    anon_container.ingest_sources = repo_cls()
    anon_client = _client(jwk, anon_container)

    assert anon_client.get(SOURCES_URL).status_code == 401
    assert anon_client.post(
        SOURCES_URL,
        json={"kind": "channel", "source_id": VALID_CHANNEL_ID, "label": None},
    ).status_code == 401

    employee_container = build_in_memory_container()
    employee_container.ingest_sources = repo_cls()
    _seed_profile(
        employee_container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    employee_client = _client(jwk, employee_container)
    employee_token = _mint(private_key, email="alice@sberbank.ru")
    employee_headers = {"Authorization": f"Bearer {employee_token}"}

    get = employee_client.get(SOURCES_URL, headers=employee_headers)
    assert get.status_code == 403
    assert get.json()["detail"] == "forbidden"
    assert "sources" not in get.json()

    post = employee_client.post(
        SOURCES_URL,
        headers=employee_headers,
        json={"kind": "channel", "source_id": VALID_CHANNEL_ID, "label": None},
    )
    assert post.status_code == 403
    assert post.json()["detail"] == "forbidden"


def test_missing_ingest_sources_returns_503() -> None:
    """D-21: container with no ingest_sources → GET/POST 503 ingest_sources_not_configured."""
    client, headers, _container = _admin_env(attach_repo=False)

    get = client.get(SOURCES_URL, headers=headers)
    assert get.status_code == 503
    assert get.json()["detail"] == "ingest_sources_not_configured"

    post = client.post(
        SOURCES_URL,
        headers=headers,
        json={"kind": "channel", "source_id": VALID_CHANNEL_ID, "label": None},
    )
    assert post.status_code == 503
    assert post.json()["detail"] == "ingest_sources_not_configured"


def test_build_in_memory_container_wires_ingest_sources() -> None:
    """D-21 / D-24: default in-memory build exposes InMemoryIngestSourceRepository."""
    repo_cls = _ingest_repo_cls()
    container = build_in_memory_container()
    assert hasattr(container, "ingest_sources")
    assert isinstance(container.ingest_sources, repo_cls)
