---
phase: 05-admin-digest-publish
plan: 09
subsystem: ui
tags: [fastapi, react, playwright, shortlist, digest, digest_rest, TDD, G-05-2]

requires:
  - phase: 05-admin-digest-publish
    provides: Preview/send order and Отправка записана / Уже отправлено from 05-08
provides:
  - AdminShortlist digest_rest + days_until_next_batch=7 weekly cadence
  - SPA post-send / cold-rest panel hiding triage chrome
  - Playwright G-05-2 rest vs D-80 empty distinction
affects: [phase-05-verify, digest-admin-uat]

actuals:
  tokens: 7674
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - get_current_batch None + get_latest_batch.sent_at → digest_rest DTO
    - SPA restMode = batchSent || digestRest hides triage; sticky footer keeps Уже отправлено

key-files:
  created: []
  modified:
    - backend/src/backend/domain/shortlist.py
    - backend/src/backend/application/use_cases/get_admin_shortlist.py
    - backend/src/backend/interface/http/routes/admin.py
    - tests/unit/test_get_admin_shortlist.py
    - tests/unit/test_http_admin.py
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx
    - tests/admin.spec.js
    - .planning/phases/05-admin-digest-publish/05-UI-SPEC.md

key-decisions:
  - "days_until_next_batch is DIGEST_WEEKLY_CADENCE_DAYS=7 from product weekly cadence — not voting_cycles or week_start math"
  - "D-80 empty copy only when digest_rest is false; post-send/cold rest uses separate rest surface"

patterns-established:
  - "Mock __DIGEST_ADMIN_DIGEST_REST__ and post-send mockBatch.sent_at return rest DTO"
  - "confirmSend / ALREADY_SENT clear items and enter restMode while preserving locked banners"

requirements-completed: [ADMIN-01, ADMIN-07]

coverage:
  - id: D1
    description: Shortlist API returns digest_rest + days_until_next_batch=7 after send; genuine empty stays D-80-shaped
    requirement: ADMIN-01
    verification:
      - kind: unit
        ref: "tests/unit/test_get_admin_shortlist.py#test_get_admin_shortlist_after_send_returns_digest_rest"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_shortlist_after_send_returns_digest_rest"
        status: pass
    human_judgment: false
  - id: D2
    description: Post-send and ALREADY_SENT hide shortlist/checkboxes; show rest copy; keep Отправка записана / Уже отправлено
    requirement: ADMIN-07
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#G-05-2: after Отправка записана shortlist hides; rest copy shown"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#G-05-2: Уже отправлено enters rest hide without inactive checkboxes"
        status: pass
    human_judgment: false
  - id: D3
    description: Cold digest_rest load shows rest panel; D-80 empty does not
    requirement: ADMIN-01
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#G-05-2: cold load digest_rest shows rest instead of Кандидатов пока нет"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#empty shortlist shows Кандидатов пока нет without пайплайн"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 09: Post-send shortlist rest Summary

**G-05-2 closed: after stub send (or cold `digest_rest`), triage rows/checkboxes hide behind «дайджест успешно выпущен» + «через 7 дней», while locked «Отправка записана» / «Уже отправлено» stay**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-21T19:02:37Z
- **Completed:** 2026-09-21T19:12:14Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- Extended `AdminShortlist` / GET `/admin/shortlist` with `digest_rest` and weekly `days_until_next_batch=7`
- SPA rest mode hides toolbar, editors, and checkboxes after send / ALREADY_SENT / cold rest
- Full `tests/admin.spec.js` green with D-80 vs rest distinction

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Shortlist rest DTO tests** - `ced237a` (test)
2. **Task 1 (GREEN): digest_rest DTO + UI-SPEC** - `fa4b144` (feat)
3. **Task 2 (RED): Playwright rest panel** - `a96055c` (test)
4. **Task 2 (GREEN): SPA rest panel** - `f45e435` (feat)
5. **Task 3: D-80 vs rest regression** - `3f0c425` (test)

**Plan metadata:** `928b031` (docs: complete post-send shortlist rest plan)

_Note: TDD tasks used separate test → feat commits_

## Files Created/Modified
- `backend/src/backend/domain/shortlist.py` - `digest_rest`, `days_until_next_batch`, `DIGEST_WEEKLY_CADENCE_DAYS`
- `backend/src/backend/application/use_cases/get_admin_shortlist.py` - rest DTO via `get_latest_batch`
- `backend/src/backend/interface/http/routes/admin.py` - response fields
- `web/src/services/adminApi.js` - map rest fields; mock rest after send / sticky flag
- `web/src/pages/AdminDigestPage.jsx` - restMode panel + footer lock
- `tests/unit/test_get_admin_shortlist.py` / `test_http_admin.py` - unit coverage
- `tests/admin.spec.js` - G-05-2 Playwright + D-80 negative assert
- `.planning/phases/05-admin-digest-publish/05-UI-SPEC.md` - rest copy + state machine

## Decisions Made
- Countdown X = product weekly cadence constant 7 (not voting window / week_start arithmetic)
- D-80 «Кандидатов пока нет» only when `digest_rest` is false

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0
**Impact on plan:** N/A

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 05 plans 01–09 complete — ready for `/gsd-verify-work` / phase verification
- G-05-2 UAT remark addressed; locked D-87/D-89 strings unchanged

---
*Phase: 05-admin-digest-publish*
*Completed: 2026-09-21*

## Self-Check: PASSED

