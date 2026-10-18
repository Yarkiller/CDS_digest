"""GET /health/ready + check_readiness use-case (monitoring readiness probe)."""

from __future__ import annotations

from backend.application.ports.health_probe import ComponentHealth
from backend.application.use_cases.check_readiness import check_readiness
from backend.composition.container import build_in_memory_container
from backend.composition.settings import Settings
from backend.interface.http.app import create_app
from fastapi.testclient import TestClient


class _Probe:
    def __init__(self, name: str, healthy: bool, detail: str = "") -> None:
        self._health = ComponentHealth(name=name, healthy=healthy, detail=detail)

    def check(self) -> ComponentHealth:
        return self._health


def _settings() -> Settings:
    return Settings(
        api_cors_origins="http://127.0.0.1:5173",
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
    )


def test_check_readiness_all_healthy() -> None:
    report = check_readiness([_Probe("database", True)])
    assert report.ready is True
    assert report.components[0].name == "database"
    assert report.to_dict()["status"] == "ready"


def test_check_readiness_reports_failure_without_raising() -> None:
    report = check_readiness([_Probe("database", False, "boom")])
    assert report.ready is False
    payload = report.to_dict()
    assert payload["status"] == "not_ready"
    assert payload["components"]["database"] == {"healthy": False, "detail": "boom"}


def test_check_readiness_treats_raising_probe_as_unhealthy() -> None:
    class _Exploding:
        name = "probe"

        def check(self) -> ComponentHealth:
            raise RuntimeError("connection refused")

    report = check_readiness([_Exploding()])
    assert report.ready is False
    assert "connection refused" in report.to_dict()["components"]["probe"]["detail"]


def test_ready_returns_200_without_auth_when_all_probes_healthy() -> None:
    container = build_in_memory_container()
    client = TestClient(create_app(_settings(), container=container))
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert "components" in body


def test_ready_returns_503_when_a_probe_fails() -> None:
    container = build_in_memory_container()
    container.health_probes = (_Probe("database", False, "downstream down"),)
    client = TestClient(create_app(_settings(), container=container))
    response = client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["components"]["database"]["healthy"] is False


def test_ready_does_not_leak_probe_error_detail() -> None:
    # Security: the public endpoint must not expose connection strings/SDK errors.
    container = build_in_memory_container()
    container.health_probes = (
        _Probe("database", False, "postgres://user:pass@db.internal:5432/postgres refused"),
    )
    client = TestClient(create_app(_settings(), container=container))
    body = client.get("/health/ready").json()
    detail = body["components"]["database"]["detail"]
    assert "postgres://" not in detail
    assert "pass" not in detail
    assert detail == "unhealthy"
