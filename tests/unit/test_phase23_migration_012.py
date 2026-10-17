"""RED/contract: migration 012 pipeline_ingest_sources + RLS (SRC-01, D-16/D-17).

Reads the migration as text (no DB). Mirrors tests/unit/test_phase16_migration_011.py.
"""

from __future__ import annotations

from pathlib import Path

_MIGRATION = "supabase-integration/migrations/012_phase23_ingest_sources.sql"


def _text() -> str:
    path = Path(_MIGRATION)
    assert path.exists(), f"migration missing: {_MIGRATION}"
    return path.read_text(encoding="utf-8")


def test_migration_012_creates_pipeline_ingest_sources_table() -> None:
    """D-16/D-17: identity PK, kind check, unique (kind, source_id), timestamps, is_enabled."""
    lower = _text().lower()
    assert "create table if not exists public.pipeline_ingest_sources" in lower
    assert "generated always as identity" in lower
    assert "kind text not null" in lower
    assert "check (kind in ('channel','playlist'))" in lower or (
        "check (kind in ('channel', 'playlist'))" in lower
    )
    assert "source_id text not null" in lower
    assert "is_enabled boolean not null default true" in lower
    assert "created_at timestamptz" in lower
    assert "updated_at timestamptz" in lower
    assert "unique (kind, source_id)" in lower


def test_migration_012_enables_rls_with_no_permissive_policy() -> None:
    """D-17 / T-23-11: RLS enabled, deny-by-default — no CREATE POLICY."""
    lower = _text().lower()
    assert "enable row level security" in lower
    assert "create policy" not in lower


def test_migration_012_has_no_wipe_statements() -> None:
    """Shared VM safety: insert/DDL only — never a destructive wipe."""
    lower = _text().lower()
    assert "\ntruncate " not in lower
    assert "\ndelete from" not in lower


def test_migration_012_does_not_touch_ingestion_sources() -> None:
    """D-16: must not ALTER/reuse public.ingestion_sources (fetched-items table)."""
    lower = _text().lower()
    assert "alter table public.ingestion_sources" not in lower
    assert "alter table ingestion_sources" not in lower
    # Table name in comments about what NOT to touch is fine; DDL must target pipeline_*.
    assert "create table if not exists public.ingestion_sources" not in lower
