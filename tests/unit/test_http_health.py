"""Public GET /health must respond without auth."""

from backend.composition.settings import Settings
from backend.interface.http.app import create_app
from fastapi.testclient import TestClient


def test_health_returns_200_ok_without_auth() -> None:
    settings = Settings(
        api_cors_origins="http://127.0.0.1:5173",
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
        supabase_url="",
        supabase_publishable_key="",
        supabase_secret_key="",
        supabase_jwks_url="",
        supabase_jwt_issuer="",
    )
    client = TestClient(create_app(settings))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
