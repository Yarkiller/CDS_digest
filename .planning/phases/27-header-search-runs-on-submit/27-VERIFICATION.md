---
phase: 27-header-search-runs-on-submit
verified: 2026-10-22T12:22:00Z
status: human_needed
score: 29/32 must-haves verified
behavior_unverified: 2
overrides_applied: 0
goal: "One Enter from the header produces results."
requirements:
  KNOW-05: satisfied
requirement_ids_in_plans: [KNOW-05]
requirement_ids_in_requirements_md: [KNOW-05]
orphaned_requirements: []
unmapped_requirement_ids: []
decision_coverage:
  honored: 10
  total: 10
  not_honored: []
gaps: []
behavior_unverified_items:
  - truth: "E5 · partial / C-12 — a paginated delivery is stored and restored as one snapshot; «Показать ещё» resumes at nextOffset"
    test: "On a live catalogue where has_more is true, search, click «Показать ещё», open a hit, then Back."
    expected: "The restored snapshot keeps the merged items, hasMore and nextOffset; the next «Показать ещё» continues from the shown-rows count, with Δ=0 on restore."
    why_human: "Mock catalogue is 8 rows with DEFAULT_SEARCH_LIMIT=10, so has_more is never true. Presence of hasMore/nextOffset on the Map entry cannot prove resume."
  - truth: "E3 · error — a failed role change shows kb-filter-toast «Фильтр недоступен» for 4 s while kb-search-error renders separately"
    test: "Force an INVALID_ROLE response (live adapter or a dedicated fail-next-role harness), then click a role chip on a settled search."
    expected: "Toast «Фильтр недоступен» for ~4 s; search error, if any, is kb-search-error, not the header."
    why_human: "The mock adapter never returns INVALID_ROLE. searchFailureState + setToast exist, but no test can redden this path."
human_verification:
  - test: "At 320/390/1280, submit a long query and inspect hint chips, MaterialListRow titles/snippets, the zero-hit card, the live region, and kb-search-error."
    expected: "Text wraps inside the existing flex-wrap / grid-cols-[4rem_minmax(0,1fr)] / p-8 / panel layout. No new truncate, line-clamp, or scroll container on these surfaces."
    why_human: "Six PLAN truths are tagged verification: backstop (E3/E4/E5/E6/E7/E8 overflow). Presence of flex-wrap and absence of truncate is wiring, not wrap proof."
  - test: "On a live catalogue where has_more is true, search, paginate with «Показать ещё», open a material, then Back."
    expected: "Restored rows include the appended page; the next «Показать ещё» continues from nextOffset. Restore itself issues 0 requests."
    why_human: "C-12 resume is listed as Manual-Only in 27-VALIDATION.md; the mock never sets has_more."
  - test: "Trigger INVALID_ROLE on a role-chip change (live API or a role-fail harness)."
    expected: "kb-filter-toast «Фильтр недоступен» for 4 s; the header stays free of the search error."
    why_human: "Mock never produces INVALID_ROLE; this PLAN-03 must-have is present in code and unexercised."
---

# Phase 27: Header search runs on submit — Verification Report

**Phase Goal:** One Enter from the header produces results.
**Verified:** 2026-10-22T12:22:00Z
**Status:** human_needed
**Re-verification:** No — initial verification (no previous `27-VERIFICATION.md` existed)

Goal is observably true in the tree: one Enter in the header searchbox navigates to `/knowledge?q=…`, the page effect runs `searchKnowledge` once, and a hit row is on screen without clicking «Найти». KNOW-05 is satisfied. Status is `human_needed` only because two PLAN truths have no runtime exercise and six overflow truths are tagged `verification: backstop`.

SUMMARY.md claims were not treated as evidence. Production files, tests, greps, the two `node:test` gates, and `git diff --exit-code -- web/src/services/knowledgeApi.js` were.

## Goal Achievement

### Observable Truths

