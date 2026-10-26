---
phase: 03-voting-cycle
plan: 04
subsystem: api
tags: [fastapi, react, playwright, voting, cas, 409, toast, tdd]

requires:
  - phase: 03-voting-cycle
    provides: VoteRepository + cast_vote tracer (03-01); BallotSnapshot leaders (03-03); SPA votingApi/VotingPage (03-05/03-06)
provides:
  - A→B upsert while open with tallies in BallotSnapshot (VOTE-03)
  - HTTP 409 detail {code, message, ballot} for CYCLE_CLOSED and VOTE_CONFLICT
  - SPA read-only flip on closed mid-submit; conflict adopt-server banner
  - Toast «Голос сохранён» / «Голос изменён» with timed fade; GET ServiceUnavailable vs POST ErrorPanel
affects: [phase-04, verify-work]

actuals:
  tokens: 12055
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "409 detail.ballot carries full BallotSnapshot for SPA one-shot adopt (D-51/D-54)"
    - "expected_updated_at JSON CAS — no ETag headers"
    - "GET fail → ServiceUnavailable splash; POST fail → ErrorPanel (never splash for mutation)"

key-files:
  created: []
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/application/use_cases/cast_vote.py
    - backend/src/backend/interface/http/routes/voting.py
    - tests/unit/test_cast_vote.py
    - tests/unit/test_http_voting.py
    - web/src/services/votingApi.js
    - web/src/pages/VotingPage.jsx
    - tests/web-app.spec.js

key-decisions:
  - "Domain errors carry optional ballot; HTTP serializes via BallotSnapshotResponse.model_dump"
  - "Conflict banner uses role=alert so vote status role=status stays unique for a11y queries"
  - "Mock harnesses: CLOSE_ON_SUBMIT, CONFLICT_ON_SUBMIT, FAIL_NEXT_BALLOT (sticky until clear)"

patterns-established:
  - "cast_vote attaches ballot on closed/CAS before re-raise; map only at HTTP edge to 409"
  - "submitVote parses live 409 detail.code + detail.ballot into VoteSubmitError"
  - "Toast dismiss ~4s mirrors PlatformProofBanner DISMISS_MS pattern"

requirements-completed: [VOTE-01, VOTE-03]

coverage:
  - id: D1
    description: "A→B while open updates personal_vote.topic_id and moves tallies; one row"
    requirement: VOTE-03
    verification:
      - kind: unit
        ref: "tests/unit/test_cast_vote.py#test_cast_vote_changes_topic_a_to_b_while_open"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_post_change_a_to_b_returns_200_with_moved_tallies"
        status: pass
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows Голос сохранён then changes vote A→B with Голос изменён"
        status: pass
    human_judgment: false
  - id: D2
    description: "Closed-cycle POST → 409 CYCLE_CLOSED with Russian message + detail.ballot; SPA flips read-only"
    requirement: VOTE-03
    verification:
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_post_closed_returns_409_cycle_closed_with_ballot"
        status: pass
      - kind: automated_ui
        ref: "tests/web-app.spec.js#flips to closed banner when submit races cycle close"
        status: pass
    human_judgment: false
  - id: D3
    description: "CAS mismatch → 409 VOTE_CONFLICT; SPA conflict banner adopts server radios/status"
    requirement: VOTE-03
    verification:
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_post_cas_mismatch_returns_409_vote_conflict_with_ballot"
        status: pass
      - kind: automated_ui
        ref: "tests/web-app.spec.js#adopts server vote on VOTE_CONFLICT response"
        status: pass
    human_judgment: false
  - id: D4
    description: "POST network/5xx → ErrorPanel «Ошибка сохранения» + Retry; selection kept; no splash"
    requirement: VOTE-01
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows vote error state and recovers on retry"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ballot GET failure → ServiceUnavailable splash + Повторить (D-55)"
    requirement: VOTE-01
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows ServiceUnavailable splash on ballot GET failure with Повторить"
        status: pass
    human_judgment: false
  - id: D6
    description: "Same-topic repeat open → 200 idempotent; toasts Голос сохранён / Голос изменён"
    requirement: VOTE-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_post_same_topic_repeat_returns_200"
        status: pass
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows Голос сохранён then changes vote A→B with Голос изменён"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-20
status: complete
---

# Phase 03 Plan 04: Closed 409, CAS, Toasts & Phase Gate Summary

