---
phase: 10-cli-composition-uat
plan: 05
subsystem: database
tags: [already_saved, SupabaseDraftPersister, migration-008, CLI-02, D-09, D-12]

requires:
  - phase: 10-cli-composition-uat
    provides: Migration 008 SQL + PersistResult.already_saved on port (10-01/10-03)
  - phase: 09-draft-persist-shortlist-enqueue
    provides: persist_draft_and_enqueue baseline and FakeDraftPersister idempotency
provides:
  - Adapter requires and maps RPC already_saved onto PersistResult
  - Migration 008 live on shared VM (Studio SQL apply)
  - Idempotency unit suite green with already_saved on insert vs conflict
affects:
  - 10-04 live UAT re-run already_saved true / stored slug lines
  - CLI stdout already_saved line after persist

actuals:
  tokens: 1825
  tasks: 2
  commits: 2

plan_head_before: 4075b06c3c3f7d712565bb93b66ca4b42f87fe12
plan_head_after: a0868d47f1e60ca537a74106c3305ac0b9bddfc9

tech-stack:
  added: []
  patterns:
    - Adapter _RESULT_KEYS validates already_saved before PersistResult construction
    - Live schema apply via Studio SQL when supabase db push cannot auth non-interactively

key-files:
  created: []
  modified:
    - ingestion-service/src/ingestion_service/adapters/supabase_persist.py
    - tests/unit/test_supabase_draft_persister_contract.py
    - tests/unit/test_persist_idempotency_overflow.py
    - tests/unit/test_persist_draft_use_case.py
    - tests/unit/test_captions_failure_zero_persist.py

key-decisions:
  - "Migration 008 applied via Studio SQL (CLI push auth unavailable); human verified RPC shape and grants"
  - "Adapter maps bool(payload['already_saved']); missing key raises DraftPersistRpcError"

patterns-established:
  - "Pattern: RPC return keys remain a closed _RESULT_KEYS tuple; already_saved is required post-008"
  - "Pattern: Phase 10 schema push ritual matches Phase 9 — Studio apply + pg_proc / grant smoke checks"

requirements-completed: [CLI-02]

coverage:
  - id: D1
    description: SupabaseDraftPersister requires already_saved and maps it onto PersistResult
    requirement: CLI-02
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_draft_persister_contract.py"
        status: pass
    human_judgment: false
  - id: D2
    description: Idempotency overflow fake tests pass with already_saved on insert vs conflict
    requirement: CLI-02
    verification:
      - kind: unit
        ref: "tests/unit/test_persist_idempotency_overflow.py"
        status: pass
    human_judgment: false
  - id: D3
    description: Migration 008 live — persist_draft_and_enqueue returns already_saved; service_role-only execute
    requirement: CLI-02
    verification:
      - kind: manual_procedural
        ref: "Studio SQL apply 008 + pg_proc count=1 + prosrc already_saved + grant smoke"
        status: pass
    human_judgment: true
    rationale: "Shared VM schema apply requires human Studio/MCP ritual; cannot be proven by unit SQL-as-text alone"

duration: 25min
completed: 2026-09-29
status: complete
---

# Phase 10 Plan 05: Adapter already_saved + schema push Summary

**`SupabaseDraftPersister` now requires and maps RPC `already_saved`, and migration 008 is live on the shared VM with service_role-only execute (CLI-02 / D-09 / D-12).**

## Performance

- **Duration:** ~25 min (adapter TDD + migrate checkpoint + continuation)
- **Started:** 2026-09-29T18:17:50Z (approx Task 1 RED)
- **Completed:** 2026-09-29T18:23:05Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Adapter `_RESULT_KEYS` includes `already_saved`; missing key → `DraftPersistRpcError`
- Idempotency / use-case / captions-failure unit suites updated and green (30 passed including migration 008 SQL contracts)
- Migration 008 applied to shared VM via Studio SQL; live RPC returns `already_saved`; execute remains postgres owner + service_role only

## Task Commits

1. **Task 1 RED: Adapter contract tests** — `8a2e54b` (test)
2. **Task 1 GREEN: Parse already_saved** — `a0868d4` (feat)
3. **Task 2: [BLOCKING] Push migration 008** — no code commit (human Studio apply; checkpoint cleared with `pushed`)

## Migrate evidence (Task 2)

Human verification after Studio SQL apply of `008_phase10_persist_already_saved.sql`:

| Check | Result |
|-------|--------|
| Migration 008 applied via Studio SQL | Success |
| `persist_draft_and_enqueue` count (`pg_proc`) | 1 |
| `prosrc` contains `already_saved` | true |
| Execute grants | postgres (owner) + service_role only; no anon/authenticated/public |

Resume signal: user replied **pushed**. Do not re-apply.

## Files Created/Modified

- `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` — `_RESULT_KEYS` + `bool(payload["already_saved"])` mapping
- `tests/unit/test_supabase_draft_persister_contract.py` — happy/conflict/missing-key contract tests
- `tests/unit/test_persist_idempotency_overflow.py` — already_saved on insert vs conflict
- `tests/unit/test_persist_draft_use_case.py` — PersistResult constructions include already_saved
- `tests/unit/test_captions_failure_zero_persist.py` — PersistResult constructions include already_saved

## Decisions Made

- Studio SQL apply used instead of interactive `supabase db push` (same Phase 9 ritual)
- Adapter treats `already_saved` as required post-008; no soft default on live RPC payloads

## Deviations from Plan

None - plan executed as written after the cleared migrate checkpoint. Continuation re-ran unit verify only (no live re-apply).

## Auth gates

- Task 2: `supabase db push` non-interactive auth unavailable → human applied via Studio SQL → verified and resumed with `pushed`

## Issues Encountered

None beyond the expected migrate human gate.

## User Setup Required

None - migration is live; no new env vars.

## Next Phase Readiness

- CLI-02 adapter + live RPC shape ready for Wave 4 (`10-04` live composition UAT)
- Re-run should surface stored slug + `already_saved: true` without duplicate material rows

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: `.planning/phases/10-cli-composition-uat/10-05-SUMMARY.md`
- FOUND: `ingestion-service/src/ingestion_service/adapters/supabase_persist.py`
- FOUND: `8a2e54b`, `a0868d4`
- COMMITS_ACTUAL: 2 from plan_head_before

---
*Phase: 10-cli-composition-uat*
*Completed: 2026-09-29*
