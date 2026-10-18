"""RED→GREEN: migration 007 SQL contract for persist_draft_and_enqueue (D-05, D-06, D-09)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPO_ROOT / "supabase-integration/migrations/007_phase9_persist_draft.sql"


def _sql() -> str:
    assert MIGRATION.is_file(), "007_phase9_persist_draft.sql must exist"
    return MIGRATION.read_text(encoding="utf-8")


def _sql_without_line_comments() -> str:
    """Executable SQL only — `--` comments cannot satisfy D-09 assertions."""
    kept: list[str] = []
    for raw in _sql().splitlines():
        kept.append(raw.split("--", 1)[0])
    return "\n".join(kept)


def _normalized_executable_sql() -> str:
    return " ".join(_sql_without_line_comments().lower().split())


def test_migration_007_exists_and_adds_provenance_columns() -> None:
    text = _sql()
    executable = _normalized_executable_sql()
    assert "alter table materials add column if not exists source_url text not null" in executable
    assert "add column if not exists youtube_video_id text" in executable
    assert "alter column youtube_video_id set not null" in executable
    assert "add constraint materials_youtube_video_id_key unique (youtube_video_id)" in executable
    assert "source_author text not null" in executable
    assert "source_published_at timestamptz" in executable
    assert "phase5-admin-draft" in text


def test_migration_007_youtube_video_id_unique_is_ddl_not_comment() -> None:
    """D-09 / PERS-01: unique NOT NULL must be ALTER/CONSTRAINT statements, not a comment."""
    executable = _normalized_executable_sql()
    comments = "\n".join(
        raw.split("--", 1)[1] for raw in _sql().splitlines() if "--" in raw
    )
    comments_norm = " ".join(comments.lower().split())

    assert "add column if not exists youtube_video_id text" in executable
    assert "alter column youtube_video_id set not null" in executable
    assert "add constraint materials_youtube_video_id_key unique (youtube_video_id)" in executable
    assert "materials_youtube_video_id_key" in executable
    # The plan phrase may live in a comment; executable SQL must still carry the ALTER/constraint.
    if "youtube_video_id text not null unique" in comments_norm:
        assert "youtube_video_id text not null unique" not in executable


def test_migration_007_creates_persist_draft_and_enqueue_rpc() -> None:
    executable = _normalized_executable_sql()
    assert "create or replace function public.persist_draft_and_enqueue" in executable
    assert "security invoker" in executable
    assert "'draft'" in executable
    assert "'статья'" in executable
    assert "on conflict (youtube_video_id) do nothing" in executable
    assert "sent_at is null" in executable
    assert "p_batch_size" in executable
    assert "get diagnostics" in executable
    # Trailing comments used to satisfy status=/format=; those phrases must not count.
    assert "status='draft'" not in executable
    assert "format='статья'" not in executable


def test_migration_007_skips_sent_batches_and_is_idempotent_on_video_id() -> None:
    """RESEARCH batch_sent: a latest batch with sent_at set is not the enqueue target."""
    executable = _normalized_executable_sql()
    assert "and b.sent_at is null" in executable
    assert "where b.sent_at is null" in executable
    assert "v_inserted" in executable
    assert "on conflict (youtube_video_id) do nothing" in executable
    assert "digest_shortlist_items" in executable
    assert "decision" in executable and "'pending'" in executable
    # Comment-only skip/conflict wording must not satisfy the contract.
    assert "sent_at is not null" not in executable
    assert "already exists" not in executable


def test_migration_007_conflict_path_does_not_fall_back_to_sent_batch() -> None:
    """WR-02: existing material returns only an unsent shortlist row, else P0001."""
    executable = _normalized_executable_sql()
    assert executable.count("select si.batch_id, si.rank") == 1
    assert "and b.sent_at is null" in executable
    assert "has no shortlist row" in executable


def test_migration_007_locks_unsent_batch_and_unique_rank() -> None:
    """WR-05: lock the chosen batch before count; ranks unique per batch."""
    executable = _normalized_executable_sql()
    assert "for update" in executable
    assert "unique (batch_id, rank)" in executable
    assert "digest_shortlist_items_batch_id_rank_key" in executable


def test_migration_007_grants_execute_only_to_service_role() -> None:
    text = _sql()
    lower = text.lower()
    assert "revoke all" in lower and "from public" in lower
    assert "revoke all" in lower and "from anon, authenticated" in lower
    assert "grant execute" in lower and "to service_role" in lower


def test_migration_007_has_no_destructive_wipes() -> None:
    text = _sql()
    lower = text.lower()
    assert "\ntruncate " not in lower
    assert "\ndrop table" not in lower
    assert "\ndelete from materials" not in lower
    assert "\ndelete from digest_shortlist" not in lower
