---
phase: 27-header-search-runs-on-submit
plan: 03
subsystem: ui
tags: [react, react-router, data-router, module-scope-cache, lru, navigation-state, one-shot-marker]

# Dependency graph
requires:
  - phase: 27
    plan: 02
    provides: the [qUrl] effect, the X-1 counter, and the X-2 harness collector that this plan reuses unchanged
provides:
  - module-scope snapshot cache (searchSnapshots / snapshotKey / remember / recall / forget / lastRoleForQuery)
  - one-shot submitId protocol (SearchPill createSubmitId + KnowledgePage consume-and-strip)
  - restore-silence and marker-strip assertions
affects: [27-04, 27-05]

actuals:
  tokens: 21500
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Cache keyed by a NUL-joined string (role\\u0000q), never by an object or a selector"
    - "Lookup placed above runSearch so a restore is structurally unable to reach the counter"
    - "One-shot marker compared only with === and stripped with replace + state:null"

key-files:
  created: []
  modified:
    - web/src/pages/KnowledgePage.jsx
    - web/src/components/SearchPill.jsx
    - tests/knowledge.spec.js

key-decisions:
  - "The marker branch sits above BOTH the ref guard and the cache — not merely above the cache as the plan's prose first suggested"
  - "navigate(marker) must pass state in the SECOND argument: the data router ignores to.state"
  - "lastRoleForQuery is updated by handleRoleChange as well as by a successful search, so a remount looks the cache up under the chip the user last chose"

patterns-established:
  - "A module-scope Map is the only cache allowed: the reload case proves it dies with the document"
  - "A navigation marker is consumed and stripped in the same effect pass that uses it, with the refs armed before any await"

requirements-completed: [KNOW-05]

coverage:
  - id: D1
    description: "Back from a material restores the identical two rows with the counter still at 1, and the X-2 log stays empty — no in-flight affordance on a restore"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#returning from a material restores the rows with no request"
        status: pass
    human_judgment: false
  - id: D2
    description: "A same-document reload re-queries: the counter is re-installed at 0 and reads 1, so the cache never left the tab"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a reloaded URL re-queries because the cache is memory-only"
        status: pass
    human_judgment: false
  - id: D3
    description: "A first search renders no skeleton (the skeleton belongs to the append path)"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a first search renders no skeleton"
        status: pass
    human_judgment: false
  - id: D4
    description: "Re-submitting the same q from the header issues exactly one NEW request (counter 1 → 2) and keeps the URL at ?q=RAG"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#re-submitting the same q issues exactly one new request"
        status: pass
    human_judgment: false
  - id: D5
    description: "The submitId marker is stripped after consumption and a reload then costs exactly one request"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#the submitId marker is stripped after it is consumed"
        status: pass
    human_judgment: false
  - id: D6
    description: "A header submit resets a narrowed role chip to «Все»: 2 rows instead of 1, aria-pressed flipped, +1 request"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a header submit resets the role filter"
        status: pass
    human_judgment: false
  - id: D7
    description: "The strip assertion is non-vacuous: with setSearchParams removed the marker survives as «1792667269000-1»"
    verification:
      - kind: other
        ref: "manual mutation: delete the setSearchParams(searchParams, { replace: true, state: null }) call -> #the submitId marker is stripped fails with Received: \"1792667269000-1\"; the call restored in the same shape -> green"
        status: pass
    human_judgment: true
    rationale: "The mutation is performed and reverted by hand; the evidence is a one-time observation, not a repeatable suite run."

duration: 55min
completed: 2026-10-22
status: complete
---

# Phase 27 Plan 03: Snapshot cache and the one-shot `submitId` Summary

**Two identities for one trigger: `(role, q)` in a module-scope LRU cache makes Back from a material free, and an opaque one-shot `submitId` in history state makes a deliberate re-submit cost exactly one request — with the marker branch ordered above the ref guard so neither identity can swallow the other.**

## Performance

