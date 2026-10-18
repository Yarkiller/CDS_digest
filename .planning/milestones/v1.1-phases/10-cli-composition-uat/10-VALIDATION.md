---
phase: "10"
slug: "cli-composition-uat"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-29"
updated: "2026-10-01T22:40"
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Audited by `/gsd-validate-phase` on 2026-10-01. CLI-01, CLI-02, CLI-04, CLI-05, and CONSISTENCY-01 are covered by unit tests. CLI-03 live drafts and the Studio apply of migration 008 stay manual-only.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `>=8.3.0` via `uv` |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`) |
| **Quick run command** | `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_ingest_pipeline.py tests/unit/test_phase10_migration_008.py tests/unit/test_ingestion_env_example.py tests/unit/test_build_ingest_deps_wiring.py tests/unit/test_supabase_draft_persister_contract.py -x` |
| **Full suite command** | `uv run pytest tests/unit -q` |
| **Estimated runtime** | ~2 seconds (phase-10 mapped files); full unit suite longer |

---

## Sampling Rate

- **After every task commit:** Run the task's targeted `uv run pytest … -x` command
- **After every plan wave:** Run `uv run pytest tests/unit -q`
- **Before `/gsd-verify-work`:** Full unit suite must be green, and manual `10-UAT.md` must have four video rows filled
- **Max feedback latency:** 60 seconds for the targeted command

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | CLI-01 | T-10-SC | Typer install only after the package-legitimacy gate | checkpoint | `git ls-files -- ingestion-service/pyproject.toml` | N/A | ✅ green |
| 10-01-02 | 01 | 1 | CLI-01, CLI-04 | T-10-01, T-10-03 | Success stdout is eight locked lines; only `cli.py` imports typer; `--template` is required | unit (CliRunner) | `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_persist_port.py tests/unit/test_data_collection_public_api.py -x` | ✅ exists | ✅ green |
| 10-01-03 | 01 | 1 | CLI-01 | T-10-01 | Fake re-run prints `already_saved: true` with stored ids and one stored row | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -x` | ✅ exists | ✅ green |
| 10-02-01 | 02 | 2 | CONSISTENCY-01, CLI-04 | T-10-04 | Mismatched video ids stop at `stage=consistency`; article and persist are not called; captions run before metadata | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -x` | ✅ exists | ✅ green |
| 10-02-02 | 02 | 2 | CLI-04 | T-10-05 | Mid-pipeline JSON stderr keeps prior checkmarks; config/template errors are human stderr without `stage`/`ok` | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -x` | ✅ exists | ✅ green |
| 10-02-03 | 02 | 2 | CLI-05 | T-10-06 | `ingestion-service/.env.example` lists CLI keys; CLI does not autoload dotenv | unit | `uv run pytest tests/unit/test_ingestion_env_example.py -x` | ✅ exists | ✅ green |
| 10-03-01 | 03 | 2 | CLI-02 | T-10-09 | One-way RPC amend decision (`proceed`) before writing 008 | checkpoint | `git ls-files -- supabase-integration/migrations/007_phase9_persist_draft.sql` | N/A | ✅ green |
| 10-03-02 | 03 | 2 | CLI-02 | T-10-07, T-10-08 | Conflict returns stored `materials.slug` and `already_saved`; grants stay service_role-only; no wipes | unit (SQL contract) | `uv run pytest tests/unit/test_phase10_migration_008.py -x` | ✅ exists | ✅ green |
| 10-05-01 | 05 | 3 | CLI-02 | T-10-10 | Adapter requires `already_saved` and maps it; missing key raises `DraftPersistRpcError` | unit | `uv run pytest tests/unit/test_supabase_draft_persister_contract.py tests/unit/test_persist_idempotency_overflow.py tests/unit/test_persist_draft_use_case.py tests/unit/test_captions_failure_zero_persist.py -x` | ✅ exists | ✅ green |
| 10-05-02 | 05 | 3 | CLI-02 | T-10-14 | Migration 008 live on the shared VM | manual | Studio SQL + `pg_proc` / `prosrc` / grant smoke | N/A | ✅ green |
| 10-04-01 | 04 | 4 | CLI-03 | T-10-12 | Live `build_ingest_deps` wires captions, metadata, article, and persist through composition factories | unit | `uv run pytest tests/unit/test_build_ingest_deps_wiring.py tests/unit/test_cli_ingest_contract.py -x` | ✅ exists | ✅ green |
| 10-04-02 | 04 | 4 | CLI-03 | T-10-11 | `10-UAT.md` checklist names lecture/podcast, ids, slug, `/admin/digest`, and D-13 | file assert | checklist file present (filled in 10-04-03) | ✅ `10-UAT.md` | ✅ green |
| 10-04-03 | 04 | 4 | CLI-03 | T-10-11, T-10-13 | Four real drafts on `/admin/digest` with D-16 reader checks | manual | — | ✅ `10-UAT.md` | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Seeded stub names landed during execution. Re-audit on 2026-10-01 found each file present.

