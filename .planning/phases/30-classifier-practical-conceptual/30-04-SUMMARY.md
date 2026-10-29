---
phase: 30-classifier-practical-conceptual
plan: 04
subsystem: database
tags: [topic-kind, migration-014, persist_draft_and_enqueue, postgres, tdd, kind-01]

requires:
  - phase: 30-classifier-practical-conceptual
    provides: MaterialDraft.topic_kind closed set (practical | conceptual) from Plan 01
provides:
  - materials.topic_kind text NOT NULL DEFAULT conceptual with materials_topic_kind_check
  - persist_draft_and_enqueue 13-arg (p_topic_kind) after DROP of live 12-arg
  - SupabaseDraftPersister._rpc_params p_topic_kind
  - runbook §4l Applied 2026-10-29 on shared knowledge-db VM
affects: [31-tavily-quota, 32-pass-2-enricher]

actuals:
  tokens: 7644
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - DROP exact-arity FUNCTION then CREATE (never CREATE OR REPLACE when adding an argument)
    - Postgres 42P13: every parameter after the first DEFAULT must also have DEFAULT
    - DROP+CREATE+GRANT of an arity-changing RPC in one transaction
    - text + CHECK for closed topic_kind; no CREATE TYPE ENUM

key-files:
  created:
    - supabase-integration/migrations/014_phase30_materials_topic_kind.sql
    - tests/unit/test_phase30_migration_014.py
  modified:
    - ingestion-service/src/ingestion_service/adapters/supabase_persist.py
    - tests/unit/test_supabase_draft_persister_contract.py
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "DROP 12-arg persist_draft_and_enqueue then CREATE 13-arg with p_topic_kind (drop-then-create-13; KIND-01, D-01, T-30-06)"
  - "42P13: p_batch_size int default null so trailing defaults are legal; DROP+CREATE+GRANT share one transaction"
  - "Live apply 2026-10-29 Studio SQL Editor on shared knowledge-db VM; operator screenshot n=1 pronargs=13"

patterns-established:
  - "Pattern: additive column IF NOT EXISTS + DO-block CHECK; RPC arity change is DROP then CREATE"
  - "Pattern: runbook §4l Applied records operator screenshot proof; never db reset"

requirements-completed: [KIND-01]

coverage:
  - id: D1
    description: "Migration 014 SQL contract: ADD COLUMN topic_kind, DO-block CHECK, DROP 12-arg, CREATE 13-arg with p_topic_kind, service_role grant, no ENUM, 007/008/009 unmodified (KIND-01, D-01, T-30-04, T-30-06)"
    requirement: KIND-01
    verification:
      - kind: unit
        ref: tests/unit/test_phase30_migration_014.py
        status: pass
    human_judgment: false
  - id: D2
    description: "SupabaseDraftPersister._rpc_params forwards draft.topic_kind as p_topic_kind (default conceptual; practical override) (KIND-01)"
    requirement: KIND-01
    verification:
      - kind: unit
        ref: tests/unit/test_supabase_draft_persister_contract.py
        status: pass
    human_judgment: false
  - id: D3
    description: "Migration 014 applied on shared knowledge-db VM: one persist_draft_and_enqueue with pronargs=13 (KIND-01, T-30-06)"
    requirement: KIND-01
    verification:
      - kind: other
        ref: docs/agents/local-platform-runbook.md §4l Applied 2026-10-29; operator screenshot pg_proc n=1 pronargs=13
        status: pass
    human_judgment: false
    rationale: "Operator provided Studio screenshot n=1 pronargs=13 after re-apply of fixed 014. Live VM cannot be auto-passed from unit tests. Column+CHECK were not re-pasted; first-run 0-row ADD COLUMN / DO-block plus successful 13-arg CREATE after the 42P13 fix are the evidence."

duration: 20min
completed: 2026-10-29
status: complete
---

# Phase 30 Plan 04: topic_kind persist Summary

**Additive `materials.topic_kind` plus 13-arg `persist_draft_and_enqueue(p_topic_kind)` via DROP-then-CREATE, applied on the shared knowledge-db VM (`n=1`, `pronargs=13`)**

## Performance

- **Duration:** 20 min active (wall clock ~14 h including blocking-human apply)
- **Started:** 2026-10-29T03:38:20Z
- **Completed:** 2026-10-29T17:55:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Migration `014_phase30_materials_topic_kind.sql` ADDs `public.materials.topic_kind text NOT NULL DEFAULT 'conceptual'` and a DO-block CHECK `materials_topic_kind_check` (`practical` | `conceptual`) (KIND-01, D-01).
- Live 12-arg `persist_draft_and_enqueue` is DROPped, then CREATE 13-arg with `p_topic_kind`; INSERT writes `topic_kind`; `ON CONFLICT DO NOTHING` and `already_saved` branches survive; grant execute to `service_role` only (T-30-04, T-30-06).
- `SupabaseDraftPersister._rpc_params` sends `p_topic_kind` from `draft.topic_kind` (practical override forwards `practical`).
- Operator applied 014 on the shared knowledge-db VM (Studio SQL Editor, `knowledge-db.ru`) on 2026-10-29. Screenshot proof: `pg_proc` `n=1`, `pronargs=13`. Never db reset.

