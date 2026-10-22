---
phase: 27-header-search-runs-on-submit
plan: 05
subsystem: ui
tags: [react, history-replace, search-submit, error-cache, xss, playwright]

# Dependency graph
requires:
  - phase: 27
    plan: 04
    provides: overlong inline rejection, empty-q reset, landing keyed on qUrl
  - phase: 27
    plan: 03
    provides: submitId marker, module snapshot cache, catch-side forgetSearchSnapshot
provides:
  - "{ replace: true } on the header navigate so Back leaves /knowledge"
  - "writeQueryToUrl(q) — page form and role chip write ?q with replace and no state"
  - "C-21 chip-from-landing URL write so hints cannot sit above a result surface"
  - "S10 error panel / retry / never-cached seed-then-fail pin"
  - "S11 XSS inert-text probe with a recorded innerHTML non-vacuity fail"
affects: [phase-27-verify]

actuals:
  tokens: 3152
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Both submit paths replace; only the header attaches submitId"
    - "Arm lastHandledQueryRef before writeQueryToUrl so the URL-change effect is a no-op"
    - "Seed-then-fail is the only falsifiable never-cached proof (store is success-only)"
    - "XSS probe is shown to fail against a scratch innerHTML sink, then the sink is reverted"

key-files:
  created: []
  modified:
    - web/src/components/SearchPill.jsx
    - web/src/pages/KnowledgePage.jsx
    - tests/knowledge.spec.js

key-decisions:
  - "Header navigate takes { replace: true, state: { submitId } }; the page form and chip write only q with replace and no state"
  - "lastHandledQueryRef is assigned before writeQueryToUrl so one click is one request"
  - "preSearch is restored to qUrl === '' && error === null (27-04 claimed it; the tree still had activeQuery)"
  - "Error-not-cached waits for the voting heading before goBack so KnowledgePage actually unmounts"

patterns-established:
  - "A replace vs push pin that starts on / must assert history.length; goBack from / is / either way"
  - "Cache-eligible revisit proofs must settle on the destination surface, not only its URL"

requirements-completed: [KNOW-05]

coverage:
  - id: D1
    description: "A header submit replaces the history entry so Back leaves /knowledge (C-07)"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a header submit replaces the history entry"
        status: pass
    human_judgment: false
  - id: D2
    description: "A page-form submit writes ?q with no state marker and issues exactly one request per click (D-02 + D-05)"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a page-form submit writes ?q and executes once"
        status: pass
    human_judgment: false
  - id: D3
    description: "A chip change on a URL that already carries q is byte-identical and adds no history entry; a chip on a landing with typed text writes ?q (C-21)"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a chip change keeps the URL and adds no history entry"
        status: pass
      - kind: e2e
        ref: "tests/knowledge.spec.js#a chip change on a landing with typed text writes ?q"
        status: pass
    human_judgment: false
  - id: D4
    description: "A failed ?q search shows kb-search-error + Повторить, hides hints and the live region, and retry costs exactly one new request"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a failed search shows the error panel and retry recovers"
        status: pass
    human_judgment: false
  - id: D5
    description: "A pre-seeded snapshot is evicted on failure so a cache-eligible goBack from /voting re-attempts (counters 1 → 2 → 3) instead of replaying rows"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#an error is not cached"
        status: pass
    human_judgment: false
  - id: D6
    description: "The header never shows a search error (no alert, no aria-invalid, no «Не удалось»/«Повторить» in header text)"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#the header never shows a search error"
        status: pass
    human_judgment: false
  - id: D7
    description: "Markup in ?q is inert text; the probe fails when a scratch innerHTML sink is introduced"
    requirement: KNOW-05
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#a markup payload in q is rendered as inert text"
        status: pass
    human_judgment: false

duration: 18min
completed: 2026-10-22
status: complete
---

# Phase 27 Plan 05: History, error boundary and XSS probe Summary

