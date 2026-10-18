---
phase: 04-knowledge-razbory
plan: 04
subsystem: api
tags: [razbor, chronology, fastapi, ports-adapters, jwt, tdd, RAZB-01]

requires:
  - phase: 04-knowledge-razbory
    provides: AppContainer/router wiring patterns from 04-01 knowledge tracer
provides:
  - RazborStatus + Razbor frozen entity
  - RazborRepository Protocol + InMemoryRazborRepository (meeting_at DESC NULLS LAST)
  - list_razbors + get_razbor (NotFound stub for 04-06)
  - JWT-gated GET /razbory chronology DTO with empty 200 and 503 mapping
affects:
  - 04-05 RazboryListPage SPA
  - 04-06 razbor detail / notebook
  - 04-08 live Supabase razbor adapter

actuals:
  tokens: 11554
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Razbor list order: meeting_at DESC NULLS LAST then created_at DESC in repository"
    - "HTTP list DTO {items:[{id,title,meeting_at,status}]}; announcement status exposed raw"
    - "PersistenceError → 503 razbory_unavailable (issues/knowledge pattern)"

key-files:
  created:
    - backend/src/backend/domain/razbor.py
    - backend/src/backend/application/ports/razbor_repository.py
    - backend/src/backend/application/use_cases/list_razbors.py
    - backend/src/backend/application/use_cases/get_razbor.py
    - backend/src/backend/interface/http/routes/razbory.py
    - tests/unit/test_http_razbory.py
    - tests/unit/test_razbor_use_cases.py
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/interface/http/app.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/live.py
    - tests/unit/test_http_knowledge_search.py

key-decisions:
  - "List JSON uses items[] (not razbory[]) matching knowledge list shape"
  - "Status serialized as schema enum strings announcement|published for «Анонс» UI later"
  - "get_razbor stub raises RazborNotFoundError only — detail HTTP deferred to 04-06"
  - "live.py keeps InMemoryRazborRepository until Supabase adapter plan"

patterns-established:
  - "Pattern: chronology list empty → 200 items=[]; PersistenceError → 503 *_unavailable"
  - "Pattern: AppContainer.razbors required field; in-memory default for memory + live until adapter"

requirements-completed: [RAZB-01]

coverage:
  - id: D1
    description: Authenticated GET /razbory returns chronology items with id/title/meeting_at/status including announcement
    requirement: RAZB-01
    verification:
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_list_returns_chronology_items_including_announcement
        status: pass
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_list_without_authorization_returns_401
        status: pass
    human_judgment: false
  - id: D2
    description: Ordering is meeting_at DESC NULLS LAST then created_at DESC
    requirement: RAZB-01
    verification:
      - kind: unit
        ref: tests/unit/test_razbor_use_cases.py#test_list_razbors_orders_meeting_at_desc_nulls_last_then_created_at
        status: pass
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_list_orders_null_meeting_at_last
        status: pass
    human_judgment: false
  - id: D3
    description: Empty repository returns HTTP 200 with items=[]
    requirement: RAZB-01
    verification:
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_list_empty_returns_200_with_empty_items
        status: pass
    human_judgment: false
  - id: D4
    description: PersistenceError on GET /razbory maps to 503 razbory_unavailable
    requirement: RAZB-01
    verification:
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_list_persistence_error_returns_503_unavailable
        status: pass
    human_judgment: false

duration: 3min
completed: 2026-09-21
status: complete
---

# Phase 04 Plan 04: Razbor List Backend Tracer Summary

**JWT-gated `GET /razbory` chronology via RazborRepository → list_razbors, with empty 200 and 503 unavailable (RAZB-01 / D-66 / D-69).**

## Performance

- **Duration:** 3min
- **Started:** 2026-09-21T04:42:28Z
- **Completed:** 2026-09-21T04:45:07Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Domain `Razbor` / `RazborStatus` + port + thin `list_razbors` / stub `get_razbor`
- In-memory repo orders `meeting_at DESC NULLS LAST`, then `created_at DESC`
- HTTP list DTO `{items:[{id,title,meeting_at,status}]}`; JWT required; empty → 200; PersistenceError → 503

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): End-to-end razbor list tests** - `a0659d3` (test)
2. **Task 1 (GREEN): Implement GET /razbory tracer** - `0c97f0c` (feat)
3. **Task 2 (RED): Empty/unavailable HTTP tests** - `76633e5` (test)
4. **Task 2 (GREEN): Map PersistenceError → 503** - `1b07b44` (feat)

