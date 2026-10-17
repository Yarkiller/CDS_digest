---
status: complete
phase: 23-admin-managed-ingest-sources
source: [23-VERIFICATION.md]
started: 2026-10-17T20:55:00+03:00
updated: 2026-10-17T22:41:00+03:00
---

## Current Test

[testing complete]

## Tests

### 1. ADUX-10 dirty OR на форме источников
expected: Один UnsavedChangesDialog с Phase-19 копией; kind-only не промптит; успешный add разоружает при чистом YAML
result: pass

### 2. Визуально: длинный список источников и YAML ниже на 1280px и узкой ширине
expected: Страница скроллится; редактор YAML остаётся достижимым
result: pass

### 3. Визуально: label 120 символов в строке источника
expected: Перенос/break-words без горизонтального overflow страницы
result: pass

### 4. Визуально: раскрытый блок «Где взять id?»
expected: Рецепты канала/плейлиста укладываются в ширину секции без горизонтального overflow
result: pass

### 5. Опционально ops: RLS/policies каталог для pipeline_ingest_sources
expected: relrowsecurity=true; count(pg_policies)=0; ingestion_sources не затронут
result: pass

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

## Deferred Follow-Ups

- test: 1
  idea: "AdminLayout chrome: убрать надпись «АДМИН» над вкладками Дайджест|Пайплайн; уменьшить пустоту сверху; уменьшить кегль вкладок до уровня остальных заголовков (как «Источники ингеста»); чуть увеличить расстояние между вкладками Дайджест и Пайплайн"
  deferred_at: 2026-10-17
