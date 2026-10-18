---
phase: 02-issue-materials-archive
plan: 02
subsystem: database
tags: [supabase, postgres, ports-adapters, seed, service-role, pytest]

requires:
  - phase: 02-issue-materials-archive
    provides: AppContainer.issues port, get_current_issue, InMemoryIssueRepository placeholder in live.py
provides:
  - Idempotent Phase 2 SQL seed (issues 13+14, materials incl. rag-systems, voting cycle)
  - SupabaseIssueRepository + SupabaseMaterialRepository (get_by_slug)
  - live.py service_role wiring for issues/materials (closes RESEARCH pitfall 3)
  - Runbook §4b apply-once + confirmed PostgREST apply on shared VM
affects:
  - 02-03 archive list (list_past_published + past issue №13)
  - 02-04 material reader (get_by_slug)
  - 02-05 voting cycle stub (seeded voting_cycles row)

actuals:
  tokens: 13029
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - Idempotent ON CONFLICT seed + WHERE NOT EXISTS for tables without natural unique keys
    - Offline FakeSupabaseClient contract tests mirroring Phase 1 ping/profile stubs
    - service_role content adapters constructed only in composition/live.py

key-files:
  created:
    - supabase-integration/migrations/002_phase2_issue_seed.sql
    - supabase-integration/src/supabase_integration/issue_repository.py
    - supabase-integration/src/supabase_integration/material_repository.py
    - tests/unit/test_supabase_issue_repository_contract.py
  modified:
    - docs/agents/local-platform-runbook.md
    - supabase-integration/src/supabase_integration/__init__.py
    - backend/src/backend/composition/live.py
    - backend/src/backend/application/ports/issue_repository.py
    - backend/src/backend/application/ports/material_repository.py
    - backend/src/backend/tests_support/in_memory.py
    - tests/unit/test_live_container_wiring.py

key-decisions:
  - "Seed applied via Supabase MCP PostgREST insert (service_role) because raw_sql needs POSTGRES_URL"
  - "voting_cycles idempotency uses WHERE NOT EXISTS on opens_at/closes_at (no unique constraint)"
  - "MaterialRepository.get_by_slug + ready-only related filter landed for MAT-01 readiness"

patterns-established:
  - "Supabase content adapters: Protocol client injection, PersistenceError at boundary, export from __init__"
  - "Live wiring assertions reject InMemory* for materials/issues when APP_CONTAINER=live"

requirements-completed: [ISSUE-01, MAT-01]

coverage:
  - id: D1
    description: "Idempotent checked-in seed creates 2 published issues + rag-systems + voting cycle"
    requirement: ISSUE-01
    verification:
      - kind: other
        ref: node -e seed-file checks (rag-systems, ON CONFLICT, no TRUNCATE)
        status: pass
      - kind: manual_procedural
        ref: shared VM counts after MCP PostgREST apply (issues=2, rag-systems, cycles=1)
        status: pass
    human_judgment: true
    rationale: "Shared VM seed presence requires operator-confirmed row counts; cannot be fully proven offline"
  - id: D2
    description: "build_live_container wires SupabaseIssueRepository + SupabaseMaterialRepository via service_role"
    requirement: MAT-01
    verification:
      - kind: unit
        ref: tests/unit/test_live_container_wiring.py#test_build_live_container_wires_supabase_adapters
        status: pass
    human_judgment: false
  - id: D3
    description: "Offline contract: get_latest_published ordering + get_by_slug with tags/relations"
    requirement: MAT-01
    verification:
      - kind: unit
        ref: tests/unit/test_supabase_issue_repository_contract.py
        status: pass
    human_judgment: false
  - id: D4
    description: "Runbook §4b documents apply-once and records successful PostgREST apply method"
    verification:
      - kind: other
        ref: docs/agents/local-platform-runbook.md#4b
        status: pass
    human_judgment: false

duration: 45min
completed: 2026-09-20
status: complete
---

# Phase 02 Plan 02: Seed + Live Supabase Adapters Summary

**Idempotent mock.js→SQL seed on shared VM plus service_role Issue/Material adapters replacing live in-memory content**

## Performance

