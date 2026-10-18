"""HTTP GET /knowledge/search — JWT gate, no score in JSON (KNOW-01 / D-59 / D-61)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

from backend.application.ports.query_embedder import StubQueryEmbedder
from backend.composition.container import AppContainer, build_in_memory_container
from backend.composition.settings import Settings
from backend.domain.knowledge import KnowledgeChunk
from backend.domain.material import Material, MaterialStatus
from backend.interface.http.app import create_app
from backend.tests_support.in_memory import (
    InMemoryDigestPublisher,
    InMemoryIssueRepository,
    InMemoryKnowledgeChunkRepository,
    InMemoryMaterialRepository,
    InMemoryPingRecorder,
    InMemoryProfileRepository,
    InMemoryRazborRepository,
    InMemoryShortlistRepository,
    InMemoryVoteRepository,
    InMemoryVotingCycleReader,
)

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


def _ready_material(
    *,
    material_id: int = 7,
    slug: str = "pgvector",
    roles: tuple[str, ...] = ("ds", "sva"),
) -> Material:
    now = datetime(2026, 3, 17, tzinfo=timezone.utc)
    return Material(
        id=material_id,
        slug=slug,
        title="pgvector for Enterprise Search",
        dek="PostgreSQL + pgvector",
        body_markdown="## Setup\n\nUse HNSW indexes for semantic search.",
        format="статья",
        status=MaterialStatus.READY,
        reading_minutes=6,
        provenance_label="внешний текстовый источник",
        source_id=None,
        roles=roles,
        tags=(("pgvector", "pgvector"),),
        related_material_ids=(),
        published_at=now,
        created_at=now,
        updated_at=now,
    )


def _seeded_container(materials: list[Material], chunks_by_material: dict[int, list[KnowledgeChunk]]) -> AppContainer:
    materials_repo = InMemoryMaterialRepository(materials)
    chunks = InMemoryKnowledgeChunkRepository(materials=materials_repo)
    for material_id, chunk_list in chunks_by_material.items():
        chunks.replace_for_material(material_id, chunk_list)
    from backend.infrastructure.local_notebook_storage import LocalNotebookStorage
    from backend.infrastructure.stub_mailer import StubMailer

    shortlist_repo = InMemoryShortlistRepository()
    issues_repo = InMemoryIssueRepository()
    return AppContainer(
        materials=materials_repo,
        chunks=chunks,
        profiles=InMemoryProfileRepository(),
        pings=InMemoryPingRecorder(),
        issues=issues_repo,
        voting_cycles=InMemoryVotingCycleReader(),
        votes=InMemoryVoteRepository(),
        embedder=StubQueryEmbedder(),
        razbors=InMemoryRazborRepository(),
        notebook_storage=LocalNotebookStorage("."),
        shortlist=shortlist_repo,
        mailer=StubMailer(),
        publisher=InMemoryDigestPublisher(lambda: shortlist_repo, lambda: issues_repo),
    )


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


def test_knowledge_search_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.get("/knowledge/search", params={"q": "HNSW"})
    assert response.status_code == 401


def test_knowledge_search_returns_200_without_score_field() -> None:
    """KNOW-01 / D-59: hits expose slug/snippet/title; never score."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    material = _ready_material()
    now = datetime(2026, 3, 17, tzinfo=timezone.utc)
    embedder = StubQueryEmbedder()
    query = "HNSW"
    embedding = embedder.embed(query)
    container = _seeded_container(
        [material],
        {
            7: [
                KnowledgeChunk(
                    id=1,
                    material_id=7,
                    chunk_index=0,
                    heading="Setup",
                    content_md="Use HNSW indexes for semantic search.",
                    embedding=embedding,
                    embedding_model_id="foundry-embed-v1",
                    content_sha256="sha",
                    created_at=now,
                )
            ]
        },
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/knowledge/search",
        params={"q": query},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "has_more" in body
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["slug"] == "pgvector"
    assert "HNSW" in item["snippet"]
    assert item["title"] == "pgvector for Enterprise Search"
    assert item.get("cover_url") is None
    assert "score" not in item
    assert "score" not in body


def test_knowledge_search_blank_q_returns_400_empty_query() -> None:
    """KNOW-01: whitespace-only q → 400 empty_query when route is invoked."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/knowledge/search",
        params={"q": "   \t  "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "empty_query"


def test_knowledge_search_overlong_q_returns_400() -> None:
    """Overlong q (>500 Unicode code points) → 400 when route is invoked."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk)
    token = _mint(private_key, email="alice@sberbank.ru")
    # 501 code points (CJK ideograph counts as one each)
    overlong = "字" * 501
    assert len(overlong) == 501
    response = client.get(
        "/knowledge/search",
        params={"q": overlong},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "query_too_long"


def test_knowledge_search_has_more_true_when_more_materials_exist() -> None:
    """D-61: has_more true when results beyond limit exist."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    now = datetime(2026, 3, 17, tzinfo=timezone.utc)
    embedder = StubQueryEmbedder()
    query = "HNSW"
    embedding = embedder.embed(query)
    materials = [
        _ready_material(material_id=i, slug=f"mat-{i}")
        for i in range(1, 4)
    ]
    # Override titles for uniqueness — _ready_material uses fixed title; slug differs.
    chunks_by_material = {
        i: [
            KnowledgeChunk(
                id=i,
                material_id=i,
                chunk_index=0,
                heading="Setup",
                content_md=f"HNSW topic material {i}",
                embedding=embedding,
                embedding_model_id="foundry-embed-v1",
                content_sha256="sha",
                created_at=now,
            )
        ]
        for i in range(1, 4)
    }
    container = _seeded_container(materials, chunks_by_material)
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/knowledge/search",
        params={"q": query, "limit": 2, "offset": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["limit"] == 2
    assert len(body["items"]) == 2


def _hnsw_chunk(*, material_id: int, embedding: list[float], now: datetime) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=material_id,
        material_id=material_id,
        chunk_index=0,
        heading="Setup",
        content_md="Use HNSW indexes for semantic search.",
        embedding=embedding,
        embedding_model_id="foundry-embed-v1",
        content_sha256="sha",
        created_at=now,
    )


def test_knowledge_search_role_analyst_returns_only_analyst_materials() -> None:
    """KNOW-02 / D-62: role=analyst is membership; ds-only materials stay out."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    now = datetime(2026, 3, 17, tzinfo=timezone.utc)
    embedding = StubQueryEmbedder().embed("HNSW")
    analyst = _ready_material(material_id=1, slug="sql-notes", roles=("analyst",))
    ds_only = _ready_material(material_id=2, slug="ml-experiment", roles=("ds",))
    container = _seeded_container(
        [analyst, ds_only],
        {
            1: [_hnsw_chunk(material_id=1, embedding=embedding, now=now)],
            2: [_hnsw_chunk(material_id=2, embedding=embedding, now=now)],
        },
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/knowledge/search",
        params={"q": "HNSW", "role": "analyst"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    slugs = [item["slug"] for item in response.json()["items"]]
    assert slugs == ["sql-notes"]
    assert "score" not in response.text


def test_knowledge_search_empty_role_param_is_unrestricted() -> None:
    """KNOW-02: role= (empty) is «Все», same as omitting the param."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    now = datetime(2026, 3, 17, tzinfo=timezone.utc)
    embedding = StubQueryEmbedder().embed("HNSW")
    analyst = _ready_material(material_id=1, slug="sql-notes", roles=("analyst",))
    ds_only = _ready_material(material_id=2, slug="ml-experiment", roles=("ds",))
    container = _seeded_container(
        [analyst, ds_only],
        {
            1: [_hnsw_chunk(material_id=1, embedding=embedding, now=now)],
            2: [_hnsw_chunk(material_id=2, embedding=embedding, now=now)],
        },
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/knowledge/search",
        params={"q": "HNSW", "role": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert {item["slug"] for item in response.json()["items"]} == {"sql-notes", "ml-experiment"}


def test_knowledge_search_invalid_role_returns_400() -> None:
    """T-04-05: role outside analyst|ds → 400 invalid_role (not an empty 200)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/knowledge/search",
        params={"q": "HNSW", "role": "sva"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_role"
