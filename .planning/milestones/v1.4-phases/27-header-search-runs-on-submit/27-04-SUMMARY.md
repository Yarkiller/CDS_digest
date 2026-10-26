---
phase: 27-header-search-runs-on-submit
plan: 04
subsystem: ui
tags: [react, input-boundary, validation, landing-rule, empty-state, a11y-alert]

# Dependency graph
requires:
  - phase: 27
    plan: 03
    provides: the URL as the single trigger, so invalid and empty inputs now arrive through ?q
provides:
  - the qUrl === '' view-reset branch (clears rows without touching role or the cache)
  - the overlong inline rejection that reuses the validator's own message
  - "preSearch = qUrl === '' && error === null as the single landing gate"
affects: [27-05]

actuals:
  tokens: 9800
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Derive the landing flag from the URL synchronously, never from state that a 0-request path never sets"
    - "Copy comes from the validator's message field; the page holds no second literal"
    - "Prove a rejected input by its counter delta (0) as well as its rendered text"

key-files:
  created: []
  modified:
    - web/src/pages/KnowledgePage.jsx
    - tests/knowledge.spec.js

key-decisions:
  - "The empty branch clears the rows but leaves role and the snapshot cache alone — a URL reset is a view reset, not a data reset"
  - "The invalid branch writes validation.message (one call site), so «Сократите запрос» still appears on exactly two lines"
  - "preSearch reads qUrl, not activeQuery: an overlong query issues no request, so a state-derived flag would leak the hints"

patterns-established:
  - "A 501-code-point submission is asserted on both the rendered copy AND the counter, and the absence of maxlength is asserted rather than assumed"

requirements-completed: [KNOW-05]

coverage:
  - id: D1
    description: "Removing ?q from the header clears the two rendered rows, shows the hint chips, empties the page field and issues no request"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#removing ?q clears the rows"
        status: pass
    human_judgment: false
  - id: D2
    description: "A blank page-form submit shows «Введите запрос» with role=alert, aria-invalid and aria-describedby resolving to the node, leaving URL and counter untouched"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a blank page-form submit shows the inline error and issues no request"
        status: pass
    human_judgment: false
  - id: D3
    description: "A 501-code-point header submission renders «Сократите запрос», no rows, no hint chips, no error panel, 0 requests, and the full text in both inputs with no maxlength"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#an overlong header submit is rejected inline with no request"
        status: pass
    human_judgment: false
  - id: D4
    description: "The hint block is absent for an overlong, a zero-hit and a populated ?q (landing and results are mutually exclusive by qUrl)"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#the landing never coexists with a query"
        status: pass
    human_judgment: false
  - id: D5
    description: "A whitespace-only ?q (%20) trims to the landing: chips visible, no rows, empty field, 0 requests"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a whitespace-only q is the landing"
        status: pass
    human_judgment: false
  - id: D6
    description: "The hint set is exactly four fixed labels (RAG, SQL, качество данных, pgvector)"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#the hint set is four fixed labels"
        status: pass
    human_judgment: false
  - id: D7
    description: "The live region shows «Показано 2» for RAG and never echoes the query"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#the live region carries only the status copy"
        status: pass
    human_judgment: false
  - id: D8
    description: "The empty branch and the landing rule are both non-vacuous: removing the branch leaves 2 stale rows, and the old state-derived flag leaks 1 chip block on the overlong frame"
    verification:
      - kind: other
        ref: "manual mutation: delete the qUrl === '' branch -> #removing ?q clears the rows fails with Received: 2; restore -> green. Before Task 3's preSearch, #landing never coexists fails with Received: 1 (hint block)."
        status: pass
    human_judgment: true
    rationale: "Mutations are performed and reverted by hand; the evidence is a one-time observation, not a repeatable suite run."

duration: 40min
completed: 2026-10-22
status: complete
---

# Phase 27 Plan 04: Input boundary and the landing rule Summary

**Invalid input now arrives through the URL like valid input does, and each variant has a provable zero-request outcome: removing `?q` clears the rows but keeps the chip, an overlong query is rejected with the validator's own copy and no truncation, and the hint block became a pure function of `qUrl` so a landing can never sit on top of a query.**

## Performance

- **Duration:** 40 min
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- The `qUrl === ''` branch runs before `validateKnowledgeQuery`: it re-arms `lastHandledQueryRef`, clears `activeQuery`/`items`/`hasMore`/`nextOffset`/`error`/`inlineError`/`searching`/`loadingMore` and returns. `role` and `searchSnapshots` are deliberately untouched, so a URL reset does not become a data reset.
- The invalid branch now writes `validation.message` and stops before `runSearch`. Because the copy is read rather than authored, «Сократите запрос» still appears on exactly two lines (the two pre-existing sites in `handleSubmit`/`handleRoleChange`), and the effect adds none.
- `preSearch` is now `qUrl === '' && error === null`, read synchronously during render from the URL parameter. That single line hides the hints for overlong, in-flight, zero-hit and error frames without any extra condition — which is why Task 3 needed no other code.
- Seven Playwright cases cover the boundary (empty header submit, blank page-form submit with its `role="alert"`/`aria-invalid`/`aria-describedby` wiring), the overlong rejection (copy, 0 rows, 0 chips, no error panel, counter 0, 501 characters preserved in both inputs, no `maxlength`), the three-frame landing exclusion, the whitespace-only landing, the four fixed labels and the live region's copy-only text.

