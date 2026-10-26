"""RED→GREEN: migration 009 SQL contract for sent-batch already_saved (D-08, D-09; CLI-02)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_009 = (
    REPO_ROOT
    / "supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql"
)
MIGRATION_008 = (
    REPO_ROOT / "supabase-integration/migrations/008_phase10_persist_already_saved.sql"
)


def _sql(path: Path = MIGRATION_009) -> str:
    assert path.is_file(), f"{path.name} must exist"
    return path.read_text(encoding="utf-8")


def _sql_without_line_comments(path: Path = MIGRATION_009) -> str:
    """Executable SQL only — `--` comments cannot satisfy D-08/D-09 assertions."""
    kept: list[str] = []
    for raw in _sql(path).splitlines():
        kept.append(raw.split("--", 1)[0])
    return "\n".join(kept)


def _normalized_executable_sql(path: Path = MIGRATION_009) -> str:
    return " ".join(_sql_without_line_comments(path).lower().split())


def _conflict_branch_executable() -> str:
    """Slice from conflict guard through end of conflict return (before new-material path)."""
    executable = _normalized_executable_sql()
    marker = "if v_inserted = 0 then"
    start = executable.find(marker)
    assert start >= 0, "conflict branch (v_inserted = 0) must exist"
    # New-material path starts by selecting latest unsent batch into v_batch_id
    # with sent_at is null and for update — after conflict return.
    after = executable[start:]
    end_marker = "select b.id into v_batch_id from public.digest_shortlist_batches"
    end = after.find(end_marker)
    assert end > 0, "new-material enqueue path must follow conflict branch"
    return after[:end]


def test_migration_009_exists_and_replaces_persist_rpc() -> None:
    executable = _normalized_executable_sql()
    assert "create or replace function public.persist_draft_and_enqueue" in executable
    assert "security invoker" in executable
    assert "on conflict (youtube_video_id) do nothing" in executable
    assert "v_inserted" in executable


def test_migration_009_conflict_returns_already_saved_true() -> None:
    executable = _normalized_executable_sql()
    assert "'already_saved', true" in executable
    assert "'already_saved', false" in executable
    assert executable.count("jsonb_build_object") >= 2


def test_migration_009_sent_batch_fallback_select_without_exclusive_sent_at_null() -> None:
    """D-08/D-09: after unsent lookup fails, SELECT any shortlist row (sent ok)."""
    conflict = _conflict_branch_executable()
    assert "and b.sent_at is null" in conflict
    # Fallback SELECT for material shortlist must not require sent_at is null exclusively.
    # Count shortlist item lookups in the conflict branch: prefer-unsent + any-row fallback.
    shortlist_lookups = conflict.count("from public.digest_shortlist_items")
    assert shortlist_lookups >= 2, (
        "conflict branch must fall back to a second shortlist SELECT when unsent is null"
    )
    # At least one shortlist SELECT in the conflict branch omits sent_at is null filter.
    # Split on shortlist FROM clauses and require one segment without the filter.
    parts = conflict.split("from public.digest_shortlist_items")
    fallback_without_sent_filter = False
    for part in parts[1:]:
        # Look ahead until next FROM or raise/return boundary for the WHERE clause window.
        window = part[: min(len(part), 280)]
        if "si.material_id = v_material_id" in window and "sent_at is null" not in window:
            fallback_without_sent_filter = True
            break
    assert fallback_without_sent_filter, (
        "second shortlist SELECT must include sent batches (no exclusive sent_at is null)"
    )


def test_migration_009_raise_p0001_only_when_no_shortlist_row() -> None:
    conflict = _conflict_branch_executable()
    assert "has no shortlist row" in conflict
    assert "using errcode = 'p0001'" in conflict
    # Must not raise solely because the unsent filter missed a sent-batch row —
    # raise follows the fallback SELECT (second shortlist lookup present).
    first_raise = conflict.find("raise exception")
    second_select = conflict.find(
        "from public.digest_shortlist_items",
        conflict.find("from public.digest_shortlist_items") + 1,
    )
    assert second_select >= 0
    assert first_raise > second_select, (
        "P0001 raise must come after the sent-batch fallback SELECT"
    )


def test_migration_009_grants_execute_only_to_service_role() -> None:
    text = _sql()
    lower = text.lower()
    assert "revoke all" in lower and "from public" in lower
    assert "revoke all" in lower and "from anon, authenticated" in lower
    assert "grant execute" in lower and "to service_role" in lower


def test_migration_009_has_no_destructive_wipes() -> None:
    executable = _normalized_executable_sql()
    assert "truncate " not in executable
    assert "drop table" not in executable


def test_migration_008_file_unchanged_relative_to_git_blob() -> None:
    """D-09: do not edit applied 008 in place — 009 is CREATE OR REPLACE."""
    import subprocess

    result = subprocess.run(
        [
            "git",
            "diff",
            "--",
            "supabase-integration/migrations/008_phase10_persist_already_saved.sql",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "", "008 must remain unmodified"
    assert MIGRATION_008.is_file()
