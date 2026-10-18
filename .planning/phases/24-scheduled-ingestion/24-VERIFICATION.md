---
phase: 24-scheduled-ingestion
verified: 2026-10-18T13:26:16Z
status: human_needed
score: 13/13 must-haves verified
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
covered_digest: "v2:sha256:6a2a360854951429ff7a6f6d897ff3fc4efa97ad6622b849d4ac28b26339762f"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Live systemd запуск: §4k установить юниты и `sudo systemctl enable --now digest-ingest.timer`; дождаться двух тиков"
    expected: "`systemctl list-timers digest-ingest.timer` показывает следующее срабатывание ≤15 мин; journald содержит две строки сводки (`sources: read=…` / `videos: …`) либо `not due: …`; юнит не уходит в failed"
    why_human: "Таймер и journald — поведение VM; unit-тесты читают файлы как текст и не запускают systemd"
  - test: "flock: во время активного прогона запустить второй `systemctl start digest-ingest.service`"
    expected: "Второй запуск завершается кодом 75, `systemctl status` не failed, `digest-ingest-alert.service` не поднимается"
    why_human: "Конкурентное поведение flock/SuccessExitStatus проверяется только на живой системе"
  - test: "RuntimeMaxSec: имитировать зависший прогон дольше 1800 с (или временно уменьшить лимит)"
    expected: "Прогон убит; `last_run_at` не обновлён; следующий тик снова `due` и продолжает с того же курсора"
    why_human: "Инвариант «убитый прогон не штампует last_run_at» требует реального SIGTERM от systemd"
  - test: "OnFailure alert: форсировать exit 1 и отдельно exit 2"
    expected: "journald alert различает «partial failure … (exit 1)» и «no source could be read … (exit 2)»"
    why_human: "`MONITOR_EXIT_CODE` и OnFailure-цепочка не исполняются unit-тестами"
  - test: "Права EnvironmentFile на VM: `ls -l /etc/digest-cds/ingest.env`"
    expected: "Режим `0600`, владелец root; в git и в юнитах нет секретов"
    why_human: "FS-режим файла вне репозитория; text-contract проверяет только путь и отсутствие секретов"
  - test: "Живой прогон на реальном включённом источнике (YouTube Atom + Supabase) с последующей проверкой БД"
    expected: "Новые видео появляются как `materials.status='draft'` и строки шортлиста `pending`; публикаций/отправок нет; повторный запуск не вызывает captions/LLM и не двигает курсор"
    why_human: "Внешние сервисы и реальные креденшелы; unit-тесты используют фейки"
  - test: "Проверить миграцию 013 на общей VM (Studio SQL / psql)"
    expected: "Колонки `last_seen_published_at`/`last_seen_video_id` есть; `ingestion_schedule` существует, RLS=t, политик 0, seed-строки нет"
    why_human: "DDL на shared VM нельзя доказать text-контрактом; в SUMMARY заявлен операторский apply"
  - test: "Визуальная проверка блока «Автоматический сбор» на `/admin/pipeline` (desktop и узкая ширина)"
    expected: "Блок читается, контролы не переполняют секцию, порядок «Источники → Сбор → YAML» визуально очевиден"
    why_human: "Playwright проверяет функциональный контракт и порядок по boundingBox, но не качество вёрстки"
---

# Phase 24: Scheduled ingestion Verification Report

