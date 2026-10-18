---
phase: 15-cli-debug-diagnostics
plan: 02
subsystem: cli
tags: [typer, diagnostics, redaction, ports-and-adapters, tdd]

requires:
  - phase: 15-cli-debug-diagnostics
    provides: "plan 15-01 diagnostics port, StderrDiagnostics sink, redaction module, --debug flag, captions stage hook"
provides:
  - "Full metadata/llm/persist success stage lines (D-04)"
  - "stage_failed emission for url/captions/metadata/consistency/llm/persist with mapped reason/exit_code/elapsed_ms (D-10/D-11)"
  - "Pre-video stage=config debug line for ConfigurationError/TemplateLoadError (D-12)"
  - "RecordingDiagnostics call-spy test double for pipeline event-order assertions"
affects: [15-cli-debug-diagnostics verification, 16-pipe-01-mvp-config-ui]

actuals:
  tokens: 6500
  tasks: 3
  commits: 3

commits: 3
plan_head_before: 3380bc0bc09ea5eee7ed84d76d5e9674df136b24
plan_head_after: 55c5816db6becbec437cfdf778b53ef58066c650

tech-stack:
  added: []
  patterns:
    - "Diagnostics emission guarded by `if diagnostics is not None` at every stage boundary"
    - "Failure attribution: map the adapter error once, emit stage_failed from the mapped IngestError, then re-raise"

key-files:
  created: []
  modified:
    - ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
    - ingestion-service/src/ingestion_service/cli.py
    - ingestion-service/src/ingestion_service/tests_support/fakes.py
    - tests/unit/test_cli_debug_diagnostics.py
    - tests/unit/test_ingest_pipeline.py

key-decisions:
  - "Metadata debug line emits only video_id; failure lines emit reason/exit_code/elapsed_ms and never IngestError.message or context (D-06/D-08)"
  - "stage_failed uses the mapped IngestError stage/reason/exit_code verbatim so debug lines correlate 1:1 with the JSON envelope"
  - "url (pre-stage) and consistency failures emit elapsed_ms=0"
  - "config_error runs through sanitize and never mints an IngestError (D-12)"

patterns-established:
  - "Per-stage signals restricted to observable DTO fields; bodies reported as lengths/counters only"
  - "Fail-closed attribution: every mapping except-block reports before re-raising the unchanged IngestError"

requirements-completed: [DBG-01, DBG-02]

coverage:
  - id: D1
    description: "Successful --debug prints one line per stage (captions/metadata/llm/persist) with D-04 signals while stdout stays byte-identical"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_success_emits_all_stage_lines"
        status: pass
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_stage_lines_carry_allowlisted_signals"
        status: pass
    human_judgment: false
  - id: D2
    description: "The metadata debug line exposes only video_id — never the author or the full source URL"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_metadata_line_minimized"
        status: pass
    human_judgment: false
  - id: D3
    description: "Failed runs print completed-stage lines plus the failed stage's reason/exit_code/elapsed_ms before the unchanged JSON envelope"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_failure_prints_completed_and_failed"
        status: pass
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_url_failure_prints_stage_line_with_zero_elapsed"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingest_pipeline.py#test_captions_failure_records_stage_failed"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingest_pipeline.py#test_article_failure_records_stage_failed_after_completed_stages"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingest_pipeline.py#test_invalid_url_records_stage_failed_without_stage_start"
        status: pass
    human_judgment: false
  - id: D4
    description: "Pre-video ConfigurationError/TemplateLoadError prints a stage=config line before the human text and mints no IngestError JSON envelope"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_config_error_line"
        status: pass
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_template_load_error_line"
        status: pass
    human_judgment: false
  - id: D5
    description: "Pipeline emits start/complete (and fail) events in stage order, with persist completion carrying the PersistResult identifiers"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_ingest_pipeline.py#test_pipeline_emits_stage_events_in_order"
        status: pass
    human_judgment: false
  - id: D6
    description: "With --debug off, stdout/stderr, the JSON envelope, and exit codes are unchanged (including the config-error human-text path)"
    requirement: DBG-02
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_off_is_byte_identical"
        status: pass
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_config_error_without_debug_has_no_debug_line"
        status: pass
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-10-04
status: complete
---

