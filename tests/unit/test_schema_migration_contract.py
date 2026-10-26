"""Contract: initial migration defines ingestion, publication, and knowledge layers."""

from pathlib import Path


def test_initial_migration_defines_core_tables() -> None:
    migration = Path("supabase-integration/migrations/001_initial_schema.sql")
    assert migration.is_file()
    sql = migration.read_text(encoding="utf-8")

    for table in (
        "ingestion_sources",
        "ingestion_jobs",
        "source_texts",
        "materials",
        "material_tags",
        "material_relations",
        "digest_issues",
        "digest_issue_items",
        "digest_shortlist_batches",
        "digest_shortlist_items",
        "knowledge_chunks",
        "voting_cycles",
        "topics",
        "topic_materials",
        "votes",
        "razbors",
        "activity_events",
        "profiles",
    ):
        assert f"create table {table}" in sql.lower() or f"create table if not exists {table}" in sql.lower()

    assert "vector(" in sql.lower()
    assert "tsvector" in sql.lower()
    assert "enable row level security" in sql.lower()
