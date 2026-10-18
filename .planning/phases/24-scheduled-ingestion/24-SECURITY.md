---
phase: "24"
slug: "scheduled-ingestion"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-18"
---

# Phase 24 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Реестр собран из `<threat_model>` блоков шести планов (`24-01`…`24-06-PLAN.md`),
дополнен `## Threat Flags` из шести SUMMARY (все — «None beyond plan threat model»).
Глубина проверки: L1 (ASVS level 1, `block_on=high`) — статическая проверка
наличия контролов в реализации плюс ссылки на покрывающие тесты.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| YouTube Atom `feeds/videos.xml` → `YouTubeFeedAdapter` | Недоверенный внешний XML; парсинг и лимит объёма на границе адаптера | Публичный XML-фид (недоверенный) |
| `pipeline_ingest_sources` → `SupabaseCollectSourceReader` | Идентификаторы источников приходят только из БД, не из argv | `source_id`, `kind`, курсор |
| `collect_batch` → `run_ingest_pipeline` | Доменный seam; запись только через существующий `persist_draft_and_enqueue` | `video_id`, черновики, pending-строки шортлиста |
| `ingest-collect` → journald | stdout — сводка, stderr — `video_id` + причина; контент не печатается | Идентификаторы и коды причин |
| systemd → процесс `ingest-collect` | Непривилегированный прогон (`User=digestcds`) по таймеру | env-файл с секретами (вне git, 0600) |
| admin SPA → `PATCH /admin/ingestion-schedule` | Пользовательский ввод, влияющий на расписание | Расписание (enabled/time/days) |
| FastAPI `service_role` → Postgres | Только клиент из composition обходит RLS | Строка `ingestion_schedule`, курсоры |
| anon/authenticated PostgREST → `ingestion_schedule` | Прямого доступа нет: RLS deny-by-default, ноль политик | — |
| Оператор → общая VM | Применение DDL вручную, необратимый шаг | SQL-миграция 013 |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-24-01 | Information Disclosure | `parse_feed` / `ET.fromstring` | high | mitigate | DTD-скан `_DTD_MARKERS` на первых 4096 байтах → `feed_doctype`; 1 MiB cap до разбора (`youtube_feed.py:16,42-48,100-120`) | closed |
| T-24-02 | Denial of Service | `_read_capped` | high | mitigate | `content-length` проверяется до чтения; накопление по чанкам прерывается на 1 MiB → `feed_too_large` (`youtube_feed.py:100-120`); `test_youtube_feed_adapter.py` | closed |
| T-24-03 | Tampering | `source_id`/`kind` в листинге | medium | mitigate | Значения только из `pipeline_ingest_sources`; `kind` вне `{channel, playlist}` → `unsupported_kind` (`youtube_feed.py:86-88`) | closed |
| T-24-04 | Elevation of Privilege | `collect_cli` импорт `backend`/publisher | high | mitigate | `ingest-collect` живёт в `ingestion-service`; локальный `SupabaseCollectSourceReader` не тянет `backend.domain.*`; доказано `test_phase24_scheduler_guard.py` | closed |
| T-24-05 | Information Disclosure | секреты в `Settings`/выводе | medium | mitigate | Новые ключи не секретные; `repr=False` у `deepseek_api_key`/`supabase_secret_key` сохранён (`settings.py:87,91`); в stderr только `video_id` + причина | closed |
| T-24-06 | Denial of Service | `run_collect_batch` | high | mitigate | Лимит на источник (`INGEST_MAX_VIDEOS_PER_SOURCE`, дефолт 5) + per-video try/except, чтобы одно зависание не блокировало остальные (`collect_batch.py:170-210`) | closed |
| T-24-07 | Information Disclosure | stderr-диагностика | high | mitigate | Строки собираются из `video_id`/`source_id`, типа и причины; тесты `test_collect_cli_video_failure_exit_1_and_stderr_diagnostic` проверяют отсутствие текста транскрипта/статьи | closed |
| T-24-08 | Tampering | курсор | high | mitigate | `advance_cursor` монотонен; use-case передаёт адаптеру только результат слияния (`collect_batch.py:189-195`, `schedule.py:80-89`); тесты монотонности и tie-break | closed |
| T-24-09 | Repudiation | сводка прогона | medium | mitigate | Фиксированный формат двух строк + счётчик `failed`; каждый пропуск/сбой — строка в stderr (D-09) (`collect_cli.py:74-90`) | closed |
| T-24-10 | Elevation of Privilege | `public.ingestion_schedule` | high | mitigate | `enable row level security`, ноль политик (`013:30`); `test_phase24_migration_013.py:48-49` | closed |
| T-24-11 | Tampering | идемпотентность миграции | high | mitigate | `add column if not exists` + `create table if not exists`; text-тест запрещает `truncate`/`delete from`/`drop`/`alter table public.ingestion_sources` (`test_phase24_migration_013.py:57-66`) | closed |
| T-24-12 | Denial of Service | вечно-«пора» после пустого прогона | high | mitigate | `stamp_last_run` вызывается после гейта для любого прогона с ≥1 включённым источником, включая пустой фид (`collect_batch.py:226-239`); `test_due_empty_run_stamps_last_run_at`. Отклонение D-27: при нуле включённых источников штамп намеренно пропускается (см. примечание) | closed |
| T-24-13 | Spoofing | таймзона хоста | medium | mitigate | `due_decision` считает в инъектированной `Europe/Moscow`; naive `now_utc` → `ValueError` (`schedule.py:41-43`); `test_schedule_module_has_no_zoneinfo_or_datetime_now` | closed |
| T-24-14 | Repudiation | применение миграции | medium | mitigate | BLOCKING-гейт плана + строка `Applied (2026-10-18)` в runbook §4j (`local-platform-runbook.md:598`) + verify-SQL в файле миграции | closed |
| T-24-20 | Elevation of Privilege | `GET`/`PATCH /admin/ingestion-schedule` | high | mitigate | `Depends(require_admin)` на обоих методах (`routes/admin.py:914,940`); тесты 401/403 (`test_http_ingestion_schedule.py:123-146`) | closed |
| T-24-21 | Tampering | `days_of_week` / `time_of_day` | high | mitigate | Доменная валидация 1…7, непусто, `HH:MM` (`domain/ingestion_schedule.py`) до записи; `extra="forbid"` → 422 на неизвестные поля (`test_http_ingestion_schedule.py:225-234`) | closed |
| T-24-22 | Information Disclosure | `service_role`-клиент | high | mitigate | Клиент создаётся только в `composition`/`clients.py` и адаптере; в `backend/domain` и в домене/use-case `ingestion-service` импортов `supabase` нет (grep пуст) | closed |
| T-24-23 | Denial of Service | PATCH-флуд | medium | accept | Один admin, одна строка; rate limiting вне области ASVS L1 | closed |
| T-24-24 | Spoofing | отсутствие строки в БД | low | accept | Дефолты отдаются кодом; пустая таблица = рабочее состояние (D-14) | closed |
| T-24-30 | Information Disclosure | `deploy/systemd/*` | high | mitigate | `EnvironmentFile=/etc/digest-cds/ingest.env` вне репозитория; text-скан юнитов на секреты (`test_phase24_systemd_units.py`); 0600 — ручной шаг §4k | closed |
| T-24-31 | Elevation of Privilege | `ingest-collect` → publish/send | high | mitigate | AST-скан + рантайм `sys.modules` + anti-vacuum инъекционная проверка + отсутствие `run_ingest_pipeline` в `collect_cli` (`test_phase24_scheduler_guard.py:51-124`) | closed |
| T-24-32 | Denial of Service | зависший прогон держит лок | high | mitigate | `RuntimeMaxSec=1800` + `flock -n -E 75` + `SuccessExitStatus=0 75` (`digest-ingest.service:16-19`) | closed |
| T-24-33 | Tampering | одновременный двойной запуск | medium | mitigate | `flock -n` на `/run/digest-ingest/lock`; каталог создаёт `RuntimeDirectory=digest-ingest` (0750) под `User=digestcds` | closed |
| T-24-34 | Repudiation | «почему не пришло» | medium | mitigate | `OnFailure=digest-ingest-alert.service`; alert различает exit 1/2 через `MONITOR_EXIT_CODE`/`EXIT_CODE` и ссылается на `journalctl`; UAT §5e | closed |
| T-24-35 | Privilege Escalation | юнит под root | medium | mitigate | `User=digestcds`/`Group=digestcds` + `NoNewPrivileges=true` + `PrivateTmp=true` в обоих юнитах | closed |
| T-24-40 | Tampering | `IngestionScheduleSection` | high | mitigate | Состояние после сохранения берётся только из ответа сервера (`onScheduleChange(updated)`, `setTimeDraft(updated.time_of_day)`); локальная проверка дней дублирует серверную | closed |
| T-24-41 | Elevation of Privilege | UI-транспорт | high | mitigate | Все запросы через `ingestScheduleApi.js` с `getAccessToken()`; прямого `fetch` в UI нет; `require_admin` — последний рубеж | closed |
| T-24-42 | Information Disclosure | mock-harness | medium | mitigate | `sessionStorage` читается только внутри ветки `mocksEnabled()`; в live-режиме ветка недостижима | closed |
| T-24-43 | Spoofing | «Сохранено» без ответа | medium | mitigate | Без оптимистичного рендера: статус «Сохранено» ставится только после успешного `await patchIngestionSchedule(...)` | closed |
| T-24-44 | Denial of Service | спам PATCH с `onInput` | medium | mitigate | Время уходит только по `onBlur`; `onChange` — локальный state; `grep "onInput\|onKeyDown"` в компоненте пуст; тест `patchCount` | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

