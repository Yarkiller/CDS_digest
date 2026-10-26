---
phase: 27-header-search-runs-on-submit
plan: 02
subsystem: ui
tags: [react, react-router, useeffect, ref-guard, strictmode, playwright, request-counter]

# Dependency graph
requires:
  - phase: 27
    plan: 01
    provides: the frozen adapter (sha256 pin) and the single call-site gate that this plan had to keep green
provides:
  - "?q as the only search trigger: one ref-guarded effect in KnowledgePage.jsx"
  - "X-1 request counter at the searchKnowledge boundary (window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__)"
  - "X-2 harness affordance collector (live-searching / field-disabled / loading-state)"
  - "A settle gate that distinguishes the knowledge surface from the outgoing issue route"
  - knowledgeSurface/expectKnowledgeSettled test helpers reused by 27-03…27-05
affects: [27-03, 27-04, 27-05]

actuals:
  tokens: 14800
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Ref written synchronously before the first await, so StrictMode's setup->cleanup->setup finds the guard armed"
    - "Counter at the adapter boundary instead of page.route, because under VITE_USE_MOCKS=true no HTTP request exists"
    - "Surface-specific settle gate (kb-role-chips + live summary) instead of a row assertion that the previous route also satisfies"

key-files:
  created: []
  modified:
    - web/src/pages/KnowledgePage.jsx
    - tests/knowledge.spec.js

key-decisions:
  - "The URL is the only trigger (D-01): the effect is keyed on the literal [qUrl], and runSearch/searchParams/role are deliberately excluded"
  - "lastHandledQueryRef is assigned BEFORE runSearch, not inside it — the naive version measured 2 requests under StrictMode"
  - "The settle gate asserts kb-role-chips + the live summary, never a bare /materials/ row: IssuePage renders IssueToc anchors with identical accessible names"
  - "R-1 (searching || …) is kept as defense-in-depth and recorded as NOT independently discriminated by any test"

patterns-established:
  - "Non-vacuity by real mutation on the client: remove the guard, observe the stated wrong number, restore byte-identically, re-run"
  - "A settle gate must name a node that exists only on the target surface, or it can pass against the route being left"
  - "A transient in-flight state is observed by a collector that accumulates labels, never by a post-settle assertion"

requirements-completed: [KNOW-05]

coverage:
  - id: D1
    description: "A header Enter on / lands on /knowledge?q=RAG, renders the two RAG hits, hides the hint chips and mirrors RAG into the page field"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#header submit renders results from ?q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Changing ?q while the page is mounted replaces the rows (RAG row disappears, Anomaly row appears) at exactly +1 request"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#changing ?q while mounted replaces the rows"
        status: pass
    human_judgment: false
  - id: D3
    description: "One submission costs exactly one searchKnowledge call, and theme toggle, focus change, typing without Enter and a 1.2 s idle window add none"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#header submit issues exactly one search request"
        status: pass
    human_judgment: false
  - id: D4
    description: "The header path shows all three in-flight affordances (live-searching, field-disabled, loading-state)"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#the header path shows the in-flight live region"
        status: pass
    human_judgment: false
  - id: D5
    description: "A role chip change is its own deliberate action: exactly one new request and a narrowed result set"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a role chip change issues exactly one new request"
        status: pass
    human_judgment: false
  - id: D6
    description: "A zero-hit query renders nothing-found, keeps the reset control enabled, reports «Найдено 0 материалов» and costs one request"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a zero-hit query renders the empty state and no rows"
        status: pass
    human_judgment: false
  - id: D7
    description: "A hint chip click fills the field and costs zero requests"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a hint chip click fills the field without a request"
        status: pass
    human_judgment: false
  - id: D8
    description: "The single-request guarantee is non-vacuous: removing the ref guard makes the same assertion read 2"
    verification:
      - kind: other
        ref: "manual mutation: delete `if (lastHandledQueryRef.current === q) return` -> header submit reads 2 (StrictMode setup/cleanup/setup); guard restored byte-identically -> reads 1"
        status: pass
    human_judgment: true
    rationale: "The mutation is performed and reverted by hand; the evidence is a one-time observation, not a repeatable suite run."

duration: 65min
completed: 2026-10-22
status: complete
---

# Phase 27 Plan 02: Header submit drives the search Summary

**`?q` is now the only thing that starts a search: one effect keyed on the literal `[qUrl]`, a ref armed before the first await so StrictMode cannot double-fire it, and an X-1 counter at the adapter boundary that proved the naive version costs 2 requests where the guarded one costs 1.**

