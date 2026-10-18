---
phase: 05-admin-digest-publish
plan: 04
subsystem: ui
tags: [react, playwright, admin-digest, mocks, role-gate, preview-send, tdd]

requires:
  - phase: 05-admin-digest-publish
    provides: require_admin HTTP + shortlist decision/preview/send + meApi setMockMeRole
provides:
  - adminApi.js mocks + live fetch for shortlist/decision/preview/send
  - AppShell «Админ» nav gated on /me.role === admin (D-76)
  - ForbiddenPage 403 deep-link (D-75)
  - AdminDigestPage triage + preview/send gate under mocks
  - tests/admin.spec.js Playwright honesty suite
affects:
  - 05-05 live shortlist adapters
  - 05-06 Playwright honesty expansion / UAT

actuals:
  tokens: 15272
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "adminApi mirrors votingApi isMocksEnabled + typed AdminApiError"
    - "Sticky __DIGEST_MOCK_ME_ROLE__ / __DIGEST_ADMIN_*__ Playwright harness flags"
    - "Client emailPreviewed fingerprint gate; server remains authoritative on send"

key-files:
  created:
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx
    - web/src/pages/ForbiddenPage.jsx
    - tests/admin.spec.js
  modified:
    - web/src/components/AppShell.jsx
    - web/src/App.jsx
    - web/src/services/meApi.js
    - web/src/main.jsx
    - playwright.config.js

key-decisions:
  - "Route /admin/digest; AdminDigestPage self-gates Forbidden vs triage after /me"
  - "Send pool = approved∩ready (not checkboxes); checkboxes are batch Approve/Reject only (D-83)"
  - "Top-N locked at N=3; preview modal close race ignored via functional setState"
  - "Playwright resets adminApi harness between /admin navigations to clear Vite singleton mock state"

patterns-established:
  - "Pattern: role-gated NavLink from fetchMe.role; never authorize from JWT claim"
  - "Pattern: emailPreviewed + fingerprint(approved∩ready) invalidates on approved-set change (D-86)"
  - "Pattern: confirm dialog «Подтвердить отправку» / «Не отправлять»; success «Отправка записана»"

requirements-completed: [ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07]

coverage:
  - id: D1
    description: "Employee never sees Админ nav; admin NavLink → /admin/digest"
    requirement: ADMIN-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#admin sees Админ nav linking to /admin/digest"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#employee never sees Админ nav link"
        status: pass
    human_judgment: false
  - id: D2
    description: "Non-admin deep-link renders ForbiddenPage «Недостаточно прав» + «На выпуск»"
    requirement: ADMIN-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#employee deep-link /admin/digest shows 403 Недостаточно прав"
        status: pass
    human_judgment: false
  - id: D3
    description: "Populated shortlist ≤5 rows with badges, factors honesty, empty D-80 copy, Approve caption"
    requirement: ADMIN-02
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#populated shortlist shows ≤5 rows with badges and score factors"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#empty shortlist shows Кандидатов пока нет without пайплайн"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#Одобрить выбранные persists and shows одобрен caption"
        status: pass
    human_judgment: false
  - id: D4
    description: "Select-all / top-3 checkbox ops; preview unlocks send; success and already-sent copy"
    requirement: ADMIN-06
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#Выбрать все and Оставить топ-3 update checkboxes"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#превью unlocks send; confirm records Отправка записана"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#Уже отправлено when batch already sent"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 04: Admin Digest SPA Summary

**Role-gated Admin Digest triage SPA under mocks: 403 for employees, shortlist chrome with factor honesty, batch Approve/Reject, select-all/top-3, mandatory preview fingerprint gate, and confirm send.**

## Performance

- **Duration:** 15min
- **Started:** 2026-09-21T14:55:44Z
- **Completed:** 2026-09-21T15:10:21Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- AppShell shows «Админ» only when `/me.role === admin`; employees deep-linking `/admin/digest` see ForbiddenPage (D-75, D-76)
- AdminDigestPage renders ≤5 shortlist rows with ready/draft badges, score factors or «обоснование недоступно», empty D-80 copy, and batch Approve/Reject
- Select-all / top-3, mandatory email preview gate, confirm send with «Отправка записана» / «Уже отправлено» under adminApi mocks

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED:** `e36892b` — test(05-04): admin nav + 403 failing checks
2. **Task 1 GREEN:** `708823c` — feat(05-04): adminApi, role nav, ForbiddenPage
3. **Task 2 RED:** `dbdba55` — test(05-04): shortlist triage failing checks
4. **Task 2 GREEN:** `6ff9bcb` — feat(05-04): AdminDigestPage shortlist triage
5. **Task 3 RED:** `0d315dc` — test(05-04): select/preview/send failing checks
6. **Task 3 GREEN:** `268ba3f` — feat(05-04): select-all, preview gate, confirm send

