---
phase: 11-address-tech-debt-captions-diagnostics-and-persist-error-cla
plan: 03
subsystem: database
tags: [postgres, supabase, rpc, idempotency, already_saved, migration, pytest, tdd]

requires:
  - phase: 10-cli-composition-uat
    provides: migration 008 persist_draft_and_enqueue conflict already_saved pattern
provides:
  - migration 009 CREATE OR REPLACE sent-batch already_saved return (authored offline)
  - offline SQL contract tests for 009
  - BatchTrackingFakePersister + overflow unit invert for D-08
affects:
  - 11-04 live Studio/psql apply of migration 009
  - CLI-02 operator re-run after send

actuals:
  tokens: 5173
  tasks: 3
  commits: 9

plan_head_before: 7762d382be357126044211767ab73122635c82ff
plan_head_after: 33b3a5f4da6091978cc2e8f77820b3c4e98a9039

tech-stack:
  added: []
  patterns:
    - "CREATE OR REPLACE RPC amend via new migration file (007→008→009); never edit applied SQL in place"
    - "Conflict prefer-unsent then fallback any shortlist row including sent_at IS NOT NULL → already_saved true"
    - "Unit fake mirrors RPC sent-batch already_saved; new-material enqueue still skips sent batches"

key-files:
  created:
    - supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql
    - tests/unit/test_phase11_migration_009.py
  modified:
    - ingestion-service/src/ingestion_service/tests_support/fakes.py
    - tests/unit/test_persist_idempotency_overflow.py
    - .planning/STATE.md

key-decisions:
  - "User proceed: one-way D-09 RPC amend accepted — sent-batch-only conflict returns already_saved true (exit 0), not P0001"
  - "Live push via Studio SQL deferred to plan 11-04; 009 authored and contract-tested only"
  - "Fallback SELECT order by week_start desc, created_at desc, limit 1 (matches unsent prefer ordering)"

patterns-established:
  - "SQL-as-text contract asserts second shortlist SELECT without exclusive sent_at is null before P0001 raise"
  - "BatchTrackingFakePersister conflict path returns PersistResult(already_saved=True) for sent batches"

requirements-completed: [CLI-02]

coverage:
  - id: D1
    description: Migration 009 CREATE OR REPLACE persist_draft_and_enqueue with sent-batch already_saved fallback
    requirement: CLI-02
    verification:
      - kind: unit
        ref: tests/unit/test_phase11_migration_009.py#test_migration_009_sent_batch_fallback_select_without_exclusive_sent_at_null
        status: pass
    human_judgment: false
  - id: D2
    description: Offline SQL contract for grants, security invoker, no destructive wipes, 008 untouched
    requirement: CLI-02
    verification:
      - kind: unit
        ref: tests/unit/test_phase11_migration_009.py
        status: pass
    human_judgment: false
  - id: D3
    description: Unit fake + overflow test expect already_saved on sent-batch-only re-run
    requirement: CLI-02
    verification:
      - kind: unit
        ref: tests/unit/test_persist_idempotency_overflow.py#test_rerun_when_only_sent_batch_exists_returns_already_saved
        status: pass
    human_judgment: false
  - id: D4
    description: Live shared-VM apply of migration 009
    requirement: CLI-02
    verification: []
    human_judgment: true
    rationale: Owned by plan 11-04 Studio/psql gate; not applied in 11-03 per plan prohibitions

duration: 8min
completed: 2026-10-02
status: complete
---

# Phase 11 Plan 03: Migration 009 + sent-batch fake invert Summary

**Migration 009 CREATE OR REPLACE so sent-batch-only conflict returns `already_saved: true`; unit fake/overflow inverted; live apply deferred to 11-04.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-02T11:03:02Z
- **Completed:** 2026-10-02T11:11:00Z
- **Tasks:** 3/3
- **Files modified:** 5 (plus concurrent planning metadata in measured commit window)

## Accomplishments

