---
phase: 22-admin-nav-grouping
plan: 01
subsystem: ui
tags: [react-router-dom, nested-layout, navlink, tailwind, playwright, adux-12]

# Dependency graph
requires:
  - phase: 19-unsaved-changes-guard-for-the-pipeline-editor
    provides: useUnsavedChangesGuard + UnsavedChangesDialog leave contract reused unchanged by tab/select navigation
  - phase: 16-pipe-01-mvp-config-ui
    provides: AdminPipelineConfigPage editor, scope hint, and the AppShell «Пайплайн» pill this plan retires
provides:
  - web/src/components/AdminLayout.jsx — shared admin chrome (eyebrow + underline section switch + narrow select + Outlet)
  - Single admin-gated AppShell «Админ» entry with pathname-prefix active state for any /admin/*
  - Pathless AdminLayout route parent for admin/digest + admin/pipeline only; materials preview stays a sibling
  - Playwright contract for the ADUX-12 nav shape (shell vs section landmark scoping, active tab, select backstop)
affects: [22-admin-nav-grouping/22-02, 23-ingest-sources]

# Actuals (#2632) — chars/4 over the realized diff (6 files, +213/−36)
actuals:
  tokens: 5088
  tasks: 2
  commits: 4
  plan_head_before: cad092e2ce32a2fc84835d9491b6ac7de0811b1e
  plan_head_after: d51cf996e49d4fd0c2c905b01209c03199550919

tech-stack:
  added: []
  patterns:
    - "Pathless layout route for shared chrome without a URL segment (/admin/digest + /admin/pipeline unchanged)"
    - "Custom NavLink active state via useLocation pathname prefix for a fixed-entry shell link"
    - "Landmark-scoped Playwright queries (Основная навигация vs Разделы админки) to keep name-only matchers honest"
    - "Native select + useNavigate() as a narrow-viewport section switch that still fires useBlocker"

key-files:
  created:
    - web/src/components/AdminLayout.jsx
  modified:
    - web/src/components/AppShell.jsx
    - web/src/App.jsx
    - web/src/pages/AdminDigestPage.jsx
    - web/src/pages/AdminPipelineConfigPage.jsx
    - tests/admin.spec.js

key-decisions:
  - "AdminLayout is a pathless parent route so /admin/digest and /admin/pipeline stay byte-identical and no /admin index is introduced (D-01…D-04)"
  - "«Админ» active state is computed from useLocation pathname (/admin or /admin/*) because NavLink prefix matching on /admin/digest never lights /admin/pipeline or materials preview (D-09, RESEARCH Pitfall 1)"
  - "Section switch is nav + NavLink (underline, no pill fill, no ARIA tab roles) — destinations are routes, URL is the source of truth (D-05, D-12)"
  - "Narrow select carries a hard-coded /admin/digest | /admin/pipeline whitelist and navigates via navigate() so the Phase 19 guard still blocks a dirty leave (T-22-02, D-17, D-19)"
  - "Page H1 + duplicate eyebrow removed on every branch (ready/loading/error) of both child pages; hierarchy lives in the active tab at text-3xl font-semibold (D-06, D-08)"

patterns-established:
  - "Shell vs in-page nav: pills in AppShell, underline tabs in AdminLayout — never two shell-level admin items"
  - "Every «Пайплайн» query in Playwright is scoped by landmark or testid so a shell/tab move cannot produce a false green"

requirements-completed: [ADUX-12]

coverage:
  - id: D1
    description: "AppShell exposes exactly one admin-gated «Админ» link to /admin/digest and no «Пайплайн» pill"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config nav item renders only in the in-page section switch"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config nav item hidden for employee"
        status: pass
    human_judgment: false
  - id: D2
    description: "In-page section switch «Дайджест | Пайплайн» on /admin/digest and /admin/pipeline: two ordered destinations, active tab, URL unchanged"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#admin-section nav lists Дайджест then Пайплайн and marks digest active"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#admin-section pipeline tab navigates and keeps the shell Админ entry active"
        status: pass
    human_judgment: false
  - id: D3
    description: "Shell «Админ» stays active on materials preview while the preview route renders no section switch"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#admin-section nav is absent from materials preview while shell Админ stays active"
        status: pass
    human_judgment: false
  - id: D4
    description: "Below sm the section switch collapses to the native select backstop and still changes section"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#narrow viewport swaps the section nav for the select backstop"
        status: pass
    human_judgment: false
  - id: D5
    description: "Page-level H1 «Shortlist дайджеста» / «Конфиг пайплайна» and duplicate eyebrow removed; active tab carries the hierarchy"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#populated shortlist shows ≤5 rows with badges and score factors"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config happy path"
        status: pass
    human_judgment: false
  - id: D6
    description: "Tab labels stay on one row without horizontal page scroll at 1280px and ~640px; select usable without overflow below sm"
    requirement: ADUX-12
    verification: []
    human_judgment: true
    rationale: "UI-SPEC overflow rows are `backstop` probes — automated asserts cannot judge layout elegance, only breakpoint swaps (D4 covers the swap)."

metrics:
  duration: 22min
  completed: 2026-10-17
status: complete
---

# Phase 22 Plan 01: Tracer — single «Админ» shell entry + AdminLayout section switch Summary

**One admin-gated AppShell «Админ» entry plus a shared in-page «Дайджест | Пайплайн» underline switch, with both admin URLs unchanged and page H1s retired**

## Performance

- **Duration:** 22 min
- **Started:** 2026-10-17T10:10:00Z (13:10 local)
- **Completed:** 2026-10-17T10:30:00Z (13:30 local)
- **Tasks:** 2
- **Files modified:** 6 (1 created, 5 modified)

## RED → GREEN evidence (TDD, mandatory)

Both tasks followed Red–Green–Refactor. No production file was touched before the RED run.

**Task 1 RED** — command: `npm run test:web -- tests/admin.spec.js -g "pipeline config nav|Админ nav|admin-section|Дайджест|Пайплайн"`

```text
  1) [web] › tests\admin.spec.js:117:3 › Admin nav grouping — in-page section switch … › admin-section nav lists Дайджест then Пайплайн and marks digest active
    Error: expect(locator).toBeVisible() failed
    Error: element(s) not found
    > 122 |     await expect(sectionNav).toBeVisible();
  2) … admin-section pipeline tab navigates and keeps the shell Админ entry active
    Error: locator.click: Test timeout of 30000ms exceeded.
  3) … admin-section nav is absent from materials preview while shell Админ stays active
    Error: expect(locator).toHaveClass(expected) failed   (> 176 | shellAdminLink … /bg-accent/)
  4) … narrow viewport swaps the section nav for the select backstop
    Error: expect(locator).toHaveCount(expected) failed  (> 183 | admin-section-nav toHaveCount(1))
  5) … pipeline config nav item renders only in the in-page section switch
    Error: expect(locator).toHaveCount(expected) failed  (> 1471 | shell Пайплайн toHaveCount(0))
 5 failed
 59 passed (3.6m)
```

Failing assertions are all about the new nav contract (missing section nav, inactive shell pill, still-present shell «Пайплайн»); no `ERR_CONNECTION_REFUSED`, `0 passed`, or unrelated failure.

**Task 2 RED** — command: `npm run test:web -- tests/admin.spec.js -g "populated shortlist|pipeline config happy path"`

```text
  1) … populated shortlist shows ≤5 rows with badges and score factors
    Error: expect(locator).toHaveCount(expected) failed
    > 206 |     ).toHaveCount(0);            // «Shortlist дайджеста» still rendered
  2) … pipeline config happy path
    Error: expect(locator).toHaveCount(expected) failed
    > 1097 |     ).toHaveCount(0);           // «Конфиг пайплайна» still rendered
 2 failed
 62 passed (3.1m)
```

**GREEN** — after implementation, `npm run test:web -- tests/admin.spec.js` → **64 passed (2.9m)**, twice (targeted grep run + full file run).

**TDD gate commits:** `test(22-01)` → `feat(22-01)` → `test(22-01)` → `feat(22-01)` (both gates satisfied, no violations).

## Accomplishments

- `AdminLayout.jsx` created: eyebrow «Админ», sm+ `nav aria-label="Разделы админки"` with underline `NavLink`s (`admin-section-nav`, `admin-tab-digest`, `admin-tab-pipeline`), below-sm native select (`admin-section-select`, hard-coded two-option whitelist, `navigate()` on change), nested `<Outlet />`.
- `AppShell.jsx`: the admin-gated «Пайплайн» pill is gone; one «Админ» link always `to="/admin/digest"` and lights active for any `/admin/*` via `useLocation` pathname prefix.
- `App.jsx`: pathless `AdminLayout` parent wraps `admin/digest` + `admin/pipeline` only; `admin/materials/:id` stays a sibling; no `/admin` index or redirect added.
- `AdminDigestPage` / `AdminPipelineConfigPage`: page H1s and duplicate eyebrows removed on every branch; pipeline hint «Просмотр и правка без запуска пайплайна», editor, and Phase 19 guard wiring untouched.
- `tests/admin.spec.js`: shell tripwires re-scoped by landmark, four new section-switch cases, heading asserts converted to active-tab assertions, stale «global Пайплайн» comments corrected.

## Task Commits

Each task was committed atomically (TDD: test → feat):

1. **Task 1 (RED): amend admin nav contract** - `4b62669` (test)
2. **Task 1 (GREEN): single «Админ» shell + AdminLayout section switch** - `fed7b0b` (feat)
3. **Task 2 (RED): require layout hierarchy instead of page H1/eyebrow** - `b24b010` (test)
4. **Task 2 (GREEN): drop page H1 + duplicate eyebrow under AdminLayout** - `d51cf99` (feat)

**Plan metadata:** docs commit (this SUMMARY + STATE.md + ROADMAP.md)

## Files Created/Modified

- `web/src/components/AdminLayout.jsx` (new) — eyebrow, underline section switch, narrow select backstop, `<Outlet />`
- `web/src/components/AppShell.jsx` — single admin-gated «Админ» link, pathname-prefix active state, «Пайплайн» pill removed
- `web/src/App.jsx` — pathless `AdminLayout` parent for digest + pipeline; materials preview sibling; no new route
- `web/src/pages/AdminDigestPage.jsx` — removed H1 «Shortlist дайджеста» + duplicate eyebrow (4 branches)
- `web/src/pages/AdminPipelineConfigPage.jsx` — removed H1 «Конфиг пайплайна» + duplicate eyebrow (4 branches); hint and guard unchanged
- `tests/admin.spec.js` — landmark-scoped shell asserts, new section-switch/select/materials cases, active-tab heading replacements, comment refresh

## Decisions Made

- Pathless layout parent (not `path: 'admin'`) keeps both URLs byte-identical and avoids an accidental `/admin` index (D-01…D-04, RESEARCH Pitfall 5).
- Shell active state is a pathname-prefix check rather than `NavLink end`/prefix semantics, because default matching on `/admin/digest` never activates on `/admin/pipeline` (D-09).
- Section switch stays `nav` + `NavLink`: no `role="tablist"`, no pill fills, no horizontal scroll — underline only (D-05, D-12, D-16…D-19).
- Select `onChange` calls `navigate(value)` with a two-value whitelist so the dirty-leave guard still fires and no free-form path can be navigated (T-22-02, D-19).
- `admin-section-select` derives its value from `pathname` rather than local state, so back/forward navigation keeps the control honest.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Playwright's `-g` filter did not narrow the run: every invocation executed all 64 `admin.spec.js` tests. This did not weaken the evidence — each RED run failed only on the target assertions (5 then 2) with all other tests green, and the GREEN run was a full-file pass.
- No stale `:5174` listener was present (checked with `Get-NetTCPConnection` before the first run); the STATE.md Vite flakiness blocker did not recur.

## Known Stubs

None — both pages are wired to their existing data sources; no placeholder copy or empty-value plumbing was introduced.

## Threat Flags

None — no new endpoints, auth paths, or trust boundaries. The select whitelist (T-22-02) and the preserved `appRole === 'admin'` shell gate (T-22-03) are the only threat-relevant surfaces and both are implemented as planned.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 22-02 can proceed: the layout, shell entry, and section switch exist, so the dirty→tab journey (D-14) and the `16-UI-SPEC` A-2 supersession are the only remaining phase work.
- `/admin/materials/:id` deliberately has no section switch this phase (D-11); the «← К шортлисту» back-link remains deferred.
- Phase 23 (ingest sources) can grow under the «Пайплайн» tab without redesigning the switch.

---
*Phase: 22-admin-nav-grouping*
*Completed: 2026-10-17*

## Self-Check: PASSED

- Created/modified files: 7/7 found
- Commits: 4b62669, fed7b0b, b24b010, d51cf99 all present on `experiment/gsd-framework`

