---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: 10
subsystem: testing
tags: [node:test, playwright, semantic-token-coverage, contrast, loading-state, specificity, tailwind]

# Dependency graph
requires:
  - phase: 25-09
    provides: G-14/G-16 status-contract gates and the test-file layout (stateChromeOffences neighbourhood) this plan extends
provides:
  - e2e case "in-flight vote label keeps its colour and only dims" (idle→loading in dark+light, /voting)
  - static gate G-21 (a loading state paints no colour of its own) + stateChromeOffences + two proof tests
  - mutation proof that both the e2e case and G-21 can fail on a real regression
affects: [verify-work, 25-04 #7 closure, G-21 future consumers, THEME-01 proof gates]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 2187
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "object-scoped gate parsing: STATE_FILL_BLOCK / STATE_ENTRY parse the `stateFill`/`stateChrome` object literals, not a whole-file regex"
    - "specificity-pinned e2e: `disabled:opacity-55` / `disabled:cursor-not-allowed` (0-2-0) beat `opacity-80` / `cursor-wait` (0-1-0) from stateChrome.loading"
    - "transition-neutralisation: `*, *::before, *::after { transition: none !important; }` before click so computed-style reads don't race the 150ms transition-colors"

key-files:
  created: []
  modified:
    - tests/admin-chrome.spec.js
    - tests/unit/test_semantic_token_coverage.js

key-decisions:
  - "G-21 asserts exactly two `loading` entries (one per stateFill/stateChrome block) so the gate cannot silently pass after a key rename."
  - "The e2e case neutralises CSS transitions before the click, otherwise `transition-colors` (150ms) masks an instant colour read mid-transition (mutation #2 first passed for this reason)."
  - "Expected opacity/cursor are pinned to the measured `0.55` / `not-allowed`, with a comment explaining the 0-2-0 vs 0-1-0 specificity, while colour/background equality checks are never weakened."

requirements-completed: [THEME-01]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "confirm-vote in data-state=loading keeps colour rgb(15,23,42) on rgb(234,179,8) in both themes and only dims (opacity 0.55, cursor not-allowed, contrast 9.309)"
    requirement: "THEME-01"
    verification:
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#in-flight vote label keeps its colour and only dims"
        status: pass
    human_judgment: false
  - id: D2
    description: "G-21 forbids a loading state painting its own colour in stateFill/stateChrome and requires opacity- in stateChrome.loading; proof reddens on painted loading states"
    requirement: "THEME-01"
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-21: a loading state paints no colour of its own"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-21 proof: a painted loading state is an offender"
        status: pass
    human_judgment: false

# Metrics
duration: 28min
completed: 2026-10-21
status: complete
---

# Phase 25 Plan 10: In-flight vote label keeps its colour (only dims) — e2e + gate G-21

**Closed `behavior_unverified` 25-04 #7 by rendering the `loading` state: a new Playwright case proves `confirm-vote` keeps `rgb(15,23,42)` on `rgb(234,179,8)` (9.31:1) in both themes and only dims (opacity 0.55, cursor not-allowed); a static gate `G-21` forbids the loading state painting its own colour — test-only, zero production edits.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-10-21T22:35:00+03:00
- **Completed:** 2026-10-21T23:02:00+03:00
- **Tasks:** 2
- **Files modified:** 2 (`tests/admin-chrome.spec.js`, `tests/unit/test_semantic_token_coverage.js`)
- **Plan head:** `e0dbc50` → `dca85b7` (task) → docs commit

## Accomplishments

- **25-04 #7 closed by substance.** The new e2e case measures `idle` *after* radio selection (so the disabled button doesn't pre-apply `opacity: 0.55`), then clicks `confirm-vote` and asserts `data-state="loading"` + text `Сохраняем…` + the full computed-style pair. `flying.color === idle.color`, `flying.background === idle.background`, `flying.fontSize === idle.fontSize`, contrast ≥ 4.5 (measured 9.309), opacity `"0.55"`, cursor `"not-allowed"` — in **both** `dark` and `light`.
- **G-21 added** (`stateChromeOffences` + two proof tests): the `loading` entry in `stateFill` must be empty of any `bg-/text-/border-/ring-/outline-/divide-/fill-/stroke-` utility, and `stateChrome.loading` must contain `opacity-` and no colour utility. Anti-vacuum: exactly two `loading` entries found (one per block).
- **Non-vacuity proven by two mutations** (see below): `stateChrome.loading` + `bg-danger` reddens both e2e and G-21; `stateFill.loading: 'text-text-primary'` reddens both. Each reverted — `ActionButton.jsx` production code untouched (`stateFill.loading: ''` still 1 match, no `stateClass` key).
- **Four previously-closed gates untouched:** G-9 (labels on fills 5.201…11.007), G-15 (toast 16.296/14.516), G-17 (accent links 5.358/7.248), G-18 (field boundary 4.759/3.698 @ 3.0) — all still green in `npm run test:js`.

## idle → loading pair, both themes (pinned by the e2e case)

| State | color | background | opacity | cursor | contrast |
|-------|-------|------------|---------|--------|----------|
| idle (dark) | rgb(15, 23, 42) | rgb(234, 179, 8) | 1 | — | 9.309 |
| loading (dark) | rgb(15, 23, 42) | rgb(234, 179, 8) | 0.55 | not-allowed | 9.309 |
| idle (light) | rgb(15, 23, 42) | rgb(234, 179, 8) | 1 | — | 9.309 |
| loading (light) | rgb(15, 23, 42) | rgb(234, 179, 8) | 0.55 | not-allowed | 9.309 |

The 0.55 / `not-allowed` come from `disabled:opacity-55` / `disabled:cursor-not-allowed` (specificity 0-2-0) beating `opacity-80` / `cursor-wait` (0-1-0) in `stateChrome.loading` — a specificity effect, not stylesheet order.

## Task Commits

1. **Task 1: e2e "in-flight vote label" + G-21 gate with mutation proof** — `dca85b7` (test)

**Plan metadata:** docs commit (SUMMARY + STATE + ROADMAP, below).

## Mutation protocols (each reddened its check, then was reverted)

1. **`stateChrome.loading` → `'cursor-wait opacity-80 bg-danger'`** — e2e reddens on background equality (`flying.background` ≠ `rgb(234, 179, 8)`); G-21 reddens `ActionButton.jsx: stateChrome.loading paints a colour — in-flight only dims (…)`.
2. **`stateFill.loading` → `'text-text-primary'`** — e2e reddens on `flying.color`: `Expected: "rgb(15, 23, 42)"`, `Received: "rgb(241, 245, 249)"` (dark), and on `flying.background` (non-empty `stateFill.loading` enables `hasStateFill`, stripping `bg-voting`); G-21 reddens `stateFill.loading`.

Both mutations were reverted; the tree is back to `stateFill.loading: ''` / `stateChrome.loading: 'cursor-wait opacity-80'`. The transition-neutralisation line (`transition: none !important`) was added before the click to make mutation #2 redden deterministically instead of passing on a mid-transition read.

## Files Created/Modified

- `tests/admin-chrome.spec.js` — new case `in-flight vote label keeps its colour and only dims` (line 809); inline `getComputedStyle` reads for `opacity`/`cursor`; `transition` neutralisation.
- `tests/unit/test_semantic_token_coverage.js` — `STATE_FILL_BLOCK`, `STATE_ENTRY`, `stateChromeOffences`, `it('G-21: a loading state paints no colour of its own')` (line 1712), `it('G-21 proof: a painted loading state is an offender')` (line 1740).

## Decisions Made

- G-21 asserts exactly two `loading` entries (one per `stateFill`/`stateChrome` block) so a key rename cannot make the gate pass silently.
- The e2e case neutralises CSS transitions before the click — `transition-colors` (150ms) otherwise lets a colour read slip in mid-transition (mutation #2 passed unexpectedly on the first attempt for exactly this reason).
- Opacity/cursor expectations are pinned to measured `0.55` / `not-allowed` with an explanatory message; the colour/background equality checks are never weakened (they are the must_have).

## Deviations from Plan

None that changed scope or behaviour — the plan executed as written. The only refinement is the transition-neutralisation line recorded above (a test-harness detail the plan implied but did not spell out); it does not touch production code, the 4.5 threshold, or any allowlist.

## Issues Encountered

None — the only flakiness noted is the known Vite/port-5174 issue, avoided by confirming port 5174 was free (0 listeners) and letting `playwright.config.js` set `VITE_USE_MOCKS=true` before each Playwright run.

## Отложено и не планируется здесь

- **WR-11** — граница радиокружка `1.178` / `1.554` при поле 3:1 (`TopicBallot.jsx`, `role="radio"`): единственный визуальный индикатор выбора ниже 3:1. Отложена верификатором в будущую UI-фазу (25-VERIFICATION.md § Deferred: «WR-11 стоит взять в ближайшую UI-фазу — это тот же класс дефекта, что закрывал 25-07»). **Не входит** в 25-08…25-10; `TopicBallot.jsx` и значения `--color-border` не трогаются.
- **12 backstop-пунктов** (геометрия 320px, реальный мобильный браузер, частично заполненная форма, 20 строк, длинные id, диалог несохранённых изменений): закрываются `/gsd-verify-work` (human verification), а не планом 25-10. Никаких geometry-ассертов 320px здесь нет.
- **WR-12** (провал отправки печатается `text-success-ink` — `AdminDigestPage.jsx:771`) и **WR-13** (условный страж темы / `reuseExistingServer` — риск флейка): вне трёх заявленных гэпов (вердикт `gaps`, не `fail`), здесь не адресуются.

## Next Phase Readiness

- `behavior_unverified` 25-04 #7 is closed: the in-flight label colour is now proven in-browser (computed style) and statically (G-21), and both can fail on their own mutations.
- `npm run test:js` → 97/97; Playwright `admin-chrome` 13/13, `admin.spec` 88/88; `npm run build` succeeds with no new Tailwind warnings (only the pre-existing chunk-size note).
- `waitForTimeout`/`page.clock` → 0 matches; `test.skip`/`test.fixme` → 0 matches (unchanged).

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*

## Self-Check: PASSED

- `25-10-SUMMARY.md` exists.
- Commit `dca85b7` (Task 1 test commit) present in history.
- `tests/admin-chrome.spec.js` + `tests/unit/test_semantic_token_coverage.js` are the only test files changed; `web/src` is clean (no production edits).
