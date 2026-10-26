---
phase: 16-pipe-01-mvp-config-ui
plan: 01
subsystem: api
tags: [fastapi, react, vite, playwright, pytest, ports-and-adapters, yaml, pipeline-config]

# Dependency graph
requires:
  - phase: 12-admin-shortlist-empty-batch-contract
    provides: admin DTO extra=forbid convention (D-09) carried into PipelineConfigSaveRequest/Response
  - phase: 13-admin-material-email-preview-honesty
    provides: AdminDigestPage role-gate/load-state chrome reused by AdminPipelineConfigPage
  - phase: 14-draft-ready-justification-honesty
    provides: admin route family + in-memory fakes in tests_support/in_memory.py
provides:
  - PipelineConfig domain model (yaml, updated_at)
  - PipelineConfigRepository + PipelineConfigValidator ports (one merged module)
  - get_pipeline_config / save_pipeline_config use-cases (validate then persist)
  - InMemoryPipelineConfigRepository + InMemoryPipelineConfigValidator fakes
  - GET/PUT /admin/pipeline/config thin routes behind require_admin
  - pipelineConfigApi.js as the sole SPA transport boundary (PIPE-03)
  - AdminPipelineConfigPage + admin/pipeline route (raw-YAML editor, Save toolbar)
  - backend route/auth/DTO unit harness + Playwright happy-path coverage
affects: [16-02 validation depth, 16-03 live persistence, 16-04 full page surface]

actuals:
  tokens: 7230   # chars/4 over the realized diff (28,922 added chars)
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Merged capability port module: repository + validator Protocols side by side (application/ports/pipeline_config.py)"
    - "Validate-then-persist use-case: validator port called before repo.save (no silent accept)"
    - "Test-attached post-build fakes: container.pipeline_config = InMemory... on a plain dataclass (16-01 defers container field declaration to 16-02)"
    - "sessionStorage-backed mock so a page reload re-reads the saved config (PIPE-03 reload proof)"

key-files:
  created:
    - backend/src/backend/domain/pipeline_config.py
    - backend/src/backend/application/ports/pipeline_config.py
    - backend/src/backend/application/use_cases/pipeline_config.py
    - backend/src/backend/interface/http/routes/admin.py (GET/PUT additions)
    - web/src/services/pipelineConfigApi.js
    - web/src/pages/AdminPipelineConfigPage.jsx
    - tests/unit/test_http_pipeline_config.py
    - tests/admin.spec.js (pipeline describe)
  modified:
    - backend/src/backend/interface/http/routes/admin.py
    - backend/src/backend/tests_support/in_memory.py
    - web/src/App.jsx

key-decisions:
  - "16-01 attaches the tracer fakes to the container post-build; AppContainer field declaration + build_in_memory_container wiring stay in 16-02 (plan-locked)"
  - "PUT reject branch (PipelineConfigValidationError -> structured 400 {errors:[...]}) is deliberately deferred to 16-02; 16-01 proves the happy path only"
  - "Mock config is persisted to sessionStorage so a page reload proves the round-trip without adding a reload control in the tracer surface"
  - "The local mock cutover helper is named mocksEnabled (not useMocks) to avoid adding react-hooks lint false positives already present in adminApi.js/authApi.js"

patterns-established:
  - "Pipeline config slice: domain -> merged ports -> merged use-case -> thin admin routes -> SPA service -> page -> route"
  - "DTO boundary assertion: every GET/PUT success body must expose exactly {yaml, updated_at}"

requirements-completed: [PIPE-01, PIPE-03]

coverage:
  - id: D1
    description: "Admin-only GET/PUT /admin/pipeline/config round-trip: saved config read back, empty state, 401/403 gate, 503 guard, DTO exposes exactly {yaml, updated_at}"
    requirement: PIPE-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_pipeline_config.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "SPA reaches the config only through web/src/services/pipelineConfigApi.js (fetchPipelineConfig/savePipelineConfig)"
    requirement: PIPE-03
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config happy path"
        status: pass
    human_judgment: true
    rationale: "The E2E exercises the service end-to-end, but no automated import-boundary guard ships in 16-01; the PIPE-03 boundary guard is 16-04-T1"
  - id: D3
    description: "Admin at /admin/pipeline sees the raw-YAML editor, edits, saves («Сохранено»), and a reload read returns the saved YAML; no execution control renders"
    requirement: PIPE-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config happy path"
        status: pass
    human_judgment: false
  - id: D4
    description: "No run/trigger/scheduler control ships in the pipeline-config surface (PIPE-EXEC-* deferral)"
    requirement: PIPE-01
    verification: []
    human_judgment: true
    rationale: "16-01 asserts the scope subhead only; the banned-control absence assertion is 16-04's no-execution Playwright case"

# Metrics
duration: 5min
completed: 2026-10-04
status: complete
commits: 3
plan_head_before: 038bc642e47ef8125e43613640abb99a9db34b77
plan_head_after: 8213ff842e6b093d2e6402fb27e46a506bd95cc5
---

# Phase 16 Plan 01: Tracer — view + save pipeline config end-to-end Summary

**Admin-only GET/PUT pipeline-config route with a raw-YAML editor, validate-then-persist use-case behind a repository port, and the SPA reaching storage only through `pipelineConfigApi.js` — no execution control ships**

## Performance

