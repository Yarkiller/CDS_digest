---
phase: 24-scheduled-ingestion
plan: 02
subsystem: ingestion
tags: [select-window, cursor, isolation, exit-codes, ingest-collect, tdd]

requires:
  - phase: 24-01
    provides: FakeFeed / FakeCollectSourceReader / run_collect_batch tracer / advance_cursor / collect_cli
provides:
  - select_window (asc sort + cursor filter + per-source limit)
  - CollectOutcome with graded exit codes 0/1/2
  - Video- and source-level failure isolation via emit_diagnostic
  - Fixed two-line stdout summary driven by outcome.exit_code
affects:
  - 24-03 (due gate + stamp + migration 013)
  - 24-04 (systemd OnFailure / alert units keyed to exit codes)

actuals:
  tokens: 10894
  tasks: 2
  commits: 4

plan_head_before: 3efa2684ede388473e920c1350a97d2a18641484
plan_head_after: eb9f4d131130d0fb0c62923c218052a0c1b65ce7

tech-stack:
  added: []
  patterns:
    - domain select_window owns sort/filter/limit; use-case never sorts
    - CollectOutcome(counters, exit_code) as CLI seam
    - emit_diagnostic for all per-item failures (no typer/print in use-case)

key-files:
  created: []
  modified:
    - ingestion-service/src/ingestion_service/domain/schedule.py
    - ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py
    - ingestion-service/src/ingestion_service/collect_cli.py
    - tests/unit/test_schedule_due.py
    - tests/unit/test_collect_batch.py
    - tests/unit/test_collect_cli_contract.py

key-decisions:
  - "Older-than-cursor videos are filtered by select_window (no pipeline/advance call); T-24-08 still enforced via advance_cursor on processed successes"
  - "Video-level try/except landed in Task 1 GREEN so D-09 cursor monotonicity tests could pass before Task 2 expanded source/list isolation"

patterns-established:
  - "_EchoCaptions / _EchoMetadata test doubles for multi-video batches (per-id transcript/metadata)"
  - "CollectOutcome.exit_code is the single source for typer.Exit in collect_cli"

requirements-completed: [ING-02, ING-05, ING-06]

coverage:
  - id: D1
    description: "select_window oldest→newest, limit cuts newest tail, videos_skipped_limit counts cut records only"
    requirement: ING-05
    verification:
      - kind: unit
        ref: "tests/unit/test_schedule_due.py#test_select_window_empty_cursor_limit_cuts_newest_tail"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_run_collect_batch_first_run_processes_oldest_five_in_asc_order"
        status: pass
    human_judgment: false
  - id: D2
    description: "Rescan at feed head makes zero LLM calls"
    requirement: ING-05
    verification:
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_rescan_at_feed_head_makes_zero_llm_calls"
        status: pass
    human_judgment: false
  - id: D3
    description: "Failed video does not advance cursor; later success does; exit 1"
    requirement: ING-05
    verification:
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_run_collect_batch_failed_video_does_not_advance_cursor"
        status: pass
    human_judgment: false
  - id: D4
    description: "Source FeedError isolation + list_enabled_sources failure → exit 2 without feed calls"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_unreadable_source_continues_to_next_source"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_list_enabled_sources_failure_exit_2_no_feed_calls"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_cli_contract.py#test_collect_cli_source_list_failure_exit_2"
        status: pass
    human_judgment: false
  - id: D5
    description: "Graded exit codes and two-line stdout; no ✓ leak; ConfigurationError → exit 1 empty stdout"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_collect_cli_contract.py#test_collect_cli_video_failure_exit_1_and_stderr_diagnostic"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_cli_contract.py#test_collect_cli_configuration_error_exit_1_empty_stdout"
        status: pass
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-18
status: complete
---

# Phase 24 Plan 02: Incremental window, isolation & exit codes Summary

**`select_window` + monotonic successful-only cursor + zero-LLM rescan at feed head; video/source isolation with graded exit codes 0/1/2 and fixed two-line stdout.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-18T11:33:30Z
- **Completed:** 2026-10-18T11:40:33Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- Domain `select_window` sorts oldest→newest, filters by cursor, and lets the per-source limit cut the newest tail (`videos_skipped_limit`).
- Batch writes only domain `advance_cursor` results; failed videos skip cursor advance; rescan at feed head issues zero LLM calls.
- `CollectOutcome` drives CLI `typer.Exit(0|1|2)`; FeedError / list failures isolated with one stderr diagnostic line each.

## Task Commits

1. **Task 1 RED:** `cfe1094` — `test(24-02): add failing tests for select_window and incremental batch`
2. **Task 1 GREEN:** `42f0005` — `feat(24-02): implement select_window and incremental batch cursor`
3. **Task 2 RED:** `8441f00` — `test(24-02): add failing tests for isolation and exit codes`
4. **Task 2 GREEN:** `eb9f4d1` — `feat(24-02): isolate source/video failures and graded exit codes`

## Files Created/Modified

- `ingestion-service/.../domain/schedule.py` — `Cursor` alias + `select_window`
- `ingestion-service/.../collect_batch.py` — windowing, isolation, `CollectOutcome`
- `ingestion-service/.../collect_cli.py` — summary from counters; `Exit(outcome.exit_code)`
- Unit contracts under `tests/unit/test_schedule_due.py`, `test_collect_batch.py`, `test_collect_cli_contract.py`

## Decisions Made

- Older-than-cursor entries never reach the pipeline (filter in `select_window`); the prior 24-01 “advance with current on stale candidate” test was rewritten to assert empty advance/pipeline calls.
- Video-level `try/except` shipped in Task 1 so D-09 monotonicity could be proven before Task 2 added source/list isolation and exit-code grading.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Video isolation in Task 1 GREEN**
- **Found during:** Task 1 GREEN (behavior required failed-video cursor semantics)
- **Issue:** Plan put `try/except` around `run_ingest_pipeline` in Task 2, but Task 1 behavior/D-09 needs it for monotonic cursor tests.
- **Fix:** Landed video-level catch in Task 1; Task 2 added source/list isolation + `CollectOutcome` exit codes.
- **Files modified:** `collect_batch.py`
- **Commit:** `42f0005`

**Total deviations:** 1 auto-fixed (Rule 2). **Impact:** none on contracts; Task 2 still owns exit-code grading and source-level isolation.

## TDD Gate Compliance

- RED commits present: `test(24-02): …` (`cfe1094`, `8441f00`)
- GREEN commits present: `feat(24-02): …` (`42f0005`, `eb9f4d1`)
- RED phases failed on missing `select_window` / missing `CollectOutcome` / uncaught FeedError — intentional assertion/import failures. `workflow.tdd_mode` is false so TAP RED-evidence gate was not enforced.

## Known Stubs

None.

## Threat Flags

None beyond plan `<threat_model>` (T-24-06…T-24-09 mitigations implemented).

## Issues Encountered

None.

## Next Phase Readiness

Ready for `24-03` (due gate, `last_run_at` stamp, migration 013 cursor columns).

## Self-Check: PASSED

- Modified production files exist on disk (`schedule.py`, `collect_batch.py`, `collect_cli.py`).
- Commits `cfe1094`, `42f0005`, `8441f00`, `eb9f4d1` present in `git log`.
- Verify: 43 unit tests green across schedule/batch/CLI collect + ingest contract suites.
