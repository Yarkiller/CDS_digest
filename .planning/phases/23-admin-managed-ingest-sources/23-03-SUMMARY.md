---
phase: 23-admin-managed-ingest-sources
plan: 03
subsystem: database
tags: [supabase, migration, rls, ports-adapters, ingest-sources, composition]

requires:
  - phase: 23-admin-managed-ingest-sources
    provides: IngestSourceRepository port, use-cases, HTTP reject/enable/delete (23-01/23-02)
provides:
  - Idempotent migration 012 creating public.pipeline_ingest_sources with RLS deny-by-default (D-16/D-17)
  - SupabaseIngestSourceRepository implementing the port with PersistenceError boundary
  - Live composition wire: ingest_sources=SupabaseIngestSourceRepository(admin_client)
  - Runbook §4i apply/verify; Applied stamped after shared-VM operator apply
affects: [23-04, 24-scheduled-ingestion]

actuals:
  tokens: 6902
  tasks: 3
  commits: 3
  plan_head_before: a65259fc1f71c6550857f943853ccd08b4add358
  plan_head_after: ffb8dd94a310fa552b3a8a7133fff23d23b78f47

tech-stack:
  added: []
  patterns:
    - "New pipeline_ingest_sources table (not ingestion_sources) with RLS enabled and zero policies"
    - "Supabase adapter maps SDK Exception → PersistenceError; table name only pipeline_ingest_sources"
    - "BLOCKING shared-VM apply gated via runbook §4i Applied line (T-23-14)"

key-files:
  created:
    - supabase-integration/migrations/012_phase23_ingest_sources.sql
    - supabase-integration/src/supabase_integration/ingest_source_repository.py
    - tests/unit/test_phase23_migration_012.py
    - tests/unit/test_supabase_ingest_source_repository_contract.py
  modified:
    - supabase-integration/src/supabase_integration/__init__.py
    - backend/src/backend/composition/live.py
    - docs/agents/local-platform-runbook.md
    - tests/unit/test_live_container_wiring.py

key-decisions:
  - "D-16/D-17 schema door: new-table-012 — ship public.pipeline_ingest_sources via migration 012 with RLS enabled and zero policies (do not reuse ingestion_sources)"
  - "Operator applied 012 on shared VM (2026-10-17); count(*)=0 accepted; RLS/policy checklist accepted via resume-signal without restate"

patterns-established:
  - "Text-only migration contract tests mirror Phase 16 (011) — never edit 001/011 or their contracts (D-23)"
  - "§4i Applied stamp is the ops proof for live SRC-01 persistence DoD"

requirements-completed: [SRC-01, SRC-03]

coverage:
  - id: D1
    description: "Idempotent migration 012 creates pipeline_ingest_sources with identity PK, kind check, unique (kind, source_id), RLS on, zero policies, no wipe"
    requirement: SRC-01
    verification:
      - kind: unit
        ref: "tests/unit/test_phase23_migration_012.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "SupabaseIngestSourceRepository implements list/add/set_enabled/delete; SDK failures → PersistenceError; exported in __all__"
    requirement: SRC-03
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_ingest_source_repository_contract.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "build_live_container wires SupabaseIngestSourceRepository(admin_client); in-memory build unchanged"
    requirement: SRC-03
    verification:
      - kind: unit
        ref: "tests/unit/test_live_container_wiring.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Migration 012 applied on shared knowledge-db VM; table reachable; empty list OK"
    requirement: SRC-01
    verification:
      - kind: manual_procedural
        ref: "docs/agents/local-platform-runbook.md#4i — Applied (2026-10-17); operator count(*)=0; PostgREST select id limit 5 → []"
        status: pass
    human_judgment: true
    rationale: "Shared-VM DDL apply and RLS/policy catalog checks require operator Studio/psql; raw_sql unavailable without POSTGRES_URL"

duration: 22min
completed: 2026-10-17
status: complete
---

# Phase 23 Plan 03: Migration 012 + Supabase adapter + live wire Summary

**Idempotent `pipeline_ingest_sources` (012) with RLS deny-by-default, `SupabaseIngestSourceRepository` on the live admin client, and shared-VM apply stamped in runbook §4i.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-10-17T17:18:00Z
- **Completed:** 2026-10-17T17:40:00Z
- **Tasks:** 3/3
- **Files modified:** 8

