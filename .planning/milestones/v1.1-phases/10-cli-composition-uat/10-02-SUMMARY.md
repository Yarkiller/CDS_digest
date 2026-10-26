---
phase: 10-cli-composition-uat
plan: 02
subsystem: ingestion-cli
tags: [consistency, ingest-pipeline, CliRunner, D-08, env-example, CLI-05]

requires:
  - phase: 10-cli-composition-uat
    provides: Typer ingest tracer, run_ingest_pipeline happy path, PersistResult.already_saved
provides:
  - CONSISTENCY-01 fail-closed video_id_mismatch gate before LLM
  - CliRunner mid-pipeline JSON stderr + D-08 TemplateLoadError human path
  - Expanded ingestion-service/.env.example + runbook --env-file invoke
affects:
  - 10-03 migration 008 already_saved RPC
  - 10-04 live UAT operator path
  - 10-05 SupabaseDraftPersister RPC parse

actuals:
  tokens: 4487
  tasks: 3
  commits: 6

plan_head_before: c9b942520cb13841be0a985bd7b55c8bb07a4e4c
plan_head_after: dea13a9748546dc2d8c530b4eb2f47a694505053

tech-stack:
  added: []
  patterns:
    - consistency gate after captions+metadata, before article.process
    - D-08 ConfigurationError|TemplateLoadError human stderr vs IngestError JSON

key-files:
  created:
    - tests/unit/test_ingest_pipeline.py
    - tests/unit/test_ingestion_env_example.py
  modified:
    - ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
    - ingestion-service/src/ingestion_service/cli.py
    - tests/unit/test_cli_ingest_contract.py
    - ingestion-service/.env.example
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "Consistency context allowlist is only transcript_video_id + metadata_video_id (T-10-04)"
  - "TemplateLoadError shares the ConfigurationError D-08 human branch — no new IngestError stage"

patterns-established:
  - "Pattern: fail closed on DTO video_id mismatch before any LLM/persist call"
  - "Pattern: pre-video exceptions echo str(err) on stderr; pipeline IngestError dumps to_dict() JSON"

requirements-completed: [CLI-04, CLI-05]

coverage:
  - id: D1
    description: Mismatched transcript/metadata video_id raises consistency/video_id_mismatch with empty article and persist calls
    requirement: CLI-04
    verification:
      - kind: unit
        ref: "tests/unit/test_ingest_pipeline.py::test_consistency_mismatch_raises_before_llm_and_persist"
        status: pass
    human_judgment: false
  - id: D2
    description: Captions-then-metadata order and EN/RU provenance suffix via ENGLISH_TRANSLATION_SUFFIX
    requirement: CLI-04
    verification:
      - kind: unit
        ref: "tests/unit/test_ingest_pipeline.py::test_captions_fetched_before_metadata"
        status: pass
    human_judgment: false
  - id: D3
    description: Mid-pipeline llm IngestError keeps ✓ transcript on stdout and JSON stderr; config/template errors are human stderr without stage/ok
    requirement: CLI-04
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py::test_cli_mid_pipeline_llm_error_keeps_transcript_checkmark_json_stderr"
        status: pass
    human_judgment: false
  - id: D4
    description: ingestion-service/.env.example lists CLI-05 keys; runbook documents uv run --env-file ingestion-service/.env ingest
    requirement: CLI-05
    verification:
      - kind: unit
        ref: "tests/unit/test_ingestion_env_example.py::test_ingestion_env_example_lists_required_keys"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-09-29
status: complete
---

# Phase 10 Plan 02: Pipeline edges, errors, and ingestion env example Summary

**CONSISTENCY-01 fail-closed gate, D-05/D-08 CliRunner failure split, and CLI-05 ingestion `.env.example` + runbook `--env-file` path.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-09-29T18:00:29Z
- **Completed:** 2026-09-29T18:20:00Z
- **Tasks:** 3/3
- **Files modified:** 7

## Accomplishments

