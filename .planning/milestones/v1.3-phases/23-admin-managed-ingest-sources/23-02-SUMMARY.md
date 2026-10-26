---
phase: 23-admin-managed-ingest-sources
plan: 02
subsystem: api
tags: [fastapi, cors, pydantic, react, ports-adapters, ingest-sources, validation]

requires:
  - phase: 23-admin-managed-ingest-sources
    provides: tracer GET/POST ingest-sources spine, InMemoryIngestSourceRepository write log, 400 mapper
provides:
  - Full add reject matrix with top-level {errors:[…]} and zero writes (D-14/D-15/D-20)
  - PATCH enable/disable + hard DELETE 204 with IngestSourceNotFoundError → 404
  - CORS allow_methods includes DELETE
  - SPA setIngestSourceEnabled + deleteIngestSource (mock+live)
affects: [23-03, 23-04, 24-scheduled-ingestion]

actuals:
  tokens: 5520
  tasks: 3
  commits: 4
  plan_head_before: 25189ebb0387c43651aff0469fed76ff27e36a11
  plan_head_after: fc47695eff3790f00bfc4091ec9b0ad688f57a93

tech-stack:
  added: []
  patterns:
    - "Validate-then-persist reject matrix asserted via write_count/adds == unchanged on every 400"
    - "IngestSourceNotFoundError maps KeyError from repo to HTTP 404 ingest_source_not_found"
    - "Hard DELETE returns Response 204 with empty body; unique (kind, source_id) reusable after delete"

key-files:
  created: []
  modified:
    - tests/unit/test_http_ingest_sources.py
    - tests/unit/test_cors.py
    - backend/src/backend/domain/errors.py
    - backend/src/backend/application/use_cases/ingest_sources.py
    - backend/src/backend/interface/http/routes/admin.py
    - backend/src/backend/interface/http/app.py
    - web/src/services/ingestSourcesApi.js

key-decisions:
  - "D-10 confirmed hard-delete (user selected hard-delete; no soft delete)"
  - "Missing PATCH/DELETE id uses detail ingest_source_not_found (404), matching material/shortlist style"

patterns-established:
  - "Reject rows never include line; detail key absent on 400 body"
  - "PATCH body is {is_enabled} only (extra=forbid → 422)"

requirements-completed: [SRC-01, SRC-02]

coverage:
  - id: D1
    description: "Invalid source_id / kind mismatch / label>120 / duplicate → 400 {errors:[…]} with zero writes"
    requirement: SRC-02
    verification:
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_post_invalid_source_id_returns_400_and_writes_nothing"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_post_duplicate_returns_400_and_writes_nothing"
        status: pass
    human_judgment: false
  - id: D2
    description: "PATCH disable then hard DELETE 204; row gone; re-add same (kind, source_id) → 201"
    requirement: SRC-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_patch_disable_then_delete_hard_removes_row"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_readd_after_delete_succeeds"
        status: pass
    human_judgment: false
  - id: D3
    description: "DELETE missing id → 404 ingest_source_not_found; PATCH/DELETE 401/403 admin-gated"
    requirement: SRC-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_delete_missing_id_returns_404"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_patch_delete_require_admin_unauth_401_and_employee_403"
        status: pass
    human_judgment: false
  - id: D4
    description: "CORS preflight advertises DELETE for ingest-source routes"
    requirement: SRC-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cors.py#test_delete_method_is_advertised_in_cors_preflight"
        status: pass
    human_judgment: false

duration: 18min
completed: 2026-10-17
status: complete
---

# Phase 23 Plan 02: Validation rejects + enable/delete API Summary

**Server is the authority for canonical ingest-source ids: rejects never write, PATCH toggles enablement, hard DELETE returns 204, and CORS advertises DELETE for the live SPA.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-10-17T16:42:00Z
- **Completed:** 2026-10-17T17:00:00Z
- **Tasks:** 3/3
- **Files modified:** 7

## Accomplishments

- Reject matrix (invalid ids, kind/prefix mismatch, duplicate «Этот источник уже добавлен», label max 120) returns top-level `{errors:[…]}` with `write_count` unchanged (SRC-02, D-20).
- PATCH `{is_enabled}` + hard DELETE 204; missing id → 404 `ingest_source_not_found`; re-add after delete → 201 (SRC-01, D-10).
- CORS `allow_methods` includes DELETE; SPA gained `setIngestSourceEnabled` / `deleteIngestSource`.

## Task Commits

Each task was committed atomically (TDD RED→GREEN for Tasks 2–3; Task 1 was the D-10 decision checkpoint):

1. **Task 1:** decision `hard-delete` (D-10) — no code commit; verify `checkpoint-d10-ack`
2. **Task 2 RED:** `d4b80ac` — test(23-02): add failing reject matrix and PATCH/DELETE HTTP contracts
3. **Task 2 GREEN:** `eb687a8` — feat(23-02): implement ingest-source reject matrix and PATCH/DELETE
4. **Task 3 RED:** `74f6cdf` — test(23-02): add failing CORS DELETE preflight assertion
5. **Task 3 GREEN:** `fc47695` — feat(23-02): advertise DELETE in CORS allow_methods

## Files Created/Modified

- `tests/unit/test_http_ingest_sources.py` — reject matrix, PATCH/DELETE, auth, re-add contracts
- `tests/unit/test_cors.py` — DELETE preflight case
- `backend/src/backend/domain/errors.py` — `IngestSourceNotFoundError`
- `backend/src/backend/application/use_cases/ingest_sources.py` — `set_ingest_source_enabled` / `delete_ingest_source`
- `backend/src/backend/interface/http/routes/admin.py` — PATCH/DELETE routes + patch DTO
- `backend/src/backend/interface/http/app.py` — CORS DELETE
- `web/src/services/ingestSourcesApi.js` — enable/delete mock+live

## Decisions Made

- Proceeded with locked D-10 hard DELETE (user selected `hard-delete`).
- 404 detail code `ingest_source_not_found` for missing PATCH/DELETE targets.

## Deviations from Plan

None - plan executed exactly as written.

Notes: add-path validation regex/kind/label/duplicate already existed from 23-01 tracer; Task 2 RED failed on missing PATCH/DELETE routes (intentional), while reject assertions were already green — GREEN focused on lifecycle APIs + SPA methods without rewriting the tracer.

## TDD Gate Compliance

| Task | RED commit | GREEN commit | RED evidence |
|------|------------|--------------|--------------|
| 2 reject + PATCH/DELETE | `d4b80ac` | `eb687a8` | 5 failed (PATCH/DELETE 404 Not Found / missing routes); 15 passed |
| 3 CORS DELETE | `74f6cdf` | `fc47695` | `test_delete_method_is_advertised_in_cors_preflight` assert 400==200 (method not allowed) |

## Threat Flags

None — PATCH/DELETE surfaces covered by plan register T-23-06…T-23-09 (`require_admin`, validation before write).

## Known Stubs

None that block this plan's goal. Row toggle/delete UI journey remains for 23-04; live Supabase adapter for 23-03.

## Self-Check: PASSED

- Key artifact paths present (7 modified files)
- Commits `d4b80ac`, `eb687a8`, `74f6cdf`, `fc47695` found in git log
- Verify: `uv run pytest tests/unit/test_http_ingest_sources.py tests/unit/test_cors.py -q` → 25 passed
- Measured commits: 4 (`25189eb`..`fc47695`)
