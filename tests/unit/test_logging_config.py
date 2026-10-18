"""Structured logging config: LOG_LEVEL env + status-based log levels (Step 7)."""

from __future__ import annotations

import json
import logging

from backend.composition.settings import Settings
from backend.interface.http.app import create_app
from backend.interface.http.middleware import level_for_status, resolve_log_level
from fastapi.testclient import TestClient


def _settings() -> Settings:
    return Settings(
        api_cors_origins="http://127.0.0.1:5173",
        allowed_email_domains="@sberbank.ru,@omega.sbrf.ru",
    )


def test_level_for_status_maps_server_errors_to_error() -> None:
    assert level_for_status(500) == "error"
    assert level_for_status(503) == "error"


def test_level_for_status_maps_client_errors_to_warning() -> None:
    assert level_for_status(404) == "warning"
    assert level_for_status(401) == "warning"


def test_level_for_status_maps_success_to_info() -> None:
    assert level_for_status(200) == "info"
    assert level_for_status(302) == "info"


def test_resolve_log_level_parses_names_and_defaults_to_info() -> None:
    assert resolve_log_level("debug") == logging.DEBUG
    assert resolve_log_level("WARNING") == logging.WARNING
    assert resolve_log_level("nonsense") == logging.INFO
    assert resolve_log_level("") == logging.INFO


def test_settings_from_env_reads_log_level() -> None:
    assert Settings.from_env({"LOG_LEVEL": "warning"}).log_level == "warning"
    assert Settings.from_env({}).log_level == "info"


def test_4xx_request_is_logged_at_warning(capsys) -> None:
    client = TestClient(create_app(_settings()))
    response = client.get("/definitely-missing")
    assert response.status_code == 404
    out = capsys.readouterr().out
    events = [json.loads(line) for line in out.splitlines() if line.strip().startswith("{")]
    client_errors = [event for event in events if event.get("event") == "request_client_error"]
    assert client_errors, f"expected request_client_error log, got: {out!r}"
    assert client_errors[-1]["level"] == "warning"
