"""RED→GREEN: GET/PUT /admin/pipeline/config tracer — PIPE-01/PIPE-03, D-08/D-10/D-11/D-13.

Reuses the ES256 JWT harness from tests/unit/test_http_admin.py and attaches the
in-memory PipelineConfigRepository/Validator fakes to the container post-build
(16-01 does not touch composition/container.py; field declaration + wiring is 16-02).
"""

from __future__ import annotations

import json
import re
import sys
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
from backend.domain.current_user import CurrentUser
from backend.domain.errors import PipelineConfigValidationError
from backend.domain.pipeline_config import PipelineConfig, PipelineConfigError
from backend.infrastructure.yaml_pipeline_config_validator import (
    YamlPipelineConfigValidator,
    _EXTRA_ANCHOR_KEY_MESSAGE,
    _MERGE_TOO_BIG_MESSAGE,
    _TOO_DEEP_MESSAGE,
    _UNREADABLE_MESSAGE,
)
from backend.interface.http.app import create_app
from backend.tests_support.in_memory import (
    InMemoryPipelineConfigRepository,
    InMemoryPipelineConfigValidator,
)

ISSUER = "https://auth.example/auth/v1"
CONFIG_URL = "/admin/pipeline/config"


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
    config: PipelineConfig | None = None,
    attach_repo: bool = True,
    attach_validator: bool = True,
) -> tuple[TestClient, dict[str, str], Any]:
    """Admin-authenticated client with the tracer fakes attached post-build."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.pipeline_config = (
        InMemoryPipelineConfigRepository(config) if attach_repo else None
    )
    container.pipeline_config_validator = (
        InMemoryPipelineConfigValidator() if attach_validator else None
    )
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    return client, {"Authorization": f"Bearer {token}"}, container


def _real_validator_admin_env() -> tuple[TestClient, dict[str, str], Any]:
    """Admin client on the default wiring: real YamlPipelineConfigValidator + recording repo."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    return client, {"Authorization": f"Bearer {token}"}, container


def test_get_returns_empty_state_when_absent() -> None:
    """D-11: absent singleton row → 200 with exactly {yaml:'', updated_at:null}."""
    client, headers, _container = _admin_env(config=None)

    response = client.get(CONFIG_URL, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body == {"yaml": "", "updated_at": None}
    assert set(body.keys()) == {"yaml", "updated_at"}


def test_get_returns_saved_config() -> None:
    """PIPE-01/PIPE-03: a stored config round-trips through the read route (D-11)."""
    stored = PipelineConfig(
        yaml="template: podcast\nroles:\n  - analyst\nlanguage: ru\nmax_chars: 8000\n",
        updated_at=datetime(2026, 10, 4, 9, 0, tzinfo=timezone.utc),
    )
    client, headers, _container = _admin_env(config=stored)

    response = client.get(CONFIG_URL, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"yaml", "updated_at"}
    assert body["yaml"] == stored.yaml
    assert body["updated_at"] is not None


def test_put_then_get_round_trip_returns_saved_yaml() -> None:
    """PIPE-01/PIPE-03, D-11: PUT a valid document, then GET returns the identical yaml."""
    yaml_text = "template: lecture\nroles:\n  - employee\nlanguage: ru\nmax_chars: 4000\n"
    client, headers, container = _admin_env(config=None)

    put = client.put(CONFIG_URL, headers=headers, json={"yaml": yaml_text})

    assert put.status_code == 200
    put_body = put.json()
    assert set(put_body.keys()) == {"yaml", "updated_at"}
    assert put_body["yaml"] == yaml_text
    assert put_body["updated_at"] is not None
    # The validator port ran before the write (validate-then-persist).
    assert container.pipeline_config_validator.calls == [yaml_text]

    get = client.get(CONFIG_URL, headers=headers)

    assert get.status_code == 200
    assert get.json()["yaml"] == yaml_text


def test_put_merge_document_round_trips() -> None:
    """PIPE-04 / ROADMAP criterion 1: a merge-key config persists and reads back verbatim."""
    yaml_text = (
        "<<: &base\n"
        "  template: lecture\n"
        "  roles:\n"
        "    - employee\n"
        "  language: ru\n"
        "  max_chars: 4000\n"
    )
    client, headers, container = _real_validator_admin_env()

    put = client.put(CONFIG_URL, headers=headers, json={"yaml": yaml_text})

    assert put.status_code == 200
    put_body = put.json()
    assert set(put_body.keys()) == {"yaml", "updated_at"}
    assert put_body["yaml"] == yaml_text
    assert put_body["updated_at"] is not None
    # Validate-then-persist through the REAL strict validator: exactly one write.
    assert container.pipeline_config.save_count == 1

    get = client.get(CONFIG_URL, headers=headers)

    assert get.status_code == 200
    assert get.json()["yaml"] == yaml_text


def test_put_merge_source_duplicate_returns_400_and_writes_nothing() -> None:
    """CR-01 end-to-end: a duplicate inside a merge source → 400 envelope, zero writes."""
    client, headers, container = _real_validator_admin_env()
    document = (
        "<<: &b {language: ru, language: en}\n"
        "template: lecture\n"
        "roles: [employee]\n"
        "max_chars: 4000\n"
    )

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": document})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == [
        PipelineConfigError(
            path="", message="found duplicate key ('language')", line=1
        ).to_dict()
    ]
    # The reject never reached the repository (D-03/D-07): zero saves.
    assert container.pipeline_config.save_count == 0