- **Duration:** 55 min
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `searchSnapshots` (module-scope `Map`, cap 20, LRU touch on read and on write) keyed by `` `${role}\u0000${q}` ``. `recallSearchSnapshot` sits **above** `runSearch`, whose first statement is `bumpKnowledgeSearchCount()`, so a restore is structurally unable to reach the counter — the Δ=0 guarantee is enforced by placement, not by discipline.
- The snapshot is evicted in `catch` under the same `(roleValue, q)` pair the success branch stores, so a failure is never cached and a failure under one role cannot evict another role's rows.
- `SearchPill` now produces `createSubmitId()` (`${Date.now()}-${seq}`); `KnowledgePage` compares it with `===` against `consumedSubmitIdRef`, arms both refs, resets the role to `all` (D-07), strips the marker with `setSearchParams(searchParams, { replace: true, state: null })`, and only then calls `runSearch`.
- `lastRoleForQuery` is written by a successful non-append search **and** by `handleRoleChange`, and seeds `useState(() => lastRoleForQuery)`, so the cache key and the restored chip agree after a remount (C-09).
- Six new Playwright cases: restore-with-no-request (including an empty X-2 log and a structural "no `data-state`/`aria-busy` on a chip" pin), reload re-queries, no skeleton, re-submit +1, marker stripped, role reset.

## Task Commits

1. **Task 1: Restore path**
   - `cabb589` — `test(27-03)`: failing cache-restore case (RED; Back read 2)
   - `32183b8` — `feat(27-03)`: module-scope cache, LRU, role seed, restore branch (GREEN)
2. **Task 2: One-shot `submitId`**
   - `6321970` — `test(27-03)`: failing re-submit (1, expected 2) and role-reset cases
   - `1cb6551` — `feat(27-03)`: marker protocol, consume-and-strip, reordering (GREEN)

**Plan metadata:** committed after this file (docs commit).

## Files Created/Modified

- `web/src/pages/KnowledgePage.jsx` — +84/−2 then +57/−4: cache block, role seed, restore branch, marker branch, `forgetSearchSnapshot` in `catch`, `lastRoleForQuery` in `handleRoleChange`.
- `web/src/components/SearchPill.jsx` — `submitSeq`/`createSubmitId`, object-form `navigate` with the marker.
- `tests/knowledge.spec.js` — six cases; every helper reused from 27-02 unchanged.

`knowledgeApi.js` and `MaterialListRow.jsx` untouched (`git diff --stat` empty); `npm run test:js` 112/112 keeps the adapter pin and the single call-site gate green.

## Decisions Made

- **The marker branch is checked before the ref guard, not just before the cache.** The plan placed the marker "after validateKnowledgeQuery and before the cache lookup", and the ref guard sits in that same span. Placing it after the guard made the re-submit a no-op (measured: counter stayed 1, chip stayed `DS`) because the guard sees an unchanged `q` and returns first. The final order is: validate → consume marker → ref guard → cache → `runSearch`.
- **`navigate` takes the marker in its second argument.** See the deviation below — this is the one place the plan's literal code could not work, and it failed silently (no error, `history.state.usr === null`).
- **`lastRoleForQuery` on chip change.** Without it a chip change followed by a material visit and Back would look the cache up under `all` and miss, burning a request the phase promises not to spend.
- **No assertion for C-12 paging.** The mock catalogue returns ≤5 rows against `DEFAULT_SEARCH_LIMIT = 10`, so `has_more` is never true; `hasMore`/`nextOffset` are stored and restored as part of the same object (that is code, exercised by every restore) but `nextOffset`-resume is recorded as manual-only in `27-VALIDATION.md` rather than asserted vacuously.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `navigate({ pathname, search, state })` silently drops `state` on a data router**
- **Found during:** Task 2 GREEN, third failing run (counter and chip both unchanged)
- **Issue:** `App.jsx` builds the app with `createBrowserRouter`. Its `navigate` calls `createLocation(currentLocation, path, opts && opts.state, …)` — state comes from the **second argument only**, so the marker inside the `To` object was discarded without an error. The evidence: `history.state === {"usr":null,…}` after a submit that definitely carried `state: { submitId }`.
- **Fix:** `navigate({ pathname: '/knowledge', search }, { state: { submitId: createSubmitId() } })`, with the reason in a comment so it is not "simplified" back later.
- **Files modified:** `web/src/components/SearchPill.jsx`
- **Verification:** 16/16 in `tests/knowledge.spec.js`; `history.state.usr.submitId` observed non-null before the strip and null after.
- **Committed in:** `1cb6551`

