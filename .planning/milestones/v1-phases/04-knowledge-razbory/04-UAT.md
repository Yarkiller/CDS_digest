---
status: complete
phase: 04-knowledge-razbory
source: [04-VERIFICATION.md]
started: 2026-09-21T09:50:00Z
updated: 2026-09-21T10:16:00Z
---

## Current Test

[testing complete]

## Tests

### 1. UI-SPEC overflow / long-text backstops
expected: No clipped CTAs; titles wrap; sticky/mobile TOC usable without horizontal overflow at 320/390/1280
result: pass

### 2. Visual honesty: snippets without scores; chronology pattern; dual notebook strip placement
expected: Matches design-frontend chronology + notebook strip canon; no score chrome on knowledge hits
result: issue
reported: "Если разбор темы ещё не готов (готовится) — кнопка «Читать разбор →» не должна быть показана. Это не логично. Показываем надпись — «Разбор этой темы ещё готовится — следите за обновлениями»."
severity: major

### 3. Optional live FE↔BE smoke (runbook §5b)
expected: Authenticated knowledge search + razbory consume work against live FastAPI/Supabase after 004 seed (mocks off)
result: pass

## Summary

total: 3
passed: 2
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-04-2
  truth: "Announcement / not-yet-ready razbory must not render a «Читать разбор →» CTA; instead show «Разбор этой темы ещё готовится — следите за обновлениями»"
  status: failed
  reason: "User reported: Если разбор темы ещё не готов (готовится) — кнопка «Читать разбор →» не должна быть показана. Это не логично. Показываем надпись — «Разбор этой темы ещё готовится — следите за обновлениями»."
  severity: major
  test: 2
  root_cause: "web/src/components/ChronologyItem.jsx renders the «Читать разбор →» <Link to=/razbory/{id}> unconditionally, ignoring item.status. Announcement (status === 'announcement') / not-yet-ready razbory therefore still expose a read CTA."
  artifacts:
    - web/src/components/ChronologyItem.jsx
    - tests/razbory.spec.js
  missing:
    - "Conditional in ChronologyItem: when status === 'announcement' (razbor not published/ready), suppress the «Читать разбор →» Link and render «Разбор этой темы ещё готовится — следите за обновлениями» instead."
