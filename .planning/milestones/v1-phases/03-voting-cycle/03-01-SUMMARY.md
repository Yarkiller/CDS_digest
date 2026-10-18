---
phase: 03-voting-cycle
plan: 01
subsystem: api
tags: [fastapi, jwt, voting, ports-adapters, ballot-snapshot, tdd]

requires:
  - phase: 02-issue-materials-archive
    provides: select_active_voting_cycle, VotingCycleReader, JWT get_principal, PersistenceError→503 pattern
provides:
  - BallotSnapshot / BallotTopic / PersonalVote / BallotLeader domain models
  - VoteRepository Protocol + InMemoryVoteRepository
  - get_ballot + cast_vote use-cases
  - GET /voting/current + POST /voting/votes (JWT, D-52 snapshot)
  - InvalidVoteError → HTTP 400; PersistenceError → 503 voting_unavailable
affects: [03-02-supabase-votes, 03-03-leaders-ui, 03-04-ab-cas-closed, 03-05-spa-ballot]

actuals:
  tokens: 11135
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "BallotSnapshot as sole voting DTO (GET 200 + POST 200)"
    - "user_id from claims.sub only — never request body"
    - "PersistenceError→503 detail voting_unavailable (mirror issues_unavailable)"
    - "InvalidVoteError mapped at HTTP edge only → 400 invalid_vote"

key-files:
  created:
    - backend/src/backend/domain/vote.py
    - backend/src/backend/application/ports/vote_repository.py
    - backend/src/backend/application/use_cases/get_ballot.py
    - backend/src/backend/application/use_cases/cast_vote.py
    - backend/src/backend/interface/http/routes/voting.py
    - tests/unit/test_get_ballot.py
    - tests/unit/test_cast_vote.py
    - tests/unit/test_http_voting.py
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/live.py
    - backend/src/backend/interface/http/app.py

key-decisions:
  - "D-52: POST /voting/votes returns full BallotSnapshot (costly reversibility)"
  - "Reuse select_active_voting_cycle; status column is open/closed switch"
  - "live.py keeps InMemoryVoteRepository until 03-02 Supabase adapter"
  - "Same-topic POST is idempotent 200 (VOTE-01 assumption)"

patterns-established:
  - "Vote writes live on VoteRepository — never fold into VotingCycleReader"
  - "No leading bool on BallotTopic; leaders[] computed in get_ballot"
  - "CastVoteRequest extra=forbid blocks client user_id injection (T-03-01/02)"

requirements-completed: [VOTE-01, VOTE-02]

coverage:
  - id: D1
    description: "GET /voting/current returns never-voted BallotSnapshot with personal_vote null and no topic.leading"
    requirement: VOTE-02
    verification:
      - kind: unit
        ref: "tests/unit/test_get_ballot.py#test_get_ballot_never_voted_returns_personal_vote_null_and_topics"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_current_never_voted_returns_snapshot_with_null_personal_vote"
        status: pass
    human_judgment: false
  - id: D2
    description: "POST /voting/votes stores one vote for claims.sub and returns BallotSnapshot with personal_vote (D-52)"
    requirement: VOTE-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cast_vote.py#test_cast_vote_stores_exactly_one_vote_and_returns_snapshot"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_post_vote_returns_snapshot_with_personal_vote"
        status: pass
    human_judgment: false
  - id: D3
    description: "JWT required; PersistenceError on GET maps to 503 voting_unavailable"
    requirement: VOTE-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_current_without_authorization_returns_401"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_current_persistence_error_returns_503_voting_unavailable"
        status: pass
    human_judgment: false
  - id: D4
    description: "Open-path InvalidVoteError (unknown/empty topic) maps to HTTP 400"
    requirement: VOTE-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_voting.py#test_voting_post_unknown_topic_returns_400"
        status: pass
      - kind: unit
        ref: "tests/unit/test_cast_vote.py#test_cast_vote_topic_from_other_cycle_raises_invalid_vote"
        status: pass
    human_judgment: false

duration: 22min
completed: 2026-09-20
status: complete
---