**Phase Goal:** New videos are collected on a schedule without a human running the CLI — drafts and pending shortlist rows only, never publishing or sending.
**Verified:** 2026-10-18T13:26:16Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Прогон перечисляет **включённые** источники и тянет новые видео через key-free Atom `feeds/videos.xml` (`channel_id` для `kind=channel`, `playlist_id` для `kind=playlist`), затем прогоняет их через существующий `run_ingest_pipeline` с голым `video_id` | ✓ VERIFIED | `adapters/youtube_feed.py` (`_FEED_ENDPOINT`, `_PARAMS`, stream + 1 MiB cap); `collect_batch.py` → `run_ingest_pipeline(video.video_id, …)`; `url.py` accepts bare id; тесты `test_list_recent_channel_sends_channel_id_query`, `test_run_collect_batch_passes_bare_video_id_to_pipeline` |
| 2 | Записываются только черновики и pending-строки шортлиста — публикации/отправки нет | ✓ VERIFIED | persist идёт через RPC `persist_draft_and_enqueue` (`supabase_persist.py`); `007_phase9_persist_draft.sql:122` `status='draft'`, `:209` `'pending'`; ING-07 guard (`test_phase24_scheduler_guard.py`) — в импорт-графе и runtime нет корней `backend`/`publish`/`send` |
| 3 | Порт листинга асинхронный, получает инжектированный `httpx.AsyncClient`; адаптер не читает `os.environ` | ✓ VERIFIED | `ports/video_list_provider.py` (`async list_recent`); `YouTubeFeedAdapter(client)`; `test_adapter_does_not_read_environ` |
| 4 | Окно выбирается oldest→newest; лимит на источник отрезает хвост; `videos_skipped_limit` считает только отрезанные лимитом | ✓ VERIFIED | `domain/schedule.py:select_window`; `test_select_window_empty_cursor_limit_cuts_newest_tail`, `test_run_collect_batch_first_run_processes_oldest_five_in_asc_order`, `test_select_window_cursor_on_twelfth_limit_two_skips_one` |
| 5 | Курсор монотонен, equal-second tie-break по `video_id`; упавшее видео курсор не двигает; повторный прогон на голове фида не вызывает LLM | ✓ VERIFIED | `is_newer`/`advance_cursor`; `test_is_newer_same_second_tie_break_by_video_id`, `test_run_collect_batch_failed_video_does_not_advance_cursor`, `test_rescan_at_feed_head_makes_zero_llm_calls` |
| 6 | Упавшее видео не прерывает батч: следующее видео обрабатывается, `videos_failed+1`, ровно одна stderr-строка с `video_id` и причиной | ✓ VERIFIED | `collect_batch.py:162-181` try/except вокруг pipeline; `test_collect_cli_video_failure_exit_1_and_stderr_diagnostic`, `test_run_collect_batch_failed_video_does_not_advance_cursor` |
| 7 | Нечитаемый источник не прерывает батч; отказ `list_enabled_sources` → exit 2 без обращений к фиду; отказ `get_schedule` → exit 2; отказ `stamp_last_run` → exit 1 с сохранением счётчиков | ✓ VERIFIED | `collect_batch.py:91-125, 212-219`; тесты `test_unreadable_source_continues_to_next_source`, `test_list_enabled_sources_failure_exit_2_no_feed_calls`, `test_get_schedule_failure_exit_2_no_feed_no_stamp`, `test_stamp_last_run_failure_keeps_counters_exit_1` |
| 8 | Due-гейт в `Europe/Moscow` — чистая функция с инъекцией `tzinfo`; причины `disabled|day|before_time|already_ran|ok`; catch-up после пропущенных дней; «не пора» — одна строка, exit 0, без фида/LLM; `last_run_at` штампуется после любого due-прогона, включая пустой и с нулём источников | ✓ VERIFIED | `domain/schedule.py:due_decision` (без `zoneinfo`/`datetime.now` — `test_schedule_module_has_no_zoneinfo_or_datetime_now`); `collect_cli.py:74-77`; `test_due_decision_catch_up_after_missed_days`, `test_not_due_skips_feed_and_returns_reason`, `test_due_empty_run_stamps_last_run_at`, `test_due_zero_enabled_sources_stamps_and_zeros` |
| 9 | systemd-юниты описывают unattended-путь: oneshot под `flock`, `RuntimeDirectory`, `RuntimeMaxSec=1800`, `OnFailure=`, `SuccessExitStatus=0 75`, `EnvironmentFile=`, `TZ=UTC`, 15-минутный таймер `Persistent=false`, journald-alert с различением exit 1/2; секретов в юнитах нет | ✓ VERIFIED | `deploy/systemd/*`; 10 text-проверок `test_phase24_systemd_units.py` (включая анти-secret и анти-publish сканы, §4k↔`.env.example`) |
| 10 | Миграция 013 идемпотентна: две `add column if not exists` на `pipeline_ingest_sources`, singleton `ingestion_schedule` (`check (id = 1)`), RLS enabled, ноль политик, нет seed/destructive, `ingestion_sources` не тронута | ✓ VERIFIED | `013_phase24_scheduled_ingestion.sql`; `test_phase24_migration_013.py` (5 тестов) |
| 11 | Backend `GET`/`PATCH /admin/ingestion-schedule`: admin-only, доменные дефолты при отсутствии строки, merge-patch только переданных полей, нормализация `HH:MM`/дней, 400 top-level `{errors:[…]}`, 422 `extra=forbid`, 503 при несмонтированном порте | ✓ VERIFIED | `routes/admin.py:903-960`, `use_cases/ingestion_schedule.py`, `domain/ingestion_schedule.py`; `test_http_ingestion_schedule.py` (9 тестов) |
| 12 | SPA-блок «Автоматический сбор» стоит между источниками и YAML, сохраняет немедленно (toggle / blur времени / дни), отказывает пустой неделе, честно показывает ошибки save/load с retry, не входит в `dirty`, ходит только через `ingestScheduleApi.js`, harness доступен до первого рендера | ✓ VERIFIED | `IngestionScheduleSection.jsx`, `AdminPipelineConfigPage.jsx:280-288` (`dirty = yamlDirty || sourceFormDirty`), `main.jsx:96-102`; Playwright describe «Admin pipeline — automatic collection» — **7 passed** |
| 13 | `ingest <url>` остаётся байт-идентичным; scheduled path физически не может дойти до publish/send (AST + runtime `sys.modules`) | ✓ VERIFIED | `cli.py` не менялся с Phase 15, `tests/unit/test_cli_ingest_contract.py` не менялся с Phase 11 и зелёный; `test_phase24_scheduler_guard.py` — AST/runtime + anti-vacuum + injection probe |

