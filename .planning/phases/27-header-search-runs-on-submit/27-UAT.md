---
status: complete
phase: 27-header-search-runs-on-submit
source: [27-VERIFICATION.md]
started: 2026-10-22T15:10:00+03:00
updated: 2026-10-22T19:46:00+03:00
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Overflow wrap (backstop)
expected: Copy wraps in the existing flex-wrap / grid-cols-[4rem_minmax(0,1fr)] / p-8 / panel layout. No new truncate, line-clamp, or scroll container on these surfaces.
result: pass
source: automated
evidence: "Playwright MCP against dev server 127.0.0.1:5174 (VITE_USE_MOCKS=true), viewports 320/390/1280. States: long-query hits (7 rows), zero-hit, forced error panel (window.__DIGEST_FAIL_NEXT_KNOWLEDGE__), landing hint chips. At every width documentElement.scrollWidth == clientWidth; no element under main with text-overflow:ellipsis, -webkit-line-clamp != none, or overflow-x/y auto|scroll. Only the sr-only label and the single-line <input> report internal scrollWidth (native input behaviour). Rows use grid-cols-[4rem_minmax(0,1fr)] with minmax(0,1fr), chips use flex-wrap, zero-hit card is p-8 — all wrapped, live region read «Показано 7» / «Найдено 0 материалов»."
screenshots: [.playwright-mcp/uat27-320-hits.png, .playwright-mcp/uat27-1280-error.png]

### 2. C-12 paging resume
expected: On a live catalogue where has_more is true, search, click «Показать ещё», open a hit, Back, then «Показать ещё» again. Restored snapshot includes the appended page; next fetch continues from nextOffset; restore itself issues 0 requests.
result: pass
source: automated
evidence: "Closed by a test-only fixture, not by hand: `web/src/data/mock.js` now appends 21 `pagingFixtures` (unique `paging` token, `inIssue: false`, so the issue list, archive cards and voting counts are unchanged). New case `a paginated delivery is restored as one snapshot and resumes from nextOffset` (tests/knowledge.spec.js): `/knowledge?q=paging` → «Показано 10+» (10 rows, counter 1); «Показать ещё» → «Показано 20+» (20 rows, counter 2); open a hit that exists only on the appended page; Back → «Показано 20+», 20 rows, counter STILL 2 (restore issues 0 requests) and «Показать ещё» still visible; «Показать ещё» again → «Показано 21», 21 rows, counter 3, and the 21 hrefs are pairwise distinct (a restart at offset 0 would duplicate rows). Red first: the case failed with «Найдено 0 материалов» before the fixtures existed."
screenshots: []

### 3. INVALID_ROLE filter toast
expected: Trigger INVALID_ROLE on a role-chip change. kb-filter-toast «Фильтр недоступен» for ~4 s; search error stays on kb-search-error, not in the header.
result: skipped
reason: "Deferred follow-up: the mock adapter cannot produce INVALID_ROLE (the code exists only in the live HTTP 400 detail=invalid_role branch), and re-pinning the frozen `knowledgeApi.js` to fake it would trade a real gate for a simulated pass. Verify on the live stand during Phase 28 «Live proof — streamed DeepSeek ingest»."

## Summary

total: 3
passed: 2
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps

<!-- Blocked tests are environment gates, not code issues — intentionally not listed here. -->

## Deferred Follow-Ups

```yaml
- test: 3
  idea: "Trigger INVALID_ROLE on a role-chip change against the live API: kb-filter-toast «Фильтр недоступен» for ~4 s, and the search error stays on kb-search-error rather than in the header."
  deferred_at: 2026-10-22
  verify_in: "Phase 28 — Live proof — streamed DeepSeek ingest"
```

