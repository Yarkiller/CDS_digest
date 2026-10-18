"""RED/contract: migration 005 delivery columns + demo shortlist seed (ADMIN-01, D-78, D-87)."""

from __future__ import annotations

from pathlib import Path


def test_migration_005_has_delivery_columns_and_demo_seed() -> None:
    path = Path("supabase-integration/migrations/005_phase5_admin_shortlist.sql")
    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "delivery_status" in text
    assert "recipient_count" in text
    assert "published_issue_id" in text or "issue_url" in text
    assert "demo batch" in text
    assert "digest_shortlist" in text
    assert "claim_and_publish_digest" in text
    assert "service_role" in text
    # Insert/alter only — no destructive wipe statements (comments may mention TRUNCATE).
    assert "\ntruncate " not in text.lower()
    assert "\ndelete from digest_shortlist" not in text.lower()


def test_migration_006_passes_material_ids_into_claim_rpc() -> None:
    """CR-01: follow-up migration orders digest_issue_items from p_material_ids in-RPC."""
    path = Path("supabase-integration/migrations/006_claim_publish_material_ids.sql")
    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "p_material_ids" in text
    assert "claim_and_publish_digest" in text
    assert "unnest" in text.lower()
    assert "with ordinality" in text.lower()
    assert "service_role" in text
    assert "\ntruncate " not in text.lower()
