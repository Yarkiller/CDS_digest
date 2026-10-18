---
phase: 09-draft-persist-shortlist-enqueue
fixed_at: 2026-09-27T17:20:00Z
review_path: .planning/phases/09-draft-persist-shortlist-enqueue/09-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 09: Code Review Fix Report

**Fixed at:** 2026-09-27T17:20:00Z
**Source review:** `.planning/phases/09-draft-persist-shortlist-enqueue/09-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 3 (WR-02, WR-04, WR-05)
- Fixed: 3
- Skipped: 0
- Ledger-only: IN-01 skipped (decision A / by design); WR-03 and IN-02 closed; IN-03 deferred

## Fixed Issues

### WR-02: Conflict path can return a sent batch

**Files modified:** `supabase-integration/migrations/007_phase9_persist_draft.sql`, `ingestion-service/src/ingestion_service/tests_support/fakes.py`, `tests/unit/test_phase9_migration_007.py`, `tests/unit/test_persist_idempotency_overflow.py`
**Applied fix:** Removed the conflict-path fallback that selected any shortlist row. An existing material now returns only an unsent (`sent_at is null`) shortlist row, otherwise `P0001`. `BatchTrackingFakePersister` raises `DraftPersistBatchError(reason="batch_creation_failed")` when the stored row sits on a sent batch.

### WR-04: CAP-02 test never composes captions/article with persist

**Files modified:** `ingestion-service/src/ingestion_service/application/use_cases/ingest_until_persist.py`, `tests/unit/test_captions_failure_zero_persist.py`
**Applied fix:** Added `run_ingest_until_persist` (captions → article → assemble → persist_draft). CAP-02 tests now fail the provider/generator inside that composer and assert `persist.calls == []` (and that article is not called when captions fail).

### WR-05: Unlocked overflow can exceed `p_batch_size` and duplicate `rank`

**Files modified:** `supabase-integration/migrations/007_phase9_persist_draft.sql`, `tests/unit/test_phase9_migration_007.py`
**Applied fix:** Latest unsent batch is selected `FOR UPDATE` before count. Idempotent unique constraint `digest_shortlist_items_batch_id_rank_key` on `(batch_id, rank)`.

## Ledger (not code)

### IN-01: RPC does not enforce the closed RoleKind set

**Disposition:** skipped — decision A / by design. Documented in `09-CONTEXT.md` (D-14a) and a comment on `p_roles` in migration 007.

### WR-03 / IN-02

**Disposition:** fixed (already in live code from the prior wave). Closed in `09-REVIEW-DISPOSITION.md`.

### IN-03: Environ-access scan skips ingestion-service adapters

**Disposition:** deferred — low priority.

## Verification

- `uv run pytest tests/unit/test_phase9_migration_007.py tests/unit/test_persist_idempotency_overflow.py tests/unit/test_captions_failure_zero_persist.py tests/unit/test_persist_draft_use_case.py` — 21 passed.

Re-apply migration `007_phase9_persist_draft.sql` on the shared VM (`CREATE OR REPLACE` function + unique constraint `IF NOT EXISTS`).

---

_Fixed: 2026-09-27T17:20:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