**Header and page-form submits both `replace`, the chip writes the executed `q` (C-21), failures reuse `kb-search-error` and are never cached, and `?q` markup stays inert text.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-10-22T11:37:00Z
- **Completed:** 2026-10-22T11:55:25Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- SearchPill's non-empty submit now passes `{ replace: true }` next to the existing `submitId` marker, so a header Enter cannot stack query variants. Measured RED: `history.length` grew 2 → 3; GREEN keeps it at 2 and `goBack` leaves `/knowledge`.
- `writeQueryToUrl(q)` writes only `q` with `{ replace: true }` and **no** `state`. `handleSubmit` and `handleRoleChange` assign `lastHandledQueryRef.current = validation.q` before the write, then still call `runSearch` (D-02 + D-05). One «Найти» click reads 1; a second click reads 2. A chip on `/knowledge` with typed `RAG` lands on `?q=RAG`, `kb-hint-chips` count 0, counter 1 (C-21).
- Error path is pinned, not rewritten: sticky `window.__DIGEST_FAIL_NEXT_KNOWLEDGE__` after `goto` → header Enter shows `kb-search-error` / «Не удалось найти материалы» / «Повторить», hints 0, live region 0, counter 1; retry clears the flag and restores 2 rows at counter 2. Seed-then-fail then `goBack` from `/voting` re-attempts (1 → 2 → 3). Header-scoped locators prove no alert and no error copy in `<header>`.
- Two markup payloads in `?q` (`<img src=x onerror=…>` and `</script><script>…`) create no elements, fire no handlers, leave `document.title` unchanged, stay out of the live region, and still issue one search. A scratch `innerHTML = query` sibling set `window.__KB_XSS__ = 1`; the file was restored with `git checkout -- web/src/pages/KnowledgePage.jsx` and the probe was not committed.

## Task Commits

1. **Task 1 RED: history / C-21 failing tests** - `aa53fb1` (test)
2. **Task 1 GREEN: replace + writeQueryToUrl + preSearch restore** - `26d3cf8` (feat)
3. **Task 2: error panel, retry, never-cached, header-free** - `057fcc0` (test — assertion layer; production already in 27-03)
4. **Task 3: XSS inert-text probe** - `e78228f` (test — assertion layer; no sink in production)

**Plan metadata:** committed after this file.

_Note: TDD tasks 2 and 3 are characterization pins. 27-03 already calls `forgetSearchSnapshot` in `catch` and `handleRetry` already calls `clearFailNextKnowledgeSearch`. No feat commit was required._

## Files Created/Modified

- `web/src/components/SearchPill.jsx` — `{ replace: true }` on the non-empty `navigate` (empty submit unchanged).
- `web/src/pages/KnowledgePage.jsx` — `writeQueryToUrl`, ref-then-write in `handleSubmit` / `handleRoleChange`, `preSearch = qUrl === '' && error === null`.
- `tests/knowledge.spec.js` — eight KNOW-05 cases (history, form write, chip pin, C-21, error/retry, never-cached, header-free, XSS).

## Decisions Made

- **Replace, never push, on both submit paths.** The header owns `submitId`; the page form and chip must not look like a header submission (that would reset the role per D-07).
- **Ref before URL write.** If `lastHandledQueryRef` is assigned after `setSearchParams`, the effect fires a second request. The counter pin (`1` then `2`) is what keeps the order honest.
- **Restore `preSearch` onto `qUrl`.** 27-04 SUMMARY claimed `qUrl === '' && error === null`; the post-27-04 tree still had `activeQuery === null && !error`. C-21's "hints above a result surface" frame only exists with the URL-derived flag, so GREEN restored it.
- **Never-cached revisit goes through `/voting` + `goBack`, not a header re-submit.** A header re-submit would take the `submitId` branch (D-06) and skip the cache lookup.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Restored `preSearch = qUrl === '' && error === null`**
- **Found during:** Task 1 GREEN
- **Issue:** 27-04 SUMMARY and e69bd90's message say the landing flag was re-keyed on `qUrl`, but `59298b3` still had `activeQuery === null && !error`. C-21's hint assertion is vacuous under the old flag because `runSearch` sets `activeQuery` at start.
- **Fix:** one-line restore plus the existing 27-04 comment. No new component or string.
- **Files modified:** `web/src/pages/KnowledgePage.jsx`
- **Verification:** `the landing never coexists with a query` and `a chip change on a landing with typed text writes ?q` both green.
- **Committed in:** `26d3cf8`

