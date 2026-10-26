---
phase: 02-issue-materials-archive
plan: 03
subsystem: api
tags: [fastapi, jwt, react, ports-adapters, archive, content-api, playwright, pytest]

requires:
  - phase: 02-issue-materials-archive
    provides: IssueRepository port (get_by_number, list_past_published), get_current_issue, IssuePage, contentApi, seed issues 13+14
provides:
  - list_archive_issues use-case excluding current (D-31)
  - get_issue_by_number + IssueNotFoundError → HTTP 404
  - GET /archive and GET /issues/{number} JWT-gated
  - ArchivePage + AppShell «Архив» nav (D-28)
  - Past IssuePage without EditorialCallout (D-34) + soft empty «Выпуск не найден»
affects:
  - 02-04 material reader (shared IssueToc / materials links)
  - 02-05 voting cycle stub on current-only callout
  - 02-06 load-failure splash (retryable NETWORK path)

actuals:
  tokens: 15497
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - Archive business rule in application layer via list_past_published port
    - ContentApiError NOT_FOUND (retryable=false) distinct from NETWORK for soft editorial empties
    - IssuePage isCurrent prop gates EditorialCallout (D-34)

key-files:
  created:
    - backend/src/backend/application/use_cases/list_archive_issues.py
    - backend/src/backend/application/use_cases/get_issue_by_number.py
    - tests/unit/test_get_issue_by_number.py
    - web/src/pages/ArchivePage.jsx
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/interface/http/routes/issues.py
    - backend/src/backend/interface/http/app.py
    - tests/unit/test_list_archive_issues.py
    - tests/unit/test_http_issues.py
    - web/src/services/contentApi.js
    - web/src/data/mock.js
    - web/src/pages/IssuePage.jsx
    - web/src/App.jsx
    - web/src/components/AppShell.jsx
    - tests/web-app.spec.js

key-decisions:
  - "GET /archive mounted via issues.archive_router (no /issues prefix) alongside issues.router"
  - "Past/current issue DTO reuses CurrentIssueResponse shape without voting_cycle"
  - "Mock pastIssue №13 + __DIGEST_EMPTY_ARCHIVE__ harness mirrors empty-current pattern"

patterns-established:
  - "Soft issue 404: ContentApiError NOT_FOUND → editorial empty, never bad_gateway splash"
  - "Archive cards link by number `/issues/:number`; no «текущий» badge in grid"

requirements-completed: [ISSUE-04]

coverage:
  - id: D1
    description: "Archive list excludes current latest-published (D-31); empty OK"
    requirement: ISSUE-04
    verification:
      - kind: unit
        ref: tests/unit/test_list_archive_issues.py#test_list_archive_excludes_current_latest_published
        status: pass
      - kind: unit
        ref: tests/unit/test_http_issues.py#test_archive_excludes_current_and_lists_past
        status: pass
    human_judgment: false
  - id: D2
    description: "GET /issues/{number} JWT-gated; missing → 404; SPA soft empty «Выпуск не найден»"
    requirement: ISSUE-04
    verification:
      - kind: unit
        ref: tests/unit/test_http_issues.py#test_issues_by_number_missing_returns_404
        status: pass
      - kind: e2e
        ref: tests/web-app.spec.js#shows soft empty «Выпуск не найден» for unknown issue number
        status: pass
    human_judgment: false
  - id: D3
    description: "Archive nav + past issue without callout; empty archive CTA to current"
    requirement: ISSUE-04
    verification:
      - kind: e2e
        ref: tests/web-app.spec.js#navigates Архив nav to past issue without voting callout
        status: pass
      - kind: e2e
        ref: tests/web-app.spec.js#shows empty archive «Архив пуст» with CTA to current
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-09-20
status: complete
---

# Phase 02 Plan 03: Archive & Past Issues Summary

**JWT-gated archive API + `/archive` reader UX with past IssuePage (no voting callout) and calm «Выпуск не найден» soft empty.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-20T10:34:50Z
- **Completed:** 2026-09-20T10:41:30Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments

- `list_archive_issues` / `get_issue_by_number` with `IssueNotFoundError`; HTTP `GET /archive` + `GET /issues/{number}` require JWT
- AppShell «Архив» between Выпуск and База; ArchivePage empty/populated CTAs per UI-SPEC (D-28…D-31)
- Past `/issues/:number` reuses IssuePage without EditorialCallout (D-34); unknown number → soft empty without `bad_gateway`

## Task Commits

1. **Task 1 RED:** `69d6c7a` — test(02-03): add failing tests for archive and issue-by-number
2. **Task 1 GREEN:** `2c9f673` — feat(02-03): implement archive and issue-by-number APIs
3. **Task 2 RED:** `d97a1bd` — test(02-03): add failing Playwright for archive and soft-404
4. **Task 2 GREEN:** `3365f76` — feat(02-03): add ArchivePage, nav, and past IssuePage soft-404

**Plan metadata:** `5290e92` (docs: complete plan)

## Files Created/Modified

- `backend/.../list_archive_issues.py` — D-31 archive use-case
- `backend/.../get_issue_by_number.py` — published-by-number or not-found
- `backend/.../routes/issues.py` — current + by-number + archive_router
- `web/src/pages/ArchivePage.jsx` — archive list / empty states
- `web/src/pages/IssuePage.jsx` — `isCurrent` + NOT_FOUND soft empty
- `web/src/services/contentApi.js` — `fetchArchive` / `fetchIssueByNumber`
- `tests/unit/test_*.py` + `tests/web-app.spec.js` — TDD coverage

## Decisions Made

- Mount `/archive` on a sibling `archive_router` (issues module) so path is not under `/issues`
- Reuse `CurrentIssueResponse` for by-number payloads (no voting_cycle on past issues)
- Mock `pastIssue` №13 + `window.__DIGEST_EMPTY_ARCHIVE__` for offline Playwright

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] IssueNotFoundError domain type**
- **Found during:** Task 1
- **Issue:** Plan required domain not-found → HTTP 404; only MaterialNotFoundError existed
- **Fix:** Added `IssueNotFoundError(number)` in `domain/errors.py`; use-case raises it
- **Files modified:** `backend/src/backend/domain/errors.py`, `get_issue_by_number.py`, `issues.py`
- **Verification:** unit HTTP 404 + use-case raise tests green
- **Committed in:** `2c9f673`

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** Required for correct not-found mapping; no scope creep.

## Issues Encountered

None blocking. Unrelated AppShell identity WIP left unstaged (not part of 02-03 commit).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Archive/past-issue reader path ready for 02-04 material deep-links from IssueToc
- Current-only callout preserved for 02-05 voting DTO stub
- Retryable NETWORK splash still deferred to 02-06

## Self-Check: PASSED

- FOUND: `backend/src/backend/application/use_cases/list_archive_issues.py`
- FOUND: `backend/src/backend/application/use_cases/get_issue_by_number.py`
- FOUND: `web/src/pages/ArchivePage.jsx`
- FOUND: `02-03-SUMMARY.md`
- FOUND commits: `69d6c7a`, `2c9f673`, `d97a1bd`, `3365f76`

---
*Phase: 02-issue-materials-archive*
*Completed: 2026-09-20*
