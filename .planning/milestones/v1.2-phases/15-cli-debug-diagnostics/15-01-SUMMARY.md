---
phase: 15-cli-debug-diagnostics
plan: 01
subsystem: cli
tags: [typer, diagnostics, redaction, ports-and-adapters, tdd]

requires:
  - phase: 14-draft-ready-justification
    provides: ingestion pipeline + frozen CLI stdout contract honored by this plan
provides:
  - "Opt-in --debug flag on the ingest CLI (default off, stderr only)"
  - "StageDiagnostics + Clock ports with a NullDiagnostics no-op"
  - "StderrDiagnostics sink with injected clock and emitter"
  - "Allowlist + SecretRegistry + DENY_PATTERNS redaction module"
  - "Captions-stage debug line proven end-to-end"
affects: [15-cli-debug-diagnostics plan 02, 16-pipe-01-mvp-config-ui]

actuals:
  tokens: 4600
  tasks: 3
  commits: 4

commits: 4
plan_head_before: 467f0e2b84cd6cf3b04b94945c3e47d3f9a74257
plan_head_after: 7fe240bba54b51ac430b07db76d9013ebd3307f1

tech-stack:
  added: []
  patterns:
    - "Optional side-channel via typing.Protocol port + Null Object"
    - "Clock port injected into the adapter for deterministic timings"
    - "Hybrid redaction: allowlist emission + exact-value registry + denylist safety net"

key-files:
  created:
    - ingestion-service/src/ingestion_service/diagnostics/__init__.py
    - ingestion-service/src/ingestion_service/diagnostics/redaction.py
    - ingestion-service/src/ingestion_service/application/ports/diagnostics.py
    - ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py
    - tests/unit/test_cli_debug_diagnostics.py
    - tests/unit/test_stderr_diagnostics.py
    - tests/unit/test_debug_redaction.py
  modified:
    - ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
    - ingestion-service/src/ingestion_service/cli.py
    - ingestion-service/src/ingestion_service/tests_support/fakes.py

key-decisions:
  - "Sink stays typer-free: cli.py injects typer.echo(..., err=True) as the emitter, keeping test_ingestion_service_has_no_typer_import green while production debug still goes to stderr"
  - "Redaction order is SecretRegistry.mask -> DENY_PATTERNS -> control-char strip -> length cap; the Bearer pattern precedes the assignment pattern so a token value cannot leak past the scheme word"
  - "Captions stage emits the domain token 'captions' (not 'transcript') for 1:1 correlation with IngestError.stage (resolved Q2)"

patterns-established:
  - "Optional diagnostics side-channel: StageDiagnostics Protocol + NullDiagnostics no-op; the use-case imports no time/sys/typer/datetime"
  - "Injected Clock + FakeClock makes elapsed_ms and [HH:MM:SS] timestamps exactly assertable"

requirements-completed: [DBG-01, DBG-02]

coverage:
  - id: D1
    description: "--debug prints a secret-safe [HH:MM:SS] debug stage=captions line on stderr while stdout stays byte-identical"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_success_emits_stage_lines"
        status: pass
    human_judgment: false
  - id: D2
    description: "Without --debug, stderr is empty and stdout matches the frozen success contract"
    requirement: DBG-02
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_off_is_byte_identical"
        status: pass
    human_judgment: false
  - id: D3
    description: "Redaction masks exact secrets and denylist shapes (cookie/bearer/JWT/URL userinfo), strips control chars, and never raises on a violation"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_debug_redaction.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Sink formats deterministic timestamp/elapsed_ms/allowlist output against an injected clock"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_stderr_diagnostics.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Use-case stays infra-free: no time/sys/typer/datetime imports in run_ingest_pipeline"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_ingest_pipeline_retains_no_infra_imports"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-10-04
status: complete
---

# Phase 15 Plan 01: CLI --debug diagnostics (foundation + captions tracer) Summary

**Opt-in `--debug` prints a secret-safe `[HH:MM:SS] debug stage=captions …` line on stderr through a Clock-injected sink and hybrid allowlist/denylist redaction, while the default stdout contract stays byte-identical.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-10-04T11:05:00+03:00
- **Completed:** 2026-10-04T11:13:00+03:00
- **Tasks:** 3
- **Files modified:** 10 (7 created, 3 modified)

