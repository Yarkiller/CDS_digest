---
phase: 14-draft-ready-justification-honesty
plan: 01
subsystem: api
tags: [adux-05, mark-ready, shortlist, fastapi, tdd]

requires:
  - phase: 13-admin-material-email-preview-honesty
    provides: Admin shortlist GET/decision/send with draft_in_send_pool gate
provides:
  - Material.with_ready_status status-only triage transition
  - mark_material_ready use-case (no publish_material / as_ready)
  - POST /admin/materials/{id}/ready + MarkReadyResponse
  - In-memory shortlist material_status overlay from materials repo
affects:
  - 14-02 batch ready endpoint
  - 14-03 FE markReady + AdminDigestPage UX

actuals:
  tokens: 6559
  tasks: 2
  commits: 3

plan_head_before: 9103b3805fc60ce841033c22b46eb9111b9b4e18
plan_head_after: 367499cc6fd20afbcbe4e2fbd6d3f5a83f657a61

tech-stack:
  added: []
  patterns:
    - "Status-only triage ready via with_ready_status (contrast as_ready/publish)"
    - "InMemoryShortlistRepository overlays material_status from attached materials repo"

key-files:
  created:
    - tests/unit/test_mark_material_ready.py
    - backend/src/backend/application/use_cases/mark_material_ready.py
    - .planning/phases/14-draft-ready-justification-honesty/14-01-task1-red-evidence.json
  modified:
    - tests/unit/test_http_admin.py
    - backend/src/backend/domain/material.py
    - backend/src/backend/interface/http/routes/admin.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/composition/container.py

key-decisions:
  - "Triage ready uses with_ready_status — never publish_material/as_ready/index (D-06)"
  - "Single ready route is body-less; MarkReadyResponse extra=forbid (D-07/D-10)"
  - "In-memory shortlist overlays + claim_sent persist overlaid statuses for send-bridge fidelity"

patterns-established:
  - "Pattern: mark_material_ready → MaterialRepository.save; shortlist reads status via join/overlay"
  - "Pattern: admin material promote behind Depends(require_admin) under /admin/materials/{id}/ready"

requirements-completed: [ADUX-05]

coverage:
  - id: D1
    description: Empty-body draft promotes to ready with published_at unchanged
    requirement: ADUX-05
    verification:
      - kind: unit
        ref: tests/unit/test_mark_material_ready.py#test_mark_material_ready_empty_body_draft_sets_ready_leaves_published_at
        status: pass
    human_judgment: false
  - id: D2
    description: Admin POST ready → shortlist material_status ready → send clears draft_in_send_pool
    requirement: ADUX-05
    verification:
      - kind: unit
        ref: tests/unit/test_http_admin.py#test_admin_mark_ready_promotes_draft_and_clears_send_gate
        status: pass
    human_judgment: false
  - id: D3
    description: Already-ready is HTTP/use-case no-op; employee gets 403
    requirement: ADUX-05
    verification:
      - kind: unit
        ref: tests/unit/test_http_admin.py#test_admin_mark_ready_already_ready_is_noop
        status: pass
      - kind: unit
        ref: tests/unit/test_http_admin.py#test_admin_mark_ready_employee_returns_403
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-03
status: complete
---

# Phase 14 Plan 01: Tracer draft→ready Summary

**Admin JWT can promote one draft to triage-ready without publishing; shortlist and D-85 send gate follow materials.status.**

## Performance

- **Duration:** 5min
- **Started:** 2026-10-03T12:41:05Z
- **Completed:** 2026-10-03
- **Tasks:** 2/2
- **Files modified:** 8

## Accomplishments

- Status-only `Material.with_ready_status` + `mark_material_ready` (empty body allowed; `published_at` untouched)
- `POST /admin/materials/{id}/ready` with `MarkReadyResponse`, `require_admin`, 404 `material_not_found`
- In-memory shortlist overlays `material_status` from materials (including `claim_sent`) so send bridge clears `draft_in_send_pool`

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): End-to-end POST ready unblocks D-85** - `e42a030` (test)
2. **Task 1 (GREEN): End-to-end POST ready unblocks D-85** - `0df1a0d` (feat)
3. **Task 2: Lock idempotent already-ready and employee 403** - `367499c` (test)

## TDD Gate Compliance

| Gate | Commit | Evidence |
|------|--------|----------|
| RED | `e42a030` | `test_mark_material_ready_empty_body_draft_sets_ready_leaves_published_at` AssertionError DRAFT≠READY; `14-01-task1-red-evidence.json` → `RED_EVIDENCE_OK` |
| GREEN | `0df1a0d` | Wave filter `ready or draft_in_send_pool` → 7 passed |
| Task 2 lock | `367499c` | Already-ready + employee 403 HTTP locks; green immediately because Task 1 GREEN already shipped D-09 + `require_admin` (T-14-01) |
| REFACTOR | n/a | Not needed |

## Files Created/Modified

- `tests/unit/test_mark_material_ready.py` — domain/use-case ADUX-05 proofs
- `tests/unit/test_http_admin.py` — HTTP tracer + D-09/403 locks; `_admin_client_with_batch` attaches materials
- `backend/src/backend/domain/material.py` — `with_ready_status`
- `backend/src/backend/application/use_cases/mark_material_ready.py` — status-only use-case
- `backend/src/backend/interface/http/routes/admin.py` — ready route + `MarkReadyResponse`
- `backend/src/backend/tests_support/in_memory.py` — materials overlay on shortlist reads/claim
- `backend/src/backend/composition/container.py` — wire materials into in-memory shortlist
- `.planning/phases/14-draft-ready-justification-honesty/14-01-task1-red-evidence.json` — RED evidence

## Decisions Made

- Triage ready must not call `publish_material` / `as_ready` / knowledge indexing (D-06)
- Single ready has no request body; response forbids extras (D-07/D-10)
- Overlay also applied inside `claim_sent` so `InMemoryDigestPublisher` pool matches materials.status (Rule 2 for send-bridge correctness)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Overlay on claim_sent**
- **Found during:** Task 1 GREEN
- **Issue:** Plan listed overlay only on `get_current_batch` / `get_latest_batch`; `claim_and_publish` reads `claim_sent` items and would still see denormalized `draft`
- **Fix:** Persist overlaid statuses in `claim_sent` before return
- **Files modified:** `backend/src/backend/tests_support/in_memory.py`
- **Commit:** `0df1a0d`

**2. [Rule 3 - Blocking] Accidental inclusion of pre-existing in_memory WIP**
- **Found during:** Task 1 GREEN commit review
- **Issue:** Staging `in_memory.py` also committed unrelated dirty helper extractions already present in the working tree (knowledge/vote helpers refactor vs parent)
- **Fix:** Left self-consistent helpers in place (search still works); documented — do not rewrite unrelated WIP mid-plan
- **Files modified:** `backend/src/backend/tests_support/in_memory.py`
- **Commit:** `0df1a0d`

## Issues Encountered

- Pytest output is not TAP; RED evidence persisted in TAP shape per Phase 13 convention while live AssertionError remained the intentional failure
- Task 2 could not produce a separate failing RED — behaviors already present after Task 1 GREEN

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 14-02 batch `POST /admin/materials/ready` and 14-03 FE/UX

## Self-Check: PASSED

- All key files present
- Commits `e42a030`, `0df1a0d`, `367499c` present on branch
- Wave verify: 9 passed (`ready or draft_in_send_pool`)
