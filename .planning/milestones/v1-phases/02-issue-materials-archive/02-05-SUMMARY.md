---
phase: 02-issue-materials-archive
plan: 05
subsystem: api
tags: [fastapi, jwt, react, ports-adapters, voting-cycle, playwright, pytest]

requires:
  - phase: 02-issue-materials-archive
    provides: get_current_issue, IssuePage isCurrent gate, contentApi mocks, seeded voting_cycles
provides:
  - VotingCycleReader port + A2 open-first / latest-closed selection
  - voting_cycle on GET /issues/current DTO only (D-32/D-33)
  - EditorialCallout open/closed/absent from DTO on `/` only (D-34/D-35)
affects:
  - 02-06 load-failure splash + phase-gate e2e
  - Phase 3 vote write APIs

actuals:
  tokens: 7943
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - Narrow VotingCycleReader Protocol; cycle selection in use-case (A2)
    - CurrentIssueView {issue, voting_cycle} assembly; past routes omit cycle
    - Playwright harness flags __DIGEST_VOTING_CYCLE_CLOSED__ / __DIGEST_NO_VOTING_CYCLE__

key-files:
  created:
    - backend/src/backend/domain/voting_cycle.py
    - backend/src/backend/application/ports/voting_cycle_reader.py
    - supabase-integration/src/supabase_integration/voting_cycle_repository.py
  modified:
    - backend/src/backend/application/use_cases/get_current_issue.py
    - backend/src/backend/interface/http/routes/issues.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/live.py
    - backend/src/backend/tests_support/in_memory.py
    - web/src/components/EditorialCallout.jsx
    - web/src/pages/IssuePage.jsx
    - web/src/services/contentApi.js
    - tests/unit/test_get_current_issue.py
    - tests/unit/test_http_issues.py
    - tests/web-app.spec.js

key-decisions:
  - "Cycle selection lives in get_current_issue (A2); adapters only list_cycles"
  - "SupabaseVotingCycleReader in sibling voting_cycle_repository.py (not folded into IssueRepository)"
  - "Past GET /issues/{number} forces voting_cycle=null even if cycles exist"

patterns-established:
  - "CurrentIssueView payload attaches optional voting_cycle for SPA callout only"
  - "EditorialCallout data-testid + muted closed surface; open CTA → /voting"

requirements-completed: [ISSUE-02]

coverage:
  - id: D1
    description: "Current-issue DTO includes read-only voting_cycle; A2 open-first else latest closed"
    requirement: ISSUE-02
    verification:
      - kind: unit
        ref: tests/unit/test_get_current_issue.py#test_get_current_issue_prefers_open_cycle_by_closes_at
        status: pass
      - kind: unit
        ref: tests/unit/test_http_issues.py#test_issues_current_includes_open_voting_cycle
        status: pass
    human_judgment: false
  - id: D2
    description: "EditorialCallout on `/` only — open CTA /voting, closed no CTA, absent hidden"
    requirement: ISSUE-02
    verification:
      - kind: e2e
        ref: tests/web-app.spec.js#shows open voting callout with Выбрать тему CTA on current issue
        status: pass
      - kind: e2e
        ref: tests/web-app.spec.js#shows closed voting callout without topic-select CTA
        status: pass
      - kind: e2e
        ref: tests/web-app.spec.js#hides voting callout when cycle is absent
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-09-20
status: complete
---

# Phase 02 Plan 05: Voting Callout Stub Summary

**Read-only `voting_cycle` on current-issue DTO drives EditorialCallout open/closed/absent on `/` only — no vote write APIs.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-20T10:52:09Z
- **Completed:** 2026-09-20T10:59:00Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments

- `VotingCycleReader` + A2 selection attaches `{status, closes_at}` to `GET /issues/current`
- SPA EditorialCallout: open → «Выбрать тему →» `/voting`; closed → muted copy, no CTA; absent → hidden
- Past `/issues/:number` still omits callout (D-34); no POST vote routes

## Task Commits

Each task was committed atomically:

1. **Task 1 RED:** `4a78dee` — test(02-05): failing voting_cycle unit/HTTP tests
2. **Task 1 GREEN:** `84d4e58` — feat(02-05): attach read-only voting_cycle to current issue DTO
3. **Task 2 RED:** `4879cfb` — test(02-05): failing Playwright callout state tests
4. **Task 2 GREEN:** `750776e` — feat(02-05): wire EditorialCallout from voting_cycle DTO

**Plan metadata:** `98b9ec6` (docs: complete plan)

## Files Created/Modified

- `backend/.../voting_cycle.py` / `voting_cycle_reader.py` — domain + port
- `backend/.../get_current_issue.py` — `CurrentIssueView` + A2 selection
- `backend/.../routes/issues.py` — `VotingCycleResponse` on current only
- `supabase-integration/.../voting_cycle_repository.py` — service_role list reader
- `web/.../IssuePage.jsx` / `EditorialCallout.jsx` / `contentApi.js` — DTO-driven callout + harness
- Unit + Playwright tests for open/closed/absent

## Decisions Made

- Keep cycle selection in the use-case; adapters expose `list_cycles()` only
- Separate Supabase voting-cycle adapter module (cleaner than folding into IssueRepository)
- By-number responses always omit `voting_cycle`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Supabase adapter as sibling module**
- **Found during:** Task 1
- **Issue:** Plan listed extending `issue_repository.py`; a separate `VotingCycleReader` adapter better matches the new port
- **Fix:** Added `voting_cycle_repository.py` + public export; wired in `live.py`
- **Files modified:** `supabase-integration/.../voting_cycle_repository.py`, `__init__.py`, `live.py`
- **Commit:** `84d4e58`

## Known Stubs

None that block ISSUE-02 — Phase 3 still owns vote cast/change; `/voting` page remains mock ballot (intentional D-32).

## Threat Flags

None — no new write endpoints or trust-boundary expansion beyond read-only cycle fields (T-02-01 accept).

## Self-Check: PASSED

- Created files present: domain/port/adapter, EditorialCallout, SUMMARY
- Commits present: `4a78dee`, `84d4e58`, `4879cfb`, `750776e`
- ROADMAP: 02-05 checked; 02-06 still open (5/6)
