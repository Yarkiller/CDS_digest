---
phase: 24
review: 24-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: deferred
    title: "Падение advance_cursor роняет весь batch без graded exit"
  - id: WR-01
    severity: warning
    disposition: deferred
    title: "Курсор уходит вперёд мимо failed-видео — повторный ingest невозможен"
  - id: WR-02
    severity: warning
    disposition: deferred
    title: "Неожиданные ошибки feed не изолированы на уровне источника"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "Stamp при нуле enabled-источников блокирует same-day сбор"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "Alert-unit выполняется от root"
  - id: WR-05
    severity: warning
    disposition: deferred
    title: "Очистка поля времени + blur оставляет пустой draft"
  - id: WR-06
    severity: warning
    disposition: deferred
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
open: 10
total: 10
recorded: 2026-10-18T13:30:00.000Z
---

# Phase 24: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | deferred | Deferred to human decision at phase gate: fix requires a failing-test-first follow-up (`run_collect_batch` cursor write outside `try`). Verifier scored it ⚠️ Warning, does not falsify a must-have. |
| WR-01 | warning | deferred | Same follow-up as CR-01 (cursor gap semantics, D-09 contract change). |
| WR-02 | warning | deferred | Same follow-up: broaden source-level isolation to `Exception`. |
| WR-03 | warning | deferred | Same follow-up: skip `stamp_last_run` when zero enabled sources (touches ING-06 D-23 contract). |
| WR-04 | warning | deferred | systemd hardening, apply together with WR-01..03 follow-up. |
| WR-05 | warning | deferred | UI polish, batch with follow-up. |
| WR-06 | warning | deferred | Adapter fallback, batch with follow-up. |
| IN-01 | info | deferred | Diagnostics polish. |
| IN-02 | info | deferred | Minor duplication in CLI composition. |
| IN-03 | info | deferred | Documented limitation of the AST guard. |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently.
