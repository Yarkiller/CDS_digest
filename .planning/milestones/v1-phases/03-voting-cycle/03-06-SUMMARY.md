---
phase: 03-voting-cycle
plan: 06
subsystem: ui
tags: [react, playwright, voting, leaders, ru-plural, empty-states, tdd]

requires:
  - phase: 03-voting-cycle
    provides: BallotSnapshot leaders[] from 03-03; SPA votingApi + VotingPage from 03-05
provides:
  - leaderStripText from snapshot.leaders[] (muted strip, no row badge)
  - ruCount materialCountLabel + voteCountLabel (incl. 0 материалов)
  - TopicBallot audit dek + counts
  - Closed/empty /voting UX (D-48…50) via mock window harnesses
affects: [03-04-ab-cas-closed, phase-04]

actuals:
  tokens: 6613
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Leaders rendered only from BallotSnapshot.leaders[] — no React tally math"
    - "Sticky window harnesses __DIGEST_VOTING_CLOSED__/NO_TOPICS__/NO_CYCLE__ for Playwright"
    - "Shared ruCount.js for material/vote Russian plurals across Issue/Archive/Voting"

key-files:
  created:
    - web/src/utils/ruCount.js
  modified:
    - web/src/utils/voting.js
    - web/src/components/TopicBallot.jsx
    - web/src/pages/VotingPage.jsx
    - web/src/pages/IssuePage.jsx
    - web/src/pages/ArchivePage.jsx
    - web/src/data/mock.js
    - web/src/services/votingApi.js
    - tests/web-app.spec.js

key-decisions:
  - "Leader strip test uses exact:true for «Лидирует» so strip phrase does not false-fail"
  - "Confirm CTA omitted entirely when cycle.status===closed (not merely disabled)"
  - "Mock closed POST throws CYCLE_CLOSED with ballot payload for D-51 readiness"

patterns-established:
  - "leaderStripText(leaders) pure helper — single vs tie copy (D-40/D-42)"
  - "Empty voting CTAs mirror Archive «К выпуску» → /"

requirements-completed: [VOTE-02, VOTE-03, VOTE-04]

coverage:
  - id: D1
    description: "Leader strip shows «Сейчас лидирует: RAG… · 31 голосов»; no exact row «Лидирует»; «0 материалов» on AutoML"
    requirement: VOTE-02
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows leader strip and 0 материалов without row Лидирует"
        status: pass
    human_judgment: false
  - id: D2
    description: "Topic rows show audit dek + materialCountLabel/voteCountLabel including 0"
    requirement: VOTE-04
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows leader strip and 0 материалов without row Лидирует"
        status: pass
    human_judgment: false
  - id: D3
    description: "Closed cycle: banner «Цикл голосования закрыт»; radios disabled; confirm hidden; leader strip visible"
    requirement: VOTE-03
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows closed banner Цикл голосования закрыт with disabled radios"
        status: pass
    human_judgment: false
  - id: D4
    description: "Open zero topics → «Темы ещё не объявлены» + К выпуску; no cycle → «Сейчас нет активного голосования» (not closed)"
    requirement: VOTE-03
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows Темы ещё не объявлены empty state with К выпуску"
        status: pass
      - kind: automated_ui
        ref: "tests/web-app.spec.js#shows Сейчас нет активного голосования without closed banner"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-09-20
status: complete
---

# Phase 03 Plan 06: Ballot UI Polish Summary

**Muted server-driven leader strip, shared RU plurals with honest «0 материалов», and D-48…50 closed/empty `/voting` states under Playwright mocks.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-20T16:33:05Z
- **Completed:** 2026-09-20T16:41:26Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Leader strip from `snapshot.leaders[]` only (C3-02 muted surface; no row badge)
- Extracted `ruCount.js`; TopicBallot shows audit dek + plurals including «0 материалов»
- Closed / no-topics / no-cycle empty UX with sticky mock window harnesses

## Task Commits

Each task was committed atomically:

1. **Task 1 RED:** `effd079` — test(03-06): add failing test for leader strip and 0 materials
2. **Task 1 GREEN:** `874fb5a` — feat(03-06): implement leader strip, ruCount, and VOTE-04 dek
3. **Task 2 RED:** `3f36694` — test(03-06): add failing tests for closed and empty voting states
4. **Task 2 GREEN:** `a06a453` — feat(03-06): implement closed and empty voting states

**Plan metadata:** `14b221a` (docs: complete ballot UI polish plan)

## Files Created/Modified

- `web/src/utils/ruCount.js` — `materialCountLabel` / `voteCountLabel`
- `web/src/utils/voting.js` — `leaderStripText`
- `web/src/components/TopicBallot.jsx` — dek + ruCount meta; `disabled` for closed
- `web/src/pages/VotingPage.jsx` — strip + D-48…50 branches; hide confirm when closed
- `web/src/pages/IssuePage.jsx` / `ArchivePage.jsx` — import shared `materialCountLabel`
- `web/src/data/mock.js` — AutoML `materialsCount: 0`
- `web/src/services/votingApi.js` — closed/no-topics/no-cycle mock harnesses
- `tests/web-app.spec.js` — Playwright for strip, 0 materials, closed/empty

## Decisions Made

- Exact-match assertion for row «Лидирует» so strip copy «лидирует» is allowed
- Closed cycle omits confirm footer entirely (D-48)
- Mock POST under closed throws `CYCLE_CLOSED` with ballot for future D-51 adopt path

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Exact «Лидирует» assertion after strip landed**
- **Found during:** Task 1 GREEN
- **Issue:** `getByText("Лидирует")` matched substring inside «Сейчас лидирует»
- **Fix:** Use `{ exact: true }` for the forbidden row badge
- **Files modified:** `tests/web-app.spec.js`
- **Verification:** Playwright suite green
- **Committed in:** `874fb5a`

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Necessary for correct acceptance; no scope creep.

## Issues Encountered

None beyond the substring assertion fix above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- VOTE-02/03/04 SPA polish complete under mocks
- Plan 03-04 (A→B CAS / closed reject live path) remains incomplete in phase runnable set
- Visual backstops (long-title wrap, initial GET pending) still held for verify-work per UI-SPEC

## Self-Check: PASSED

- FOUND: `web/src/utils/ruCount.js`
- FOUND: `web/src/pages/VotingPage.jsx` leader strip + closed/empty
- FOUND: commits `effd079`, `874fb5a`, `3f36694`, `a06a453`

---
*Phase: 03-voting-cycle*
*Completed: 2026-09-20*
