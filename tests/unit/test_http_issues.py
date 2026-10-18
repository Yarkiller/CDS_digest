"""Authenticated GET /issues/current — JWT gate + current-issue DTO (ISSUE-01 / D-24)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

from backend.composition.container import AppContainer, build_in_memory_container
from backend.composition.settings import Settings
from backend.domain.issue import Issue, IssueItem
from backend.domain.voting_cycle import VotingCycle
from backend.interface.http.app import create_app
from backend.tests_support.in_memory import InMemoryIssueRepository, InMemoryVotingCycleReader


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


def _seeded_container() -> AppContainer:
    container = build_in_memory_container()
    issue = Issue(
        id="iss-14",
        number=14,
        period_label="17–23 марта 2026",
        title="Новости DS для СВА",
        editor="Редакция Digest CDS",
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
        items=(
            IssueItem(
                slug="rag-systems",
                title="Building Production RAG Systems",
                position=1,
                format="Статья",
                reading_minutes=8,
                dek="Как быстро находить нужные фрагменты.",
            ),
        ),
    )
    container.issues = InMemoryIssueRepository([issue])
    return container


def _client(signing_jwk: dict[str, Any], container: AppContainer | None = None) -> TestClient:
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
        container=container or build_in_memory_container(),
        signing_key_resolver=lambda _token: signing_jwk,
    )
    return TestClient(app)


def test_issues_current_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.get("/issues/current")
    assert response.status_code == 401


def test_issues_current_with_corporate_jwt_returns_seeded_issue() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/issues/current",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["number"] == 14
    assert body["period_label"] == "17–23 марта 2026"
    assert body["title"] == "Новости DS для СВА"
    assert body["items"][0]["slug"] == "rag-systems"
    assert body["items"][0]["position"] == 1
    assert body["items"][0]["format"] == "Статья"
    assert body["items"][0]["reading_minutes"] == 8


def test_issues_current_with_no_published_returns_honest_empty_200() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.issues = InMemoryIssueRepository([])
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/issues/current",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["number"] is None
    assert body["items"] == []
    assert body.get("voting_cycle") is None


def test_issues_current_includes_open_voting_cycle() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = _seeded_container()
    container.voting_cycles = InMemoryVotingCycleReader(
        [
            VotingCycle(
                id="vc-1",
                status="open",
                opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
                closes_at=datetime(2026, 4, 16, 23, 59, 59, tzinfo=timezone.utc),
            )
        ]
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/issues/current",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["voting_cycle"]["status"] == "open"
    assert "2026-04-16" in body["voting_cycle"]["closes_at"]


def test_issues_current_includes_closed_voting_cycle() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = _seeded_container()
    container.voting_cycles = InMemoryVotingCycleReader(
        [
            VotingCycle(
                id="vc-closed",
                status="closed",
                opens_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                closes_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
            )
        ]
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/issues/current",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["voting_cycle"]["status"] == "closed"


def test_issues_by_number_omits_voting_cycle() -> None:
    """Past issues reuse CurrentIssueResponse without requiring voting_cycle (D-34)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = _two_issue_container()
    container.voting_cycles = InMemoryVotingCycleReader(
        [
            VotingCycle(
                id="vc-1",
                status="open",
                opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
                closes_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
            )
        ]
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/issues/13",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json().get("voting_cycle") is None


def _two_issue_container() -> AppContainer:
    older = Issue(
        id="iss-13",
        number=13,
        period_label="10–16 марта 2026",
        title="Прошлый выпуск",
        editor="Редакция Digest CDS",
        published_at=datetime(2026, 3, 10, tzinfo=timezone.utc),
        items=(
            IssueItem(
                slug="past-mat",
                title="Past Material",
                position=1,
                format="Статья",
                reading_minutes=6,
                dek=None,
            ),
        ),
    )
    current = Issue(
        id="iss-14",
        number=14,
        period_label="17–23 марта 2026",
        title="Новости DS для СВА",
        editor="Редакция Digest CDS",
        published_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
        items=(
            IssueItem(
                slug="rag-systems",
                title="Building Production RAG Systems",
                position=1,
                format="Статья",
                reading_minutes=8,
                dek="Как быстро находить нужные фрагменты.",
            ),
        ),
    )
    container = build_in_memory_container()
    container.issues = InMemoryIssueRepository([older, current])
    return container


def test_archive_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.get("/archive")
    assert response.status_code == 401


def test_archive_excludes_current_and_lists_past() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _two_issue_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/archive", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    numbers = [item["number"] for item in body["issues"]]
    assert 14 not in numbers
    assert 13 in numbers
    past = next(item for item in body["issues"] if item["number"] == 13)
    assert past["period_label"] == "10–16 марта 2026"
    assert past["title"] == "Прошлый выпуск"
    assert past["material_count"] == 1


def test_issues_by_number_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.get("/issues/13")
    assert response.status_code == 401


def test_issues_by_number_returns_published_issue() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _two_issue_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/issues/13",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["number"] == 13
    assert body["title"] == "Прошлый выпуск"
    assert body["items"][0]["slug"] == "past-mat"


def test_issues_by_number_missing_returns_404() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _two_issue_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/issues/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
