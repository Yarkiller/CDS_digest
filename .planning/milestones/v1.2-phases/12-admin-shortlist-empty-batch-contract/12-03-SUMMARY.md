---
phase: 12-admin-shortlist-empty-batch-contract
plan: 03
subsystem: testing
tags: [playwright, admin-mock, empty-unsent, tdd, fix-01]

requires:
  - phase: 12-admin-shortlist-empty-batch-contract
    provides: HTTP empty-unsent proofs + 12-FIX-01-LOCK.md (plans 01–02)
provides:
  - "emptyUnsentDto + __DIGEST_ADMIN_EMPTY_UNSENT__ mock harness (D-12/D-13)"
  - "Playwright empty-unsent path locked to D-80 empty UI (not digest_rest)"
affects:
  - phase-12-verify
  - FIX-01 FE/E2E surface

actuals:
  tokens: 686
  tasks: 2
  commits: 2

plan_head_before: 81ecad1adefa11e6f66ed5cc7e045ca7cc9df6a4
plan_head_after: 57e3ca96f24ea94f37aeae4d2118b86f217920c0

tech-stack:
  added: []
  patterns:
    - "Sticky flag precedence DIGEST_REST → EMPTY_UNSENT → EMPTY in adminApi mock fetchShortlist"
    - "emptyUnsentDto ISO week_label parity with HTTP D-04 #2"

key-files:
  created: []
  modified:
    - web/src/services/adminApi.js
    - tests/admin.spec.js

key-decisions:
  - "D-13: no AdminDigestPage chrome — weekDek stays gated by showTriage; empty-unsent reuses D-80 empty UI"
  - "Playwright is the behavioral RED for emptyUnsentDto harness (no separate node:test for sticky window mocks)"

patterns-established:
  - "__DIGEST_ADMIN_EMPTY_UNSENT__ sticky flag cleared in resetAdminHarness (T-12-06)"
  - "Empty-unsent E2E mirrors no-batch empty asserts; mutual exclusivity with DIGEST_REST/EMPTY"

requirements-completed: [FIX-01]

coverage:
  - id: D1
    description: "Mock harness returns empty-unsent DTO (batch_id 7, ISO week_label, items=[], digest_rest false) via EMPTY_UNSENT flag"
    requirement: FIX-01
    verification:
      - kind: other
        ref: "rg -n emptyUnsentDto|__DIGEST_ADMIN_EMPTY_UNSENT__ web/src/services/adminApi.js"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#empty-unsent shortlist shows Кандидатов пока нет without пайплайн (EMPTY_UNSENT)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Playwright empty-unsent shows D-80 empty UI and zero admin-digest-rest"
    requirement: FIX-01
    verification:
      - kind: automated_ui
        ref: "npx playwright test --project=web tests/admin.spec.js --grep EMPTY_UNSENT"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-10-02
status: complete
---

# Phase 12 Plan 03: FE mock harness + Playwright empty-unsent Summary

**Wired `emptyUnsentDto` + `__DIGEST_ADMIN_EMPTY_UNSENT__` sticky harness and locked Playwright empty-unsent to D-80 empty UI (not digest_rest).**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-02T16:18:47Z
- **Completed:** 2026-10-02T16:24:43Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- Added `emptyUnsentDto()` matching D-04 #2 / D-12 / D-13 (`batch_id: 7`, `week_label: '2026-10-06'`, empty items, `digest_rest: false`).
- Wired sticky `__DIGEST_ADMIN_EMPTY_UNSENT__` after DIGEST_REST and before EMPTY; cleared in `resetAdminHarness` (T-12-06).
- Playwright empty-unsent case green: Кандидатов пока нет + Обновить, zero пайплайн/rows/digest_rest; no new empty chrome (D-13).

## Task Commits

1. **Task 2 RED / shared RED: Playwright empty-unsent** - `82c2633` (test)
2. **Task 1 GREEN: emptyUnsentDto + EMPTY_UNSENT harness** - `57e3ca9` (feat)

**Plan metadata:** (this commit)

_Note: TDD RED (Playwright) preceded harness GREEN; AdminDigestPage untouched._

## TDD Cycle

### RED
- **Evidence:** `npx playwright test --project=web tests/admin.spec.js --grep EMPTY_UNSENT` → exit 1; heading Кандидатов пока нет not found (flag ignored → populated mock).
- **Record:** `.planning/tmp/12-03-task1-red-evidence.json` → `tdd-red-evidence` → `RED_EVIDENCE_OK`.
- **Commit:** `82c2633`

### GREEN
- Implemented `emptyUnsentDto` + sticky branch + reset clear in `adminApi.js`.
- Playwright EMPTY_UNSENT → 1 passed (5.9s).
- **Commit:** `57e3ca9`

### REFACTOR
- None — minimal GREEN sufficient.

## Files Created/Modified

- `web/src/services/adminApi.js` — `emptyUnsentDto`, EMPTY_UNSENT branch + reset clear
- `tests/admin.spec.js` — empty-unsent Playwright mirroring no-batch empty asserts

## Decisions Made

- No `AdminDigestPage.jsx` edits (D-03/D-13): empty-unsent already maps to existing empty UI when `items=[]` and `digest_rest=false`.
- Used Playwright as the intentional RED for the harness (window sticky flags are E2E-native).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None for 12-03 scope. Pre-existing unrelated Playwright flake (`/me network failure shows ServiceUnavailable`) observed when the whole `admin.spec.js` ran without `--grep` — out of scope per D-02; not introduced by this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 12 plans 01–03 complete on disk once this SUMMARY lands — ready for `/gsd-verify-work` / phase close.
- FIX-01 FE/E2E surface closed alongside HTTP lock from 12-01/12-02.

## TDD Gate Compliance

- RED commit: `test(12-03): …` (`82c2633`) present
- GREEN commit: `feat(12-03): …` (`57e3ca9`) present
- RED evidence: `RED_EVIDENCE_OK` (target_test_failed)

## Self-Check: PASSED

- `web/src/services/adminApi.js` FOUND (emptyUnsentDto + EMPTY_UNSENT ×3)
- `tests/admin.spec.js` FOUND (EMPTY_UNSENT case)
- Commits `82c2633` / `57e3ca9` FOUND on branch
- Playwright EMPTY_UNSENT: 1 passed
- HTTP units no-batch + empty-unsent: 2 passed

---
*Phase: 12-admin-shortlist-empty-batch-contract*
*Completed: 2026-10-02*
