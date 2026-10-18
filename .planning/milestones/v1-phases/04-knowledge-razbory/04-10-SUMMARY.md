---
phase: 04-knowledge-razbory
plan: 10
subsystem: ui
tags: [razbory, chronology, playwright, tdd, gap-closure]

requires:
  - phase: 04-knowledge-razbory
    provides: ChronologyItem list SPA with announcement|published status DTO
provides:
  - Announcement chronology rows suppress «Читать разбор →» and show готовится placeholder (G-04-2)
  - Playwright coverage locking announcement vs published CTA behavior
affects: [04-knowledge-razbory UAT, verify-work]

actuals:
  tokens: 601
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Thin presentational branch on item.status DTO in ChronologyItem (no new props/fetch)"

key-files:
  created: []
  modified:
    - tests/razbory.spec.js
    - web/src/components/ChronologyItem.jsx

key-decisions:
  - "Branch on item.status === 'announcement' only; published keeps Link to /razbory/{id}"
  - "Placeholder uses data-testid=chronology-pending and text-muted for muted honesty copy"

patterns-established:
  - "Announcement honesty: suppress read affordance when status is announcement; assert RED before GREEN in razbory.spec.js"

requirements-completed: [RAZB-01]

coverage:
  - id: D1
    description: "Announcement chronology rows show готовится placeholder and no Читать разбор CTA"
    requirement: RAZB-01
    verification:
      - kind: automated_ui
        ref: "playwright:tests/razbory.spec.js#lists chronology with date/status and empty CTA to /voting (RAZB-01)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Published chronology rows still render Читать разбор → link"
    requirement: RAZB-01
    verification:
      - kind: automated_ui
        ref: "playwright:tests/razbory.spec.js#lists chronology with date/status and empty CTA to /voting (RAZB-01)"
        status: pass
    human_judgment: false

duration: 2min
completed: 2026-09-21
status: complete
gap_closure: true
gap_ids: [G-04-2]
---

# Phase 04 Plan 10: Announcement CTA honesty Summary

**Announcement chronology rows no longer expose «Читать разбор →»; they show the honest «готовится» placeholder while published rows keep the read link (G-04-2).**

## Performance

- **Duration:** 2 min
- **Started:** 2026-09-21T10:54:18Z
- **Completed:** 2026-09-21T10:56:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Closed UAT gap G-04-2: not-yet-ready (announcement) разборы do not show a misleading read CTA
- Playwright RAZB-01 chronology test now asserts announcement placeholder + published CTA preservation
- Thin presentational conditional in `ChronologyItem` only — status semantics stay on the DTO field

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing Playwright coverage for announcement placeholder vs published CTA** - `f8ada73` (test)
2. **Task 2 (GREEN): Conditional CTA-vs-placeholder in ChronologyItem** - `501c942` (feat)

**Plan metadata:** `c819ac1` (docs: complete plan)

## Files Created/Modified

- `tests/razbory.spec.js` - G-04-2 assertions: no Читать разбор on announcement row; готовится + chronology-pending; published row still has link
- `web/src/components/ChronologyItem.jsx` - branch on `item.status === 'announcement'` for placeholder vs Link

## Decisions Made

- Branch solely on `item.status === 'announcement'` (same field `razborStatusLabel` maps to «Анонс»)
- Use `data-testid="chronology-pending"` and `text-muted` for the placeholder; no new props or fetching

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

- RED gate: `f8ada73` — test failed with announcement link count 1 (expected 0)
- GREEN gate: `501c942` — full `tests/razbory.spec.js` (4 tests) passed

## Known Stubs

None.

## Threat Flags

None — mitigation T-04-G2-01 applied as planned (suppress read affordance for announcement status).

## Self-Check: PASSED

- FOUND: 04-10-SUMMARY.md, tests/razbory.spec.js, ChronologyItem.jsx
- FOUND commits: f8ada73, 501c942

