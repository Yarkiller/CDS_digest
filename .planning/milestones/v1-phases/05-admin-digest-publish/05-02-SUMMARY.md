---
phase: 05-admin-digest-publish
plan: 02
subsystem: api
tags: [fastapi, shortlist, set_decision, require_admin, admin-triage, tdd, ports-adapters]

requires:
  - phase: 05-admin-digest-publish
    provides: ShortlistRepository GET + require_admin + InMemoryShortlistRepository
provides:
  - set_shortlist_decision use-case with snapshot return
  - ShortlistRepository.set_decision port + in-memory mutation
  - POST /admin/shortlist/items/{material_id}/decision behind require_admin
  - ShortlistNotFoundError / InvalidShortlistDecisionError domain errors
  - draft|ready material_status on decision + GET shortlist DTOs
affects:
  - 05-03 preview/send draft-in-pool gate
  - 05-04 AdminDigestPage SPA mutations
  - 05-05 live ShortlistRepository.set_decision adapter

actuals:
  tokens: 5941
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "set_shortlist_decision → port.set_decision → get_admin_shortlist snapshot (cast_vote analog)"
    - "POST /admin/shortlist/items/{id}/decision with extra=forbid; allowlist in use-case → HTTP 400"
    - "decided_by from CurrentUser.id only — never client body (T-05-07)"

key-files:
  created:
    - backend/src/backend/application/use_cases/set_shortlist_decision.py
    - tests/unit/test_set_shortlist_decision.py
  modified:
    - backend/src/backend/application/ports/shortlist_repository.py
    - backend/src/backend/domain/shortlist.py
    - backend/src/backend/domain/errors.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/interface/http/routes/admin.py
    - tests/unit/test_http_admin.py

key-decisions:
  - "Decision allowlist pending|approved|rejected enforced in use-case (HTTP 400); Pydantic forbids extras only — avoids FastAPI 422 for invalid enum (D-82)"
  - "Approve on draft succeeds here; DraftInSendPoolError deferred to 05-03 send gate (D-85)"
  - "Actor decided_by from require_admin CurrentUser.id, not request body (T-05-07)"

patterns-established:
  - "Pattern: shortlist mutation returns AdminShortlist snapshot for SPA refresh"
  - "Pattern: ShortlistNotFoundError → 404 shortlist_item_not_found; InvalidShortlistDecisionError → 400"

requirements-completed: [ADMIN-02, ADMIN-03]

coverage:
  - id: D1
    description: "Approve persists shortlist_decision=approved and is visible on subsequent GET"
    requirement: ADMIN-02
    verification:
      - kind: unit
        ref: "tests/unit/test_set_shortlist_decision.py#test_approve_persists_decision_and_returns_snapshot"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_decision_approve_returns_updated_shortlist_with_status"
        status: pass
    human_judgment: false
  - id: D2
    description: "Reject persists shortlist_decision=rejected and is reflected on subsequent GET"
    requirement: ADMIN-02
    verification:
      - kind: unit
        ref: "tests/unit/test_set_shortlist_decision.py#test_reject_persists_decision_on_subsequent_get"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_decision_reject_persists_on_get"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every shortlist item exposes material_status draft|ready on GET and decision response"
    requirement: ADMIN-03
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_decision_approve_returns_updated_shortlist_with_status"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_shortlist_admin_returns_ranked_items_with_factor_honesty"
        status: pass
    human_judgment: false
  - id: D4
    description: "Approve is allowed on draft materials (send-pool draft block is 05-03)"
    requirement: ADMIN-03
    verification:
      - kind: unit
        ref: "tests/unit/test_set_shortlist_decision.py#test_approve_allowed_on_draft_material"
        status: pass
    human_judgment: false
  - id: D5
    description: "Non-admin cannot POST decision — HTTP 403"
    requirement: ADMIN-02
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_decision_employee_returns_403"
        status: pass
    human_judgment: false
  - id: D6
    description: "Invalid decision → 400; unknown material → 404; PersistenceError → 503"
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_decision_invalid_body_returns_400"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_decision_unknown_material_returns_404"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_decision_persistence_error_returns_503"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 02: Shortlist Decision Persistence Summary

