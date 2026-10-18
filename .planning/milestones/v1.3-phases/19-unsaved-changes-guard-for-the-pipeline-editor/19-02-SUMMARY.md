---
phase: 19-unsaved-changes-guard-for-the-pipeline-editor
plan: 02
subsystem: ui
tags: [useBlocker, beforeunload, unsaved-changes, playwright, node-test, ADUX-09]

requires:
  - phase: 19-unsaved-changes-guard-for-the-pipeline-editor
    provides: module-scope createBrowserRouter + RouterProvider (Plan 19-01)
provides:
  - reusable unsaved-changes util + hook + dialog trio
  - in-app SPA leave modal with locked Russian copy
  - correct dirty-scoped beforeunload arming (no confirm/alert)
  - amended tripwire + SPA/save/reject Playwright journeys
affects:
  - Phase 23 ADUX-10 ingest-sources editor (reuses the same guard)

actuals:
  tokens: 4196
  tasks: 3
  commits: 5

plan_head_before: aa8c762494c298d6f9e46538735e1d92e4f37044
plan_head_after: 7dfb49df0a2b9ecbd8d90c161da799cda7c1c863

tech-stack:
  added: []
  patterns:
    - boolean useBlocker(dirty) + UnsavedChangesDialog (proceed/reset)
    - armBeforeUnload two-statement contract registered only while dirty
    - Vite-free util importable by node --test

key-files:
  created:
    - web/src/utils/unsavedChangesGuard.js
    - web/src/hooks/useUnsavedChangesGuard.js
    - web/src/components/UnsavedChangesDialog.jsx
    - tests/unit/test_unsaved_changes_guard.js
  modified:
    - web/src/pages/AdminPipelineConfigPage.jsx
    - tests/admin.spec.js

key-decisions:
  - "D-01/D-02/D-03: custom modal with Stay/Leave + Esc=stay; no Save-and-exit"
  - "D-04: boolean useBlocker(dirty) — every SPA nav blocked, no pathname carve-out"
  - "D-05/D-06: armBeforeUnload = preventDefault + truthy returnValue; browser-owned prompt text"
  - "D-07: util/hook/dialog trio with one home for UNSAVED_LEAVE_CONFIRM"
  - "D-08: RESET_CONFIRM window.confirm path untouched"
  - "D-10: tripwire amended (not deleted) to registry + real beforeunload type()"
  - "D-12: guard consumes existing dirty = yaml !== savedYaml"

patterns-established:
  - "useUnsavedChangesGuard(dirty) above early returns; dialog open={blocker.state==='blocked'}"
  - "beforeunload spy filters Vite HMR willUnload noise; assert only app arming handlers"

requirements-completed: [ADUX-09]

coverage:
  - id: D1
    description: "Dirty editor blocks in-app shell nav; modal shows locked copy; Stay/Escape keep draft"
    requirement: ADUX-09
    verification:
      - kind: automated_ui
        ref: "npx playwright test --project=web tests/admin.spec.js -g \"blocks in-app nav\""
        status: pass
    human_judgment: false
  - id: D2
    description: "Leave navigates once to /archive with no native dialog on the SPA path"
    requirement: ADUX-09
    verification:
      - kind: automated_ui
        ref: "npx playwright test --project=web tests/admin.spec.js -g \"navigates once\""
        status: pass
    human_judgment: false
  - id: D3
    description: "armBeforeUnload body contract + dirty-scoped registry; real beforeunload dialog.type()"
    requirement: ADUX-09
    verification:
      - kind: unit
        ref: "node --test tests/unit/test_unsaved_changes_guard.js"
        status: pass
      - kind: automated_ui
        ref: "npx playwright test --project=web tests/admin.spec.js -g \"unsaved-leave guard\""
        status: pass
    human_judgment: false
  - id: D4
    description: "Reject keeps guard armed; successful save disarms; no double prompt"
    requirement: ADUX-09
    verification:
      - kind: automated_ui
        ref: "npx playwright test --project=web tests/admin.spec.js -g \"save disarms\""
        status: pass
    human_judgment: false

duration: 22min
completed: 2026-10-16
status: complete
---

# Phase 19 Plan 02: Unsaved-changes guard Summary

**Shipped the ADUX-09 leave guard as a reusable util/hook/dialog trio: boolean `useBlocker(dirty)` drives an in-app modal with the locked Russian copy, and a two-statement `armBeforeUnload` arms the browser prompt only while dirty — full Playwright `web` suite 113 passed (110 Wave-0 + 3 new).**

## Performance

