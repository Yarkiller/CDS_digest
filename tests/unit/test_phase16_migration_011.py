"""RED/contract: migration 011 pipeline_config singleton + RLS (PIPE-03, D-08).

Reads the migration as text (no DB). Mirrors tests/unit/test_phase5_migration_005.py.
"""

from __future__ import annotations

from pathlib import Path

_MIGRATION = "supabase-integration/migrations/011_phase16_pipeline_config.sql"


def _text() -> str:
    path = Path(_MIGRATION)
    assert path.exists(), f"migration missing: {_MIGRATION}"
    return path.read_text(encoding="utf-8")


def test_migration_011_creates_singleton_pipeline_config_table() -> None:
    """D-08: singleton table (id = 1 PK + CHECK) holding yaml + updated_at."""
    lower = _text().lower()
    assert "create table if not exists public.pipeline_config" in lower
    assert "id integer primary key default 1" in lower
    assert "check (id = 1)" in lower
    assert "yaml text not null" in lower
    assert "updated_at timestamptz" in lower


def test_migration_011_enables_rls_with_no_permissive_policy() -> None:
    """T-16-10 / Pitfall 7: RLS enabled, deny-by-default — no permissive policy invented."""
    lower = _text().lower()
    assert "enable row level security" in lower
    assert "create policy" not in lower


def test_migration_011_has_no_wipe_statements() -> None:
    """Shared VM safety: insert/DDL only — never a destructive wipe."""
    lower = _text().lower()
    assert "\ntruncate " not in lower
    assert "\ndelete from" not in lower