## Accomplishments

- Migration `012_phase23_ingest_sources.sql` creates `public.pipeline_ingest_sources` (identity PK, kind check, unique `(kind, source_id)`, timestamps, `is_enabled` default true, RLS enabled, zero policies) without touching `ingestion_sources` (D-16/D-17, SRC-01).
- `SupabaseIngestSourceRepository` implements the port; SDK exceptions map to `PersistenceError`; exported from `supabase_integration` (SRC-03).
- `build_live_container` wires `SupabaseIngestSourceRepository(admin_client)`; unit contracts green (24 passed).
- **[BLOCKING] apply complete:** operator confirmed «applied» with `count(*) = 0` (empty OK). §4i **Applied (2026-10-17)** stamped. Operator did not restate `relrowsecurity` / `pg_policies` checklist lines — accepted per resume-signal and §4h pattern. Optional PostgREST probe after stamp: `pipeline_ingest_sources` select → `[]` (table reachable). `raw_sql` / `list_rls_policies` unavailable without `POSTGRES_URL` — not blocking.

## Task Commits

Each task was committed atomically (TDD RED→GREEN for Task 2; Task 1 was the D-16/D-17 decision checkpoint with no code commit):

1. **Task 1: Confirm new-table-012 (D-16/D-17)** — decision `new-table-012` (no commit; recorded in STATE)
2. **Task 2: Migration 012 + adapter + live wire** — `a158484` (test RED), `72a5c5e` (feat GREEN)
3. **Task 3: [BLOCKING] Apply migration 012 on shared VM** — `ffb8dd9` (docs: §4i Applied stamp)

**Plan metadata:** _(final docs commit after STATE/ROADMAP update)_

## Files Created/Modified

- `supabase-integration/migrations/012_phase23_ingest_sources.sql` — idempotent DDL + RLS enable, no policies
- `supabase-integration/src/supabase_integration/ingest_source_repository.py` — live adapter
- `supabase-integration/src/supabase_integration/__init__.py` — export + `__all__`
- `backend/src/backend/composition/live.py` — wire ingest_sources to Supabase adapter
- `docs/agents/local-platform-runbook.md` — §4i apply/verify + Applied (2026-10-17)
- `tests/unit/test_phase23_migration_012.py` — text-only migration contract
- `tests/unit/test_supabase_ingest_source_repository_contract.py` — fake-client CRUD + PersistenceError
- `tests/unit/test_live_container_wiring.py` — live ingest_sources type assert (D-24)

## Decisions Made

- Proceeded with **new-table-012** (locked D-16/D-17): new `pipeline_ingest_sources`, not reuse of `ingestion_sources`.
- Live apply accepted on operator «applied» + `count(*)=0`; RLS/policy catalog not re-pasted by operator — documented, not deferred.

## Deviations from Plan

None - plan executed exactly as written (Task 3 closed after human apply resume).

## Issues Encountered

- Supabase MCP `raw_sql` / `list_rls_policies` require `POSTGRES_URL` / `DATABASE_URL` — unavailable in this environment. PostgREST `query` on `pipeline_ingest_sources` returned `[]`, confirming table existence under service client. RLS/policy verify left to operator checklist + migration contract tests.

## User Setup Required

**Shared VM migration apply (complete).** See [docs/agents/local-platform-runbook.md](../../../docs/agents/local-platform-runbook.md) §4i — Applied (2026-10-17). No further operator action for 23-03.

## Next Phase Readiness

- Live persistence path for SRC-01 is real on knowledge-db; Phase 23-04 (SPA ADUX-10 / UI) can assume the table and adapter exist.
- Phase 24 scheduled ingestion can read enabled rows via service_role without widening RLS.

## Self-Check: PASSED

- FOUND: `supabase-integration/migrations/012_phase23_ingest_sources.sql`
- FOUND: `supabase-integration/src/supabase_integration/ingest_source_repository.py`
- FOUND: `docs/agents/local-platform-runbook.md` (§4i Applied 2026-10-17)
- FOUND: commits `a158484`, `72a5c5e`, `ffb8dd9`
- FOUND: unit verify 24 passed

---
*Phase: 23-admin-managed-ingest-sources*
*Completed: 2026-10-17*
