"""RED→GREEN: GET/PATCH /admin/ingestion-schedule — ING-06, D-14/D-16.

Harness mirrors tests/unit/test_http_ingest_sources.py (ES256 JWT + container).
Imports of not-yet-shipped symbols stay inside helpers for assertion-level RED.
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
SCHEDULE_URL = "/admin/ingestion-schedule"

_TIME_MSG = "Укажите время в формате ЧЧ:ММ."
_DAYS_EMPTY_MSG = "Выберите хотя бы один день недели."
_NO_CHANGES_MSG = "Нет изменений."


def _schedule_repo_cls() -> type:
    try:
        from backend.tests_support.in_memory import InMemoryIngestionScheduleRepository
    except ImportError as exc:  # pragma: no cover - RED until fake ships
        pytest.fail(f"InMemoryIngestionScheduleRepository not importable: {exc}")
    return InMemoryIngestionScheduleRepository


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
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    assert hasattr(container, "ingestion_schedule"), (
        "AppContainer.ingestion_schedule field missing (D-14)"
    )
    if attach_repo:
        container.ingestion_schedule = _schedule_repo_cls()()
    else:
        container.ingestion_schedule = None
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    return client, {"Authorization": f"Bearer {token}"}, container


def test_get_requires_admin_unauth_401_and_employee_403() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    repo_cls = _schedule_repo_cls()

    anon_container = build_in_memory_container()
    anon_container.ingestion_schedule = repo_cls()
    anon_client = _client(jwk, anon_container)
    assert anon_client.get(SCHEDULE_URL).status_code == 401

    employee_container = build_in_memory_container()
    employee_container.ingestion_schedule = repo_cls()
    _seed_profile(
        employee_container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    employee_client = _client(jwk, employee_container)
    employee_token = _mint(private_key, email="alice@sberbank.ru")
    employee_headers = {"Authorization": f"Bearer {employee_token}"}
    get = employee_client.get(SCHEDULE_URL, headers=employee_headers)
    assert get.status_code == 403
    assert get.json()["detail"] == "forbidden"


def test_get_defaults_on_fresh_container() -> None:
    client, headers, _container = _admin_env()
    response = client.get(SCHEDULE_URL, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "enabled",
        "time_of_day",
        "days_of_week",
        "last_run_at",
        "updated_at",
    }
    assert body["enabled"] is True
    assert body["time_of_day"] == "06:00"
    assert body["days_of_week"] == [1, 2, 3, 4, 5, 6, 7]
    assert body["last_run_at"] is None


def test_patch_enabled_only_preserves_time_and_days() -> None:
    client, headers, _container = _admin_env()
    patched = client.patch(SCHEDULE_URL, headers=headers, json={"enabled": False})
    assert patched.status_code == 200
    body = patched.json()
    assert body["enabled"] is False
    assert body["time_of_day"] == "06:00"
    assert body["days_of_week"] == [1, 2, 3, 4, 5, 6, 7]


def test_patch_time_and_days_normalizes() -> None:
    client, headers, _container = _admin_env()
    patched = client.patch(
        SCHEDULE_URL,
        headers=headers,
        json={"time_of_day": "07:30", "days_of_week": [5, 1, 1]},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["time_of_day"] == "07:30"
    assert body["days_of_week"] == [1, 5]


def test_patch_invalid_time_returns_400_top_level_errors() -> None:
    client, headers, container = _admin_env()
    before = container.ingestion_schedule.update_calls
    response = client.patch(
        SCHEDULE_URL,
        headers=headers,
        json={"time_of_day": "25:00"},
    )
    assert response.status_code == 400
    assert response.json() == {
        "errors": [{"path": "time_of_day", "message": _TIME_MSG}],
    }
    assert "detail" not in response.json()
    assert container.ingestion_schedule.update_calls == before


def test_patch_empty_days_and_empty_body_reject() -> None:
    client, headers, container = _admin_env()
    before = container.ingestion_schedule.update_calls

    empty_days = client.patch(
        SCHEDULE_URL,
        headers=headers,
        json={"days_of_week": []},
    )
    assert empty_days.status_code == 400
    assert empty_days.json()["errors"][0]["message"] == _DAYS_EMPTY_MSG

    empty_body = client.patch(SCHEDULE_URL, headers=headers, json={})
    assert empty_body.status_code == 400
    assert empty_body.json()["errors"][0]["path"] == "body"
    assert empty_body.json()["errors"][0]["message"] == _NO_CHANGES_MSG
    assert container.ingestion_schedule.update_calls == before


def test_patch_unknown_field_returns_422_without_write() -> None:
    client, headers, container = _admin_env()
    before = container.ingestion_schedule.update_calls
    response = client.patch(
        SCHEDULE_URL,
        headers=headers,
        json={"cron": "* * * * *"},
    )
    assert response.status_code == 422
    assert container.ingestion_schedule.update_calls == before


def test_missing_ingestion_schedule_returns_503() -> None:
    client, headers, _container = _admin_env(attach_repo=False)
    get = client.get(SCHEDULE_URL, headers=headers)
    assert get.status_code == 503
    assert get.json()["detail"] == "ingestion_schedule_not_configured"

    patch = client.patch(SCHEDULE_URL, headers=headers, json={"enabled": False})
    assert patch.status_code == 503
    assert patch.json()["detail"] == "ingestion_schedule_not_configured"


def test_build_in_memory_container_wires_ingestion_schedule() -> None:
    repo_cls = _schedule_repo_cls()
    container = build_in_memory_container()
    assert hasattr(container, "ingestion_schedule")
    assert container.ingestion_schedule is not None
    assert isinstance(container.ingestion_schedule, repo_cls)
