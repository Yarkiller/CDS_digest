---
phase: 14-draft-ready-justification-honesty
plan: 07
subsystem: ui
tags: [react, admin, gap-closure, adux-05, d85, operator-override]

# Dependency graph
requires:
  - phase: 14-draft-ready-justification-honesty
    provides: "14-03 per-row promote UX + batch CTA; 14-05 deduped footer + quantified batch CTA"
provides:
  - "Batch promote affordance removed from the admin footer (admin-mark-ready-batch + promoteApprovedDrafts + markReadyBatch import gone)"
  - "Coherent sendHint branch order with a neutral «Отправка недоступна.» lock when an approved draft exists"
  - "Per-row «Сделать ready» and the D-85 send gate (sendUnlocked requires approvedDrafts.length === 0) retained unchanged"
affects: [14-draft-ready-justification-honesty, admin-shortlist]

actuals:
  tokens: 2636
  tasks: 1
  commits: 2
plan_head_before: 1a0b6ef5907d00546282d6d0e4dd9d9bb5ba12be
plan_head_after: c84f6b6f0d66014df72848ff4708a588d677de53

tech-stack:
  added: []
  patterns:
    - "Operator override removes only the UI entry point; the retained backend batch contract (POST /admin/materials/ready + mark_materials_ready + FE markReadyBatch client/mock) stays covered but unhooked"
    - "Source-shape node assertion locks a removed-control invariant (no import / no handler / no testid) alongside the Playwright DOM proof"

key-files:
  created: []
  modified:
    - web/src/pages/AdminDigestPage.jsx
    - tests/admin.spec.js
    - tests/unit/test_admin_mark_ready.js

key-decisions:
  - "Delete the UI control + handler + import; retain the D-08 backend route, use-case, FE markReadyBatch client/mock and harness counter (no UI caller) — deleting them would violate a locked decision and reduce coverage"
  - "Reordered sendHint so the removed copy is gone and the approved-draft state reads a neutral «Отправка недоступна.» — keep sendUnlocked's D-85 requirement unchanged so Send stays disabled"
  - "Left promoteReady, applyBatch, preservePromotedReady and the per-row admin-mark-ready path untouched"

patterns-established:
  - "sendHint branch order: already-sent → no approved-ready → approved-draft lock → preview-locked → send-ready"

requirements-completed: [ADUX-05]

coverage:
  - id: D1
    description: "The sticky footer offers no batch promote control in any state (admin-mark-ready-batch absent), and the «Уберите черновики…» copy renders nowhere (G-14-2)"
    requirement: "ADUX-05"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#no batch promote CTA is rendered (G-14-2)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#approved draft blocks send with draft hint (ADMIN-03/07, D-85)"
        status: pass
      - kind: unit
        ref: "tests/unit/test_admin_mark_ready.js#promoteReady reconciles the refetch via preservePromotedReady; batch CTA is gone"
        status: pass
    human_judgment: false
  - id: D2
    description: "Per-row «Сделать ready» and the D-85 send gate are unchanged; sendHint falls through coherently when approvedDrafts.length > 0"
    requirement: "ADUX-05"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#per-row Сделать ready promotes draft and clears draft hint (ADUX-05)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#stale still-draft refetch does not revert a promoted row (G-14-2)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#Approve does not auto-ready draft (D-02)"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-03
status: complete
---

# Phase 14 Plan 07: Remove the batch promote control + approved-drafts hint (G-14-2) Summary

**The admin footer no longer advertises or performs a batch promote — the «Сделать ready все одобренные черновики (N)» CTA, its `promoteApprovedDrafts` handler/import, and the «Уберите черновики из одобренных или дождитесь ready.» copy are gone; the per-row «Сделать ready» and the D-85 send gate stay intact, and `sendHint` now reads a neutral «Отправка недоступна.» while an approved draft blocks send.**

## Performance

- **Duration:** 5min
- **Started:** 2026-10-03T18:30:00Z
- **Completed:** 2026-10-03T18:35:00Z
- **Tasks:** 1
- **Files modified:** 3 (0 created, 3 modified)

