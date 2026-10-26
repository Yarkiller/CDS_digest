---
phase: 14-draft-ready-justification-honesty
fixed_at: 2026-10-03T13:26:26.715Z
review_path: .planning/phases/14-draft-ready-justification-honesty/14-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 14: Code Review Fix Report

**Fixed at:** 2026-10-03T13:26:26.715Z
**Source review:** `.planning/phases/14-draft-ready-justification-honesty/14-REVIEW.md`
**Iteration:** 1
**Worktree mode:** `workflow.use_worktrees=false` — edits/commits and verification ran in the main checkout (no isolated worktree).

**Summary:**
- Findings in scope: 3 (CR-01, WR-01, WR-02)
- Fixed: 3
- Skipped: 0
- Info out of scope: IN-01 resolved as part of CR-01; IN-02 left untouched

## Fixed Issues

### CR-01: Live `markReady` rolls back UI after successful promote when shortlist refetch fails

**Files modified:** `tests/unit/test_admin_mark_ready.js`, `web/src/services/adminApi.js`, `web/src/pages/AdminDigestPage.jsx`
**Commit:** `48e94c3`
**Applied fix:** Live `markReady` try/catches `fetchShortlist` and returns `null` on refetch failure (POST success preserved). `promoteReady` uses the returned DTO when present; on `null`, best-effort refetch; rollback to previous items only when the promote POST itself fails. Also removes the redundant always-refetch path (IN-01).
**Verification:** `node --test tests/unit/test_admin_mark_ready.js` (6 passed) in main checkout; Tier-1 re-read of modified sections.

### WR-01: Batch helper aborts on `PersistenceError`, violating “never abort” and desyncing FE rollback

**Files modified:** `tests/unit/test_mark_material_ready.py`, `backend/src/backend/application/use_cases/mark_material_ready.py`, `backend/src/backend/interface/http/routes/admin.py`
**Commit:** `7e881df`
**Applied fix:** `mark_materials_ready` catches per-id `PersistenceError` → `materials_unavailable` and unexpected `Exception` → `unexpected_error`, continuing the batch. Batch HTTP route no longer maps escaped `PersistenceError` to wholesale 503 (missing materials repo still 503 via `_require_materials`).
**Verification:** `uv run pytest tests/unit/test_mark_material_ready.py -q` (6 passed) in main checkout; Python `ast.parse` on modified files.
**Commit status note:** `fixed: requires human verification` for batch error-mapping logic (confirm live Supabase `PersistenceError` surfaces as per-id `materials_unavailable` under partial failure).

### WR-02: Non-empty blank `factors` list still shadows readable flat keys (honesty edge)

**Files modified:** `tests/unit/test_score_factors.py`, `backend/src/backend/domain/shortlist.py`
**Commit:** `70df151`
**Applied fix:** After filtering structured `factors` labels, if none are readable, fall through to the flat-key branch (same as empty `factors: []`).
**Verification:** `uv run pytest tests/unit/test_score_factors.py -q` (8 passed) in main checkout; Python `ast.parse` on `shortlist.py`.

## Skipped Issues

None — all in-scope findings were fixed.

---

_Fixed: 2026-10-03T13:26:26.715Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