## Performance

- **Duration:** 65 min (including a full-suite re-run after the dev server died mid-run)
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `KnowledgePage.jsx` now has exactly two effects: the pre-existing toast timer and the data effect whose dependency array is the literal `[qUrl]`. `runSearch`, `searchParams` and `role` are deliberately absent — their identities change every render, and including them reproduces the duplicate fire this phase removes.
- `lastHandledQueryRef.current = q` is assigned **before** `void runSearch(...)`, not inside it. Measured: with the guard removed, one header Enter reads **2** (StrictMode's setup → cleanup → setup); with it, **1**.
- `bumpKnowledgeSearchCount()` sits as the first statement inside `runSearch`'s `try`, above `await searchKnowledge(...)` — exactly one call site, so failed and retried searches are counted the same way as successful ones.
- `setActiveQuery(q)` joined the non-append branch of `runSearch`, making the in-flight render coherent: the live summary and the zero-hit block both read `activeQuery`, so a search no longer spends its first commit in the pre-search landing state.
- Five new Playwright cases plus the two from Task 1 pin the behaviour: one request per submission across re-renders (theme toggle, focus change, typing without Enter, a 1.2 s idle window), the three in-flight affordances, chip change = +1, zero-hit, hint chip = 0.

## Task Commits

1. **Task 1: Tracer — header submit renders results from ?q**
   - `eb483d2` — `test(27-02)`: failing specs + the X-1 counter helpers (RED; landed on the hint-chip landing with counter 0)
   - `cf43ab7` — `feat(27-02)`: `[qUrl]` effect, ref guard, counter, `setActiveQuery` (GREEN)
2. **Task 2: Re-render, affordance, chip, zero-hit and hint-chip cases**
   - `c5e420a` — `feat(27-02)`: five cases, the X-2 collector, the settle gate and R-1

**Plan metadata:** committed after this file (docs commit).

## Files Created/Modified

- `web/src/pages/KnowledgePage.jsx` — +43/−1: `useRef` import, `SEARCH_COUNT_KEY`/`bumpKnowledgeSearchCount`, `qUrl`/`roleRef`/`lastHandledQueryRef` derivations, the `[qUrl]` effect, `setActiveQuery(q)`, and R-1.
- `tests/knowledge.spec.js` — +163: the X-1 counter helpers (`installKnowledgeCounter`/`readCount`/`expectCount`), the X-2 collector (`installAffordanceCollector`/`resetAffordanceLog`/`affordanceLog`), `knowledgeSurface`/`expectKnowledgeSettled`, `hitLinks`, and seven KNOW-05 cases.

`web/src/services/knowledgeApi.js`, `SearchPill.jsx` and `MaterialListRow.jsx` were not touched (`git diff --stat` empty), and the 27-01 digest gate stayed green throughout.

## Decisions Made

- **The settle gate is the knowledge surface, not a row.** This is the plan's most consequential deviation and it came from a real false green: `expect(page.getByRole("link", { name: /building production rag systems/i })).toBeVisible()` passed immediately after `toHaveURL(/\/knowledge?q=RAG$/)` while the extra case read the counter as **0**. `navigate()` updates the URL one commit before React swaps the route, and `IssuePage` (the outgoing surface) renders `IssueToc` anchors `to={/materials/${item.id}}` with the same accessible names. `expectKnowledgeSettled` now gates on `kb-role-chips` + the live summary — nodes that exist only on `/knowledge` — so every later row assertion is meaningful.
- **The chip change is a deliberate action, not a re-render.** ROADMAP criterion 3's «no extra request» is read as covering re-renders and history, so a chip click is asserted at exactly +1 (UI-SPEC C-09), not +0.
- **R-1 is defense-in-depth and is recorded as such.** `{searching || (activeQuery !== null && !error)}` was added per the UI-SPEC, then probed: with the line reverted the in-flight case still passes, because `setActiveQuery(q)` already makes `activeQuery` non-null in the same commit. The line is kept (it protects the narrow window where `searching` is true and `activeQuery` is not yet set) but **no test discriminates it** — stated here rather than implied by a green run.
- **The 4 s filter-toast timer is not exercised.** `setToast('Фильтр недоступен')` only fires on an `INVALID_ROLE` response, which the mock adapter never produces; a 4 s wait would assert nothing. The reason is a comment in the test, and the 1.2 s idle window covers timer-driven re-renders that are reachable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's Task 1 assertions were satisfiable by the outgoing route (false green)**
- **Found during:** Task 2, first full-spec run — the in-flight case failed with an empty affordance log while the counter read 0
- **Issue:** the plan's prescribed order (`toHaveURL` → row visible) can be satisfied by `IssuePage`'s `IssueToc` anchors before `KnowledgePage` mounts. Two of the seven cases were passing for the wrong reason and one was intermittently green.
- **Fix:** added `expectKnowledgeSettled(page, summary)` (gates on `kb-role-chips` + the live summary) and rewrote every case to settle through it before asserting rows.
- **Files modified:** `tests/knowledge.spec.js`
- **Verification:** 3 consecutive full-spec runs green (10/10 each); the RAG row assertion now only fires on the knowledge surface.
- **Committed in:** `c5e420a`

**2. [Rule 1 - Bug] The X-2 collector was sampled by `MutationObserver` only, and read too early**
- **Found during:** Task 2, in-flight case (a temporary `setInterval` probe and a phase-stamped sample log were used to diagnose)
- **Issue:** the observer fires after the mutations that already happened, so the seed sample caught nothing, and the test read the log right after `toHaveURL` — before the effect had started the request. The probe showed the three labels arriving ~80 ms into the search and clearing at ~2050 ms.
- **Fix:** the collector keeps the observer and the samples are read only after `expectKnowledgeSettled`; the diagnostic `setInterval`, the console logging and the sample log were all removed.
- **Files modified:** `tests/knowledge.spec.js`
- **Verification:** `rg "DEBUG-|console\.log|setInterval"` on the spec returns nothing; 3/3 runs green.
- **Committed in:** `c5e420a`

### Nothing else deviated

No adapter edit, no `SearchPill.jsx` edit, no class-name change, no new testid in app code (X-2 lives entirely in the harness).

---

**Total deviations:** 2 auto-fixed (both Rule 1 — the plan's own assertion strategy and instrumentation were unsound; neither weakened a gate, and the first made two cases stricter by rejecting a false green)
**Impact on plan:** none on scope; the settle-gate helper is reused by 27-03…27-05.

## Issues Encountered

- **The Playwright dev server died mid-run and produced 144 `ERR_CONNECTION_REFUSED` failures.** A single `npx playwright test --project=web` full-project run (188 tests, 6.8 min) went red on every test after ~test 44 with `net::ERR_CONNECTION_REFUSED` on `127.0.0.1:5174` — nothing to do with the change. Re-running in chunks against a dev server started explicitly (`VITE_USE_MOCKS=true npm run dev --prefix web -- --host 127.0.0.1 --port 5174`) gave **knowledge 10 passed**, **web-app 55 passed**, **auth+razbory+admin-chrome 34 passed**, **admin 89 passed**, and `npm run test:js` **112 pass / 0 fail**. Port 5174 was confirmed free before every run.
- **A long foreground Playwright invocation aborted at the tool layer** (`Command failed to spawn: Aborted`); the same run succeeded once backgrounded. Not a test or code condition.

## Threat Flags

None — the plan edits one page component and one spec. The counter is a `window` property written by the page and read by tests, with no network, storage or auth surface. The `readCount` helper throws when the instrument is missing, so a vacuous `0` cannot pass.

## Known Stubs

None.

## User Setup Required

None.

## Next Phase Readiness

- The `[qUrl]` effect is the single entry point 27-03 extends with the in-memory cache and the `submitId` marker; `lastHandledQueryRef` is the place a cache hit must also arm.
- `expectKnowledgeSettled` and `hitLinks` are the helpers 27-03…27-05 should reuse instead of re-deriving row assertions.
- The 27-01 gates remain the guard: `bumpKnowledgeSearchCount()` must stay the only counter site and the adapter must stay byte-identical.

---
*Phase: 27-header-search-runs-on-submit*
*Completed: 2026-10-22*

## Self-Check: PASSED

- `npx playwright test --project=web tests/knowledge.spec.js` → 10 passed.
- `npx playwright test --project=web tests/web-app.spec.js` → 55 passed (header `toHaveValue("RAG")` pin intact).
- `npm run test:js` → 112 pass / 0 fail (27-01 gates green).
- `rg -n "bumpKnowledgeSearchCount\(\)"` → 2 hits (the declaration at :31 and the single call at :122).
- `rg -n "searching \|\| \(activeQuery !== null && !error\)"` → 1 hit; `rg -n "aria-live"` → 1 hit.
- Commits exist: `eb483d2`, `cf43ab7`, `c5e420a`.
