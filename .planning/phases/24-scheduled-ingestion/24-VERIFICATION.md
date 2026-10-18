---
phase: 24-scheduled-ingestion
verified: 2026-10-18T17:43:03Z
status: human_needed
score: 15/15 must-haves verified
covered_files:
  - .planning/phases/24-scheduled-ingestion/24-01-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-01-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-02-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-02-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-03-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-03-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-04-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-04-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-05-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-05-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-06-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-06-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-07-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-07-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-08-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-08-SUMMARY.md
  - backend/src/backend/application/ports/ingestion_schedule.py
  - backend/src/backend/application/use_cases/ingestion_schedule.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/domain/errors.py
  - backend/src/backend/domain/ingestion_schedule.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/tests_support/in_memory.py
  - data-collection/src/data_collection/__init__.py
  - data-collection/src/data_collection/adapters/youtube_feed.py
  - data-collection/src/data_collection/dto/video_ref.py
  - data-collection/src/data_collection/errors/feed.py
  - data-collection/src/data_collection/ports/__init__.py
  - data-collection/src/data_collection/ports/video_list_provider.py
  - deploy/systemd/digest-ingest-alert.service
  - deploy/systemd/digest-ingest.service
  - deploy/systemd/digest-ingest.timer
  - docs/agents/local-platform-runbook.md
  - ingestion-service/.env.example
  - ingestion-service/pyproject.toml
  - ingestion-service/src/ingestion_service/adapters/supabase_collect_sources.py
  - ingestion-service/src/ingestion_service/adapters/utc_clock.py
  - ingestion-service/src/ingestion_service/application/ports/collect_sources.py
  - ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py
  - ingestion-service/src/ingestion_service/collect_cli.py
  - ingestion-service/src/ingestion_service/composition/clients.py
  - ingestion-service/src/ingestion_service/composition/settings.py
  - ingestion-service/src/ingestion_service/domain/schedule.py
  - ingestion-service/src/ingestion_service/tests_support/fakes.py
  - supabase-integration/migrations/013_phase24_scheduled_ingestion.sql
  - supabase-integration/src/supabase_integration/__init__.py
  - supabase-integration/src/supabase_integration/ingestion_schedule_repository.py
  - tests/admin.spec.js
  - tests/unit/test_collect_batch.py
  - tests/unit/test_collect_cli_contract.py
  - tests/unit/test_http_ingestion_schedule.py
  - tests/unit/test_ingestion_schedule_domain.py
  - tests/unit/test_phase24_migration_013.py
  - tests/unit/test_phase24_scheduler_guard.py
  - tests/unit/test_phase24_systemd_units.py
  - tests/unit/test_schedule_due.py
  - tests/unit/test_supabase_collect_sources_contract.py
  - tests/unit/test_supabase_ingestion_schedule_repository_contract.py
  - tests/unit/test_youtube_feed_adapter.py
  - web/src/components/IngestionScheduleSection.jsx
  - web/src/main.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - web/src/services/ingestScheduleApi.js
covered_digest: "v2:sha256:b2cc1f95cfce5f0b17021da52e510bcb5f9c44a0af071e5eb4b3840c64d75861"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 13/13
  gaps_closed:
    - "G-24-3: инертный runtime-лимит был нерабочим на Type=oneshot; граница перенесена на TimeoutStartSec=1800, инертный токен запрещён негативным text-гейтом"
    - "G-24-4: alert читал квалификатор exited/killed; теперь читает MONITOR_EXIT_STATUS (fallback EXIT_STATUS), exit 1/2 различаются"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Live systemd запуск: §4k установить юниты и `sudo systemctl enable --now digest-ingest.timer`; дождаться двух тиков"
    expected: "`systemctl list-timers digest-ingest.timer` показывает следующее срабатывание ≤15 мин; journald содержит две строки сводки (`sources: read=…` / `videos: …`) либо `not due: …`; юнит не уходит в failed"
    why_human: "Таймер и journald — поведение VM; unit-тесты читают файлы как текст и не запускают systemd"
  - test: "flock: во время активного прогона запустить второй `systemctl start digest-ingest.service`"
    expected: "Второй запуск завершается кодом 75, `systemctl status` не failed, `digest-ingest-alert.service` не поднимается"
    why_human: "Конкурентное поведение flock/SuccessExitStatus проверяется только на живой системе"
  - test: "TimeoutStartSec: имитировать зависший прогон дольше 1800 с (или временно уменьшить лимит — но только до значения, которое гарантированно убивает **до** `stamp_last_run`; живой прогон показал, что 2 с попадают в shutdown tail и `last_run_at` успевает обновиться, 500 мс — нет)"
    expected: "Прогон убит; `last_run_at` не обновлён, если kill пришёл до `stamp_last_run`; следующий тик снова `due` и продолжает с того же курсора"
    why_human: "Инвариант «убитый прогон не штампует last_run_at» требует реального SIGTERM от systemd и держится только когда kill опережает stamp"
  - test: "OnFailure alert: форсировать exit 1 и отдельно exit 2"
    expected: "journald alert различает «partial failure … (exit 1)» и «no source could be read … (exit 2)»; alert-юнит отрабатывает от `digestcds`, а не root"
    why_human: "`MONITOR_EXIT_STATUS`, OnFailure-цепочка и фактический `User=` не исполняются unit-тестами"
  - test: "Права EnvironmentFile на VM: `ls -l /etc/digest-cds/ingest.env`"
    expected: "Режим `0600`, владелец root; в git и в юнитах нет секретов"
    why_human: "FS-режим файла вне репозитория; text-contract проверяет только путь и отсутствие секретов"
  - test: "Живой прогон на реальном включённом источнике (YouTube Atom + Supabase) с последующей проверкой БД; отдельно — переход из нуля источников"
    expected: "Новые видео появляются как `materials.status='draft'` и строки шортлиста `pending`; публикаций/отправок нет; повторный запуск не вызывает captions/LLM и не двигает курсор. Отдельно: due-тик с нулём включённых источников не меняет `last_run_at`; после включения источника следующий тик собирает его видео (D-27)"
    why_human: "Внешние сервисы и реальные креденшелы; unit-тесты используют фейки"
  - test: "Проверить миграцию 013 на общей VM (Studio SQL / psql)"
    expected: "Колонки `last_seen_published_at`/`last_seen_video_id` есть; `ingestion_schedule` существует, RLS=t, политик 0, seed-строки нет"
    why_human: "DDL на shared VM нельзя доказать text-контрактом; в SUMMARY заявлен операторский apply"
  - test: "Визуальная проверка блока «Автоматический сбор» на `/admin/pipeline` (desktop и узкая ширина)"
    expected: "Блок читается, контролы не переполняют секцию, порядок «Источники → Сбор → YAML» визуально очевиден"
    why_human: "Playwright проверяет функциональный контракт и порядок по boundingBox, но не качество вёрстки"
