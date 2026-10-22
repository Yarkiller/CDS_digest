---
status: partial
phase: 27-header-search-runs-on-submit
source: [27-VERIFICATION.md]
started: 2026-10-22T15:10:00+03:00
updated: 2026-10-22T15:38:00+03:00
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing paused — 2 blocked items outstanding]

## Tests

### 1. Overflow wrap (backstop)
expected: Copy wraps in the existing flex-wrap / grid-cols-[4rem_minmax(0,1fr)] / p-8 / panel layout. No new truncate, line-clamp, or scroll container on these surfaces.
result: pass
source: automated
evidence: "Playwright MCP against dev server 127.0.0.1:5174 (VITE_USE_MOCKS=true), viewports 320/390/1280. States: long-query hits (7 rows), zero-hit, forced error panel (window.__DIGEST_FAIL_NEXT_KNOWLEDGE__), landing hint chips. At every width documentElement.scrollWidth == clientWidth; no element under main with text-overflow:ellipsis, -webkit-line-clamp != none, or overflow-x/y auto|scroll. Only the sr-only label and the single-line <input> report internal scrollWidth (native input behaviour). Rows use grid-cols-[4rem_minmax(0,1fr)] with minmax(0,1fr), chips use flex-wrap, zero-hit card is p-8 — all wrapped, live region read «Показано 7» / «Найдено 0 материалов»."
screenshots: [.playwright-mcp/uat27-320-hits.png, .playwright-mcp/uat27-1280-error.png]

### 2. C-12 paging resume
expected: On a live catalogue where has_more is true, search, click «Показать ещё», open a hit, Back, then «Показать ещё» again. Restored snapshot includes the appended page; next fetch continues from nextOffset; restore itself issues 0 requests.
result: blocked
blocked_by: other
reason: "Mock harness cannot reach the state: web/src/data/mock.js has 8 materials and DEFAULT_SEARCH_LIMIT = 10, so has_more is never true and «Показать ещё» never renders. No live catalogue or running backend in this environment."

### 3. INVALID_ROLE filter toast
expected: Trigger INVALID_ROLE on a role-chip change. kb-filter-toast «Фильтр недоступен» for ~4 s; search error stays on kb-search-error, not in the header.
result: blocked
blocked_by: other
reason: "mockSearchKnowledge never returns INVALID_ROLE; the code is produced only by the live adapter on HTTP 400 detail=invalid_role. No live backend/authenticated session here."

## Summary

total: 3
passed: 1
issues: 0
pending: 0
skipped: 0
blocked: 2

## Gaps

<!-- Blocked tests are environment gates, not code issues — intentionally not listed here. -->