**2. [Rule 1 - Bug] The plan's branch placement made the re-submit a no-op**
- **Found during:** Task 2 GREEN, first run after adding the marker branch
- **Issue:** with the marker branch after `if (lastHandledQueryRef.current === q) return`, a same-`q` submission returned at the guard. Measured: counter 1 (expected 2), «Все» `aria-pressed="false"`.
- **Fix:** moved the marker branch above the ref guard (and therefore above the cache), matching the plan's must_have ("the marker beats the cache") and its `key_links`.
- **Files modified:** `web/src/pages/KnowledgePage.jsx`
- **Verification:** counter 1 → 2, chip reset, URL unchanged, 16/16 green.
- **Committed in:** `1cb6551`

**3. [Rule 3 - Blocker] Two acceptance greps were satisfied only by rewording comments**
- **Found during:** acceptance-criteria sweep
- **Issue:** the negative greps (`sessionStorage|localStorage|indexedDB|document.cookie` and `location.href`) matched explanatory comments that named the forbidden APIs in order to forbid them.
- **Fix:** reworded to "never persisted to any browser storage" and "never … a navigation target". The prohibitions still hold; the gates stay machine-checkable and non-vacuous.
- **Verification:** both greps empty; `web/src` contains no `MutationObserver`/`__KB_AFFORDANCE_LOG__`.

### Nothing else deviated

---

**Total deviations:** 3 auto-fixed (2 Rule 1 — the plan's literal code could not work on a data router and its branch ordering contradicted its own must_have; 1 Rule 3 — comment wording)
**Impact on plan:** none on scope. The marker protocol is stricter than the plan's prose: it is proven to survive neither the navigation nor a reload.

## Issues Encountered

- **The first probe reported a phantom `+1`.** An early `page.evaluate` probe reset the counter and then read it 1.5 s after Enter, catching the tail of the *initial* load's request rather than the re-submit. Re-probing after an explicit `Показано 2` wait showed the true delta of 0, which is what led to the `history.state` inspection and the `navigate` discovery. Lesson recorded: a counter read is only meaningful once the previous search has settled.
- Playwright dev-server stability: runs went through the manually started server (`VITE_USE_MOCKS=true`, 127.0.0.1:5174); no `ERR_CONNECTION_REFUSED` this plan.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| marker-in-history | `web/src/components/SearchPill.jsx`, `web/src/pages/KnowledgePage.jsx` | A client-generated token crosses into `history.state` and back. Mitigated as planned: equality-only comparison, stripped with `state: null`, never a URL/selector/key. No new endpoint, no persistence. |

## Known Stubs

None.

## User Setup Required

None.

## Next Phase Readiness

- 27-04 extends the same effect with the empty/overlong branches and the landing rule; the marker branch now sits first, so an overlong *marker* submission must be handled before it (27-04's own ordering task).
- 27-05 asserts the history discipline (Back after a chip change leaves `/knowledge`) and will reuse `expectKnowledgeSettled`, `hitLinks`, `expectCount` and the X-2 helpers.
- The 27-01 gates remain the guard: no adapter edit, no second `searchKnowledge(` site.

---
*Phase: 27-header-search-runs-on-submit*
*Completed: 2026-10-22*

## Self-Check: PASSED

- `npx playwright test --project=web tests/knowledge.spec.js` → 16 passed.
- `npx playwright test --project=web tests/web-app.spec.js` → 55 passed.
- `npm run test:js` → 112 pass / 0 fail.
- `rg "sessionStorage|localStorage|indexedDB|document\.cookie"` and `rg "location\.href|dangerouslySetInnerHTML"` on `KnowledgePage.jsx` → empty.
- `rg -n "setSearchParams"` → exactly one strip site (:168).
- `rg -n "consumedSubmitIdRef"` → 3 hits (declaration, equality, assignment).
- Commits exist: `cabb589`, `32183b8`, `6321970`, `1cb6551`.
