---
status: testing
phase: 24-scheduled-ingestion
source: [24-VERIFICATION.md]
started: 2026-10-18T13:30:00.000Z
updated: 2026-10-18T13:30:00.000Z
---

## Current Test

number: 1
name: Live systemd timer
expected: |
  `systemctl list-timers digest-ingest.timer` показывает следующее срабатывание ≤15 мин;
  journald содержит две строки сводки (`sources: read=…` / `videos: …`) либо `not due: …`;
  юнит не уходит в failed.
awaiting: user response

## Tests

### 1. Live systemd timer

Установить юниты по §4k, заполнить `/etc/digest-cds/ingest.env`,
`sudo systemctl enable --now digest-ingest.timer`, дождаться двух тиков.

expected: `systemctl list-timers digest-ingest.timer` показывает следующее срабатывание ≤15 мин; journald содержит две строки сводки либо `not due: …`; юнит не в failed.
result: [pending]

### 2. flock и конкурентный запуск

Во время активного прогона запустить второй `systemctl start digest-ingest.service`.

expected: Второй запуск завершается кодом 75, `systemctl status` не failed, `digest-ingest-alert.service` не поднимается.
result: [pending]

### 3. RuntimeMaxSec и last_run_at

Дождаться/сымитировать прогон дольше 1800 с (или временно уменьшить лимит).

expected: Прогон убит; `last_run_at` не обновлён; следующий тик снова `due` и продолжает с того же курсора.
result: [pending]

### 4. OnFailure alert (exit 1 vs exit 2)

Форсировать exit 1 и отдельно exit 2, затем `journalctl -u digest-ingest-alert.service`.

expected: Разные сообщения «partial failure … (exit 1)» и «no source could be read … (exit 2)».
result: [pending]

### 5. EnvironmentFile 0600

`ls -l /etc/digest-cds/ingest.env` на VM.

expected: Режим `0600`, владелец root; секретов в git и в юнитах нет.
result: [pending]

### 6. Живой прогон на реальном включённом источнике

YouTube Atom + Supabase, затем проверить БД.

expected: Новые видео появляются как `materials.status='draft'` и строки шортлиста `pending`; публикаций/отправок нет; повторный запуск не вызывает captions/LLM и не двигает курсор.
result: [pending]

### 7. Проверка миграции 013 на общей VM

Studio SQL / psql: колонки курсора, `ingestion_schedule`, RLS, seed.

expected: Колонки `last_seen_published_at`/`last_seen_video_id` есть; `ingestion_schedule` существует, RLS=true, политик 0, seed-строки нет.

note: Оператор подтвердил apply 2026-10-18; PostgREST-проба `select * from public.ingestion_schedule limit 5` → `[]`. Осталось подтвердить колонки и RLS/политики.
result: [pending]

### 8. Визуальная проверка блока «Автоматический сбор»

`/admin/pipeline`, desktop и узкая ширина.

expected: Блок читается, контролы не переполняют секцию, порядок «Источники → Сбор → YAML» визуально очевиден.
result: [pending]

## Summary

total: 8
passed: 0
issues: 0
pending: 8
skipped: 0
blocked: 0

## Gaps
