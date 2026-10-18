"""Authenticated /admin shortlist — AUTH-03 / ADMIN-01…03/05, D-74, D-77…D-85."""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

from backend.composition.container import AppContainer, build_in_memory_container
from backend.composition.settings import Settings
from backend.domain.current_user import CurrentUser
from backend.domain.errors import PersistenceError
from backend.domain.material import Material, MaterialStatus
from backend.domain.shortlist import ShortlistBatch, ShortlistItem
from backend.interface.http.app import create_app
from backend.interface.http.routes.materials import EDITOR_BYLINE
from backend.tests_support.in_memory import InMemoryShortlistRepository


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


def _seeded_shortlist() -> ShortlistBatch:
    return ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            ShortlistItem(
                material_id=101,
                rank=1,
                title="RAG в продакшене",
                material_status="ready",
                decision="pending",
                score=0.92,
                score_factors={
                    "factors": [
                        {"label": "Релевантность"},
                        {"label": "Свежесть"},
                    ]
                },
            ),
            ShortlistItem(
                material_id=102,
                rank=2,
                title="Черновик без факторов",
                material_status="draft",
                decision="pending",
                score=0.4,
                score_factors={"only": 1},
            ),
        ),
    )


def test_admin_shortlist_without_authorization_returns_401() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    container = build_in_memory_container()
    client = _client(_public_jwk(private_key), container)
    response = client.get("/admin/shortlist")
    assert response.status_code == 401


