---
phase: 02-issue-materials-archive
plan: 06
subsystem: ui
tags: [playwright, service-unavailable, contentApi, load-failure, D-21, D-22, D-23]

requires:
  - phase: 02-issue-materials-archive
    provides: Issue/Material/Archive pages + contentApi harness (02-04/02-05)
provides:
  - ServiceUnavailable splash with /bad_gateway.png + Повторить
  - Sticky fail harness (__DIGEST_FAIL_NEXT_CONTENT__) for Playwright/StrictMode
  - Phase 2 full automated gate green under mocks
  - Updated 02-VALIDATION.md Nyquist map (nyquist_compliant still false)
affects:
  - gsd-verify-work
  - gsd-validate-phase

actuals:
  tokens: 17600
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - sticky window fail flag cleared on Retry (StrictMode-safe)
    - ServiceUnavailable fixed Russian copy — no HTTP codes (D-23)

key-files:
  created:
    - web/public/bad_gateway.png
    - web/src/components/ServiceUnavailable.jsx
  modified:
    - web/src/services/contentApi.js
    - web/src/pages/IssuePage.jsx
    - web/src/pages/MaterialPage.jsx
    - web/src/pages/ArchivePage.jsx
    - web/src/main.jsx
    - tests/web-app.spec.js
    - .planning/phases/02-issue-materials-archive/02-VALIDATION.md

key-decisions:
  - "Window __DIGEST_FAIL_NEXT_CONTENT__ is sticky (not one-shot) so React StrictMode remounts still show splash; clearFailNextContentFetch on Retry"
  - "UI-SPEC visual backstops held as describe.skip for /gsd-verify-work — not silent-passed"

patterns-established:
  - "Page load failure → ServiceUnavailable; soft NOT_FOUND stays editorial empty without splash art"
  - "Phase gate full suite only in 02-06; prior plans keep targeted verifies"

requirements-completed: [ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04, MAT-01, MAT-02, MAT-03]

coverage:
  - id: D1
    description: "Live content load failure shows splash /bad_gateway.png + «Ошибочка вышла» + Повторить without mock fallback"
    requirement: ISSUE-01
    verification:
      - kind: e2e
        ref: "tests/web-app.spec.js#shows ошибочка splash with bad_gateway art and recovers on Повторить"
        status: pass
    human_judgment: false
  - id: D2
    description: "Soft material/issue 404 never shows bad_gateway splash art"
    requirement: MAT-02
    verification:
      - kind: e2e
        ref: "tests/web-app.spec.js#shows not-found recovery for an unknown material id"
        status: pass
    human_judgment: false
  - id: D3
    description: "Phase 2 full automated gate (test:web + test:unit) green under mocks"
    requirement: ISSUE-01
    verification:
      - kind: e2e
        ref: "npm run test:web && npm run test:unit"
        status: pass
    human_judgment: false
  - id: D4
    description: "UI-SPEC overflow/plural/long-text backstops (visual held-out)"
    verification: []
    human_judgment: true
    rationale: "10 UI-SPEC backstops require visual judgment at /gsd-verify-work; tracked as describe.skip"

duration: 12min
completed: 2026-09-20
status: complete
---

# Phase 02 Plan 06: Load-failure splash + phase gate Summary

**ServiceUnavailable splash (`/bad_gateway.png` + «Ошибочка вышла» + Повторить) with sticky content fail harness and green Phase 2 full Playwright+pytest gate under mocks**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-09-20T11:00:04Z
- **Completed:** 2026-09-20T11:10:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Relocated `bad_gateway.png` to `web/public/` and shipped `ServiceUnavailable` on Issue/Material/Archive retryable load errors (D-21…D-23)
- Sticky `__DIGEST_FAIL_NEXT_CONTENT__` harness survives StrictMode; Retry clears via `clearFailNextContentFetch`
- Expanded e2e: stable slug `/materials/rag-systems`, archive/material overflow sampling, UI-SPEC `describe.skip` backstops
- Full gate: `npm run test:web` (37 pass / 1 skip) + `npm run test:unit` (92 pass); VALIDATION map updated (`nyquist_compliant: false` until validate-phase)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED:** `6ee41a3` — `test(02-06): add failing splash Retry e2e for D-21..23`
2. **Task 1 GREEN:** `ec18d39` — `feat(02-06): ServiceUnavailable splash + sticky fail harness`
3. **Task 2:** `8d10d1f` — `test(02-06): expand phase-gate e2e + VALIDATION map`

**Plan metadata:** `9950fa5` (docs: complete plan)

## Files Created/Modified

- `web/public/bad_gateway.png` — Vite-served splash asset
- `web/src/components/ServiceUnavailable.jsx` — fixed Russian copy + Retry (role=alert)
- `web/src/services/contentApi.js` — sticky fail arm + `clearFailNextContentFetch`
- `web/src/pages/IssuePage.jsx` / `MaterialPage.jsx` / `ArchivePage.jsx` — splash on retryable errors
- `web/src/main.jsx` — expose clear on content harness
- `tests/web-app.spec.js` — splash e2e + phase-gate expansions
- `.planning/phases/02-issue-materials-archive/02-VALIDATION.md` — task map + wave_0 addressed

## Decisions Made

- Sticky window fail flag (not consume-and-clear) so StrictMode double-mount still shows splash; clear only on Retry
- UI-SPEC visual backstops intentionally `describe.skip` — human gate at verify-work

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] StrictMode consumed one-shot fail arm before splash rendered**
- **Found during:** Task 1 (GREEN)
- **Issue:** `consumeFailNext` cleared window flag on first effect; remount succeeded with mock data → splash never appeared
- **Fix:** Keep `__DIGEST_FAIL_NEXT_CONTENT__` sticky; add `clearFailNextContentFetch` called from page Retry
- **Files modified:** `contentApi.js`, Issue/Material/Archive pages, `main.jsx`
- **Verification:** splash e2e green
- **Committed in:** `ec18d39`

**2. [Rule 1 - Bug] Voting responsive flake under parallel suite**
- **Found during:** Task 2 full gate
- **Issue:** Radio click timed out once under 2-worker load after longer overflow loop
- **Fix:** `await expect(topic).toBeVisible()` before click
- **Files modified:** `tests/web-app.spec.js`
- **Verification:** full `test:web` green on re-run
- **Committed in:** `8d10d1f`

---

**Total deviations:** 2 auto-fixed (Rule 1)
**Impact on plan:** Correctness for harness + flake hardening; no scope creep

## Issues Encountered

- First full-suite run had one timeout on voting responsive; re-run green after harden

## Known Stubs

| Stub | File | Line | Reason |
|------|------|------|--------|
| UI-SPEC visual backstops `describe.skip` | `tests/web-app.spec.js` | ~406 | Held for `/gsd-verify-work` — not silent-pass |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 automated gate green under mocks — ready for `/gsd-verify-work` (incl. visual backstops) then milestone close
- Live FE↔BE content proof remains human/ops follow-up outside this plan

## Self-Check: PASSED

- FOUND: `web/public/bad_gateway.png`
- FOUND: `web/src/components/ServiceUnavailable.jsx`
- FOUND: commits `6ee41a3`, `ec18d39`, `8d10d1f`

---
*Phase: 02-issue-materials-archive*
*Completed: 2026-09-20*
