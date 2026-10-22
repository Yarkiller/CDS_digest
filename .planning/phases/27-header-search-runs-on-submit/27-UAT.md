---
status: testing
phase: 27-header-search-runs-on-submit
source: [27-VERIFICATION.md]
started: 2026-10-22T15:10:00+03:00
updated: 2026-10-22T15:10:00+03:00
---

## Current Test

number: 1
name: Overflow wrap (backstop)
expected: |
  At 320, 390 and 1280, after submitting a long query, hint chips, hit titles/snippets, the zero-hit card, the live region, and kb-search-error wrap inside the existing layout. No new truncation or inner scroll on those surfaces.
awaiting: user response

## Tests

### 1. Overflow wrap (backstop)
expected: Copy wraps in the existing flex-wrap / grid-cols-[4rem_minmax(0,1fr)] / p-8 / panel layout. No new truncate, line-clamp, or scroll container on these surfaces.
result: [pending]

### 2. C-12 paging resume
expected: On a live catalogue where has_more is true, search, click «Показать ещё», open a hit, Back, then «Показать ещё» again. Restored snapshot includes the appended page; next fetch continues from nextOffset; restore itself issues 0 requests.
result: [pending]

### 3. INVALID_ROLE filter toast
expected: Trigger INVALID_ROLE on a role-chip change. kb-filter-toast «Фильтр недоступен» for ~4 s; search error stays on kb-search-error, not in the header.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