**Score:** 13/13 truths verified (0 present, behavior-unverified)

### Deferred Items

None — Phase 24 последняя в milestone; ни одна truth не отложена на более позднюю фазу.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `data-collection/src/data_collection/adapters/youtube_feed.py` | Atom + 1 MiB cap + DTD reject | ✓ VERIFIED | 130 строк; stream + `aiter_bytes`, local-name разбор |
| `data-collection/src/data_collection/dto/video_ref.py` | `VideoRef`/`FeedSkip`/`FeedListing` | ✓ VERIFIED | frozen dataclasses |
| `data-collection/src/data_collection/ports/video_list_provider.py` | async `VideoListProvider` | ✓ VERIFIED | Protocol |
| `data-collection/src/data_collection/errors/feed.py` | `FeedError(source_id, reason)` | ✓ VERIFIED | импортируется адаптером и use-case |
| `ingestion-service/.../domain/schedule.py` | `is_newer`/`advance_cursor`/`select_window`/`due_decision` | ✓ VERIFIED | чистые функции, tz инъектируется |
| `ingestion-service/.../application/ports/collect_sources.py` | `EnabledSource` + `CollectSourceReader` (list/schedule/stamp/advance) | ✓ VERIFIED | Protocol |
| `ingestion-service/.../adapters/supabase_collect_sources.py` | Supabase reader + schedule upsert | ✓ VERIFIED | фильтр `is_enabled=True`, upsert `id=1` |
| `ingestion-service/.../application/use_cases/collect_batch.py` | `CollectDeps`/`CollectCounters`/`CollectOutcome`/`run_collect_batch` | ✓ VERIFIED | due-гейт, изоляция, exit codes |
| `ingestion-service/.../collect_cli.py` | `ingest-collect` entry point | ✓ VERIFIED | `[project.scripts]` + Typer app; `cli.py` не тронут |
| `ingestion-service/.../composition/settings.py` | `INGEST_TEMPLATE`, `INGEST_MAX_VIDEOS_PER_SOURCE` | ✓ VERIFIED | дефолт `lecture`, 5; `ConfigurationError` на невалид |
| `ingestion-service/pyproject.toml` | `ingest-collect` script | ✓ VERIFIED | diff за фазу: только `+ ingest-collect = …`, новых зависимостей нет |
| `supabase-integration/migrations/013_phase24_scheduled_ingestion.sql` | cursor columns + singleton + RLS | ✓ VERIFIED | idempotent, no seed/wipe |
| `backend/.../domain/ingestion_schedule.py` | value object + normalize/parse/format | ✓ VERIFIED | русские сообщения, bool отвергается |
| `backend/.../application/ports/ingestion_schedule.py` | Protocol `get/update` | ✓ VERIFIED | без SDK-импортов |
| `backend/.../application/use_cases/ingestion_schedule.py` | validate-then-persist merge-patch | ✓ VERIFIED | пустой PATCH → 400 |
| `backend/.../interface/http/routes/admin.py` | GET/PATCH routes | ✓ VERIFIED | `Depends(require_admin)`; 503 `_require_ingestion_schedule` |
| `supabase-integration/.../ingestion_schedule_repository.py` | Supabase adapter | ✓ VERIFIED | defaults без записи; upsert `on_conflict=id` |
| `backend/.../composition/container.py` / `live.py` | wiring `ingestion_schedule` | ✓ VERIFIED | live — `SupabaseIngestionScheduleRepository(admin_client)` |
| `deploy/systemd/digest-ingest.service` / `.timer` / `-alert.service` | oneshot + 15-min timer + journald alert | ✓ VERIFIED | см. truth 9 |
| `web/src/services/ingestScheduleApi.js` | единственный SPA-транспорт + mock/arms | ✓ VERIFIED | fetch/patch, harness reset/arm |
| `web/src/components/IngestionScheduleSection.jsx` | блок «Автоматический сбор» | ✓ VERIFIED | testids, немедленный PATCH, no Save |
| `web/src/pages/AdminPipelineConfigPage.jsx` | вставка между источниками и редактором | ✓ VERIFIED | строки 280-288; `dirty` без schedule |
| `web/src/main.jsx` | `__DIGEST_INGESTION_SCHEDULE_HARNESS__` | ✓ VERIFIED | 4 функции + `readIngestionScheduleMock` |
| `docs/agents/local-platform-runbook.md` | §4j apply 013, §4k install, §5e UAT | ✓ VERIFIED | §4k/§5e найдены и покрыты cross-check тестом |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `collect_cli.py` | `collect_batch.py` | `build_collect_deps()` → `run_collect_batch(...)` | ✓ WIRED | импорт + вызов в `main()` |
| `collect_batch.py` | `ingest_pipeline.py` | `run_ingest_pipeline(video.video_id, template, on_stage=None, diagnostics=None)` | ✓ WIRED | запрет на `on_stage` соблюдён |
| `collect_batch.py` | `video_list_provider.py` | `deps.feed.list_recent(kind=…, source_id=…)` | ✓ WIRED | |
| `supabase_collect_sources.py` | `pipeline_ingest_sources` (013/012) | select + `.eq("is_enabled", True)` + cursor update | ✓ WIRED | `[`last_seen_published_at`,`last_seen_video_id`]` |
| `collect_cli.py` | `Europe/Moscow` | `ZoneInfo` только в composition | ✓ WIRED | `collect_cli.build_collect_deps`; domain без `zoneinfo` |
| `digest-ingest.timer` | `digest-ingest.service` | `Unit=digest-ingest.service` | ✓ WIRED | text-contract |
| `digest-ingest.service` | `collect_cli` entry | `ExecStart=…/bin/ingest-collect` | ✓ WIRED | absolute venv path |
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
| `AdminPipelineConfigPage` dirty | `yamlDirty`/`sourceFormDirty` | реальные состояния страницы | Да; schedule намеренно не входит | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Unit-контракты фазы (Atom, cursor/due, batch, CLI, migration, systemd, guard, backend schedule) | `uv run pytest tests/unit/test_youtube_feed_adapter.py tests/unit/test_schedule_due.py tests/unit/test_collect_batch.py tests/unit/test_collect_cli_contract.py tests/unit/test_supabase_collect_sources_contract.py tests/unit/test_phase24_migration_013.py tests/unit/test_phase24_systemd_units.py tests/unit/test_phase24_scheduler_guard.py tests/unit/test_ingestion_schedule_domain.py tests/unit/test_http_ingestion_schedule.py tests/unit/test_supabase_ingestion_schedule_repository_contract.py tests/unit/test_cli_ingest_contract.py tests/unit/test_data_collection_public_api.py tests/unit/test_ingestion_settings.py tests/unit/test_ingestion_env_example.py -q` | `207 passed` | ✓ PASS |
| SPA-блок расписания (7 сценариев) | `npx playwright test tests/admin.spec.js --project=web --grep "automatic collection"` | `7 passed (25.0s)` | ✓ PASS |
| PRESERVE: нет элементов запуска на `/admin/pipeline` | `npx playwright test tests/admin.spec.js --project=web --grep "pipeline config no execution controls render"` | `1 passed (4.4s)` | ✓ PASS |
| ING-07 guard (AST + runtime) | входит в pytest-прогон выше | green | ✓ PASS |
| Zero new runtime deps | `git diff --stat 874ea23..HEAD -- '*pyproject.toml' 'uv.lock'` | `ingestion-service/pyproject.toml \| 1 +` (только `ingest-collect` script) | ✓ PASS |
| `ingest <url>` контракт не изменён | `git log --oneline -5 -- ingestion-service/src/ingestion_service/cli.py tests/unit/test_cli_ingest_contract.py` | последние коммиты — Phase 15/11; в Phase 24 изменений нет | ✓ PASS |

