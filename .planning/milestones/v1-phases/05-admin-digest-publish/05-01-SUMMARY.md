---
phase: 05-admin-digest-publish
plan: 01
subsystem: api
tags: [fastapi, require_admin, shortlist, app_role, profiles, tdd, ports-adapters]

requires:
  - phase: 01-platform-foundation-auth
    provides: JWT get_principal, ProfileRepository, in-memory container, /me routes
  - phase: 03-voting-cycle
    provides: HTTP route + Depends gate patterns (voting.py analog)
provides:
  - require_admin Depends from profiles.role
  - GET /admin/shortlist with ≤5 ranked items + factor honesty
  - ShortlistRepository port + InMemoryShortlistRepository
  - GET /me.role as app_role (employee default; admin when seeded)
  - meApi mock employee + setMockMeRole harness
affects:
  - 05-02 approve/reject decision API
  - 05-04 AdminDigestPage + AppShell admin nav
  - 05-05 live ShortlistRepository + migration 005

actuals:
  tokens: 11865
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "require_admin: get_principal → ProfileRepository → role==admin else 403"
    - "ShortlistRepository.get_current_batch → get_admin_shortlist use-case → HTTP DTO"
    - "ADMIN-05 honesty: ≥2 readable factor labels or empty list for «обоснование недоступно»"
    - "app_role on /me from profiles — never JWT role claim (D-76)"

key-files:
  created:
    - backend/src/backend/domain/shortlist.py
    - backend/src/backend/application/ports/shortlist_repository.py
    - backend/src/backend/application/use_cases/get_admin_shortlist.py
    - backend/src/backend/interface/http/routes/admin.py
    - tests/unit/test_http_admin.py
    - tests/unit/test_get_admin_shortlist.py
    - tests/unit/test_score_factors.py
  modified:
    - backend/src/backend/interface/http/deps.py
    - backend/src/backend/interface/http/app.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/live.py
    - backend/src/backend/domain/current_user.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/interface/http/routes/me.py
    - web/src/services/meApi.js
    - tests/unit/test_http_me.py
    - tests/unit/test_composition_container.py

key-decisions:
  - "Authorize admin only via profiles.role through require_admin — never JWT role claim (D-74, T-05-01)"
  - "Default app_role employee on CurrentUser / in-memory / meApi to match live _DEFAULT_APP_ROLE (D-76)"
  - "Empty shortlist batch returns 200 items=[] for D-80 SPA empty state — not 404"
  - "factor_labels empty when <2 readable labels so UI shows honesty copy (ADMIN-05 / D-79)"

patterns-established:
  - "Pattern: require_admin Depends for all /admin/* routes"
  - "Pattern: ShortlistRepository port with in-memory fake; live adapter deferred to 05-05"
  - "Pattern: meApi setMockMeRole harness for SPA admin nav under mocks"

requirements-completed: [ADMIN-01, ADMIN-05]

coverage:
  - id: D1
    description: "Admin JWT + profiles.role=admin GET /admin/shortlist returns ≤5 ranked items with draft/ready, score, and factor_labels or honesty empty"
    requirement: ADMIN-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_shortlist_returns_ranked_items"
        status: pass
      - kind: unit
        ref: "tests/unit/test_get_admin_shortlist.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Non-admin authenticated caller gets HTTP 403 on GET /admin/shortlist — never empty shortlist JSON"
    requirement: ADMIN-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_employee_gets_403_on_admin_shortlist"
        status: pass
    human_judgment: false
  - id: D3
    description: "ADMIN-05 score_factors honesty — ≥2 readable labels returned; 0 or 1 → empty factor_labels"
    requirement: ADMIN-05
    verification:
      - kind: unit
        ref: "tests/unit/test_score_factors.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "GET /me.role is app_role employee by default; seeded admin returns admin (D-76)"
    requirement: ADMIN-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_me.py#test_me_with_valid_corporate_jwt_returns_current_user"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_me.py#test_me_with_seeded_admin_profile_returns_role_admin"
        status: pass
    human_judgment: false
  - id: D5
    description: "Empty current batch returns 200 with items=[] for «Кандидатов пока нет»"
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_empty_batch_returns_empty_items"
        status: pass
    human_judgment: false
  - id: D6
    description: "Long titles/factor strings wrap without horizontal scroll; 44px targets usable"
    verification: []
    human_judgment: true
    rationale: "Layout/backstop visual — deferred to SPA plan 05-04 / Playwright 05-06"

