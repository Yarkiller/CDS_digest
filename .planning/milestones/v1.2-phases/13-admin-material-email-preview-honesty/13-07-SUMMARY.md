---
phase: 13-admin-material-email-preview-honesty
plan: 07
subsystem: ui
tags: [react, playwright, tailwind, admin-digest]

requires:
  - phase: 13-admin-material-email-preview-honesty
    provides: Material and email preview dialogs from plans 13-04 and 13-05
provides:
  - Pinned close control on the material preview dialog
  - Pinned close control on the email preview dialog
  - Mock-only long body_markdown seam for the material scroll proof
affects: [13-admin-material-email-preview-honesty]

actuals:
  tokens: 4402
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Preview dialog chrome is a flex column; the header row sits outside overflow-y-auto"
    - "Mock window flags that change shortlist DTOs stay inside fetchShortlist's useMocks branch"

key-files:
  created: []
  modified:
    - web/src/pages/AdminDigestPage.jsx
    - web/src/services/adminApi.js
    - tests/admin.spec.js

key-decisions:
  - "Close stays visible because the header row is outside the scrollport, not because it is position sticky"
  - "The long-body seam repeats one sentence forty times and is read only in the mock shortlist branch"

patterns-established:
  - "Admin preview dialogs: shrink-0 header with cursor-pointer close, min-h-0 flex-1 overflow-y-auto body"

requirements-completed: [ADUX-01, ADUX-02]

coverage:
  - id: D1
    description: "Material preview close stays in view with cursor-pointer while the markdown body scrolls"
    requirement: ADUX-01
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#material preview close stays visible while the body scrolls"
        status: pass
    human_judgment: false
  - id: D2
    description: "Email preview close stays in view with cursor-pointer while the preview scrolls"
    requirement: ADUX-02
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#email preview close stays visible while the preview scrolls"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-10-03
status: complete
plan_head_before: b4e98a75f3145d1f7b6ccf6ecc9e2f88150ee779
plan_head_after: 41417f72b1cc0831981918130628c86f6f53a146
---

# Phase 13 Plan 07: Pin preview close controls Summary

**Material and email preview dialogs keep «Закрыть» in view with cursor-pointer while their bodies scroll**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-03T08:39:00Z
- **Completed:** 2026-10-03T08:50:02Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Material preview header (heading plus «Закрыть») sits outside the scrolling markdown body, and that close control uses `cursor-pointer` (G-13-1, G-13-2).
- Email preview uses the same shell: loading, error, and success content scroll, the close control does not, and the iframe keeps `sandbox=""` and `srcDoc` (G-13-3).
- Mock shortlist sets a forty-paragraph body only when `__DIGEST_ADMIN_MATERIAL_LONG_BODY__` is set, and `resetAdminHarness` clears that flag.

## Task Commits

Each task was committed atomically:

1. **Task 1: Pin material-preview close while the body scrolls** - `1575693` (test) then `c5979c7` (feat)
2. **Task 2: Pin email-preview close while the preview scrolls** - `4eba28e` (test) then `41417f7` (feat)

## Files Created/Modified

- `web/src/pages/AdminDigestPage.jsx` - Flex-column shells for the material and email preview dialogs; confirm-send dialog unchanged
- `web/src/services/adminApi.js` - Mock-only long `body_markdown` and harness reset for `__DIGEST_ADMIN_MATERIAL_LONG_BODY__`
- `tests/admin.spec.js` - Playwright proofs that close stays in the viewport after each body is scrolled

## Decisions Made

- The header row is a sibling of the `overflow-y-auto` region, so the close control cannot scroll away with the body.
- The long-body flag follows the empty-body flag: it mutates `items[0]` only inside `fetchShortlist`'s `useMocks` branch. The live `/admin/shortlist` fetch is unchanged.
- Email overflow was real at 1280×480, so the test did not shrink the viewport further.

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR | Evidence |
|------|-----|-------|----------|----------|
| 1 Material close | `1575693` | `c5979c7` | — | `RED_EVIDENCE_OK` (`13-07-task1-red-evidence.json`) |
| 2 Email close | `4eba28e` | `41417f7` | — | `RED_EVIDENCE_OK` (`13-07-task2-red-evidence.json`) |

RED for both tasks was `expect(closeContract.insideOverflow).toBe(false)` receiving `true` (close still inside `overflow-y-auto`). Tracer feedback gate re-ran the material test after `c5979c7` and it passed before the email task.

## Issues Encountered

- On this Windows npm, `-g` and `--grep` are consumed before they reach Playwright, so `npm run test:web -- tests/admin.spec.js -g "…"` executed the whole admin file. The same `playwright test --project=web` invocation with `--grep` passed: material close 1 passed, then both close tests 2 passed.
- That unfiltered file run also failed `/me network failure shows ServiceUnavailable not Forbidden` in `tests/admin.spec.js`. It failed before the layout change and is outside this plan.
- The IDE browser opened `/admin/digest` as the employee role (Недостаточно прав), so the dialogs were not clicked there. The project Playwright browser proved both scroll contracts.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- G-13-1, G-13-2, and G-13-3 are covered by the two scroll tests. Confirm-send and the iframe sandbox were left as they were.
- G-13-3b (items list under the email iframe) is still rendered; this plan was not allowed to remove it.

## Self-Check: PASSED

- FOUND: web/src/pages/AdminDigestPage.jsx
- FOUND: web/src/services/adminApi.js
- FOUND: tests/admin.spec.js
- FOUND: 1575693
- FOUND: c5979c7
- FOUND: 4eba28e
- FOUND: 41417f7

---
*Phase: 13-admin-material-email-preview-honesty*
*Completed: 2026-10-03*
