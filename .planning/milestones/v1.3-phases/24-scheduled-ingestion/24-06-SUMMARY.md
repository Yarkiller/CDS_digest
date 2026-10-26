---
phase: 24-scheduled-ingestion
plan: 06
subsystem: ui
tags: [ingestion-schedule, admin-ui, playwright, react, immediate-save, tdd]

requires:
  - phase: 24-05
    provides: GET/PATCH /admin/ingestion-schedule DTO contract (enabled, time_of_day, days_of_week)
provides:
  - ingestScheduleApi.js (fetch/patch + mock harness arms + patchCount)
  - IngestionScheduleSection («Автоматический сбор») between sources and YAML
  - window.__DIGEST_INGESTION_SCHEDULE_HARNESS__
  - Playwright describe «Admin pipeline — automatic collection»
affects:
  - phase-24 verification / UAT for ING-06

actuals:
  tokens: 7598
  tasks: 2
  commits: 4

plan_head_before: 878297ea2c7afec760d99f82bfe44b2f22dd3f1e
plan_head_after: c3b92bd40cdc689adb7a0b43b21c2d0077da05ca

tech-stack:
  added: []
  patterns:
    - immediate PATCH with server-response render (no scheduleDirty)
    - time blur-only save; days refuse empty week client-side before network
    - page-owned loadSchedule + onRetry; component never imports fetchIngestionSchedule

key-files:
  created:
    - web/src/services/ingestScheduleApi.js
    - web/src/components/IngestionScheduleSection.jsx
  modified:
    - web/src/pages/AdminPipelineConfigPage.jsx
    - web/src/main.jsx
    - tests/admin.spec.js

key-decisions:
  - "dirty stays yamlDirty || sourceFormDirty — schedule never arms leave dialog (D-16)"
  - "Empty-week validation message is shown alone in status (not prefixed with Включён/Выключен)"
  - "Harness exposes readIngestionScheduleMock for patchCount assertions (Task 2 blur contract)"

patterns-established:
  - "Schedule SPA transport mirrors ingestSourcesApi mock/live + sessionStorage arms"
  - "IngestionScheduleSection props: schedule, onScheduleChange, onLoadError, onRetry — page owns loader"

requirements-completed: [ING-06]

coverage:
  - id: D1
    description: "Блок «Автоматический сбор» между источниками и YAML; harness; немедленный PATCH переключателя; PRESERVE no-execution"
    requirement: ING-06
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#ingestion schedule sits between sources and YAML editor"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#ingestion schedule toggle patches immediately"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#pipeline config no execution controls render"
        status: pass
    human_judgment: false
  - id: D2
    description: "Время по blur; дни с отказом пустой недели; откат при ошибке save/load; не dirty"
    requirement: ING-06
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#ingestion schedule time saves on blur, not on each keystroke"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#ingestion schedule days normalize and refuse an empty week"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#ingestion schedule save failure keeps the value and shows the message"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#ingestion schedule load failure shows an error state without a fake success"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#ingestion schedule changes do not mark the page dirty"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_ingestion_schedule.py"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-10-18
status: complete
---

# Phase 24 Plan 06: Блок «Автоматический сбор» Summary

**Админ на `/admin/pipeline` настраивает автоматический сбор (переключатель, время МСК, дни) с немедленным PATCH и честным откатом — без кнопки запуска и без влияния на YAML-dirty.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-18T12:36:58Z
- **Completed:** 2026-10-18T12:48:00Z
- **Tasks:** 2/2
- **Files modified:** 5 (+ red-evidence)

## Accomplishments

- Блок `ingestion-schedule-section` между «Источники ингеста» и YAML-редактором; заголовок «Автоматический сбор»; PRESERVE-трипваер зелёный.
- `ingestScheduleApi.js` — единственный транспорт к `GET`/`PATCH /admin/ingestion-schedule` (mock + live + армы).
- Немедленное сохранение: toggle / blur времени / дни; пустая неделя отклоняется локально; ошибки save/load с откатом и retry через page `onRetry`.

## Task Commits

1. **Task 1 RED:** `79f1052` — test(24-06): add failing Playwright tests for automatic collection block
2. **Task 1 GREEN:** `d7ddcdf` — feat(24-06): add automatic collection block on admin pipeline
3. **Task 2 RED:** `aa106ef` — test(24-06): add failing tests for schedule time, days, errors, dirty
4. **Task 2 GREEN:** `c3b92bd` — feat(24-06): show empty-week validation alone in schedule status

## Files Created/Modified

- `web/src/services/ingestScheduleApi.js` — DTO, IngestScheduleError, fetch/patch, mock store + patchCount, arms
- `web/src/components/IngestionScheduleSection.jsx` — UI block, immediate PATCH, no Save
- `web/src/pages/AdminPipelineConfigPage.jsx` — schedule state + insert after IngestSourcesSection; dirty unchanged
- `web/src/main.jsx` — `__DIGEST_INGESTION_SCHEDULE_HARNESS__`
- `tests/admin.spec.js` — `resetIngestionScheduleMock` + describe automatic collection (7 tests)

## Decisions Made

- Schedule never enters `dirty` (`yamlDirty || sourceFormDirty` only).
- Empty-week copy is the sole status text (not joined with «Включён»).
- `readIngestionScheduleMock` shipped with Task 1 harness so Task 2 blur tests can assert `patchCount`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Empty-week status must be exact copy**
- **Found during:** Task 2 RED
- **Issue:** Status joined «Включён. Выберите хотя бы один день недели.»; test required exact D-15 message alone.
- **Fix:** When `statusMsg === EMPTY_WEEK_MSG`, render that message only.
- **Files modified:** `web/src/components/IngestionScheduleSection.jsx`
- **Commit:** `c3b92bd`

**2. [Rule 2 - Missing critical functionality] Task 1 GREEN included time/days UI early**
- **Found during:** Task 1 GREEN
- **Issue:** Plan Task 2 owns blur/days/error behaviors; shipping the controls in Task 1 avoided a second UI wave and made most Task 2 tests green immediately (only empty-week status needed GREEN).
- **Fix:** Kept full section in Task 1; Task 2 RED/GREEN covered remaining status contract.
- **Files modified:** same component
- **Commit:** `d7ddcdf` / `c3b92bd`

## TDD Gate Compliance

| Task | RED | GREEN | Notes |
|------|-----|-------|-------|
| 1 | `79f1052` | `d7ddcdf` | RED: harness wait timeout (feature absent). Formal `tdd-red-evidence` does not parse Playwright reporter (TAP); documented failure + nonzero exit. |
| 2 | `aa106ef` | `c3b92bd` | RED: empty-week `toHaveText` assertion failure (intentional). |

## Self-Check: PASSED

- FOUND: `web/src/services/ingestScheduleApi.js`
- FOUND: `web/src/components/IngestionScheduleSection.jsx`
- FOUND: commits `79f1052`, `d7ddcdf`, `aa106ef`, `c3b92bd`
- FOUND: 16 Playwright + 9 pytest green on plan verify command
