---
phase: 24-scheduled-ingestion
plan: 05
subsystem: api
tags: [ingestion-schedule, admin-api, fastapi, supabase, ports-adapters, tdd]

requires:
  - phase: 24-03
    provides: migration 013 public.ingestion_schedule singleton; schedule defaults pattern
provides:
  - backend IngestionSchedule + parse_time_of_day / normalize_days / format_time_of_day
  - IngestionScheduleRepository port + get/update use-cases
  - GET/PATCH /admin/ingestion-schedule on admin router
  - InMemoryIngestionScheduleRepository + SupabaseIngestionScheduleRepository
  - AppContainer.ingestion_schedule wired in-memory and live
affects:
  - 24-06 (ingestScheduleApi.js + IngestionScheduleSection UI)

actuals:
  tokens: 12212
  tasks: 3
  commits: 6

plan_head_before: d76c32b8a6bd4b8d12b5c879df43a623fd6f8720
plan_head_after: 112df0c0a69f0ff9031b92e81457136c990876b6

tech-stack:
  added: []
  patterns:
    - validate-then-persist merge-patch for singleton schedule (extra=forbid → 422)
    - missing DB row → domain defaults on get; first update upserts id=1
    - Russian PipelineConfigError envelope at top-level {errors:[…]}

key-files:
  created:
    - backend/src/backend/domain/ingestion_schedule.py
    - backend/src/backend/application/ports/ingestion_schedule.py
    - backend/src/backend/application/use_cases/ingestion_schedule.py
    - supabase-integration/src/supabase_integration/ingestion_schedule_repository.py
    - tests/unit/test_ingestion_schedule_domain.py
    - tests/unit/test_http_ingestion_schedule.py
    - tests/unit/test_supabase_ingestion_schedule_repository_contract.py
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/interface/http/routes/admin.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/live.py
    - supabase-integration/src/supabase_integration/__init__.py

key-decisions:
  - "Port method is update(...) with full merged fields (not save(schedule)) — matches PLAN over PATTERNS sketch"
  - "Route OpenAPI descriptions omit the detail code so ingestion_schedule_not_configured appears once (in _require_*)"

patterns-established:
  - "Admin schedule surface: Depends(require_admin) + _require_ingestion_schedule → 503 when None"
  - "Supabase adapter: empty select → defaults without write; upsert on_conflict=id always sets updated_at"

requirements-completed: [ING-06]

coverage:
  - id: D1
    description: "Domain parse/normalize/format + validate-before-write use-case with Russian messages"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_ingestion_schedule_domain.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "GET/PATCH /admin/ingestion-schedule auth, defaults, merge-patch, 400/422/503"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_http_ingestion_schedule.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "SupabaseIngestionScheduleRepository get defaults / upsert / PersistenceError; live wiring"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_ingestion_schedule_repository_contract.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_live_container_wiring.py"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-10-18
status: complete
---

# Phase 24 Plan 05: Backend API расписания Summary

**Admin GET/PATCH `/admin/ingestion-schedule` с доменной валидацией (русские сообщения), портом и Supabase-адаптером на `ingestion_schedule(id=1)`.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-10-18T15:27:27Z
- **Completed:** 2026-10-18T15:52:00Z
- **Tasks:** 3/3
- **Files modified:** 13

## Accomplishments

- Домен нормализует `HH:MM`/`HH:MM:SS` → `HH:MM` и дни 1…7 (дедуп + sort); пустой PATCH и невалидный ввод не пишут в repo.
- HTTP: admin-only, top-level `{errors:[…]}` на 400, `extra=forbid` → 422, unwired port → 503 `ingestion_schedule_not_configured`.
- Live composition подключает `SupabaseIngestionScheduleRepository(admin_client)` только из `composition/live.py`.

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1 RED:** `4cc6cd3` — test(24-05): add failing domain tests for ingestion schedule
2. **Task 1 GREEN:** `457e5c6` — feat(24-05): implement ingestion schedule domain and use-case
3. **Task 2 RED:** `ad8a429` — test(24-05): add failing HTTP tests for ingestion schedule
4. **Task 2 GREEN:** `e71c9a5` — feat(24-05): add GET/PATCH /admin/ingestion-schedule
5. **Task 3 RED:** `04d1689` — test(24-05): add failing Supabase schedule repository contract
6. **Task 3 GREEN:** `112df0c` — feat(24-05): add Supabase ingestion schedule adapter and live wiring

## Files Created/Modified

- `backend/src/backend/domain/ingestion_schedule.py` — frozen schedule + parsers
- `backend/src/backend/domain/errors.py` — `IngestionScheduleValidationError`
- `backend/src/backend/application/ports/ingestion_schedule.py` — Protocol get/update
- `backend/src/backend/application/use_cases/ingestion_schedule.py` — merge-patch use-cases
- `backend/src/backend/tests_support/in_memory.py` — `InMemoryIngestionScheduleRepository`
- `backend/src/backend/interface/http/routes/admin.py` — GET/PATCH routes + DTOs
- `backend/src/backend/composition/container.py` / `live.py` — wiring
- `supabase-integration/.../ingestion_schedule_repository.py` + `__init__.py` export
- three unit test modules for domain / HTTP / adapter contract

## Decisions Made

- Port API uses `update(*, enabled, time_of_day, days_of_week)` as specified in PLAN (not PATTERNS `save(schedule)`).
- OpenAPI description text avoids repeating `ingestion_schedule_not_configured` so the detail code appears once in `_require_ingestion_schedule`.

## Deviations from Plan

None - plan executed exactly as written (minor description-string tweak for acceptance grep count=1).

## Threat Flags

None — T-24-20/21/22 mitigations landed (`require_admin`, domain validation + `extra=forbid`, service_role only in composition).

## Known Stubs

None.

## Self-Check: PASSED

- Created artifacts present: domain, port, use-case, adapter, three test files
- Commits `4cc6cd3`…`112df0c` present on branch
- Final verification: 62 passed (domain + HTTP + adapter + ingest_sources + composition + live wiring)
