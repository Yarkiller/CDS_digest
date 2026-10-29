"""RED→GREEN: migration 014 SQL contract for materials.topic_kind (KIND-01, D-01, T-30-06)."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_014 = (
    REPO_ROOT / "supabase-integration/migrations/014_phase30_materials_topic_kind.sql"
)
MIGRATION_007 = (
    REPO_ROOT / "supabase-integration/migrations/007_phase9_persist_draft.sql"
)
MIGRATION_008 = (
    REPO_ROOT / "supabase-integration/migrations/008_phase10_persist_already_saved.sql"
)
MIGRATION_009 = (
    REPO_ROOT
    / "supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql"
)
MATERIAL_REPOSITORY = (
    REPO_ROOT / "supabase-integration/src/supabase_integration/material_repository.py"
)
RUNBOOK = REPO_ROOT / "docs/agents/local-platform-runbook.md"

_DROP_12 = (
    "drop function if exists public.persist_draft_and_enqueue("
    "text, text, text, text, int, text, text, text, text, timestamptz, text[], int)"
)
_SIG_13 = (
    "text, text, text, text, int, text, text, text, text, timestamptz, text[], text, int"
)


def _sql(path: Path = MIGRATION_014) -> str:
    assert path.is_file(), f"{path.name} must exist"
    return path.read_text(encoding="utf-8")


def _sql_without_line_comments(path: Path = MIGRATION_014) -> str:
    """Executable SQL only — `--` comments cannot satisfy KIND-01 assertions."""
    kept: list[str] = []
    for raw in _sql(path).splitlines():
        kept.append(raw.split("--", 1)[0])
    return "\n".join(kept)


def _normalized_executable_sql(path: Path = MIGRATION_014) -> str:
    return " ".join(_sql_without_line_comments(path).lower().split())


def test_migration_014_adds_topic_kind_column() -> None:
    executable = _normalized_executable_sql()
    assert "add column if not exists" in executable
    assert "topic_kind" in executable
    assert "not null default 'conceptual'" in executable


def test_migration_014_drops_live_12_arg_then_creates_p_topic_kind() -> None:
    executable = _normalized_executable_sql()
    assert _DROP_12 in executable
    assert "p_topic_kind" in executable
    assert "p_topic_kind text default 'conceptual'" in executable
    assert "p_topic_kind text default 'conceptual', p_batch_size int" in executable
    create_idx = executable.find("create function public.persist_draft_and_enqueue")
    drop_idx = executable.find(_DROP_12)
    assert drop_idx >= 0
    assert create_idx > drop_idx, "CREATE 13-arg must follow DROP of the 12-arg signature"
    create_window = executable[create_idx:]
    insert_end = create_window.find("on conflict")
    assert insert_end > 0
    create_and_insert = create_window[:insert_end]
    assert "p_topic_kind" in create_and_insert
    assert "topic_kind" in create_and_insert


def test_migration_014_check_constraint_via_do_block() -> None:
    executable = _normalized_executable_sql()
    assert "do $$" in executable
    assert "pg_constraint" in executable
    assert "materials_topic_kind_check" in executable
    assert "check (topic_kind in ('practical', 'conceptual'))" in executable
    assert "add constraint if not exists" not in executable


def test_migration_014_keeps_already_saved_and_conflict_branches() -> None:
    executable = _normalized_executable_sql()
    assert "on conflict (youtube_video_id) do nothing" in executable
    assert "'already_saved', true" in executable
    assert "'already_saved', false" in executable
    assert "security invoker" in executable


def test_migration_014_grants_13_arg_execute_only_to_service_role() -> None:
    executable = _normalized_executable_sql()
    grant = (
        "grant execute on function public.persist_draft_and_enqueue("
        f"{_SIG_13}) to service_role"
    )
    revoke_public = (
        "revoke all on function public.persist_draft_and_enqueue("
        f"{_SIG_13}) from public"
    )
    revoke_anon = (
        "revoke all on function public.persist_draft_and_enqueue("
        f"{_SIG_13}) from anon, authenticated"
    )
    # Normalized SQL collapses newlines; allow optional spaces inside the type list.
    compact = executable.replace(" ", "")
    assert grant.replace(" ", "") in compact
    assert revoke_public.replace(" ", "") in compact
    assert revoke_anon.replace(" ", "") in compact


def test_migration_014_has_no_destructive_wipes_or_enum_type() -> None:
    executable = _normalized_executable_sql()
    assert "truncate " not in executable
    assert "drop table" not in executable
    assert "create type" not in executable
    assert " as enum" not in executable


def test_applied_007_008_009_files_unchanged_relative_to_git_blob() -> None:
    """T-30-06: do not edit applied 007/008/009 in place — 014 is DROP then CREATE."""
    for rel in (
        "supabase-integration/migrations/007_phase9_persist_draft.sql",
        "supabase-integration/migrations/008_phase10_persist_already_saved.sql",
        "supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql",
    ):
        result = subprocess.run(
            ["git", "diff", "--", rel],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "", f"{rel} must remain unmodified"
    assert MIGRATION_007.is_file()
    assert MIGRATION_008.is_file()
    assert MIGRATION_009.is_file()


def test_material_repository_select_list_omits_topic_kind() -> None:
    """T-30-05: reader SELECT must not grow topic_kind this phase."""
    text = MATERIAL_REPOSITORY.read_text(encoding="utf-8")
    start = text.find(".select(")
    assert start >= 0
    end = text.find(")", start)
    select_list = text[start:end].lower()
    assert "topic_kind" not in select_list
    result = subprocess.run(
        [
            "git",
            "diff",
            "--",
            "supabase-integration/src/supabase_integration/material_repository.py",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "", "material_repository.py SELECT list must stay unmodified"


def test_runbook_4l_documents_014_apply_and_13_arg_verify() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "## 4l." in text
    section = text.split("## 4l.", 1)[1]
    next_heading = section.find("\n## ")
    body = section if next_heading < 0 else section[:next_heading]
    lower = body.lower()
    assert "014_phase30_materials_topic_kind.sql" in body
    assert "topic_kind" in lower
    assert "materials_topic_kind_check" in lower
    assert "pronargs" in lower
    assert "13" in body
    assert "knowledge-db.ru" in lower
    assert "db reset" in lower
    assert "truncate" in lower
