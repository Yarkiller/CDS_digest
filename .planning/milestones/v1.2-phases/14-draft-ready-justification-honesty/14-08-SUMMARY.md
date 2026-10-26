---
phase: 14-draft-ready-justification-honesty
plan: 08
subsystem: ui
tags: [react, admin, tailwind, gap-closure, adux-05, cursor]

# Dependency graph
requires:
  - phase: 14-draft-ready-justification-honesty
    provides: "14-07 per-row promote controls + D-85 gate; audited admin interactive surfaces"
provides:
  - "Global base rule button:not(:disabled) { cursor: pointer } in web/src/index.css"
  - "Computed-cursor Playwright lock for «Превью материала», per-row admin-mark-ready, and «Выбрать все»"
  - "Disabled-button guard: the disabled «Отправить дайджест →» does not compute cursor: pointer"
affects: [14-draft-ready-justification-honesty, admin-shortlist, web-styles]

actuals:
  tokens: 3120
  tasks: 1
  commits: 2
plan_head_before: 87b18a4
plan_head_after: ca67e66

tech-stack:
  added: []
  patterns:
    - "One global `@layer base` cursor rule instead of ~a dozen per-button `cursor-pointer` classes; Tailwind utilities still override on disabled controls"
    - "Computed-cursor Playwright assertion (`toHaveCSS('cursor', 'pointer')`) as the affordance regression lock, plus a `not.toHaveCSS` guard for the disabled path"

key-files:
  created: []
  modified:
    - web/src/index.css
    - tests/admin.spec.js

key-decisions:
  - "Fix at the base layer, not per element: Tailwind v4 dropped the native button pointer cursor and ~a dozen Phase 14 controls lacked an explicit class — one rule closes the gap and prevents recurrence on future buttons"
  - "Scope the rule with `:not(:disabled)` so `disabled:cursor-not-allowed` / the native default still win on disabled controls"

patterns-established:
  - "Affordance regressions are locked by computed CSS assertions on the audited controls, with a negative assertion for the disabled state"

requirements-completed: [ADUX-05]

coverage:
  - id: D1
    description: "All audited enabled admin controls (shortlist «Превью материала», per-row «Сделать ready», toolbar «Выбрать все») compute cursor: pointer (G-14-3)"
    requirement: "ADUX-05"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#interactive admin controls show a pointer cursor (G-14-3)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Disabled controls are excluded from the pointer rule — the disabled «Отправить дайджест →» does not compute cursor: pointer"
    requirement: "ADUX-05"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#interactive admin controls show a pointer cursor (G-14-3)"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-03
status: complete
---

# Phase 14 Plan 08: Pointer cursor on interactive admin controls (G-14-3) Summary

**A single global `@layer base` rule `button:not(:disabled) { cursor: pointer }` restores the pointer affordance across the admin surface — the shortlist «Превью материала» button, the per-row «Сделать ready», and the toolbar «Выбрать все» now compute `cursor: pointer`, while the disabled Send button stays non-pointer; the behavior is locked by a computed-cursor Playwright assertion.**

## Performance

- **Duration:** 5min
- **Started:** 2026-10-03T21:35:00Z
- **Completed:** 2026-10-03T21:40:00Z
- **Tasks:** 1
- **Files modified:** 2 (0 created, 2 modified)

## Accomplishments
- Added a `@layer base { button:not(:disabled) { cursor: pointer } }` rule to `web/src/index.css` (after the `@theme` and `@layer utilities` blocks), fixing every enabled native `<button>` in one place without per-element churn.
- Added the «interactive admin controls show a pointer cursor (G-14-3)» Playwright test asserting computed `cursor: pointer` for the shortlist «Превью материала» button, the draft row's `admin-mark-ready` button, and the toolbar «Выбрать все» button.
- Guarded the `:not(:disabled)` clause: the disabled «Отправить дайджест →» button is asserted `toBeDisabled()` and `not.toHaveCSS('cursor', 'pointer')`.
- No `AdminDigestPage.jsx` markup change and no per-button `cursor-pointer` classes added.

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: Global button pointer cursor + computed-cursor Playwright lock**
   - `209c2a8` (test) — lock pointer cursor on admin controls (G-14-3)
   - `ca67e66` (fix) — restore pointer cursor on native buttons (G-14-3)

**Plan metadata:** pending (this SUMMARY + tracking commit)

_Note: RED was observed before GREEN — `toHaveCSS('cursor', 'pointer')` failed with `Received: "default"` on the «Превью материала» button._

## Files Created/Modified
- `web/src/index.css` — new `@layer base` rule restoring the native-button pointer cursor, scoped with `:not(:disabled)`; comment cites G-14-3 / ADUX-05.
- `tests/admin.spec.js` — new `interactive admin controls show a pointer cursor (G-14-3)` test covering the three audited enabled controls and the disabled-button guard.

## Decisions Made
- **Global base rule over per-button classes:** Tailwind v4 no longer applies `cursor: pointer` to `<button>`, and ~a dozen Phase 14 controls (per-row promote, toolbar, preview modal, footer) lacked an explicit class. One base rule closes all of them and prevents recurrence; the two pre-existing explicit `cursor-pointer` classes remain harmless.
- **`:not(:disabled)` scope:** keeps `disabled:cursor-not-allowed` / the native default winning on disabled controls, so the affordance stays honest.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `npm run test:web -- tests/admin.spec.js -g "pointer cursor"` let npm swallow the `-g`, so Playwright ran the whole file (`pointer cursor` was treated as a positional arg). Used `npx playwright test --project=web tests/admin.spec.js --grep "pointer cursor"` for the targeted RED/GREEN run; the full admin suite was run separately for regression.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- G-14-3 closed: interactive admin controls show a pointer cursor; the rule is global and regression-locked, disabled controls unaffected.
- All three Phase 14 gap-closure plans (14-06, 14-07, 14-08) are now complete — the phase is ready for post-execution verification.

---
*Phase: 14-draft-ready-justification-honesty*
*Completed: 2026-10-03*

## Self-Check: PASSED

- FOUND: `.planning/phases/14-draft-ready-justification-honesty/14-08-SUMMARY.md`
- FOUND: `web/src/index.css`, `tests/admin.spec.js`
- FOUND: `209c2a8`, `ca67e66` (TDD RED/GREEN task commits)
- `npx playwright test --project=web tests/admin.spec.js --grep "pointer cursor"` — 1 passed / 0 failed
- `npm run test:web -- tests/admin.spec.js` (full admin suite) — 36 passed / 0 failed