**Approve/Reject via `set_shortlist_decision` + `POST /admin/shortlist/items/{id}/decision` with draft approve allowed and non-admin 403**

## Performance

- **Duration:** 4min
- **Started:** 2026-09-21T14:36:59Z
- **Completed:** 2026-09-21T14:41:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- `ShortlistRepository.set_decision` + in-memory mutation with `decided_by` / `decided_at`
- Use-case returns `AdminShortlist` snapshot (same shape as GET) for SPA refresh
- Admin HTTP POST decision gated by `require_admin`; employee → 403
- draft|ready exposed on items; Approve on draft succeeds (D-85); send draft block deferred to 05-03

## Task Commits

Each task was committed atomically:

1. **Task 1: set_shortlist_decision use-case** — `29ebae3` (test) → `81a4b47` (feat)
2. **Task 2: Admin HTTP decision route** — `24bb6a6` (test) → `789edf8` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks use test → feat commit pairs_

## Files Created/Modified

- `backend/src/backend/application/use_cases/set_shortlist_decision.py` — Approve/Reject/pending + snapshot
- `backend/src/backend/application/ports/shortlist_repository.py` — `set_decision` Protocol method
- `backend/src/backend/domain/shortlist.py` — optional `decided_by` / `decided_at` on ShortlistItem
- `backend/src/backend/domain/errors.py` — `ShortlistNotFoundError`, `InvalidShortlistDecisionError`
- `backend/src/backend/tests_support/in_memory.py` — InMemoryShortlistRepository.set_decision
- `backend/src/backend/interface/http/routes/admin.py` — POST decision + shared `_to_response`
- `tests/unit/test_set_shortlist_decision.py`, `tests/unit/test_http_admin.py` — contracts

## Decisions Made

- Allowlist `pending|approved|rejected` in use-case (HTTP 400) rather than Pydantic `Literal` (would 422) so SPA can toast «Не сохранено» on non-2xx with a stable 400
- No `container.py` change — shortlist port already wired in 05-01
- Actor always `admin.id` from `require_admin` (T-05-07)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Invalid decision body maps to 400 not 422**
- **Found during:** Task 2 (GREEN)
- **Issue:** Pydantic `Literal` produced FastAPI 422; plan/must_haves require HTTP 400 for invalid decision
- **Fix:** Request body `decision: str` + use-case allowlist → `InvalidShortlistDecisionError` → 400 `invalid_decision`
- **Files modified:** `backend/src/backend/interface/http/routes/admin.py`
- **Verification:** `test_admin_decision_invalid_body_returns_400` passes
- **Committed in:** `789edf8` (Task 2 feat)

---

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** Correctness for SPA error UX; no scope creep.

## Issues Encountered

Shared-ID gate (#2388): `requirements.ready-ids` reported ADMIN-02/ADMIN-03 not ready (still declared by 05-03/05-04/05-05). Left Pending in REQUIREMENTS.md until sibling plans finish; SUMMARY still lists them under `requirements-completed` as this plan's contribution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 05-03 preview/send with draft-in-pool block on approved∩draft
- SPA can call POST decision and refresh from returned shortlist DTO
- Live `set_decision` adapter still deferred to 05-05

## Self-Check: PASSED

- FOUND: `backend/src/backend/application/use_cases/set_shortlist_decision.py`
- FOUND: `backend/src/backend/interface/http/routes/admin.py` (POST decision)
- FOUND: `tests/unit/test_set_shortlist_decision.py`
- FOUND: commits `29ebae3`, `81a4b47`, `24bb6a6`, `789edf8`
- VERIFY: `uv run pytest tests/unit/test_set_shortlist_decision.py tests/unit/test_http_admin.py -x` → 18 passed

---
*Phase: 05-admin-digest-publish*
*Completed: 2026-09-21*
