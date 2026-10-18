---
phase: 14-draft-ready-justification-honesty
plan: 03
subsystem: ui
tags: [adux-05, adux-06, mark-ready, admin-digest, playwright, tdd, honesty]

requires:
  - phase: 14-draft-ready-justification-honesty
    provides: POST /admin/materials/{id}/ready + POST /admin/materials/ready batch (14-01/14-02)
provides:
  - Pure adminReadyMock helpers (applyMockMarkReady / batch / getMockDefaultItems)
  - adminApi.markReady + markReadyBatch (mock + live; batch never calls markReady)
  - AdminDigestPage per-row + batch Сделать ready UX with optimistic ready
  - Exact D-15 empty Обоснование copy + named honest_factor_labels matrix
affects:
  - Phase 14 UAT / verify-work
  - Admin digest send gate (D-85 unblock without SQL)

actuals:
  tokens: 28555
  tasks: 3
  commits: 6

plan_head_before: e567375dd5a92e3f1455b981329d652f71221668
plan_head_after: 691285c9d662ce0b518659a9cb198ca4329696c0

tech-stack:
  added: []
  patterns:
    - "Pure mock helpers in adminReadyMock.js (node --test; no Vite/import.meta)"
    - "Optimistic draft→ready + silent fetchShortlist; batch one markReadyBatch call"

key-files:
  created:
    - web/src/services/adminReadyMock.js
    - tests/unit/test_admin_mark_ready.js
    - .planning/phases/14-draft-ready-justification-honesty/14-03-task1-red-evidence.json
    - .planning/phases/14-draft-ready-justification-honesty/14-03-task2-red-evidence.json
    - .planning/phases/14-draft-ready-justification-honesty/14-03-task3-red-evidence.json
  modified:
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx
    - web/src/main.jsx
    - tests/admin.spec.js
    - tests/unit/test_score_factors.py

key-decisions:
  - "Mock DEFAULT_ITEMS seed owned by getMockDefaultItems (material 104 empty factor_labels)"
  - "Batch mock call counter exposed on __DIGEST_ADMIN_HARNESS__ for D-08 Playwright proof"
  - "Empty Обоснование is exact D-15 sentence; populated join unchanged (D-13/D-14)"

patterns-established:
  - "Pattern: markReady / markReadyBatch mirror setDecision auth + AdminApiError; mocks via pure helpers"
  - "Pattern: per-row promote next to draft badge; batch CTA in send footer when approvedDrafts.length > 0"

requirements-completed: [ADUX-05, ADUX-06]

coverage:
  - id: D1
    description: Per-row Сделать ready next to draft badge; empty-body soft-warn; optimistic ready clears D-85
    requirement: ADUX-05
    verification:
      - kind: e2e
        ref: tests/admin.spec.js#per-row Сделать ready promotes draft and clears draft hint (ADUX-05)
        status: pass
    human_judgment: false
  - id: D2
    description: Batch CTA confirm with count N issues exactly one markReadyBatch
    requirement: ADUX-05
    verification:
      - kind: e2e
        ref: tests/admin.spec.js#batch Сделать ready одобренные черновики issues one markReadyBatch (ADUX-05)
        status: pass
      - kind: unit
        ref: tests/unit/test_admin_mark_ready.js#returns order-preserving partial results in a single call (D-08)
        status: pass
    human_judgment: false
  - id: D3
    description: Approve does not auto-ready draft (D-02)
    requirement: ADUX-05
    verification:
      - kind: e2e
        ref: tests/admin.spec.js#Approve does not auto-ready draft (D-02)
        status: pass
    human_judgment: false
  - id: D4
    description: Exact D-15 empty Обоснование copy on shortlist; named honesty matrix 0/1/2+/whitespace
    requirement: ADUX-06
    verification:
      - kind: e2e
        ref: tests/admin.spec.js#populated shortlist shows ≤5 rows with badges and score factors
        status: pass
      - kind: unit
        ref: tests/unit/test_score_factors.py#test_honest_factor_labels_zero_factors_returns_empty
        status: pass
    human_judgment: false