### Probe Execution

N/A — фаза не объявляет probe-скрипты (`probe-*.sh`), проверка идёт unit/Playwright-тестами и runbook §5e (human UAT).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| ING-02 | 24-01, 24-02 | Scheduled run перечисляет новые видео по каждому **включённому** источнику и прогоняет их через существующий pipeline, только drafts + pending shortlist | ✓ SATISFIED | Atom adapter + `list_enabled_sources(is_enabled=True)` + `run_ingest_pipeline` + RPC `persist_draft_and_enqueue` (status `draft`, `pending`); truth 1-6 |
| ING-05 | 24-01, 24-02, 24-03 | Per-source high-water mark исключает повторную обработку; повторный прогон не переплачивает captions/LLM | ✓ SATISFIED | `last_seen_*` в 013; `select_window` до pipeline; `test_rescan_at_feed_head_makes_zero_llm_calls`; cursor monotonic tests |
| ING-06 | 24-02, 24-03, 24-04, 24-05, 24-06 | Unattended запуск из systemd timer с нужным окружением; исход каждого прогона виден; одно плохое видео не валит батч | ✓ SATISFIED (live-часть — human) | units + 10 text-checks; due-гейт + `last_run_at` + exit codes; source/video isolation; admin API/UI. Live systemd/VM — human_verification #1-5 |
| ING-07 | 24-01, 24-04 | Scheduled path доказуемо не может дойти до publish/send; `ingest <url>` stdout байт-идентичен | ✓ SATISFIED | AST + runtime guard; unit publish/send scan; `cli.py`/`test_cli_ingest_contract.py` без изменений и зелёные |