- **Duration:** 45min (includes blocking-human seed gate)
- **Started:** 2026-09-20T09:49:00Z
- **Completed:** 2026-09-20T10:32:00Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- Checked-in `002_phase2_issue_seed.sql`: issues №13+№14, six ready materials (Playwright slugs), tags/relations, one open voting cycle — `ON CONFLICT` / no wipe SQL
- `SupabaseIssueRepository` (`get_latest_published`, `get_by_number`, `list_past_published`) and `SupabaseMaterialRepository` (`get`, `get_by_slug`, `save`) with PersistenceError boundary
- `build_live_container` wires service_role adapters for issues + materials (closes RESEARCH pitfall 3)
- Operator applied seed via MCP PostgREST insert; verified published issues=2, materials=6 incl. `rag-systems`, voting_cycles=1

## Task Commits

Each task was committed atomically:

1. **Task 1: Idempotent Phase 2 seed SQL** - `33bb43d` (feat)
2. **Task 2: Adapters + live wiring (TDD)** - `377f5ce` (test RED), `69103fe` (feat GREEN)
3. **Task 3: [BLOCKING] Apply seed** - operator `applied` via MCP PostgREST; runbook note + this SUMMARY in metadata commit

**Plan metadata:** (this docs commit)

## Files Created/Modified

- `supabase-integration/migrations/002_phase2_issue_seed.sql` — idempotent D-25/D-27 seed
- `supabase-integration/src/supabase_integration/issue_repository.py` — live issue reads
- `supabase-integration/src/supabase_integration/material_repository.py` — live material reads + `get_by_slug`
- `backend/src/backend/composition/live.py` — service_role wiring for issues/materials
- `backend/src/backend/application/ports/issue_repository.py` — extended port for archive readiness
- `backend/src/backend/application/ports/material_repository.py` — `get_by_slug`
- `backend/src/backend/tests_support/in_memory.py` — matching fakes
- `tests/unit/test_supabase_issue_repository_contract.py` — offline stub contracts
- `tests/unit/test_live_container_wiring.py` — asserts Supabase* not InMemory*
- `docs/agents/local-platform-runbook.md` — §4b apply-once + Applied note

## Decisions Made

- Prefer PostgREST MCP insert when `raw_sql` / `POSTGRES_URL` unavailable; record method in runbook
- Voting cycle seed uses `WHERE NOT EXISTS` on fixed window timestamps (no unique key to `ON CONFLICT`)
- Do not pollute shared VM with draft materials — draft 404 cases stay in unit fakes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Seed verify rejected `TRUNCATE` word in SQL comments**
- **Found during:** Task 1
- **Issue:** Automated verify `/TRUNCATE/i` matched a caution comment
- **Fix:** Reworded comment to “no table wipes” without the forbidden token
- **Files modified:** `supabase-integration/migrations/002_phase2_issue_seed.sql`
- **Verification:** node seed-file check exits 0
- **Committed in:** `33bb43d`

**2. [Rule 1 - Bug] Fake client `.not_` must be a property**
- **Found during:** Task 2 GREEN
- **Issue:** Real supabase-py exposes `.not_.is_`; method-style fake broke adapters
- **Fix:** `@property def not_` on FakeQuery
- **Files modified:** `tests/unit/test_supabase_issue_repository_contract.py`
- **Verification:** 15 unit tests pass
- **Committed in:** `69103fe`

---

**Total deviations:** 2 auto-fixed (2 Rule 1)
**Impact on plan:** Required for verify/green; no scope creep

## Issues Encountered

- Task 3 non-interactive `supabase db push` blocked: no `SUPABASE_ACCESS_TOKEN`, CLI not on PATH, MCP `raw_sql` unavailable without `POSTGRES_URL`. Operator applied via PostgREST insert instead — accepted.

## Auth Gates

- Task 3 human-action gate: shared VM seed apply. Outcome: **applied** (PostgREST service_role); counts verified by operator.

## User Setup Required

None beyond already-documented shared VM seed in runbook §4b (apply completed 2026-09-20).

## Next Phase Readiness

- Live `APP_CONTAINER=live` can serve published issues/materials from shared DB
- 02-03 can use `list_past_published` / past issue №13; 02-04 can call `get_by_slug('rag-systems')`; 02-05 can read seeded voting cycle

## Self-Check: PASSED

- FOUND: `supabase-integration/migrations/002_phase2_issue_seed.sql`
- FOUND: `supabase-integration/src/supabase_integration/issue_repository.py`
- FOUND: `supabase-integration/src/supabase_integration/material_repository.py`
- FOUND: `33bb43d`, `377f5ce`, `69103fe`
- FOUND: runbook Applied note (PostgREST)

---
*Phase: 02-issue-materials-archive*
*Completed: 2026-09-20*
