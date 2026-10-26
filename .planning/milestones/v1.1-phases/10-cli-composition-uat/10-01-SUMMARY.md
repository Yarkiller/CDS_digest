---
phase: 10-cli-composition-uat
plan: 01
subsystem: ingestion-cli
tags: [typer, cli, ingest, PersistResult, CliRunner, already_saved]

requires:
  - phase: 09-draft-persist-shortlist-enqueue
    provides: PersistPort / FakeDraftPersister / persist_draft / Settings composition
provides:
  - Typer console script `ingest` with happy-path stdout contract
  - async run_ingest_pipeline with on_stage callbacks
  - PersistResult.already_saved on port + fake conflict branch
affects:
  - 10-02 pipeline error paths
  - 10-03 migration 008 already_saved RPC
  - 10-05 SupabaseDraftPersister RPC parse

actuals:
  tokens: 6497
  tasks: 3
  commits: 4

plan_head_before: 088988d699c05fbfb6400470d0125d09a9d9d144
plan_head_after: 6b0f1beb01bcfc466d42dd74292c0df4bba758e0

tech-stack:
  added: [typer>=0.27.2]
  patterns:
    - thin Typer cli.py + injectable build_ingest_deps for CliRunner
    - print-as-you-go on_stage checkmarks then id lines

key-files:
  created:
    - ingestion-service/src/ingestion_service/cli.py
    - ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
    - tests/unit/test_cli_ingest_contract.py
  modified:
    - ingestion-service/pyproject.toml
    - uv.lock
    - ingestion-service/src/ingestion_service/application/ports/persist.py
    - ingestion-service/src/ingestion_service/tests_support/fakes.py
    - tests/unit/test_persist_port.py
    - tests/unit/test_data_collection_public_api.py
    - tests/unit/test_persist_draft_use_case.py
    - tests/unit/test_persist_idempotency_overflow.py

key-decisions:
  - "build_ingest_deps returns SimpleNamespace of ports; CliRunner monkeypatches the builder"
  - "PersistResult.already_saved defaults to False so deferred 10-05 call sites keep constructing"
  - "Fake conflict returns stored ids/slug with already_saved=True without a second stored row"

patterns-established:
  - "Pattern: Typer one-shot @app.command with required --template Enum, no subcommand"
  - "Pattern: staged progress via on_stage('transcript'|'llm'|'saved') → Unicode checkmarks"

requirements-completed: [CLI-01, CLI-04]

coverage:
  - id: D1
    description: CliRunner happy path prints eight locked stdout lines with already_saved false
    requirement: CLI-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py::test_cli_happy_path_stdout_contract"
        status: pass
    human_judgment: false
  - id: D2
    description: --template is required; missing flag exits non-zero without material_id
    requirement: CLI-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py::test_cli_requires_template_flag"
        status: pass
    human_judgment: false
  - id: D3
    description: Checkmark progress lines use exact Unicode ✓ transcript / ✓ LLM / ✓ saved
    requirement: CLI-04
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py::test_cli_happy_path_stdout_contract"
        status: pass
    human_judgment: false
  - id: D4
    description: Fake re-run prints already_saved true with stored ids and one stored row
    requirement: CLI-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py::test_cli_rerun_prints_already_saved_true_with_stored_ids"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-29
status: complete
---

# Phase 10 Plan 01: Tracer Typer ingest happy path Summary

**Typer `ingest` one-shot prints the locked eight-line stdout contract through injectable fakes, with `PersistResult.already_saved` on the fake port.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-09-29T20:51:00+03:00
- **Completed:** 2026-09-29T21:00:00+03:00
- **Tasks:** 3/3
- **Files modified:** 11

## Accomplishments

- Approved `typer` 0.27.2 installed via `uv add --package ingestion-service typer`; console script `ingest = ingestion_service.cli:app`
- CliRunner happy path matches CONTEXT sample (three checkmarks, four ids, `already_saved: false`); missing `--template` exits non-zero
- Fake re-run exits 0 with `already_saved: true` and identical stored ids; only `cli.py` may import typer

## Task Commits

1. **Task 1: Verify typer package legitimacy** — human `approved` (no code commit; gate only)
2. **Task 2 RED: failing contract tests** — `5ee7c3b` (test)
3. **Task 2 GREEN: Typer ingest + pipeline + already_saved** — `2de49ca` (feat)
4. **Task 3: CliRunner re-run already_saved true** — `e245eaa` (test)
5. **Rule 1 fix: default already_saved + idempotency asserts** — `6b0f1be` (fix)

## TDD Gate Compliance

- **RED:** `test_fake_repeat_video_id_returns_already_saved_true_without_second_entry` failed with TypeError (unexpected `already_saved`); `tdd-red-evidence` → `RED_EVIDENCE_OK`. CliRunner happy-path failed ImportError for missing `cli` (also `RED_EVIDENCE_OK`).
- **GREEN:** `feat(10-01)` implemented port/fakes/pipeline/cli; plan verify suite 35 passed.
- **Task 3:** re-run CliRunner test was unexpectedly green (behavior already shipped in Task 2 FakeDraftPersister); committed as documenting test only.

## Files Created/Modified

- `ingestion-service/src/ingestion_service/cli.py` — Typer one-shot + `build_ingest_deps`
- `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` — full operator pipeline
- `ingestion-service/src/ingestion_service/application/ports/persist.py` — `already_saved: bool = False`
- `ingestion-service/src/ingestion_service/tests_support/fakes.py` — conflict → `already_saved=True`
- `tests/unit/test_cli_ingest_contract.py` — happy path, required template, re-run
- `ingestion-service/pyproject.toml` / `uv.lock` — typer + `[project.scripts]`

## Decisions Made

- Composition seam is `build_ingest_deps()` returning a `SimpleNamespace` of ports (monkeypatch-friendly).
- Default `already_saved=False` keeps deferred PersistResult constructors compiling until 10-05 updates the live adapter.
- CONSISTENCY-01 fail path left for 10-02; happy path runs captions → metadata → LLM → persist.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Cascade from required `already_saved`**
- **Found during:** Task 2 GREEN / post-verify full suite
- **Issue:** Required `already_saved` broke deferred PersistResult constructors; Fake conflict `already_saved=True` broke `first == second` idempotency asserts
- **Fix:** Default `already_saved=False`; update idempotency tests to assert id equality + already_saved flip
- **Files modified:** `persist.py`, `test_persist_draft_use_case.py`, `test_persist_idempotency_overflow.py`
- **Commit:** `6b0f1be`

**2. [Task 3 TDD] Unexpected green on re-run test**
- **Found during:** Task 3
- **Issue:** FakeDraftPersister conflict branch already returned `already_saved=True` from Task 2
- **Fix:** Committed documenting CliRunner re-run test without a separate feat
- **Commit:** `e245eaa`

## Auth Gates

None after the cleared typer package-legitimacy `blocking-human` gate (user replied `approved`).

## Known Stubs

None — happy path uses real pipeline stages with injectable fakes; live Supabase parse deferred to 10-05 by plan.

## Threat Flags

None beyond plan threat_model (T-10-01..T-10-SC mitigated: no secrets in stdout, no dotenv autoload, Enum template, legitimacy gate).

## Self-Check: PASSED

- FOUND: `ingestion-service/src/ingestion_service/cli.py`
- FOUND: `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py`
- FOUND: `tests/unit/test_cli_ingest_contract.py`
- FOUND: commit `5ee7c3b`
- FOUND: commit `2de49ca`
- FOUND: commit `e245eaa`
- FOUND: commit `6b0f1be`
