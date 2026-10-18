---
phase: 11-address-tech-debt-captions-diagnostics-and-persist-error-cla
plan: 04
subsystem: cli
tags: [cli, typer, already_saved, sent-batch, migration, supabase, pytest, tdd]

requires:
  - phase: 11-03
    provides: migration 009 SQL authored offline + BatchTrackingFakePersister sent-batch already_saved
  - phase: 10-cli-composition-uat
    provides: CLI checkmarks + already_saved stdout contract
provides:
  - CLI unit contract for sent-batch re-run checkmarks + already_saved (D-08; CLI-02; CLI-04)
  - Live migration 009 applied on knowledge-db.ru via Studio SQL
affects:
  - operator re-run after shortlist send
  - phase 11 verification / milestone close

actuals:
  tokens: 510
  tasks: 2
  commits: 1

plan_head_before: 2ba72525f535e5cb984f6d6c0a559f7db1440874
plan_head_after: 0e68b4d1ddb702e448ff9ca6a88dd7486fa477ba

tech-stack:
  added: []
  patterns:
    - "CliRunner + BatchTrackingFakePersister sent-batch seed proves operator stdout without live DB"
    - "Live RPC apply remains blocking human Studio/psql ritual (mirror Phase 10 008)"

key-files:
  created: []
  modified:
    - tests/unit/test_cli_ingest_contract.py
    - supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql

key-decisions:
  - "Unexpected GREEN on Task 1: no cli.py change — Phase 10 stdout + 11-03 fake invert already satisfied contract"
  - "Human pushed: migration 009 live on knowledge-db.ru; grants postgres+service_role only"

patterns-established:
  - "Sent-batch CLI contract seeds BatchTrackingFakePersister like overflow suite, asserts three checkmarks + already_saved: true"

requirements-completed: [CLI-02, CLI-04]

coverage:
  - id: D1
    description: CliRunner sent-batch re-run exits 0 with three checkmarks and already_saved: true
    requirement: CLI-04
    verification:
      - kind: unit
        ref: tests/unit/test_cli_ingest_contract.py#test_cli_sent_batch_rerun_prints_checkmarks_and_already_saved
        status: pass
    human_judgment: false
  - id: D2
    description: Live migration 009 on shared VM — sent-batch already_saved path + service_role-only execute
    requirement: CLI-02
    verification: []
    human_judgment: true
    rationale: Schema apply and live RPC body/grants require Studio/psql human verification on knowledge-db.ru

duration: 140min
completed: 2026-10-02
status: complete
---

# Phase 11 Plan 04: CLI sent-batch checkmarks + migration 009 apply Summary

**CLI unit proves checkmarks + `already_saved: true` on sent-batch re-run; migration 009 applied live on knowledge-db.ru via Studio SQL.**

## Performance

- **Duration:** ~140 min (includes human Studio apply wait)
- **Started:** 2026-10-02T11:13:36Z
- **Completed:** 2026-10-02T13:34:00Z
- **Tasks:** 2/2
- **Files modified:** 1 code file (CLI contract); migration 009 applied live (authored in 11-03)

## Accomplishments

- Added CliRunner contract `test_cli_sent_batch_rerun_prints_checkmarks_and_already_saved` (D-08; CLI-02; CLI-04).
- Confirmed exit 0, `✓ transcript` / `✓ LLM` / `✓ saved`, `already_saved: true` with stored ids, single stored material, empty stderr.
- Human applied migration 009 via Studio SQL on knowledge-db.ru; live RPC matches sent-batch already_saved contract with service_role-only execute.

## Task Commits

1. **Task 1: CLI sent-batch re-run prints checkmarks and already_saved** - `0e68b4d` (test)
2. **Task 2: [BLOCKING] Apply migration 009 on shared VM via Studio/psql** - human verify (`pushed`) — no code commit; no re-apply by executor

**Plan metadata:** `5f431d5` (docs: complete plan)

## Files Created/Modified

- `tests/unit/test_cli_ingest_contract.py` — sent-batch CliRunner contract (BatchTrackingFakePersister seed)
- `supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql` — live-applied (authored 11-03; not re-authored here)

## Decisions Made

- **Unexpected GREEN (Task 1):** Contract test passed without `cli.py` changes — Phase 10 checkmark/`already_saved` emission plus 11-03 `BatchTrackingFakePersister` invert already deliver D-08 at unit level. Plan allowed skipping production change unless RED proved regression.
- **Human `pushed` (Task 2):** Migration 009 is live; live CLI-02 sent-batch edge may be claimed.

## Human Verification Notes (Task 2 — resume: pushed)

Migration 009 applied via **Studio SQL** on **knowledge-db.ru**. Human verified (executor did **not** re-apply):

| Check | Result |
|-------|--------|
| `persist_draft_and_enqueue` count | 1 |
| `prosrc` RAISE EXCEPTION | 3 only — `p_batch_size>=1`, material lookup failed, existing material has no shortlist row |
| "batch already sent" raise | Absent |
| `ON CONFLICT DO NOTHING` | Present |
| Conflict branch | Fetches existing shortlist (prefer unsent then any) |
| `already_saved` return | Present |
| Function `src_length` | 3414 (008) → 4092 (009) |
| Execute grants | `postgres` + `service_role` only; no anon/authenticated/public |
| P0001 | Only for legit edges (validation, lookup fail, material without shortlist) |

Threat mitigations T-11-07 (grants) and T-11-08 (already_saved path / no second insert intent) satisfied by this human verify.

## Deviations from Plan

### Auto-fixed Issues

None.

### Other

**1. Unexpected GREEN on TDD Task 1 (no production commit)**
- **Found during:** Task 1 RED run
- **Issue:** New CliRunner test passed immediately — feature already present via prior plans.
- **Fix:** Committed contract test only (`test`); no `cli.py` change per plan guidance.
- **Files modified:** `tests/unit/test_cli_ingest_contract.py`
- **Commit:** `0e68b4d`
- **Impact on plan:** Goal met; GREEN feat gate N/A for this task.

**Total deviations:** 1 (process/TDD unexpected green)
**Impact on plan:** None on deliverables.

## Issues Encountered

None blocking. Checkpoint wait for Studio apply completed with resume signal `pushed`.

## Auth Gates

None.

## User Setup Required

None remaining — migration 009 is live.

## Next Phase Readiness

- Phase 11 plans 11-01…11-04 complete at execution level.
- Optional live smoke: re-run ingest for a video whose only shortlist row is on a sent batch (human optional step from plan).
- Ready for phase verify / milestone audit follow-up.

## Known Stubs

None — CLI contract is real assertions; live RPC verified by human; no placeholder paths for this plan's goal.

## Self-Check: PASSED

- FOUND: `11-04-SUMMARY.md`
- FOUND: `tests/unit/test_cli_ingest_contract.py`
- FOUND: `supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql`
- FOUND commit: `0e68b4d`
- Verification: `uv run pytest tests/unit/test_cli_ingest_contract.py -x` → 8 passed
- Human resume: `pushed` (migration 009 live; not re-applied by executor)

---
*Phase: 11-address-tech-debt-captions-diagnostics-and-persist-error-cla*
*Completed: 2026-10-02*
