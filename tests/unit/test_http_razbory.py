"""HTTP GET /razbory — JWT gate + chronology list DTO (RAZB-01 / D-66).

Notebook download: GET /razbory/{id}/notebook FileResponse (RAZB-03 / D-70…72).
"""

from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jwt.algorithms import ECAlgorithm

from backend.composition.container import AppContainer, build_in_memory_container
from backend.composition.settings import Settings
from backend.domain.errors import PersistenceError
from backend.domain.razbor import Razbor, RazborStatus
from backend.interface.http.app import create_app
from backend.tests_support.in_memory import InMemoryRazborRepository

ISSUER = "https://auth.example/auth/v1"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SEED_IPYNB = _REPO_ROOT / "design-frontend" / "assets" / "notebooks" / "hybrid-retrieval.ipynb"


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


def _razbor(
    *,
    razbor_id: int,
    title: str,
    status: RazborStatus,
    meeting_at: datetime | None,
    created_at: datetime,
) -> Razbor:
    return Razbor(
        id=razbor_id,
        title=title,
        body_markdown="",
        meeting_at=meeting_at,
        status=status,
        notebook_path=None,
        created_at=created_at,
    )


def _client(
    signing_jwk: dict[str, Any],
    container: AppContainer | None = None,
    *,
    notebook_root: str = "",
) -> TestClient:
    settings = Settings(
        api_cors_origins="http://127.0.0.1:5173",
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
        supabase_url="",
        supabase_publishable_key="",
        supabase_secret_key="",
        supabase_jwks_url="https://unused.example/jwks.json",
        supabase_jwt_issuer=ISSUER,
        notebook_root=notebook_root,
    )
    wired = container
    if wired is None:
        wired = build_in_memory_container(notebook_root=notebook_root or None)
    elif notebook_root:
        from backend.infrastructure.local_notebook_storage import LocalNotebookStorage

        wired.notebook_storage = LocalNotebookStorage(notebook_root)
    app = create_app(
        settings,
        container=wired,
        signing_key_resolver=lambda _token: signing_jwk,
    )
    return TestClient(app)