- `run_ingest_pipeline` raises `IngestError(stage=consistency, reason=video_id_mismatch)` before LLM/persist when DTO video ids diverge; captions-then-metadata order and EN/RU provenance proven
- CliRunner mid-pipeline JSON stderr keeps prior `✓ transcript`; `TemplateLoadError` joins `ConfigurationError` on the D-08 human path
- `ingestion-service/.env.example` expanded with DeepSeek/YouTube/max-chars keys; runbook documents `uv run --env-file ingestion-service/.env ingest`

## Task Commits

1. **Task 1 RED: CONSISTENCY-01 pipeline tests** — `200b5c3` (test)
2. **Task 1 GREEN: video_id mismatch gate** — `96e76a8` (feat)
3. **Task 2 RED: CliRunner error contracts** — `50ca601` (test)
4. **Task 2 GREEN: TemplateLoadError D-08 catch** — `921b095` (feat)
5. **Task 3 RED: ingestion .env.example assertions** — `51244b0` (test)
6. **Task 3 GREEN: expand env example + runbook** — `dea13a9` (feat)

## TDD Gate Compliance

- **Task 1 RED:** `test_consistency_mismatch_raises_before_llm_and_persist` → DID NOT RAISE; `tdd-red-evidence` → `RED_EVIDENCE_OK`. GREEN: consistency compare before `article.process`.
- **Task 2 RED:** mid-pipeline + ConfigurationError already green from 10-01; intentional RED on `test_cli_template_load_error_is_human_stderr_without_json_envelope` (empty stderr); `RED_EVIDENCE_OK`. GREEN: catch `(ConfigurationError, TemplateLoadError)`.
- **Task 3 RED:** missing `DEEPSEEK_API_KEY=` in `.env.example`; `RED_EVIDENCE_OK`. GREEN: expanded keys + runbook subsection.

## Files Created/Modified

- `tests/unit/test_ingest_pipeline.py` — CONSISTENCY-01, order, provenance, CAP-02
- `ingest_pipeline.py` — consistency gate with allowlisted context
- `tests/unit/test_cli_ingest_contract.py` — mid-pipeline + D-08 cases
- `cli.py` — TemplateLoadError on D-08 human branch
- `tests/unit/test_ingestion_env_example.py` — CLI-05 key/gitignore/runbook asserts
- `ingestion-service/.env.example` — eight operator keys (empty values / SHORTLIST=5)
- `docs/agents/local-platform-runbook.md` — ingest `--env-file` subsection

## Decisions Made

- Consistency context is only `transcript_video_id` and `metadata_video_id` (T-10-04).
- `TemplateLoadError` shares the ConfigurationError human stderr branch — no new stage (D-08).

## Deviations from Plan

### Auto-fixed Issues

**1. [Task 2 TDD] Mid-pipeline + ConfigurationError unexpectedly green**
- **Found during:** Task 2 RED
- **Issue:** 10-01 already wired IngestError JSON and ConfigurationError human catch
- **Fix:** Kept documenting tests; intentional RED was TemplateLoadError (uncaught → empty stderr)
- **Files modified:** `cli.py`, `test_cli_ingest_contract.py`
- **Commit:** `921b095`

## Auth Gates

None.

## Known Stubs

None — consistency, error split, and env example are fully wired for this plan's goal.

## Threat Flags

None beyond plan threat_model (T-10-04…T-10-06 mitigated: allowlisted consistency context, human messages name keys only, separate ingestion env file).

## Self-Check: PASSED

- FOUND: `tests/unit/test_ingest_pipeline.py`
- FOUND: `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py`
- FOUND: `tests/unit/test_cli_ingest_contract.py`
- FOUND: `ingestion-service/src/ingestion_service/cli.py`
- FOUND: `tests/unit/test_ingestion_env_example.py`
- FOUND: `ingestion-service/.env.example`
- FOUND: `docs/agents/local-platform-runbook.md`
- FOUND: commit `200b5c3`
- FOUND: commit `96e76a8`
- FOUND: commit `50ca601`
- FOUND: commit `921b095`
- FOUND: commit `51244b0`
- FOUND: commit `dea13a9`
