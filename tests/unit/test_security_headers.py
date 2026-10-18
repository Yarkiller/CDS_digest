"""OWASP A05: security headers on API responses."""

from backend.composition.settings import Settings
from backend.interface.http.app import create_app
from fastapi.testclient import TestClient


def _client() -> TestClient:
    return TestClient(
        create_app(
            Settings(
                api_cors_origins="http://127.0.0.1:5173",
                allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
            )
        )
    )


def test_response_sets_mime_and_frame_guards() -> None:
    response = _client().get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_response_sets_referrer_and_permissions_policy() -> None:
    response = _client().get("/health")
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "camera=()" in response.headers["permissions-policy"]


def test_response_sets_hsts() -> None:
    response = _client().get("/health")
    assert "max-age=" in response.headers["strict-transport-security"]
