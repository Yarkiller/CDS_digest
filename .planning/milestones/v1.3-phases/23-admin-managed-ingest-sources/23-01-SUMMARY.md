---
phase: 23-admin-managed-ingest-sources
plan: 01
subsystem: api
tags: [fastapi, pydantic, react, playwright, ports-adapters, ingest-sources, adux-10]

requires:
  - phase: 16-pipe-01-mvp-config-ui
    provides: pipeline-config HTTP/JWT harness, pipelineConfigApi mock pattern, AdminPipelineConfigPage host
  - phase: 19-unsaved-changes-guard-for-the-pipeline-editor
    provides: useUnsavedChangesGuard + UnsavedChangesDialog reused for ADUX-10 dirty OR
  - phase: 22-admin-nav-grouping
    provides: /admin/pipeline host under AdminLayout
provides:
  - IngestSource domain entity + IngestSourceValidationError (D-19 shape)
  - IngestSourceRepository port + list/add use cases + InMemoryIngestSourceRepository
  - AppContainer.ingest_sources wired in build_in_memory_container (D-21)
  - GET/POST /admin/ingest-sources require_admin routes
  - web/src/services/ingestSourcesApi.js + IngestSourcesSection above YAML
  - dirty = yamlDirty || sourceFormDirty with one guard/dialog (ADUX-10)
affects: [23-02, 23-03, 23-04, 24-scheduled-ingestion]

actuals:
  tokens: 13452
  tasks: 2
  commits: 4
  plan_head_before: ca240d56bfade04c5f9001ca92d03e875a6dc2a5
  plan_head_after: 0c37bf79bf99a3afd0efbae59f4f915477695136

tech-stack:
  added: []
  patterns:
    - "Ingest sources vertical slice mirrors pipeline-config: domain → port → use case → in-memory → admin HTTP → SPA service → section"
    - "ADUX-10 dirty OR widens leave guard only; YAML Save/Reset stay gated on yamlDirty"
    - "Playwright ingest harness on window.__DIGEST_INGEST_SOURCES_HARNESS__ with sessionStorage mock list"

key-files:
  created:
    - backend/src/backend/domain/ingest_source.py
    - backend/src/backend/application/ports/ingest_sources.py
    - backend/src/backend/application/use_cases/ingest_sources.py
    - web/src/services/ingestSourcesApi.js
    - web/src/components/IngestSourcesSection.jsx
    - tests/unit/test_http_ingest_sources.py
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/interface/http/routes/admin.py
    - web/src/pages/AdminPipelineConfigPage.jsx
    - web/src/main.jsx
    - tests/unit/test_composition_container.py
    - tests/admin.spec.js

key-decisions:
  - "Tracer ships full happy-path spine in one plan (domain through SPA) before 23-02 reject matrix"
  - "YAML Save/Reset use yamlDirty; combined dirty is leave-guard only (ADUX-10 / D-03)"
  - "HTTP RED uses deferred import of InMemoryIngestSourceRepository so collection succeeds and failures are assertion-level"

patterns-established:
  - "IngestSourceRepository Protocol with list/add/set_enabled/delete; set_enabled/delete implemented in-memory for later plans"
  - "Top-level {errors:[…]} 400 mapper for IngestSourceValidationError (never under detail)"
  - "SPA transport only via ingestSourcesApi.js; no supabase in pages/components"

requirements-completed: [SRC-01, SRC-03, ADUX-10]

coverage:
  - id: D1
    description: "GET empty {sources:[]} and POST valid channel → 201; following GET includes the row"
    requirement: SRC-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_get_returns_empty_sources_list"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_post_channel_then_get_includes_row"
        status: pass
    human_judgment: false
  - id: D2
    description: "GET/POST admin-gated (401/403) and missing repo → 503 ingest_sources_not_configured"
    requirement: SRC-03
    verification:
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_get_post_require_admin_unauth_401_and_employee_403"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_ingest_sources.py#test_missing_ingest_sources_returns_503"
        status: pass
    human_judgment: false
  - id: D3
    description: "build_in_memory_container wires InMemoryIngestSourceRepository on ingest_sources"
    requirement: SRC-03
    verification:
      - kind: unit
        ref: "tests/unit/test_composition_container.py#test_in_memory_container_wires_ingest_sources"
        status: pass
    human_judgment: false
  - id: D4
    description: "Admin sees «Источники ингеста» above YAML; empty → add channel → mono row; D-22 tripwire unchanged"
    requirement: SRC-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#ingest sources section above YAML — empty then add channel row"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config no execution controls render"
        status: pass
    human_judgment: false
  - id: D5
    description: "dirty = yamlDirty || sourceFormDirty with single useUnsavedChangesGuard + UnsavedChangesDialog"
    requirement: ADUX-10
    verification:
      - kind: other
        ref: "web/src/pages/AdminPipelineConfigPage.jsx#yamlDirty||sourceFormDirty"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-10-17
status: complete
---

