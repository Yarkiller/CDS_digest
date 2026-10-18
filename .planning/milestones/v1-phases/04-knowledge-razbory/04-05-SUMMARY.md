---
phase: 04-knowledge-razbory
plan: 05
subsystem: ui
tags: [razbor, chronology, react, spa, mocks, tdd, RAZB-01]

requires:
  - phase: 04-knowledge-razbory
    provides: GET /razbory chronology DTO from 04-04; knowledge role chips mocks from 04-03
provides:
  - razboryApi.fetchRazbory with isMocksEnabled + JWT live path
  - RazboryListPage chronology list + empty CTA to /voting
  - ChronologyItem with «Анонс» + byline «Редакция Digest CDS»
  - AppShell nav «Разборы» + /razbory and /razbory/:id shell route
affects:
  - 04-06 razbor detail / notebook SPA
  - 04-09 Playwright list/empty/nav proofs

actuals:
  tokens: 6876
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Chronology-item rows (not MaterialListRow) for /razbory list (D-67)"
    - "Empty razbory honesty: single CTA «К голосованию» → /voting (D-69)"
    - "armEmptyRazbory / armFailNextRazboryFetch harness mirrors archive contentApi"

key-files:
  created:
    - web/src/services/razboryApi.js
    - web/src/pages/RazboryListPage.jsx
    - web/src/components/ChronologyItem.jsx
    - tests/unit/test_razbory_api.js
  modified:
    - web/src/App.jsx
    - web/src/components/AppShell.jsx
    - web/src/data/mock.js

key-decisions:
  - "Byline constant RAZBOR_EDITOR_BYLINE in razboryApi; ChronologyItem consumes it (Q3 RESOLVED)"
  - "Announcement overline label «Анонс»; published omits status suffix"
  - "/razbory/:id shell placeholder for 04-06 detail fill"
  - "App.jsx/AppShell commits isolated from unrelated profile WIP"

patterns-established:
  - "Pattern: ArchivePage load/error/empty → RazboryListPage with ServiceUnavailable + D-69 CTA"
  - "Pattern: SPA services under web/src/services/ with isMocksEnabled cutover + JWT Bearer"

requirements-completed: [RAZB-01]

coverage:
  - id: D1
    description: AppShell «Разборы» nav links to /razbory and App registers list + :id shell routes (D-66)
    requirement: RAZB-01
    verification:
      - kind: other
        ref: node -e AppShell/App.jsx path+label asserts (plan verify)
        status: pass
      - kind: unit
        ref: tests/unit/test_razbory_api.js#mockListRazbory
        status: pass
    human_judgment: false
  - id: D2
    description: Chronology rows show date/status (Анонс), title, editorial byline, «Читать разбор →» (D-67/D-68)
    requirement: RAZB-01
    verification:
      - kind: unit
        ref: tests/unit/test_razbory_api.js#maps announcement status label to Анонс
        status: pass
      - kind: unit
        ref: tests/unit/test_razbory_api.js#exposes editorial byline constant
        status: pass
    human_judgment: false
  - id: D3
    description: Empty list shows «Разборов пока нет» + «К голосованию» → /voting only (D-69)
    requirement: RAZB-01
    verification:
      - kind: unit
        ref: tests/unit/test_razbory_api.js#page source has empty copy + /voting CTA and no К выпуску
        status: pass
      - kind: other
        ref: node -e RazboryListPage empty-copy assert (plan verify)
        status: pass
    human_judgment: false
  - id: D4
    description: Chronology list reflows at many items without clipped CTAs
    requirement: RAZB-01
    verification: []
    human_judgment: true
    rationale: UI-SPEC overflow backstop — visual check deferred to verify-work / 04-09 Playwright

duration: 5min
completed: 2026-09-21
status: complete
---

# Phase 04 Plan 05: Razbor List SPA Summary

**Razbory chronology SPA at `/razbory` with AppShell «Разборы», ChronologyItem rows (Анонс + editorial byline), and empty CTA to `/voting` only (RAZB-01 / D-66…D-69).**

## Performance

- **Duration:** 5min
- **Started:** 2026-09-21T05:06:26Z
- **Completed:** 2026-09-21T05:11:20Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- `razboryApi` mock/live `fetchRazbory` with JWT headers and empty/fail harness flags
- `RazboryListPage` + `ChronologyItem` chronology UI (not MaterialListRow covers)
- AppShell nav «Разборы» after «Голосование»; `/razbory/:id` shell for 04-06
- Empty honesty: «Разборов пока нет» + single «К голосованию» → `/voting`

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): End-to-end SPA razbor list tests** - `afc84bc` (test)
2. **Task 1 (GREEN): Implement razbor list SPA** - `2707085` (feat)
3. **Task 2 (RED): Empty razbory CTA tests** - `2c89381` (test)
4. **Task 2 (GREEN): Empty CTA to voting only** - `fb7ff3e` (feat)

**Plan metadata:** (pending docs commit)

_Note: TDD tasks used test → feat commit pairs_

## Files Created/Modified

- `web/src/services/razboryApi.js` — fetchRazbory, mockListRazbory, status label, harness
- `web/src/pages/RazboryListPage.jsx` — list / empty / ServiceUnavailable
- `web/src/components/ChronologyItem.jsx` — chronology-item row + byline
- `web/src/data/mock.js` — razbory seed + getRazboryList
- `web/src/App.jsx` — `/razbory` + `/razbory/:id` shell (profile WIP left uncommitted)
- `web/src/components/AppShell.jsx` — «Разборы» nav (profile identity WIP left uncommitted)
- `tests/unit/test_razbory_api.js` — mock DTO + empty-copy contracts

## Decisions Made

- Editorial byline lives as `RAZBOR_EDITOR_BYLINE` shared by ChronologyItem
- Published rows omit status overline suffix; announcement shows «Анонс»
- Detail route is a placeholder shell until 04-06
- Staged App/AppShell from HEAD+razbory-only hunks so profile WIP stayed out of commits

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written (dirty-tree isolation handled without Rule 4).

**Total deviations:** 0
**Impact on plan:** N/A

## Issues Encountered

Dirty working tree mixed profile WIP into `App.jsx` / `AppShell.jsx`. Committed razbory-only versions from HEAD, then restored WIP on top — no profile/auth files in 04-05 commits.

## TDD Gate Compliance

- RED `test(04-05)` commits: `afc84bc`, `2c89381`
- GREEN `feat(04-05)` commits: `2707085`, `fb7ff3e`

## Known Stubs

| File | Stub | Reason |
|------|------|--------|
| `App.jsx` `/razbory/:id` | Placeholder `<p data-testid="razbor-detail-shell">` | Detail/notebook owned by 04-06 |
| Playwright list/empty/nav | Deferred | Plan assumes 04-09 |

## Threat Flags

None beyond plan threat model — Bearer JWT via existing `getAccessToken` pattern (T-04-07).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 04-06 can replace the `:id` shell with RazborPage (announcement stub / longread)
- 04-09 can Playwright-nav `/razbory`, assert chronology + empty CTA to `/voting`
- Live `GET /razbory` already exists from 04-04 when `VITE_USE_MOCKS=false`

## Self-Check: PASSED

- FOUND: `web/src/services/razboryApi.js`
- FOUND: `web/src/pages/RazboryListPage.jsx`
- FOUND: `web/src/components/ChronologyItem.jsx`
- FOUND: `tests/unit/test_razbory_api.js`
- FOUND: commits `afc84bc`, `2707085`, `2c89381`, `fb7ff3e`

---
*Phase: 04-knowledge-razbory*
*Completed: 2026-09-21*
