---
phase: 03-voting-cycle
plan: 03
subsystem: api
tags: [ballot-snapshot, leaders, ties, get_ballot, tdd, ports-adapters]

requires:
  - phase: 03-voting-cycle
    provides: BallotSnapshot / get_ballot / BallotLeader from 03-01 tracer
provides:
  - Unit coverage for leaders[] single / ties / hide-when-zero (D-40…43)
  - Empty/null/closed BallotSnapshot shapes for D-48…50 (SPA-ready DTOs)
affects: [03-06-leader-strip-empty-ui]

actuals:
  tokens: 1774
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "leaders[] computed only in get_ballot; no BallotTopic.leading (C3-02)"
    - "D-49 vs D-50 distinguished by cycle null vs cycle present + topics []"

key-files:
  created: []
  modified:
    - tests/unit/test_get_ballot.py

key-decisions:
  - "Leaders/ties/hide-when-zero already in get_ballot from 03-01 — plan 03-03 adds contract tests only"
  - "Closed-cycle GET reuses select_active_voting_cycle (latest closed when no open)"

patterns-established:
  - "Server-only leader math verified by unit tests before SPA strip (03-06)"
  - "Empty snapshot shapes are DTO contracts; Russian copy stays in 03-06"

requirements-completed: [VOTE-02]

coverage:
  - id: D1
    description: "get_ballot leaders[]: all-zero → []; unique max → one BallotLeader; ties → all max titles; no topic.leading"
    requirement: VOTE-02
    verification:
      - kind: unit
        ref: "tests/unit/test_get_ballot.py#test_get_ballot_hide_when_zero_leaders_empty_when_all_tallies_zero"
        status: pass
      - kind: unit
        ref: "tests/unit/test_get_ballot.py#test_get_ballot_computes_leaders_when_tallies_nonzero"
        status: pass
      - kind: unit
        ref: "tests/unit/test_get_ballot.py#test_get_ballot_tie_includes_all_max_leaders"
        status: pass
    human_judgment: false
  - id: D2
    description: "Empty/null/closed snapshot shapes: D-50 null cycle; D-49 open+zero topics; D-48 closed with tallies/leaders"
    requirement: VOTE-03
    verification:
      - kind: unit
        ref: "tests/unit/test_get_ballot.py#test_get_ballot_no_cycle_returns_null_cycle_empty_shape"
        status: pass
      - kind: unit
        ref: "tests/unit/test_get_ballot.py#test_get_ballot_open_cycle_zero_topics_empty_shape"
        status: pass
      - kind: unit
        ref: "tests/unit/test_get_ballot.py#test_get_ballot_closed_cycle_still_computes_tallies_and_leaders"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-09-20
status: complete
---

# Phase 03 Plan 03: Leaders & Empty Snapshot Shapes Summary

**Unit-locked get_ballot leaders[] (single/tie/hide-when-zero) and D-48…50 empty/closed BallotSnapshot shapes — production logic already from 03-01; SPA copy deferred to 03-06.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-20T15:56:49Z
- **Completed:** 2026-09-20T16:00:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Contract tests for D-40/42/43: unique leader, multi-tie leaders[], empty leaders when all tallies zero
- Contract tests for D-48/49/50: closed tallies+leaders, open zero-topics, null-cycle empty snapshot
- Confirmed no `leading` field on `BallotTopic` (C3-02 / T-03-09)

## Task Commits

Each task was committed atomically:

1. **Task 1: get_ballot leaders — single, ties, hide-when-zero** - `6a6f001` (test)
2. **Task 2: get_ballot empty shapes — no cycle / zero topics** - `36898cb` (test)

**Plan metadata:** `fd00b14` (docs: complete plan)

## Files Created/Modified

- `tests/unit/test_get_ballot.py` — leaders + empty/closed snapshot shape coverage (7 tests)

## Decisions Made

- No production change to `get_ballot.py` — `_compute_leaders` and null-cycle early return already correct from 03-01
- VOTE-03/VOTE-04 remain open in REQUIREMENTS until A→B/closed reject (03-04) and SPA dek/counts (03-06); this plan only ships DTO shapes

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written.

### TDD note (feature pre-existed)

**1. [Investigation - fail-fast RED]** Leaders/empty shapes already green from 03-01
- **Found during:** Task 1 & 2 RED
- **Issue:** New contract tests passed immediately — `_compute_leaders` + null-cycle return already implemented in tracer
- **Fix:** No GREEN feat commit; ship test-only commits locking the contract for 03-06
- **Files modified:** `tests/unit/test_get_ballot.py` only
- **Verification:** `uv run pytest tests/unit/test_get_ballot.py -x` → 7 passed
- **Committed in:** `6a6f001`, `36898cb`

**Total deviations:** 0 auto-fixes; 1 documented pre-existing GREEN (expected after 03-01)
**Impact on plan:** Scope unchanged — plan goal was contract coverage before SPA

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 03-06: leader strip + empty/closed Russian copy consuming these DTO shapes
- 03-02 Supabase adapter and 03-04 A→B/CAS remain independent of this plan
- No stubs introduced

## TDD Gate Compliance

- RED commits with failing tests: skipped — implementation already present from `b58dffb` (03-01)
- GREEN feat commits: not required (no production delta)
- Test commits present: `6a6f001`, `36898cb`
- Verify: `uv run pytest tests/unit/test_get_ballot.py -x` → 7 passed

## Self-Check: PASSED

- FOUND: tests/unit/test_get_ballot.py
- FOUND: backend/src/backend/application/use_cases/get_ballot.py (unchanged, verified)
- FOUND commits: 6a6f001, 36898cb
- MISSING feat commits: intentional (pre-existing GREEN)

---
*Phase: 03-voting-cycle*
*Completed: 2026-09-20*