def test_get_put_require_admin_unauth_401_and_employee_403() -> None:
    """D-10 / T-16-01: both routes are admin-gated; 401 unauthenticated, 403 non-admin."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)

    anon_container = build_in_memory_container()
    anon_container.pipeline_config = InMemoryPipelineConfigRepository()
    anon_container.pipeline_config_validator = InMemoryPipelineConfigValidator()
    anon_client = _client(jwk, anon_container)

    assert anon_client.get(CONFIG_URL).status_code == 401
    assert anon_client.put(CONFIG_URL, json={"yaml": "template: lecture"}).status_code == 401

    employee_container = build_in_memory_container()
    employee_container.pipeline_config = InMemoryPipelineConfigRepository()
    employee_container.pipeline_config_validator = InMemoryPipelineConfigValidator()
    _seed_profile(
        employee_container,
        user_id="user-uuid-1",
        email="alice@sberbank.ru",
        role="employee",
    )
    employee_client = _client(jwk, employee_container)
    employee_token = _mint(private_key, email="alice@sberbank.ru")
    employee_headers = {"Authorization": f"Bearer {employee_token}"}

    get = employee_client.get(CONFIG_URL, headers=employee_headers)
    assert get.status_code == 403
    assert get.json()["detail"] == "forbidden"
    assert "yaml" not in get.json()

    put = employee_client.put(
        CONFIG_URL,
        headers=employee_headers,
        json={"yaml": "template: lecture"},
    )
    assert put.status_code == 403
    assert put.json()["detail"] == "forbidden"
    assert "yaml" not in put.json()


def test_dto_exposes_only_yaml_and_updated_at_keys() -> None:
    """PIPE-03 / T-16-14: every GET/PUT success body exposes exactly {yaml, updated_at}."""
    yaml_text = "template: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 2000\n"
    client, headers, _container = _admin_env(config=None)

    empty_get = client.get(CONFIG_URL, headers=headers)
    assert empty_get.status_code == 200
    assert set(empty_get.json().keys()) == {"yaml", "updated_at"}

    put = client.put(CONFIG_URL, headers=headers, json={"yaml": yaml_text})
    assert put.status_code == 200
    assert set(put.json().keys()) == {"yaml", "updated_at"}

    saved_get = client.get(CONFIG_URL, headers=headers)
    assert saved_get.status_code == 200
    assert set(saved_get.json().keys()) == {"yaml", "updated_at"}


def test_missing_pipeline_config_returns_503() -> None:
    """D-11 guard: container with no pipeline_config → GET/PUT 503 not_configured."""
    client, headers, _container = _admin_env(attach_repo=False, attach_validator=False)

    get = client.get(CONFIG_URL, headers=headers)
    assert get.status_code == 503
    assert get.json()["detail"] == "pipeline_config_not_configured"

    put = client.put(CONFIG_URL, headers=headers, json={"yaml": "template: lecture"})
    assert put.status_code == 503
    assert put.json()["detail"] == "pipeline_config_not_configured"


def test_put_invalid_yaml_returns_400_top_level_errors_and_writes_nothing() -> None:
    """RED→GREEN PIPE-02, D-03/D-05: invalid YAML → 400 with top-level errors, zero writes."""
    client, headers, container = _real_validator_admin_env()

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": "template: [unclosed\n"})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) >= 1
    first = body["errors"][0]
    assert first["path"] == ""
    assert "message" in first
    # The reject never reached the repository (D-03/D-07): zero saves.
    assert container.pipeline_config.save_count == 0


def test_put_invalid_error_rows_are_verbatim_and_top_level() -> None:
    """RED→GREEN D-05: error rows expose path/message (+ optional line), verbatim server text."""
    client, headers, container = _real_validator_admin_env()
    document = (
        "template: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 100\nscore_factors: 1.0\n"
    )
    try:
        YamlPipelineConfigValidator().validate(document)
        raise AssertionError("expected the validator to reject the unknown key")
    except PipelineConfigValidationError as exc:
        expected = [error.to_dict() for error in exc.errors]

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": document})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == expected
    row = body["errors"][0]
    assert set(row.keys()) <= {"path", "message", "line"}
    assert row["path"] == "score_factors"
    assert "line" not in row
    assert container.pipeline_config.save_count == 0


def test_put_deeply_nested_yaml_returns_400_not_500() -> None:
    """RED→GREEN WR-02: deeply nested flow collections → structured 400, never an unhandled 500."""
    client, headers, container = _real_validator_admin_env()
    depth = sys.getrecursionlimit() + 500
    document = ("[" * depth) + ("]" * depth)

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": document})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == [
        {"path": "", "message": _TOO_DEEP_MESSAGE}
    ]
    # The reject never reached the repository (D-03/D-07): zero saves.
    assert container.pipeline_config.save_count == 0


def test_put_control_char_yaml_returns_400_not_500() -> None:
    """RED→GREEN CR-01: a control char → structured 400, never an unhandled 500."""
    client, headers, container = _real_validator_admin_env()
    document = "template: lecture\nroles:\n  - ds\nlanguage: \x00ru\nmax_chars: 100\n"

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": document})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == [
        {"path": "", "message": _UNREADABLE_MESSAGE}
    ]
    # The reject never reached the repository (D-03/D-07): zero saves.
    assert container.pipeline_config.save_count == 0


def _merge_bomb(*, fanout: int = 3, nesting: int = 13) -> str:
    """The fan-out merge bomb (17-RESEARCH § Q9): tiny document, huge expansion."""
    lines = ["a0: &a0 {k0: v0}"]
    for level in range(1, nesting + 1):
        sources = ", ".join([f"*a{level - 1}"] * fanout)
        lines.append(f"a{level}: &a{level} {{<<: [{sources}]}}")
    lines.extend(
        ("template: lecture", "roles: [employee]", "language: ru", "max_chars: 4000")
    )
    return "\n".join(lines) + "\n"


def test_put_merge_bomb_returns_400_and_writes_nothing() -> None:
    """PIPE-05: the merge bound's row crosses the unchanged HTTP envelope, zero writes."""
    client, headers, container = _real_validator_admin_env()

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": _merge_bomb()})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == [{"path": "", "message": _MERGE_TOO_BIG_MESSAGE}]
    # The reject never reached the repository (D-03/D-07): zero saves.
    assert container.pipeline_config.save_count == 0