duration: 16min
completed: 2026-10-03
status: complete
---

# Phase 14 Plan 03: FE promote UX + justification honesty Summary

**Admin can promote draft→ready in the SPA (per-row + approved-drafts batch) against Plan 01/02 APIs, and empty shortlist «Обоснование» shows the exact D-15 honesty sentence.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-03T12:55:40Z
- **Completed:** 2026-10-03T13:11:30Z
- **Tasks:** 3
- **Files modified:** 7 production/test sources (+ 3 red-evidence JSON)

## Accomplishments

- Pure `adminReadyMock` + `markReady` / `markReadyBatch` FE service boundary (D-07/D-08)
- Per-row + batch «Сделать ready» UX with optimistic ready, soft empty-body warn, one batch call
- Locked ADUX-06: exact D-15 empty copy + named `honest_factor_labels` matrix

## Task Commits

Each task was committed atomically (RED→GREEN):

1. **Task 1 RED:** `3d78011` — `test(14-03): add failing markReady mock + adminApi export tests`
2. **Task 1 GREEN:** `a1e2b45` — `feat(14-03): wire markReady and markReadyBatch with pure mocks`
3. **Task 2 RED:** `27fc8c2` — `test(14-03): add failing Playwright ready promote UX tests`
4. **Task 2 GREEN:** `a1bfb19` — `feat(14-03): add per-row and batch Сделать ready UX`
5. **Task 3 RED:** `096b91c` — `test(14-03): lock D-15 empty Обоснование + factor honesty matrix`
6. **Task 3 GREEN:** `691285c` — `feat(14-03): show exact D-15 empty Обоснование copy`

## TDD Gate Compliance

| Task | RED commit | GREEN commit | RED evidence |
|------|------------|--------------|--------------|
| 1 adminApi mocks | `3d78011` | `a1e2b45` | `14-03-task1-red-evidence.json` → `RED_EVIDENCE_OK` |
| 2 AdminDigestPage UX | `27fc8c2` | `a1bfb19` | `14-03-task2-red-evidence.json` → `RED_EVIDENCE_OK` |
| 3 D-15 + matrix | `096b91c` | `691285c` | `14-03-task3-red-evidence.json` → `RED_EVIDENCE_OK` |

## Files Created/Modified

- `web/src/services/adminReadyMock.js` — pure mark-ready mock helpers + default seed
- `web/src/services/adminApi.js` — `markReady` / `markReadyBatch` + harness counter
- `web/src/pages/AdminDigestPage.jsx` — promote UX + D-15 `factorText`
- `web/src/main.jsx` — expose `getMockMarkReadyBatchCalls`
- `tests/unit/test_admin_mark_ready.js` — node --test gate
- `tests/admin.spec.js` — Playwright ready + D-15 asserts
- `tests/unit/test_score_factors.py` — named 0/1/2+/whitespace matrix

## Decisions Made

- Seed ownership moved to `getMockDefaultItems` so node --test and SPA share material 104 empty `factor_labels`
- Playwright proves single batch call via harness counter (mocks have no HTTP route)
- No score_factors writers / PIPE UI (D-11/D-12 out of scope)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Batch call counter raced optimistic UI**
- **Found during:** Task 2 GREEN
- **Issue:** Optimistic `ready` badge asserted before mock `delay(60)` incremented the harness counter → `batchCalls === 0`
- **Fix:** Increment counter before delay; Playwright `waitForFunction` until calls ≥ 1
- **Files modified:** `web/src/services/adminApi.js`, `tests/admin.spec.js`
- **Commit:** `a1bfb19`

## Auth Gates

None.

## Known Stubs

None — promote paths and D-15 copy are fully wired under mocks and live clients.

## Threat Flags

None beyond plan threat model (T-14-07…T-14-09 mitigated by exact D-15 + Bearer reuse + no fake ready on error).

## Self-Check: PASSED

