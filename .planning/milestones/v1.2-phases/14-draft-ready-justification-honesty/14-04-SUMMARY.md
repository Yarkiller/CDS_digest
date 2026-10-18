---
phase: 14-draft-ready-justification-honesty
plan: 04
subsystem: ui
tags: [react, vite, playwright, node-test, admin, adux-05, gap-closure, tdd]

# Dependency graph
requires:
  - phase: 14-draft-ready-justification-honesty
    provides: "14-03 FE promote UX + exact D-15 Обоснование honesty lock (per-row/batch promote controls)"
provides:
  - "Pure preservePromotedReady(refetchedItems, promotedIds) post-promote refetch reconciliation helper (node --test safe)"
  - "markReady decoupled from fetchShortlist — returns authoritative MarkReadyResult { material_id, status } in mock + live paths"
  - "promoteReady / promoteApprovedDrafts reconcile refetches through preservePromotedReady (no silent draft revert)"
  - "__DIGEST_ADMIN_STALE_READY__ mock harness flag simulating a backend that acks the POST without persisting"
  - "Playwright stale still-draft refetch regression lock"
affects: [14-draft-ready-justification-honesty, 14-05-PLAN, admin-shortlist]

actuals:
  tokens: 3980
  tasks: 2
  commits: 4
plan_head_before: 6c3d5eb09c03e8ba4e5abfb19fe76acf939ebeeb
plan_head_after: b9e7d6aed7ab6f97bd5cdd822b1789021f5a37f1

tech-stack:
  added: []
  patterns:
    - "Authoritative promote response: POST MarkReadyResponse is source of truth; post-POST shortlist refetch is best-effort display reconciliation"
    - "Pure reconciliation seam: state-decision logic lives in a Vite-free pure module, wired in JSX, proven under node --test"

key-files:
  created:
    - web/src/services/adminReadyReconcile.js
  modified:
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx
    - tests/unit/test_admin_mark_ready.js
    - tests/admin.spec.js

key-decisions:
  - "Keep the reconciliation decision in the pure helper preservePromotedReady — JSX only wraps the refetched DTO, never re-implements the rule (G-14-2 missing #2)"
  - "markReady returns MarkReadyResult { material_id, status } and its body contains no fetchShortlist call — promote success no longer depends on a shortlist read (G-14-2 missing #1)"
  - "Prior CR-01 commit 48e94c3 only partially decoupled; this plan completed it to the plan's full acceptance criteria (MarkReadyResult shape, no fetchShortlist token, both handlers reconciled, stale harness)"
  - "A refetched still-draft row is forced to ready for promoted ids only; non-promoted still-draft rows follow the refetch unchanged"

patterns-established:
  - "preservePromotedReady: force promoted material_ids to 'ready' over a refetch, identity-preserving when no change is needed"
  - "Mock staleness harness flag (window.__DIGEST_ADMIN_STALE_READY__, cleared by resetAdminHarness) to exercise backend-does-not-persist classes under mocks"

requirements-completed: [ADUX-05]

coverage:
  - id: D1
    description: "Pure preservePromotedReady helper forces promoted still-draft ids back to ready and leaves all other rows untouched"
    requirement: "ADUX-05"
    verification:
      - kind: unit
        ref: "tests/unit/test_admin_mark_ready.js#preservePromotedReady refetch reconciliation (G-14-2 / ADUX-05)"
        status: pass
    human_judgment: false
  - id: D2
    description: "markReady is decoupled from fetchShortlist and returns an authoritative MarkReadyResult { material_id, status } in mock + live paths"
    requirement: "ADUX-05"
    verification:
      - kind: unit
        ref: "tests/unit/test_admin_mark_ready.js#markReady is decoupled from fetchShortlist and returns a MarkReadyResult"
        status: pass
    human_judgment: false
  - id: D3
    description: "Per-row «Сделать ready» stays ready when the post-POST shortlist refetch still reports draft (silent revert eliminated)"
    requirement: "ADUX-05"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js:306 stale still-draft refetch does not revert a promoted row (G-14-2)"
        status: pass
      - kind: unit
        ref: "tests/unit/test_admin_mark_ready.js#promoteReady and promoteApprovedDrafts reconcile refetch via preservePromotedReady"
        status: pass
    human_judgment: false
  - id: D4
    description: "Batch promote path reconciles its ok ids through preservePromotedReady; existing per-row + batch ready tests stay green"
    requirement: "ADUX-05"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js:339 batch Сделать ready одобренные черновики issues one markReadyBatch (ADUX-05)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js:274 per-row Сделать ready promotes draft and clears draft hint (ADUX-05)"
        status: pass
    human_judgment: false

duration: 40min
completed: 2026-10-03
status: complete
---

# Phase 14 Plan 04: G-14-2 decouple promote from refetch, kill silent revert (ADUX-05) Summary

**Per-row and batch «Сделать ready» now treat the POST response as authoritative — a still-draft shortlist refetch is reconciled by a pure `preservePromotedReady` helper and can no longer silently revert a promoted row.**

