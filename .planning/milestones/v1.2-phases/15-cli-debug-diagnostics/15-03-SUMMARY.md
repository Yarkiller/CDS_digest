---
phase: 15-cli-debug-diagnostics
plan: 03
subsystem: cli
tags: [typer, diagnostics, redaction, ports-and-adapters, tdd, gap-closure]

requires:
  - phase: 15-cli-debug-diagnostics
    provides: "plan 15-01/15-02 diagnostics port, StderrDiagnostics sink, redaction module, --debug flag, full stage signals"
provides:
  - "Underscore-compound credential masking in the DENY_PATTERNS safety net (secret_key/access_token/client_secret/refresh_token/private_key/auth)"
  - "Control characters stripped BEFORE the deny token patterns (no partial-mask tail leak)"
  - "Committed underscore-compound + control-char-split regression cases"
  - "Registry wiring covered end-to-end (Settings -> _settings_secrets -> SecretRegistry -> stderr)"
affects: [15-cli-debug-diagnostics verification, 16-pipe-01-mvp-config-ui]

actuals:
  tokens: 1650
  tasks: 3
  commits: 3

commits: 3
plan_head_before: e46d0f843adf60f8bc2f8dc1702b5ab1d7550598
plan_head_after: 325dfad3e01a58f877c426249a08477b5356fcaa

tech-stack:
  added: []
  patterns:
    - "Denylist assignment shape: a non-word left boundary (?<![A-Za-z0-9_]) plus compound alternatives ordered before the bare secret/token, with NO trailing word boundary"
    - "Control-character strip applied once as the first step before an ordered token-pattern loop (no fragile identity branch)"

key-files:
  created: []
  modified:
    - ingestion-service/src/ingestion_service/diagnostics/redaction.py
    - tests/unit/test_debug_redaction.py
    - tests/unit/test_cli_debug_diagnostics.py

key-decisions:
  - "Removed the trailing \\b after the keyword group and added compound alternatives (access_token/refresh_token/client_secret/secret_key/private_key/auth) before the bare secret/token — `_` is a word char, so the old boundary could never match (T-15-07)"
  - "Applied the control-character strip as a dedicated first step before the token patterns and dropped _CONTROL_CHARS from DENY_PATTERNS, deleting the fragile `pattern is _CONTROL_CHARS` identity branch (T-15-08)"

patterns-established:
  - "Redaction denylist assignment alternative set covers the env-var spelling of proxy credentials/cookies/auth tokens, not just the bare keyword"

requirements-completed: [DBG-01, DBG-02]

coverage:
  - id: D1
    description: "Underscore-compound credential assignments mask to exactly [redacted]"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_debug_redaction.py#test_sanitize_masks_underscore_compound_credentials"
        status: pass
    human_judgment: false
  - id: D2
    description: "Control-char-split Bearer token masks fully (no tail fragment survives)"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_debug_redaction.py#test_sanitize_masks_control_char_split_bearer"
        status: pass
    human_judgment: false
  - id: D3
    description: "Plain assignment shapes (api_key/token/secret) still mask — no regression"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_debug_redaction.py#test_sanitize_underscore_compound_positive_control"
        status: pass
    human_judgment: false
  - id: D4
    description: "Settings secret registry wiring end-to-end (Settings -> _settings_secrets -> SecretRegistry -> sanitize -> stderr)"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_secret_registry_masks_settings_secret"
        status: pass
    human_judgment: false
  - id: D5
    description: "Stage lines assert concrete signal values (rank/batch_id/material_id/already_saved/template/response_chars)"
    requirement: DBG-01
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_debug_diagnostics.py#test_debug_stage_lines_carry_allowlisted_signals"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-10-04
status: complete
---

# Phase 15 Plan 03: CLI --debug diagnostics (gap closure — redaction safety net) Summary

