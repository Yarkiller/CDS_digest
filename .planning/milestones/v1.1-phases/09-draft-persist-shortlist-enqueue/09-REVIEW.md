---
phase: 09-draft-persist-shortlist-enqueue
reviewed: 2026-09-27T17:10:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - supabase-integration/migrations/007_phase9_persist_draft.sql
  - tests/unit/test_phase9_migration_007.py
  - tests/unit/test_persist_idempotency_overflow.py
  - tests/unit/test_captions_failure_zero_persist.py
  - ingestion-service/src/ingestion_service/tests_support/fakes.py
  - ingestion-service/src/ingestion_service/composition/settings.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 09: Code Review Report

**Reviewed:** 2026-09-27T17:10:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Targeted `--fix` pass for carried findings from the first full review (`b704755`). Incremental wave already closed WR-01 (executable-SQL RPC tests). This report re-opens the remaining production/test defects the operator asked to fix: WR-02, WR-04, WR-05.

**Already closed in live code (ledger only):** WR-03 unique-constraint comment-match; IN-02 Settings `repr=False`.

**By design (decision A):** IN-01 — RoleKind stays closed in Python (`normalize_roles`); the RPC dumps `p_roles`.

**Deferred:** IN-03 — environ-access scan of `ingestion-service/adapters` (low priority).

## Warnings

### WR-02: Conflict path can return a sent batch

**File:** `supabase-integration/migrations/007_phase9_persist_draft.sql:143-156`
**Issue:** After the unsent-batch lookup misses, the RPC falls back to any shortlist row, including `sent_at IS NOT NULL`. A post-publish re-run then returns a sent `batch_id`/`rank`.
**Fix:** Delete the sent-batch fallback. If no unsent shortlist row exists, raise `P0001`. Treat a post-publish re-run as `batch_creation_failed`. Mirror that on `BatchTrackingFakePersister`.

### WR-04: CAP-02 test never composes captions/article with persist

**File:** `tests/unit/test_captions_failure_zero_persist.py:45-69`
**Issue:** Tests construct a persist spy, raise on a helper that does not receive the spy, then assert `spy.calls == []`. The assertion cannot fail.
**Fix:** Extract `run_ingest_until_persist(captions, article, persist, metadata)` and test that function: script captions or article to fail and assert `persist.calls == []`.

### WR-05: Unlocked overflow can exceed `p_batch_size` and duplicate `rank`

**File:** `supabase-integration/migrations/007_phase9_persist_draft.sql:175-203`
**Issue:** The RPC counts items then inserts with no `FOR UPDATE` on the chosen batch. `digest_shortlist_items` has no `unique (batch_id, rank)`.
**Fix:** Lock the target unsent batch before counting, and add an idempotent `unique (batch_id, rank)` constraint.

## Info

### IN-01: RPC does not enforce the closed RoleKind set

**File:** `supabase-integration/migrations/007_phase9_persist_draft.sql:112`
**Issue:** `coalesce(p_roles, '{}'::text[])` writes any `text[]`. Python `normalize_roles` is the closed set.
**Fix:** Do not add a CHECK. Document as **decision A / by design**: ingest CLI is the only v1 writer; RoleKind is enforced on DTOs.

### IN-02: `Settings` repr includes `supabase_secret_key`

Already fixed in live code (`field(..., repr=False)` + behavior test). Close in ledger.

### IN-03: Environ-access scan skips ingestion-service adapters

**File:** `tests/unit/test_ingestion_settings.py`
**Issue:** Scan walks only `data-collection` adapters.
**Fix:** Defer (low). Phase 10 can extend the scan.

---

_Reviewed: 2026-09-27T17:10:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