## Accomplishments
- `--debug` flag wired end-to-end: `cli.main` → `StderrDiagnostics` → `run_ingest_pipeline(diagnostics=…)` → captions stage line.
- New `StageDiagnostics` + `Clock` ports and `NullDiagnostics` no-op guarantee zero debug output when the flag is off (D-13 / DBG-02).
- `redaction.py` ships the allowlist (`ALLOWED_KEYS`), exact-value `SecretRegistry`, and the `DENY_PATTERNS` safety net (cookie/bearer/sk-/JWT/URL-userinfo/control chars), with mask-not-fail semantics.
- Deterministic sink formatting proven against a scripted `FakeClock`; the use-case imports no `time`/`sys`/`typer`/`datetime`.

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "--debug" captions line (tracer)** — `72f8525` (feat)
2. **Task 2: Sink formatting determinism with FakeClock** — `b163de1` (test)
3. **Task 3: Redaction denylist + exact-value safety net** — `2ae1862` (feat)
4. **Deviation fix: keep typer out of the diagnostics adapter** — `7fe240b` (fix)

**Plan metadata:** final `docs(15-01)` metadata commit (SUMMARY + STATE + ROADMAP).

_Note: TDD tasks used the RED→GREEN cycle; each task is a single commit (Task 1 had no refactor step)._

## Files Created/Modified
- `ingestion-service/src/ingestion_service/diagnostics/__init__.py` - package marker
- `ingestion-service/src/ingestion_service/diagnostics/redaction.py` - `ALLOWED_KEYS`, `SecretRegistry`, `DENY_PATTERNS`, `sanitize`
- `ingestion-service/src/ingestion_service/application/ports/diagnostics.py` - `DebugValue`, `Clock`, `StageDiagnostics`, `NullDiagnostics`
- `ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py` - `SystemClock`, `StderrDiagnostics`
- `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` - optional `diagnostics` param + captions events
- `ingestion-service/src/ingestion_service/cli.py` - `--debug` flag, `_settings_secrets`, `_emit_debug`, sink wiring, `settings` in deps namespace
- `ingestion-service/src/ingestion_service/tests_support/fakes.py` - `FakeClock` scripted clock double
- `tests/unit/test_cli_debug_diagnostics.py` - flag on/off + stdout contract + infra-import guard
- `tests/unit/test_stderr_diagnostics.py` - deterministic formatting, control-char, allowlist
- `tests/unit/test_debug_redaction.py` - registry + denylist + mask-not-fail

## Decisions Made
- Sink stays `typer`-free; `cli.py` injects `typer.echo(..., err=True)` as the emitter (see deviation below).
- Denylist ordering: Bearer before the assignment pattern; control characters are stripped (no trace) rather than masked.
- Captions stage uses the domain `captions` token per locked Q2.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Sink imported `typer`, breaking the architecture guard**
- **Found during:** full-suite verification after Task 3
- **Issue:** `tests/unit/test_data_collection_public_api.py::test_ingestion_service_has_no_typer_import` asserts only `cli.py` imports `typer`; the plan directed the adapter to call `typer.echo(..., err=True)` directly, which violated that existing guard.
- **Fix:** Removed `import typer` from `stderr_diagnostics.py`; added an injected `emit` callable (fallback `sys.stderr`). `cli.py` now passes `_emit_debug = lambda line: typer.echo(line, err=True)`. Production debug still emits only via `typer.echo(..., err=True)` on stderr; the adapter stays framework-free.
- **Files modified:** `ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py`, `ingestion-service/src/ingestion_service/cli.py`
- **Verification:** `uv run pytest -q` → 699 passed; architecture guard green.
- **Committed in:** `7fe240b`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary to honor the repo's existing "only `cli.py` imports typer" invariant while keeping the plan's stderr-only, mask-not-fail intent. No scope creep.

## Issues Encountered
- Running the plan's `<automated>` suites individually stayed green; only the full-suite architecture guard surfaced the `typer`-import conflict (see deviation).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The port/sink/redaction foundation is ready for plan 15-02 to add metadata/llm/persist stages plus `stage_failed` and `stage=config` emission.
- Full suite is green at 699 passed (baseline 684 + 15 new).

---
*Phase: 15-cli-debug-diagnostics*
*Completed: 2026-10-04*

## Self-Check: PASSED

- All 7 created files present; all 4 commits (`72f8525`, `b163de1`, `2ae1862`, `7fe240b`) found.
- `uv run pytest -q` → 699 passed (baseline 684 + 15 new).