Roadmap success criteria are 1–5 (criterion 3 split into re-render/history vs chip, matching locked KNOW-02 / PLAN deviation). Remaining rows are PLAN must-haves that are not restatements of those criteria. E\* copy/layout rows that restate a numbered truth are folded into that row.

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Typing in the header and pressing Enter lands on «База знаний» with results already rendered; «Найти» is never clicked (ROADMAP 1 / KNOW-05 c1) | ✓ VERIFIED | `tests/knowledge.spec.js` `header submit renders results from ?q`: `fill` + `press("Enter")` on `searchbox` «Поиск Digest CDS», URL `/knowledge?q=RAG`, hit «Building Production RAG Systems» visible, `kb-hint-chips` count 0, page field `RAG`, counter 1. `SearchPill.jsx` `onSubmit` only `navigate`s. |
| 2 | Exactly one search per submission (ROADMAP 2 / KNOW-05 c2) | ✓ VERIFIED | X-1 `bumpKnowledgeSearchCount()` is the first statement inside `runSearch` `try`, immediately before `await searchKnowledge`. `expectCount(page, 1, "header submit")` and `expectCount(page, 1, "settled")`. ROADMAP's `page.route` proof is vacuous under `VITE_USE_MOCKS=true` (CONTEXT discretion 1); the counter is the locked instrument. `readCount` throws if the global is missing. Static gate: one non-comment `searchKnowledge(` in `web/src`. |
| 3 | Re-render after results (theme, focus, typing, idle) issues no extra request; Back/Forward do not re-issue (ROADMAP 3 re-render/history half) | ✓ VERIFIED | `header submit issues exactly one search request` pins 1 after theme-toggle, blur, typing without Enter, and 1200 ms idle. `returning from a material restores the rows with no request` pins counter still 1 and empty X-2 log. `lastHandledQueryRef` is assigned before `runSearch`. |
| 4 | A role-chip change is a deliberate action and issues exactly +1 (PLAN / KNOW-02 reading of ROADMAP 3) | ✓ VERIFIED | `a role chip change issues exactly one new request`: SQL 5 rows at 1, DS click → 1 row + counter 2. ROADMAP's parenthetical listing «role chip change» as a mere re-render contradicts locked KNOW-02/D-64 and `tests/knowledge.spec.js` KNOW-02 pin; PLAN deviations document the intended reading. Not a gap. |
| 5 | Empty / whitespace submit navigates to «База знаний» and issues zero search requests (ROADMAP 4 / KNOW-05) | ✓ VERIFIED | `removing ?q clears the rows`: empty header Enter → `/knowledge`, 0 hits, hint chips visible, counter stays 1. `a whitespace-only q is the landing`: `?q=%20` → chips, 0 hits, field `""`, counter 0. `a blank page-form submit…`: «Введите запрос», counter 0. `SearchPill` empty path `navigate('/knowledge')` with no `searchKnowledge` import. |
| 6 | `knowledgeApi.js` stays byte-identical (C-24) | ✓ VERIFIED | `FROZEN_SHA256 = bce5c54e08f588e4ebf816466411b74bbe8d1896f6ab6942afb2469298d2f29f`. This session: digest matches, LF length 6283, 0 CRLF, `git diff --exit-code` clean. `node --test tests/unit/test_knowledge_api_snapshot.js` → pass 1. |
| 7 | Exactly one `web/src` module imports `searchKnowledge` | ✓ VERIFIED | Gate `imports searchKnowledge in exactly one module` deepEquals `['web/src/pages/KnowledgePage.jsx']`. `rg` confirms only that page plus the adapter declaration. |
| 8 | Exactly one non-comment `searchKnowledge(` call; counter and extra limiter stay out of the adapter | ✓ VERIFIED | Gate pass 3/3. `bumpKnowledgeSearchCount` lives in `KnowledgePage.jsx`. Adapter has 0 `__DIGEST_KNOWLEDGE_SEARCH_COUNT__`. `DEFAULT_SEARCH_LIMIT` defined only in the adapter (declaration regex, not bare token). Walker anti-vacuum `files.length > 20`. |
| 9 | A `?q` change while mounted replaces the rows (C-03) | ✓ VERIFIED | `changing ?q while mounted replaces the rows`: RAG → SQL via header, Anomaly visible, RAG count 0, counter 2. |
| 10 | R-1 / X-2: header path records live-searching, field-disabled, loading-state | ✓ VERIFIED | Status node condition `searching \|\| (activeQuery !== null && !error)`. Harness `MutationObserver` in the spec only (`rg MutationObserver web/src` empty). Test asserts all three labels, then chips 0, then the row. |
| 11 | `?q` drives the page field (D-10) | ✓ VERIFIED | Effect's first statement `setQuery(qUrl)`. Header RAG submit asserts page searchbox value `RAG`. |
| 12 | Header pill never gains loading or search-error UI (E1 loading/error) | ✓ VERIFIED | `SearchPill.jsx` has no `disabled`, `data-state`, `searchKnowledge`, or error node. `the header never shows a search error` scopes locators to `header`: alert count 0, no `aria-invalid`, innerText not matching `/Не удалось\|Повторить/`. |
| 13 | Hint-chip click fills the field and issues 0 requests (D-60) | ✓ VERIFIED | `a hint chip click fills the field without a request`: field `RAG`, 0 hits, counter 0. `onClick={() => setQuery(hint)}` only. |
| 14 | Zero-hit query renders «Ничего не нашли», 0 hits, 0 hint chips, live «Найдено 0 материалов» | ✓ VERIFIED | `a zero-hit query renders the empty state and no rows` + counter 1. Control that C-01 is query-dependent. |
| 15 | Back from `/materials/:id` restores the same rows at Δ=0, with no in-flight affordance; reload re-queries | ✓ VERIFIED | Restore test: 2 hits, counter 1, affordance log `[]`, role chips `[data-state],[aria-busy]` count 0. Reload test: post-reload counter 1 (init script resets to 0). Cache is module-scope `Map`; `rg sessionStorage\|localStorage\|indexedDB\|document.cookie` on `KnowledgePage.jsx` empty. First search: `kb-skeleton` count 0. |
| 16 | Re-submitting the same `q` from the header costs exactly +1 (C-11 / D-05 / D-06) | ✓ VERIFIED | `re-submitting the same q issues exactly one new request`: 1 → 2. Marker branch sits above the ref guard and `recallSearchSnapshot`. |
| 17 | One-shot `submitId` is compared with `===`, then stripped; it does not survive reload | ✓ VERIFIED | `createSubmitId()` in `SearchPill`; consume + `setSearchParams(searchParams, { replace: true, state: null })`. Test polls `history.state` until `submitId` is null; reload counter 1. |
| 18 | Header submit resets the role filter to «Все» (D-07) | ✓ VERIFIED | `a header submit resets the role filter`: DS-narrowed SQL → header RAG → 2 hits, «Все» pressed, DS not pressed, counter 3. Effect sets `roleRef` / `setRole` / `lastRoleForQuery` to `'all'` before `runSearch`. |
| 19 | Removing `?q` while mounted returns to the landing and clears rows (C-16) | ✓ VERIFIED | `if (qUrl === '')` clears items/activeQuery/error/searching and returns without `runSearch`. Test: 2 hits → empty Enter → 0 hits, chips visible, counter unchanged. Does not clear `role` or the Map (prohibition). |
| 20 | Overlong header submit is an inline rejection, 0 requests, full text, no `maxlength` (C-18) | ✓ VERIFIED | From `/`, 501 `a`s: URL `?q=a{501}`, «Сократите запрос» via `validation.message`, 0 hits, 0 chips, 0 `kb-search-error`, counter 0, both inputs length 501, `maxlength` null. `rg maxlength web/src` empty. Literals «Сократите запрос» remain two (`handleSubmit` / `handleRoleChange`); the effect uses `validation.message`. See WR-03 for the untested mounted transition. |
| 21 | Landing rule: `kb-hint-chips` ⟺ `qUrl === '' && error === null` | ✓ VERIFIED | `preSearch = qUrl === '' && error === null` is the only condition wrapping the hint block. `the landing never coexists with a query` covers overlong / zzzz / RAG. Four fixed labels test: RAG, SQL, качество данных, pgvector. |
| 22 | Live region carries only status copy, never the query (E6) | ✓ VERIFIED | One `aria-live="polite"` node. RAG search: text `Показано 2`, does not match `/RAG/`. |
| 23 | Non-empty header submit uses `replace`; Back leaves `/knowledge` (C-07) | ✓ VERIFIED | `navigate(..., { replace: true, state: { submitId } })`. Test pins `history.length` unchanged then `not.toHaveURL(/\/knowledge/)`. See WR-02 for the empty path, which still `push`es. |
| 24 | Page-form submit writes `?q` with replace and no `state`, one request per click (D-02 + D-05) | ✓ VERIFIED | `writeQueryToUrl` → `setSearchParams(q ? { q } : {}, { replace: true })`. `handleSubmit` assigns `lastHandledQueryRef` then writes then `runSearch`. Test: 1 then 2 on two «Найти» clicks, URL stays `?q=RAG`. |
| 25 | Role-chip change writes executed `q` with replace (C-21) and adds no history entry (C-06) | ✓ VERIFIED | `handleRoleChange` assigns the ref then `writeQueryToUrl`. `a chip change keeps the URL…` URL byte-identical, Back leaves `/knowledge`. `a chip change on a landing with typed text writes ?q`: landing + typed RAG + DS → `/knowledge?q=RAG`, chips 0, counter 1. |
| 26 | Failed `?q` search shows `kb-search-error` + «Повторить»; retry +1; error is never cached | ✓ VERIFIED | Fail test: panel «Не удалось найти материалы», hints 0, live 0, hits 0, counter 1; retry → 2 hits, panel gone, counter 2; panel has no loading affordance. Seed-then-fail: counters 1 → 2 → 3, panel still visible, 0 hits. `forgetSearchSnapshot(roleValue, q)` in `catch` before `setError`. |
| 27 | Markup in `?q` is inert text; no HTML sinks in `web/src` (C-13) | ✓ VERIFIED | XSS test: `__KB_XSS__` undefined, 0 `img[src=x]`, 0 `[onerror]`, title has no `<img`, field holds the payload, counter 1; script payload likewise, live region has no `script`. `rg dangerouslySetInnerHTML\|\.innerHTML\|document\.write\|document\.title\s*=` over `web/src` empty. |
| 28 | SearchPill stays navigation-only | ✓ VERIFIED | No `knowledgeApi` / `searchKnowledge` / counter import. Single-call-site gate would redden a second caller. Pill only produces URL + opaque `submitId`. |
| 29 | Static gates are auto-discovered and non-vacuous by construction | ✓ VERIFIED | `scripts/run-unit-js.cjs` still flat `readdirSync` + `.endsWith('.js')` — no allowlist. Digest `assert.equal` fails on any content edit; call-site gate names the offending path and pins the declaration it skips. This session: 4/4 unit tests pass. |
| 30 | Overflow wrap on chips / rows / zero-hit card / live region / error panel (E3–E8 overflow) | ⚠️ insufficient_spec | `verification: backstop`. No `truncate`/`line-clamp` in `KnowledgePage.jsx` or `MaterialListRow.jsx`; hint/role chips use `flex-wrap`; zero-hit card is `p-8`. That is wiring, not wrap proof. See Human Verification. |
| 31 | C-12 «Показать ещё» resumes at stored `nextOffset` | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `rememberSearchSnapshot` stores `{ items, hasMore, nextOffset, limit }`; restore copies those fields. Resume cannot run: mock 8 rows, limit 10. 27-VALIDATION.md Manual-Only. |
| 32 | E3 · error — INVALID_ROLE chip change shows «Фильтр недоступен» toast | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `searchFailureState` + `setToast('Фильтр недоступен')` exist. Mock never returns `INVALID_ROLE`. PLAN 02 already recorded the 4 s timer as unexercised. |

