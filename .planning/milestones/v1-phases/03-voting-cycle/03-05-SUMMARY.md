---
phase: 03-voting-cycle
plan: 05
subsystem: ui
tags: [react, playwright, voting, mocks, ballot-snapshot, tdd]

requires:
  - phase: 03-voting-cycle
    provides: GET/POST /voting BallotSnapshot contract from 03-01; leaders[] shapes from 03-03
provides:
  - votingApi.fetchBallot + submitVote via isMocksEnabled (D-56)
  - VotingPage loads ballot + confirm with D-47 disabled guard
  - Honest never-voted «голос не отдан»; «Изменить голос» (D-44); no row «Лидирует» (D-40)
affects: [03-04-ab-cas-closed, 03-06-leader-strip-empty-ui]

actuals:
  tokens: 6823
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "votingApi mirrors contentApi: isMocksEnabled gate; live Bearer to /voting/*"
    - "POST returns BallotSnapshot applied in one round-trip (D-52)"
    - "voteButtonLabel(state, { confirmedId }) — never «Голос принят»"

key-files:
  created: []
  modified:
    - web/src/services/votingApi.js
    - web/src/pages/VotingPage.jsx
    - web/src/components/TopicBallot.jsx
    - web/src/utils/voting.js
    - web/src/data/mock.js
    - tests/web-app.spec.js

key-decisions:
  - "Empty «Выберите тему» shown when ready && !selectedId (disabled CTA cannot receive click)"
  - "Mock tallies mutate in-module on submit; leaders derived without topic.leading"
  - "GET splash deferred — initial load uses neutral status until snapshot (must_haves)"

patterns-established:
  - "SPA voting DTO: topics camelCase materialsCount; personal_vote.topic_id from snapshot"
  - "confirmDisabled = !selectedId || selectedId === confirmedId || loading (D-47)"

requirements-completed: [VOTE-01, VOTE-02]

coverage:
  - id: D1
    description: "Never-voted ballot: zero checked radios, status «голос не отдан», no «Лидирует» row badge"
    requirement: VOTE-02
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#lets a reader pick a voting topic and confirm"
        status: pass
    human_judgment: false
  - id: D2
    description: "Confirm stores one vote; status «Ваш голос: RAG…»; CTA «Изменить голос»; D-47 disabled while selection===confirmed"
    requirement: VOTE-01
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#lets a reader pick a voting topic and confirm"
        status: pass
      - kind: automated_ui
        ref: "tests/web-app.spec.js#confirms a vote with loading then Изменить голос state"
        status: pass
    human_judgment: false
  - id: D3
    description: "Empty submit blocked with «Выберите тему»; no POST /voting fired"
    requirement: VOTE-01
    verification:
      - kind: automated_ui
        ref: "tests/web-app.spec.js#blocks empty submit with Выберите тему and does not POST"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-09-20
status: complete
---

# Phase 03 Plan 05: SPA Ballot Wire Summary

**SPA votingApi + VotingPage under mocks: honest never-voted UX, confirm-one-vote with D-52 snapshot apply, D-47 pointless-POST guard, no row «Лидирует» (D-40, D-44…47, D-52, D-56).**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-20T16:01:48Z
- **Completed:** 2026-09-20T16:08:30Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Wired `fetchBallot` / `submitVote` through `isMocksEnabled` with live Bearer paths to `/voting/current` and `/voting/votes`
- Never-voted status is exactly `голос не отдан`; CTA becomes «Изменить голос»; row «Лидирует» removed
- D-47: confirm disabled while selection equals confirmed topic; empty selection shows «Выберите тему» with no POST

## Task Commits

Each task was committed atomically:

1. **Task 1: SPA ballot wire — votingApi + VotingPage confirm under mocks** - `3ad6ed8` (test) + `c1265af` (feat)
2. **Task 2: Wave SPA gate — voting honesty suite** - verify-only (9 passed; no code change)

**Plan metadata:** `caa106a` (docs: complete plan)

## Files Created/Modified

- `web/src/services/votingApi.js` — fetchBallot + submitVote; mock snapshot + leaders; VoteSubmitError harness
- `web/src/pages/VotingPage.jsx` — load ballot on mount; D-47 disabled; apply POST snapshot
- `web/src/components/TopicBallot.jsx` — removed `topic.leading` / «Лидирует»
- `web/src/utils/voting.js` — honest never-voted + «Изменить голос» labels
- `web/src/data/mock.js` — drop `leading`; add audit descriptions
- `tests/web-app.spec.js` — VOTE-01/02 honesty Playwright suite

## Decisions Made

- Show «Выберите тему» when ballot ready and nothing selected — disabled buttons cannot surface a click-driven validation path
- Leader strip UI remains 03-06; this plan only removes row badges and ships honesty/confirm under mocks
- Initial GET pending uses short «Загрузка…» status (no skeleton; no ServiceUnavailable for mock path)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Empty-submit force-click cannot fire React onClick on disabled button**
- **Found during:** Task 1 (GREEN)
- **Issue:** Playwright `el.disabled=false; el.click()` / force-click did not reliably show validation from `confirmVote`
- **Fix:** Render «Выберите тему» when `loadState === 'ready' && !selectedId`; test asserts visible copy + disabled CTA + zero POSTs
- **Files modified:** `web/src/pages/VotingPage.jsx`, `tests/web-app.spec.js`
- **Verification:** Playwright empty-submit test pass
- **Committed in:** `c1265af`

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Correctness for VOTE-01 empty-submit copy; no scope creep.

## Issues Encountered

None beyond the empty-submit interaction noted above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 03-06 leader strip / empty-cycle copy and 03-04 A→B / closed reject UI
- Live Supabase vote adapter remains 03-02; SPA already has live fetch paths when `VITE_USE_MOCKS=false`

## TDD Gate Compliance

- RED: `3ad6ed8` — failing Playwright honesty assertions
- GREEN: `c1265af` — production wire + green suite

## Self-Check: PASSED

- FOUND: web/src/services/votingApi.js
- FOUND: web/src/pages/VotingPage.jsx
- FOUND: web/src/components/TopicBallot.jsx
- FOUND: web/src/utils/voting.js
- FOUND: tests/web-app.spec.js
- FOUND: 3ad6ed8
- FOUND: c1265af

---
*Phase: 03-voting-cycle*
*Completed: 2026-09-20*