## Files Created/Modified
- `web/src/services/adminApi.js` — shortlist/decision/preview/send mocks + live fetch
- `web/src/pages/AdminDigestPage.jsx` — triage UI + send gate state machine
- `web/src/pages/ForbiddenPage.jsx` — 403 deep-link page
- `web/src/components/AppShell.jsx` — role-gated «Админ» NavLink
- `web/src/App.jsx` — route `/admin/digest`
- `web/src/services/meApi.js` — sticky `__DIGEST_MOCK_ME_ROLE__`
- `web/src/main.jsx` — `__DIGEST_ADMIN_HARNESS__` + setMockMeRole
- `tests/admin.spec.js` — Playwright honesty suite
- `playwright.config.js` — include admin.spec.js in web project

## Decisions Made
- AdminDigestPage self-gates Forbidden vs triage after `/me` (single route)
- Checkboxes are batch-action targets only; send pool = all approved∩ready (D-83)
- Preview success sets session `emailPreviewed` for fingerprint(approved∩ready); approved-set change invalidates (D-86)
- Playwright resets `adminApi` harness on each `/admin` navigation to clear Vite module singleton state

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preview modal reopen race after early close**
- **Found during:** Task 3 (preview/send)
- **Issue:** Closing the email modal while `previewEmail` was in flight let the late success setState reopen the dialog and block the sticky send footer
- **Fix:** Functional `setEmailModal` that keeps `null` if the user already closed; tests wait for preview body before close
- **Files modified:** `web/src/pages/AdminDigestPage.jsx`, `tests/admin.spec.js`
- **Committed in:** `268ba3f`

**2. [Rule 3 - Blocking] Cross-test adminApi mock pollution**
- **Found during:** Task 3 (full suite)
- **Issue:** Vite keeps `adminApi` module singleton across Playwright tests; prior Approve/Send left dirty mock state
- **Fix:** `gotoAsRole` resets `__DIGEST_ADMIN_HARNESS__.resetAdminHarness()` then reloads for `/admin` paths
- **Files modified:** `tests/admin.spec.js`
- **Committed in:** `268ba3f`

**3. [Rule 3 - Blocking] ProfilePage required by pre-existing App.jsx WIP**
- **Found during:** Task 1 GREEN commit
- **Issue:** Working tree already imported `ProfilePage` in `App.jsx`; committing App without the page would break the SPA
- **Fix:** Included `web/src/pages/ProfilePage.jsx` in the Task 1 feat commit
- **Files modified:** `web/src/pages/ProfilePage.jsx`
- **Committed in:** `708823c`

---

**Total deviations:** 3 auto-fixed (1 Rule 1, 2 Rule 3)
**Impact on plan:** Necessary for green Playwright and a buildable App; no scope creep beyond plan deliverables.

## Issues Encountered
None beyond the auto-fixed races/harness isolation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 05-05 can wire live ShortlistRepository adapters; SPA already uses Bearer JWT when `VITE_USE_MOCKS=false`
- 05-06 can expand Playwright honesty / visual backstops against the landed AdminDigestPage

## TDD Gate Compliance
RED→GREEN commits present for all three tasks (`test(05-04)` then `feat(05-04)` pairs).

## Self-Check: PASSED
- FOUND: `web/src/services/adminApi.js`, `web/src/pages/AdminDigestPage.jsx`, `web/src/pages/ForbiddenPage.jsx`, `tests/admin.spec.js`
- FOUND: commits `e36892b`, `708823c`, `dbdba55`, `6ff9bcb`, `0d315dc`, `268ba3f`
- Playwright `tests/admin.spec.js` — 9 passed

---
*Phase: 05-admin-digest-publish*
*Completed: 2026-09-21*