**Примечание к T-24-12.** Плановая формулировка — «`stamp_last_run` вызывается всегда после прохождения гейта». Реализация следует решению D-27: штамп выполняется после гейта для любого прогона с ≥1 включённым источником (включая пустой фид — `test_due_empty_run_stamps_last_run_at`), но пропускается, когда включённых источников ноль (`collect_batch.py:227-228`). Это устраняет обратный риск — «включил источник в тот же день и застрял до завтра». Для нуля источников тик остаётся «пора» и повторяется каждые 15 минут, но стоит один `SELECT` без обращений к фиду, captions и LLM. Отклонение задокументировано в `24-REVIEW-DISPOSITION.md` (WR-03) и `24-CONTEXT.md` (D-27); порог `high` не пробит.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-24-01 | T-24-23 | PATCH-флуд по расписанию: один admin, одна строка; rate limiting вне области ASVS L1 | plan owner (24-05-PLAN) | 2026-10-18 |
| AR-24-02 | T-24-24 | Пустая таблица `ingestion_schedule` — штатное состояние; дефолты отдаёт код (D-14) | plan owner (24-05-PLAN) | 2026-10-18 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-18 | 30 | 30 | 0 | /gsd-secure-phase 24 (Cursor agent, L1 / ASVS 1) |

**Метод:** реестр собран из `<threat_model>` шести PLAN-файлов (authored at plan
time) + `## Threat Flags` шести SUMMARY (все пусты сверх плана). Каждая
mitigate-угроза сверена с реализацией и покрывающим unit/text-тестом. Сканирование
новых угроз не выполнялось — реестр плановый (`register_authored_at_plan_time:
true`), глубина L1 достаточна при `asvs_level: 1`, поэтому аудитор-субагент по
short-circuit правилу не спавнился.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-18