def test_put_anchor_holder_key_returns_400_with_teaching_message() -> None:
    """D-06/D-07/D-09: the anchor-holder row crosses the unchanged envelope, zero writes."""
    client, headers, container = _real_validator_admin_env()
    document = (
        "defaults: &base\n"
        "  template: lecture\n"
        "  roles:\n"
        "    - employee\n"
        "  language: ru\n"
        "  max_chars: 4000\n"
        "<<: *base\n"
    )

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": document})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == [
        {"path": "defaults", "message": _EXTRA_ANCHOR_KEY_MESSAGE.format(key="defaults")}
    ]
    row = body["errors"][0]
    assert set(row.keys()) <= {"path", "message", "line"}
    assert "line" not in row
    # The reject never reached the repository (D-03/D-07): zero saves.
    assert container.pipeline_config.save_count == 0


def test_build_in_memory_container_wires_real_validator_and_repo() -> None:
    """RED→GREEN wiring: default container yields the in-memory repo + real YAML validator."""
    default_container = build_in_memory_container()

    assert isinstance(default_container.pipeline_config, InMemoryPipelineConfigRepository)
    assert isinstance(default_container.pipeline_config_validator, YamlPipelineConfigValidator)


def test_app_container_still_constructs_without_pipeline_kwargs() -> None:
    """RED→GREEN Pitfall 6: the new fields default to None so AppContainer(...) keeps working."""
    template = build_in_memory_container()
    bare = AppContainer(
        materials=template.materials,
        chunks=template.chunks,
        profiles=template.profiles,
        pings=template.pings,
        issues=template.issues,
        voting_cycles=template.voting_cycles,
        votes=template.votes,
        embedder=template.embedder,
        razbors=template.razbors,
        notebook_storage=template.notebook_storage,
        shortlist=template.shortlist,
        mailer=template.mailer,
        publisher=template.publisher,
    )

    assert bare.pipeline_config is None
    assert bare.pipeline_config_validator is None


