---
status: testing
phase: 22-admin-nav-grouping
source: [22-VERIFICATION.md]
started: 2026-10-17T11:30:00Z
updated: 2026-10-17T11:30:00Z
---

## Current Test

number: 1
name: Вкладки раздела на одной строке (1280px и ~640px)
expected: |
  На /admin/digest и /admin/pipeline обе вкладки «Дайджест» / «Пайплайн» остаются на одной
  строке; горизонтального скролла страницы нет; активная вкладка подчёркнута accent-линией,
  неактивная — тише.
awaiting: user response

## Tests

### 1. Вкладки раздела на одной строке (1280px и ~640px)
expected: На /admin/digest и /admin/pipeline обе вкладки «Дайджест» / «Пайплайн» остаются на одной строке; горизонтального скролла страницы нет; активная вкладка подчёркнута accent-линией, неактивная — тише.
result: [pending]

### 2. Select «Разделы админки» ниже sm
expected: Окно уже 640px — native select «Разделы админки» полностью помещается в колонке контента без горизонтального переполнения; смена опции переводит на соответствующий URL.
result: [pending]

### 3. Единственная пилюля «Админ» при переносе шапки
expected: На узкой ширине, доведя шапку AppShell до переноса строк, пилюля «Админ» остаётся видимой, а переключатель разделов читается как in-page underline-хром, а не как второй ряд пилюль.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
