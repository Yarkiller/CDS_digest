---
phase: 05-admin-digest-publish
fixed_at: 2026-09-22T04:00:00Z
review_path: .planning/milestones/v1-phases/05-admin-digest-publish/05-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 5: Code Review Fix Report

**Fixed at:** 2026-09-22T04:00:00Z
**Source review:** `.planning/milestones/v1-phases/05-admin-digest-publish/05-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 8 (Critical + Warning; Info skipped)
- Fixed: 8
- Skipped: 0

**Verification:** Tier-1 re-reads and Tier-2 syntax/unit checks ran inside the isolated review-fix worktree (`.claude/worktrees/rf-05-*`). Playwright suites were not executed there (no worktree `node_modules`).

## Fixed Issues

### CR-01: Rank rewrite is outside the claim+publish transaction

**Files modified:** `supabase-integration/migrations/006_claim_publish_material_ids.sql`, `supabase-integration/src/supabase_integration/digest_publisher.py`, `backend/src/backend/application/ports/digest_publisher.py`, `tests/unit/test_supabase_digest_publisher_contract.py`, `tests/unit/test_phase5_migration_005.py`
**Commit:** `a7b6bac`
**Applied fix:** New migration 006 adds `p_material_ids bigint[]` to `claim_and_publish_digest` and assigns `digest_issue_items.position` from `unnest … WITH ORDINALITY` inside the RPC. Python adapter passes `p_material_ids` and no longer rewrites shortlist ranks via separate UPDATEs.

### CR-02: Audit failure after successful publish returns send failure

**Files modified:** `backend/src/backend/application/use_cases/send_digest.py`, `tests/unit/test_send_digest.py`
**Commit:** `3675965`
**Status:** `fixed: requires human verification`
**Applied fix:** After successful `claim_and_publish`, mail and ping audit are best-effort (`PersistenceError` logged; send still returns success).

### WR-01: D-86 preview gate ignores composition (order / intro / text)

**Files modified:** `web/src/services/adminPreviewComposition.js`, `web/src/pages/AdminDigestPage.jsx`, `tests/unit/test_admin_preview_composition.js`
**Commit:** `9288154`
**Applied fix:** `compositionFingerprint({ intro, blocks })` drives the preview gate; reordering, intro edits, or interstitial text clear `emailPreviewed`.

### WR-02: Stub/live send body ignores previewed intro and text blocks

**Files modified:** `backend/src/backend/application/use_cases/send_digest.py`, `backend/src/backend/application/use_cases/preview_digest_email.py`, `backend/src/backend/interface/http/routes/admin.py`, `web/src/services/adminApi.js`, `web/src/pages/AdminDigestPage.jsx`, `tests/unit/test_send_digest.py`
**Commit:** `29e3d12`
**Status:** `fixed: requires human verification`
**Applied fix:** Shared `compose_digest_segments` / `compose_digest_body`; send accepts `intro` + `blocks` (HTTP + SPA) so StubMailer body matches preview.

### WR-03: Admin role probe maps any `/me` failure to Forbidden

**Files modified:** `web/src/pages/AdminDigestPage.jsx`, `web/src/services/meApi.js`, `tests/admin.spec.js`
**Commit:** `230f954`
**Applied fix:** `UNAUTHORIZED`/`FORBIDDEN` → ForbiddenPage; network/other → ServiceUnavailable + retry. Sticky `__DIGEST_ME_FAIL_FETCH__` for Playwright.

### WR-04: Live shortlist DTO omits fields the SPA already consumes

**Files modified:** `backend/src/backend/domain/shortlist.py`, `backend/src/backend/application/use_cases/get_admin_shortlist.py`, `backend/src/backend/interface/http/routes/admin.py`, `backend/src/backend/tests_support/in_memory.py`, `supabase-integration/src/supabase_integration/shortlist_repository.py`, `tests/unit/test_get_admin_shortlist.py`
**Commit:** `eec8112`
**Applied fix:** Response/DTO now include `week_label`, `sent_at`, and per-item `dek` (materials.dek joined in the adapter).

### WR-05: Display truncate (≤5) vs send pool (full batch) mismatch

**Files modified:** `backend/src/backend/domain/shortlist.py`, `backend/src/backend/application/use_cases/get_admin_shortlist.py`, `backend/src/backend/application/use_cases/send_digest.py`, `backend/src/backend/application/use_cases/preview_digest_email.py`, `backend/src/backend/tests_support/in_memory.py`, `tests/unit/test_send_digest.py`
**Commits:** `53de3a4`, `7c46b5e`, `925b21a`
**Status:** `fixed: requires human verification`
**Applied fix:** Shared `visible_shortlist_items` (top-5 by rank) used by GET, preview, and send; in-memory publisher accepts a material_ids subset.

### WR-06: Partial batch decision apply leaves silent half-state

**Files modified:** `web/src/pages/AdminDigestPage.jsx`, `tests/admin.spec.js`
**Commit:** `96804f3`
**Applied fix:** Per-id try/catch; on any failure reload shortlist via GET, toast failed ids, keep failed ids selected; clear selection only when all succeed.

---

_Fixed: 2026-09-22T04:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
