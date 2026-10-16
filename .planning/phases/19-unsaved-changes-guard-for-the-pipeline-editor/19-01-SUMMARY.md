---
phase: 19-unsaved-changes-guard-for-the-pipeline-editor
plan: 01
subsystem: ui
tags: [react-router, createBrowserRouter, RouterProvider, data-router, playwright]

requires:
  - phase: 18-reader-route-honesty-for-draft-materials
    provides: admin/materials/:id preview route and RequireAuth layout composition
provides:
  - module-scope createBrowserRouter instance in web/src/App.jsx
  - data-router context required by useBlocker (Plan 19-02)
affects:
  - 19-02 unsaved-changes guard wiring
  - any future useBlocker consumers

actuals:
  tokens: 782
  tasks: 2
  commits: 1

plan_head_before: 09b428898b90cb74bbb015d3e2241bc6665f2597
plan_head_after: 6240fe91cedb588c6b1c9076368c969908dbcdaf

tech-stack:
  added: []
  patterns:
    - module-scope createBrowserRouter + RouterProvider (never inside App)
    - pathless layout route with RequireAuth wrapping AppShell

key-files:
  created: []
  modified:
    - web/src/App.jsx

key-decisions:
  - "D-09: router migration alone, proven at Wave-0 baseline 110 before any useBlocker wiring"
  - "No errorElement — behaviour-preserving refactor only (RESEARCH OQ3)"
  - "ADUX-09 remains Pending until Plan 19-02 lands the guard"

patterns-established:
  - "SPA router is a single module-scope createBrowserRouter; App() only returns RouterProvider"
  - "Wave-0 Playwright count is MEASURED on the untouched tree before router edits"

requirements-completed: []  # ADUX-09 criterion 4 only; full ADUX-09 closes with 19-02

coverage:
  - id: D1
    description: "App.jsx renders through one module-scope createBrowserRouter + RouterProvider; all prior routes preserved; no errorElement"
    requirement: ADUX-09
    verification:
      - kind: automated_ui
        ref: "npm run test:web → 110 passed (equals Wave-0 baseline)"
        status: pass
      - kind: other
        ref: "web/src/App.jsx source contract — module-scope router, RequireAuth+AppShell layout, route set equality, * replace, no errorElement"
        status: pass
    human_judgment: false
  - id: D2
    description: "Named at-risk surfaces green: auth returnUrl gate, catch-all / soft-not-found paths, admin/materials/:id preview"
    requirement: ADUX-09
    verification:
      - kind: automated_ui
        ref: "npm run test:web -- tests/auth.spec.js tests/web-app.spec.js tests/admin.spec.js → 103 passed"
        status: pass
    human_judgment: false

duration: 16min
completed: 2026-10-16
status: complete
---

# Phase 19 Plan 01: Data-router migration Summary

**Migrated `web/src/App.jsx` to a single module-scope `createBrowserRouter` + `<RouterProvider>`, preserving every route and the RequireAuth layout; full Playwright `web` suite stayed at the measured Wave-0 baseline of 110.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-16T06:24:28Z
- **Completed:** 2026-10-16T06:40:00Z
- **Tasks:** 2/2
- **Files modified:** 1 (`web/src/App.jsx`)

## Accomplishments

- Replaced declarative `<BrowserRouter>/<Routes>/<Route>` with module-scope `createBrowserRouter([...])` and `<RouterProvider router={router} />`
- Preserved pathless `RequireAuth`+`AppShell` layout, relative child paths (incl. `index`, `admin/materials/:id` preview, `admin/pipeline`), and `*` → `/` with `replace`
- Wave-0 baseline **110 passed** on untouched tree; post-migration full suite **110 passed**; focused at-risk run **103 passed**
- No `errorElement`; `web/src/main.jsx` untouched; imports stay on `react-router-dom` only

## Task Commits

Each task was committed atomically:

1. **Task 1 (tracer): Migrate App.jsx to module-scope data router** - `6240fe9` (refactor)
2. **Task 2: Pin at-risk surfaces + source contract** - no code commit (verification-only; App.jsx already correct)

**Plan metadata:** (docs commit follows this SUMMARY)

## Wave-0 baseline (measured)

- Port `127.0.0.1:5174`: no listener before run
- Command: `npm run test:web`
- Result: **110 passed** (3.2m)
- Spec set (`playwright.config.js` `web` project `testMatch`): `web-app`, `auth`, `knowledge`, `razbory`, `admin`

## Post-migration verify

- Full suite: **110 passed** (3.5m) — equals baseline; no `ERR_CONNECTION_REFUSED`
- Focused: `npm run test:web -- tests/auth.spec.js tests/web-app.spec.js tests/admin.spec.js` → **103 passed** (3.2m) after one flake retry
- Named surfaces observed green:
  - auth: `redirects protected route to login with returnUrl when auth gate is on`
  - web-app: unknown material / unknown issue soft-empty paths (catch-all does not swallow real routes)
  - admin: draft preview journeys under `admin/materials/:id` (ADUX-07/08)

## Route-set equality check

Pre-migration child paths (order preserved): `index`, `archive`, `issues/:number`, `voting`, `knowledge`, `materials/:id`, `razbory`, `razbory/:id`, `profile`, `admin/digest`, `admin/materials/:id`, `admin/pipeline`, `*` (with `replace`). Top-level: `/login`, `/register`, pathless layout. Post-migration set identical; no additions/removals/reorders; no `errorElement`.

## Decisions Made

- Followed D-09: migration alone, gated by full suite before Plan 19-02 wires `useBlocker`
- Did not add `errorElement` (RESEARCH Open Question 3)
- Left ADUX-09 unchecked in REQUIREMENTS.md — criterion 4 only; full requirement closes with 19-02

## Deviations from Plan

None - plan executed as written. Task 2 produced no production edit.

### Issues Encountered

**1. Focused-run flake (not a router regression)**
- **Found during:** Task 2 first focused run
- **Issue:** `admin.spec.js` G-05-2 timed out because email-preview dialog still intercepted clicks after «Закрыть» — 1 failed / 102 passed
- **Resolution:** Cleared port 5174 and re-ran the same three files → **103 passed**. Same journey was green in both full-suite runs (pre/post migration). No App.jsx change.
- **Impact:** None on migration acceptance

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Data-router context is in place for `useBlocker` in Plan **19-02**
- Do not combine guard wiring with further router shape changes (PITFALLS: Never)
- Before next full `web` run: confirm nothing listens on `127.0.0.1:5174`

## Self-Check: PASSED

- FOUND: `web/src/App.jsx` (module-scope `createBrowserRouter`, `RouterProvider`, no `errorElement`/`Routes`/`BrowserRouter`)
- FOUND: commit `6240fe9`
- FOUND: `web/src/main.jsx` byte-identical to pre-task (no diff vs plan head)

---
*Phase: 19-unsaved-changes-guard-for-the-pipeline-editor*
*Completed: 2026-10-16*