**VOTE-03 complete: A→B upsert, closed/CAS 409+ballot with SPA adopt, mutation ErrorPanel vs GET splash, save toasts — phase voting gate green under mocks.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-09-20T16:44:26Z
- **Completed:** 2026-09-20T16:53:00Z
- **Tasks:** 3/3
- **Files modified:** 8

## Accomplishments

- Server: A→B while open; closed → `VotingCycleClosedError`+ballot → HTTP 409 `CYCLE_CLOSED`; CAS → `VoteConflictError`+ballot → 409 `VOTE_CONFLICT`
- Client: parse 409; flip read-only on close race; conflict banner adopts server vote; toast fade; GET splash vs POST ErrorPanel
- Phase gate: 26 unit + 12 Playwright voting-tagged tests green; no «Голос принят» / «Ваш голос: не отдан» expectations

## Task Commits

1. **Task 1 RED:** `d5387b8` — test(03-04): add failing tests for A→B, closed 409, CAS conflict
2. **Task 1 GREEN:** `4ee40cf` — feat(03-04): implement A→B, closed 409, CAS conflict with ballot
3. **Task 2 RED:** `a38f436` — test(03-04): add failing Playwright for toast, 409 flip, GET splash
4. **Task 2 GREEN:** `53e4d76` — feat(03-04): SPA 409 flip, conflict adopt, toast fade, GET splash
5. **Task 3:** verify-only (no code commit) — phase gate already green after Task 2

**Plan metadata:** `4a5e35d` (docs: complete plan)

## Files Created/Modified

- `backend/src/backend/domain/errors.py` — optional `ballot` on closed/conflict errors
- `backend/src/backend/application/use_cases/cast_vote.py` — rebuild snapshot on closed/CAS
- `backend/src/backend/interface/http/routes/voting.py` — 409 detail `{code,message,ballot}`
- `tests/unit/test_cast_vote.py` / `test_http_voting.py` — A→B, closed, CAS coverage
- `web/src/services/votingApi.js` — 409 parse; close/conflict/GET fail harnesses
- `web/src/pages/VotingPage.jsx` — toast fade, conflict banner, ServiceUnavailable GET path
- `tests/web-app.spec.js` — A→B/toast, close mid-submit, conflict, GET splash

## Decisions Made

- Ballot attached on domain errors in use-case; HTTP only maps to FastAPI 409 dict (no ETag)
- Conflict banner `role="alert"` to avoid colliding with vote `role="status"` queries
- Task 3 produced no file diffs — gate commands recorded below

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Conflict banner role collided with vote status**
- **Found during:** Task 2 (Playwright VOTE_CONFLICT)
- **Issue:** Both conflict banner and status used `role="status"` → strict-mode locator failure
- **Fix:** Conflict banner → `role="alert"`; test targets status via `[role="status"][aria-live="polite"]`
- **Files modified:** `web/src/pages/VotingPage.jsx`, `tests/web-app.spec.js`
- **Commit:** `53e4d76`

## Requirement → Verification Map

| Requirement | Passing commands / refs |
|-------------|-------------------------|
| VOTE-01 | `uv run pytest … test_cast_vote test_http_voting`; Playwright confirm / empty submit / simulateError |
| VOTE-02 | Prior 03-05/03-06; gate grep includes never-voted flows |
| VOTE-03 | Unit A→B + closed/CAS 409; Playwright A→B, close-on-submit, conflict adopt |
| VOTE-04 | Prior 03-06; gate includes «0 материалов» / leader strip |

## Verify Commands (recorded)

```text
uv run pytest tests/unit/test_get_ballot.py tests/unit/test_cast_vote.py tests/unit/test_http_voting.py
# → 26 passed

npx playwright test tests/web-app.spec.js --project=web -g "voting|голос|лидирует|материал|закрыт|Выберите|Изменить" --reporter=line
# → 12 passed
```

## Threat Flags

None — 409 surface and CAS were in plan `<threat_model>` (T-03-05, T-03-10, T-03-11).

## Known Stubs

None — mock harnesses are intentional Playwright fakes (D-56), not incomplete production paths.

## Self-Check: PASSED

- FOUND: modified use-case, routes, votingApi, VotingPage, unit + Playwright tests
- FOUND: commits `d5387b8`, `4ee40cf`, `a38f436`, `53e4d76`
- FOUND: SUMMARY path `.planning/phases/03-voting-cycle/03-04-SUMMARY.md`
