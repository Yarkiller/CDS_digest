---
phase: 24-scheduled-ingestion
reviewed: 2026-10-18T12:50:00Z
depth: standard
files_reviewed: 28
files_reviewed_list:
  - data-collection/src/data_collection/adapters/youtube_feed.py
  - data-collection/src/data_collection/dto/video_ref.py
  - data-collection/src/data_collection/errors/feed.py
  - data-collection/src/data_collection/ports/video_list_provider.py
  - ingestion-service/src/ingestion_service/domain/schedule.py
  - ingestion-service/src/ingestion_service/application/ports/collect_sources.py
  - ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py
  - ingestion-service/src/ingestion_service/adapters/supabase_collect_sources.py
  - ingestion-service/src/ingestion_service/adapters/utc_clock.py
  - ingestion-service/src/ingestion_service/collect_cli.py
  - ingestion-service/src/ingestion_service/composition/settings.py
  - ingestion-service/src/ingestion_service/composition/clients.py
  - supabase-integration/migrations/013_phase24_scheduled_ingestion.sql
  - deploy/systemd/digest-ingest.service
  - deploy/systemd/digest-ingest.timer
  - deploy/systemd/digest-ingest-alert.service
  - backend/src/backend/domain/ingestion_schedule.py
  - backend/src/backend/application/ports/ingestion_schedule.py
  - backend/src/backend/application/use_cases/ingestion_schedule.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/composition/live.py
  - supabase-integration/src/supabase_integration/ingestion_schedule_repository.py
  - web/src/services/ingestScheduleApi.js
  - web/src/components/IngestionScheduleSection.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - web/src/main.jsx
  - tests/unit/test_phase24_scheduler_guard.py
findings:
  critical: 1
  warning: 6
  info: 3
  total: 10
status: issues_found
---

# Phase 24: Code Review Report

**Reviewed:** 2026-10-18T12:50:00Z
**Depth:** standard
**Files Reviewed:** 28
**Status:** issues_found

## Summary

Проверен путь `ingest-collect` (Atom → cursor/due-gate → batch), systemd units, admin GET/PATCH schedule + UI, изоляция ING-07. Главный дефект: запись курсора после успешного ingest не изолирована — падение SDK роняет весь oneshot без graded exit. Дополнительно: курсор «перепрыгивает» failed-видео (закреплено D-09, но контент теряется), штамп при нуле источников блокирует same-day enable, alert-unit без `User=`, несколько UI/XML edge cases.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Падение `advance_cursor` роняет весь batch без graded exit

**File:** `ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py:187-195`
**Issue:** `run_ingest_pipeline` обёрнут в `try/except`, но последующие `advance_cursor` + `deps.sources.advance_cursor(...)` — нет. `CollectSourceError`/SDK-сбой после успешного ingest пробивает `run_collect_batch`, `collect_cli` ловит только `ConfigurationError`/`TemplateLoadError` → traceback, нет `stamp_last_run`, нет exit 0/1/2. Остальные видео окна не обрабатываются; systemd `OnFailure` видит «unexpected» код.
**Fix:**
```python
            try:
                result = await run_ingest_pipeline(...)
                next_cursor = advance_cursor(
                    current, (video.published, video.video_id)
                )
                deps.sources.advance_cursor(
                    source.id,
                    published=next_cursor[0],
                    video_id=next_cursor[1],
                )
            except Exception as err:
                videos_failed += 1
                deps.emit_diagnostic(
                    f"video failed: {video.video_id}: {type(err).__name__}: {err}"
                )
                continue
            # already_saved / ingested counters, then:
            current = next_cursor
```
Либо отдельный `except` вокруг записи курсора с `videos_failed += 1` и diagnostic `cursor advance failed`.

## Warnings

### WR-01: Курсор уходит вперёд мимо failed-видео — повторный ingest невозможен

**File:** `ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py:162-195`
**Issue:** Окно идёт oldest→newest. При fail на `v2` и success на `v3` курсор ставится на `v3` (закреплено тестом D-09). `v2` становится старше курсора и навсегда отфильтровывается `select_window`. Exit 1 есть, retry-пути нет (кроме ручного сброса курсора в БД).
**Fix:** Не продвигать курсор дальше первого разрыва: при `videos_failed` на источнике — `break` из цикла видео (watermark = последний непрерывный success). Обновить контракт `test_run_collect_batch_failed_video_does_not_advance_cursor` соответственно. Опционально: quarantine / отдельный retry-список.

