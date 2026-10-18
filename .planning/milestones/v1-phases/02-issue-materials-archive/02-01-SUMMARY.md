---
phase: 02-issue-materials-archive
plan: 01
subsystem: api
tags: [fastapi, jwt, react, ports-adapters, content-api, playwright, pytest]

requires:
  - phase: 01-platform-foundation-auth
    provides: get_principal JWT gate, AppContainer, meApi mock/live pattern, VITE_USE_MOCKS
provides:
  - IssueRepository + get_current_issue (D-24 latest published_at)
  - GET /issues/current JWT-protected honest-empty DTO
  - contentApi.fetchCurrentIssue mock/live cutover (D-20/D-21)
  - IssuePage typography hero + TOC or «Выпуск готовится» (D-26/D-30)
  - Wave 0 importorskip scaffolds for archive/materials
affects:
  - 02-02 live Supabase issue adapters + seed
  - 02-03 archive list + ArchivePage
  - 02-04 material reader
  - 02-05 voting cycle stub on current DTO
  - 02-06 load-failure splash

actuals:
  tokens: 14500
  tasks: 3
  commits: 7

tech-stack:
  added: []
  patterns:
    - Ports & Adapters content read path (domain → port → use-case → FastAPI → contentApi → page)
    - Honest empty CurrentIssueResponse (null number + items=[]) instead of 404/500
    - Window-persisted Playwright content harness (__DIGEST_EMPTY_CURRENT_ISSUE__)

key-files:
  created:
    - backend/src/backend/domain/issue.py
    - backend/src/backend/application/ports/issue_repository.py
    - backend/src/backend/application/use_cases/get_current_issue.py
    - backend/src/backend/interface/http/routes/issues.py
    - web/src/services/contentApi.js
    - tests/unit/test_get_current_issue.py
    - tests/unit/test_http_issues.py
    - tests/unit/test_list_archive_issues.py
    - tests/unit/test_get_material_for_reader.py
    - tests/unit/test_http_materials.py
  modified:
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/live.py
    - backend/src/backend/interface/http/app.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/domain/current_user.py
    - web/src/pages/IssuePage.jsx
    - web/src/main.jsx
    - tests/web-app.spec.js

key-decisions:
  - "CurrentIssueResponse uses flat null fields + items=[] for no published issue (SPA treats items.length===0 as empty)"
  - "Empty Playwright arm uses window.__DIGEST_EMPTY_CURRENT_ISSUE__ so full page reload keeps the harness (module flags reset on reload)"
  - "Archive CTA asserts href=/archive only — /archive route lands in 02-03 (catch-all would redirect)"
  - "live.py wires empty InMemoryIssueRepository until 02-02 Supabase adapter"

patterns-established:
  - "contentApi mirrors meApi: ContentApiError {code,retryable}, isMocksEnabled(), never silent mock fallback"
  - "IssueToc consumes mock-shaped items via IssuePage toTocItems (slug→id) mapping"
  - "Wave 0 scaffolds use pytest.importorskip on future modules so default suite stays green"

requirements-completed: [ISSUE-01]

coverage:
  - id: D1
    description: "GET /issues/current requires JWT; returns latest published issue DTO with ordered items"
    requirement: ISSUE-01
    verification:
      - kind: unit
        ref: tests/unit/test_http_issues.py#test_issues_current_with_corporate_jwt_returns_seeded_issue
        status: pass
      - kind: unit
        ref: tests/unit/test_get_current_issue.py#test_get_current_issue_returns_latest_published_by_published_at
        status: pass
    human_judgment: false
  - id: D2
    description: "Typography-only IssuePage hero + IssueTOC under mocks (no cover img); rag-systems slug link"
    requirement: ISSUE-01
    verification:
      - kind: e2e
        ref: tests/web-app.spec.js#opens a material from the issue table of contents
        status: pass
    human_judgment: false
  - id: D3
    description: "Empty current shows «Выпуск готовится» + CTA href /archive (D-30)"
    requirement: ISSUE-01
    verification:
      - kind: e2e
        ref: tests/web-app.spec.js#shows empty current issue «Выпуск готовится» with archive CTA
        status: pass
    human_judgment: false
  - id: D4
    description: "Wave 0 archive/material scaffolds present and skip until modules exist"
    verification:
      - kind: unit
        ref: tests/unit/test_list_archive_issues.py + test_get_material_for_reader.py + test_http_materials.py
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-09-20
status: complete
---

# Phase 02 Plan 01: Current-Issue Tracer Summary

**JWT-protected `GET /issues/current` through ports → in-memory → contentApi → typography IssuePage (hero+TOC or «Выпуск готовится»), with Wave 0 archive/material scaffolds**

## Performance

- **Duration:** 10min
- **Started:** 2026-09-20T09:38:44Z
- **Completed:** 2026-09-20T09:48:00Z
- **Tasks:** 3
- **Files modified:** 18

## Accomplishments

