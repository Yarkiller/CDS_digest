---
phase: 11-address-tech-debt-captions-diagnostics-and-persist-error-cla
plan: 02
subsystem: api
tags: [persist, postgrest, error-classification, rpc, supabase]

requires:
  - phase: 09-draft-persist-shortlist-enqueue
    provides: PERSIST_REASONS, DraftPersist* errors, map_persist_error
  - phase: 10-cli-composition-uat
    provides: SupabaseDraftPersister classification frozensets
provides:
  - SQLSTATE 23514 → batch_creation_failed (alongside check_violation)
  - int HTTP gateway code → rpc_error via _http_status_code (D-06)
affects:
  - 11-03 sent-batch RPC
  - operator persist stderr reasons

actuals:
  tokens: 1387
  tasks: 2
  commits: 6
plan_head_before: b08b2500876b1ce95a1837d7617fadc13f19ed06
plan_head_after: 5b0d2cb00e1f274af0d4451cdc46fc46e23ebc02

tech-stack:
  added: []
  patterns:
    - "_BATCH_CODES includes both check_violation name and SQLSTATE 23514"
    - "_http_status_code(int) → DraftPersistRpcError before generic SDK fallthrough"

key-files:
  created: []
  modified:
    - ingestion-service/src/ingestion_service/adapters/supabase_persist.py
    - tests/unit/test_supabase_draft_persister_contract.py

key-decisions:
  - "Keep PERSIST_REASONS unchanged (D-07); classification-only fix"
  - "Int HTTP → rpc_error per D-06 (not network_error from Phase 10 REVIEW)"

patterns-established:
  - "String SDK codes via _sdk_code; int HTTP via _http_status_code"

requirements-completed: [PERS-02]

coverage:
  - id: D1
    description: SQLSTATE 23514 classifies as batch_creation_failed like check_violation
    requirement: PERS-02
    verification:
      - kind: unit
        ref: tests/unit/test_supabase_draft_persister_contract.py::test_sqlstate_23514_maps_to_batch_error
        status: pass
    human_judgment: false
  - id: D2
    description: Numeric HTTP 503 classifies as rpc_error (not network_error)
    requirement: PERS-02
    verification:
      - kind: unit
        ref: tests/unit/test_supabase_draft_persister_contract.py::test_int_http_503_maps_to_rpc_error_not_network
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-10-02
status: complete
---

# Phase 11 Plan 02: Persist error classification Summary

**Adapter-local recognition: SQLSTATE `23514` → `batch_creation_failed` and int HTTP gateway codes → `rpc_error`, with `PERSIST_REASONS` frozen.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-02T10:57:36Z
- **Completed:** 2026-10-02T11:03:36Z
- **Tasks:** 2/2
- **Files modified:** 2
- **Commits (measured ledger→last feat):** 6 (4 plan-scoped 11-02 RED/GREEN; 2 interleaved 11-01 commits on same branch)

## Accomplishments

- `_BATCH_CODES` now includes `"23514"` next to `"check_violation"` and `"P0001"` (D-06)
- `_http_status_code` recognizes numeric PostgREST gateway `code` values and maps them to `DraftPersistRpcError` / `rpc_error` (D-06 locks rpc over Phase 10 REVIEW `network_error`)
- Contract suite green (14 passed); `mapping/persist.py` / `PERSIST_REASONS` untouched (D-07)

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED: Classify SQLSTATE 23514** — `9375314` (test)
2. **Task 1 GREEN: Classify SQLSTATE 23514** — `4c3e8a7` (feat)
3. **Task 2 RED: Classify integer HTTP status** — `f5ffc01` (test)
4. **Task 2 GREEN: Classify integer HTTP status** — `5b0d2cb` (feat)

**Plan metadata:** (this SUMMARY commit)

## Files Created/Modified

- `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` — `_BATCH_CODES` + `_http_status_code` + int-status branch in `_map_exception`
- `tests/unit/test_supabase_draft_persister_contract.py` — `23514` batch contract; int `503` → rpc_error; stub accepts `str | int`

## Decisions Made

- Classification-only fix; do not mutate `PERSIST_REASONS` (D-07)
- Int HTTP statuses classify as `rpc_error` per locked D-06 (override Phase 10 REVIEW WR-02 suggestion of `network_error`)

## Deviations from Plan

None - plan executed exactly as written.

_Note:_ Wave-parallel 11-01 commits interleaved on `experiment/gsd-framework` between 11-02 RED/GREEN pairs; measured `commits: 6` spans ledger→last feat for #3968 instrument fidelity.

## TDD Gate Compliance

- Task 1: RED (`9375314`) failed on `"23514" not in _BATCH_CODES`; GREEN (`4c3e8a7`) added `"23514"`
- Task 2: RED (`f5ffc01`) failed on missing `_http_status_code`; GREEN (`5b0d2cb`) added helper + explicit branch
- `workflow.tdd_mode` was false; workspace TDD discipline followed regardless

## Self-Check: PASSED

- FOUND: `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` (`23514`, `_http_status_code`)
- FOUND: `tests/unit/test_supabase_draft_persister_contract.py` (both new contracts)
- FOUND: commits `9375314`, `4c3e8a7`, `f5ffc01`, `5b0d2cb`
- FOUND: `uv run pytest tests/unit/test_supabase_draft_persister_contract.py -x` → 14 passed
- FOUND: `mapping/persist.py` not modified
