---
phase: 10-cli-composition-uat
verified: 2026-10-02T09:20:34Z
status: passed
score: 18/18 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 16
  total: 16
  not_honored: []
re_verification:
  previous_status: passed
  previous_score: 18/18
  gaps_closed: []
  gaps_remaining: []
  regressions: []
covered_files:
  - ".planning/phases/10-cli-composition-uat/10-01-PLAN.md"
  - ".planning/phases/10-cli-composition-uat/10-01-SUMMARY.md"
  - ".planning/phases/10-cli-composition-uat/10-02-PLAN.md"
  - ".planning/phases/10-cli-composition-uat/10-02-SUMMARY.md"
  - ".planning/phases/10-cli-composition-uat/10-03-PLAN.md"
  - ".planning/phases/10-cli-composition-uat/10-03-SUMMARY.md"
  - ".planning/phases/10-cli-composition-uat/10-04-PLAN.md"
  - ".planning/phases/10-cli-composition-uat/10-04-SUMMARY.md"
  - ".planning/phases/10-cli-composition-uat/10-05-PLAN.md"
  - ".planning/phases/10-cli-composition-uat/10-05-SUMMARY.md"
  - ".planning/phases/10-cli-composition-uat/10-UAT.md"
  - "docs/agents/local-platform-runbook.md"
  - "ingestion-service/.env.example"
  - "ingestion-service/pyproject.toml"
  - "ingestion-service/src/ingestion_service/adapters/supabase_persist.py"
  - "ingestion-service/src/ingestion_service/application/ports/persist.py"
  - "ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py"
  - "ingestion-service/src/ingestion_service/cli.py"
  - "ingestion-service/src/ingestion_service/composition/clients.py"
  - "ingestion-service/src/ingestion_service/tests_support/fakes.py"
  - "supabase-integration/migrations/008_phase10_persist_already_saved.sql"
  - "tests/unit/test_build_ingest_deps_wiring.py"
  - "tests/unit/test_captions_failure_zero_persist.py"
  - "tests/unit/test_cli_ingest_contract.py"
  - "tests/unit/test_data_collection_public_api.py"
  - "tests/unit/test_ingest_pipeline.py"
  - "tests/unit/test_ingestion_env_example.py"
  - "tests/unit/test_persist_draft_use_case.py"
  - "tests/unit/test_persist_idempotency_overflow.py"
  - "tests/unit/test_persist_port.py"
  - "tests/unit/test_phase10_migration_008.py"
  - "tests/unit/test_supabase_draft_persister_contract.py"
  - "uv.lock"
covered_digest: "v2:sha256:f6ca1626365f85ab1b0f256c2b55ce1a046a9f9895f4362720f65b0e21e69497"
---

# Phase 10: CLI Composition & UAT Verification Report

**Phase Goal:** Operator runs one Typer command end-to-end with staged progress, idempotent re-runs, separate env, and 3–5 real videos visible as drafts in `/admin/digest`
**Verified:** 2026-10-02T09:20:34Z
**Status:** passed
**Re-verification:** Prior report had no gaps (`passed`, 18/18, verified 2026-10-01T19:30:46Z). This pass re-checked the goal after `10-UAT.md` moved from `status: passed` to `status: complete` (updated 2026-10-02T09:17:00.000Z, Current Test `[testing complete]`) and refreshes `covered_digest`. UAT close-out was left in place. No production code changed in this session.

## Goal Achievement

### Observable Truths