**The assignment denylist now masks underscore-compound credentials (`secret_key`/`access_token`/`client_secret`/`refresh_token`/`private_key`/`auth` → `[redacted]`) and strips control characters before the token patterns, closing the verifier's single blocker with committed regressions plus the review's W-2/W-3 coverage.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-10-04T11:38:00+03:00
- **Completed:** 2026-10-04T11:50:00+03:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- `redaction.sanitize` now masks all six verifier reproductions to exactly `[redacted]`; the control-char-split `Bearer abc\ndef_secondhalf` no longer leaks the `def_secondhalf` tail.
- The assignment pattern uses a non-word left boundary `(?<![A-Za-z0-9_])` with compound alternatives ordered before the bare `secret`/`token`, and drops the trailing `\b` that `_`-adjacency defeated (T-15-07).
- Control characters are stripped once, before the deny token patterns; `_CONTROL_CHARS` left `DENY_PATTERNS` and the `pattern is _CONTROL_CHARS` identity branch is gone (T-15-08).
- W-2: a CLI test seeds `Settings(deepseek_api_key=VIDEO_ID)` and proves `Settings → _settings_secrets → SecretRegistry → sanitize → stderr` (`video_id=[redacted]`, sentinel absent).
- W-3: stage-line assertions now check concrete values; the shape-only denylist test was replaced with behavioral `sanitize` coverage.

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — underscore-compound + control-char-split tests** - `6e9fadb` (test)
2. **Task 2: GREEN — assignment boundary + control-char ordering fix** - `d71e7fc` (feat)
3. **Task 3: W-2 registry e2e + W-3 concrete-value coverage** - `325dfad` (test)

**Plan metadata:** final `docs(15-03)` metadata commit (SUMMARY + STATE + ROADMAP).

_Note: TDD RED→GREEN; Task 3 is characterization/tightening with no production change._

## Files Created/Modified
- `ingestion-service/src/ingestion_service/diagnostics/redaction.py` — assignment denylist boundary + compound names; control-char strip reordered before token patterns; `_CONTROL_CHARS` removed from `DENY_PATTERNS`
- `tests/unit/test_debug_redaction.py` — underscore-compound parametrized negative case, positive control, control-char-split case; behavioral plain-assignment test replaces the shape-only test
- `tests/unit/test_cli_debug_diagnostics.py` — `test_debug_secret_registry_masks_settings_secret` (W-2); concrete-value assertions in `test_debug_stage_lines_carry_allowlisted_signals` (W-3)

## Decisions Made
- The compound alternatives are listed before the bare `secret`/`token` so `secret_key`/`access_token` are consumed as a single unit (regex alternation is ordered).
- The control-character strip runs immediately after `registry.mask` and before the token loop; `registry.mask` order relative to the strip is unchanged (redaction-py contract preserved).
- No production change for Task 3 — it is characterization + tightening only.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The TDD RED-evidence checker (`gsd-tools check tdd-red-evidence`) is Node/TAP-oriented: it recognises `node --test` TAP summaries or Surefire XML. The generated pytest JUnit XML is parsed via the Surefire path, but the parser's `name="…"` regex collides with pytest's `classname="…"` attribute, so every failing test resolves to the module name and the target test cannot match (`INVALID_RED: no_target_test_failure`). The checker therefore cannot validate a pytest RED run; RED-first discipline was instead observed directly — `uv run pytest tests/unit/test_debug_redaction.py -q` showed **7 failed** (six underscore-compound params + the control-char-split case) on the intended assertions before the production edit, then **31 passed** after.
- No blocking impact; the plan's Task 1 `<verify>` (observe the expected failures) was met.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The verifier's single blocker is closed: all six reproductions mask to `[redacted]`, and the regression tier now exercises the exact shapes that slipped through.
- Full workspace suite green at **720 passed** (baseline 711 + 9 net new assertions); `test_cli_ingest_contract.py` / `test_ingest_error.py` unchanged (15 passed) — the stdout/JSON/exit-code contracts are untouched.
- Phase 15 has 3/3 plans complete; ready for `/gsd-verify-work 15` re-verification.

---
*Phase: 15-cli-debug-diagnostics*
*Completed: 2026-10-04*

## Self-Check: PASSED

- All 3 task commits present (`6e9fadb`, `d71e7fc`, `325dfad`); measured ledger `e46d0f8..325dfad` = 3 commits.
- `uv run pytest tests/unit/test_debug_redaction.py tests/unit/test_stderr_diagnostics.py tests/unit/test_cli_debug_diagnostics.py -q` → 31 passed.
- `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_ingest_error.py -q` → 15 passed.
- `uv run pytest -q` → 720 passed (baseline 711 + 9 net new).
- Six verifier reproductions all return `[redacted]`; no allowlist/SecretRegistry/sink/use-case/CLI/stdout-contract files touched.