### WR-02: Неожиданные ошибки feed не изолированы на уровне источника

**File:** `ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py:127-137`
**Issue:** Ловятся только `(FeedError, CollectSourceError)`. Любой другой exception из `list_recent` (баг адаптера, неожиданный httpx) валит весь batch так же, как CR-01 — без stamp и без graded exit 2.
**Fix:**
```python
        except Exception as err:
            sources_unreadable += 1
            deps.emit_diagnostic(
                f"source unreadable: {source.source_id}: "
                f"{type(err).__name__}: {err}"
            )
            continue
```

### WR-03: Stamp при нуле enabled-источников блокирует same-day сбор

**File:** `ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py:117-124` + `213-219`
**Issue:** Due-прогон с `enabled=[]` всё равно вызывает `stamp_last_run`. Админ включает источник позже в тот же день МСК → `due_decision` → `already_ran` до следующего календарного дня. Таймер 15 мин бесполезен.
**Fix:** Не штамповать, если `len(enabled) == 0` (или штамповать только при `sources_read + sources_unreadable > 0`). Зафиксировать тестом: zero sources → exit 0, `stamp` не вызывается, повторный тик снова due.

### WR-04: Alert-unit выполняется от root

**File:** `deploy/systemd/digest-ingest-alert.service:4-6`
**Issue:** У `digest-ingest.service` есть `User=digestcds`, у alert — нет. OnFailure oneshot с `/bin/sh -c` бежит от root. Сейчас только `echo` в journald, но поверхность шире необходимого.
**Fix:**
```ini
[Service]
Type=oneshot
User=digestcds
Group=digestcds
NoNewPrivileges=true
PrivateTmp=true
ExecStart=/bin/sh -c '...'
```

### WR-05: Очистка поля времени + blur оставляет пустой draft

**File:** `web/src/components/IngestionScheduleSection.jsx:75-78`
**Issue:** При пустом `timeDraft` `onTimeBlur` делает early-return без восстановления `schedule.time_of_day`. Инпут остаётся пустым, в БД старое значение — рассинхрон UI/сервера до следующего load.
**Fix:**
```javascript
    const next = String(timeDraft ?? '').trim()
    if (!next) {
      setTimeDraft(schedule.time_of_day)
      return
    }
    if (next === schedule.time_of_day) return
```

### WR-06: Fallback ответа PATCH обнуляет `last_run_at` в DTO

**File:** `supabase-integration/src/supabase_integration/ingestion_schedule_repository.py:118-127`
**Issue:** Если upsert вернул пустой `data`, синтетический `IngestionSchedule` ставит `last_run_at=None`, хотя в БД штамп мог остаться. API/UI покажут «никогда не запускалось» после успешного PATCH.
**Fix:** При пустом `rows` делать follow-up `get()`, либо всегда запрашивать `Prefer: return=representation` и fail → `PersistenceError`, если строки нет.

## Info

### IN-01: `missing_video_id` смешивает отсутствие и невалидный id

**File:** `data-collection/src/data_collection/adapters/youtube_feed.py:65-67`
**Issue:** И отсутствующий, и не matching `^[A-Za-z0-9_-]{11}$` id логируются как `missing_video_id` — усложняет диагностику.
**Fix:** Разделить причины: `missing_video_id` / `invalid_video_id`.

### IN-02: Двойной `Settings.from_env()` в CLI

**File:** `ingestion-service/src/ingestion_service/collect_cli.py:61-67`
**Issue:** `main()` читает settings, затем `build_collect_deps()` читает снова. Лишняя работа; риск расхождения при гипотетической мутации env.
**Fix:** Передавать `settings` в `build_collect_deps(settings)` или читать один раз внутри composition seam.

### IN-03: ING-07 AST не ловит динамические импорты

**File:** `tests/unit/test_phase24_scheduler_guard.py:22-48`
**Issue:** Сканер смотрит только `ast.Import` / `ImportFrom`. `__import__` / `importlib.import_module("publish")` AST не увидит (runtime subprocess частично компенсирует для статического графа collect_cli).
**Fix:** Документировать ограничение; при ужесточении — добавить запрет на `importlib` к forbidden roots в collect-пути.

---

_Reviewed: 2026-10-18T12:50:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
