"""CORS allowlist from API_CORS_ORIGINS must reflect allowed Origin."""

from backend.composition.settings import Settings
from backend.interface.http.app import create_app
from backend.interface.http.middleware import RequestIdMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


def _settings_with_cors(origins: str) -> Settings:
    return Settings(
        api_cors_origins=origins,
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
        supabase_url="",
        supabase_publishable_key="",
        supabase_secret_key="",
        supabase_jwks_url="",
        supabase_jwt_issuer="",
    )


def test_cors_middleware_is_outermost() -> None:
    """Starlette runs the last added middleware first; CORS must wrap the rest."""
    app = create_app(_settings_with_cors("http://localhost:5173"))
    classes = [layer.cls for layer in app.user_middleware]
    assert classes[0] is CORSMiddleware
    assert classes.index(CORSMiddleware) < classes.index(RequestIdMiddleware)


def test_allowed_origin_receives_access_control_allow_origin() -> None:
    origins = (
        "http://127.0.0.1:5173,http://localhost:5173,"
        "http://127.0.0.1:5174,http://localhost:5174"
    )
    client = TestClient(create_app(_settings_with_cors(origins)))
    origin = "http://127.0.0.1:5173"
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin


def test_put_method_is_advertised_in_cors_preflight() -> None:
    """PIPE-02 (RESEARCH Pitfall 1): PUT /admin/pipeline/config preflight must allow PUT."""
    client = TestClient(create_app(_settings_with_cors("http://127.0.0.1:5173")))
    response = client.options(
        "/admin/pipeline/config",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "PUT",
        },
    )
    assert response.status_code == 200
    allowed = response.headers.get("access-control-allow-methods", "")
    assert "PUT" in allowed


def test_delete_method_is_advertised_in_cors_preflight() -> None:
    """SRC-01 / D-18: DELETE /admin/ingest-sources/{id} preflight must allow DELETE."""
    client = TestClient(create_app(_settings_with_cors("http://127.0.0.1:5173")))
    response = client.options(
        "/admin/ingest-sources/1",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "DELETE",
        },
    )
    assert response.status_code == 200
    allowed = response.headers.get("access-control-allow-methods", "")
    assert "DELETE" in allowed


def test_disallowed_origin_does_not_receive_allow_origin() -> None:
    client = TestClient(
        create_app(_settings_with_cors("http://127.0.0.1:5173,http://localhost:5173"))
    )
    response = client.get(
        "/health",
        headers={"Origin": "http://evil.example"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in {
        k.lower(): v for k, v in response.headers.items()
    } or response.headers.get("access-control-allow-origin") != "http://evil.example"