# Phase 15 Plan 02: CLI --debug diagnostics (full stage signals + failure/config paths) Summary

**Full per-stage `--debug` lines across captions/metadata/llm/persist plus completed-stage + failed `reason`/`exit_code`/`elapsed_ms` failure lines and a `stage=config` line for pre-video errors — the default stdout/JSON/exit-code contracts stay byte-identical.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-10-04T11:13:00+03:00
- **Completed:** 2026-10-04T11:21:00+03:00
- **Tasks:** 3
- **Files modified:** 5 (0 created, 5 modified)

## Accomplishments
- `run_ingest_pipeline` now emits start→complete events for all four success stages; metadata is `video_id`-only (D-06), llm carries `template`/`response_chars`, persist carries `material_id`/`slug`/`batch_id`/`rank`/`already_saved` (D-04).
- Every mapping `except` block (url/captions/metadata/llm/persist) and the direct `consistency` `IngestError` now emit `stage_failed` with the mapped `stage`/`reason`/`exit_code` before re-raising, so debug lines correlate 1:1 with the JSON envelope (D-10/D-11).
- A pre-video `ConfigurationError`/`TemplateLoadError` emits `stage=config error_type=…` on stderr before the unchanged human text and mints no `IngestError` envelope (D-12).
- `RecordingDiagnostics` call-spy in `tests_support/fakes.py` makes pipeline event order and failure attribution directly assertable.
- Full suite green at **711 passed** (baseline 699 + 12 new).

## Task Commits

Each task was committed atomically (TDD RED→GREEN; tests observed failing for the expected reason before implementation, then shipped in the task commit per the plan's per-task commit contract):

1. **Task 1: Emit metadata/llm/persist stage signals** — `fc5ac09` (feat)
2. **Task 2: Failure diagnostics — completed stages + failed reason/timing** — `bfacd38` (feat)
3. **Task 3: Pre-video config-error diagnostics (`stage=config`)** — `55c5816` (feat)

**Plan metadata:** final `docs(15-02)` metadata commit (SUMMARY + STATE + ROADMAP + REQUIREMENTS).

## Files Created/Modified
- `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` — full stage signals + `stage_failed` attribution in every mapping block
- `ingestion-service/src/ingestion_service/cli.py` — `diagnostics.config_error(...)` in the pre-video config-error handler
- `ingestion-service/src/ingestion_service/tests_support/fakes.py` — `RecordingDiagnostics` call-spy
- `tests/unit/test_cli_debug_diagnostics.py` — success/failure/config CLI assertions
- `tests/unit/test_ingest_pipeline.py` — event-order + `stage_failed` pipeline assertions

## Decisions Made
- Metadata line restricted to `video_id`; failure lines carry only `reason`/`exit_code`/`elapsed_ms` — the JSON envelope already carries the allowlisted context.
- `stage_failed` reports the mapped `IngestError` fields verbatim (including `llm_truncation`/`consistency` when mapped) for envelope correlation.
- Pre-stage (`url`) and `consistency` failures report `elapsed_ms=0` via the sink's no-open-stage path.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 15 is complete (2/2 plans); ready for `/gsd-verify-work 15`.
- The full D-04 signal set plus D-10…D-12 failure/config diagnostics are shipped; plan 16 (PIPE-01 MVP) can proceed.

---
*Phase: 15-cli-debug-diagnostics*
*Completed: 2026-10-04*

## Self-Check: PASSED

- All 3 task commits present (`fc5ac09`, `bfacd38`, `55c5816`); measured `commit` ledger = 3 (`3380bc0..55c5816`).
- `uv run pytest tests/unit/test_cli_debug_diagnostics.py tests/unit/test_ingest_pipeline.py -q` → 20 passed.
- `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_ingest_error.py -q` → green.
- `uv run pytest -q` → 711 passed (baseline 699 + 12 new).
