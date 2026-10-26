---
phase: 23-admin-managed-ingest-sources
reviewed: 2026-10-17T17:50:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - backend/src/backend/domain/ingest_source.py
  - backend/src/backend/domain/errors.py
  - backend/src/backend/application/ports/ingest_sources.py
  - backend/src/backend/application/use_cases/ingest_sources.py
  - backend/src/backend/tests_support/in_memory.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/interface/http/app.py
  - web/src/services/ingestSourcesApi.js
  - web/src/components/IngestSourcesSection.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - web/src/main.jsx
  - supabase-integration/migrations/012_phase23_ingest_sources.sql
  - supabase-integration/src/supabase_integration/ingest_source_repository.py
  - supabase-integration/src/supabase_integration/__init__.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 23: Code Review Report

**Reviewed:** 2026-10-17T17:50:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Вертикальный срез SRC-01/02/03 и ADUX-10 в целом собран правильно: port → use case → HTTP `require_admin`, SPA только через `ingestSourcesApi.js`, миграция `pipeline_ingest_sources` с RLS deny-by-default, dirty OR с одним guard. Критических дыр (auth bypass, nested 400, soft-delete, supabase в UI) не найдено. Ниже — три предупреждения по гонкам/UX и три info по защите в глубину и mock-паритету.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Unique-constraint race maps to 503 instead of 400 duplicate

**File:** `supabase-integration/src/supabase_integration/ingest_source_repository.py:94-99`
**Issue:** Use-case pre-check (D-15) покрывает последовательные дубликаты, но при гонке двух POST уникальный `(kind, source_id)` в Postgres даёт SDK/PostgREST ошибку. Адаптер глотает любой `Exception` в `PersistenceError` → HTTP `503 ingest_sources_unavailable`. Plan 23-02 запрещает показывать unique-constraint как PersistenceError 503; SRC-02 требует top-level `{errors:[…]}` 400. В `vote_repository.py` уже есть паттерн маппинга `"unique"/"duplicate"` → доменный конфликт.
**Fix:** На границе `add` распознать unique violation и пробросить как доменный reject (или re-raise так, чтобы HTTP отдал 400 с `«Этот источник уже добавлен»`), а не `PersistenceError`:

```python
except Exception as exc:  # noqa: BLE001
    message = str(exc).lower()
    if "unique" in message or "duplicate" in message or "23505" in message:
        raise IngestSourceValidationError(
            (PipelineConfigError(path="source_id", message="Этот источник уже добавлен"),)
        ) from exc
    raise PersistenceError(f"pipeline_ingest_sources add failed: {exc}") from exc
```

(Либо тонкий доменный сигнал из адаптера, который route мапит в тот же 400 envelope — без протекания SDK в use-case.)

### WR-02: Toggle double-click can fire two PATCH before busy re-render

**File:** `web/src/components/IngestSourcesSection.jsx:114-133`
**Issue:** `onToggle` проверяет `busyRowId != null`, затем вызывает `setBusyRowId(id)` (асинхронный re-render). До перерисовки кнопка «Включить»/«Выключить» ещё `disabled={rowBusy === false}`, поэтому двойной клик может отправить два PATCH с чередующимся `is_enabled`. Итог — непредсказуемое конечное состояние (D-05 / T-23-20).
**Fix:** Синхронный lock (ref) + disable всех row-action кнопок, пока идёт запрос:

```jsx
const busyRef = useRef(false)

async function onToggle(row) {
  if (busyRef.current) return
  busyRef.current = true
  setBusyRowId(Number(row.id))
  try {
    // ... existing try/catch ...
  } finally {
    busyRef.current = false
    setBusyRowId(null)
  }
}

// в разметке строки:
disabled={busyRowId != null}
```

### WR-03: In-flight lock blocks all rows but only disables the busy row

**File:** `web/src/components/IngestSourcesSection.jsx:115-116,230-238`
**Issue:** Handlers делают early-return при любом `busyRowId != null`, но `disabled={rowBusy}` только у текущей строки. Остальные кнопки выглядят активными, клик молча игнорируется — ломает ожидание D-05 («disable in-flight») и даёт ложное ощущение, что действие принято.
**Fix:** Пока `busyRowId != null`, отключать controls у всех строк: `disabled={busyRowId != null}` (или `disabled={busyRowId != null || rowBusy}`).

## Info

### IN-01: YouTube href builds without encodeURIComponent

**File:** `web/src/components/IngestSourcesSection.jsx:19-25`
**Issue:** URL собирается конкатенацией `source_id`. При текущей серверной валидации UC/PL это безопасно; defense-in-depth слабее, если данные когда-либо попадут мимо D-14.
**Fix:** `encodeURIComponent(id)` в обоих шаблонах URL.

### IN-02: Mock add skips D-14/D-15 validation

**File:** `web/src/services/ingestSourcesApi.js:234-246`
**Issue:** Mock `addIngestSource` не проверяет regex/kind/duplicate — под `VITE_USE_MOCKS` можно добавить невалидный или повторный id. Для Playwright RED серверных rejects это ожидаемо (D-20), но live/mock паритет для ручных сценариев слабый.
**Fix:** Опционально зеркалить минимальный duplicate-check (и/или отклонять явно bad ids) в mock-пути; rejects по-прежнему через `armRejectNextAdd`.

### IN-03: Path param `source_id` shadows domain `source_id`

**File:** `backend/src/backend/interface/http/routes/admin.py:792-804`
**Issue:** Path `{source_id}` — это PK (`int`), тогда как доменный `source_id` — канонический YouTube id. Риск путаницы при сопровождении PATCH/DELETE.
**Fix:** Переименовать path/param в `ingest_source_id` / `source_pk` (без смены URL contract, если уже зафиксирован — хотя бы внутреннее имя аргумента).

---

_Reviewed: 2026-10-17T17:50:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