- **Duration:** 5 min
- **Started:** 2026-10-04T10:37:26Z
- **Completed:** 2026-10-04T10:42:38Z
- **Tasks:** 2 (tracer + Playwright)
- **Files modified:** 10 (893 insertions)

## Accomplishments
- `PipelineConfig` domain model + merged `PipelineConfigRepository`/`PipelineConfigValidator` ports + `get_pipeline_config`/`save_pipeline_config` use-cases (validate before persist)
- GET/PUT `/admin/pipeline/config` thin routes behind `require_admin`, returning the `{yaml, updated_at}` DTO with `extra="forbid"`; absent row → empty state; missing port → 503 `pipeline_config_not_configured`
- `pipelineConfigApi.js` as the sole SPA transport boundary (mock/live cutover, no silent mock fallback) + minimal `AdminPipelineConfigPage` (role gate, raw monospace editor, Save toolbar, status caption) + `admin/pipeline` route
- Backend route/auth/DTO/503 unit harness (6 tests) and Playwright happy-path coverage (load → edit → save «Сохранено» → reload read returns the saved YAML)
- Full backend suite green: **726 passed**; full `tests/admin.spec.js` green: **37 passed**

## Task Commits

Each task was committed atomically; the tracer ran the RED→GREEN cycle:

1. **Task 1 RED** — `41187e5` (test): add failing tests for pipeline config read+save route
2. **Task 1 GREEN** — `d27121c` (feat): implement pipeline config view+save end-to-end slice
3. **Task 2** — `8213ff8` (test): add Playwright pipeline config happy-path coverage

**Plan metadata:** final `docs(16-01)` metadata commit (SUMMARY + STATE + ROADMAP).

_Note: no REFACTOR commit was needed — the GREEN implementation was already minimal._

## Files Created/Modified
- `backend/src/backend/domain/pipeline_config.py` — `PipelineConfig(yaml, updated_at)` frozen dataclass
- `backend/src/backend/application/ports/pipeline_config.py` — repository + validator Protocols (merged)
- `backend/src/backend/application/use_cases/pipeline_config.py` — `get_pipeline_config` / `save_pipeline_config`
- `backend/src/backend/tests_support/in_memory.py` — `InMemoryPipelineConfigRepository` + call-recording `InMemoryPipelineConfigValidator`
- `backend/src/backend/interface/http/routes/admin.py` — `PipelineConfigSaveRequest`, `PipelineConfigResponse`, `_require_pipeline_config`, `read_pipeline_config`, `put_pipeline_config`
- `web/src/services/pipelineConfigApi.js` — `PipelineConfigError`, `fetchPipelineConfig`, `savePipelineConfig`
- `web/src/pages/AdminPipelineConfigPage.jsx` — minimal tracer page (editor + Save toolbar + states)
- `web/src/App.jsx` — `admin/pipeline` route inside `RequireAuth` + `AppShell`
- `tests/unit/test_http_pipeline_config.py` — route/auth/DTO/round-trip/503 harness
- `tests/admin.spec.js` — pipeline config describe block

## Decisions Made
- Kept `composition/container.py` untouched: the tracer attaches `container.pipeline_config` / `container.pipeline_config_validator` in tests post-build; field declaration and `build_in_memory_container` wiring remain 16-02's slice (plan-locked).
- Deferred the `PipelineConfigValidationError` → structured `400 {errors:[...]}` reject branch to 16-02; the tracer must not import the validator adapter.
- Persisted the mock config to `sessionStorage` so `page.reload()` re-reads the saved YAML without adding a reload control to the minimal tracer surface.
- Named the service mock cutover helper `mocksEnabled` (not `useMocks`) so the new module adds no new `react-hooks` lint false positives.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The RED run surfaced as a pytest collection error (`ModuleNotFoundError: backend.domain.pipeline_config`) because the production modules did not exist yet — the expected RED cause for a tracer whose source is written after the test. Fixed by the GREEN implementation (6/6 tests pass).

## Known Stubs

| Stub | File | Line | Reason |
|------|------|------|--------|
| PUT `/admin/pipeline/config` has no `PipelineConfigValidationError` reject branch | `backend/src/backend/interface/http/routes/admin.py` | 563 | Deliberately deferred to 16-02 (plan-locked): 16-01 proves the happy path only and must not import the validator adapter. Recorded in `.planning/WINDOWS.md`. |

## Threat Flags

None — the tracer adds only the planned `/admin/pipeline/config` surface; both routes sit behind the existing `require_admin` gate and the response DTO declares exactly `{yaml, updated_at}` (T-16-01 / T-16-14 mitigated; no new trust boundary beyond the planned one).

## User Setup Required

None - no external service configuration required (live migration `011` is 16-03's `user_setup`).

## Next Phase Readiness
- The architectural spine (domain → ports → use-case → route → SPA service → page → route) is proven end-to-end; 16-02 can fill strict YAML/schema validation behind the same `PipelineConfigValidator` port and wire the container fields.
- REQUIREMENTS.md PIPE-01/PIPE-03 are **not** marked complete yet: the shared-ID gate (`requirements.ready-ids`) reports 0/2 ready because sibling plans 16-03 (PIPE-03) and 16-04 (PIPE-01, PIPE-03) have not produced summaries.

---
*Phase: 16-pipe-01-mvp-config-ui*
*Completed: 2026-10-04*

## Self-Check: PASSED

All 7 declared created files exist on disk and all 3 plan commits (`41187e5`, `d27121c`, `8213ff8`) are present in `git log`.