**Score:** 29/32 truths verified (2 present, behavior-unverified; 1 backstop abstention)

### ROADMAP wording vs locked decisions (not gaps)

- **SC 2 proof instrument.** ROADMAP asks for Playwright `page.route` on `/knowledge/search`. CONTEXT discretion 1 forbids it under mocks (`page.route` would count 0 and pass vacuously). Implementation uses `window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__` at the `searchKnowledge` boundary. Intent of «exactly one request» is proven.
- **SC 3 parenthetical «role chip change».** Literal «chip change issues 0» would regress KNOW-02/D-64. PLAN implements +1 for chips and Δ=0 for re-render/history. Intent of «no extra request from re-renders and Back» is proven.

No `overrides:` applied — these are the locked readings, not deviations that hide a miss.

### Review warnings WR-01…WR-04 (advisory, not must-have gaps)

| ID | Verdict | Why not a blocking gap |
| --- | --- | --- |
| WR-01 stale overlapping `runSearch` | ✅ **RESOLVED 2026-10-22** | Was: a header cannot be `disabled` (pill is payload-only), so two in-flight submits could commit the older query last. Fixed under TDD in `bf11782`: `runSearch` claims a generation before its first await and the success, error and `finally` branches re-check it, so a superseded response touches neither the rows, the snapshot cache nor the spinner. Red-first test holds the mock's fixed `delay(80)` timers and releases them in reverse order (failed with «Показано 2» under `?q=SQL`). `knowledge` 35/35, `web-app` 55/55, `test:js` 112/112. |
| WR-02 empty header `navigate('/knowledge')` still pushes | ⚠️ WARNING | C-07/truth 23 are about the non-empty replace path (tested). ROADMAP 4 only requires 0 API calls. Hole: from `/knowledge?q=RAG`, empty Enter stacks a landing; Back returns the query. |
| WR-03 overlong on a mounted result surface does not `setItems([])` | ✅ **RESOLVED 2026-10-22** | Raised from WARNING to **BLOCKER** by `27-UI-REVIEW.md` (the `overlong` state must render «строк нет», so the screen was self-contradicting). Fixed under TDD in `4eba79e`: red-first case `an overlong submit on a mounted result surface clears the rows`, then a four-line view reset (`setItems([])`, `setHasMore(false)`, `setNextOffset(0)`, `setActiveQuery(null)`) in the invalid branch of the `?q` effect. `knowledge.spec.js` 32/32, `web-app.spec.js` 55/55, `test:js` 112/112. |
| WR-04 `handleResetFilter` does not write `?q` | ℹ️ INFO | 27-05 action explicitly leaves retry / load-more / reset calling `runSearch` directly because `q` is already in the URL. KNOW-04 already covers reset. Out of this phase's must-haves. |

