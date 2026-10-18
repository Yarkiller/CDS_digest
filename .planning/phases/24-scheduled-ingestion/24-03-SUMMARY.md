---
phase: 24-scheduled-ingestion
plan: 03
subsystem: ingestion
tags: [due-gate, last_run_at, ingestion_schedule, migration-013, europe-moscow, tdd]

requires:
  - phase: 24-02
    provides: select_window / CollectOutcome exit codes / FakeFeed / FakeCollectSourceReader / run_collect_batch
provides:
  - IngestionSchedule / DueDecision / due_decision (injected tzinfo)
  - UtcClock (aware UTC now)
  - CollectSourceReader.get_schedule + stamp_last_run
  - CollectDeps.clock/tz; not_due_reason on CollectOutcome
  - Migration 013 (cursor columns + singleton ingestion_schedule) applied on shared VM
  - Runbook §4j apply/verify
affects:
  - 24-04 (systemd timer polls; due-gate makes Persistent=false safe)
  - 24-05 (admin GET/PATCH ingestion_schedule)
  - 24-06 (UI schedule section)

actuals:
  tokens: 14405
  tasks: 3
  commits: 3

plan_head_before: c1197e0b7f4d784b9ca286ed55f9a8f971c36564
plan_head_after: d164b9b8273ccd73e031dffd23f436c2321ec0e4

tech-stack:
  added: []
  patterns:
    - pure due_decision with injected tzinfo; ZoneInfo only in collect_cli composition
    - stamp_last_run always after due gate (empty run / zero sources included)
    - migration singleton RLS deny-by-default, no seed row (defaults in code)

key-files:
  created:
    - ingestion-service/src/ingestion_service/adapters/utc_clock.py
    - supabase-integration/migrations/013_phase24_scheduled_ingestion.sql
    - tests/unit/test_phase24_migration_013.py
  modified:
    - ingestion-service/src/ingestion_service/domain/schedule.py
    - ingestion-service/src/ingestion_service/application/ports/collect_sources.py
    - ingestion-service/src/ingestion_service/adapters/supabase_collect_sources.py
    - ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py
    - ingestion-service/src/ingestion_service/collect_cli.py
    - ingestion-service/src/ingestion_service/tests_support/fakes.py
    - docs/agents/local-platform-runbook.md
    - tests/unit/test_schedule_due.py
    - tests/unit/test_collect_batch.py
    - tests/unit/test_collect_cli_contract.py
    - tests/unit/test_supabase_collect_sources_contract.py

key-decisions:
  - "schema-013-now: cursor columns on pipeline_ingest_sources + singleton ingestion_schedule in one migration (D-06/D-14)"
  - "Operator applied 013 on shared VM 2026-10-18; PostgREST probe ingestion_schedule → [] (no seed)"

patterns-established:
  - "not due: <reason> single stdout line; exit 0; no feed/LLM"
  - "get_schedule empty → domain defaults; stamp upserts id=1 with last_run_at + updated_at"

requirements-completed: [ING-05, ING-06]

coverage:
  - id: D1
    description: "due_decision reasons: before_time / ok / day / disabled / already_ran; catch-up after missed days; naive now_utc → ValueError"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_schedule_due.py#test_due_decision_before_time_of_day"
        status: pass
      - kind: unit
        ref: "tests/unit/test_schedule_due.py#test_due_decision_catch_up_after_missed_days"
        status: pass
    human_judgment: false
  - id: D2
    description: "not due skips feed/LLM; stamps last_run_at on empty and zero-source due runs"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_not_due_skips_feed_and_returns_reason"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_due_zero_enabled_sources_stamps_and_zeros"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_cli_contract.py#test_collect_cli_not_due_one_line_exit_0_no_feed"
        status: pass
    human_judgment: false
  - id: D3
    description: "schedule read failure → exit 2; stamp failure → exit 1 keeping counters"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_get_schedule_failure_exit_2_no_feed_no_stamp"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_cli_contract.py#test_collect_cli_stamp_failed_exit_1_keeps_summary"
        status: pass
    human_judgment: false
  - id: D4
    description: "Migration 013 text contract + live apply on shared VM (cursor columns, empty schedule, RLS, zero policies)"
    requirement: ING-05
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_migration_013.py"
        status: pass
      - kind: manual_procedural
        ref: "docs/agents/local-platform-runbook.md#4j"
        status: pass
    human_judgment: true
    rationale: "Live DDL on shared knowledge-db VM cannot be proven by unit text-contract alone; operator apply + PostgREST empty-table probe required"

duration: 40min
completed: 2026-10-18
status: complete
---

# Phase 24 Plan 03: Due-gate, last_run_at, migration 013 Summary

**«Пора/не пора» считается в Europe/Moscow по БД; пустой прогон штампует last_run_at; миграция 013 применена на общей VM без seed-строки.**

## Performance

- **Duration:** ~40 min (automate + operator apply gate)
- **Started:** 2026-10-18T11:43:36Z
- **Completed:** 2026-10-18T12:10:00Z
- **Tasks:** 3/3
- **Files modified:** 14

## Accomplishments

- Pure `due_decision` with injected `tzinfo`; reasons `disabled|day|before_time|already_ran|ok`.
- `stamp_last_run` always after due gate (empty feed / zero sources included); schedule-read → exit 2, stamp-fail → exit 1.
- Migration `013` checked in and **applied** on shared VM (2026-10-18); `ingestion_schedule` empty (D-14); runbook §4j stamped.

## Task Commits

1. **Task 1: Подтвердить схему 013 (`schema-013-now`)** — decision only (D-06/D-14); verify `test_phase23_migration_012` green; no code commit
2. **Task 2: Due-гейт + last_run_at + миграция 013** — `d81a35a` (test RED), `1a24a42` (feat GREEN)
3. **Task 3: [BLOCKING] Apply 013 on shared VM** — operator `applied`; `d164b9b` (docs Applied stamp)

**Plan metadata:** `8e690d5` (docs: complete plan); `a60aad7`+ (docs: SUMMARY ledger sync)

## Files Created/Modified

- `ingestion-service/.../domain/schedule.py` — `IngestionSchedule`, `DueDecision`, `due_decision`
- `ingestion-service/.../adapters/utc_clock.py` — aware UTC `Clock`
- `ingestion-service/.../ports/collect_sources.py` — `get_schedule` / `stamp_last_run`
- `ingestion-service/.../adapters/supabase_collect_sources.py` — schedule read + upsert
- `ingestion-service/.../use_cases/collect_batch.py` — due gate + always stamp
- `ingestion-service/.../collect_cli.py` — `not due:` line; `ZoneInfo("Europe/Moscow")`
- `supabase-integration/migrations/013_phase24_scheduled_ingestion.sql` — cursor + singleton + RLS
- `docs/agents/local-platform-runbook.md` — §4j + Applied 2026-10-18

## Decisions Made

- `schema-013-now` (locked D-06/D-14): one migration for cursor columns + `ingestion_schedule`.
- Live apply confirmed by operator; PostgREST `select * from public.ingestion_schedule limit 5` → `[]`.

## Deviations from Plan

None - plan executed as written (decision auto-selected from CONTEXT; BLOCKING apply completed by operator).

### Auth Gates

None.

## Known Stubs

None.

## Threat Flags

None beyond plan threat model (T-24-10…T-24-14 mitigated as designed).

## Self-Check: PASSED

- FOUND: domain/schedule.py, utc_clock.py, migration 013, test_phase24_migration_013.py, 24-03-SUMMARY.md, runbook §4j
- FOUND commits: d81a35a, 1a24a42, d164b9b
