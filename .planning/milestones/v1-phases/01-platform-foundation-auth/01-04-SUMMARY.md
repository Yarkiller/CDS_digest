---
phase: 01-platform-foundation-auth
plan: 04
subsystem: database
tags: [supabase, adapters, activity-events, profiles, composition, service-role]

requires:
  - phase: 01-platform-foundation-auth
    provides: PingRecorder + ProfileRepository ports, in-memory HTTP tracer, Settings/JWKS fields
provides:
  - SupabasePingRecorder inserting activity_events kind platform_ping
  - SupabaseProfileRepository get_or_upsert with app_role
  - build_live_container + APP_CONTAINER=live|memory selection
  - README Local platform + manual Auth seed docs (D-08)
affects:
  - 01-05 SPA auth/API clients
  - 01-06 live FE↔BE proof (needs Auth test users)

actuals:
  tokens: 7178
  tasks: 3
  commits: 5

tech-stack:
  added: [supabase==2.31.0]
  patterns:
    - create_*_client helpers only in supabase_integration/client.py; wired in composition/live.py
    - APP_CONTAINER env selects memory vs live; unit suite stays offline

key-files:
  created:
    - supabase-integration/src/supabase_integration/client.py
    - supabase-integration/src/supabase_integration/ping_recorder.py
    - supabase-integration/src/supabase_integration/profile_repository.py
    - backend/src/backend/composition/live.py
    - tests/unit/test_supabase_ping_recorder_contract.py
    - tests/unit/test_live_container_wiring.py
  modified:
    - supabase-integration/src/supabase_integration/__init__.py
    - supabase-integration/pyproject.toml
    - backend/src/backend/domain/errors.py
    - backend/src/backend/composition/settings.py
    - backend/src/backend/composition/__init__.py
    - backend/src/backend/interface/http/app.py
    - README.md
    - .env.example
    - uv.lock

key-decisions:
  - "APP_CONTAINER=memory|live (default memory) selects builder; create_default_app uvicorn factory"
  - "service_role client constructed only in composition/live.py; adapters receive injected client"
  - "Auth dashboard user seed deferred to Plan 01-06 live proof (orchestrator USER_SETUP note)"

patterns-established:
  - "Offline fake table-chain stubs for supabase-integration unit contracts"
  - "PersistenceError maps SDK failures at adapter boundary"

requirements-completed: [PLAT-01, PLAT-04, AUTH-01]

coverage:
  - id: D1
    description: "SupabasePingRecorder inserts activity_events with kind platform_ping via stubbed client"
    requirement: PLAT-04
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_ping_recorder_contract.py#test_ping_recorder_inserts_platform_ping_payload"
        status: pass
    human_judgment: false
  - id: D2
    description: "SupabaseProfileRepository get_or_upsert returns app_role and is idempotent"
    requirement: AUTH-01
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_ping_recorder_contract.py#test_profile_get_or_upsert_returns_app_role_shape"
        status: pass
    human_judgment: false
  - id: D3
    description: "build_live_container wires Supabase adapters; create_client only under composition"
    requirement: PLAT-04
    verification:
      - kind: unit
        ref: "tests/unit/test_live_container_wiring.py#test_build_live_container_wires_supabase_adapters"
        status: pass
    human_judgment: false
  - id: D4
    description: "README documents remote VM connectivity, APP_CONTAINER=live, manual Auth seed (PLAT-01/D-08)"
    requirement: PLAT-01
    verification:
      - kind: other
        ref: "README.md#Local platform"
        status: pass
    human_judgment: false
  - id: D5
    description: "Manual corporate Auth users on shared Supabase dashboard"
    requirement: PLAT-01
    verification: []
    human_judgment: true
    rationale: "D-08 forbids automated seed against shared VM; deferred to Plan 01-06 live proof"

duration: 12min
completed: 2026-09-19
status: complete
---

# Phase 01 Plan 04: Live Supabase Adapters Summary

**Supabase profile + ping adapters and env-selected live composition are green offline; Auth dashboard seed is deferred for Plan 01-06 live proof.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-09-19T15:22:34Z
- **Completed:** 2026-09-19T15:35:00Z
- **Tasks:** 2/2 code tasks complete; Task 3 (Auth seed) deferred as user_setup
- **Files modified:** 15

## Accomplishments

- `supabase` 2.31.0 in `supabase-integration` with `create_publishable_client` / `create_service_role_client`
- `SupabasePingRecorder` → `activity_events` (`kind=platform_ping`); `SupabaseProfileRepository` upserts `profiles` (`app_role`)
- `build_live_container` + `APP_CONTAINER=live|memory`; `create_default_app` uvicorn factory; README Local platform
- Unit suite: **52 passed** (offline stubs; no live network required)