---

# Phase 24: Scheduled ingestion Verification Report

**Phase Goal:** Scheduled ingestion — A systemd timer drives the existing `ingest` CLI against enabled sources, writing drafts + shortlist rows only.
**Verified:** 2026-10-18T17:43:03Z
**Status:** human_needed
**Re-verification:** Yes — `--gaps-only` после gap-closure планов 24-07 (G-24-3) и 24-08 (G-24-4)

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Прогон перечисляет **включённые** источники и тянет новые видео через key-free Atom `feeds/videos.xml` (`channel_id` для `kind=channel`, `playlist_id` для `kind=playlist`), затем прогоняет их через существующий `run_ingest_pipeline` с голым `video_id` | ✓ VERIFIED | `adapters/youtube_feed.py` (`_FEED_ENDPOINT`, `_PARAMS`, stream + 1 MiB cap); `collect_batch.py` → `run_ingest_pipeline(video.video_id, …)`; тесты `test_list_recent_channel_sends_channel_id_query`, `test_run_collect_batch_passes_bare_video_id_to_pipeline` |
| 2 | Записываются только черновики и pending-строки шортлиста — публикации/отправки нет | ✓ VERIFIED | persist идёт через RPC `persist_draft_and_enqueue` (`supabase_persist.py`); `007_phase9_persist_draft.sql:122` `status='draft'`, `:209` `'pending'`; ING-07 guard (`test_phase24_scheduler_guard.py`) — в импорт-графе и runtime нет корней `backend`/`publish`/`send` |
| 3 | Порт листинга асинхронный, получает инжектированный `httpx.AsyncClient`; адаптер не читает `os.environ` | ✓ VERIFIED | `ports/video_list_provider.py` (`async list_recent`); `YouTubeFeedAdapter(client)`; `test_adapter_does_not_read_environ` |
| 4 | Окно выбирается oldest→newest; лимит на источник отрезает хвост; `videos_skipped_limit` считает только отрезанные лимитом | ✓ VERIFIED | `domain/schedule.py:select_window`; `test_select_window_empty_cursor_limit_cuts_newest_tail`, `test_run_collect_batch_first_run_processes_oldest_five_in_asc_order`, `test_select_window_cursor_on_twelfth_limit_two_skips_one` |
| 5 | Курсор монотонен, equal-second tie-break по `video_id`; упавшее видео курсор не двигает; повторный прогон на голове фида не вызывает LLM | ✓ VERIFIED | `is_newer`/`advance_cursor`; `test_is_newer_same_second_tie_break_by_video_id`, `test_run_collect_batch_failed_video_does_not_advance_cursor`, `test_rescan_at_feed_head_makes_zero_llm_calls` |
| 6 | Упавшее видео не прерывает батч: следующее видео обрабатывается, `videos_failed+1`, ровно одна stderr-строка с `video_id` и причиной; сбой записи курсора изолирован (CR-01) | ✓ VERIFIED | `collect_batch.py:170-215` try/except вокруг pipeline **и** вокруг `advance_cursor`; при сбое курсора — `videos_failed += 1`, `cursor advance failed: …`, батч продолжается, exit 1; тесты `test_collect_cli_video_failure_exit_1_and_stderr_diagnostic`, `test_cursor_write_failure_is_isolated_and_batch_completes`, `test_run_collect_batch_failed_video_does_not_advance_cursor` |
| 7 | Нечитаемый источник не прерывает батч; отказ `list_enabled_sources` → exit 2 без обращений к фиду; отказ `get_schedule` → exit 2; отказ `stamp_last_run` → exit 1 с сохранением счётчиков. Неожиданные исключения фида тоже изолируются (WR-02) | ✓ VERIFIED | `collect_batch.py:91-148, 226-239`; `except (FeedError, CollectSourceError)` и отдельный `except Exception` → `sources_unreadable += 1`, диагностика `source unreadable (unexpected): …`, `continue`; тесты `test_unreadable_source_continues_to_next_source`, `test_unexpected_feed_exception_is_isolated_per_source`, `test_unexpected_feed_exception_only_source_exit_code_2`, `test_list_enabled_sources_failure_exit_2_no_feed_calls`, `test_get_schedule_failure_exit_2_no_feed_no_stamp`, `test_stamp_last_run_failure_keeps_counters_exit_1` |
| 8 | Due-гейт в `Europe/Moscow` — чистая функция с инъекцией `tzinfo`; причины `disabled\|day\|before_time\|already_ran\|ok`; catch-up после пропущенных дней; «не пора» — одна строка, exit 0, без фида/LLM. **D-27:** due-прогон с нулём **включённых** источников НЕ штампует `last_run_at`; прогон с ≥1 прочитанным источником штампует всегда, включая пустой фид | ✓ VERIFIED | `domain/schedule.py:35-59` (без `zoneinfo`/`datetime.now` — `test_schedule_module_has_no_zoneinfo_or_datetime_now`); `collect_cli.py:74-77`; `collect_batch.py:226-239` — `if enabled:` перед `stamp_last_run`; тесты `test_due_decision_catch_up_after_missed_days`, `test_not_due_skips_feed_and_returns_reason`, `test_due_empty_run_stamps_last_run_at`, `test_due_zero_enabled_sources_does_not_stamp_and_zeros` (проверяет `stamped == []` **и** что после нулевого тика источник всё ещё `due`) |
| 9 | systemd-юниты описывают unattended-путь: oneshot под `flock`, `RuntimeDirectory`, `TimeoutStartSec=1800`, `OnFailure=`, `SuccessExitStatus=0 75`, `EnvironmentFile=`, `TZ=UTC`, 15-минутный таймер `Persistent=false`, journald-alert читает числовой `MONITOR_EXIT_STATUS` и различает exit 1/2; alert-юнит не root (WR-04); секретов в юнитах нет | ✓ VERIFIED | `deploy/systemd/*`; `digest-ingest-alert.service:4-7` — `User=digestcds`, `Group=digestcds`, `NoNewPrivileges=true`, `PrivateTmp=true`; 15 text-проверок `test_phase24_systemd_units.py`, включая `test_alert_unit_runs_unprivileged`, `test_alert_unit_does_not_read_exit_qualifier`, `test_service_does_not_use_runtime_limit_on_oneshot`, `test_runbook_and_records_name_the_oneshot_start_limit` и `test_runbook_and_verification_name_numeric_status` |
| 10 | Миграция 013 идемпотентна: две `add column if not exists` на `pipeline_ingest_sources`, singleton `ingestion_schedule` (`check (id = 1)`), RLS enabled, ноль политик, нет seed/destructive, `ingestion_sources` не тронута | ✓ VERIFIED | `013_phase24_scheduled_ingestion.sql`; `test_phase24_migration_013.py` (5 тестов) |
| 11 | Backend `GET`/`PATCH /admin/ingestion-schedule`: admin-only, доменные дефолты при отсутствии строки, merge-patch только переданных полей, нормализация `HH:MM`/дней, 400 top-level `{errors:[…]}`, 422 `extra=forbid`, 503 при несмонтированном порте; пустой ответ upsert перечитывается (WR-06) | ✓ VERIFIED | `routes/admin.py:903-960`, `use_cases/ingestion_schedule.py`, `domain/ingestion_schedule.py`; `ingestion_schedule_repository.py:121-133` — при пустом `data` вызывается `_read_row()`, отсутствие строки → `PersistenceError`; тесты `test_update_empty_upsert_data_preserves_last_run_at_via_follow_up_read`, `test_update_empty_upsert_and_missing_row_raises_persistence_error`, `test_http_ingestion_schedule.py` (9 тестов) |
| 12 | SPA-блок «Автоматический сбор» стоит между источниками и YAML, сохраняет немедленно, отказывает пустой неделе, честно показывает ошибки save/load с retry, не входит в `dirty`, ходит только через `ingestScheduleApi.js`, harness доступен до первого рендера; очистка времени + blur восстанавливает сохранённое значение (WR-05) | ✓ VERIFIED | `IngestionScheduleSection.jsx:75-83`; `AdminPipelineConfigPage.jsx:145` (`dirty = yamlDirty || sourceFormDirty`); `main.jsx:96-102`; Playwright describe «Admin pipeline — automatic collection» — **8 passed** в предыдущем прогоне; `web/` не менялся после него (`git diff --name-only` по HEAD не содержит `web/`) |
| 13 | `ingest <url>` остаётся байт-идентичным; scheduled path физически не может дойти до publish/send (AST + runtime `sys.modules`) | ✓ VERIFIED | `cli.py` не менялся с Phase 15 (`55c5816`), `tests/unit/test_cli_ingest_contract.py` не менялся с Phase 11 (`0e68b4d`) и зелёный; `test_phase24_scheduler_guard.py` — AST/runtime + anti-vacuum + injection probe |
| 14 | **G-24-3 / D-23:** `digest-ingest.service` ограничивает start-фазу oneshot через `TimeoutStartSec=1800` и не содержит инертного runtime-параметра; убитый прогон не штампует `last_run_at`, **если kill пришёл до `stamp_last_run`**, и следующий тик снова due; инертный токен запрещён инвертированным text-гейтом | ✓ VERIFIED | `digest-ingest.service:17-18`; тесты `test_service_tokens`, `test_service_does_not_use_runtime_limit_on_oneshot`, `test_runbook_and_records_name_the_oneshot_start_limit`; живой WSL2/systemd 255: scratch `TimeoutStartSec=3`+`sleep 10` → `Result=timeout`/`ExecMainStatus=15` за 3115 ms, контроль с runtime-лимитом 3 с → 10011 ms `Result=success`; реальный прогон при `TimeoutStartSec=500ms` убит за 530 ms, `last_run_at` остался backdated, следующий старт штампнул. Оговорка: при 2 с kill попадает в shutdown tail и `last_run_at` успевает обновиться |
| 15 | **G-24-4 / D-12, D-20:** alert вычисляет числовой код из `MONITOR_EXIT_STATUS` (fallback `EXIT_STATUS`) и не читает квалификатор exited/killed; форсированные exit 1 и exit 2 дают две разные строки; alert остаётся journald-only, unprivileged, с `1)`/`2)`/`*)` arms, а `*)` печатает числовой код для killed-прогона | ✓ VERIFIED | `digest-ingest-alert.service:10` (`code="${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}"`, `*)` → `exit $code`); тесты `test_alert_unit`, `test_alert_unit_does_not_read_exit_qualifier`, `test_runbook_and_verification_name_numeric_status`; живой WSL2/systemd 255: exit 1 → «partial failure … (exit 1)», exit 2 → «no source could be read … (exit 2)», до фикса тот же exit 2 печатал «unexpected failure (exit exited)»; hardening `User/Group=digestcds`, `NoNewPrivileges=true`, `PrivateTmp=true` |

