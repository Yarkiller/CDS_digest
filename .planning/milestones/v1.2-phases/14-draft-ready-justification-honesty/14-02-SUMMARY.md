---
phase: 14-draft-ready-justification-honesty
plan: 02
subsystem: api
tags: [adux-05, mark-ready, batch, partial-success, fastapi, tdd]

requires:
  - phase: 14-draft-ready-justification-honesty
    provides: Single POST /admin/materials/{id}/ready + mark_material_ready (14-01)
provides:
  - mark_materials_ready batch helper with per-id MarkReadyItemResult
  - POST /admin/materials/ready + MarkReadyBatchRequest/Response (extra=forbid)
  - D-02 approve≠ready regression lock (unit + HTTP + import guard)
affects:
  - 14-03 FE markReadyBatch + AdminDigestPage UX

actuals:
  tokens: 3454
  tasks: 2
  commits: 3

plan_head_before: 7ccef6e0c5b34ac0c71652717c95cf885444d019
plan_head_after: 259decce06dab44f1ac6aba030e5afee02175131

tech-stack:
  added: []
  patterns:
    - "Batch ready: one endpoint, HTTP 200 partial success results[] (never 207 / FE-loop)"
    - "Compose mark_materials_ready from mark_material_ready catching MaterialNotFoundError"

key-files:
  created:
    - .planning/phases/14-draft-ready-justification-honesty/14-02-task1-red-evidence.json
  modified:
    - backend/src/backend/application/use_cases/mark_material_ready.py
    - backend/src/backend/interface/http/routes/admin.py
    - tests/unit/test_http_admin.py
    - tests/unit/test_mark_material_ready.py
    - tests/unit/test_set_shortlist_decision.py

key-decisions:
  - "Batch collection route registered before /materials/{id}/ready; HTTP 200 for partial success (D-08 / A4)"
  - "MarkReadyBatch* DTOs use ConfigDict extra=forbid (T-14-05)"
  - "D-02 locked via docstring+assert + AST import guard — no decision→ready coupling"

patterns-established:
  - "Pattern: mark_materials_ready → list[MarkReadyItemResult] order = request ids"
  - "Pattern: POST /admin/materials/ready {material_ids} → {results:[{material_id,ok,status,error}]}"

requirements-completed: [ADUX-05]

coverage:
  - id: D1
    description: Batch POST /admin/materials/ready returns 200 with order-preserving partial success
    requirement: ADUX-05
    verification:
      - kind: unit
        ref: tests/unit/test_http_admin.py#test_admin_mark_ready_batch_partial_success_preserves_order
        status: pass
      - kind: unit
        ref: tests/unit/test_mark_material_ready.py#test_mark_materials_ready_order_preserving_partial_results
        status: pass
    human_judgment: false
  - id: D2
    description: Empty material_ids and extra=forbid 422; employee 403 on batch ready
    requirement: ADUX-05
    verification:
      - kind: unit
        ref: tests/unit/test_http_admin.py#test_admin_mark_ready_batch_empty_ids_returns_empty_results
        status: pass
      - kind: unit
        ref: tests/unit/test_http_admin.py#test_admin_mark_ready_batch_unknown_field_returns_422
        status: pass
      - kind: unit
        ref: tests/unit/test_http_admin.py#test_admin_mark_ready_batch_employee_returns_403
        status: pass
    human_judgment: false
  - id: D3
    description: Approve on draft leaves material_status draft; decision use-case uncoupled from ready
    requirement: ADUX-05
    verification:
      - kind: unit
        ref: tests/unit/test_set_shortlist_decision.py#test_approve_allowed_on_draft_material
        status: pass
      - kind: unit
        ref: tests/unit/test_set_shortlist_decision.py#test_set_shortlist_decision_does_not_import_ready_path
        status: pass
      - kind: unit
        ref: tests/unit/test_http_admin.py#test_admin_decision_approve_returns_updated_shortlist_with_status
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-10-03
status: complete
---

# Phase 14 Plan 02: Batch ready partial success Summary

**Collection `POST /admin/materials/ready` returns order-preserving partial-success `results[]`; Approve still never flips `material_status` (D-02).**

## Performance

- **Duration:** 4min
- **Started:** 2026-10-03T12:48:50Z
- **Completed:** 2026-10-03T12:52:38Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- `mark_materials_ready` composes single ready per id; missing → `material_not_found` without aborting batch
- `POST /admin/materials/ready` with `MarkReadyBatchRequest/Response` (`extra=forbid`), admin-only, HTTP 200 partial success
- D-02 regression lock: approve-stays-draft asserts + AST import guard against ready coupling

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Batch POST ready partial success** - `70e3257` (test)
2. **Task 1 (GREEN): Batch POST ready partial success** - `42eaf50` (feat)
3. **Task 2: Regression lock Approve≠ready** - `259decc` (test)

## TDD Gate Compliance

| Gate | Commit | Evidence |
|------|--------|----------|
| RED | `70e3257` | `test_mark_materials_ready_order_preserving_partial_results` AssertionError helper missing; HTTP 404; `14-02-task1-red-evidence.json` → `RED_EVIDENCE_OK` |
| GREEN | `42eaf50` | `uv run pytest … -k ready` → 15 passed |
| Task 2 | `259decc` | Test-only D-02 lock (no production coupling change); wave gate 20 passed |

## Files Created/Modified

- `backend/src/backend/application/use_cases/mark_material_ready.py` — `MarkReadyItemResult` + `mark_materials_ready`
- `backend/src/backend/interface/http/routes/admin.py` — batch DTOs + `POST /materials/ready`
- `tests/unit/test_mark_material_ready.py` — batch unit proofs
- `tests/unit/test_http_admin.py` — batch HTTP + D-02 docstring lock
- `tests/unit/test_set_shortlist_decision.py` — D-02 cite + import guard
- `.planning/phases/14-draft-ready-justification-honesty/14-02-task1-red-evidence.json` — RED gate record

## Decisions Made

- HTTP 200 (not 207) for partial success per RESEARCH A4 / D-08
- Collection route declared before parameterized single-ready route for clear coexistence
- Task 2 kept production untouched; strengthened regression tests only

## Deviations from Plan

None - plan executed exactly as written.

## Threat Mitigations

| Threat | Disposition | Proof |
|--------|-------------|-------|
| T-14-04 Elevation (batch ready) | mitigate | `Depends(require_admin)`; employee 403 test |
| T-14-05 Tampering (batch body) | mitigate | `extra=forbid`; unknown field → 422 |
| T-14-06 Info disclosure (missing id) | accept | Per-id `material_not_found` only |

## Self-Check: PASSED

- FOUND: `backend/src/backend/application/use_cases/mark_material_ready.py` (`mark_materials_ready`)
- FOUND: `backend/src/backend/interface/http/routes/admin.py` (`POST /materials/ready`)
- FOUND: commits `70e3257`, `42eaf50`, `259decc`
- FOUND: wave verify 20 passed (`ready or approve or draft`)