Orphaned requirements: нет — `REQUIREMENTS.md` мапит на Phase 24 ровно ING-02/05/06/07 (строки 118-121), все покрыты планами.

### Anti-Patterns Found

Debt-маркеров (`TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`) в файлах фазы нет.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `ingestion-service/.../collect_batch.py` | 187-195 | `deps.sources.advance_cursor(...)` вне `try` (CR-01 из `24-REVIEW.md`) | ⚠️ Warning | SDK-сбой записи курсора после успешного ingest пробрасывается наверх: traceback, батч обрывается, `stamp_last_run` не пишется. Не нарушает must-have (падает не «видео», а запись состояния), но exit-контракт деградирует — рекомендуется follow-up |
| `ingestion-service/.../collect_batch.py` | 127-137 | Ловятся только `FeedError`/`CollectSourceError` (WR-02) | ⚠️ Warning | Неожиданное исключение из `list_recent` обрывает батч без graded exit |
| `deploy/systemd/digest-ingest-alert.service` | 4-6 | Нет `User=`/`Group=` (WR-04) | ℹ️ Info | Alert-юнит бежит от root; сейчас только `echo` в journald — сузить поверхность |
| `web/src/components/IngestionScheduleSection.jsx` | 75-78 | Очистка `timeDraft` + blur оставляет пустой input (WR-05) | ℹ️ Info | Рассинхрон UI/сервера до перезагрузки; на must-have не влияет |
| `supabase-integration/.../ingestion_schedule_repository.py` | 118-127 | Fallback без `last_run_at` (WR-06) | ℹ️ Info | После PATCH с пустым `data` UI может показать «никогда не запускалось» |
| `data-collection/.../youtube_feed.py` | 65-67 | `missing_video_id` смешивает отсутствие и невалидный id (IN-01) | ℹ️ Info | Диагностика менее точная |