- Recorded user `proceed` acceptance for one-way D-09 amend before authoring SQL (Q4 / D-08 / D-09 / D-10 rationale).
- Authored `009_phase11_persist_sent_batch_already_saved.sql` with prefer-unsent then any-shortlist fallback; P0001 only when no shortlist row exists.
- Offline SQL contract green (7 tests); applied `008` left unmodified.
- Inverted `BatchTrackingFakePersister` + overflow re-run test to expect `already_saved` with stored ids; neighboring skip-sent-batch enqueue tests remain green.

## Task Commits

1. **Task 1: Checkpoint proceed (one-way RPC amend)** - `c05bb8c` (docs)
2. **Task 2 RED: SQL contract test** - `87ba33a` (test)
3. **Task 2 GREEN: migration 009** - `08dd9d4` (feat)
4. **Task 3 RED: inverted overflow expectation** - `b4b0212` (test)
5. **Task 3 GREEN: fake already_saved return** - `37552ff` (feat)

**Plan metadata:** `33b3a5f` (docs: complete plan)

_Note: `git rev-list` from plan ledger → metadata HEAD counts **9** commits because concurrent 11-01/11-02 docs commits landed in the same window; plan-owned commits are the five task commits plus this metadata commit._

## Files Created/Modified

- `supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql` — RPC amend (offline)
- `tests/unit/test_phase11_migration_009.py` — SQL-as-text contract
- `ingestion-service/src/ingestion_service/tests_support/fakes.py` — sent-batch conflict → already_saved
- `tests/unit/test_persist_idempotency_overflow.py` — inverted D-08 unit expectation
- `.planning/STATE.md` — proceed decision recorded

## Decisions Made

- **proceed (blocking-human checkpoint):** Author migration 009 so sent-batch re-run returns `already_saved: true` / exit 0 instead of P0001. Rationale recorded from user: Q4 already decided; consistency with D-09/D-10; without fix = known v1.1 bug; one-way migration consistent with 007/008; CREATE OR REPLACE idempotent; no second materials insert / no content refresh; live Studio push owned by 11-04.

## Deviations from Plan

### Auto-fixed Issues

None for correctness of 009 / fake invert.

### Other

**1. Concurrent staging contamination on Task 3 RED commit**
- **Found during:** Task 3 RED commit `b4b0212`
- **Issue:** Commit intended only `tests/unit/test_persist_idempotency_overflow.py` but also included concurrent `.planning/STATE.md`, `.planning/ROADMAP.md`, and `11-02-SUMMARY.md` already staged by parallel wave work.
- **Fix:** Did not rewrite history; subsequent fake GREEN commit staged only intended paths. Documented here for verifier.
- **Impact on plan:** No production SQL/fake scope creep; planning docs from 11-02 hitchhiked into a 11-03 test commit.

**Total deviations:** 1 process contamination (not a Rule 1–3 code fix)
**Impact on plan:** Negligible for CLI-02 deliverables; live apply still correctly deferred.

## Issues Encountered

None blocking. Live schema apply intentionally not performed (11-04).

## User Setup Required

None for this plan. Plan 11-04 owns human Studio/psql apply of migration 009 on the shared VM.

## Next Phase Readiness

- 11-04 can apply `009_phase11_persist_sent_batch_already_saved.sql` after verifying offline contract remains green.
- Unit suite already matches D-08; operator UAT of live re-run after send remains 11-04.

## Known Stubs

None — migration is complete SQL; fake returns real stored ids; no placeholder paths for this plan's goal. Live apply is intentionally out of scope (not a stub).

## Self-Check: PASSED

- FOUND: `supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql`
- FOUND: `tests/unit/test_phase11_migration_009.py`
- FOUND: `11-03-SUMMARY.md`
- FOUND commits: `c05bb8c`, `87ba33a`, `08dd9d4`, `b4b0212`, `37552ff`
- Verification: `uv run pytest tests/unit/test_phase11_migration_009.py tests/unit/test_persist_idempotency_overflow.py -x` → 12 passed

---
*Phase: 11-address-tech-debt-captions-diagnostics-and-persist-error-cla*
*Completed: 2026-10-02*