**2. [Rule 1 - Bug] Header-history pin uses `history.length`, not only `goBack`**
- **Found during:** Task 1 RED
- **Issue:** `goto("/")` → submit → `goBack` returns to `/` for both push and replace, so `not.toHaveURL(/\/knowledge/)` is green without `replace`. Starting on `/knowledge` made `goBack` a no-op (single history entry after the marker strip).
- **Fix:** assert `history.length` stays at the pre-submit value (RED observed 2 → 3), then `goBack` + `not.toHaveURL(/\/knowledge/)` as the plan asked.
- **Files modified:** `tests/knowledge.spec.js`
- **Verification:** RED 2 → 3; GREEN stays 2.
- **Committed in:** `aa53fb1` (test) / `26d3cf8` (feat)

**3. [Rule 1 - Bug] Never-cached case must settle on the voting heading before `goBack`**
- **Found during:** Task 2
- **Issue:** `toHaveURL(/\/voting/)` can fire before the outlet unmounts `KnowledgePage`. Immediate `goBack` reuses the still-mounted error state (ref guard, counter stays 2, panel still up).
- **Fix:** wait for `getByRole("heading", { name: /голосование/i })` then `goBack`.
- **Files modified:** `tests/knowledge.spec.js`
- **Verification:** counters 1 → 2 → 3. Mutation: commenting out `forgetSearchSnapshot` in `catch` made the revisit restore the seeded rows (`kb-search-error` absent). Restored with `git checkout -- web/src/pages/KnowledgePage.jsx`.
- **Committed in:** `057fcc0` (test only; mutation not committed)

---

**Total deviations:** 3 auto-fixed (2 missing-critical/test-honesty, 1 race)
**Impact on plan:** All three are required for the assertions to be non-vacuous. No scope creep. `knowledgeApi.js` stayed byte-identical.

## XSS non-vacuity (Task 3)

Temporary scratch in `KnowledgeSearchForm`: a sibling `div` with `ref={(node) => { if (node) node.innerHTML = query }}`. Re-ran `-g "rendered as inert text"`. **Failed:** `expect(imgProbe.xss).toBeUndefined()` received `1` (`window.__KB_XSS__` set by the injected `onerror`). Restored with `git checkout -- web/src/pages/KnowledgePage.jsx`. The probe was not committed. Source gate `dangerouslySetInnerHTML|\.innerHTML|document\.write|document\.title\s*=` over `web/src` is empty.

## TDD Gate Compliance

| Task | RED | GREEN | Notes |
|------|-----|-------|-------|
| 1 (tracer) | `aa53fb1` | `26d3cf8` | History 2→3; form `?q` absent; C-21 URL absent |
| 2 | characterization | n/a | Production already in 27-03; tests are the deliverable. Mutation proved the catch call. |
| 3 | characterization | n/a | No HTML sink in production; innerHTML probe recorded above and reverted |

## Issues Encountered

- Recurring 5174 listener: killed via `Get-NetTCPConnection -LocalPort 5174 -State Listen` before every Playwright run. Clean re-runs were green.
- Previous partial 27-05 commits (`0f748ee` / `25dbe97`) were already reverted (`99cb200` / `cd4b64b`). This run re-implemented; those commits were not restored.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 27's five plans now all have SUMMARYs. Ready for `/gsd-verify-work 27`. `knowledgeApi.js` byte-identical; no new component, token, string or spec file.

Plan-level verification this run:

- `npx playwright test --project=web tests/knowledge.spec.js` — 31 passed
- `npx playwright test --project=web tests/web-app.spec.js` — 55 passed
- `npm run test:js` — 112 passed
- `git diff --exit-code -- web/src/services/knowledgeApi.js` — clean

---
*Phase: 27-header-search-runs-on-submit*
*Completed: 2026-10-22*

## Self-Check: PASSED

- FOUND: `web/src/pages/KnowledgePage.jsx`
- FOUND: `web/src/components/SearchPill.jsx`
- FOUND: `tests/knowledge.spec.js`
- FOUND: `aa53fb1` test(27-05) history/C-21 RED
- FOUND: `26d3cf8` feat(27-05) replace + writeQueryToUrl
- FOUND: `057fcc0` test(27-05) error panel / never-cached
- FOUND: `e78228f` test(27-05) XSS inert text