_SUPABASE_IMPORT = re.compile(
    r"""(?:from|require\()\s*['"]@?supabase(?:[/'"])""",
    re.IGNORECASE,
)


def test_pipeline_page_reaches_storage_only_through_service_no_supabase() -> None:
    """RED→GREEN PIPE-03 / D-10 boundary guard (static-source assertion).

    The admin pipeline page must reach storage only through the SPA service module:
    it imports ``../services/pipelineConfigApi.js``, neither the page nor the service
    imports a supabase module, and only the service composes the
    ``/admin/pipeline/config`` URL. The same service module is the single place that
    exposes the Playwright mock-control harness (no storage coupling in components).
    """
    page_src = Path("web/src/pages/AdminPipelineConfigPage.jsx").read_text(encoding="utf-8")
    service_src = Path("web/src/services/pipelineConfigApi.js").read_text(encoding="utf-8")

    # The page consumes the service, never a transport/storage SDK directly.
    assert re.search(
        r"""from\s+['"]\.\./services/pipelineConfigApi\.js['"]""", page_src
    ), "AdminPipelineConfigPage must import ../services/pipelineConfigApi.js"
    assert not _SUPABASE_IMPORT.search(page_src), "page must not import a supabase module"
    assert not _SUPABASE_IMPORT.search(service_src), "service must not import a supabase module"

    # Only the service composes the transport URL — no component knows the endpoint.
    assert "/admin/pipeline/config" not in page_src
    assert "/admin/pipeline/config" in service_src

    # The mock-control harness lives on the service module (Task 1 deliverable).
    for arm in (
        "armRejectNextSave",
        "armFailNextSave",
        "armFailNextLoad",
        "resetPipelineConfigHarness",
    ):
        assert arm in service_src, f"service must expose {arm}"