Блокирующих anti-patterns нет.

### Human Verification Required

### 1. Live systemd timer

**Test:** Установить юниты по §4k, заполнить `/etc/digest-cds/ingest.env`, `systemctl enable --now digest-ingest.timer`, дождаться двух тиков.
**Expected:** `list-timers` показывает следующий запуск ≤15 мин; journald содержит две строки сводки или `not due: …`; юнит не в failed.
**Why human:** systemd/journald — поведение VM, unit-тесты читают файлы как текст.

### 2. flock и конкурентный запуск

**Test:** Во время активного прогона запустить второй `systemctl start digest-ingest.service`.
**Expected:** Второй запуск exit 75, `systemctl status` не failed, alert-юнит не поднимается.
**Why human:** Конкурентность/flock проверяется только на живой системе.

### 3. RuntimeMaxSec и last_run_at

**Test:** Дождаться/сымитировать прогон дольше 1800 с.
**Expected:** Прогон убит, `last_run_at` не обновлён, следующий тик снова due и продолжает с того же курсора.
**Why human:** Требует реального SIGTERM от systemd и проверки БД.

### 4. OnFailure alert (exit 1 vs exit 2)

**Test:** Форсировать exit 1 и отдельно exit 2, посмотреть `journalctl -u digest-ingest-alert.service`.
**Expected:** Разные сообщения «partial failure … (exit 1)» и «no source could be read … (exit 2)».
**Why human:** `MONITOR_EXIT_CODE` и OnFailure-цепочка unit-тестами не исполняются.

### 5. EnvironmentFile 0600

**Test:** `ls -l /etc/digest-cds/ingest.env` на VM.
**Expected:** `0600`, владелец root; секретов в git/юнитах нет.
**Why human:** FS-режим вне репозитория (runbook §4k явно отмечает, что text-тест его не покрывает).

### 6. Живой прогон на реальном источнике

**Test:** Дать таймеру/ручному `ingest-collect` прогнать включённый канал; проверить БД; затем повторный запуск.
**Expected:** Новые материалы — `status='draft'`, строки шортлиста — `pending`; публикаций/отправок нет; повторный запуск не вызывает captions/LLM и не двигает курсор.
**Why human:** Внешние сервисы (YouTube, DeepSeek, Supabase) и реальные креденшелы.

### 7. Миграция 013 на shared VM

**Test:** Выполнить verify-SQL из `013_phase24_scheduled_ingestion.sql` (§4j).
**Expected:** cursor-колонки есть; `ingestion_schedule` существует; RLS=t; 0 политик; seed-строки нет.
**Why human:** DDL на shared VM не доказывается text-контрактом; в SUMMARY заявлен операторский apply 2026-10-18.

### 8. Визуальная проверка блока

**Test:** Открыть `/admin/pipeline` на desktop и узкой ширине.
**Expected:** Блок «Автоматический сбор» читается, контролы не переполняют секцию, порядок «Источники → Сбор → YAML» очевиден.
**Why human:** Playwright проверяет функцию и порядок по `boundingBox`, но не качество вёрстки.

### Gaps Summary

Блокирующих gaps нет: все 13 must-have truths подтверждены кодом и зелёными тестами (207 pytest + 8 Playwright), требования ING-02/05/06/07 покрыты, orphaned requirements отсутствуют, debt-маркеров нет.

Остаётся открытый **Critical** из `24-REVIEW.md` (CR-01: запись курсора не изолирована) и четыре warning/info-наблюдения. Они не фальсифицируют ни одну must-have truth (падает запись состояния, а не «плохое видео»), но перед production-эксплуатацией их стоит закрыть отдельным follow-up. Phase goal достижим в коде; финальное подтверждение — UAT на VM (§5e) по списку выше.

---

_Verified: 2026-10-18T13:26:16Z_
_Verifier: Claude (gsd-verifier)_