- [x] `tests/unit/test_cli_ingest_contract.py` — CLI-01, CLI-04, D-05…D-11 (happy path, required template, re-run, mid-pipeline JSON, D-08 human stderr)
- [x] `tests/unit/test_ingest_pipeline.py` — CONSISTENCY-01, provenance suffix, captions-then-metadata order, CAP-02 persist spy through the pipeline
- [x] `tests/unit/test_phase10_migration_008.py` — SQL/contract: conflict returns stored slug + `already_saved`
- [x] `tests/unit/test_ingestion_env_example.py` — CLI-05 example keys present; not the root backend file
- [x] `test_ingestion_service_has_no_typer_import` allows only `cli.py` to import typer
- [x] `FakeDraftPersister` / `PersistResult` / adapter parse tests cover `already_saved`
- [x] `tests/unit/test_build_ingest_deps_wiring.py` — live composition seam (plan 04 deviation from `test_ingestion_clients.py`)
- [x] `10-UAT.md` manual checklist (four videos) — not automated

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 3–5 real captioned videos appear as drafts in `/admin/digest`, including at least one English source whose draft is Russian | CLI-03 | Live YouTube, DeepSeek, and Supabase service credentials; D-13 forbids Playwright | Already filled in `10-UAT.md` (materials 9–12, batch 3, operator approved 2026-10-01). Re-check: four `[draft]` rows, EN rows Russian with ` · пер. с англ.` on `/materials/<slug>` |
| Migration 008 applies on the shared VM | CLI-02 | Shared dev database; non-interactive `supabase db push` cannot auth | Already applied via Studio SQL (10-05, resume `pushed`). Re-check: `persist_draft_and_enqueue` count = 1, `prosrc` contains `already_saved`, execute is postgres owner + `service_role` only |

*Otherwise: All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s for targeted commands
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-01 (`nyquist_compliant: true`)

---

## Validation Audit 2026-10-01

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

State A re-audit. The seeded map still said Wave 0 files were missing; execution had already created them. PLAN/SUMMARY artifacts were cross-checked against the live suite. Phase 10 mapped files: **91 passed** in 1.61s. No MISSING or PARTIAL automated gaps. Nyquist auditor was not spawned.

Requirement classification (COVERED = test exists, targets the behavior, and ran green):

| Requirement | Status | Evidence |
|-------------|--------|----------|
| CLI-01 | COVERED | `test_cli_happy_path_stdout_contract`, `test_cli_requires_template_flag`, `test_cli_rerun_prints_already_saved_true_with_stored_ids`; typer import limited to `cli.py` |
| CLI-02 | COVERED | `test_phase10_migration_008.py` (stored slug + `already_saved` + grants); `test_persist_maps_already_saved_true_with_stored_slug` and missing-key RPC error; idempotency overflow insert vs conflict |
| CLI-03 | COVERED (wiring) + manual UAT | `test_build_ingest_deps_wiring.py`; four-video evidence in `10-UAT.md` (D-13) |
| CLI-04 | COVERED | Happy-path Unicode checkmarks; `test_cli_mid_pipeline_llm_error_keeps_transcript_checkmark_json_stderr`; D-08 human stderr |
| CLI-05 | COVERED | `test_ingestion_env_example.py` keys, distinct from root backend example, no dotenv autoload, runbook `--env-file` |
| CONSISTENCY-01 | COVERED | `test_consistency_mismatch_raises_before_llm_and_persist` |