None of these match Phase 28's goal (live DeepSeek ingest proof), so they are **not deferred**. They are follow-ups, not `gaps_found`.

### Deferred Items

None. Phase 28 does not cover header-search races, empty-submit history, overlong view-reset, or paging resume.

### Required Artifacts

`gsd-tools query verify.artifacts` returned `total: 0` because PLAN YAML lists artifact paths as strings, not `{path, provides}` objects. Manual three-level + data-flow check:

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `web/src/pages/KnowledgePage.jsx` | `?q` effect, X-1 counter, cache, submitId consume, empty/overlong branches, `writeQueryToUrl`, R-1 gate | ✓ VERIFIED | ~600 lines; `useEffect([qUrl, submitId])`; `runSearch` → `searchKnowledge`; not a stub |
| `web/src/components/SearchPill.jsx` | `replace: true` + `submitId` on non-empty submit; empty → `/knowledge` | ✓ VERIFIED | Navigation-only; wired from the shell (pre-existing). Empty path still pushes (WR-02) |
| `tests/knowledge.spec.js` | KNOW-05 describe with counter, X-2, restore, boundary, history, error, XSS | ✓ VERIFIED | 29 cases in `KNOW-05 header submit runs the search` plus KNOW-01…04 honesty block |
| `tests/unit/test_knowledge_api_snapshot.js` | sha256 pin over LF-normalised adapter | ✓ VERIFIED | Pass 1 this session |
| `tests/unit/test_knowledge_search_single_call_site.js` | one import, one call, counter/limiter out of adapter | ✓ VERIFIED | Pass 3 this session |
| `web/src/services/knowledgeApi.js` | Untouched frozen adapter | ✓ VERIFIED | Digest match; git clean. Not modified by this phase (prohibition) |