def test_razbory_list_without_authorization_returns_401() -> None:
    """RAZB-01 / D-66: GET /razbory requires Bearer JWT."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.get("/razbory")
    assert response.status_code == 401


def test_razbory_list_returns_chronology_items_including_announcement() -> None:
    """RAZB-01 / D-68: list DTO has id, title, meeting_at, status; announcement included."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    earlier = datetime(2026, 3, 10, tzinfo=timezone.utc)
    later = datetime(2026, 4, 14, tzinfo=timezone.utc)
    created = datetime(2026, 3, 1, tzinfo=timezone.utc)
    container = build_in_memory_container()
    container.razbors = InMemoryRazborRepository(
        [
            _razbor(
                razbor_id=1,
                title="Older published",
                status=RazborStatus.PUBLISHED,
                meeting_at=earlier,
                created_at=created,
            ),
            _razbor(
                razbor_id=2,
                title="RAG в корпоративной среде",
                status=RazborStatus.ANNOUNCEMENT,
                meeting_at=later,
                created_at=created,
            ),
        ]
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/razbory", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    items = body["items"]
    assert len(items) == 2
    assert items[0]["id"] == 2
    assert items[0]["title"] == "RAG в корпоративной среде"
    assert items[0]["status"] == "announcement"
    assert items[0]["meeting_at"] is not None
    assert set(items[0].keys()) >= {"id", "title", "meeting_at", "status"}
    assert items[1]["id"] == 1
    assert items[1]["status"] == "published"


def test_razbory_list_orders_null_meeting_at_last() -> None:
    """RAZB-01 ordering: meeting_at DESC NULLS LAST, then created_at DESC."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    meeting = datetime(2026, 4, 1, tzinfo=timezone.utc)
    older_created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer_created = datetime(2026, 2, 1, tzinfo=timezone.utc)
    container = build_in_memory_container()
    container.razbors = InMemoryRazborRepository(
        [
            _razbor(
                razbor_id=10,
                title="No meeting",
                status=RazborStatus.ANNOUNCEMENT,
                meeting_at=None,
                created_at=newer_created,
            ),
            _razbor(
                razbor_id=11,
                title="Has meeting",
                status=RazborStatus.PUBLISHED,
                meeting_at=meeting,
                created_at=older_created,
            ),
            _razbor(
                razbor_id=12,
                title="Also no meeting older",
                status=RazborStatus.ANNOUNCEMENT,
                meeting_at=None,
                created_at=older_created,
            ),
        ]
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/razbory", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [11, 10, 12]


def test_razbory_list_empty_returns_200_with_empty_items() -> None:
    """RAZB-01 empty ASSUMPTION / D-69 backend: empty repo → 200 items=[]."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, build_in_memory_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/razbory", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["items"] == []


class _UnavailableRazbors:
    def list_for_reader(self) -> list[Razbor]:
        raise PersistenceError("razbors down")

    def get(self, razbor_id: int) -> Razbor | None:
        raise PersistenceError("razbors down")


def test_razbory_list_persistence_error_returns_503_unavailable() -> None:
    """D-69 / RAZB-01: PersistenceError → 503 razbory_unavailable."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.razbors = _UnavailableRazbors()  # type: ignore[assignment]
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/razbory", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 503
    assert response.json()["detail"] == "razbory_unavailable"


def test_razbory_detail_without_authorization_returns_401() -> None:
    """RAZB-02: GET /razbory/{id} requires Bearer JWT."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key))
    response = client.get("/razbory/1")
    assert response.status_code == 401


def test_razbory_detail_not_found_returns_404() -> None:
    """RAZB-02: unknown id → 404 razbor_not_found (SPA soft 404)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    client = _client(jwk, build_in_memory_container())
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/razbory/99", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "razbor_not_found"


def test_razbory_detail_returns_published_longread_fields() -> None:
    """RAZB-02: published detail DTO has id, title, meeting_at, status, body_markdown."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    meeting = datetime(2026, 3, 17, tzinfo=timezone.utc)
    created = datetime(2026, 3, 1, tzinfo=timezone.utc)
    body = "## Intro\n\nHello.\n\n## Deep dive\n\nMore."
    container = build_in_memory_container()
    container.razbors = InMemoryRazborRepository(
        [
            Razbor(
                id=2,
                title="Anomaly Detection во внутреннем аудите",
                body_markdown=body,
                meeting_at=meeting,
                status=RazborStatus.PUBLISHED,
                notebook_path=None,
                created_at=created,
            )
        ]
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/razbory/2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == 2
    assert payload["title"] == "Anomaly Detection во внутреннем аудите"
    assert payload["status"] == "published"
    assert payload["meeting_at"] is not None
    assert payload["body_markdown"] == body
    assert set(payload.keys()) >= {"id", "title", "meeting_at", "status", "body_markdown"}


def test_razbory_detail_announcement_returns_empty_body() -> None:
    """D-68: announcement detail is stub — body_markdown emptied, status announcement."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    meeting = datetime(2026, 4, 14, tzinfo=timezone.utc)
    created = datetime(2026, 3, 1, tzinfo=timezone.utc)
    container = build_in_memory_container()
    container.razbors = InMemoryRazborRepository(
        [
            Razbor(
                id=4,
                title="RAG в корпоративной среде",
                body_markdown="## Draft\n\nHidden.",
                meeting_at=meeting,
                status=RazborStatus.ANNOUNCEMENT,
                notebook_path=None,
                created_at=created,
            )
        ]
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/razbory/4", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "announcement"
    assert payload["title"] == "RAG в корпоративной среде"
    assert payload["body_markdown"] == ""


def test_razbory_notebook_without_authorization_returns_401(tmp_path: Path) -> None:
    """RAZB-03 / D-70: GET /razbory/{id}/notebook requires Bearer JWT."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    client = _client(_public_jwk(private_key), notebook_root=str(tmp_path))
    response = client.get("/razbory/2/notebook")
    assert response.status_code == 401


def test_razbory_notebook_streams_attachment_when_available(tmp_path: Path) -> None:
    """RAZB-03 / D-70: notebook_available → FileResponse attachment with ipynb bytes."""
    assert _SEED_IPYNB.is_file()
    dest = tmp_path / "notebooks" / "anomaly.ipynb"
    dest.parent.mkdir(parents=True)
    shutil.copyfile(_SEED_IPYNB, dest)
    expected = dest.read_bytes()

    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    created = datetime(2026, 3, 1, tzinfo=timezone.utc)
    container = build_in_memory_container()
    container.razbors = InMemoryRazborRepository(
        [
            Razbor(
                id=2,
                title="Anomaly Detection",
                body_markdown="## Intro\n\nHi.",
                meeting_at=created,
                status=RazborStatus.PUBLISHED,
                notebook_path="notebooks/anomaly.ipynb",
                created_at=created,
            )
        ]
    )
    client = _client(jwk, container, notebook_root=str(tmp_path))
    token = _mint(private_key, email="alice@sberbank.ru")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/razbory/2/notebook", headers=headers)
    assert response.status_code == 200
    assert response.content == expected
    content_type = response.headers.get("content-type", "")
    assert "ipynb" in content_type or content_type.startswith("application/")
    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition.lower()
    assert "anomaly.ipynb" in disposition

    # Idempotent read — repeat download succeeds again (RAZB-03 ASSUMPTION).
    again = client.get("/razbory/2/notebook", headers=headers)
    assert again.status_code == 200
    assert again.content == expected


def test_razbory_notebook_rejects_path_traversal(tmp_path: Path) -> None:
    """RAZB-03 / T-04-09: path with .. outside NOTEBOOK_ROOT → 400/404, never file bytes."""
    secret = tmp_path.parent / "outside-secret.ipynb"
    secret.write_text('{"cells":[]}', encoding="utf-8")
    (tmp_path / "notebooks").mkdir(parents=True, exist_ok=True)

    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    created = datetime(2026, 3, 1, tzinfo=timezone.utc)
    container = build_in_memory_container()
    container.razbors = InMemoryRazborRepository(
        [
            Razbor(
                id=7,
                title="Escape attempt",
                body_markdown="## Intro\n\nHi.",
                meeting_at=created,
                status=RazborStatus.PUBLISHED,
                notebook_path="../outside-secret.ipynb",
                created_at=created,
            )
        ]
    )
    client = _client(jwk, container, notebook_root=str(tmp_path))
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/razbory/7/notebook",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (400, 404)
    assert response.content != secret.read_bytes()
    assert b'"cells"' not in response.content


def test_razbory_notebook_missing_returns_404(tmp_path: Path) -> None:
    """RAZB-03 / D-72: missing notebook_path or file → 404 (UI shows disabled strip)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    created = datetime(2026, 3, 1, tzinfo=timezone.utc)
    container = build_in_memory_container()
    container.razbors = InMemoryRazborRepository(
        [
            Razbor(
                id=3,
                title="No notebook",
                body_markdown="## Intro\n\nHi.",
                meeting_at=created,
                status=RazborStatus.PUBLISHED,
                notebook_path=None,
                created_at=created,
            )
        ]
    )
    client = _client(jwk, container, notebook_root=str(tmp_path))
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/razbory/3/notebook",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
