---
status: complete
phase: 15-cli-debug-diagnostics
source: [15-01-SUMMARY.md, 15-02-SUMMARY.md, 15-03-SUMMARY.md]
started: 2026-10-04T12:06:00+03:00
updated: 2026-10-04T12:09:00+03:00
---

## Current Test

[testing complete]

## Tests

### 1. Confirm auto-covered deliverables
expected: |
  All Phase 15 coverage entries are backed by passing automated tests (49 passed).
  Confirm the opt-in --debug diagnostics behavior and the unchanged default
  stdout/stderr/JSON/exit-code contracts match expectations.
result: pass

### 2. [15-01/D1] Captions debug line on stderr, stdout byte-identical
expected: "--debug prints a secret-safe [HH:MM:SS] debug stage=captions line on stderr while stdout stays byte-identical"
result: pass
source: automated
coverage_id: 15-01-D1

### 3. [15-01/D2] --debug off keeps stderr empty and stdout frozen
expected: "Without --debug, stderr is empty and stdout matches the frozen success contract"
result: pass
source: automated
coverage_id: 15-01-D2

### 4. [15-01/D3] Redaction masks secrets/denylist shapes and never raises
expected: "Redaction masks exact secrets and denylist shapes (cookie/bearer/JWT/URL userinfo), strips control chars, and never raises on a violation"
result: pass
source: automated
coverage_id: 15-01-D3

### 5. [15-01/D4] Deterministic sink formatting against injected clock
expected: "Sink formats deterministic timestamp/elapsed_ms/allowlist output against an injected clock"
result: pass
source: automated
coverage_id: 15-01-D4

### 6. [15-01/D5] Use-case stays infra-free
expected: "Use-case stays infra-free: no time/sys/typer/datetime imports in run_ingest_pipeline"
result: pass
source: automated
coverage_id: 15-01-D5

### 7. [15-02/D1] Full per-stage success lines, stdout byte-identical
expected: "Successful --debug prints one line per stage (captions/metadata/llm/persist) with D-04 signals while stdout stays byte-identical"
result: pass
source: automated
coverage_id: 15-02-D1

### 8. [15-02/D2] Metadata line exposes only video_id
expected: "The metadata debug line exposes only video_id — never the author or the full source URL"
result: pass
source: automated
coverage_id: 15-02-D2

### 9. [15-02/D3] Failed runs print completed + failed stage detail
expected: "Failed runs print completed-stage lines plus the failed stage's reason/exit_code/elapsed_ms before the unchanged JSON envelope"
result: pass
source: automated
coverage_id: 15-02-D3

### 10. [15-02/D4] Pre-video config/template errors emit stage=config
expected: "Pre-video ConfigurationError/TemplateLoadError prints a stage=config line before the human text and mints no IngestError JSON envelope"
result: pass
source: automated
coverage_id: 15-02-D4

### 11. [15-02/D5] Pipeline emits stage events in order
expected: "Pipeline emits start/complete (and fail) events in stage order, with persist completion carrying the PersistResult identifiers"
result: pass
source: automated
coverage_id: 15-02-D5

### 12. [15-02/D6] --debug off leaves all contracts unchanged
expected: "With --debug off, stdout/stderr, the JSON envelope, and exit codes are unchanged (including the config-error human-text path)"
result: pass
source: automated
coverage_id: 15-02-D6

### 13. [15-03/D1] Underscore-compound credentials mask fully
expected: "Underscore-compound credential assignments mask to exactly [redacted]"
result: pass
source: automated
coverage_id: 15-03-D1

### 14. [15-03/D2] Control-char-split Bearer masks fully
expected: "Control-char-split Bearer token masks fully (no tail fragment survives)"
result: pass
source: automated
coverage_id: 15-03-D2

### 15. [15-03/D3] Plain assignment shapes still mask (no regression)
expected: "Plain assignment shapes (api_key/token/secret) still mask — no regression"
result: pass
source: automated
coverage_id: 15-03-D3

### 16. [15-03/D4] Settings secret registry wiring end-to-end
expected: "Settings secret registry wiring end-to-end (Settings -> _settings_secrets -> SecretRegistry -> sanitize -> stderr)"
result: pass
source: automated
coverage_id: 15-03-D4

### 17. [15-03/D5] Stage lines assert concrete signal values
expected: "Stage lines assert concrete signal values (rank/batch_id/material_id/already_saved/template/response_chars)"
result: pass
source: automated
coverage_id: 15-03-D5

## Summary

total: 17
passed: 17
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
