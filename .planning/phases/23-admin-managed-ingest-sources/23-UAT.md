---
status: testing
phase: 23-admin-managed-ingest-sources
source: [23-VERIFICATION.md]
started: 2026-10-17T20:55:00+03:00
updated: 2026-10-17T20:55:00+03:00
---

## Current Test

number: 1
name: ADUX-10 dirty OR на форме источников (id/label vs kind-only vs после успешного add)
expected: |
  Один UnsavedChangesDialog с Phase-19 копией «Есть несохранённые изменения. Уйти без сохранения?»;
  kind-only не промптит; успешный add разоружает при чистом YAML.
awaiting: user response

## Tests

### 1. ADUX-10 dirty OR на форме источников
expected: Один UnsavedChangesDialog с Phase-19 копией; kind-only не промптит; успешный add разоружает при чистом YAML
result: [pending]

### 2. Визуально: длинный список источников и YAML ниже на 1280px и узкой ширине
expected: Страница скроллится; редактор YAML остаётся достижимым
result: [pending]

### 3. Визуально: label 120 символов в строке источника
expected: Перенос/break-words без горизонтального overflow страницы
result: [pending]

### 4. Визуально: раскрытый блок «Где взять id?»
expected: Рецепты канала/плейлиста укладываются в ширину секции без горизонтального overflow
result: [pending]

### 5. Опционально ops: RLS/policies каталог для pipeline_ingest_sources
expected: relrowsecurity=true; count(pg_policies)=0; ingestion_sources не затронут
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps
