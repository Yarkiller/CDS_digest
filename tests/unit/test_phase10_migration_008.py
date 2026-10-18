"""RED→GREEN: migration 008 SQL contract for stored slug + already_saved (D-09, D-12; CLI-02)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPO_ROOT / "supabase-integration/migrations/008_phase10_persist_already_saved.sql"


def _sql() -> str:
    assert MIGRATION.is_file(), "008_phase10_persist_already_saved.sql must exist"
    return MIGRATION.read_text(encoding="utf-8")


def _sql_without_line_comments() -> str:
    """Executable SQL only — `--` comments cannot satisfy D-09/D-12 assertions."""
    kept: list[str] = []
    for raw in _sql().splitlines():
        kept.append(raw.split("--", 1)[0])
    return "\n".join(kept)


def _normalized_executable_sql() -> str:
    return " ".join(_sql_without_line_comments().lower().split())


def test_migration_008_exists_and_replaces_persist_rpc() -> None:
    executable = _normalized_executable_sql()
    assert "create or replace function public.persist_draft_and_enqueue" in executable
    assert "security invoker" in executable
    assert "on conflict (youtube_video_id) do nothing" in executable
    assert "v_inserted" in executable


def test_migration_008_conflict_returns_stored_materials_slug_not_caller_p_slug() -> None:
    """D-12: conflict branch slug comes from materials.slug, not caller p_slug."""
    executable = _normalized_executable_sql()
    # Insert success may still emit 'slug', p_slug once; conflict must not rely on it alone.
    assert executable.count("'slug', p_slug") == 1
    assert "materials.slug" in executable or "m.slug" in executable
    # Conflict return must select stored slug (declare/into or subquery), not only p_slug.
    assert "v_inserted = 0" in executable
    assert "'already_saved', true" in executable


def test_migration_008_both_returns_include_already_saved() -> None:
    """D-09: insert → already_saved false; conflict → already_saved true."""
    executable = _normalized_executable_sql()
    assert executable.count("jsonb_build_object") >= 2
    assert "'already_saved', true" in executable
    assert "'already_saved', false" in executable
    assert "already_saved" in executable


def test_migration_008_grants_execute_only_to_service_role() -> None:
    text = _sql()
    lower = text.lower()
    assert "revoke all" in lower and "from public" in lower
    assert "revoke all" in lower and "from anon, authenticated" in lower
    assert "grant execute" in lower and "to service_role" in lower


def test_migration_008_has_no_destructive_wipes() -> None:
    text = _sql()
    lower = text.lower()
    assert "\ntruncate " not in lower
    assert "\ndrop table" not in lower
    assert "truncate " not in _normalized_executable_sql()
    assert "drop table" not in _normalized_executable_sql()