- End-to-end current-issue tracer: domain Issue/IssueItem, IssueRepository, get_current_issue (D-24), FastAPI route, AppContainer.issues, InMemoryIssueRepository
- SPA contentApi with VITE_USE_MOCKS cutover; IssuePage loads DTO — typography hero only (D-26), TOC links `/materials/{slug}`
- Empty path: «Выпуск готовится» + «В архив →» href `/archive` (D-30); loading skeleton distinct via `data-testid`
- Wave 0 importorskip scaffolds for list_archive, get_material_for_reader, HTTP materials

## Task Commits

Each task was committed atomically:

1. **Task 1 RED:** `9430d01` — test(02-01): failing current-issue unit tests (D-24)
2. **Task 1 GREEN:** `3a67265` — feat(02-01): tracer JWT→API→IssuePage (D-24, D-26)
3. **Task 1 fix:** `73c0255` — fix(02-01): CurrentUser.display_name for swept profile in-memory
4. **Task 2 RED:** `3378ef7` — test(02-01): failing Playwright empty current (D-30)
5. **Task 2 GREEN:** `7c4b05e` — feat(02-01): empty-issue harness + green Playwright (D-30)
6. **Task 3:** `1a7cdd8` — test(02-01): Wave 0 importorskip scaffolds

**Plan metadata:** `c128afd` (docs: complete plan)

## Files Created/Modified

- `backend/src/backend/domain/issue.py` — frozen Issue / IssueItem read-models
- `backend/src/backend/application/ports/issue_repository.py` — get_latest_published Protocol
- `backend/src/backend/application/use_cases/get_current_issue.py` — D-24 selection
- `backend/src/backend/interface/http/routes/issues.py` — GET /issues/current
- `web/src/services/contentApi.js` — fetchCurrentIssue + ContentApiError + harness
- `web/src/pages/IssuePage.jsx` — wired load / empty / ready states
- `tests/unit/test_*.py` — unit + Wave 0 scaffolds
- `tests/web-app.spec.js` — empty-issue e2e

## Decisions Made

- Flat honest-empty JSON (`number: null`, `items: []`) for no published issue
- Window flag for empty Playwright arm so Vite full reload keeps the harness
- Archive CTA href-only until 02-03 adds `/archive` route
- Temporary InMemoryIssueRepository in live composition until 02-02

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] live.py AppContainer.issues required**
- **Found during:** Task 1 GREEN
- **Issue:** AppContainer gained `issues:` field; `build_live_container` would TypeError
- **Fix:** Wire empty `InMemoryIssueRepository()` until 02-02
- **Files modified:** `backend/src/backend/composition/live.py`
- **Committed in:** `3a67265`

**2. [Rule 1 - Bug] Empty harness lost on full page.goto reload**
- **Found during:** Task 2 GREEN
- **Issue:** Module-level `emptyCurrentIssue` resets when Playwright reloads
- **Fix:** Persist via `window.__DIGEST_EMPTY_CURRENT_ISSUE__` + `addInitScript`
- **Files modified:** `web/src/services/contentApi.js`, `tests/web-app.spec.js`
- **Committed in:** `7c4b05e`

**3. [Dirty-tree sweep] Phase 1 WIP mixed into shared files**
- **Found during:** Task 1 GREEN commit of `app.py` / `in_memory.py`
- **Issue:** Working tree already had CORS PATCH allow + profile `display_name` methods; could not cleanly `git add -p` on Windows
- **Fix:** Documented sweep; follow-up `73c0255` committed `CurrentUser.display_name` so in-memory profile code stays consistent
- **Files modified:** `app.py` (PATCH method), `in_memory.py` (set_display_name), `current_user.py`
- **Committed in:** `3a67265`, `73c0255`

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 dirty-tree)
**Impact on plan:** Necessary for correctness; no scope creep beyond Phase 1 WIP already in the tree

## Issues Encountered

- `/archive` not routed yet — catch-all Navigate to `/` would break click assertion; switched to href check
- Sequential executor continued past tracer human-verify gate after automated pytest+Playwright green (plan `autonomous: true`, full SUMMARY required)

## User Setup Required

None - no external service configuration required for 02-01 (live seed is 02-02).

## Next Phase Readiness

- Ready for 02-02: Supabase IssueRepository + seed migration 002
- contentApi live path already calls `/issues/current` when `VITE_USE_MOCKS=false`
- Wave 0 scaffolds will activate when 02-03/02-04 modules appear

## Self-Check: PASSED

- FOUND: `.planning/phases/02-issue-materials-archive/02-01-SUMMARY.md`
- FOUND: `backend/src/backend/domain/issue.py`
- FOUND: `web/src/services/contentApi.js`
- FOUND: commits `9430d01`, `3a67265`, `73c0255`, `3378ef7`, `7c4b05e`, `1a7cdd8`

---
*Phase: 02-issue-materials-archive*
*Completed: 2026-09-20*
