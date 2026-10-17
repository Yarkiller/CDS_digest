---
phase: 23-admin-managed-ingest-sources
plan: 04
subsystem: ui
tags: [react, playwright, ingest-sources, adux-10, unsaved-changes, src-01, src-02]

requires:
  - phase: 23-admin-managed-ingest-sources
    provides: list+add tracer section, dirty OR host, PATCH/DELETE SPA transport, mock harness
provides:
  - Full IngestSourcesSection UI-SPEC chrome (empties, id help, row actions, errors, no optimistic updates)
  - Playwright lifecycle + ADUX-10 sourceFormDirty coverage with D-22 tripwire preserved
affects: [24-scheduled-ingestion]

actuals:
  tokens: 5690
  tasks: 2
  commits: 3
  plan_head_before: 6038d842a7a6af87d323c8daf81e6761cba02c54
  plan_head_after: 686984543a230d998c6c17335391e2bbd017b082

tech-stack:
  added: []
  patterns:
    - "Row PATCH/DELETE disable in-flight controls only; failure keeps last server state + inline error (D-05)"
    - "YouTube href built only from stored kind + source_id with fixed path prefixes + rel=noopener noreferrer"
    - "ADUX-10 proven via Playwright against existing dirty OR — no second guard or leave dialog"

key-files:
  created: []
  modified:
    - web/src/components/IngestSourcesSection.jsx
    - web/src/services/ingestSourcesApi.js
    - web/src/main.jsx
    - tests/admin.spec.js

key-decisions:
  - "Task 2 needed no AdminPipelineConfigPage change — dirty OR from 23-01 already correct; ADUX-10 closed by Playwright only"
  - "Toggle/delete network errors use UI-SPEC copy «Не удалось обновить источник. Повторите действие.» (shared for both actions)"

patterns-established:
  - "armFailNextSetEnabled / armFailNextDelete on __DIGEST_INGEST_SOURCES_HARNESS__ for D-05 failure paths"
  - "resetIngestSourcesMock helper shared across ingest Playwright cases"

requirements-completed: [SRC-01, SRC-02, ADUX-10]

coverage:
  - id: D1
    description: "Disable→enable status text, zero-enabled hint, confirm delete removes row, YouTube link attrs"
    requirement: SRC-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#ingest source disable enable delete and zero-enabled hint"
        status: pass
    human_judgment: false
  - id: D2
    description: "Id short hint + «Где взять id?» disclosure with channel and playlist recipes"
    requirement: SRC-02
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#ingest source id-help disclosure shows channel and playlist recipes"
        status: pass
    human_judgment: false
  - id: D3
    description: "Add 400 structured errors keep typed values; toggle failure keeps prior state + inline error"
    requirement: SRC-02
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#ingest source add reject keeps typed values and shows structured errors"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#ingest source toggle failure keeps prior state and shows inline error"
        status: pass
    human_judgment: false
  - id: D4
    description: "sourceFormDirty id/label arms Phase 19 dialog; kind-only does not; successful add disarms"
    requirement: ADUX-10
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#sourceFormDirty id arms Phase 19 guard on Дайджест leave"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#sourceFormDirty label arms Phase 19 guard; kind-only does not"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#successful add clears sourceFormDirty so leave proceeds without dialog"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-22 no-execution-controls tripwire body preserved and green"
    requirement: SRC-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config no execution controls render"
        status: pass
    human_judgment: false
  - id: D6
    description: "120-char label and expanded id-help wrap without horizontal overflow"
    verification: []
    human_judgment: true
    rationale: "UI-SPEC backstops — visual wrap at narrow widths not automated in Playwright suite"

duration: 12min
completed: 2026-10-17
status: complete
---

# Phase 23 Plan 04: Full sources UI + ADUX-10 dirty coverage Summary

**IngestSourcesSection ships full UI-SPEC chrome (toggle/delete/YouTube/empties/id-help/errors) with Playwright proving ADUX-10 against the existing Phase 19 leave guard.**

## Performance

- **Duration:** 12min
- **Started:** 2026-10-17T17:42:00Z
- **Completed:** 2026-10-17T17:47:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Full row chrome: mono `source_id`, kind, «включён»/«выключен», Включить/Выключить, Удалить + confirm, Открыть на YouTube (`noopener`)
- Empty vs zero-enabled states; id short hint + «Где взять id?» recipes; structured add reject + toggle failure paths without optimistic UI
- ADUX-10 Playwright: id/label arm Phase 19 dialog; kind-only does not; successful add clears dirty; D-22 tripwire untouched and green

## Task Commits

Each task was committed atomically:

1. **Task 1: Complete IngestSourcesSection per UI-SPEC** — RED `42067b9` (test) → GREEN `83c8265` (feat)
2. **Task 2: Playwright ADUX-10 sourceFormDirty** — `6869845` (test; host dirty OR already correct from 23-01)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `web/src/components/IngestSourcesSection.jsx` — row actions, empties, id help, errors, no optimistic updates
- `web/src/services/ingestSourcesApi.js` — `armFailNextSetEnabled` / `armFailNextDelete`; UI-SPEC row-error copy
- `web/src/main.jsx` — expose new arms on `__DIGEST_INGEST_SOURCES_HARNESS__`
- `tests/admin.spec.js` — lifecycle + ADUX-10 cases; D-22 tripwire body PRESERVE

## Decisions Made

- No second Save or second leave dialog — single `useUnsavedChangesGuard(dirty)` retained
- Task 2 production fix unnecessary: `sourceFormDirty = id.trim() || label.trim()` already matches D-04

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written. Minor Rule 2 alignment: delete/toggle mock+live error strings unified to UI-SPEC «Не удалось обновить источник. Повторите действие.» so failure Playwright asserts one copy.

## Known Stubs

None.

## Threat Flags

None beyond plan register (T-23-16…T-23-20 mitigated in this plan's UI).

## Self-Check: PASSED

- FOUND: `web/src/components/IngestSourcesSection.jsx`
- FOUND: `web/src/services/ingestSourcesApi.js`
- FOUND: `tests/admin.spec.js`
- FOUND commits: `42067b9`, `83c8265`, `6869845`
- VERIFY: `npm run test:web -- tests/admin.spec.js -g "ingest source|…|pipeline config no execution controls"` → 13 passed
