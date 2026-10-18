"""CLI-05 / D-02: ingestion-service/.env.example lists operator keys and is not gitignored."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INGESTION_ENV_EXAMPLE = REPO_ROOT / "ingestion-service" / ".env.example"
ROOT_ENV_EXAMPLE = REPO_ROOT / ".env.example"

REQUIRED_INGESTION_KEYS = (
    "SUPABASE_URL",
    "SUPABASE_SECRET_KEY",
    "SHORTLIST_BATCH_SIZE",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "YOUTUBE_PROXY_URL",
    "MAX_TRANSCRIPT_CHARS",
    "INGEST_TEMPLATE",
    "INGEST_MAX_VIDEOS_PER_SOURCE",
)


def test_ingestion_env_example_lists_required_keys() -> None:
    assert INGESTION_ENV_EXAMPLE.is_file()
    text = INGESTION_ENV_EXAMPLE.read_text(encoding="utf-8")
    for key in REQUIRED_INGESTION_KEYS:
        assert f"{key}=" in text, f"missing {key}"
    # Distinct from root backend example — no Vite keys required here (CLI-05).
    assert "VITE_" not in text


def test_ingestion_env_example_is_not_the_root_backend_example() -> None:
    assert INGESTION_ENV_EXAMPLE.resolve() != ROOT_ENV_EXAMPLE.resolve()
    ingestion = INGESTION_ENV_EXAMPLE.read_text(encoding="utf-8")
    root = ROOT_ENV_EXAMPLE.read_text(encoding="utf-8")
    assert ingestion != root


def test_ingestion_env_example_is_not_gitignored() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "ingestion-service/.env.example"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, (
        f"ingestion-service/.env.example is ignored: {result.stdout or result.stderr}"
    )


def test_cli_and_settings_do_not_autoload_dotenv() -> None:
    """CLI-05: process env only — no hardcoded .env path open in cli/settings."""
    cli_src = (
        REPO_ROOT
        / "ingestion-service"
        / "src"
        / "ingestion_service"
        / "cli.py"
    ).read_text(encoding="utf-8")
    settings_src = (
        REPO_ROOT
        / "ingestion-service"
        / "src"
        / "ingestion_service"
        / "composition"
        / "settings.py"
    ).read_text(encoding="utf-8")
    for body in (cli_src, settings_src):
        assert "load_dotenv" not in body
        assert "dotenv" not in body.lower()
        assert 'open(".env"' not in body
        assert "open('.env'" not in body


def test_runbook_documents_ingestion_env_file_invoke() -> None:
    """D-02 / CLI-05: runbook shows uv run --env-file ingestion-service/.env ingest."""
    runbook = (
        REPO_ROOT / "docs" / "agents" / "local-platform-runbook.md"
    ).read_text(encoding="utf-8")
    assert "uv run --env-file ingestion-service/.env ingest" in runbook
