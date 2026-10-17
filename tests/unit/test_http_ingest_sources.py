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
# D-14 valid playlist: PL + 32 [A-Za-z0-9_-] = 34 chars total
VALID_PLAYLIST_ID = "PLrAXtmRdnEQy6nuLMHjMZOz59Oq8S_1rX"

_INVALID_SOURCE_ID_MSG = "Укажите канонический id: UC… для канала или PL… для плейлиста."
_KIND_MISMATCH_MSG = "Тип источника не совпадает с префиксом идентификатора."
_LABEL_TOO_LONG_MSG = "Название не длиннее 120 символов."
_DUPLICATE_MSG = "Этот источник уже добавлен"


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


def _assert_400_errors_zero_writes(
    response,
    repo,
    *,
    writes_before: int,
    expected_errors: list[dict[str, str]],
) -> None:
    """D-19/D-20: top-level {errors:[…]} without detail; zero repository writes."""
    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == expected_errors
    for row in body["errors"]:
        assert set(row.keys()) == {"path", "message"}
        assert "line" not in row
    assert repo.write_count == writes_before
    assert len(repo.adds) == writes_before  # adds only grow on successful POST


@pytest.mark.parametrize(
    ("kind", "source_id"),
    [
        ("channel", "dQw4w9WgXcQ"),  # 11-char video id
        ("channel", "@handle"),
        ("channel", "https://youtube.com/channel/UC_x5XG1OV2P6uZZ5FSMdItQ"),
        ("channel", "UC" + ("x" * 21)),  # UC + 21 ≠ 24
        ("playlist", "PL" + ("y" * 31)),  # PL + 31 ≠ 34
    ],
)
def test_post_invalid_source_id_returns_400_and_writes_nothing(
    kind: str,
    source_id: str,
) -> None:
    """SRC-02 / D-14/D-20: invalid ids → 400 {errors:[…]} and write_count unchanged."""
    client, headers, container = _admin_env()
    repo = container.ingest_sources
    before = repo.write_count

    response = client.post(
        SOURCES_URL,
        headers=headers,
        json={"kind": kind, "source_id": source_id, "label": None},
    )

    _assert_400_errors_zero_writes(
        response,
        repo,
        writes_before=before,
        expected_errors=[{"path": "source_id", "message": _INVALID_SOURCE_ID_MSG}],
    )


@pytest.mark.parametrize(
    ("kind", "source_id"),
    [
        ("channel", VALID_PLAYLIST_ID),
        ("playlist", VALID_CHANNEL_ID),
    ],
)
def test_post_kind_prefix_mismatch_returns_400_and_writes_nothing(
    kind: str,
    source_id: str,
) -> None:
    """SRC-02 / D-06: kind/prefix mismatch → 400 path source_id; zero writes."""
    client, headers, container = _admin_env()
    repo = container.ingest_sources
    before = repo.write_count

    response = client.post(
        SOURCES_URL,
        headers=headers,
        json={"kind": kind, "source_id": source_id, "label": None},
    )

    _assert_400_errors_zero_writes(
        response,
        repo,
        writes_before=before,
        expected_errors=[{"path": "source_id", "message": _KIND_MISMATCH_MSG}],
    )


def test_post_duplicate_returns_400_and_writes_nothing() -> None:
    """SRC-02 / D-15: duplicate (kind, source_id) → 400; write_count unchanged after first add."""
    client, headers, container = _admin_env()
    repo = container.ingest_sources

    first = client.post(
        SOURCES_URL,
        headers=headers,
        json={"kind": "channel", "source_id": VALID_CHANNEL_ID, "label": None},
    )
    assert first.status_code == 201
    after_add = repo.write_count
    assert after_add == 1

    duplicate = client.post(
        SOURCES_URL,
        headers=headers,
        json={"kind": "channel", "source_id": VALID_CHANNEL_ID, "label": "again"},
    )

    _assert_400_errors_zero_writes(
        duplicate,
        repo,
        writes_before=after_add,
        expected_errors=[{"path": "source_id", "message": _DUPLICATE_MSG}],
    )


def test_post_label_too_long_returns_400_and_writes_nothing() -> None:
    """SRC-02 / D-07: label length 121 → 400 path label; zero writes."""
    client, headers, container = _admin_env()
    repo = container.ingest_sources
    before = repo.write_count

    response = client.post(
        SOURCES_URL,
        headers=headers,
        json={
            "kind": "channel",
            "source_id": VALID_CHANNEL_ID,
            "label": "x" * 121,
        },
    )

    _assert_400_errors_zero_writes(
        response,
        repo,
        writes_before=before,
        expected_errors=[{"path": "label", "message": _LABEL_TOO_LONG_MSG}],
    )


