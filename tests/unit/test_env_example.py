"""Committed .env.example lists Phase 1 keys and is not gitignored."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = (
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_JWKS_URL",
    "SUPABASE_JWT_ISSUER",
    "API_CORS_ORIGINS",
    "ALLOWED_EMAIL_DOMAINS",
    "APP_CONTAINER",
    "VITE_SUPABASE_URL",
    "VITE_SUPABASE_PUBLISHABLE_KEY",
    "VITE_API_BASE_URL",
    "VITE_USE_MOCKS",
)


def test_env_example_lists_required_keys() -> None:
    path = REPO_ROOT / ".env.example"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for key in REQUIRED_KEYS:
        assert f"{key}=" in text, f"missing {key}"
    assert "VITE_SUPABASE_SECRET" not in text
    assert "5173" in text and "5174" in text


def test_env_example_is_not_gitignored() -> None:
    # Without -v: exit 0 means ignored. Negation patterns make -v exit 0 even when tracked.
    result = subprocess.run(
        ["git", "check-ignore", ".env.example"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, (
        f".env.example is ignored: {result.stdout or result.stderr}"
    )
