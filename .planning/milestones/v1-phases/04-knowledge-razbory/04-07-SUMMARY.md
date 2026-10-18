---
phase: 04-knowledge-razbory
plan: 07
subsystem: api
tags: [razbor, notebook, FileResponse, path-containment, react, tdd, RAZB-03]

requires:
  - phase: 04-knowledge-razbory
    provides: RazborPage longread + notebook_available detail DTO from 04-06
provides:
  - Authenticated GET /razbory/{id}/notebook FileResponse under NOTEBOOK_ROOT
  - NotebookStorage port + LocalNotebookStorage path containment (T-04-09)
  - Dual notebook strip on published RazborPage (D-70…72)
affects:
  - 04-09 Playwright notebook enable/disable proofs
  - Ops NOTEBOOK_ROOT env for live downloads

actuals:
  tokens: 18500
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - "NotebookStorage port; LocalNotebookStorage Path.resolve + relative_to containment"
    - "FileResponse attachment media_type application/x-ipynb+json; JWT get_principal"
    - "Dual strip UI: enabled download vs disabled + «Notebook скоро будет»; announcement omits strip"

key-files:
  created:
    - backend/src/backend/application/ports/notebook_storage.py
    - backend/src/backend/application/use_cases/download_razbor_notebook.py
    - backend/src/backend/infrastructure/local_notebook_storage.py
    - tests/unit/test_razbor_notebook_ui_copy.js
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/composition/settings.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/live.py
    - backend/src/backend/interface/http/routes/razbory.py
    - backend/src/backend/interface/http/app.py
    - web/src/pages/RazborPage.jsx
    - web/src/services/razboryApi.js
    - tests/unit/test_http_razbory.py
    - tests/unit/test_http_knowledge_search.py

key-decisions:
  - "Notebook files under NOTEBOOK_ROOT via LocalNotebookStorage — not Supabase Storage (A5)"
  - "Path with .. or absolute → 400 notebook_path_invalid; missing file/path → 404 notebook_not_available"
  - "Announcement stub omits notebook strip entirely (D-68 honesty)"
  - "Playwright enable/disable deferred to 04-09 per plan assumptions"

patterns-established:
  - "Pattern: download_razbor_notebook use-case returns contained Path; route maps domain errors to HTTP"
  - "Pattern: SPA download via fetch blob + object URL; toast «Не удалось скачать» on failure"

requirements-completed: [RAZB-03]

coverage:
  - id: D1
    description: Authenticated notebook FileResponse streams attachment bytes when available (RAZB-03 / D-70)
    requirement: RAZB-03
    verification:
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_notebook_streams_attachment_when_available
        status: pass
    human_judgment: false
  - id: D2
    description: Path traversal outside NOTEBOOK_ROOT rejected without leaking file bytes (T-04-09)
    requirement: RAZB-03
    verification:
      - kind: unit
        ref: tests/unit/test_http_razbory.py#test_razbory_notebook_rejects_path_traversal
        status: pass
    human_judgment: false
  - id: D3
    description: Dual strip UI copy — enabled CTA, missing caption, failure toast (D-70…72)
    requirement: RAZB-03
    verification:
      - kind: unit
        ref: tests/unit/test_razbor_notebook_ui_copy.js
        status: pass
    human_judgment: false
  - id: D4
    description: Playwright notebook enable/disable / download click
    requirement: RAZB-03
    verification: []
    human_judgment: true
    rationale: Plan assumes Playwright proofs land in 04-09

duration: 12min
completed: 2026-09-21
status: complete
---

# Phase 04 Plan 07: Notebook Dual Strip + FileResponse Summary

**Authenticated `GET /razbory/{id}/notebook` streams `.ipynb` under NOTEBOOK_ROOT with path containment, and published RazborPage shows honest dual download strips (D-70…72) without regressing announcement stubs.**

## Performance

- **Duration:** 12min
- **Started:** 2026-09-21T05:19:48Z
- **Completed:** 2026-09-21T05:25:00Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments

- `NotebookStorage` + `LocalNotebookStorage` enforce Path containment; escapes → 400; missing → 404; JWT required.
- FileResponse uses `application/x-ipynb+json` + attachment disposition; repeat download is idempotent.
- Published RazborPage dual strip (top + bottom); disabled + «Notebook скоро будет» when `notebook_available` false; failure toast «Не удалось скачать»; announcement omits strip.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Notebook FileResponse path containment** - `7206aa4` (test)
2. **Task 1 (GREEN): implement FileResponse + storage port** - `ffd611e` (feat)
3. **Task 2 (RED): Dual notebook strip UI honesty** - `bca6a4c` (test)
4. **Task 2 (GREEN): wire dual strip + download helper** - `0a0dbf8` (feat)
5. **Task 2 (fix): normalize RazborPage newlines** - `d03325d` (fix)

**Plan metadata:** (docs commit after state update)

## Files Created/Modified

- `backend/.../ports/notebook_storage.py` — Protocol for path-safe resolve
- `backend/.../infrastructure/local_notebook_storage.py` — NOTEBOOK_ROOT containment adapter
- `backend/.../use_cases/download_razbor_notebook.py` — load razbor + resolve path
- `backend/.../routes/razbory.py` — `GET /{id}/notebook` FileResponse
- `backend/.../composition/{settings,container,live}.py` — `notebook_root` + storage wiring
- `web/src/pages/RazborPage.jsx` — dual strip + toast
- `web/src/services/razboryApi.js` — `downloadRazborNotebook` blob helper
- `tests/unit/test_http_razbory.py` / `test_razbor_notebook_ui_copy.js` — RAZB-03 coverage

## Decisions Made

- Local filesystem under `NOTEBOOK_ROOT` (A5), not Supabase Storage.
- Invalid path → 400; unavailable → 404 (UI already disables when DTO says missing).
- Tracer pytest re-run green before UI expansion (interactive auto_advance off; automated gate satisfied).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] AppContainer gained notebook_storage — knowledge HTTP test fixture broke**
- **Found during:** Task 1 (GREEN)
- **Issue:** `test_http_knowledge_search._seeded_container` constructed `AppContainer` without `notebook_storage`
- **Fix:** Wire `LocalNotebookStorage(".")` in that helper
- **Files modified:** `tests/unit/test_http_knowledge_search.py`
- **Commit:** `ffd611e`

**2. [Rule 1 - Bug] Write tool doubled blank lines in RazborPage.jsx**
- **Found during:** Task 2 (after GREEN)
- **Issue:** Accidental blank line between every source line (~650 lines)
- **Fix:** Rewrite with normal spacing
- **Files modified:** `web/src/pages/RazborPage.jsx`
- **Commit:** `d03325d`

## Threat Flags

None beyond plan register (T-04-09 mitigated by Path containment + JWT; no StaticFiles mount).

## Known Stubs

None that block plan goals. Playwright notebook e2e deferred to 04-09 (documented in plan assumptions).

## Self-Check: PASSED

- FOUND: `backend/src/backend/application/use_cases/download_razbor_notebook.py`
- FOUND: `backend/src/backend/infrastructure/local_notebook_storage.py`
- FOUND: `web/src/pages/RazborPage.jsx`
- FOUND commits: `7206aa4`, `ffd611e`, `bca6a4c`, `0a0dbf8`, `d03325d`