def test_post_unknown_field_returns_422() -> None:
    """D-18: extra=forbid on create → 422 for unknown JSON fields."""
    client, headers, container = _admin_env()
    before = container.ingest_sources.write_count

    response = client.post(
        SOURCES_URL,
        headers=headers,
        json={
            "kind": "channel",
            "source_id": VALID_CHANNEL_ID,
            "label": None,
            "extra_field": True,
        },
    )

    assert response.status_code == 422
    assert container.ingest_sources.write_count == before


def test_patch_disable_then_delete_hard_removes_row() -> None:
    """SRC-01 / D-10/D-18: PATCH is_enabled=false → 200; DELETE → 204 and gone from GET."""
    client, headers, container = _admin_env()

    created = client.post(
        SOURCES_URL,
        headers=headers,
        json={"kind": "channel", "source_id": VALID_CHANNEL_ID, "label": "Ch"},
    )
    assert created.status_code == 201
    source_pk = created.json()["id"]

    patched = client.patch(
        f"{SOURCES_URL}/{source_pk}",
        headers=headers,
        json={"is_enabled": False},
    )
    assert patched.status_code == 200
    assert patched.json()["id"] == source_pk
    assert patched.json()["is_enabled"] is False
    assert patched.json()["source_id"] == VALID_CHANNEL_ID

    listed = client.get(SOURCES_URL, headers=headers)
    assert listed.status_code == 200
    assert listed.json()["sources"][0]["is_enabled"] is False

    deleted = client.delete(f"{SOURCES_URL}/{source_pk}", headers=headers)
    assert deleted.status_code == 204
    assert deleted.content in (b"", b"null") or deleted.text in ("", "null")

    after = client.get(SOURCES_URL, headers=headers)
    assert after.status_code == 200
    assert after.json() == {"sources": []}
    assert container.ingest_sources.write_count >= 3  # add + set_enabled + delete


def test_delete_missing_id_returns_404() -> None:
    """SRC-01 idempotency: DELETE unknown id → 404 (domain not-found mapped)."""
    client, headers, _container = _admin_env()

    response = client.delete(f"{SOURCES_URL}/999999", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "ingest_source_not_found"


def test_readd_after_delete_succeeds() -> None:
    """SRC-01: after hard DELETE, same (kind, source_id) can be POSTed again → 201."""
    client, headers, _container = _admin_env()
    payload = {"kind": "playlist", "source_id": VALID_PLAYLIST_ID, "label": None}

    first = client.post(SOURCES_URL, headers=headers, json=payload)
    assert first.status_code == 201
    source_pk = first.json()["id"]

    deleted = client.delete(f"{SOURCES_URL}/{source_pk}", headers=headers)
    assert deleted.status_code == 204

    second = client.post(SOURCES_URL, headers=headers, json=payload)
    assert second.status_code == 201
    assert second.json()["source_id"] == VALID_PLAYLIST_ID
    assert second.json()["kind"] == "playlist"
    assert second.json()["id"] != source_pk


def test_patch_delete_require_admin_unauth_401_and_employee_403() -> None:
    """T-23-09: PATCH/DELETE admin-gated; 401 unauthenticated, 403 non-admin."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    repo_cls = _ingest_repo_cls()

    anon_container = build_in_memory_container()
    anon_container.ingest_sources = repo_cls()
    anon_client = _client(jwk, anon_container)

    assert anon_client.patch(
        f"{SOURCES_URL}/1",
        json={"is_enabled": False},
    ).status_code == 401
    assert anon_client.delete(f"{SOURCES_URL}/1").status_code == 401

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

    patch = employee_client.patch(
        f"{SOURCES_URL}/1",
        headers=employee_headers,
        json={"is_enabled": False},
    )
    assert patch.status_code == 403
    assert patch.json()["detail"] == "forbidden"

    delete = employee_client.delete(f"{SOURCES_URL}/1", headers=employee_headers)
    assert delete.status_code == 403
    assert delete.json()["detail"] == "forbidden"


def test_patch_unknown_field_returns_422() -> None:
    """D-18: extra=forbid on patch → 422 for unknown JSON fields."""
    client, headers, container = _admin_env()
    created = client.post(
        SOURCES_URL,
        headers=headers,
        json={"kind": "channel", "source_id": VALID_CHANNEL_ID, "label": None},
    )
    assert created.status_code == 201
    source_pk = created.json()["id"]
    before = container.ingest_sources.write_count

    response = client.patch(
        f"{SOURCES_URL}/{source_pk}",
        headers=headers,
        json={"is_enabled": False, "label": "nope"},
    )

    assert response.status_code == 422
    assert container.ingest_sources.write_count == before