def test_admin_shortlist_employee_returns_403_forbidden() -> None:
    """D-74 / D-77: non-admin profiles.role → 403, never empty shortlist body."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_seeded_shortlist())
    _seed_profile(
        container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.get(
        "/admin/shortlist",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert "items" not in response.json()


def test_admin_shortlist_admin_returns_ranked_items_with_factor_honesty() -> None:
    """ADMIN-01 / ADMIN-05 / D-79: admin sees ≤5 items; honesty empties factor_labels."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_seeded_shortlist())
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.get(
        "/admin/shortlist",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["batch_id"] == 42
    assert len(body["items"]) == 2
    assert len(body["items"]) <= 5
    first, second = body["items"]
    assert first["rank"] == 1
    assert first["material_status"] == "ready"
    assert first["decision"] == "pending"
    assert first["score"] == 0.92
    assert first["factor_labels"] == ["Релевантность", "Свежесть"]
    assert second["material_status"] == "draft"
    assert second["factor_labels"] == []


def test_admin_shortlist_returns_full_items() -> None:
    """ADUX-01 / D-02: non-empty items carry full material preview fields (required keys)."""
    body_md = "Параграф один.\n\nПараграф два с деталями."
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(
        batch=ShortlistBatch(
            id=42,
            week_start=date(2026, 9, 15),
            sent_at=None,
            items=(
                ShortlistItem(
                    material_id=101,
                    rank=1,
                    title="RAG в продакшене",
                    material_status="ready",
                    decision="approved",
                    score=0.92,
                    score_factors={
                        "factors": [
                            {"label": "Релевантность"},
                            {"label": "Свежесть"},
                        ]
                    },
                    dek="Короткий dek",
                    body_markdown=body_md,
                    provenance_label="YouTube · канал",
                    slug="rag-v-prodakshene",
                    reading_minutes=4,
                ),
            ),
        )
    )
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.get(
        "/admin/shortlist",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    first = payload["items"][0]
    for key in (
        "body_markdown",
        "provenance_label",
        "slug",
        "reading_minutes",
        "char_count",
        "word_count",
        "rank",
        "title",
        "dek",
        "decision",
    ):
        assert key in first, f"missing required key: {key}"
    assert first["body_markdown"] == body_md
    assert first["provenance_label"] == "YouTube · канал"
    assert first["slug"] == "rag-v-prodakshene"
    assert first["reading_minutes"] == 4
    assert first["char_count"] == len(body_md)
    assert first["word_count"] == len(body_md.split())


def test_admin_shortlist_no_batches_returns_null_batch_id() -> None:
    """FIX-01 / D-04 #1: no batches → 200 with null batch_id and empty items."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=None)
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.get(
        "/admin/shortlist",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    for key in (
        "batch_id",
        "items",
        "week_label",
        "sent_at",
        "digest_rest",
        "days_until_next_batch",
    ):
        assert key in body
    assert body["batch_id"] is None
    assert body["items"] == []
    assert body["week_label"] is None
    assert body["sent_at"] is None
    assert body["digest_rest"] is False
    assert body["days_until_next_batch"] is None


def test_admin_shortlist_empty_unsent_batch_returns_batch_id() -> None:
    """FIX-01 / D-04 #2: empty unsent batch → 200 with batch_id + ISO week_label."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(
        batch=ShortlistBatch(
            id=7,
            week_start=date(2026, 10, 6),
            sent_at=None,
            items=(),
        )
    )
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.get(
        "/admin/shortlist",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    for key in (
        "batch_id",
        "items",
        "week_label",
        "sent_at",
        "digest_rest",
        "days_until_next_batch",
    ):
        assert key in body
    assert body["items"] == []
    assert body["batch_id"] == 7
    assert body["week_label"] == "2026-10-06"
    assert body["sent_at"] is None
    assert body["digest_rest"] is False
    assert body["days_until_next_batch"] is None


def test_admin_shortlist_after_send_returns_digest_rest() -> None:
    """G-05-2: sent latest batch → digest_rest + weekly cadence days."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(
        batch=ShortlistBatch(
            id=99,
            week_start=date(2026, 9, 15),
            sent_at=datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc),
            items=(
                ShortlistItem(
                    material_id=1,
                    rank=1,
                    title="Sent",
                    material_status="ready",
                    decision="approved",
                    score=0.9,
                    score_factors={"A": 1, "B": 2},
                ),
            ),
        )
    )
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.get(
        "/admin/shortlist",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["batch_id"] is None
    assert body["items"] == []
    assert body["digest_rest"] is True
    assert body["days_until_next_batch"] == 7


def test_admin_shortlist_persistence_error_returns_503() -> None:
    class _FailingShortlist:
        def get_current_batch(self):
            raise PersistenceError("db down")

    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = _FailingShortlist()  # type: ignore[assignment]
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.get(
        "/admin/shortlist",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "shortlist_unavailable"


def _decision_url(material_id: int) -> str:
    return f"/admin/shortlist/items/{material_id}/decision"


def test_admin_decision_employee_returns_403() -> None:
    """D-77: non-admin cannot PATCH/POST decision — HTTP 403."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_seeded_shortlist())
    _seed_profile(
        container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        _decision_url(101),
        headers={"Authorization": f"Bearer {token}"},
        json={"decision": "approved"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_admin_decision_approve_returns_updated_shortlist_with_status() -> None:
    """D-02 / ADMIN-02 / D-85 / ADUX-05: approve draft → decision approved; material_status stays draft."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_seeded_shortlist())
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        _decision_url(102),
        headers=headers,
        json={"decision": "approved"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["batch_id"] == 42
    draft = next(i for i in body["items"] if i["material_id"] == 102)
    assert draft["decision"] == "approved"
    # D-02: Approve ≠ ready — HTTP decision must leave material_status draft
    assert draft["material_status"] == "draft"
    ready = next(i for i in body["items"] if i["material_id"] == 101)
    assert ready["material_status"] == "ready"

    get_body = client.get("/admin/shortlist", headers=headers).json()
    assert next(i for i in get_body["items"] if i["material_id"] == 102)["decision"] == "approved"


def test_admin_decision_reject_persists_on_get() -> None:
    """ADMIN-02 / D-82: reject persists and is reflected on subsequent GET."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_seeded_shortlist())
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        _decision_url(101),
        headers=headers,
        json={"decision": "rejected"},
    )

    assert response.status_code == 200
    assert next(i for i in response.json()["items"] if i["material_id"] == 101)["decision"] == (
        "rejected"
    )
    get_body = client.get("/admin/shortlist", headers=headers).json()
    assert next(i for i in get_body["items"] if i["material_id"] == 101)["decision"] == "rejected"


def test_admin_decision_invalid_body_returns_400() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_seeded_shortlist())
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.post(
        _decision_url(101),
        headers={"Authorization": f"Bearer {token}"},
        json={"decision": "include"},
    )

    assert response.status_code == 400


def test_admin_decision_unknown_material_returns_404() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_seeded_shortlist())
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.post(
        _decision_url(999),
        headers={"Authorization": f"Bearer {token}"},
        json={"decision": "approved"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "shortlist_item_not_found"


def test_admin_decision_persistence_error_returns_503() -> None:
    class _FailingShortlist:
        def get_current_batch(self):
            raise PersistenceError("db down")

        def set_decision(self, **_kwargs):
            raise PersistenceError("db down")

    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = _FailingShortlist()  # type: ignore[assignment]
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")

    response = client.post(
        _decision_url(101),
        headers={"Authorization": f"Bearer {token}"},
        json={"decision": "approved"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "shortlist_unavailable"


def _admin_client_with_batch(batch: ShortlistBatch | None):
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    shortlist = InMemoryShortlistRepository(batch=batch)
    # Live-join fidelity: shortlist material_status overlays from materials repo (ADUX-05).
    if hasattr(shortlist, "attach_materials"):
        shortlist.attach_materials(container.materials)
    container.shortlist = shortlist
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    return client, {"Authorization": f"Bearer {token}"}, container


def _draft_material(material_id: int, *, title: str = "Draft approved") -> Material:
    return Material(
        id=material_id,
        slug=f"material-{material_id}",
        title=title,
        dek="dek",
        body_markdown="",
        format="статья",
        status=MaterialStatus.DRAFT,
        reading_minutes=5,
        provenance_label="внешний текстовый источник",
        source_id=None,
        roles=("ds",),
        tags=(),
        related_material_ids=(),
        published_at=None,
        created_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def _ready_approved_batch() -> ShortlistBatch:
    return ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            ShortlistItem(
                material_id=101,
                rank=1,
                title="RAG в продакшене",
                material_status="ready",
                decision="approved",
                score=0.92,
                score_factors={
                    "factors": [
                        {"label": "Релевантность"},
                        {"label": "Свежесть"},
                    ]
                },
            ),
            ShortlistItem(
                material_id=102,
                rank=2,
                title="Черновик",
                material_status="draft",
                decision="pending",
                score=0.4,
                score_factors={},
            ),
        ),
    )


def test_admin_preview_returns_approved_ready_only_without_sent_at() -> None:
    """ADMIN-04 / D-86: preview lists approved∩ready; never sets sent_at."""
    client, headers, container = _admin_client_with_batch(_ready_approved_batch())

    response = client.post("/admin/shortlist/preview", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["material_id"] for item in body["items"]] == [101]
    assert body["subject"]
    assert body["body"]
    assert container.shortlist.get_current_batch().sent_at is None


def test_admin_preview_accepts_intro_and_ordered_blocks() -> None:
    """G-05-1: POST {intro, blocks} composes body; never sets sent_at."""
    batch = ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            ShortlistItem(
                material_id=101,
                rank=1,
                title="Title A",
                material_status="ready",
                decision="approved",
                score=0.9,
                score_factors={"factors": [{"label": "A"}, {"label": "B"}]},
            ),
            ShortlistItem(
                material_id=103,
                rank=2,
                title="Title B",
                material_status="ready",
                decision="approved",
                score=0.8,
                score_factors={"factors": [{"label": "A"}, {"label": "B"}]},
            ),
        ),
    )
    client, headers, container = _admin_client_with_batch(batch)

    response = client.post(
        "/admin/shortlist/preview",
        headers=headers,
        json={
            "intro": "Добрый день коллеги!",
            "blocks": [
                {"kind": "material", "material_id": 101},
                {"kind": "text", "text": "связка"},
                {"kind": "material", "material_id": 103},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "Добрый день коллеги!" in body["body"]
    assert body["body"].index("Title A") < body["body"].index("связка") < body["body"].index(
        "Title B"
    )
    assert [item["material_id"] for item in body["items"]] == [101, 103]
    assert container.shortlist.get_current_batch().sent_at is None


def test_admin_preview_invalid_composition_returns_400() -> None:
    client, headers, _container = _admin_client_with_batch(_ready_approved_batch())

    response = client.post(
        "/admin/shortlist/preview",
        headers=headers,
        json={
            "intro": "",
            "blocks": [{"kind": "material", "material_id": 999}],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_preview_composition"


def test_admin_preview_employee_returns_403() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_ready_approved_batch())
    _seed_profile(
        container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        "/admin/shortlist/preview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


class _FakeStatusMailer:
    """Mailer double returning a scripted live delivery status (D-11 containment proofs)."""

    def __init__(self, *, status: str, delivered: int) -> None:
        self._status = status
        self._delivered = delivered

    def send_digest(
        self,
        *,
        batch_id: int,
        issue_url: str,
        subject: str,
        body_text: str,
        recipient_count: int,
        recipients: Any,
        body_html: str | None = None,
    ) -> dict[str, Any]:
        return {
            "delivery_status": self._status,
            "recipient_count": recipient_count,
            "delivered_count": self._delivered,
            "issue_url": issue_url,
        }


def test_admin_send_stays_200_when_mail_partial_after_publish() -> None:
    """D-11 / D-88: a contained mail partial after publish is HTTP 200 with honest N/M."""
    client, headers, container = _admin_client_with_batch(_ready_approved_batch())
    _seed_profile(container, user_id="emp-uuid-1", email="emp@sberbank.ru", role="employee")
    container.mailer = _FakeStatusMailer(status="partial", delivered=1)

    response = client.post("/admin/shortlist/send", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["delivery_status"] == "partial"
    assert body["recipient_count"] == 2
    assert body["delivered_count"] == 1
    assert body["message"] == "Выпуск опубликован. Доставлено 1 из 2 (частично)"
    assert container.issues.get_by_number(body["issue_number"]) is not None


def test_admin_send_stays_200_when_mail_failed_after_publish() -> None:
    """D-11 / D-88: a full mail failure after publish is still HTTP 200, never 5xx."""
    client, headers, container = _admin_client_with_batch(_ready_approved_batch())
    _seed_profile(container, user_id="emp-uuid-1", email="emp@sberbank.ru", role="employee")
    container.mailer = _FakeStatusMailer(status="failed", delivered=0)

    response = client.post("/admin/shortlist/send", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["delivery_status"] == "failed"
    assert body["recipient_count"] == 2
    assert body["delivered_count"] == 0
    assert body["message"] == "Выпуск опубликован. Письма не доставлены (0 из 2)"
    assert container.issues.get_by_number(body["issue_number"]) is not None


def test_admin_send_happy_path_publishes_and_returns_issue_link() -> None:
    """ADMIN-07/08 / D-88: send publishes once; stub honesty message."""
    client, headers, container = _admin_client_with_batch(_ready_approved_batch())

    response = client.post("/admin/shortlist/send", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Выпуск опубликован. Доставка писем: stub (0 из 1)"
    assert body["delivery_status"] == "stubbed"
    assert body["delivered_count"] == 0
    assert body["issue_url"].startswith("/issues/")
    # WR-03: sent batch leaves the unsent pool; sent_at is visible via get_latest_batch.
    assert container.shortlist.get_current_batch() is None
    assert container.shortlist.get_latest_batch().sent_at is not None
    assert container.issues.get_by_number(body["issue_number"]) is not None


def test_admin_send_material_ids_order_honored_and_mismatch_is_400() -> None:
    """G-05-1: SendDigestRequest.material_ids drives issue order; bad set → 400."""
    batch = ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            ShortlistItem(
                material_id=101,
                rank=1,
                title="First by rank",
                material_status="ready",
                decision="approved",
                score=0.9,
                score_factors={"factors": [{"label": "A"}, {"label": "B"}]},
            ),
            ShortlistItem(
                material_id=102,
                rank=2,
                title="Second by rank",
                material_status="ready",
                decision="approved",
                score=0.8,
                score_factors={"factors": [{"label": "A"}, {"label": "B"}]},
            ),
        ),
    )
    client, headers, container = _admin_client_with_batch(batch)

    bad = client.post(
        "/admin/shortlist/send",
        headers=headers,
        json={"material_ids": [101]},
    )
    assert bad.status_code == 400

    ok = client.post(
        "/admin/shortlist/send",
        headers=headers,
        json={"material_ids": [102, 101]},
    )
    assert ok.status_code == 200
    assert ok.json()["message"] == "Выпуск опубликован. Доставка писем: stub (0 из 1)"
    assert ok.json()["delivered_count"] == 0
    published = container.issues.get_by_number(ok.json()["issue_number"])
    assert published is not None
    assert [item.title for item in published.items] == ["Second by rank", "First by rank"]


def test_admin_send_second_returns_409_already_sent() -> None:
    """ADMIN-07 / D-89: repeat send → 409 «Уже отправлено»."""
    client, headers, _container = _admin_client_with_batch(_ready_approved_batch())

    first = client.post("/admin/shortlist/send", headers=headers)
    assert first.status_code == 200

    second = client.post("/admin/shortlist/send", headers=headers)
    assert second.status_code == 409
    detail = second.json()["detail"]
    assert detail == "already_sent" or (
        isinstance(detail, dict) and detail.get("code") == "already_sent"
    )


def test_admin_send_draft_in_pool_returns_400() -> None:
    """ADMIN-03 / D-85: approved draft blocks send with 400."""
    batch = ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            ShortlistItem(
                material_id=101,
                rank=1,
                title="Ready",
                material_status="ready",
                decision="approved",
                score=0.9,
                score_factors={"factors": [{"label": "A"}, {"label": "B"}]},
            ),
            ShortlistItem(
                material_id=102,
                rank=2,
                title="Draft approved",
                material_status="draft",
                decision="approved",
                score=0.4,
                score_factors={},
            ),
        ),
    )
    client, headers, container = _admin_client_with_batch(batch)

    response = client.post("/admin/shortlist/send", headers=headers)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail == "draft_in_send_pool" or (
        isinstance(detail, dict) and detail.get("code") == "draft_in_send_pool"
    )
    assert container.shortlist.get_current_batch().sent_at is None


def test_admin_send_employee_returns_403() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.shortlist = InMemoryShortlistRepository(batch=_ready_approved_batch())
    _seed_profile(
        container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        "/admin/shortlist/send",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_admin_mark_ready_promotes_draft_and_clears_send_gate() -> None:
    """ADUX-05 / D-06 / D-07: POST ready → shortlist ready → send no draft_in_send_pool."""
    batch = ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            ShortlistItem(
                material_id=101,
                rank=1,
                title="Ready",
                material_status="ready",
                decision="approved",
                score=0.9,
                score_factors={"factors": [{"label": "A"}, {"label": "B"}]},
            ),
            ShortlistItem(
                material_id=102,
                rank=2,
                title="Draft approved",
                material_status="draft",
                decision="approved",
                score=0.4,
                score_factors={},
            ),
        ),
    )
    client, headers, container = _admin_client_with_batch(batch)
    container.materials.save(
        Material(
            id=101,
            slug="material-101",
            title="Ready",
            dek="dek",
            body_markdown="body",
            format="статья",
            status=MaterialStatus.READY,
            reading_minutes=5,
            provenance_label="внешний текстовый источник",
            source_id=None,
            roles=("ds",),
            tags=(),
            related_material_ids=(),
            published_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
    )
    container.materials.save(_draft_material(102, title="Draft approved"))

    ready_response = client.post("/admin/materials/102/ready", headers=headers)
    assert ready_response.status_code == 200
    ready_body = ready_response.json()
    assert ready_body["material_id"] == 102
    assert ready_body["status"] == "ready"
    assert container.materials.get(102).published_at is None

    shortlist = client.get("/admin/shortlist", headers=headers)
    assert shortlist.status_code == 200
    by_id = {item["material_id"]: item for item in shortlist.json()["items"]}
    assert by_id[102]["material_status"] == "ready"

    send_response = client.post("/admin/shortlist/send", headers=headers)
    assert send_response.status_code == 200
    detail = send_response.json()
    assert detail["message"] == "Выпуск опубликован. Доставка писем: stub (0 из 1)"
    assert detail["delivered_count"] == 0


def test_admin_mark_ready_missing_material_returns_404() -> None:
    client, headers, _container = _admin_client_with_batch(_ready_approved_batch())

    response = client.post("/admin/materials/999/ready", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "material_not_found"


def test_admin_mark_ready_already_ready_is_noop() -> None:
    """D-09: already-ready POST returns 200; published_at unchanged (ADUX-05)."""
    client, headers, container = _admin_client_with_batch(_ready_approved_batch())
    published_at = datetime(2026, 9, 1, tzinfo=timezone.utc)
    container.materials.save(
        Material(
            id=101,
            slug="material-101",
            title="Ready",
            dek="dek",
            body_markdown="body",
            format="статья",
            status=MaterialStatus.READY,
            reading_minutes=5,
            provenance_label="внешний текстовый источник",
            source_id=None,
            roles=("ds",),
            tags=(),
            related_material_ids=(),
            published_at=published_at,
            created_at=published_at,
            updated_at=published_at,
        )
    )

    response = client.post("/admin/materials/101/ready", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"material_id": 101, "status": "ready"}
    assert container.materials.get(101).published_at == published_at


def test_admin_mark_ready_employee_returns_403() -> None:
    """T-14-01 / D-74: employee JWT cannot promote ready (parity with decision)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.materials.save(_draft_material(102))
    _seed_profile(
        container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        "/admin/materials/102/ready",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_admin_mark_ready_batch_partial_success_preserves_order() -> None:
    """D-08 / ADUX-05: POST /admin/materials/ready → 200 results[] order + partial success."""
    client, headers, container = _admin_client_with_batch(_ready_approved_batch())
    container.materials.save(_draft_material(102, title="Draft approved"))

    response = client.post(
        "/admin/materials/ready",
        headers=headers,
        json={"material_ids": [102, 999, 102]},
    )

    assert response.status_code == 200
    body = response.json()
    assert list(body.keys()) == ["results"]
    results = body["results"]
    assert [r["material_id"] for r in results] == [102, 999, 102]
    assert results[0] == {
        "material_id": 102,
        "ok": True,
        "status": "ready",
        "error": None,
    }
    assert results[1] == {
        "material_id": 999,
        "ok": False,
        "status": None,
        "error": "material_not_found",
    }
    assert results[2]["ok"] is True
    assert results[2]["status"] == "ready"
    assert container.materials.get(102).status == MaterialStatus.READY
    assert container.materials.get(102).published_at is None


def test_admin_mark_ready_batch_empty_ids_returns_empty_results() -> None:
    """D-08 / ADUX-05 empty probe: material_ids=[] → 200 results=[]."""
    client, headers, _container = _admin_client_with_batch(_ready_approved_batch())

    response = client.post(
        "/admin/materials/ready",
        headers=headers,
        json={"material_ids": []},
    )

    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_admin_mark_ready_batch_unknown_field_returns_422() -> None:
    """T-14-05 / ADUX-05: MarkReadyBatchRequest extra=forbid → 422."""
    client, headers, _container = _admin_client_with_batch(_ready_approved_batch())

    response = client.post(
        "/admin/materials/ready",
        headers=headers,
        json={"material_ids": [102], "extra_field": True},
    )

    assert response.status_code == 422


def test_admin_mark_ready_batch_employee_returns_403() -> None:
    """T-14-04 / D-74: employee JWT cannot batch-promote ready (ADUX-05)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.materials.save(_draft_material(102))
    _seed_profile(
        container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")

    response = client.post(
        "/admin/materials/ready",
        headers={"Authorization": f"Bearer {token}"},
        json={"material_ids": [102]},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def _material(
    *,
    slug: str,
    status: MaterialStatus,
    material_id: int = 1,
    related: tuple[str, ...] = (),
    title: str = "Draft preview article",
) -> Material:
    now = datetime(2026, 3, 20, tzinfo=timezone.utc)
    return Material(
        id=material_id,
        slug=slug,
        title=title,
        dek="Preview dek",
        body_markdown="## Draft\n\nDraft body.",
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


def _preview_env(
    materials: list[Material],
    *,
    role: str = "admin",
) -> tuple[TestClient, dict[str, str], AppContainer]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container(materials=materials)
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role=role,
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    return client, {"Authorization": f"Bearer {token}"}, container


def test_admin_material_preview_draft_returns_200_reader_dto() -> None:
    """D-01/D-02/D-04/D-08/D-12: admin reads a draft; reader DTO shape, empty tags/related."""
    related_ready = _material(
        slug="anomaly-detection",
        status=MaterialStatus.READY,
        material_id=2,
        title="Anomaly Detection",
    )
    draft = _material(
        slug="secret-draft",
        status=MaterialStatus.DRAFT,
        related=("2",),
    )
    client, headers, _container = _preview_env([draft, related_ready])

    response = client.get("/admin/materials/secret-draft", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "secret-draft"
    # D-02: byte-shaped like the reader DTO — exact key set, no `status` key anywhere
    assert set(body.keys()) == {
        "slug",
        "title",
        "dek",
        "body_markdown",
        "format",
        "provenance",
        "tags",
        "related",
        "reading_minutes",
        "published_at",
        "editor",
    }
    assert "status" not in body
    # D-04 literal: the draft's own body really is served
    assert body["body_markdown"] == "## Draft\n\nDraft body."
    # D-08: no unpublished relations/taxonomy — even though a ready target resolves
    assert body["tags"] == []
    assert body["related"] == []
    # DTO default byline, not a re-typed literal
    assert body["editor"] == EDITOR_BYLINE


def test_admin_material_preview_employee_returns_403() -> None:
    """D-03: 403 comes only from require_admin (the DB-role gate), never from the slug lookup."""
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client, headers, _container = _preview_env([draft], role="employee")

    response = client.get("/admin/materials/secret-draft", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_admin_material_preview_anonymous_returns_401() -> None:
    """D-03: no Bearer token → 401 from the auth dependency, before any slug lookup."""
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client, _headers, _container = _preview_env([draft])

    response = client.get("/admin/materials/secret-draft")

    assert response.status_code == 401


def test_admin_material_preview_unknown_slug_returns_404() -> None:
    """D-04/D-12: unknown slug for an admin → 404 material_not_found, never 403."""
    client, headers, _container = _preview_env([])

    response = client.get("/admin/materials/does-not-exist", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "material_not_found"


def test_admin_material_preview_ready_slug_returns_404() -> None:
    """D-04/D-12: a ready slug is not previewable — 404, never a 3xx redirect and never 403."""
    ready = _material(slug="rag-systems", status=MaterialStatus.READY)
    client, headers, _container = _preview_env([ready])

    response = client.get("/admin/materials/rag-systems", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "material_not_found"


def test_admin_material_preview_outcomes_are_status_driven() -> None:
    """D-04/D-12: with a draft and a ready material present, the outcome follows status."""
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT, material_id=1)
    ready = _material(slug="rag-systems", status=MaterialStatus.READY, material_id=2)
    client, headers, _container = _preview_env([draft, ready])

    draft_response = client.get("/admin/materials/secret-draft", headers=headers)
    ready_response = client.get("/admin/materials/rag-systems", headers=headers)

    assert draft_response.status_code == 200
    assert ready_response.status_code == 404
    assert ready_response.json()["detail"] == "material_not_found"


def test_admin_material_preview_draft_has_no_store() -> None:
    """D-07: only the draft preview response carries Cache-Control: no-store."""
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client, headers, _container = _preview_env([draft])

    response = client.get("/admin/materials/secret-draft", headers=headers)

    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"


def test_admin_material_preview_repeat_is_identical_and_writes_nothing() -> None:
    """Idempotency (D-08): a repeat read is byte-identical and leaves the material untouched."""
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client, headers, container = _preview_env([draft])
    before = container.materials.get_by_slug("secret-draft")
    before_snapshot = (before.status, before.body_markdown, before.updated_at)

    first = client.get("/admin/materials/secret-draft", headers=headers)
    second = client.get("/admin/materials/secret-draft", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["tags"] == [] and first.json()["related"] == []
    assert second.json()["tags"] == [] and second.json()["related"] == []
    after = container.materials.get_by_slug("secret-draft")
    assert (after.status, after.body_markdown, after.updated_at) == before_snapshot


def test_admin_material_preview_malformed_slug_never_succeeds() -> None:
    """Edge: a slug violating _SLUG_PATTERN is refused at validation — never 200 and never 403."""
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client, headers, _container = _preview_env([draft])

    for path in (
        "/admin/materials/--bad--",
        "/admin/materials/",
        "/admin/materials/Привет-мир",
    ):
        response = client.get(path, headers=headers)
        assert response.status_code in (404, 422)
        assert response.status_code not in (200, 403)
        assert response.json().get("detail") != "forbidden"


def test_admin_material_preview_slug_key_parity_with_reader() -> None:
    """D-02: the preview payload's key set equals the reader DTO's shape oracle."""
    ready = _material(slug="rag-systems", status=MaterialStatus.READY, material_id=1)
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT, material_id=2)
    client, headers, _container = _preview_env([ready, draft])

    reader_response = client.get("/materials/rag-systems", headers=headers)
    preview_response = client.get("/admin/materials/secret-draft", headers=headers)

    assert reader_response.status_code == 200
    assert preview_response.status_code == 200
    assert set(preview_response.json().keys()) == set(reader_response.json().keys())