## Task Commits

1. **Task 1 RED:** `6496ad1` — `test(01-04): add failing contract tests for Supabase adapters`
2. **Task 1 GREEN:** `62edca7` — `feat(01-04): implement Supabase profile and ping adapters`
3. **Task 2 RED:** `a53bc37` — `test(01-04): add failing tests for live container wiring`
4. **Task 2 GREEN:** `6c46f03` — `feat(01-04): wire live composition and APP_CONTAINER selection`
5. **Task 3:** deferred — Auth dashboard seed (see User Setup)

**Plan metadata:** (docs commit after state update)

## Files Created/Modified

- `supabase-integration/.../client.py` — client factories
- `supabase-integration/.../ping_recorder.py` — PingRecorder adapter
- `supabase-integration/.../profile_repository.py` — ProfileRepository adapter
- `backend/.../composition/live.py` — `build_live_container` (service_role only here)
- `backend/.../composition/settings.py` — `APP_CONTAINER` + existing JWKS fields
- `backend/.../interface/http/app.py` — `resolve_container` / `create_default_app`
- `backend/.../domain/errors.py` — `PersistenceError`
- `README.md` / `.env.example` — Local platform + `APP_CONTAINER`
- Unit: `test_supabase_ping_recorder_contract.py`, `test_live_container_wiring.py`

## Decisions Made

- `APP_CONTAINER=memory` default keeps Plans 01–03 TestClient path offline; `live` for ping persistence proof
- Adapters take an injected client Protocol — no network in default pytest
- Auth user creation left to human (D-08); not blocking code must_haves

## Deviations from Plan

### Auto-fixed Issues

None beyond test-path adjustment for lazy import of `build_live_container` in `resolve_container` (monkeypatch target `backend.composition.live.build_live_container`).

### Deferred / Orchestrator USER_SETUP

**1. [Task 3 checkpoint:human-action] Auth dashboard seed not blocking this wave**
- **Found during:** Task 3
- **Issue:** Plan marks `autonomous: false` for creating 1–2 corporate Auth users on knowledge-db.ru.
- **Action:** Implemented all code + offline unit/contract tests; documented seed steps in README. Deferred interactive dashboard confirmation to Plan 01-06 live FE↔BE proof per orchestrator note.
- **Files:** README.md (Local platform section)
- **Commit:** `6c46f03`

**Total deviations:** 1 deferred user_setup (intentional)
**Impact on plan:** Code must_haves met; live Auth users remain for Plan 06.

## Issues Encountered

- Optional MCP `list_triggers` for `auth.users` → `profiles` required `POSTGRES_URL` — unavailable; documented that `get_or_upsert` stays the idempotent safety net either way.

## User Setup Required

| Item | Status | Needed for |
|------|--------|------------|
| Create 1–2 Auth users (`@sberbank.ru` / `@omega.sbrf.ru`) on knowledge-db.ru dashboard | **Deferred** | Plan 01-06 live proof |
| Optional Auth email-domain allowlist/hook | Optional; else UI+API gates (D-04) | Hardening |
| Copy `.env.example` → `.env`, set `APP_CONTAINER=live` for live API | Operator when running live | Local live ping persistence |

## Next Phase Readiness

Ready for Plan 01-05 (SPA auth/API clients). Live adapters and composition exist; Auth users must exist before Plan 01-06 end-to-end live proof.

## TDD Gate Compliance

- RED commits: `6496ad1`, `a53bc37`
- GREEN commits: `62edca7`, `6c46f03`
- Gates satisfied for Tasks 1–2.

## Known Stubs

None that block plan goals. Materials/chunks remain in-memory in live container (Phase 1 intentional per plan).

## Threat Flags

None beyond plan threat model — service_role confined to `composition/live.py`; no new public endpoints.

## Self-Check: PASSED

- FOUND: supabase-integration/src/supabase_integration/ping_recorder.py
- FOUND: supabase-integration/src/supabase_integration/profile_repository.py
- FOUND: backend/src/backend/composition/live.py
- FOUND: tests/unit/test_supabase_ping_recorder_contract.py
- FOUND: tests/unit/test_live_container_wiring.py
- FOUND: 6496ad1, 62edca7, a53bc37, 6c46f03
- Unit suite: 52 passed (`uv run pytest tests/unit`)

---
*Phase: 01-platform-foundation-auth*
*Completed: 2026-09-19*