**Score:** 15/15 truths verified (0 present, behavior-unverified)

> Truth 8 проверена по **D-27**. Строки must_haves в `24-03-PLAN.md:44,46` (и `24-VALIDATION.md:240,269`) всё ещё содержат дословно прежнюю формулировку «`last_run_at` записан при нуле источников»; маркер **SUPERSEDED** стоит только в `24-CONTEXT.md:171`. Код и тест следуют D-27, поэтому truth не считается проваленной, но plan/VALIDATION стоит привести к текущему контракту, чтобы следующий verifier не прочитал устаревшую строку буквально.
>
> Пограничный случай D-27: если включённые источники есть, но **все нечитаемы** (`sources_read == 0`), код всё равно штампует `last_run_at` (условие — `if enabled:`), поскольку D-27 этот случай явно не регламентирует. Оба сформулированных правила D-27 соблюдены; поведение стоит подтвердить/уточнить в UAT.
>
> Truth 14: формулировка «убитый прогон не штампует» верна только когда kill опережает `stamp_last_run`. Живой прогон зафиксировал это исключение (2 с → `Result=timeout` **с** обновлённым `last_run_at`; 500 мс → без обновления). Операторское исправление в item 3 ниже и в runbook §4k/§5e сохраняет этот квалификатор; тест `test_runbook_and_records_name_the_oneshot_start_limit` пиннит его в §5e.

