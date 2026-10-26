---
phase: "15"
slug: "cli-debug-diagnostics"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-04"
updated: "2026-10-04"
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (dev group `>=8.3.0`) + `typer.testing.CliRunner` (Click 8.5.0) |
| **Config file** | root `pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`, `pythonpath = ["."]`) |
| **Quick run command** | `uv run pytest tests/unit/test_cli_debug_diagnostics.py -q` |
| **Full suite command** | `uv run pytest -q` (measured: **720 passed in ~5.3s**) |
| **Estimated runtime** | ~6 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/test_cli_debug_diagnostics.py tests/unit/test_debug_redaction.py tests/unit/test_stderr_diagnostics.py -q`
- **After every plan wave:** Run `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_ingest_pipeline.py tests/unit/test_ingest_error.py -q`
- **Before `/gsd-verify-work`:** Full suite must be green (`uv run pytest -q`, ≥684 tests)
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

*Task IDs reconcile to PLAN task IDs after plan landing. Status audited 2026-10-04 against the full suite (720 passed).*

| Req ID | Behavior | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|--------|----------|------------|-----------------|-----------|-------------------|-------------|--------|
| DBG-01 | `--debug` emits per-stage stderr lines on success; stdout unchanged | T-15-01 | No secret/body in emitted line | unit (CLI) | `uv run pytest tests/unit/test_cli_debug_diagnostics.py::test_debug_success_emits_stage_lines -x` | ✅ | ✅ green |
| DBG-01 | sink formats exact `[HH:MM:SS] debug stage=…` lines with a fake clock | — | Deterministic, unit-testable timings | unit (sink) | `uv run pytest tests/unit/test_stderr_diagnostics.py -q` | ✅ | ✅ green |
| DBG-01 | pipeline emits start/complete/fail events in order (fakes) | — | Use-case stays infra-free | unit (use-case) | `uv run pytest tests/unit/test_ingest_pipeline.py -q` | ✅ | ✅ green |
| DBG-01 | redaction never leaks secrets/proxy creds/cookies/bodies; masks on violation | T-15-01 | Allowlist + SecretRegistry + denylist | unit (redaction + CLI) | `uv run pytest tests/unit/test_debug_redaction.py -q` | ✅ | ✅ green |
| DBG-01 | failure prints completed stages + failed reason + `elapsed_ms`, then JSON | T-15-02 | Reason/exit-code observable, no secret | unit (CLI) | `uv run pytest tests/unit/test_cli_debug_diagnostics.py::test_debug_failure_prints_completed_and_failed -x` | ✅ | ✅ green |
| DBG-01 | config error emits `stage=config` with no `IngestError` envelope | — | D-08 human-text contract preserved | unit (CLI) | `uv run pytest tests/unit/test_cli_debug_diagnostics.py::test_debug_config_error_line -x` | ✅ | ✅ green |
| DBG-02 | `--debug` off → stdout byte-identical, `stderr == ""` | — | Zero debug output (D-13) | unit (CLI) | `uv run pytest tests/unit/test_cli_debug_diagnostics.py::test_debug_off_is_byte_identical -x` | ✅ | ✅ green |
| DBG-02 | `IngestError.to_dict()` envelope unchanged | — | Error contract frozen | unit | `uv run pytest tests/unit/test_ingest_error.py -q` | ✅ | ✅ green |
| DBG-02 | existing stdout contract unchanged | — | Progress lines frozen | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_cli_debug_diagnostics.py` — CLI `--debug` on/off, success/failure/config
- [x] `tests/unit/test_debug_redaction.py` — allowlist / denylist / registry masking
- [x] `tests/unit/test_stderr_diagnostics.py` — formatter + `FakeClock` determinism
- [x] `tests/unit/test_ingest_pipeline.py` — extended with `RecordingDiagnostics` + `FakeClock` event-order test
- [x] `ingestion-service/src/ingestion_service/tests_support/fakes.py` — added `FakeClock` and `RecordingDiagnostics`
- [x] Framework install: none — pytest / `CliRunner` already present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | — | All phase behaviors have automated verification. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved

---

## Validation Audit 2026-10-04

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

State A audit (VALIDATION.md present). All 9 Per-Task Verification Map rows classified **COVERED** — each requirement maps to an existing, passing test (measured: full workspace suite `720 passed in 5.27s`). No gaps → auditor not spawned (workflow Step 3). Frontmatter advanced to `status: validated`, `nyquist_compliant: true`, `wave_0_complete: true`.
