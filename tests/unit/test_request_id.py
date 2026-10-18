"""X-Request-ID correlation and structlog context binding."""

import json

from backend.composition.settings import Settings
from backend.interface.http.app import create_app
from fastapi.testclient import TestClient


def _settings() -> Settings:
    return Settings(
        api_cors_origins="http://127.0.0.1:5173",
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
        supabase_url="",
        supabase_publishable_key="",
        supabase_secret_key="",
        supabase_jwks_url="",
        supabase_jwt_issuer="",
    )


def test_response_includes_generated_x_request_id() -> None:
    client = TestClient(create_app(_settings()))
    response = client.get("/health")
    assert response.status_code == 200
    request_id = response.headers.get("x-request-id")
    assert request_id
    assert len(request_id) >= 8


def test_response_echoes_incoming_x_request_id() -> None:
    client = TestClient(create_app(_settings()))
    response = client.get("/health", headers={"X-Request-ID": "trace-abc-123"})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "trace-abc-123"


def test_structlog_context_binds_request_id(capsys) -> None:
    client = TestClient(create_app(_settings()))
    response = client.get("/health", headers={"X-Request-ID": "bound-rid-99"})
    assert response.status_code == 200
    # TestClient runs middleware in a worker thread; assert bind via JSON log merge.
    out = capsys.readouterr().out
    events = [json.loads(line) for line in out.splitlines() if line.strip().startswith("{")]
    finished = [e for e in events if e.get("event") == "request_finished"]
    assert finished, f"expected request_finished log, got: {out!r}"
    assert finished[-1].get("request_id") == "bound-rid-99"
