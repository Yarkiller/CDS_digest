---
phase: 10-cli-composition-uat
plan: 03
subsystem: database
tags: [migration, persist_draft_and_enqueue, already_saved, D-09, D-12, CLI-02]

requires:
  - phase: 10-cli-composition-uat
    provides: PersistResult.already_saved on port + D-09/D-12 CONTEXT decisions
  - phase: 09-draft-persist-shortlist-enqueue
    provides: migration 007 persist_draft_and_enqueue baseline
provides:
  - Migration 008 CREATE OR REPLACE with stored materials.slug + already_saved
  - Offline SQL contract tests for 008 (not yet applied to shared VM)
affects:
  - 10-05 adapter already_saved parse and live schema push
  - 10-04 UAT re-run already_saved true / stored slug lines

actuals:
  tokens: 1971
  tasks: 2
  commits: 2

plan_head_before: 97dcff37211759d49d0e74fe1e3c7f5cbda16618
plan_head_after: 5404a4dfae7bede37f8b57a1f6c494130d33d1dd

tech-stack:
  added: []
  patterns:
    - CREATE OR REPLACE RPC amend without editing applied migrations
    - SQL-as-text contract tests strip -- comments before assertions

key-files:
  created:
    - supabase-integration/migrations/008_phase10_persist_already_saved.sql
    - tests/unit/test_phase10_migration_008.py
  modified: []

key-decisions:
  - "Proceed with one-way RPC amend for stored slug + already_saved (D-09, D-12)"
  - "Conflict slug via select m.slug into v_slug; insert path keeps p_slug"

patterns-established:
  - "Pattern: Phase N+1 migration CREATE OR REPLACE amends RPC return shape; never edit applied 007"
  - "Pattern: already_saved derived from v_inserted (0→true, else false); no Python pre-check"

requirements-completed: [CLI-02]

coverage:
  - id: D1
    description: Migration 008 CREATE OR REPLACE persist_draft_and_enqueue with security invoker and service_role-only execute
    requirement: CLI-02
    verification:
      - kind: unit
        ref: "tests/unit/test_phase10_migration_008.py::test_migration_008_exists_and_replaces_persist_rpc"
        status: pass
    human_judgment: false
  - id: D2
    description: Conflict return uses stored materials.slug and already_saved true; insert returns already_saved false
    requirement: CLI-02
    verification:
      - kind: unit
        ref: "tests/unit/test_phase10_migration_008.py::test_migration_008_conflict_returns_stored_materials_slug_not_caller_p_slug"
        status: pass
    human_judgment: false
  - id: D3
    description: No truncate/drop table in 008; grants revoke public/anon/authenticated
    requirement: CLI-02
    verification:
      - kind: unit
        ref: "tests/unit/test_phase10_migration_008.py::test_migration_008_has_no_destructive_wipes"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-09-29
status: complete
---

# Phase 10 Plan 03: Migration 008 authoring Summary

**Authored `008_phase10_persist_already_saved.sql` so conflict returns stored `materials.slug` and `already_saved`, with offline SQL contract tests green (live push deferred to 10-05).**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-09-29T18:12:39Z
- **Completed:** 2026-09-29T18:25:00Z
- **Tasks:** 2/2 (decision checkpoint + TDD author)
- **Files modified:** 2 created

## Accomplishments

- One-way RPC amend decision accepted (`proceed`) before writing 008
- Migration 008 CREATE OR REPLACE mirrors 007 body with D-09/D-12 return changes only
- Five SQL-as-text contract tests green; 007 left untouched; no `db push`

## Task Commits

1. **Task 1: Checkpoint decision (proceed)** — no commit (decision only)
2. **Task 2 RED: SQL contract tests** — `577a0e5` (test)
3. **Task 2 GREEN: migration 008** — `5404a4d` (feat)

## Files Created/Modified

- `supabase-integration/migrations/008_phase10_persist_already_saved.sql` — CREATE OR REPLACE `persist_draft_and_enqueue` with stored slug + `already_saved`
- `tests/unit/test_phase10_migration_008.py` — offline SQL contract (existence, conflict slug, already_saved both paths, grants, no wipes)

## Decisions Made

- **proceed** on one-way migration 008 (stored `materials.slug` + `already_saved`) per D-09/D-12
- Conflict path selects `m.slug` into `v_slug`; insert success still returns caller `p_slug` with `already_saved` false

## Deviations from Plan

None - plan executed exactly as written after the cleared decision checkpoint.

## TDD Gate Compliance

- **RED:** `test_migration_008_exists_and_replaces_persist_rpc` failed with `008_phase10_persist_already_saved.sql must exist`; `tdd-red-evidence` → `RED_EVIDENCE_OK`
- **GREEN:** Migration authored; `uv run pytest tests/unit/test_phase10_migration_008.py -x` → 5 passed
- **REFACTOR:** Not needed

## Auth Gates

None.

## Known Stubs

None — migration is complete SQL; live apply and adapter `_RESULT_KEYS` parse are intentionally owned by 10-05.

## Threat Flags

None beyond plan threat_model (named RPC params + service_role-only grants retained).

## Self-Check: PASSED

- FOUND: `supabase-integration/migrations/008_phase10_persist_already_saved.sql`
- FOUND: `tests/unit/test_phase10_migration_008.py`
- FOUND: commit `577a0e5`
- FOUND: commit `5404a4d`