# Phase 03 Plan 01: Voting Ballot Tracer Summary

**JWT-protected GET/POST `/voting` returns BallotSnapshot via VoteRepository → in-memory, with PersistenceError→503 and InvalidVoteError→400 (D-40, D-52).**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-20T15:50:00Z
- **Completed:** 2026-09-20T16:12:00Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Backend vertical slice for VOTE-01/VOTE-02: never-voted GET + confirm-one-vote POST through Ports & Adapters
- `user_id` always `claims.sub`; Pydantic `extra="forbid"` blocks body user injection (T-03-01/02)
- Same-topic repeat is idempotent 200; leaders computed server-side with no `topic.leading`

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): End-to-end ballot tracer tests** - `5d635ec` (test)
2. **Task 1 (GREEN): Ballot GET/POST tracer** - `b58dffb` (feat)
3. **Task 2 (RED): InvalidVoteError → 400 tests** - `d12051f` (test)
4. **Task 2 (GREEN): Map InvalidVoteError to 400** - `b2eea1b` (feat)

**Plan metadata:** `5f3549f` (docs: complete plan)

## Files Created/Modified

- `backend/src/backend/domain/vote.py` — BallotSnapshot DTO family
- `backend/src/backend/domain/errors.py` — VotingCycleClosedError, VoteConflictError, InvalidVoteError
- `backend/src/backend/application/ports/vote_repository.py` — VoteRepository Protocol
- `backend/src/backend/application/use_cases/get_ballot.py` — snapshot + leaders
- `backend/src/backend/application/use_cases/cast_vote.py` — open-path write → snapshot
- `backend/src/backend/tests_support/in_memory.py` — InMemoryVoteRepository
- `backend/src/backend/interface/http/routes/voting.py` — `/voting/current`, `/voting/votes`
- `backend/src/backend/composition/container.py` / `live.py` — AppContainer.votes wiring
- `backend/src/backend/interface/http/app.py` — register voting router
- `tests/unit/test_get_ballot.py`, `test_cast_vote.py`, `test_http_voting.py` — unit/HTTP coverage

## Decisions Made

- D-52 Snapshot on POST (costly) — implemented as planned
- Cycle open/closed via `status`, not wall-clock vs `closes_at`
- Live composition uses InMemoryVoteRepository placeholder until 03-02 SupabaseVoteRepository

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Wire votes on live AppContainer**
- **Found during:** Task 1 (GREEN)
- **Issue:** Adding required `AppContainer.votes` would break `build_live_container` construction
- **Fix:** Temporary `InMemoryVoteRepository()` in `live.py` with comment that 03-02 replaces it
- **Files modified:** `backend/src/backend/composition/live.py`
- **Verification:** container builds; unit suite green
- **Committed in:** `b58dffb`

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** Necessary for composition correctness; no scope creep. SPA/Playwright remain 03-05.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 03-02: SupabaseVoteRepository + migration `003_phase3_voting_ballot.sql`
- Closed/CAS 409 paths deferred to 03-04; SPA honesty to 03-05
- Leaders polish (ties / hide-when-zero UX) deferred to 03-03

## TDD Gate Compliance

- RED commits present: `5d635ec`, `d12051f`
- GREEN commits present after RED: `b58dffb`, `b2eea1b`
- Verify: `uv run pytest tests/unit/test_get_ballot.py tests/unit/test_cast_vote.py tests/unit/test_http_voting.py -x` → 15 passed

## Self-Check: PASSED

- FOUND: backend/src/backend/domain/vote.py
- FOUND: backend/src/backend/application/ports/vote_repository.py
- FOUND: backend/src/backend/application/use_cases/get_ballot.py
- FOUND: backend/src/backend/application/use_cases/cast_vote.py
- FOUND: backend/src/backend/interface/http/routes/voting.py
- FOUND: tests/unit/test_get_ballot.py, test_cast_vote.py, test_http_voting.py
- FOUND commits: 5d635ec, b58dffb, d12051f, b2eea1b

---
*Phase: 03-voting-cycle*
*Completed: 2026-09-20*
