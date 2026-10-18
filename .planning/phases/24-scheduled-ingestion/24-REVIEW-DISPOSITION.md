---
phase: 24
review: 24-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Падение advance_cursor роняет весь batch без graded exit"
  - id: WR-01
    severity: warning
    disposition: deferred
    title: "Курсор уходит вперёд мимо failed-видео — повторный ingest невозможен"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Неожиданные ошибки feed не изолированы на уровне источника"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "Stamp при нуле enabled-источников блокирует same-day сбор"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Alert-unit выполняется от root"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Очистка поля времени + blur оставляет пустой draft"
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "Fallback ответа PATCH обнуляет last_run_at в DTO"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "missing_video_id смешивает отсутствие и невалидный id"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "Двойной Settings.from_env() в CLI"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "ING-07 AST не ловит динамические импорты"
open: 5
total: 10
recorded: 2026-10-18T13:30:00.000Z
---

# Phase 24: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | Fixed in `cfe45b7` (tests `364a8e6`): cursor write wrapped in try/except; `videos_failed += 1`, `cursor advance failed` diagnostic, batch continues, exit 1. |
| WR-01 | warning | deferred | Same follow-up as CR-01 (cursor gap semantics, D-09 contract change). |
| WR-02 | warning | fixed | Fixed in `cfe45b7` (tests `364a8e6`): unexpected `list_recent` exceptions degrade to `sources_unreadable` + diagnostic; known FeedError/CollectSourceError messages kept distinct. |
| WR-03 | warning | deferred | Same follow-up: skip `stamp_last_run` when zero enabled sources (touches ING-06 D-23 contract). |
| WR-04 | warning | fixed | Fixed in `3240732` (tests `bf8b2fe`): alert unit runs as `digestcds` with `NoNewPrivileges`/`PrivateTmp`. |
| WR-05 | warning | fixed | Fixed in `0ebb64b` (tests `ac9892f`): empty time blur restores `schedule.time_of_day`, no PATCH. |
| WR-06 | warning | fixed | Fixed in `744e17b` (tests `86a44af`): empty upsert representation triggers follow-up read; missing row raises `PersistenceError`. |
| IN-01 | info | deferred | Diagnostics polish. |
| IN-02 | info | deferred | Minor duplication in CLI composition. |
| IN-03 | info | deferred | Documented limitation of the AST guard. |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently.