### Deferred Items

None — Phase 24 последняя в milestone; ни одна truth не отложена на более позднюю фазу.

### Advisory (New Scope, Unevidenced)

None — новых scope-находок вне review-находок не обнаружено.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `data-collection/src/data_collection/adapters/youtube_feed.py` | Atom + 1 MiB cap + DTD reject | ✓ VERIFIED | stream + `aiter_bytes`, local-name разбор, `_DTD_MARKERS`; не менялся в fix-раунде |
| `data-collection/src/data_collection/dto/video_ref.py` | `VideoRef`/`FeedSkip`/`FeedListing` | ✓ VERIFIED | frozen dataclasses |
| `data-collection/src/data_collection/ports/video_list_provider.py` | async `VideoListProvider` | ✓ VERIFIED | Protocol |
| `data-collection/src/data_collection/errors/feed.py` | `FeedError(source_id, reason)` | ✓ VERIFIED | импортируется адаптером и use-case |
| `ingestion-service/.../domain/schedule.py` | `is_newer`/`advance_cursor`/`select_window`/`due_decision` | ✓ VERIFIED | чистые функции, tz инъектируется |
| `ingestion-service/.../application/ports/collect_sources.py` | `EnabledSource` + `CollectSourceReader` (list/schedule/stamp/advance) | ✓ VERIFIED | Protocol |
| `ingestion-service/.../adapters/supabase_collect_sources.py` | Supabase reader + schedule upsert | ✓ VERIFIED | фильтр `is_enabled=True`, upsert `id=1` |
| `ingestion-service/.../application/use_cases/collect_batch.py` | `CollectDeps`/`CollectCounters`/`CollectOutcome`/`run_collect_batch` | ✓ VERIFIED | due-гейт, изоляция source/video/cursor, D-27 stamp-гейт |
| `ingestion-service/.../collect_cli.py` | `ingest-collect` entry point | ✓ VERIFIED | `[project.scripts]` + Typer app; `cli.py` не тронут |
| `ingestion-service/.../composition/settings.py` | `INGEST_TEMPLATE`, `INGEST_MAX_VIDEOS_PER_SOURCE` | ✓ VERIFIED | дефолт `lecture`, 5; `ConfigurationError` на невалид |
| `ingestion-service/pyproject.toml` | `ingest-collect` script | ✓ VERIFIED | за фазу только строка script; новых зависимостей нет |
| `supabase-integration/migrations/013_phase24_scheduled_ingestion.sql` | cursor columns + singleton + RLS | ✓ VERIFIED | idempotent, no seed/wipe, ноль политик |
| `backend/.../domain/ingestion_schedule.py` | value object + normalize/parse/format | ✓ VERIFIED | русские сообщения, bool отвергается |
| `backend/.../application/ports/ingestion_schedule.py` | Protocol `get/update` | ✓ VERIFIED | без SDK-импортов |
| `backend/.../application/use_cases/ingestion_schedule.py` | validate-then-persist merge-patch | ✓ VERIFIED | пустой PATCH → 400 |
| `backend/.../interface/http/routes/admin.py` | GET/PATCH routes | ✓ VERIFIED | `Depends(require_admin)`; 503 `_require_ingestion_schedule` |
| `supabase-integration/.../ingestion_schedule_repository.py` | Supabase adapter с re-read после пустого upsert | ✓ VERIFIED | `_read_row()`; missing row → `PersistenceError` (WR-06) |
| `backend/.../composition/container.py` / `live.py` | wiring `ingestion_schedule` | ✓ VERIFIED | live — `SupabaseIngestionScheduleRepository(admin_client)` |
| `deploy/systemd/digest-ingest.service` | oneshot + `TimeoutStartSec=1800`, no inert runtime knob, flock/exit-75 contract | ✓ VERIFIED | `Type=oneshot`, `TimeoutStartSec=1800`, `SuccessExitStatus=0 75`, `flock -n -E 75`, `RuntimeDirectory(Mode)`, `OnFailure=`, hardening |
| `deploy/systemd/digest-ingest.timer` | 15-min poll, `Persistent=false` | ✓ VERIFIED | `OnCalendar=*:0/15`, `Persistent=false`, `Unit=digest-ingest.service` |
| `deploy/systemd/digest-ingest-alert.service` | numeric exit status, unprivileged, journald-only | ✓ VERIFIED | `MONITOR_EXIT_STATUS` + `EXIT_STATUS` fallback; `User/Group=digestcds`; hardening; no curl/webhook |
| `tests/unit/test_phase24_systemd_units.py` | 15 text checks incl. four negative gates + three positive pins | ✓ VERIFIED | 15 passed; `_section` helper; whole-file record scans |
| `docs/agents/local-platform-runbook.md` | §4k run-limit + monitor-variable + drop-in hygiene; §5e items 5 and 8 recipes | ✓ VERIFIED | 500ms recipe, teardown `rm -f …override.conf`, qualified no-stamp claim, no inert runtime knob / qualifier in §5e |
| `web/src/services/ingestScheduleApi.js` | единственный SPA-транспорт + mock/arms | ✓ VERIFIED | fetch/patch, harness reset/arm |
| `web/src/components/IngestionScheduleSection.jsx` | блок «Автоматический сбор» | ✓ VERIFIED | testids, немедленный PATCH, восстановление времени (WR-05) |
| `web/src/pages/AdminPipelineConfigPage.jsx` | вставка между источниками и редактором | ✓ VERIFIED | `dirty` без schedule; `<IngestionScheduleSection>` после `<IngestSourcesSection />` |
| `web/src/main.jsx` | `__DIGEST_INGESTION_SCHEDULE_HARNESS__` | ✓ VERIFIED | 4 функции + `readIngestionScheduleMock` |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `collect_cli.py` | `collect_batch.py` | `build_collect_deps()` → `run_collect_batch(...)` | ✓ WIRED | импорт + вызов в `main()` |
| `collect_batch.py` | `ingest_pipeline.py` | `run_ingest_pipeline(video.video_id, template, on_stage=None, diagnostics=None)` | ✓ WIRED | запрет на `on_stage` соблюдён |
| `collect_batch.py` | `video_list_provider.py` | `deps.feed.list_recent(kind=…, source_id=…)` | ✓ WIRED | два уровня изоляции (known + unexpected) |
| `collect_batch.py` | `CollectSourceReader.advance_cursor` | try/except вокруг записи курсора | ✓ WIRED | CR-01: сбой не обрывает батч |
| `collect_batch.py` | `ingestion_schedule` stamp | `stamp_last_run` только при непустом `enabled` | ✓ WIRED | D-27 |
| `supabase_collect_sources.py` | `pipeline_ingest_sources` (013/012) | select + `.eq("is_enabled", True)` + cursor update | ✓ WIRED | `[`last_seen_published_at`,`last_seen_video_id`]` |
| `collect_cli.py` | `Europe/Moscow` | `ZoneInfo` только в composition | ✓ WIRED | `collect_cli.build_collect_deps`; domain без `zoneinfo` |
| `digest-ingest.timer` | `digest-ingest.service` | `Unit=digest-ingest.service` | ✓ WIRED | text-contract |
| `digest-ingest.service` | `collect_cli` entry | `ExecStart=…/bin/ingest-collect` | ✓ WIRED | absolute venv path |
| `digest-ingest.service` | `digest-ingest-alert.service` | `OnFailure=` + `MONITOR_EXIT_STATUS` numeric | ✓ WIRED | exit 1/2 live-proven; killed → `*)` with numeric code |
| `test_phase24_scheduler_guard.py` | `collect_cli` | AST scan + subprocess `sys.modules` | ✓ WIRED | `test_runtime_modules_are_clean` green |
| `routes/admin.py` | `use_cases/ingestion_schedule.py` | `get_ingestion_schedule` / `update_ingestion_schedule` | ✓ WIRED | |
| `composition/live.py` | `ingestion_schedule_repository.py` | `SupabaseIngestionScheduleRepository(admin_client)` | ✓ WIRED | service_role не покидает composition |
| `IngestionScheduleSection.jsx` | `ingestScheduleApi.js` | `patchIngestionSchedule` (через props страницы) | ✓ WIRED | компонент не строит URL |
| `AdminPipelineConfigPage.jsx` | `IngestionScheduleSection` | рендер после `<IngestSourcesSection />` | ✓ WIRED | Playwright boundingBox order passed |
| `tests/admin.spec.js` | `main.jsx` harness | `resetIngestionScheduleMock` ждёт `__DIGEST_INGESTION_SCHEDULE_HARNESS__` | ✓ WIRED | harness keys = 4 functions |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `collect_cli` summary | `CollectCounters` | `run_collect_batch` (feed + pipeline results) | Да — реальные счётчики, не константы | ✓ FLOWING |
| `collect_batch` cursor | `source.last_seen_*` / `advance_cursor` | `SupabaseCollectSourceReader.list_enabled_sources` (SQL) + update | Да | ✓ FLOWING |
| `IngestionScheduleSection` | `schedule` | `fetchIngestionSchedule` → backend GET → Supabase `ingestion_schedule` | Да (mock в dev, live URL в prod) | ✓ FLOWING |
| `SupabaseIngestionScheduleRepository.update` | `last_run_at`/`updated_at` | ответ upsert **или** повторный `_read_row()` | Да — больше не фабрикуется `None` (WR-06) | ✓ FLOWING |
| `AdminPipelineConfigPage` dirty | `yamlDirty`/`sourceFormDirty` | реальные состояния страницы | Да; schedule намеренно не входит | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase 24 systemd text contract (15 checks, includes the four negative gates and three positive pins) | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | **15 passed** in 0.08s | ✓ PASS |
| Полный unit-набор | `uv run pytest -q` | **1151 passed**, 1 pre-existing starlette DeprecationWarning, 15.21s | ✓ PASS |
| `ingest <url>` контракт не изменён | `git log -1 -- ingestion-service/src/ingestion_service/cli.py`; `git log -1 -- tests/unit/test_cli_ingest_contract.py` | `55c5816` / `0e68b4d` (Phase 15 / 11) | ✓ PASS |
| SPA-блок расписания (Playwright) | не перезапускался в этом раунде; `web/` отсутствует в `git diff --name-only 97e3b2d..HEAD` | предыдущий прогон — 9 passed; регрессии по diff нет | ? SKIP (no diff) |

