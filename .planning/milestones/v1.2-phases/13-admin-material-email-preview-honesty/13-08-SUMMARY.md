---
phase: 13-admin-material-email-preview-honesty
plan: 08
subsystem: ui
tags: [react, playwright, admin-digest, email-preview]

requires:
  - phase: 13-admin-material-email-preview-honesty
    provides: Sandboxed email iframe and pinned close header from plans 13-04 and 13-07
provides:
  - Email preview success view is subject plus sandboxed iframe only
  - Playwright no longer requires a light-DOM ranked items list
affects: [13-admin-material-email-preview-honesty]

actuals:
  tokens: 1689
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Email honesty surface is subject plus iframe srcDoc; preview.items stays on the DTO and is not painted"

key-files:
  created:
    - .planning/phases/13-admin-material-email-preview-honesty/13-08-task1-red-evidence.json
  modified:
    - web/src/pages/AdminDigestPage.jsx
    - tests/admin.spec.js

key-decisions:
  - "Email success branch renders subject and email-preview-frame only; the preview.items ul is not mounted"
  - "Close-scroll viewport is 1280x400 so scrollHeight exceeds clientHeight from the subject plus the iframe after the list is gone"

patterns-established:
  - "Dialog ul count 0 is asserted only after the iframe success body is visible, so the loading state cannot satisfy it"

requirements-completed: [ADUX-02]

coverage:
  - id: D1
    description: "Successful email preview shows the subject and sandboxed iframe and does not render a numbered items list"
    requirement: ADUX-02
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#preview lists one approved-ready article (zero-one-many E4)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Email preview close stays visible while the subject-plus-iframe region scrolls, with dialog ul count 0"
    requirement: ADUX-02
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#email preview close stays visible while the preview scrolls"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-10-03
status: complete
plan_head_before: 0c6dd137d1ce156232bf05ce7da1f72c8417152b
plan_head_after: 0c1d27b630eeb287689644cc73d22aaef8c33bda
---

# Phase 13 Plan 08: Drop the duplicate email item list Summary

**Email preview success view is the subject plus a sandboxed iframe; the numbered preview.items list is gone**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-03T09:06:45Z
- **Completed:** 2026-10-03T09:15:03Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Removed the numbered `preview.items` list under the email iframe (G-13-3b, D-10).
- Retargeted the four light-DOM `li` asserts to dialog `ul` count 0, with the one-article title read from the iframe heading.
- Kept the close-scroll proof overflowing from the subject plus `email-preview-frame` by using a 1280×400 viewport.

## Task Commits

Each task was committed atomically:

1. **Task 1: Email preview shows subject and iframe without a ranked list** - `e16aa52` (test, RED) then `0c1d27b` (feat, GREEN)
2. **Task 2: Regression: email preview suite no longer depends on the item list** - no commit; no remaining `emailDialog.locator("li")` or `previewLis`, and the broader filter passed

**Plan metadata:** committed with this summary

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified
- `web/src/pages/AdminDigestPage.jsx` - Email success branch no longer maps `preview.items` into a `ul`
- `tests/admin.spec.js` - List asserts retargeted to iframe, subject, and dialog `ul` count 0; close-scroll viewport height 400
- `.planning/phases/13-admin-material-email-preview-honesty/13-08-task1-red-evidence.json` - RED evidence (`RED_EVIDENCE_OK`)

## Decisions Made
- Leave `preview.items` and `preview.body` on the response. Do not mount `preview.body` and do not add a plain-versus-HTML switch.
- Do not change iframe `sandbox=""` or `srcDoc`, and do not change the pinned header from plan 07.
- At 1280×480, after the list was removed, scrollHeight equalled clientHeight (356). Height 400 makes scrollHeight 356 greater than clientHeight 292 from the subject plus the iframe.

## Deviations from Plan

None - plan executed exactly as written. The viewport reduction is the contingency the plan specified when 1280×480 overflowed only because of the items list.

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR | Status |
|------|-----|-------|----------|--------|
| 1 Email list removal | `e16aa52` | `0c1d27b` | — | `RED_EVIDENCE_OK` (`13-08-task1-red-evidence.json`) |
| 2 Regression sweep | — | — | — | No leftover list asserts; broader filter 6 passed |

## Issues Encountered
- Playwright MCP could not launch system Chrome, and the Cursor browser tab did not apply the admin init script, so the live check used the project Playwright Chromium against the mock Vite server. Result: ul count 0, li count 0, `email-preview-body` count 0, subject visible, `sandbox=""`, iframe visible, close still in the viewport after scroll (scrollHeight 356, clientHeight 292).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- G-13-3b is closed in the admin email dialog. Phase 13 plans 01–08 are implemented.
- Intro, interstitial order, send unlock, and the ban-list iframe check still pass without a light-DOM ranked list.

## Self-Check: PASSED

- FOUND: web/src/pages/AdminDigestPage.jsx
- FOUND: tests/admin.spec.js
- FOUND: .planning/phases/13-admin-material-email-preview-honesty/13-08-task1-red-evidence.json
- FOUND: e16aa52
- FOUND: 0c1d27b

---
*Phase: 13-admin-material-email-preview-honesty*
*Completed: 2026-10-03*