**Artifacts:** 6/6 verified (adapter counted as the freeze contract, not a produced file)

### Key Link Verification

`gsd-tools query verify.key-links` also returned `total: 0` (string-form `key_links`). Manual:

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `SearchPill.onSubmit` | `/knowledge?q=` | `navigate({ pathname, search }, { replace: true, state: { submitId } })` | ✓ WIRED | Non-empty path. Empty path is a separate `navigate('/knowledge')` without replace |
| `?q` | `useEffect` | `qUrl = (searchParams.get('q') ?? '').trim()` deps `[qUrl, submitId]` | ✓ WIRED | |
| Effect | `runSearch` → `searchKnowledge` | Single call site; `bumpKnowledgeSearchCount` first in `try` | ✓ WIRED | X-1 sits on the only execution path |
| `lastHandledQueryRef.current = q` | `await searchKnowledge` | Synchronous assignment before `void runSearch` / before URL write | ✓ WIRED | StrictMode / form-double-fire guard |
| Cache lookup | `runSearch` | `recallSearchSnapshot` between ref guard and `runSearch`; restore never calls the adapter | ✓ WIRED | Counter lives inside `runSearch` |
| `location.state.submitId` | strip | `consumedSubmitIdRef` `===` then `setSearchParams(..., { replace: true, state: null })` | ✓ WIRED | Marker branch above cache |
| `handleSubmit` / `handleRoleChange` | URL | `lastHandledQueryRef` then `writeQueryToUrl` then `runSearch` | ✓ WIRED | |
| `handleRetry` | `runSearch` | `clearFailNextKnowledgeSearch()` then `runSearch` | ✓ WIRED | Sticky flag is why retry can succeed in-document |
| Snapshot `catch` | cache | `forgetSearchSnapshot(roleValue, q)` before `setError` | ✓ WIRED | Same key as success store |
| `tests/unit/*.js` | `scripts/run-unit-js.cjs` | flat `readdirSync` glob | ✓ WIRED | No config edit |

