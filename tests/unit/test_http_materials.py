"""HTTP GET /materials/{slug} — JWT gate, ready-only, soft 404 (MAT-02 / T-02-01)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

from backend.composition.container import build_in_memory_container
from backend.composition.settings import Settings
from backend.domain.current_user import CurrentUser
from backend.domain.material import Material, MaterialStatus
from backend.interface.http.app import create_app

ISSUER = "https://auth.example/auth/v1"


def _public_jwk(private_key: ec.EllipticCurvePrivateKey) -> dict[str, Any]:
    data = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
    data["kid"] = "test-kid-1"
    data["alg"] = "ES256"
    data["use"] = "sig"
    return data


def _mint(private_key: ec.EllipticCurvePrivateKey, *, email: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "user-uuid-1",
            "email": email,
            "role": "authenticated",
            "aud": "authenticated",
            "iss": ISSUER,
            "exp": now + 3600,
            "iat": now,
        },
        private_key,
        algorithm="ES256",
        headers={"kid": "test-kid-1"},
    )


def _material(
    *,
    slug: str,
    status: MaterialStatus,
    material_id: int = 1,
    related: tuple[str, ...] = (),
    title: str = "Building Production RAG Systems",
    body: str = "## Intro\n\nRAG body.",
) -> Material:
    now = datetime(2026, 3, 20, tzinfo=timezone.utc)
    return Material(
        id=material_id,
        slug=slug,
        title=title,
        dek="Audit dek",
        body_markdown=body,
        format="статья",
        status=status,
        reading_minutes=8,
        provenance_label="внешний текстовый источник",
        source_id=None,
        roles=("ds",),
        tags=(("RAG", "rag"), ("LLM", "llm")),
        related_material_ids=related,
        published_at=now if status == MaterialStatus.READY else None,
        created_at=now,
        updated_at=now,
    )


def _client(
    signing_jwk: dict[str, Any],
    materials: list[Material] | None = None,
) -> TestClient:
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
        container=build_in_memory_container(materials=materials),
        signing_key_resolver=lambda _token: signing_jwk,
    )
    return TestClient(app)


def _client_and_container(
    signing_jwk: dict[str, Any],
    materials: list[Material] | None = None,
) -> tuple[TestClient, Any]:
    """Mirror of `_client` that also hands back the container (to seed a profile)."""
    settings = Settings(
        api_cors_origins="http://127.0.0.1:5173",
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
        supabase_url="",
        supabase_publishable_key="",
        supabase_secret_key="",
        supabase_jwks_url="https://unused.example/jwks.json",
        supabase_jwt_issuer=ISSUER,
    )
    container = build_in_memory_container(materials=materials)
    app = create_app(
        settings,
        container=container,
        signing_key_resolver=lambda _token: signing_jwk,
    )
    return TestClient(app), container


def test_materials_by_slug_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.get("/materials/rag-systems")
    assert response.status_code == 401


def test_materials_unknown_slug_returns_404() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/materials/does-not-exist",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "material_not_found"


def test_materials_draft_slug_returns_404_not_403() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client = _client(jwk, materials=[draft])
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/materials/secret-draft",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "material_not_found"


def test_materials_ready_rag_systems_returns_200_with_body_markdown() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    related_ready = _material(
        slug="anomaly-detection",
        status=MaterialStatus.READY,
        material_id=2,
        title="Anomaly Detection in Audit Pipelines",
        body="## Related\n\nBody.",
    )
    related_draft = _material(
        slug="hidden-draft",
        status=MaterialStatus.DRAFT,
        material_id=3,
        title="Hidden",
        body="secret",
    )
    ready = _material(
        slug="rag-systems",
        status=MaterialStatus.READY,
        related=("2", "3", "999"),
    )
    client = _client(jwk, materials=[ready, related_ready, related_draft])
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/materials/rag-systems",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "rag-systems"
    assert body["title"] == "Building Production RAG Systems"
    assert body["body_markdown"] == "## Intro\n\nRAG body."
    assert body["format"] == "статья"
    assert body["dek"] == "Audit dek"
    assert body["provenance"] == "внешний текстовый источник"
    assert body["tags"] == ["RAG", "LLM"]
    assert body["reading_minutes"] == 8
    assert body["editor"] == "Редакция Digest CDS"
    assert body["published_at"] is not None
    # Only ready related targets with resolvable ids — never invent missing/draft (D-37)
    assert body["related"] == [
        {"slug": "anomaly-detection", "title": "Anomaly Detection in Audit Pipelines"}
    ]


def test_materials_draft_slug_returns_404_for_admin_token_too() -> None:
    """T-18-01: the reader route has no role branch — an admin token still gets the opaque 404."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client, container = _client_and_container(jwk, [draft])
    container.profiles._by_id["user-uuid-1"] = CurrentUser(
        id="user-uuid-1",
        email="alice@sberbank.ru",
        role="admin",
        display_name=None,
    )
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/materials/secret-draft",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "material_not_found"


def test_materials_ready_response_is_not_no_store() -> None:
    """D-07: the reader response's caching contract is untouched — no no-store."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    ready = _material(slug="rag-systems", status=MaterialStatus.READY)
    client = _client(jwk, materials=[ready])
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/materials/rag-systems",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "no-store" not in (response.headers.get("cache-control") or "")