## Accomplishments
- Deleted the `admin-mark-ready-batch` button block, the `promoteApprovedDrafts` handler, and the `markReadyBatch` import from `AdminDigestPage.jsx` (display + behavior).
- Rewrote `sendHint` to a coherent branch order that renders the removed copy in no state: already-sent → `Нет одобренных ready-материалов для отправки.` → `Отправка недоступна.` (approved draft present) → `Сначала откройте превью письма.` → `Превью просмотрено. Можно отправить.`
- Kept `sendUnlocked` unchanged (`approvedDrafts.length === 0` required), so Send stays disabled while an approved draft exists (D-85); kept the per-row `admin-mark-ready` path (`promoteReady`) untouched.
- Retained but unhooked the D-08 backend batch contract (`POST /admin/materials/ready`, `mark_materials_ready`, FE `markReadyBatch` client/mock + harness counter) — still covered by HTTP/node tests.
- Updated Playwright + node tests: removed the contradicting batch-call assertions, added a «no batch promote CTA is rendered (G-14-2)» regression and a source-shape lock (no `markReadyBatch` import, no `promoteApprovedDrafts`, no `admin-mark-ready-batch` testid).

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: Remove batch promote CTA + approved-drafts hint; lock the coherent footer**
   - `d2720d3` (test) — replace batch CTA asserts with batch-removal lock (G-14-2)
   - `c84f6b6` (feat) — remove batch CTA + approved-drafts hint; reorder sendHint (G-14-2)

**Plan metadata:** pending (this SUMMARY + tracking commit)

_Note: RED was observed before GREEN — node: 1 failed; Playwright filter: 2 failed / 33 passed (the removed-copy hint assert and the batch-testid count)._

## Files Created/Modified
- `web/src/pages/AdminDigestPage.jsx` — removed `markReadyBatch` import, the `promoteApprovedDrafts` function, and the footer batch button; reordered `sendHint`. `sendUnlocked`, `promoteReady`, `applyBatch`, `preservePromotedReady`, and the per-row control unchanged.
- `tests/admin.spec.js` — retargeted the draft-hint asserts to the neutral/transition hints, added `admin-mark-ready-batch` count-0 asserts, deleted the `batch Сделать ready … issues one markReadyBatch` test, added `no batch promote CTA is rendered (G-14-2)`.
- `tests/unit/test_admin_mark_ready.js` — renamed the reconcile describe, dropped the `promoteApprovedDrafts` branch assertion, added the batch-removal source-shape lock. `adminApi markReady / markReadyBatch exports` retained and green.

## Decisions Made
- Unhook (not delete) the FE/backend batch plumbing: D-08 is a locked Phase 14 decision and the backend path is HTTP-covered; deleting it would cascade into `main.jsx` + three test files for no product gain. The operator's request is about the admin UI control.
- `sendHint` reordering: put the `approvedReady.length === 0` branch before the `approvedDrafts.length > 0` branch so the draft-only case reads the honest "nothing ready to send" message, and the mixed case reads the neutral lock.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- G-14-2 closed: the footer no longer offers or hints at batch promote; the per-row promote and D-85 gate are intact and regression-locked.
- Wave 2 (plan 14-08, G-14-3 pointer cursor) is unblocked (`depends_on: [14-07]`).

---
*Phase: 14-draft-ready-justification-honesty*
*Completed: 2026-10-03*

## Self-Check: PASSED

- FOUND: `.planning/phases/14-draft-ready-justification-honesty/14-07-SUMMARY.md`
- FOUND: `web/src/pages/AdminDigestPage.jsx`, `tests/admin.spec.js`, `tests/unit/test_admin_mark_ready.js`
- FOUND: `d2720d3`, `c84f6b6` (TDD RED/GREEN task commits)
- `node --test tests/unit/test_admin_mark_ready.js` — 10 passed / 0 failed
- `npm run test:web -- tests/admin.spec.js` (full admin suite) — 35 passed / 0 failed