# Phase 23 Plan 01: Tracer list+add ingest sources Summary

**Admin can list and add a YouTube channel ingest source end-to-end through domain → port → HTTP → SPA service → section above YAML, with ADUX-10 dirty OR wired.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-17T16:26:02Z
- **Completed:** 2026-10-17T16:35:00Z
- **Tasks:** 2/2
- **Files modified:** 14

## Accomplishments

- Happy-path GET/POST `/admin/ingest-sources` with in-memory repository and admin JWT harness (SRC-01, SRC-03).
- SPA section «Источники ингеста» above YAML via `ingestSourcesApi.js` only; Playwright add→row green under mocks.
- Page dirty OR (`yamlDirty || sourceFormDirty`) with one guard/dialog; D-22 execution-control tripwire preserved and green.

## Task Commits

Each task was committed atomically (TDD RED→GREEN per task):

1. **Task 1 RED:** `e1fe0b2` — test(23-01): add failing HTTP tests for ingest sources list/add
2. **Task 1 GREEN:** `712b224` — feat(23-01): implement list+add ingest sources end-to-end
3. **Task 2 RED:** `50a595a` — test(23-01): add failing Playwright journey for ingest sources add
4. **Task 2 GREEN:** `0c37bf7` — feat(23-01): wire ingest sources Playwright harness on window

## Files Created/Modified

- `backend/src/backend/domain/ingest_source.py` — frozen `IngestSource` entity
- `backend/src/backend/domain/errors.py` — `IngestSourceValidationError` (D-19)
- `backend/src/backend/application/ports/ingest_sources.py` — `IngestSourceRepository` Protocol
- `backend/src/backend/application/use_cases/ingest_sources.py` — list + add (D-14 validate-then-persist)
- `backend/src/backend/tests_support/in_memory.py` — `InMemoryIngestSourceRepository` + write log
- `backend/src/backend/composition/container.py` — `ingest_sources` field + in-memory wire
- `backend/src/backend/interface/http/routes/admin.py` — GET/POST routes + DTOs
- `web/src/services/ingestSourcesApi.js` — mock/live list+add + harness
- `web/src/components/IngestSourcesSection.jsx` — section chrome (heading, empty, add, list)
- `web/src/pages/AdminPipelineConfigPage.jsx` — hosts section; dirty OR
- `web/src/main.jsx` — Playwright ingest harness export
- `tests/unit/test_http_ingest_sources.py` — HTTP/auth/503 contracts
- `tests/unit/test_composition_container.py` — D-24 AMEND wiring assert
- `tests/admin.spec.js` — add journey (D-22 tripwire untouched)

## Decisions Made

- Followed plan: tracer happy path only; PATCH/DELETE/full reject matrix deferred to 23-02; migration/live adapter to 23-03.
- Save/Reset buttons remain yaml-only so typing a source id does not arm «Сохранить конфиг».

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] YAML Save must not use combined dirty**
- **Found during:** Task 1 GREEN (AdminPipelineConfigPage dirty OR)
- **Issue:** Using `dirty` (yaml || source form) on Save/Reset would enable YAML save when only the source form was typed.
- **Fix:** Guard leave with combined `dirty`; gate Save/Reset on `yamlDirty` only.
- **Files modified:** `web/src/pages/AdminPipelineConfigPage.jsx`
- **Commit:** `712b224`

**2. [Rule 1 - Bug] HTTP RED avoided ImportError collection INVALID_RED**
- **Found during:** Task 1 RED
- **Issue:** Top-level import of missing `InMemoryIngestSourceRepository` prevented test collection (INVALID_RED).
- **Fix:** Deferred import inside helpers with assertion-level failures on missing field/routes.
- **Files modified:** `tests/unit/test_http_ingest_sources.py`, `tests/unit/test_composition_container.py`
- **Commit:** `e1fe0b2`

## TDD Gate Compliance

| Task | RED commit | GREEN commit | RED evidence |
|------|------------|--------------|--------------|
| 1 HTTP/composition | `e1fe0b2` | `712b224` | AssertionError: AppContainer.ingest_sources field missing (D-21) |
| 2 Playwright | `50a595a` | `0c37bf7` | waitForFunction timeout: `__DIGEST_INGEST_SOURCES_HARNESS__` absent |

## Threat Flags

None — new GET/POST `/admin/ingest-sources` surfaces are covered by plan threat register T-23-01…T-23-05 (require_admin, D-14 validation, SPA service boundary).

## Known Stubs

None that block the tracer goal. Row toggle/delete UI and full id-help UX polish remain for 23-02/23-04 by design.

## Self-Check: PASSED

- All 13 key artifact paths present
- Commits `e1fe0b2`, `712b224`, `50a595a`, `0c37bf7` found in git log
- Verify: `uv run pytest tests/unit/test_http_ingest_sources.py tests/unit/test_composition_container.py -x` → 8 passed
- Verify: Playwright grep ingest/tripwire → 2 passed
