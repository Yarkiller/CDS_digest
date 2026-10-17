---
status: complete
phase: 22-admin-nav-grouping
source: [22-VERIFICATION.md, 22-03-PLAN.md]
started: 2026-10-17T11:30:00Z
updated: 2026-10-17T14:55:00Z
retired_by: 22-03 (automated Playwright geometry assertions)
---

## Current Test

None — all three backstop probes were converted to deterministic Playwright assertions by plan 22-03 and now pass in CI. No human verification remains.

## Tests

### 1. Вкладки раздела на одной строке (1280px и ~640px)
expected: На /admin/digest и /admin/pipeline обе вкладки «Дайджест» / «Пайплайн» остаются на одной строке; горизонтального скролла страницы нет; активная вкладка подчёркнута accent-линией, неактивная — тише.
result: passed — automated (GAP-BACKSTOP-1, `tests/admin.spec.js` in the `Admin nav grouping` describe). Asserts equal viewport-relative tops (|Δy| ≤ 1px) on both routes at 1280 and at the exact 640px `sm` edge, digest ending before pipeline begins, and no horizontal overflow on both `documentElement` and `main`; a 639px negative control in the same test proves the probe is breakpoint-sensitive.

### 2. Select «Разделы админки» ниже sm
expected: Окно уже 640px — native select «Разделы админки» полностью помещается в колонке контента без горизонтального переполнения; смена опции переводит на соответствующий URL.
result: passed — automated (GAP-BACKSTOP-2). At 480px and 400px the select box starts inside `main`, ends inside both `main` and the viewport, and is no wider than the column; the option→URL switch is covered by the existing 480px case.

### 3. Единственная пилюля «Админ» при переносе шапки
expected: На узкой ширине, доведя шапку AppShell до переноса строк, пилюля «Админ» остаётся видимой, а переключатель разделов читается как in-page underline-хром, а не как второй ряд пилюль.
result: passed — automated (GAP-BACKSTOP-3). At 480px the test measures the wrap (`navBox.height >` one pill height) instead of assuming it, then pins the single shell «Админ» link inside the viewport with the section nav hidden and the select visible.

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