**Wiring:** 10/10 key links wired (empty-submit replace is WR-02, not an unwired link)

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `KnowledgePage` | `qUrl` | `searchParams.get('q')` (React Router) | Yes — header/form/chip writes | ✓ FLOWING |
| `KnowledgePage` | `items` | `searchKnowledge` DTO, or `recallSearchSnapshot` | Yes — mock catalogue under `VITE_USE_MOCKS=true` is the project's e2e source of truth (CONTEXT). Zero-hit `zzzz` proves it is not a static list | ✓ FLOWING |
| `KnowledgePage` | `window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__` | `bumpKnowledgeSearchCount` at the adapter boundary | Yes — incremented on every attempt including throws | ✓ FLOWING |
| `KnowledgePage` | `searchSnapshots` | module-scope `Map`, success-only; `forget` on catch | Yes — restore Δ=0 vs reload Δ=1 proves it | ✓ FLOWING |
| `SearchPill` | `submitId` | `createSubmitId()` → `location.state` | Yes — consumed and stripped | ✓ FLOWING |
| Hit titles | `MaterialListRow` `material` | `dto.items` | Yes — titles are React text children | ✓ FLOWING |
| Inline error | `inlineError` | `validateKnowledgeQuery(...).message` on the effect path | Yes — validator literals, not user text | ✓ FLOWING |

No hollow props. Mock mode is intentional, not a disconnected stub.

### Behavioral Spot-Checks

Playwright full suite was **not** re-run here (Step 7b: do not start servers; orchestrator already recorded `npm test` 215 passed / 4.8m). Unit gates were run in this process.

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Adapter digest pin | `node --test tests/unit/test_knowledge_api_snapshot.js` | `# pass 1` / `# fail 0` | ✓ PASS |
| Single call-site gate | `node --test tests/unit/test_knowledge_search_single_call_site.js` | `# pass 3` / `# fail 0` | ✓ PASS |
| KNOW-05 e2e cases exist (not re-run) | enumerate `test("` in `tests/knowledge.spec.js` KNOW-05 describe | 29 named cases covering header Enter, counter, restore, boundary, history, error, XSS | ✓ PASS (existence) |
| Adapter git-clean | `git diff --exit-code -- web/src/services/knowledgeApi.js` | clean; sha256 matches freeze | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| --- | --- | --- | --- |
| — | — | No `scripts/*/tests/probe-*.sh` and no PLAN/SUMMARY probe declaration | SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| KNOW-05 | 27-01, 27-02, 27-03, 27-04, 27-05 | Submitting a non-empty query from the header navigates to «База знаний» and runs the search immediately — results without a second click, exactly one request per submit, empty submit never calls the search API | ✓ SATISFIED | Truths 1, 2, 5 plus the KNOW-05 Playwright block. All five plans declare `requirements: [KNOW-05]`. REQUIREMENTS.md maps KNOW-05 → Phase 27 only |

**Orphaned requirements:** none. REQUIREMENTS.md Phase 27 IDs = `{KNOW-05}`. Plan-declared IDs = `{KNOW-05}`. ING-09 belongs to Phase 28.

**Coverage:** 1/1 requirements satisfied

### Decision Coverage