Roadmap success criteria are truths 1, 7, 13, and 18. Plan must-haves that restate those criteria are folded in rather than scored twice.

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Typer one-shot `ingest <url> --template lecture\|podcast` prints eight stdout lines: `✓ transcript`, `✓ LLM`, `✓ saved`, `material_id`, `slug`, `batch_id`, `rank`, `already_saved: false`, exit 0, empty stderr (CLI-01, CLI-04) | ✓ VERIFIED | `cli.py` echoes those lines after `run_ingest_pipeline`. `test_cli_happy_path_stdout_contract` is in the 82 passing tests. Console script `ingest = ingestion_service.cli:app` in `ingestion-service/pyproject.toml`. |
| 2 | `--template` is required; only `lecture` and `podcast`; no default | ✓ VERIFIED | `TemplateKind` is that closed enum. `test_cli_requires_template_flag` passed. Spot-check `--template essay` exited 2 with no `material_id:`. |
| 3 | `PersistResult.already_saved` exists; a second persist of the same `youtube_video_id` returns stored ids with `already_saved=True` and does not store a second row | ✓ VERIFIED | Field on `PersistResult`. `FakeDraftPersister` returns the stored row. `test_cli_rerun_prints_already_saved_true_with_stored_ids` and `test_fake_repeat_video_id_returns_already_saved_true_without_second_entry` are in the passing set. |
| 4 | Only `ingestion_service/cli.py` imports typer under `ingestion-service/src/ingestion_service/` | ✓ VERIFIED | `test_ingestion_service_has_no_typer_import` is in the passing set. Grep finds `import typer` only in `cli.py`. |
| 5 | Blank, missing, or invalid YouTube URL exits non-zero with no success id lines | ✓ VERIFIED | Spot-check with `build_ingest_deps` stubbed: missing args exit 2; `notaurl` exits 1 with `stage=url`, `reason=not_a_youtube_url`; a blank argument exits 1 with `stage=url`, `reason=invalid_video_id`. None printed `material_id:`. |
| 6 | Checkmarks are the Unicode strings `✓ transcript`, `✓ LLM`, `✓ saved`; metadata and consistency do not emit checkmarks | ✓ VERIFIED | `_STAGE_CHECKMARKS` has only those three keys. `on_stage` is called only after captions, after a validated article, and after persist. Happy-path test asserts the exact strings. |
| 7 | Re-running the same `video_id` does not create a duplicate material or shortlist row; conflict returns the stored `materials.slug` and does not refresh content (CLI-02) | ✓ VERIFIED | Migration 008 `on conflict (youtube_video_id) do nothing`. Conflict branch (`v_inserted = 0`) selects `m.slug` and existing shortlist ids and returns `already_saved` true. The shortlist insert runs only on the insert path. No `UPDATE` of `materials`. SQL contract tests passed. Operator re-run of material 9 kept slug, `batch_id=3`, `rank=1`, `already_saved=true` (`10-UAT.md`). |
| 8 | `transcript.video_id != metadata.video_id` raises `IngestError(stage=consistency, reason=video_id_mismatch)` before LLM and persist | ✓ VERIFIED | Gate in `ingest_pipeline.py` before `article.process`. `test_consistency_mismatch_raises_before_llm_and_persist` is in the passing set. |
| 9 | Captions are fetched before metadata; a captions failure leaves article and persist call lists empty | ✓ VERIFIED | Pipeline order is captions, then metadata. `test_captions_fetched_before_metadata` and `test_captions_failure_leaves_article_and_persist_empty` are in the passing set. |
| 10 | Non-Russian transcripts append ` · пер. с англ.`; Russian transcripts do not | ✓ VERIFIED | `ENGLISH_TRANSLATION_SUFFIX` applied when `transcript.language != "ru"`. English and Russian pipeline tests are in the passing set. |
| 11 | An `IngestError` after a successful transcript keeps `✓ transcript`, writes `IngestError.to_dict()` JSON on stderr, exits non-zero, and prints no later checkmarks | ✓ VERIFIED | `test_cli_mid_pipeline_llm_error_keeps_transcript_checkmark_json_stderr` is in the passing set. |
| 12 | `ConfigurationError` / `TemplateLoadError` before video work: human stderr, non-zero exit, no checkmarks, stderr is not a `stage`+`ok` JSON envelope | ✓ VERIFIED | `cli.py` catches those types and `typer.echo`s `str(err)` to stderr. Both D-08 tests are in the passing set. |
| 13 | Staged progress loads secrets from `ingestion-service/.env`, not the backend env file (CLI-05) | ✓ VERIFIED | `ingestion-service/.env.example` lists `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SHORTLIST_BATCH_SIZE`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `YOUTUBE_PROXY_URL`, `MAX_TRANSCRIPT_CHARS` (`SHORTLIST_BATCH_SIZE=5`). `cli.py` does not call `load_dotenv`. `test_cli_and_settings_do_not_autoload_dotenv` and the env-example tests are in the passing set. Runbook and `10-UAT.md` use `uv run --env-file ingestion-service/.env ingest`. |
| 14 | Migration 008 is `CREATE OR REPLACE` of `persist_draft_and_enqueue`, does not edit 007, is `security invoker`, revokes public/anon/authenticated, grants `service_role` only, and has no DROP/TRUNCATE | ✓ VERIFIED | SQL and `test_phase10_migration_008.py` (5 tests) are in the passing set. |
| 15 | `SupabaseDraftPersister._persist_result` requires `already_saved` and maps it onto `PersistResult` | ✓ VERIFIED | `_RESULT_KEYS` includes `already_saved`. Missing key raises `DraftPersistRpcError`. `test_persist_maps_already_saved_true_with_stored_slug` and `test_persist_missing_already_saved_raises_rpc_error` are in the passing set. |
| 16 | Schema 008 was applied before live UAT that depends on it | ✓ VERIFIED | The adapter fails closed if `already_saved` is absent. Operator re-run printed `already_saved=true` for material 9, which the CLI only prints from `PersistResult`. This session did not re-query `pg_proc`. Another live run was not required. |
| 17 | `build_ingest_deps` wires `Settings.from_env` to YouTube captions, oEmbed, DeepSeek, and `SupabaseDraftPersister`; adapters do not read `os.environ` | ✓ VERIFIED | `cli.py` `build_ingest_deps`. `test_build_ingest_deps_wires_four_ports_via_monkeypatched_factories` is in the passing set. No `os.environ` / `load_dotenv` under `data-collection` adapters. Settings are read in composition. |
| 18 | UAT: four real captioned videos (materials 9–12, batch 3, ranks 1–4) are drafts in `/admin/digest`, including English sources drafted in Russian, with no backend or SPA edits and no Playwright spec (CLI-03) | ✓ VERIFIED | `10-UAT.md` frontmatter `status: complete` (close-out 2026-10-02; `approved: 2026-10-01`). Matrix: 4 passed, 0 issues, 0 pending. lecture+ru, lecture+en, podcast+ru, podcast+en; unsent batch 3; `[draft]`; reader confirmed Russian body, EN provenance suffix, and lecture/podcast headings. No Playwright spec references this UAT. |

