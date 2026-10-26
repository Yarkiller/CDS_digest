---
phase: 15-cli-debug-diagnostics
verified: 2026-10-04T08:46:35Z
status: passed
score: 12/12 must-haves verified
covered_files:
  - .planning/phases/15-cli-debug-diagnostics/15-01-PLAN.md
  - .planning/phases/15-cli-debug-diagnostics/15-01-SUMMARY.md
  - .planning/phases/15-cli-debug-diagnostics/15-02-PLAN.md
  - .planning/phases/15-cli-debug-diagnostics/15-02-SUMMARY.md
  - .planning/phases/15-cli-debug-diagnostics/15-03-PLAN.md
  - .planning/phases/15-cli-debug-diagnostics/15-03-SUMMARY.md
  - ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py
  - ingestion-service/src/ingestion_service/application/ports/diagnostics.py
  - ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
  - ingestion-service/src/ingestion_service/cli.py
  - ingestion-service/src/ingestion_service/diagnostics/__init__.py
  - ingestion-service/src/ingestion_service/diagnostics/redaction.py
  - ingestion-service/src/ingestion_service/tests_support/fakes.py
  - tests/unit/test_cli_debug_diagnostics.py
  - tests/unit/test_debug_redaction.py
  - tests/unit/test_ingest_pipeline.py
  - tests/unit/test_stderr_diagnostics.py
covered_digest: "v2:sha256:73886a9c91786cc6bb69fea5d65fe5dd450316413bf35d9472836bbca81527fa"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 11/12
  gaps_closed:
    - "SC2 / D-07 / D-08 / D-09: the redaction safety net (`sanitize` + `DENY_PATTERNS`) masks credential-shaped values (cookies, bearer tokens, JWTs, URL userinfo, credential assignments) so no secret/key value, proxy credential, cookie, or auth token can reach an emitted debug line"
  gaps_remaining: []
  regressions: []
---

# Phase 15: CLI --debug diagnostics Verification Report