All 10 trackable CONTEXT.md `<decisions>` entries are honored by shipped artifacts (`gsd-tools query check.decision-coverage-verify` → `honored: 10, total: 10, not_honored: []`). D-01…D-10 are visible in `KnowledgePage.jsx` / `SearchPill.jsx` and the KNOW-05 spec.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/knowledge.spec.js` | KNOW-05 | 29 KNOW-05 cases + 3 honesty cases | 0 (`rg test.skip\|it.skip\|test.todo` empty) | No | Behavioral (URL, rows, counter, copy, history, XSS DOM) | PASS |
| `tests/unit/test_knowledge_api_snapshot.js` | KNOW-05 / C-24 | 1 | 0 | No — expected hash is a Wave-0 measured literal, not captured from the SUT at runtime | Value (sha256) | PASS |
| `tests/unit/test_knowledge_search_single_call_site.js` | KNOW-05 / C-05 | 3 | 0 | No | Value (counts + path set equality) | PASS |

**Disabled tests on requirements:** 0
**Circular patterns detected:** 0
**Insufficient assertions:** 0 blockers. IN-01 (`waitForTimeout(1200)` idle pin) is a warning: a duplicate fire slower than 1.2 s would stay green. Does not fail KNOW-05 c2, which is also pinned at settle.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `web/src/pages/KnowledgePage.jsx` | 217–287 | `runSearch` applies every settled response; no generation / AbortController (WR-01) | ⚠️ Warning | Overlapping header submits can show a stale `q`. Sequential C-03 still holds |
| `web/src/components/SearchPill.jsx` | 35–37 | Empty submit `navigate('/knowledge')` without `replace` (WR-02) | ⚠️ Warning | From a query URL, Back can return the previous `?q` |
| `web/src/pages/KnowledgePage.jsx` | 161–163 | Overlong invalid branch does not clear `items`/`error` (WR-03) | ⚠️ Warning | Mounted RAG + overlong Enter can leave stale rows beside «Сократите запрос» |
| `web/src/pages/KnowledgePage.jsx` | 365–371 | `handleResetFilter` uses live field, no `writeQueryToUrl` (WR-04) | ℹ️ Info | Explicitly out of 27-05 must-haves |
| `web/src/pages/KnowledgePage.jsx` | 478 | Role chips `disabled={searching}` | ℹ️ Info | Stricter than E3 · loading «no disabled»; no spinner/`data-state`. Helps WR-01 for chips |
| `tests/knowledge.spec.js` | 217 | `waitForTimeout(1200)` idle pin (IN-01) | ℹ️ Info | Duplicate fire on a >1.2 s timer would not redden |

**Debt markers:** `rg TBD\|FIXME\|XXX` on phase files → none. No blocker.

**Prohibitions (judgment-tier, all held):**

- `knowledgeApi.js` never edited — digest + git clean
- `run-unit-js.cjs` not reconfigured — still a flat glob
- No `sessionStorage`/`localStorage`/`indexedDB`/cookies for the search cache
- No `maxlength` on either search input
- No HTML sinks; `submitId` only compared with `===`
- No new user-facing string on the effect invalid path (`validation.message`)
- X-2 observer is harness-only

### Human Verification Required

### 1. Overflow wrap (backstop)

**Test:** At 320, 390 and 1280, submit a long query and inspect hint chips, hit titles/snippets, the zero-hit card, the live region, and `kb-search-error`.
**Expected:** Copy wraps in the existing layout. No new truncation or inner scroll on those surfaces.
**Why human:** PLAN truths tagged `verification: backstop`. Grep cannot see wrap.

### 2. C-12 paging resume

**Test:** Against a live/large catalogue (`has_more` true), search, click «Показать ещё», open a hit, Back, then «Показать ещё» again.
**Expected:** Restored snapshot includes the appended page; next fetch continues from `nextOffset`; restore Δ=0.
**Why human:** Mock catalogue never sets `has_more`. Listed in 27-VALIDATION.md Manual-Only Verifications.

### 3. INVALID_ROLE filter toast

**Test:** Produce `INVALID_ROLE` on a chip change.
**Expected:** `kb-filter-toast` «Фильтр недоступен» ~4 s; search error stays on the page panel, not the header.
**Why human:** Mock never returns that code; the branch is unexercised.

Do **not** re-walk the header-Enter happy path by hand — it is already pinned by Playwright (`header submit renders results from ?q` and siblings).

### Gaps Summary

No blocking gaps. Phase goal «One Enter from the header produces results» holds in code and in the KNOW-05 spec. KNOW-05 is satisfied. Remaining items are human/visual (overflow), mock-structural (C-12 resume, INVALID_ROLE toast), and review warnings that do not falsify ROADMAP success criteria.

Secure-phase has not run (`27-SECURITY.md` absent) — out of verify-work scope.

---

_Verified: 2026-10-22T12:22:00Z_
_Verifier: Claude (gsd-verifier)_