## Task Commits

1. **Task 1: Removing `?q` returns to the landing**
   - `5a7c20f` — `feat(27-04)`: the `qUrl === ''` branch (GREEN) plus the two boundary cases
   - `7c1a996` — `test(27-04)`: the boundary, overlong and landing-rule cases
2. **Tasks 2–3: Overlong rejection and the landing rule**
   - `e69bd90` — `feat(27-04)`: `validation.message` on the invalid branch, `preSearch` re-keyed on `qUrl`

**Plan metadata:** committed after this file (docs commit).

## Files Created/Modified

- `web/src/pages/KnowledgePage.jsx` — the empty branch, the invalid branch's inline copy, and the `preSearch` derivation.
- `tests/knowledge.spec.js` — seven cases, all reusing 27-02/03's helpers.

No new user-facing string, no class change, no `maxlength`, and `knowledgeApi.js` is untouched (`git diff --stat` empty; `npm run test:js` stays 112/112).

## Decisions Made

- **The empty branch precedes validation.** `?q=%20` trims to `''`, so it belongs to the empty path rather than to the validator's `EMPTY_QUERY` branch. That keeps the zero-request claim structural: the empty path cannot reach `runSearch` at all.
- **`validation.message`, not a second literal.** The plan's prohibition and the Copywriting Contract agree; the acceptance grep for the literal staying at 2 lines is what proves it.
- **`preSearch` reads the URL, not `activeQuery`.** This is the whole point of the task: an overlong query issues no request, so `activeQuery` stays `null` and the old flag rendered the landing over a query frame. The new flag is correct by construction for every frame the phase cares about.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two acceptance greps in this plan contradict each other**
- **Found during:** acceptance-criteria sweep
- **Issue:** Task 1 demands `rg -n "qUrl === ''"` return **exactly one** hit, but Task 3 mandates `preSearch = qUrl === '' && error === null` in the same file. After Task 3 the count is necessarily 3 (the branch, one doc comment, the derivation). The criterion was written per-task and cannot hold after the next task lands.
- **Fix:** none to the code — the criteria were read as "exactly one *guard branch*" (true: one `if`), and the count is recorded here rather than satisfied by mangling the derivation.
- **Verification:** `rg -n "qUrl === ''"` → the `if` at :145, a doc comment at :353, the derivation at :358.
- **Committed in:** `e69bd90`

**2. [Rule 3 - Blocker] "`maxlength` returns nothing" cannot coexist with a non-vacuous no-truncation pin**
- **Found during:** Task 2 test authoring
- **Issue:** the criterion demands `rg -n "maxlength" web/src tests/knowledge.spec.js` be empty, but the only honest way to prove "neither input truncates" is to assert the attribute is absent — which names it.
- **Fix:** the assertion stays (`getAttribute("maxlength")` → `null` on both inputs, plus the 501-character `inputValue` checks), and the grep is recorded as intentionally non-empty in the spec, never in `web/src`.
- **Verification:** `rg -n "maxlength" web/src` → empty; the spec contains the three assertion lines only.
- **Committed in:** `7c1a996`

### Nothing else deviated

No new string, no class, no adapter or pill edit, no new effect.

---

**Total deviations:** 2 (both in the plan's own acceptance greps, neither weakened an assertion)
**Impact on plan:** none on scope; both deviations made the checks stricter than the plan's prose.

## Issues Encountered

- **RED for Task 1 could not be observed in the intended order.** The empty branch and its two cases were already present in the working tree when this session reached them (a `feat(27-04)`-shaped diff plus the spec cases), so instead of re-deriving the RED, the branch was **removed and re-added**: with it gone, `#removing ?q clears the rows` failed with `Received: 2` (two stale RAG rows), and restoring it returned green. The non-vacuity claim therefore rests on an observation made in this session, not on the original transcript.
- **`#landing never coexists` reddened exactly where the plan predicted**, with `Received: 1` (the hint block on the overlong frame) — the only case in Task 3 that was not already a pin.

## Threat Flags

None beyond the plan's register. T-27-11 (overlong DoS) and T-27-13 (spoofing via a state-derived gate) are both mitigated and asserted; T-27-12's structural XSS probe remains 27-05's.

## Known Stubs

None.

## User Setup Required

None.

## Next Phase Readiness

- 27-05 must now order its own additions *above* these branches: the marker branch is first, then the ref guard, then the cache — and the history-discipline work (`replace` on chip change, `writeQueryToUrl`) sits on the same effect.
- `expectKnowledgeSettled`, `hitLinks`, `expectCount` and the X-2 helpers are the tools 27-05's error/retry and XSS cases should reuse.

---
*Phase: 27-header-search-runs-on-submit*
*Completed: 2026-10-22*

## Self-Check: PASSED

- `npx playwright test --project=web tests/knowledge.spec.js` → 23 passed.
- `npx playwright test --project=web tests/web-app.spec.js` → 55 passed.
- `npm run test:js` → 112 pass / 0 fail.
- `rg "maxlength" web/src` → empty; `rg "dangerouslySetInnerHTML"` on the page → empty.
- `rg -n "Сократите запрос"` on the page → 2 lines (both pre-existing); `rg -c "validation\.message"` → 2.
- `knowledgeApi.js` / `SearchPill.jsx` `git diff --stat` → empty.
- Commits exist: `5a7c20f`, `7c1a996`, `e69bd90`.