**Score:** 18/18 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `ingestion-service/src/ingestion_service/cli.py` | Typer one-shot `ingest` | ✓ VERIFIED | Wired to `run_ingest_pipeline` and `build_ingest_deps` |
| `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` | Captions → metadata → consistency → LLM → persist with `on_stage` | ✓ VERIFIED | Substantive; used by the CLI |
| `ingestion-service/src/ingestion_service/application/ports/persist.py` | `PersistResult.already_saved` | ✓ VERIFIED | Field present and consumed by CLI and adapter |
| `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` | Parse `already_saved` from RPC | ✓ VERIFIED | Required key; mapped onto `PersistResult` |
| `ingestion-service/src/ingestion_service/composition/clients.py` | Live factory wiring | ✓ VERIFIED | Called from `build_ingest_deps` |
| `ingestion-service/.env.example` | Ingestion operator keys, separate from backend | ✓ VERIFIED | Eight keys; file is not the root example |
| `supabase-integration/migrations/008_phase10_persist_already_saved.sql` | Stored slug + `already_saved` | ✓ VERIFIED | Conflict and insert returns; grants |
| `tests/unit/test_cli_ingest_contract.py` | Stdout, re-run, D-08 | ✓ VERIFIED | Included in the 82 passing tests |
| `tests/unit/test_ingest_pipeline.py` | Consistency, order, provenance | ✓ VERIFIED | Included in the 82 passing tests |
| `tests/unit/test_phase10_migration_008.py` | SQL contract | ✓ VERIFIED | Executable SQL, comments stripped |
| `tests/unit/test_build_ingest_deps_wiring.py` | Composition seam | ✓ VERIFIED | Source + monkeypatched factories |
| `.planning/phases/10-cli-composition-uat/10-UAT.md` | Four-row manual UAT | ✓ VERIFIED | `status: complete`; approved 2026-10-01; 4 passed, 0 issues, 0 pending |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `cli.py` Typer `main` | `run_ingest_pipeline` | `asyncio.run` + `build_ingest_deps` | WIRED | Tests monkeypatch the builder; live path calls it |
| `on_stage(transcript\|llm\|saved)` | stdout checkmarks | `typer.echo` after stage success | WIRED | Failure paths do not call `on_stage` for the failed stage |
| consistency gate | `ArticleGenerator.process` | video_id equality before LLM | WIRED | Mismatch raises; article and persist spies stay empty in the test |
| `cli.py` exception branches | stderr | `IngestError.to_dict` vs `str(ConfigurationError)` | WIRED | D-05 vs D-08 tests passed |
| conflict return | `jsonb` slug + `already_saved` | `select m.slug` when `v_inserted = 0` | WIRED | Contract test asserts stored slug and both bools |
| RPC payload | `PersistResult.already_saved` | `_persist_result` | WIRED | Missing key is `DraftPersistRpcError` |
| CLI `already_saved` line | `PersistResult.already_saved` | echo after persist | WIRED | Re-run test prints `already_saved: true` |
| `uv run --env-file ingestion-service/.env ingest` | `/admin/digest` drafts | `persist_draft_and_enqueue` and the existing reader | WIRED | UAT command uses `ingestion-service/.env`; four draft rows recorded; no Playwright spec |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| CLI success lines | `material_id`, `slug`, `batch_id`, `rank`, `already_saved` | `PersistResult` from the persister | Yes on the live path; unit tests use `FakeDraftPersister` | ✓ FLOWING |
| UAT drafts | materials 9–12 | `persist_draft_and_enqueue` into existing admin/reader | Operator-approved rows on unsent batch 3; UAT status `complete` | ✓ FLOWING |
| Provenance suffix | `provenance_label` | `metadata.author` + `ENGLISH_TRANSLATION_SUFFIX` | Computed from transcript language, not a hardcoded draft | ✓ FLOWING |
| `.env.example` | operator keys | static placeholders | Keys only; secrets stay in gitignored `.env` | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase 10 unit contracts | `uv run pytest` on the CLI, pipeline, env, migration 008, persister, persist port, idempotency, wiring, captions-failure, and typer-import tests | 82 passed in 2.28s | ✓ PASS |
| Missing args / invalid URL / blank URL / invalid template | CliRunner with deps builder stubbed | exit 2 / 1 / 1 / 2; no `material_id:`; invalid URL stderr is `stage=url` `not_a_youtube_url` | ✓ PASS |
| Live `pg_proc` re-read | Supabase `raw_sql` | not run | ? SKIP — closed by the approved UAT re-run (`already_saved=true` for material 9), not by a new query |