### Probe Execution

N/A — фаза не объявляет probe-скрипты (`probe-*.sh`); проверка идёт unit/Playwright-тестами и runbook §5e (human UAT).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| ING-02 | 24-01, 24-02 | Scheduled run перечисляет новые видео по каждому **включённому** источнику и прогоняет их через существующий pipeline, только drafts + pending shortlist | ✓ SATISFIED | Atom adapter + `list_enabled_sources(is_enabled=True)` + `run_ingest_pipeline` + RPC `persist_draft_and_enqueue` (status `draft`, `pending`); truths 1-7 |
| ING-05 | 24-01, 24-02, 24-03 | Per-source high-water mark исключает повторную обработку; повторный прогон не переплачивает captions/LLM | ✓ SATISFIED | `last_seen_*` в 013; `select_window` до pipeline; `test_rescan_at_feed_head_makes_zero_llm_calls`; cursor monotonic tests |
| ING-06 | 24-02, 24-03, 24-04, 24-05, 24-06, 24-07, 24-08 | Unattended запуск из systemd timer с нужным окружением; исход каждого прогона виден; одно плохое видео не валит батч | ✓ SATISFIED (live-часть — human) | units + 15 text-checks; due-гейт + D-27 stamp + exit codes; source/video/cursor isolation; admin API/UI; G-24-3 `TimeoutStartSec=1800` + G-24-4 `MONITOR_EXIT_STATUS`, обе live-proven на WSL2. Остаются human items 1, 2, 5, 6, 7, 8 |
| ING-07 | 24-01, 24-04 | Scheduled path доказуемо не может дойти до publish/send; `ingest <url>` stdout байт-идентичен | ✓ SATISFIED | AST + runtime guard; unit publish/send scan; `cli.py`/`test_cli_ingest_contract.py` без изменений и зелёные |