- **Duration:** 22 min
- **Started:** 2026-10-16T06:43:00Z
- **Completed:** 2026-10-16T07:05:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- In-app SPA leave: shell «Архив» while dirty opens `UnsavedChangesDialog`; «Остаться»/Escape keep the draft; «Уйти без сохранения» navigates once with no native dialog.
- Reload/close backstop: `armBeforeUnload` is exactly `preventDefault()` + `returnValue = true`, registered only while dirty, removed after save; page-local `window.confirm`-in-unload deleted.
- Dirty contract pinned: reject keeps the modal armed; successful save lets navigation proceed; reset `window.confirm` tests unchanged.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: SPA leave journeys** - `6c64dbe` (test)
2. **Task 1 GREEN: util/hook/dialog + page wire** - `0d40578` (feat)
3. **Task 2 RED: unit gate + amended tripwire** - `61b5889` (test)
4. **Task 2 GREEN: armBeforeUnload + dirty effect** - `b0fe019` (feat)
5. **Task 3: save/reject regression pin** - `7dfb49d` (test)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks produced RED then GREEN commits._

## Files Created/Modified

- `web/src/utils/unsavedChangesGuard.js` — `UNSAVED_LEAVE_CONFIRM` + `armBeforeUnload`
- `web/src/hooks/useUnsavedChangesGuard.js` — `useBlocker(dirty)` + `[dirty]` beforeunload effect
- `web/src/components/UnsavedChangesDialog.jsx` — D-02 modal; Esc → stay
- `web/src/pages/AdminPipelineConfigPage.jsx` — hook above early returns; dialog; removed broken unload effect
- `tests/unit/test_unsaved_changes_guard.js` — node --test body contract
- `tests/admin.spec.js` — amended tripwire + SPA/save journeys

## Decisions Made

Followed CONTEXT/RESEARCH: boolean blocker (D-04), custom modal (D-01–D-03), two-statement unload (D-05/D-06), extractable packaging (D-07), reset path preserved (D-08), tripwire amended (D-10), consume existing `dirty` (D-12).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tripwire listener count vs Vite HMR noise**
- **Found during:** Task 2 RED
- **Issue:** Registry saw 2 `beforeunload` listeners while dirty (Vite `willUnload` stub + app handler); raw `toHaveLength(1)` would stay red after a correct app handler.
- **Fix:** Assert only app-owned sources (`preventDefault` / `returnValue` / `confirm` / `alert`); ignore HMR stub.
- **Files modified:** `tests/admin.spec.js`
- **Commit:** `b0fe019` (with GREEN)

**2. [Rule 1 - Bug] Dismiss-during-reload leaves empty URL; `page.close({ runBeforeUnload })` silent**
- **Found during:** Task 2 GREEN
- **Issue:** After a real `beforeunload` dialog, dismiss+reload left `page.url() === ""`; `page.close({ runBeforeUnload: true })` produced no dialog in this Chromium. RESEARCH A2 fallback path.
- **Fix:** Prove real prompt last via `reload` + `dialog.accept()`, asserting only `dialog.type() === 'beforeunload'` (never message text). Registry + save-clear remain the sequential contract.
- **Files modified:** `tests/admin.spec.js`
- **Commit:** `b0fe019`

## TDD Gate Compliance

| Task | RED evidence | GREEN verify |
|------|--------------|--------------|
| 1 (tracer) | Dialog visibility failed — shell click navigated with no modal | `-g "blocks in-app nav\|navigates once\|reset confirm"` → 4 passed |
| 2 | `armBeforeUnload` undefined; tripwire `confirm` in handler source | `node --test` 3/3; `-g "unsaved-leave guard"` → 1 passed |
| 3 | N/A (regression pin — expected green first run) | `-g "save disarms"` → 1 passed; full `admin.spec.js` 60 passed |

## Verification

```text
node --test tests/unit/test_unsaved_changes_guard.js   # 3 passed
npx playwright test --project=web tests/admin.spec.js  # 60 passed
npx playwright test --project=web                      # 113 passed (110 Wave-0 + 3)
```

## Known Stubs

None.

## Threat Flags

None beyond plan register T-19-04…T-19-07 (mitigated as designed; T-19-07 accepted gap for RequireAuth redirect under mocks).

## Self-Check: PASSED

- FOUND: `web/src/utils/unsavedChangesGuard.js`
- FOUND: `web/src/hooks/useUnsavedChangesGuard.js`
- FOUND: `web/src/components/UnsavedChangesDialog.jsx`
- FOUND: `tests/unit/test_unsaved_changes_guard.js`
- FOUND: `6c64dbe`, `0d40578`, `61b5889`, `b0fe019`, `7dfb49d`
