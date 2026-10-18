---
phase: 11-address-tech-debt-captions-diagnostics-and-persist-error-cla
verified: 2026-10-02T13:41:08Z
status: passed
score: 10/10 must-haves verified
covered_files:
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-01-PLAN.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-01-SUMMARY.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-02-PLAN.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-02-SUMMARY.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-03-PLAN.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-03-SUMMARY.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-04-PLAN.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-04-SUMMARY.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-CONTEXT.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-RESEARCH.md
  - .planning/phases/11-address-tech-debt-captions-diagnostics-and-persist-error-cla/11-VALIDATION.md
  - data-collection/src/data_collection/adapters/youtube_transcript.py
  - ingestion-service/src/ingestion_service/adapters/supabase_persist.py
  - ingestion-service/src/ingestion_service/mapping/captions.py
  - ingestion-service/src/ingestion_service/mapping/url.py
  - ingestion-service/src/ingestion_service/tests_support/fakes.py
  - supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql
  - tests/unit/test_captions_error_mapping.py
  - tests/unit/test_cli_ingest_contract.py
  - tests/unit/test_ingest_error.py
  - tests/unit/test_persist_idempotency_overflow.py
  - tests/unit/test_phase11_migration_009.py
  - tests/unit/test_supabase_draft_persister_contract.py
  - tests/unit/test_youtube_transcript_adapter.py
covered_digest: "v2:sha256:12e1a0102534c38d2f0cfb3a7d6c1a846497f4d8e4dd345700dc43fa85ac5088"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 9
  total: 9
  not_honored: []
---

# Phase 11: Address tech debt — captions diagnostics and persist error classification — Verification Report

**Phase Goal:** Operator CLI diagnostics stay secret-safe and classified correctly: captions/URL envelopes never leak SDK text; out-of-catalog SDK maps to `unknown_captions_error`; persist recognizes `23514` and numeric HTTP statuses without changing `PERSIST_REASONS`; sent-batch re-run returns `already_saved: true` via RPC

**Verified:** 2026-10-02T13:41:08Z  
**Status:** passed  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Out-of-catalog SDK (CookieInvalid path) → parseable IngestError JSON on stderr with `stage=captions` and `reason=unknown_captions_error` (D-04) | ✓ VERIFIED | `test_cli_captions_cookie_invalid_unknown_json_stderr_no_traceback` PASS; mapper fallback `_REASON_BY_TYPE.get(..., "unknown_captions_error")`; adapter catches `YouTubeTranscriptApiException` → `CaptionsError` |
| 2 | Captions failure exit non-zero; combined stdout+stderr has no Python Traceback (D-05) | ✓ VERIFIED | Same CliRunner test asserts `exit_code != 0` and `"Traceback" not in combined`; CLI `json.dumps(err.to_dict())` on stderr |
| 3 | Captions `IngestError.message` is reason + video_id only; SDK text discarded; captions/URL allowlists frozen (D-01…D-03) | ✓ VERIFIED | Message pattern `captions {reason} for {video_id}`; `test_map_captions_error_cookie_invalid_message_is_reason_and_video_id_only`; `test_captions_context_allowlist_frozen`; `test_url_context_allowlist_frozen` |
| 4 | `CAPTIONS_REASONS` frozenset unchanged; no new IngestError stages | ✓ VERIFIED | Locked frozenset equality in captions mapping tests; stages remain url/captions/metadata/consistency/llm/llm_truncation/persist |
| 5 | SQLSTATE `23514` → `DraftPersistBatchError` / `batch_creation_failed` same as `check_violation` (D-06) | ✓ VERIFIED | `_BATCH_CODES = frozenset({"P0001", "check_violation", "23514"})`; `test_sqlstate_23514_maps_to_batch_error` PASS |
| 6 | Integer HTTP gateway status (e.g. 503) → `DraftPersistRpcError` / `rpc_error`, not network_error (D-06) | ✓ VERIFIED | `_http_status_code` + int branch before fallthrough; `test_int_http_503_maps_to_rpc_error_not_network` PASS |
| 7 | `PERSIST_REASONS` frozenset unchanged (D-07) | ✓ VERIFIED | `test_persist_reasons_is_exact_locked_set` PASS; five locked reasons only |
| 8 | Migration 009 CREATE OR REPLACE: sent-batch-only conflict returns `already_saved: true`; P0001 only when no shortlist row; security invoker; revoke public/anon/authenticated; grant service_role (D-08, D-09) | ✓ VERIFIED | SQL fallback SELECT without exclusive `sent_at is null`; offline suite `test_phase11_migration_009.py` (6+ tests) PASS; 008 last commit 2026-09-29 (untouched) |
| 9 | Unit: Fake + CliRunner sent-batch re-run exits 0 with ✓ transcript / ✓ LLM / ✓ saved and `already_saved: true` (D-08; CLI-02; CLI-04) | ✓ VERIFIED | `BatchTrackingFakePersister` returns `already_saved=True` on conflict; `test_cli_sent_batch_rerun_prints_checkmarks_and_already_saved` PASS; overflow invert PASS |
| 10 | Migration 009 live on shared VM (knowledge-db.ru) after Studio apply — human pushed (D-09; CLI-02) | ✓ VERIFIED | Human evidence recorded below (orchestrator/user attestation + 11-04-SUMMARY); MCP `raw_sql` unavailable (no POSTGRES_URL) — live re-probe skipped |