Orphaned requirements: нет — `REQUIREMENTS.md` мапит на Phase 24 ровно ING-02/05/06/07 (строки 118-121), все четыре покрыты планами; ни одного ID, ожидаемого для Phase 24, но не заявленного в `requirements:` планов, нет.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts (`check decision-coverage-verify`: total 27, honored 27, not_honored `[]`). Non-blocking warning-only gate — no decision vanished during execution. D-19/D-23 keep explicit SUPERSEDED (mechanism token only) markers for the `TimeoutStartSec=1800` substitution.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/unit/test_phase24_systemd_units.py` | ING-06 | 15 | 0 | no | Value (token presence + negative absence) + live-proven behaviour | PASS |
| `tests/unit/test_phase24_scheduler_guard.py` | ING-06, ING-07 | 5 | 0 | no | Behavioral (AST graph + runtime `sys.modules`) | PASS |
| `tests/unit/test_phase24_migration_013.py` | ING-02, ING-05 | 5 | 0 | no | Behavioral (DDL text contract) | PASS |
| `tests/unit/test_collect_batch.py` | ING-02, ING-05, ING-06 | active | 0 | no | Behavioral (counters, cursor, exit codes) | PASS |
| `tests/admin.spec.js` (automatic-collection describe) | ING-06 | 8 | 0 | no | Behavioral (Playwright, prior run; `web/` unchanged) | PASS |

**Disabled tests on requirements:** 0. **Circular patterns detected:** 0. **Insufficient assertions:** 0 — the systemd gates pin exact tokens and their absence, are mutation-proved in `24-REVIEW.md`, and the runtime half is backed by the live WSL2 probes.

### Anti-Patterns Found

Debt-маркеров (`TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`) в изменённых файлах фазы нет. Остались только принятые/отложенные review-находки.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `ingestion-service/.../collect_batch.py` | 170-215 | Упавшее видео не блокирует курсор: более новое успешное видео двигает high-water mark мимо failed-видео (**WR-01**, D-09 upheld) | ⚠️ Warning (accepted) | Молчаливая потеря компенсируется stderr-строкой, счётчиком `failed` и ручным `ingest <video_id>` (D-13). Реверс D-09 явно отклонён оператором 2026-10-18 |
| `data-collection/.../youtube_feed.py` | 65-67 | `missing_video_id` смешивает отсутствие и невалидный id (**IN-01**) | ℹ️ Info | Диагностика менее точная; на must-have не влияет |
| `ingestion-service/.../collect_cli.py` | 60-67 | Двойной `Settings.from_env()` в CLI (**IN-02**) | ℹ️ Info | Дублирование композиции без изменения поведения |
| `tests/unit/test_phase24_scheduler_guard.py` | 25-49 | AST-скан не ловит динамические импорты (**IN-03**) | ℹ️ Info | Документированное ограничение; runtime-проверка `sys.modules` покрывает живой граф модулей |
| `deploy/systemd/digest-ingest.service` | 18 | Комментарий `last_run_at is NOT stamped` не содержит shutdown-tail квалификатора; текст §4k/§5e и verification item 3 его содержат | ℹ️ Info | Функциональный контракт не страдает; квалификатор не запиннен в самом юните (drift-гейт проверяет §4k/§5e) |
| `docs/agents/local-platform-runbook.md` | 606 | Квалификатор «when the kill lands before `stamp_last_run`» в §4k не запиннен тестом (пиннится только §5e, IN-03 review) | ℹ️ Info | §4k-половина исправления IN-03 может регрессировать без red-теста |

Блокирующих anti-patterns нет. CR-01, WR-02, WR-03, WR-04, WR-05, WR-06 закрыты и из таблицы удалены; G-24-3/G-24-4 закрыты планами 24-07/24-08.

### Human Verification Required

Статус на 2026-10-18: пункты **3** и **4** пройдены на живой WSL2-системе (operator-reported, см. «Live evidence» ниже); пункты **1, 2, 5, 6, 7, 8** остаются открытыми. Список ниже сохранён как контракт для повторного провижининга хоста.

### 1. Live systemd timer

**Test:** Установить юниты по §4k, заполнить `/etc/digest-cds/ingest.env`, `systemctl enable --now digest-ingest.timer`, дождаться двух тиков.
**Expected:** `list-timers` показывает следующий запуск ≤15 мин; journald содержит две строки сводки или `not due: …`; юнит не в failed.
**Why human:** systemd/journald — поведение VM, unit-тесты читают файлы как текст.

### 2. flock и конкурентный запуск

**Test:** Во время активного прогона запустить второй `systemctl start digest-ingest.service`.
**Expected:** Второй запуск exit 75, `systemctl status` не failed, alert-юнит не поднимается.
**Why human:** Конкурентность/flock проверяется только на живой системе.

### 3. TimeoutStartSec и last_run_at

**Test:** Дождаться/сымитировать прогон дольше 1800 с.
**Expected:** Прогон убит, `last_run_at` не обновлён — **если kill пришёл до `stamp_last_run`** — следующий тик снова due и продолжает с того же курсора. Уменьшать лимит для проверки можно только до значения, которое гарантированно убивает раньше stamp: живой прогон на WSL2 показал, что 2 с попадают в shutdown tail (`Result=timeout` **с** обновлённым `last_run_at`), а 500 мс убивают за 530 мс до stamp.
**Why human:** Требует реального SIGTERM от systemd и проверки БД.

### 4. OnFailure alert (exit 1 vs exit 2)

**Test:** Форсировать exit 1 и отдельно exit 2, посмотреть `journalctl -u digest-ingest-alert.service`.
**Expected:** Разные сообщения «partial failure … (exit 1)» и «no source could be read … (exit 2)»; alert отрабатывает от `digestcds`.
**Why human:** `MONITOR_EXIT_STATUS`, OnFailure-цепочка и фактический `User=` unit-тестами не исполняются.

### 5. EnvironmentFile 0600

**Test:** `ls -l /etc/digest-cds/ingest.env` на VM.
**Expected:** `0600`, владелец root; секретов в git/юнитах нет.
**Why human:** FS-режим вне репозитория (runbook §4k явно отмечает, что text-тест его не покрывает).

### 6. Живой прогон на реальном источнике + переход из нуля источников

**Test:** Дать таймеру/ручному `ingest-collect` прогнать включённый канал; проверить БД; затем повторный запуск. Отдельно: оставить ноль включённых источников на due-тике, проверить `last_run_at`, затем включить источник и дождаться следующего тика.
**Expected:** Новые материалы — `status='draft'`, строки шортлиста — `pending`; публикаций/отправок нет; повторный запуск не вызывает captions/LLM и не двигает курсор. При нуле источников `last_run_at` не меняется; после включения источника следующий тик собирает его видео (D-27).
**Why human:** Внешние сервисы (YouTube, DeepSeek, Supabase) и реальные креденшелы; unit-тесты используют фейки.

### 7. Миграция 013 на shared VM

**Test:** Выполнить verify-SQL из `013_phase24_scheduled_ingestion.sql` (§4j).
**Expected:** cursor-колонки есть; `ingestion_schedule` существует; RLS=t; 0 политик; seed-строки нет.
**Why human:** DDL на shared VM не доказывается text-контрактом; в SUMMARY заявлен операторский apply 2026-10-18.

### 8. Визуальная проверка блока

**Test:** Открыть `/admin/pipeline` на desktop и узкой ширине.
**Expected:** Блок «Автоматический сбор» читается, контролы не переполняют секцию, порядок «Источники → Сбор → YAML» очевиден.
**Why human:** Playwright проверяет функцию и порядок по `boundingBox`, но не качество вёрстки.

#### Live evidence уже снято (operator-reported, 2026-10-18, не переоткрывается)

| Пункт | Наблюдение | Вердикт |
| ----- | ---------- | ------- |
| 3 | `Type=oneshot TimeoutStartUSec=30min` + `RuntimeMaxUSec=infinity`; scratch `TimeoutStartSec=3`+`sleep 10` → `Result=timeout`/`ExecMainStatus=15` за 3115 ms; контроль с runtime-лимитом 3 с → `Result=success` за 10011 ms; реальный прогон при `TimeoutStartSec=500ms` убит за 530 ms, `last_run_at` остался backdated, следующий старт штампнул; при 2 с stamp успел пройти | PASS (с квалификатором) |
| 4 | exit 1 → «partial failure … (exit 1)»; exit 2 → «no source could be read … (exit 2)»; до фикса тот же exit 2 → «unexpected failure (exit exited)»; `User/Group=digestcds`, `NoNewPrivileges=true`, `PrivateTmp=true` | PASS |
| Cleanup | runtime drop-in удалён, реальный `ExecStart=/usr/bin/flock -n -E 75 …` восстановлен, таймер `active` | PASS |

### Gaps Summary

Блокирующих gaps нет: 15/15 must-have truths подтверждены кодом и зелёными тестами (**15 focused + 1151 pytest**), требования ING-02/05/06/07 покрыты, orphaned requirements отсутствуют, debt-маркеров нет.

Gap-closure раунд закрыл оба UAT-gap'а:

- **G-24-3** — инертный runtime-лимит заменён на `TimeoutStartSec=1800`; инвертированный text-гейт (`test_service_does_not_use_runtime_limit_on_oneshot`) запрещает возврат токена; runbook §4k/§5e, SECURITY T-24-32 и VERIFICATION row 9 называют рабочий механизм; live-проба доказала kill (3115 ms / 10011 ms контроль) и отсутствие штампа при 500 мс.
- **G-24-4** — alert читает `MONITOR_EXIT_STATUS` (fallback `EXIT_STATUS`); `test_alert_unit_does_not_read_exit_qualifier` запрещает квалификатор; §5e item 8, SECURITY T-24-34 и VERIFICATION row 9 называют числовую переменную; live-проба дала две разные строки для exit 1/2 и подтвердила hardening.

Остаются только human-пункты 1, 2, 5, 6, 7, 8 (см. выше). Пункты 3 и 4 пройдены живой пробой и сохранены в чек-листе для будущего провижининга.

Не-блокирующие наблюдения для гигиены артефактов: (а) комментарий в `digest-ingest.service:18` утверждает «`last_run_at` is NOT stamped» без shutdown-tail квалификатора — функционально верно для нормального kill-пути, но литерально шире проверенного; (б) квалификатор в §4k не запиннен тестом (пиннится только §5e); (в) прежняя формулировка must-have всё ещё дословно лежит в `24-03-PLAN.md:44,46` и `24-VALIDATION.md:240,269`, маркер SUPERSEDED — только в `24-CONTEXT.md:171`. Код следует D-27.

Финальное подтверждение phase goal — UAT на VM (§5e) по открытым пунктам выше.

---

_Verified: 2026-10-18T17:43:03Z_
_Verifier: Claude (gsd-verifier)_
