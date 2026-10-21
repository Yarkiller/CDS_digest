---
status: testing
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
source: [25-VERIFICATION.md]
started: 2026-10-21T23:13:52+03:00
updated: 2026-10-21T23:13:52+03:00
---

## Current Test

number: 1
name: 25-02 backstop — 320px / строка вкладок: /admin/pipeline, «Дайджест» и «Настройка»
expected: |
  Обе подписи в одну строку внутри 44px (min-h-11) без обрезки; на < 640px строка скрыта (nav hidden … sm:flex) — работает <select>
awaiting: user response

## Tests

### 1. 25-02 backstop — 320px / строка вкладок: /admin/pipeline, «Дайджест» и «Настройка»
expected: Обе подписи в одну строку внутри 44px (min-h-11) без обрезки; на < 640px строка скрыта (nav hidden … sm:flex) — работает <select>
result: [pending]

### 2. 25-02 backstop — 320px: мобильный <select> раздела
expected: Высота 44px, непрозрачная paper, текст ink, выбранная опция не обрезана
result: [pending]

### 3. 25-03 backstop — частично заполненная форма (тип выбран, id и название пусты)
expected: Все три контрола — непрозрачная paper, текст ink-2 в обеих темах
result: [pending]

### 4. 25-03 backstop — 200-символьный id в ingest-sources-id
expected: Прокручивается внутри поля, не расширяет paper, не обрезает CTA «Добавить источник»
result: [pending]

### 5. 25-03 backstop — первичная загрузка в полёте
expected: Строк и скелетона нет, заголовок «Источники» и paper остаются отрисованными
result: [pending]

### 6. 25-03 backstop — строка только с id (без названия)
expected: Переключатель и все действия строки видимы и читаемы
result: [pending]

### 7. 25-03 backstop — 20 строк на 320px
expected: Страница удлиняется, ни одна строка не обрезана, горизонтальной прокрутки нет
result: [pending]

### 8. 25-03 backstop — 0 / 1 / 20 строк
expected: Одна и та же paper-2 на строку и ритм 8px; singular/plural не вводится
result: [pending]

### 9. 25-03 backstop — длинный id канала/плейлиста в строке
expected: Переносится/усекается внутри строки, действия во вьюпорте, текст ≥ 4.5:1
result: [pending]

### 10. 25-03 backstop — 320px: диалог несохранённых изменений
expected: Тело переносится, «Остаться» и «Уйти без сохранения» полностью видимы, без горизонтального переполнения
result: [pending]

### 11. 25-04 backstop — 320px: самая длинная подпись CTA «Уйти без сохранения»
expected: Переносится внутри 44px-цели без обрезки
result: [pending]

### 12. 25-04 backstop — 320px: подпись активной навигационной пилюли
expected: Полностью внутри пилюли, #FFFFFF на primary-solid, без обрезки
result: [pending]

## Summary

total: 12
passed: 0
issues: 0
pending: 12
skipped: 0
blocked: 0

## Gaps