### Probe Execution

No phase probe scripts are declared. Step 7c skipped.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| CLI-01 | 10-01 | Typer one-shot prints `material_id`, `slug`, `batch_id`, and `rank` on success | ✓ SATISFIED | Truth 1 |
| CLI-02 | 10-03, 10-05 | Re-run of the same `video_id` does not duplicate materials or shortlist rows | ✓ SATISFIED | Truths 3, 7, 14, 15, 16 |
| CLI-03 | 10-04 | 3–5 real captioned videos appear as drafts in `/admin/digest`, including an English source drafted in Russian | ✓ SATISFIED | Truth 18; `10-UAT.md` status `complete`, 4 passed, 0 pending |
| CLI-04 | 10-01, 10-02 | CLI prints `✓ transcript` / `✓ LLM` / `✓ saved` | ✓ SATISFIED | Truths 1, 6, 11 |
| CLI-05 | 10-02, 10-04 | `ingestion-service` has its own `.env`, separate from the backend env file | ✓ SATISFIED | Truths 13, 17 |

No requirement mapped to Phase 10 in `REQUIREMENTS.md` is missing from the plans. CLI-01 through CLI-05 are all marked Complete there.

### Decision Coverage

All 16 trackable `10-CONTEXT.md` decisions are honored by shipped artifacts. Non-blocking. `not_honored` is empty. `workflow.context_coverage_gate` is unset, so the gate ran.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `supabase_persist.py` | `_BATCH_CODES` | Review WR-01: live PostgREST check failures use SQLSTATE `23514`, while the set contains the name `check_violation` | ⚠️ Warning | Misclassified batch/check errors. Does not change the success or idempotent re-run path. |
| `supabase_persist.py` | `_sdk_code` | Review WR-02: integer HTTP status codes on non-JSON gateway errors fall through to `rpc_error` because only string `code` values are read | ⚠️ Warning | Error classification only. Success stdout is unchanged. |
| `fakes.py` | `seed_item` | Review WR-03: seeded video ids are appended to batch items and are not inserted into `stored`, so a later `persist` of that id is not treated as already saved | ⚠️ Warning | Test-double hole. `FakeDraftPersister` and the SQL `ON CONFLICT` path still enforce one row. |