## Task Commits

Each task was committed atomically:

1. **Task 1: Confirm DROP then CREATE 13-arg** - decision `drop-then-create-13` recorded in STATE (no code commit)
2. **Task 2 RED: failing test for materials.topic_kind persist** - `9d78c41` (test)
3. **Task 2 GREEN: persist topic_kind via 13-arg RPC** - `2e2a344` (feat)
4. **Rule 1 RED: pin 42P13 trailing defaults and DROP/CREATE transaction** - `9f1199d` (test)
5. **Rule 1 GREEN: 13-arg persist RPC 42P13-legal with trailing defaults** - `94bbd77` (fix)
6. **Task 3: [BLOCKING] Apply migration 014 on the shared VM** - operator `applied` + §4l Applied stamp (this docs commit)

**Plan metadata:** (docs commit after this file)

_Note: TDD tasks have multiple commits (test → feat); 42P13 was an extra RED/GREEN pair_

## Files Created/Modified

- `supabase-integration/migrations/014_phase30_materials_topic_kind.sql` — ADD COLUMN, DO-block CHECK, DROP 12-arg, CREATE 13-arg, grants in one transaction
- `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` — `_rpc_params["p_topic_kind"]`
- `tests/unit/test_phase30_migration_014.py` — SQL contract pins
- `tests/unit/test_supabase_draft_persister_contract.py` — `p_topic_kind` default + practical override
- `docs/agents/local-platform-runbook.md` — §4l apply/verify ritual; Applied 2026-10-29

007, 008, 009 and `material_repository.py` SELECT list were not edited (T-30-05).

## Decisions Made

- Arity door: `drop-then-create-13` (KIND-01, D-01, T-30-06). `CREATE OR REPLACE` with a new argument would leave a 12-arg overload and silently drop the kind.
- After live 42P13: `p_batch_size int default null` so every parameter after `p_topic_kind`'s DEFAULT also has DEFAULT; DROP+CREATE+GRANT wrapped in `begin`/`commit`.
- Live apply recorded from operator screenshot (`n=1`, `pronargs=13`). Column + CHECK outputs were not re-pasted; they are applied via the same idempotent 014 file on the first and/or second Studio run.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Postgres 42P13 trailing-parameter DEFAULT**
- **Found during:** Task 3 (operator first Studio run of 014)
- **Issue:** Plan asked for `p_topic_kind text DEFAULT 'conceptual'` immediately before required `p_batch_size int`. Postgres rejects a DEFAULT followed by a parameter without DEFAULT (`ERROR 42P13`). ALTER/DO likely committed (0 rows) before CREATE failed; DROP of the 12-arg function may have committed.
- **Fix:** `p_batch_size int default null`; wrap DROP+CREATE+GRANT in one transaction.
- **Files modified:** `supabase-integration/migrations/014_phase30_materials_topic_kind.sql`, `tests/unit/test_phase30_migration_014.py`, `docs/agents/local-platform-runbook.md`
- **Verification:** `uv run pytest tests/unit/test_phase30_migration_014.py tests/unit/test_supabase_draft_persister_contract.py -q` → 26 passed; operator re-ran fixed 014; screenshot `n=1` `pronargs=13`
- **Committed in:** `9f1199d` (test) + `94bbd77` (fix)

---

**Total deviations:** 1 auto-fixed (1 Rule 1)
**Impact on plan:** Necessary for a legal CREATE FUNCTION; no scope creep. 007–009 untouched. No db reset.

## Issues Encountered

First Studio paste of 014 failed with 42P13 (see deviation). Operator re-applied the fixed file. Column+CHECK verify queries were not re-pasted; accepted from the idempotent first-run 0-row statements plus the successful 13-arg CREATE.

## Authentication Gates

None.

## User Setup Required

Completed this plan: operator applied `014_phase30_materials_topic_kind.sql` via Studio SQL Editor on the shared knowledge-db VM (`knowledge-db.ru`) on 2026-10-29. No further setup.

## Next Phase Readiness

- Live `persist_draft_and_enqueue` is 13-arg with `p_topic_kind`; drafts store `topic_kind`.
- Phase 30 plans 01–04 are complete. KIND-01 is the persist DoD for this plan (mark Complete only if `requirements.ready-ids` agrees).
- Do not start Phase 31 from this close-out. Reader badge / SELECT-list leak of `topic_kind` stays out of scope (T-30-05).

## TDD Gate Compliance

- RED: `9d78c41` `test(30-04): add failing test for materials.topic_kind persist`
- GREEN: `2e2a344` `feat(30-04): persist topic_kind via 13-arg RPC`
- Extra RED/GREEN for 42P13: `9f1199d` → `94bbd77`

## Self-Check: PASSED

- FOUND: `supabase-integration/migrations/014_phase30_materials_topic_kind.sql`
- FOUND: `tests/unit/test_phase30_migration_014.py`
- FOUND: `ingestion-service/src/ingestion_service/adapters/supabase_persist.py`
- FOUND: `docs/agents/local-platform-runbook.md` §4l Applied 2026-10-29
- FOUND: `9d78c41` `2e2a344` `9f1199d` `94bbd77`

---
*Phase: 30-classifier-practical-conceptual*
*Completed: 2026-10-29*