**Phase Goal:** Operators can opt into richer ingest diagnostics without secret leakage or regressing default progress
**Verified:** 2026-10-04T08:46:35Z
**Status:** passed
**Re-verification:** Yes — after gap closure (plan 15-03)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1 / DBG-01: `ingestion-service` CLI accepts `--debug` and prints richer stage diagnostics on stderr | ✓ VERIFIED | `cli.py` declares `typer.Option("--debug", …, default False)`; `test_debug_success_emits_stage_lines` green; previously probe-verified |
| 2 | SC1 / D-04: a successful `--debug` run prints exactly one line per stage — captions, metadata, llm, persist — with the D-04 signals | ✓ VERIFIED | `test_debug_success_emits_all_stage_lines` + `test_debug_stage_lines_carry_allowlisted_signals` green; `ingest_pipeline.py` emits start→complete for all four stages |
| 3 | SC1 / D-01: debug is never written to stdout; stdout is byte-identical with and without `--debug` | ✓ VERIFIED | `StderrDiagnostics` emits via injected `emit` (`cli.py` `typer.echo(..., err=True)`) / injected stream / `sys.stderr` fallback only; `test_debug_success_emits_stage_lines` asserts `result.stdout.splitlines() == EXPECTED_SUCCESS_LINES` while `--debug` is on |
| 4 | SC3 / DBG-02: without `--debug`, stderr is empty and stdout matches the frozen success contract | ✓ VERIFIED | `NullDiagnostics` is a true no-op; `test_debug_off_is_byte_identical` asserts `result.stderr == ""` and the frozen lines; `test_cli_ingest_contract.py` green |
| 5 | SC3 / DBG-02: `IngestError.to_dict()` JSON envelope and exit codes remain unchanged with `--debug` off (and after debug lines when on) | ✓ VERIFIED | `test_cli_ingest_contract.py` (error paths) green; `test_debug_failure_prints_completed_and_failed` parses the last stderr line as the unchanged JSON envelope and asserts the debug lines precede it |
| 6 | SC2 / D-07: only allowlisted signal keys are emitted; full transcript/prompt bodies are never emitted (counts only) | ✓ VERIFIED | `ALLOWED_KEYS` filter in `stderr_diagnostics._emit`; `test_non_allowlisted_keys_are_dropped` green; `ingest_pipeline.py` emits `transcript_chars`/`transcript_words`/`response_chars`, never `transcript.text`/`body_markdown` |
| 7 | SC2 / D-08: exact runtime `Settings` secrets (`deepseek_api_key`, `supabase_secret_key`, `youtube_proxy_url`) are masked before emission | ✓ VERIFIED | `SecretRegistry` masking + `_settings_secrets` wiring (`cli.py`); `test_secret_registry_masks_exact_value` green; **committed** CLI test `test_debug_secret_registry_masks_settings_secret` seeds `Settings(deepseek_api_key=VIDEO_ID)` and asserts `video_id=[redacted]` with the sentinel absent from stderr |
| 8 | SC2 / D-07 / D-08 / D-09: the redaction safety net (`sanitize` + `DENY_PATTERNS`) masks credential-shaped values (cookies, bearer tokens, JWTs, URL userinfo, credential assignments) so no secret/key value, proxy credential, cookie, or auth token can reach an emitted debug line | ✓ VERIFIED | **Previously FAILED, now fixed (15-03).** Verifier re-probe in own process: `sanitize("secret_key=abcdef123456")`, `"access_token=…"`, `"client_secret=…"`, `"refresh_token=…"`, `"private_key=…"`, `"auth=…"` → exactly `[redacted]`; `sanitize("Bearer abc\ndef_secondhalf")` → exactly `[redacted]` (no `def_secondhalf` tail). Root cause fixed: non-word boundary `(?<![A-Za-z0-9_])` + compound alternatives, no trailing `\b`; control-char strip precedes the token patterns. Committed regressions: `test_sanitize_masks_underscore_compound_credentials`, `test_sanitize_masks_control_char_split_bearer`, `test_sanitize_underscore_compound_positive_control` |
| 9 | T-F / D-06: the metadata debug line exposes only `video_id` — never the author or the full source URL | ✓ VERIFIED | `test_debug_metadata_line_minimized` asserts the line lacks `"Rick Astley"` and the `source_url` string |
| 10 | T-G / D-10 / D-11: on `IngestError`, completed-stage lines plus the failed stage's `reason`, `exit_code`, and `elapsed_ms` are printed before the JSON envelope; `url`/`consistency` failures report `elapsed_ms=0` | ✓ VERIFIED | `test_debug_failure_prints_completed_and_failed`, `test_debug_url_failure_prints_stage_line_with_zero_elapsed`, `test_captions_failure_records_stage_failed`, `test_article_failure_records_stage_failed_after_completed_stages`, `test_invalid_url_records_stage_failed_without_stage_start` green |
| 11 | T-H / D-12: a pre-video `ConfigurationError`/`TemplateLoadError` prints a `stage=config` line and mints no `IngestError` JSON envelope | ✓ VERIFIED | `test_debug_config_error_line` + `test_debug_template_load_error_line` green; `test_config_error_without_debug_has_no_debug_line` green |
| 12 | T-D: `run_ingest_pipeline` depends only on the `StageDiagnostics` protocol and imports no `time`/`sys`/`typer`/`datetime` | ✓ VERIFIED | `application/ports/diagnostics.py` (Protocol + `NullDiagnostics`, no `Any`); AST guard `test_ingest_pipeline_retains_no_infra_imports` green |