No `TBD`, `FIXME`, or `XXX` markers in the phase implementation files. No skipped tests in the phase 10 unit files that were run.

### Prohibitions checked in code

Plan prohibitions are `verification: null` (not the test tier). Each product prohibition below is honored by the code and by the tests that ran. Dismissed canon-security items stay with the threat model and are not re-opened here.

| Prohibition | Result |
| --- | --- |
| No JSON success envelope on stdout | Honored — line protocol only |
| No `ingest run` subcommand | Honored — console script is the one-shot |
| No `video_id` or `provenance_label` on success stdout | Honored |
| No dotenv autoload in the CLI | Honored |
| No checkmark for a failed stage | Honored |
| No new `IngestError` stage for config/template/Typer failures | Honored — human stderr |
| No `build_provenance_label` added to `provenance.py` | Honored — suffix constant only |
| No content refresh on conflict | Honored — `ON CONFLICT DO NOTHING`, no material `UPDATE` |
| No Python video-id pre-check before captions/LLM | Honored — pipeline order starts at captions |
| No DROP/TRUNCATE in 008; execute not granted to anon/authenticated | Honored |
| No Playwright spec for this UAT | Honored |
| No `backend/` or `web/` edits so drafts appear | Honored — drafts are the existing reader over RPC rows |
| UAT command is `ingestion-service/.env`, not the root backend `.env` | Honored — runbook and `10-UAT.md` |

### Human Verification (completed)

Operator approval on 2026-10-01 is recorded in `10-UAT.md` (`approved: 2026-10-01`) and was closed out on 2026-10-02 (`status: complete`, Current Test `[testing complete]`). This verification accepts that record and does not request another live run. The close-out was not reverted.

| Check | Result |
| --- | --- |
| Materials 9–12 on unsent batch 3, ranks 1–4, badge `[draft]` | Passed |
| Reader `/materials/<slug>`: Russian body; EN rows 10 and 12 end with ` · пер. с англ.`; lecture and podcast headings | Passed |
| Re-run material 9: same slug, `batch_id=3`, `rank=1`, `already_saved=true`, no duplicate row | Passed |

Full watch URLs were not pasted. Rows are identified by `material_id`, rank, and the slug video-id suffix. That matches the approval note.

### Follow-ups (not phase 10 gaps)

`10-UAT.md` logs six UI observations for a later phase: admin preview is title+dek only, email preview is titles only, a leaked `test-header`, interstitial whitespace, no draft→ready control, and empty `score_factors`. They are not CLI-01..CLI-05 failures. They are not deferred roadmap items for a later phase in the current milestone, and they are not gaps in this phase.

### Gaps Summary

No gaps. The phase goal holds in the codebase: one Typer command prints staged progress and the four ids, re-runs are conflict-safe, secrets come from `ingestion-service/.env`, and the completed four-video UAT shows drafts in `/admin/digest` without backend or SPA changes.

Code-review warnings stay advisory. They do not block CLI-01..CLI-05.

---

_Verified: 2026-10-02T09:20:34Z_
_Verifier: gsd-verifier_
