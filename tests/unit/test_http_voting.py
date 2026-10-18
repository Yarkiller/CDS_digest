"""Authenticated GET/POST /voting — JWT gate + BallotSnapshot (VOTE-01/02, D-40, D-52)."""

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
from backend.domain.errors import PersistenceError
from backend.domain.vote import BallotTopic, PersonalVote
from backend.domain.voting_cycle import VotingCycle
from backend.interface.http.app import create_app
from backend.tests_support.in_memory import InMemoryVoteRepository, InMemoryVotingCycleReader


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


def _open_cycle() -> VotingCycle:
    return VotingCycle(
        id="cycle-1",
        status="open",
        opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
        closes_at=datetime(2026, 4, 16, 23, 59, 59, tzinfo=timezone.utc),
    )


def _seeded_container() -> AppContainer:
    container = build_in_memory_container()
    topics = [
        BallotTopic(
            id="topic-1",
            title="RAG в корпоративной среде",
            description="Аудит применения RAG.",
            materials_count=2,
            votes=0,
        ),
        BallotTopic(
            id="topic-2",
            title="Аномалии в логах",
            description="Как искать аномалии.",
            materials_count=0,
            votes=0,
        ),
    ]
    container.voting_cycles = InMemoryVotingCycleReader([_open_cycle()])
    container.votes = InMemoryVoteRepository(topics_by_cycle={"cycle-1": topics})
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


def test_voting_current_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key), _seeded_container())
    response = client.get("/voting/current")
    assert response.status_code == 401


def test_voting_current_never_voted_returns_snapshot_with_null_personal_vote() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.get(
        "/voting/current",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["personal_vote"] is None
    assert len(body["topics"]) == 2
    assert all("leading" not in t for t in body["topics"])
    assert body["cycle"]["status"] == "open"
    assert body["leaders"] == []


def test_voting_post_vote_returns_snapshot_with_personal_vote() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/voting/votes",
        headers=headers,
        json={"topic_id": "topic-1", "expected_updated_at": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["personal_vote"]["topic_id"] == "topic-1"
    assert body["topics"][0]["votes"] == 1


def test_voting_post_same_topic_repeat_returns_200() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        "/voting/votes",
        headers=headers,
        json={"topic_id": "topic-1", "expected_updated_at": None},
    )
    assert first.status_code == 200
    updated_at = first.json()["personal_vote"]["updated_at"]

    second = client.post(
        "/voting/votes",
        headers=headers,
        json={"topic_id": "topic-1", "expected_updated_at": updated_at},
    )
    assert second.status_code == 200
    assert second.json()["personal_vote"]["topic_id"] == "topic-1"


def test_voting_post_rejects_extra_body_fields() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        "/voting/votes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "topic_id": "topic-1",
            "expected_updated_at": None,
            "user_id": "attacker",
        },
    )
    assert response.status_code == 422


def test_voting_current_persistence_error_returns_503_voting_unavailable() -> None:
    class _FailingVotes:
        def list_topics_with_counts(self, cycle_id: str) -> list[BallotTopic]:
            raise PersistenceError("db down")

        def get_vote(self, cycle_id: str, user_id: str) -> PersonalVote | None:
            raise PersistenceError("db down")

        def upsert_vote(
            self,
            *,
            cycle_id: str,
            user_id: str,
            topic_id: str,
            expected_updated_at: datetime | None,
        ) -> PersonalVote:
            raise PersistenceError("db down")

    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = _seeded_container()
    container.votes = _FailingVotes()  # type: ignore[assignment]
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.get(
        "/voting/current",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "voting_unavailable"


def test_voting_post_unknown_topic_returns_400() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        "/voting/votes",
        headers={"Authorization": f"Bearer {token}"},
        json={"topic_id": "topic-missing", "expected_updated_at": None},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_vote"


def test_voting_post_empty_topic_returns_400() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        "/voting/votes",
        headers={"Authorization": f"Bearer {token}"},
        json={"topic_id": "   ", "expected_updated_at": None},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_vote"


def test_voting_post_change_a_to_b_returns_200_with_moved_tallies() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        "/voting/votes",
        headers=headers,
        json={"topic_id": "topic-1", "expected_updated_at": None},
    )
    assert first.status_code == 200
    updated_at = first.json()["personal_vote"]["updated_at"]

    second = client.post(
        "/voting/votes",
        headers=headers,
        json={"topic_id": "topic-2", "expected_updated_at": updated_at},
    )
    assert second.status_code == 200
    body = second.json()
    assert body["personal_vote"]["topic_id"] == "topic-2"
    by_id = {t["id"]: t["votes"] for t in body["topics"]}
    assert by_id["topic-1"] == 0
    assert by_id["topic-2"] == 1


def test_voting_post_closed_returns_409_cycle_closed_with_ballot() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = _seeded_container()
    container.voting_cycles = InMemoryVotingCycleReader(
        [
            VotingCycle(
                id="cycle-1",
                status="closed",
                opens_at=datetime(2026, 4, 3, tzinfo=timezone.utc),
                closes_at=datetime(2026, 4, 16, 23, 59, 59, tzinfo=timezone.utc),
            )
        ]
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        "/voting/votes",
        headers={"Authorization": f"Bearer {token}"},
        json={"topic_id": "topic-1", "expected_updated_at": None},
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "CYCLE_CLOSED"
    assert "закрыт" in detail["message"].lower()
    assert isinstance(detail["ballot"], dict)
    assert "topics" in detail["ballot"]
    assert detail["ballot"]["cycle"]["status"] == "closed"


def test_voting_post_cas_mismatch_returns_409_vote_conflict_with_ballot() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, _seeded_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        "/voting/votes",
        headers=headers,
        json={"topic_id": "topic-1", "expected_updated_at": None},
    )
    assert first.status_code == 200

    response = client.post(
        "/voting/votes",
        headers=headers,
        json={
            "topic_id": "topic-2",
            "expected_updated_at": "2020-01-01T00:00:00+00:00",
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "VOTE_CONFLICT"
    assert isinstance(detail["ballot"], dict)
    assert detail["ballot"]["personal_vote"]["topic_id"] == "topic-1"