## Performance

- **Duration:** 40min
- **Started:** 2026-10-03T16:05:00Z
- **Completed:** 2026-10-03T16:45:00Z
- **Tasks:** 2
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments
- Added the pure, Vite-free `preservePromotedReady(refetchedItems, promotedIds)` reconciliation helper with node `--test` behavior proofs.
- Decoupled `markReady` from `fetchShortlist`: it returns `MarkReadyResult { material_id, status }` in both mock and live paths, so promote success is the authoritative POST result (G-14-2 missing #1).
- Wired `promoteReady` (single id) and `promoteApprovedDrafts` (ok ids) refetches through `preservePromotedReady`, so a still-draft refetch never clobbers a confirmed promote (G-14-2 missing #2).
- Added the `__DIGEST_ADMIN_STALE_READY__` mock harness flag (cleared by `resetAdminHarness`) and a Playwright regression lock reproducing the silent-revert class under mocks.

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: Pure preservePromotedReady reconciliation helper**
   - `8d65e32` (test) — add failing preservePromotedReady reconcile tests (G-14-2)
   - `c828129` (feat) — add pure preservePromotedReady reconciliation helper
2. **Task 2: Decouple markReady + reconcile promote handlers + Playwright stale-refetch proof**
   - `93cea53` (test) — add failing decouple + stale-refetch proofs (G-14-2)
   - `b9e7d6a` (feat) — decouple markReady and reconcile promote refetch (G-14-2)

**Plan metadata:** `0bc2249` (docs: complete summary), `8c168fd` (docs: ROADMAP plan progress 4/5)

_Note: TDD tasks commit RED and GREEN separately, so a single plan task may span two commits._

## Files Created/Modified
- `web/src/services/adminReadyReconcile.js` (created) — pure `preservePromotedReady` helper; no Vite/supabase/import.meta, safe under `node --test`.
- `web/src/services/adminApi.js` — `markReady` returns `MarkReadyResult { material_id, status }` in mock + live paths, decoupled from `fetchShortlist`; added `__DIGEST_ADMIN_STALE_READY__` handling and cleared it in `resetAdminHarness`.
- `web/src/pages/AdminDigestPage.jsx` — imports `preservePromotedReady`; `promoteReady` and `promoteApprovedDrafts` reconcile refetched items before `applyBatch`.
- `tests/unit/test_admin_mark_ready.js` — `preservePromotedReady` behavior suite; rewritten G-14-2 source-shape suite (no `fetchShortlist` token in `markReady`, both handlers reference the helper).
- `tests/admin.spec.js` — `stale still-draft refetch does not revert a promoted row (G-14-2)` E2E test using the stale harness flag.

## Decisions Made
- Keep the reconciliation rule inside the pure `preservePromotedReady` helper; JSX only wraps the refetched DTO (`{ ...refreshed, items: preservePromotedReady(...) }`) — the decision never leaks into the component.
- The refetch forces `ready` for promoted ids only; non-promoted still-draft rows correctly follow the refetch.
- Completed the partially-applied prior CR-01 fix (`48e94c3`) to the plan's full acceptance criteria rather than assuming it sufficed.

## Deviations from Plan

None - plan executed exactly as written. TDD RED was observed for both tasks before GREEN (Task 1: `ERR_MODULE_NOT_FOUND` before the helper existed; Task 2: unit source-shape + Playwright stale assertions failed before implementation).

## Issues Encountered
- A prior code-review commit `48e94c3 fix(14): CR-01 decouple markReady success from shortlist refetch` had partially decoupled `markReady`. It did not satisfy the plan's acceptance criteria (no `MarkReadyResult` return shape, no `preservePromotedReady` wiring, no stale harness), so Task 2 RED was authored to fail against the pre-existing state and GREEN completed the decoupling. No files were reverted.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- G-14-2 is closed: per-row and batch promote are authoritative and non-reverting, regression-locked at both unit and E2E layers.
- Ready for `14-05-PLAN` (G-14-2a/2b: disambiguate status axes + dedupe footer) as the next gap-closure wave.
- Optional non-CI live check remains: `POST /admin/materials/{id}/ready` with an admin JWT should return `200 {material_id, status:"ready"}`.

---
*Phase: 14-draft-ready-justification-honesty*
*Completed: 2026-10-03*

## Self-Check: PASSED

- FOUND: `.planning/phases/14-draft-ready-justification-honesty/14-04-SUMMARY.md`
- FOUND: `8d65e32`, `c828129`, `93cea53`, `b9e7d6a` (task commits)
- FOUND: `0bc2249` (summary), `8c168fd` (roadmap)
- `node --test tests/unit/test_admin_mark_ready.js` — 10 pass / 0 fail
- `npm run test:web -- tests/admin.spec.js -g "stale|Сделать ready|draft hint|mark-ready"` — 35 passed / 0 failed
