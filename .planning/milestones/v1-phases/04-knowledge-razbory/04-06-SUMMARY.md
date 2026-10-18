---
phase: 04-knowledge-razbory
plan: 06
subsystem: ui
tags: [razbor, detail, toc, content_kind, fastapi, react, tdd, RAZB-02, RAZB-04]

requires:
  - phase: 04-knowledge-razbory
    provides: GET /razbory list + /razbory/:id shell from 04-04/04-05
provides:
  - GET /razbory/{id} detail DTO with announcement body emptied
  - RazborDetail view + detect_content_kind (quality | overview)
  - RazborPage longread sticky TOC, announcement stub, soft 404
  - Mock seeds for multi-section published + quality metrics body
affects:
  - 04-07 notebook download strip
  - 04-09 Playwright TOC/Обзор/Анонс/404

actuals:
  tokens: 9106
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Announcement detail empties body_markdown in use-case (D-68 / T-04-10)"
    - "content_kind via ## Качество|Оценка качества + numeric markdown table (Pattern 7)"
    - "RazborPage MaterialPage TOC/soft-404 analog; notebook deferred to 04-07"

key-files:
  created:
    - web/src/pages/RazborPage.jsx
  modified:
    - backend/src/backend/application/use_cases/get_razbor.py
    - backend/src/backend/interface/http/routes/razbory.py
    - web/src/services/razboryApi.js
    - web/src/data/mock.js
    - web/src/App.jsx
    - tests/unit/test_razbor_use_cases.py
    - tests/unit/test_http_razbory.py

key-decisions:
  - "RazborDetail application view carries content_kind; domain Razbor entity unchanged"
  - "Announcement content_kind forced to overview; prose always empty at use-case boundary"
  - "Notebook strip / FileResponse deferred to 04-07; notebook_available flag present on DTO"
  - "App.jsx commit isolated from profile WIP (ProfilePage route left uncommitted)"

patterns-established:
  - "Pattern: get_razbor returns reader view with honesty transforms (empty announcement body, content_kind)"
  - "Pattern: RazborPage announcement stub vs published longread branch (no fake prose column)"

requirements-completed: [RAZB-02, RAZB-04]

coverage:
  - id: D1
    description: Published multi-section razbor detail with sticky TOC structure and body_markdown (RAZB-02)
    requirement: RAZB-02
    verification:
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_detail_returns_published_longread_fields
        status: pass
      - kind: unit
        ref: tests/unit/test_razbor_use_cases.py#test_get_razbor_returns_published_with_body
        status: pass
    human_judgment: false
  - id: D2
    description: Announcement detail is stub only — empty body, pending note UI (D-68)
    requirement: RAZB-02
    verification:
      - kind: unit
        ref: tests/unit/test_razbor_use_cases.py#test_get_razbor_announcement_returns_empty_body
        status: pass
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_detail_announcement_returns_empty_body
        status: pass
    human_judgment: false
  - id: D3
    description: Unknown id → 404 razbor_not_found for SPA soft 404
    requirement: RAZB-02
    verification:
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_detail_not_found_returns_404
        status: pass
    human_judgment: false
  - id: D4
    description: content_kind quality vs overview discrimination (RAZB-04 / D-73)
    requirement: RAZB-04
    verification:
      - kind: unit
        ref: tests/unit/test_razbor_use_cases.py#test_get_razbor_content_kind_quality_when_heading_and_numeric_table
        status: pass
      - kind: unit
        ref: tests/unit/test_razbor_use_cases.py#test_get_razbor_content_kind_overview_without_metrics
        status: pass
    human_judgment: false
  - id: D5
    description: Long razbor sticky TOC / title wrap / announcement title wrap backstops
    requirement: RAZB-02
    verification: []
    human_judgment: true
    rationale: UI-SPEC visual backstops — Playwright/visual deferred to 04-09 / verify-work

duration: 5min
completed: 2026-09-21
status: complete
---

# Phase 04 Plan 06: Razbor Detail TOC + Metrics Honesty Summary

**GET /razbory/{id} + RazborPage ship sticky TOC longread, announcement stub honesty (D-68), and content_kind quality vs Обзор (D-73) without notebook download.**

## Performance

- **Duration:** 5min
- **Started:** 2026-09-21T05:13:26Z
- **Completed:** 2026-09-21T05:18:12Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Authenticated detail endpoint returns published longread fields; announcement empties prose at the use-case boundary (T-04-10).
- RazborPage reuses MaterialPage sticky TOC (`lg:`) + mobile «Содержание», soft 404 «Разбор не найден» → `/razbory`.
- `detect_content_kind` labels quality vs overview; UI badge «Обзор» / «Качество» label without empty metrics stubs.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Published longread + announcement stub + soft 404** - `7513038` (test)
2. **Task 1 (GREEN): implement detail + RazborPage** - `d1cbda0` (feat)
3. **Task 2 (RED): content_kind quality vs overview** - `631fdb0` (test)
4. **Task 2 (GREEN): detect_content_kind + UI labeling** - `d15400d` (feat)

**Plan metadata:** (docs commit after state update)

## Files Created/Modified

- `backend/src/backend/application/use_cases/get_razbor.py` - RazborDetail view, detect_content_kind, announcement empty body
- `backend/src/backend/interface/http/routes/razbory.py` - GET /razbory/{id} detail DTO + 404
- `web/src/pages/RazborPage.jsx` - longread / stub / soft 404 / content_kind badges
- `web/src/services/razboryApi.js` - fetchRazbor + mockRazborDetail
- `web/src/data/mock.js` - multi-section bodies + quality seed
- `web/src/App.jsx` - `/razbory/:id` → RazborPage (profile WIP not committed)
- `tests/unit/test_razbor_use_cases.py` / `test_http_razbory.py` - detail + content_kind coverage

## Decisions Made

- Application-layer `RazborDetail` carries `content_kind` so domain `Razbor` stays persistence-shaped.
- Notebook download UI deferred to 04-07; DTO still exposes `notebook_available`.
- Tracer pytest verify re-run green before expansion (interactive auto_advance off; automated gate satisfied).

## Deviations from Plan

None - plan executed as written. Dirty-tree isolation for App.jsx profile WIP handled without Rule 4.

## Threat Flags

None beyond plan register (T-04-10 mitigated by empty announcement body; T-04-11 int path + 404).

## Known Stubs

None that block plan goals. Notebook strip intentionally absent until 04-07.

## Self-Check: PASSED

- FOUND: `web/src/pages/RazborPage.jsx`
- FOUND: `backend/src/backend/application/use_cases/get_razbor.py`
- FOUND commits: `7513038`, `d1cbda0`, `631fdb0`, `d15400d`