duration: 20min
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 01: Admin Shortlist Tracer Summary

**Ports & Adapters admin shortlist GET behind `require_admin` (profiles.role) plus `/me` app_role alignment to employee/admin**

## Performance

- **Duration:** 20min (Task 1 + Task 2 continuation after human-verify)
- **Started:** 2026-09-21T14:18:00Z (approx Task 1 RED)
- **Completed:** 2026-09-21T14:34:32Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments

- Vertical slice: `ShortlistRepository` → `get_admin_shortlist` → `GET /admin/shortlist` gated by `require_admin`
- Employee → 403; admin → ≤5 ranked items; empty batch → `items=[]`; PersistenceError → 503
- ADMIN-05 factor honesty helper: ≥2 labels or empty list for UI «обоснование недоступно»
- Wave-0 D-76: `/me.role` and meApi mocks expose `app_role` (default `employee`), not JWT `"authenticated"`

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end admin shortlist GET** — `627555f` (test) → `1f6b03b` (feat)
2. **Task 2: Align /me.role and meApi mocks to app_role** — `5310f29` (test) → `c927aa0` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks use test → feat commit pairs_

## Files Created/Modified

- `backend/src/backend/domain/shortlist.py` — ShortlistBatch/Item DTOs + factor honesty helper
- `backend/src/backend/application/ports/shortlist_repository.py` — Protocol
- `backend/src/backend/application/use_cases/get_admin_shortlist.py` — pure use-case
- `backend/src/backend/interface/http/deps.py` — `require_admin`
- `backend/src/backend/interface/http/routes/admin.py` — `GET /admin/shortlist`
- `backend/src/backend/domain/current_user.py` — default role `employee`
- `backend/src/backend/tests_support/in_memory.py` — InMemoryShortlistRepository + employee default
- `web/src/services/meApi.js` — mock `employee` + `setMockMeRole` harness via `isMocksEnabled`
- `tests/unit/test_http_admin.py`, `test_get_admin_shortlist.py`, `test_score_factors.py`, `test_http_me.py` — contracts

## Decisions Made

- Admin authorization only from `profiles.role` via `require_admin` (D-74); JWT `role` remains Supabase `"authenticated"` claim only
- Default memory/profile role `employee` to match live `_DEFAULT_APP_ROLE` (D-76)
- meApi exposes `setMockMeRole` for later SPA admin-nav plans without authorizing from JWT

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated composition container test for employee default**
- **Found during:** Task 2 (RED)
- **Issue:** `test_composition_container.py` still asserted `role == "authenticated"`; would fail after GREEN default change
- **Fix:** Assert `employee` alongside `test_http_me` RED updates
- **Files modified:** `tests/unit/test_composition_container.py`
- **Verification:** pytest green with Task 2 suite
- **Committed in:** `5310f29` (Task 2 RED)

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Necessary for green suite; no scope creep.

## Auth Gates

None — human-verify checkpoint after Task 1 tracer approved by user (`approved`); Task 2 continued.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 05-02 approve/reject decision API on shortlist items
- SPA admin nav can read `/me.role` / `setMockMeRole('admin')` once AppShell lands in 05-04
- Live ShortlistRepository + migration 005 still deferred to 05-05

## Self-Check: PASSED

- FOUND: `backend/src/backend/interface/http/routes/admin.py`
- FOUND: `backend/src/backend/interface/http/deps.py` (`require_admin`)
- FOUND: `tests/unit/test_http_admin.py`
- FOUND: commits `627555f`, `1f6b03b`, `5310f29`, `c927aa0`
- VERIFY: `uv run pytest tests/unit/test_http_admin.py tests/unit/test_get_admin_shortlist.py tests/unit/test_score_factors.py tests/unit/test_http_me.py -x` → 21 passed

---
*Phase: 05-admin-digest-publish*
*Completed: 2026-09-21*
