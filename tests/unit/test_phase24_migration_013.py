"""RED/contract: migration 013 cursor columns + ingestion_schedule (ING-05/06, D-06/D-14).

Reads the migration as text (no DB). Mirrors tests/unit/test_phase23_migration_012.py.
"""

from __future__ import annotations

from pathlib import Path

_MIGRATION = "supabase-integration/migrations/013_phase24_scheduled_ingestion.sql"


def _text() -> str:
    path = Path(_MIGRATION)
    assert path.exists(), f"migration missing: {_MIGRATION}"
    return path.read_text(encoding="utf-8")


def test_migration_013_adds_cursor_columns_on_pipeline_ingest_sources() -> None:
    """D-06: last_seen_published_at + last_seen_video_id via add column if not exists."""
    lower = _text().lower()
    assert "alter table public.pipeline_ingest_sources" in lower
    assert "add column if not exists last_seen_published_at" in lower
    assert "add column if not exists last_seen_video_id" in lower
    assert "timestamptz" in lower
    assert lower.count("add column if not exists") >= 2


def test_migration_013_creates_singleton_ingestion_schedule() -> None:
    """D-14: singleton id=1, schedule fields, days CHECK, no seed row."""
    lower = _text().lower()
    assert "create table if not exists public.ingestion_schedule" in lower
    assert "check (id = 1)" in lower
    assert "enabled boolean not null default true" in lower
    assert "time_of_day time not null" in lower
    assert "days_of_week" in lower
    assert "last_run_at timestamptz" in lower
    assert "updated_at timestamptz" in lower
    assert "ingestion_schedule_days_within_iso_week" in lower or (
        "days_of_week <@ array[1,2,3,4,5,6,7]" in lower
        or "days_of_week <@ array[1, 2, 3, 4, 5, 6, 7]" in lower
    )


def test_migration_013_enables_rls_with_no_permissive_policy() -> None:
    """T-24-10 / D-14: RLS enabled, deny-by-default — no CREATE POLICY."""
    lower = _text().lower()
    assert "enable row level security" in lower
    assert "create policy" not in lower
    assert "deny-by-default" in lower or "no permissive policy" in lower


def test_migration_013_has_no_seed_insert_or_wipe() -> None:
    """D-14 / T-24-11: no seed id=1 insert; no destructive statements."""
    lower = _text().lower()
    assert "insert into" not in lower
    assert "\ntruncate " not in lower
    assert "\ndelete from" not in lower
    assert "\ndrop " not in lower
    assert "drop table" not in lower


def test_migration_013_does_not_touch_ingestion_sources() -> None:
    """Shared VM: must not ALTER public.ingestion_sources (fetched-items table)."""
    lower = _text().lower()
    assert "alter table public.ingestion_sources" not in lower
    assert "alter table ingestion_sources" not in lower