**Score:** 10/10 truths verified (0 present, behavior-unverified)

### Human evidence — live migration 009 (Task 11-04-02 / resume: pushed)

Recorded from human Studio apply confirmation (verifier did not re-apply):

| Check | Result |
|-------|--------|
| Apply method | Studio SQL on knowledge-db.ru — confirmed |
| `prosrc` length | 4092 (was 3414 under 008) |
| `RAISE EXCEPTION` count | 3 only — `p_batch_size>=1`, material lookup failed, existing material has no shortlist row |
| Sent-batch raise ("batch already sent") | Absent |
| Grants | `postgres` + `service_role` only |
| `already_saved` path | Present |

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts. (9/9 honored; D-01…D-09)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tests/unit/test_cli_ingest_contract.py` | Captions JSON stderr + sent-batch checkmarks | ✓ VERIFIED | Substantive CliRunner contracts; wired via `_fake_deps` / FakeTranscriptProvider / BatchTrackingFakePersister |
| `tests/unit/test_captions_error_mapping.py` | Mapper redaction + unknown lock | ✓ VERIFIED | Allowlist freeze + CookieInvalid message |
| `ingestion-service/.../supabase_persist.py` | `_BATCH_CODES` + int HTTP → rpc_error | ✓ VERIFIED | Wired from `persist()` → `_map_exception` |
| `tests/unit/test_supabase_draft_persister_contract.py` | 23514 + int HTTP contracts | ✓ VERIFIED | Named tests PASS |
| `supabase-integration/migrations/009_*.sql` | RPC amend sent-batch already_saved | ✓ VERIFIED | CREATE OR REPLACE; fallback SELECT; grants |
| `tests/unit/test_phase11_migration_009.py` | Offline SQL contract | ✓ VERIFIED | Suite PASS |
| `ingestion-service/.../tests_support/fakes.py` | Fake mirrors sent-batch already_saved | ✓ VERIFIED | Conflict path returns `already_saved=True` |

### Key Link Verification

Automated `verify.key-links` failed because PLAN `from:` values are descriptive (not file paths). Manual wiring:

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| FakeTranscriptProvider / adapter CaptionsError | `cli.py` stderr JSON | `ingest_pipeline` → `map_captions_error` → `IngestError.to_dict()` → `json.dumps` | ✓ WIRED | CliRunner test exercises full path |
| `PostgrestAPIError.code` | `DraftPersistBatchError` / `DraftPersistRpcError` | `_map_exception` / `_sdk_code` / `_http_status_code` | ✓ WIRED | Contract tests inject APIError codes |
| Conflict `v_inserted=0` sent-batch shortlist | jsonb `already_saved: true` | fallback SELECT without exclusive `sent_at IS NULL` | ✓ WIRED | Migration 009 lines 98–126; offline SQL tests |
| `BatchTrackingFakePersister` sent-batch | CLI stdout checkmarks + already_saved | `run_ingest_pipeline` → `cli.py` | ✓ WIRED | CliRunner sent-batch test |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| CLI stderr captions | `payload["reason"]` | `map_captions_error` ← typed CaptionsError | Yes (fixture CaptionsError → same mapper as prod) | ✓ FLOWING |
| Persist classification | exception `code` | PostgrestAPIError → `_sdk_code` / `_http_status_code` | Yes (unit injects real exception shapes) | ✓ FLOWING |
| already_saved stdout | `PersistResult.already_saved` | Fake / RPC jsonb | Unit: fake mirrors 009; live RPC attested | ✓ FLOWING |
| Migration 009 SQL | conflict branch | Postgres RPC (live) | Human Studio apply + prosrc 4092 | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Captions CookieInvalid → JSON stderr | `uv run pytest ...::test_cli_captions_cookie_invalid_unknown_json_stderr_no_traceback` | PASS | ✓ PASS |
| 23514 → batch | `...::test_sqlstate_23514_maps_to_batch_error` | PASS | ✓ PASS |
| Int HTTP 503 → rpc_error | `...::test_int_http_503_maps_to_rpc_error_not_network` | PASS | ✓ PASS |
| Sent-batch CLI already_saved | `...::test_cli_sent_batch_rerun_prints_checkmarks_and_already_saved` | PASS | ✓ PASS |
| Migration 009 SQL contract | `uv run pytest tests/unit/test_phase11_migration_009.py` | PASS (suite) | ✓ PASS |
| PERSIST_REASONS freeze | `...::test_persist_reasons_is_exact_locked_set` | PASS | ✓ PASS |
| Overflow sent-batch invert | `...::test_rerun_when_only_sent_batch_exists_returns_already_saved` | PASS | ✓ PASS |

Named spot-checks batch: **11 passed** in 1.34s (plus freeze/overflow reconfirm).

### Probe Execution

N/A — no `scripts/*/tests/probe-*.sh` declared for this phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| CAP-02 | 11-01 | Captions fail closed, secret-safe JSON stderr | ✓ SATISFIED | CliRunner + mapper/adapter locks |
| PERS-02 | 11-02 | Persist enqueue/classification hardening | ✓ SATISFIED | 23514 + int HTTP classification; reasons frozen |
| CLI-02 | 11-03, 11-04 | Idempotent re-run / sent-batch edge | ✓ SATISFIED | Migration 009 + fake + CLI unit + live apply attested |
| CLI-04 | 11-04 | Staged checkmarks | ✓ SATISFIED | Sent-batch CliRunner asserts three ✓ lines |

No orphaned REQUIREMENTS.md IDs for Phase 11 beyond plan claims (milestone maps CAP/PERS/CLI to earlier phases; Phase 11 hardens).

### Prohibitions (11-03 must_haves)

| Statement | Verdict | Evidence |
| --------- | ------- | -------- |
| MUST NOT edit applied 008 in place | ✓ held | 008 last commit 2026-09-29; 009 is separate CREATE OR REPLACE; `test_migration_008_file_unchanged_relative_to_git_blob` |
| MUST NOT refresh material content on re-run | ✓ held | Conflict path SELECTs slug only; no UPDATE of body_markdown |
| MUST NOT add Python video_id existence pre-check | ✓ held | Pipeline goes URL → captions → metadata → LLM → persist; no materials lookup before captions |
| MUST NOT DROP/TRUNCATE shared DB in 009 | ✓ held | `test_migration_009_has_no_destructive_wipes` |
| MUST NOT grant execute to anon/authenticated | ✓ held | SQL revoke + grant service_role; human grants postgres+service_role only |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | None (no TBD/FIXME/XXX; no skipped requirement tests) | — | — |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `test_cli_ingest_contract.py` | CAP-02, CLI-02, CLI-04 | yes | 0 | no | Behavioral (JSON/stdout lines) | PASS |
| `test_captions_error_mapping.py` | CAP-02 | yes | 0 | no | Value | PASS |
| `test_supabase_draft_persister_contract.py` | PERS-02 | yes | 0 | no | Value (exception type/reason) | PASS |
| `test_phase11_migration_009.py` | CLI-02 | yes | 0 | no | Value (SQL text contracts) | PASS |
| `test_persist_idempotency_overflow.py` | CLI-02 | yes | 0 | no | Behavioral | PASS |

**Disabled tests on requirements:** 0  
**Circular patterns detected:** 0  
**Insufficient assertions:** 0

### Human Verification Required

N/A — Infrastructure/foundation phase with no user-facing elements remaining. Live Studio apply human-check from 11-04 was completed (`pushed`) and attested evidence is recorded above. All acceptance criteria are programmatically verified or human-attested for the schema gate.

### Gaps Summary

None. Phase goal achieved: secret-safe captions/URL diagnostics, persist classification for `23514` + int HTTP without `PERSIST_REASONS` churn, and sent-batch re-run → `already_saved: true` (unit + migration 009 live).

---

## VERIFICATION PASSED

_Verified: 2026-10-02T13:41:08Z_  
_Verifier: Claude (gsd-verifier)_