**Score:** 12/12 truths verified (0 present, behavior-unverified; 0 failed)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `ingestion-service/src/ingestion_service/diagnostics/redaction.py` | `ALLOWED_KEYS`, `SecretRegistry`, `DENY_PATTERNS`, `sanitize` | ✓ VERIFIED | All symbols exist; **assignment boundary + control-char ordering now correct** (non-word boundary `(?<![A-Za-z0-9_])`, compound alternatives before bare `secret`/`token`, no trailing `\b`; `_CONTROL_CHARS` applied once before the token loop) |
| `ingestion-service/src/ingestion_service/application/ports/diagnostics.py` | `DebugValue`, `Clock`, `StageDiagnostics`, `NullDiagnostics` | ✓ VERIFIED | Protocol + runtime_checkable + no-op; no `Any` at the boundary |
| `ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py` | `SystemClock`, `StderrDiagnostics` (stderr-only, injected clock/emitter) | ✓ VERIFIED | Framework-free (no `typer`); emits via injected stream/emitter/`sys.stderr` fallback; allowlist filter + `sanitize` applied |
| `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` | All stage hooks + `stage_failed` attribution, infra-free | ✓ VERIFIED | Start/complete per stage; `stage_failed` in every mapping block; AST guard green |
| `ingestion-service/src/ingestion_service/cli.py` | `--debug` flag, sink wiring, `_settings_secrets`, `settings` in deps | ✓ VERIFIED | Flag explicit; sink rebuilt with secrets after `build_ingest_deps`; `settings=settings` in namespace |
| `ingestion-service/src/ingestion_service/tests_support/fakes.py` | `FakeClock`, `RecordingDiagnostics` | ✓ VERIFIED | Both present and used by tests |
| `tests/unit/test_cli_debug_diagnostics.py` | CLI on/off, per-stage, metadata, failure, config, registry e2e, AST guard | ✓ VERIFIED | All green; `test_debug_secret_registry_masks_settings_secret` (W-2) + tightened concrete-value assertions (W-3) added |
| `tests/unit/test_stderr_diagnostics.py` | Deterministic formatting, control chars, allowlist | ✓ VERIFIED | Exact-line `FakeClock` assertions green |
| `tests/unit/test_debug_redaction.py` | Registry + denylist + mask-not-fail + underscore/control-char regressions | ✓ VERIFIED | Underscore-compound parametrized case, positive control, control-char-split case, and behavioral plain-assignment test all green |

**Artifacts:** 9/9 exist; 9 fully substantive (the 2 previously-partial redaction artifacts are now complete).

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `cli.main` | `StderrDiagnostics`/`NullDiagnostics` | `debug` flag branch | ✓ WIRED | Sink rebuilt with `_settings_secrets(...)` after deps load |
| `cli.main` | `run_ingest_pipeline` | `diagnostics=diagnostics` | ✓ WIRED | Optional keyword absorbed by the use-case |
| `run_ingest_pipeline` | `StageDiagnostics` | `stage_started`/`stage_completed`/`stage_failed` guarded by `if diagnostics is not None` | ✓ WIRED | `RecordingDiagnostics` event-order tests green |
| `StderrDiagnostics` | `typer.echo(..., err=True)` | injected `emit` callable | ✓ WIRED | No stdout path; adapter stays `typer`-free |
| `cli` config-error handler | `diagnostics.config_error` → human text | `cli.py` handler | ✓ WIRED | `stage=config` line precedes unchanged human text; no JSON envelope |
| `_settings_secrets` | `SecretRegistry` → `sanitize` → stderr | `getattr(deps, "settings", None)` | ✓ WIRED | Committed CLI test `test_debug_secret_registry_masks_settings_secret` (`video_id=[redacted]`) |