**Plan metadata:** (pending docs commit)

_Note: TDD tasks used test → feat commit pairs_

## Files Created/Modified

- `backend/src/backend/domain/razbor.py` — RazborStatus + frozen Razbor
- `backend/src/backend/domain/errors.py` — RazborNotFoundError
- `backend/src/backend/application/ports/razbor_repository.py` — list_for_reader + get
- `backend/src/backend/application/use_cases/list_razbors.py` — thin list
- `backend/src/backend/application/use_cases/get_razbor.py` — NotFound stub for 04-06
- `backend/src/backend/tests_support/in_memory.py` — InMemoryRazborRepository
- `backend/src/backend/interface/http/routes/razbory.py` — GET /razbory
- `backend/src/backend/interface/http/app.py` — register razbory router
- `backend/src/backend/composition/container.py` — razbors field + in-memory default
- `backend/src/backend/composition/live.py` — InMemoryRazborRepository until adapter
- `tests/unit/test_http_razbory.py` — HTTP contract
- `tests/unit/test_razbor_use_cases.py` — ordering + get stub
- `tests/unit/test_http_knowledge_search.py` — AppContainer signature (Rule 3)

## Decisions Made

- List payload uses `items[]` consistent with knowledge search
- Announcement rows ship `status: "announcement"` for SPA «Анонс» label in 04-05
- Detail/notebook routes deferred to 04-06; get_razbor NotFound only

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] AppContainer gained required `razbors` — live + knowledge HTTP harness**
- **Found during:** Task 1 (GREEN)
- **Issue:** Missing `razbors=` breaks `build_live_container` and manual `AppContainer(...)` in knowledge HTTP tests
- **Fix:** Wire `InMemoryRazborRepository()` in `live.py` and `test_http_knowledge_search.py`
- **Files modified:** `backend/src/backend/composition/live.py`, `tests/unit/test_http_knowledge_search.py`
- **Verification:** `uv run pytest tests/unit/test_live_container_wiring.py tests/unit/test_http_knowledge_search.py` passed
- **Committed in:** `0c97f0c`

**Total deviations:** 1 auto-fixed (Rule 3)
**Impact on plan:** Necessary for composition signature; no SPA scope creep

## Issues Encountered

None beyond the live/knowledge wiring fix above.

## TDD Gate Compliance

- RED `test(04-04)` commits: `a0659d3`, `76633e5`
- GREEN `feat(04-04)` commits: `0c97f0c`, `1b07b44`
- Unavailable mapping landed briefly in tracer then removed for Task 2 RED, restored in GREEN

## Known Stubs

| File | Stub | Reason |
|------|------|--------|
| `get_razbor` | NotFound only; no detail HTTP | Detail/notebook/metrics owned by 04-06 |
| `live.py` razbors | `InMemoryRazborRepository()` | Supabase adapter later (04-08 / live wiring) |

## Threat Flags

None beyond plan threat model — JWT `get_principal` gate implemented (T-04-07).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave-2 SPA (`04-05`) can call `GET /razbory` with JWT
- Detail plan (`04-06`) can extend `razbory.py` + fill `get_razbor`
- Live SQL razbor adapter remains deferred

## Self-Check: PASSED

- FOUND: `backend/src/backend/domain/razbor.py`
- FOUND: `backend/src/backend/application/ports/razbor_repository.py`
- FOUND: `backend/src/backend/interface/http/routes/razbory.py`
- FOUND: `tests/unit/test_http_razbory.py`
- FOUND: `tests/unit/test_razbor_use_cases.py`
- FOUND: commits `a0659d3`, `0c97f0c`, `76633e5`, `1b07b44`

---
*Phase: 04-knowledge-razbory*
*Completed: 2026-09-21*