**Wiring:** 6/6 connections verified.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase 15 named suite | `uv run pytest tests/unit/test_cli_debug_diagnostics.py tests/unit/test_stderr_diagnostics.py tests/unit/test_debug_redaction.py tests/unit/test_ingest_pipeline.py tests/unit/test_cli_ingest_contract.py tests/unit/test_ingest_error.py -q` | 56 passed in 2.43s | ✓ PASS |
| Full workspace suite (run once) | `uv run pytest -q` | 720 passed, 1 warning | ✓ PASS |
| Architecture guard (`typer` only in `cli.py`) | `uv run pytest tests/unit/test_data_collection_public_api.py -q` | 27 passed | ✓ PASS |
| Registry wiring end-to-end (`--debug` + `settings.deepseek_api_key == video_id`) | `test_debug_secret_registry_masks_settings_secret` | `video_id=[redacted]`; sentinel absent from stderr; stdout unchanged | ✓ PASS |
| Denylist credential-shape re-probe (failed truth #8) | verifier process probe (`sanitize(...)`) | `secret_key=`/`access_token=`/`client_secret=`/`refresh_token=`/`private_key=`/`auth=` → exactly `[redacted]`; `Bearer abc\ndef_secondhalf` → exactly `[redacted]` | ✓ PASS |
| Denylist regression shapes | verifier process probe | `api_key=`/`token=`/`secret=`/`Cookie:`/`Bearer …`/URL userinfo → `[redacted]` (userinfo host preserved) | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh` | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| DBG-01 | 15-01, 15-02, 15-03 | CLI accepts `--debug` and prints richer stage diagnostics without leaking secrets/proxy creds/cookies/full transcript bodies | ✓ SATISFIED | `--debug` + per-stage lines verified; allowlist + registry prevent leakage; denylist safety net now masks underscore-compound and control-char-split credentials (previously the sole blocker) |
| DBG-02 | 15-01, 15-02, 15-03 | With `--debug` off, staged progress / `IngestError.to_dict()` contracts unchanged | ✓ SATISFIED | `test_debug_off_is_byte_identical` + `test_cli_ingest_contract.py` green; stderr empty, stdout/exit codes frozen |

No orphaned Phase 15 IDs: all three plans declare `requirements: [DBG-01, DBG-02]`, and `REQUIREMENTS.md` maps exactly DBG-01/DBG-02 to Phase 15.

### Prohibitions

| Statement | Verdict | Evidence |
| --------- | ------- | -------- |
| Never print secret/key values, proxy credentials, cookies, or auth tokens | ✓ held | Allowlist + exact-value registry (committed CLI test) + denylist net now masks underscore-compound credentials and control-char-split tokens (verifier re-probe) |
| Never print full transcript or prompt bodies — only lengths/counters | ✓ held | `ingest_pipeline.py` emits `transcript_chars`/`transcript_words`/`response_chars`; bodies never passed to the sink |
| Never write debug output to stdout | ✓ held | Sink emits only via `err=True` echo / injected stream; stdout frozen in all `--debug` tests |
| Never fail or abort an ingest because of a redaction violation — mask or omit instead | ✓ held | `sanitize` never raises (`test_sanitize_never_raises_and_masks_on_violation`); `_emit` is unconditional in the use-case |
| Never enable debug via an environment variable; only the `--debug` flag | ✓ held | No env read in `cli.py`; only the `typer.Option("--debug")` branch constructs a live sink |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py` | 89-95 | Unquoted `key=value` values (I-1) | ℹ️ Info | An allowlisted string value containing spaces can render pseudo-fields |
| `ingestion-service/src/ingestion_service/cli.py` | 84-98 | `StderrDiagnostics` constructed twice (I-2) | ℹ️ Info | Pre-`build_ingest_deps` sink is intentional (config errors); duplication is easy to misread |
| `ingestion-service/src/ingestion_service/diagnostics/redaction.py` | 36, 88 | `MAX_VALUE_LENGTH` caps the whole line, not each value (I-3) | ℹ️ Info | A long `message` truncates mid-value and drops trailing fields |

**Anti-patterns:** 0 blockers, 0 warnings, 3 info. The previously-flagged blocker (assignment `\b` boundary), the control-char-ordering warning, the test-coverage warning, and I-4 (`_CONTROL_CHARS` identity check) are all resolved by 15-03. No `TBD`/`FIXME`/`XXX` debt markers in phase-modified files.

### Advisory (New Scope, Unevidenced)

None. No new-scope blocker was raised on this re-verification pass; the three remaining Info items above predate the gap-closure round, were already treated as non-blocking, and are not regressions (their files were not modified since the previous `verified:` timestamp).

### Human Verification Required

None — all must-have truths were checked programmatically (unit suite, AST guard, and verifier-run behavioral probes), including the previously-failed truth which is now re-probed in the verifier's own process.

### Gaps Summary

No gaps. The single previous blocker — the redaction denylist failing to mask underscore-compound credential names and control-char-split tokens — is closed by plan 15-03. Re-verified independently:

- `sanitize("secret_key=abcdef123456")` → `[redacted]`
- `sanitize("access_token=abcdef123456")` → `[redacted]`
- `sanitize("client_secret=abcdef123456")` → `[redacted]`
- `sanitize("refresh_token=abcdef123456")` → `[redacted]`
- `sanitize("private_key=abcdef123456")` → `[redacted]`
- `sanitize("auth=abcdef123456")` → `[redacted]`
- `sanitize("Bearer abc\ndef_secondhalf")` → `[redacted]` (no tail fragment)

The fix replaced the word-boundary assignment pattern with `(?<![A-Za-z0-9_])` + compound alternatives (no trailing `\b`) and moved the control-character strip ahead of the deny token patterns; committed regressions lock the exact shapes that previously slipped through. Regression check on the previously-passed items is clean: only `redaction.py`, `test_debug_redaction.py`, and `test_cli_debug_diagnostics.py` changed since the previous verification, and the named suite grew 47 → 56 while the full workspace suite grew 711 → 720, both green. DBG-01 and DBG-02 are now satisfied.

---

_Verified: 2026-10-04T08:46:35Z_
_Verifier: Claude (gsd-verifier)_
