---
phase: 11-address-tech-debt-captions-diagnostics-and-persist-error-cla
plan: 01
subsystem: testing
tags: [captions, ingest-error, cli, redaction, regression]

requires:
  - phase: 07-captions-adapter
    provides: CaptionsError taxonomy, map_captions_error, YouTubeTranscriptApiException catch
  - phase: 10-cli-composition-uat
    provides: CliRunner stderr JSON IngestError contract
provides:
  - CliRunner captions CookieInvalid/unknown → JSON stderr regression (CAP-02 / D-04 / D-05)
  - Mapper message + captions/URL allowlist freeze locks (D-01…D-03)
affects:
  - 11-02 persist classification
  - operator CLI diagnostics

actuals:
  tokens: 1341
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Regression-lock operator stderr JSON via CliRunner + FakeTranscriptProvider.failures"
    - "Freeze mapper allowlists with exact frozenset equality tests"

key-files:
  created: []
  modified:
    - tests/unit/test_cli_ingest_contract.py
    - tests/unit/test_captions_error_mapping.py
    - tests/unit/test_ingest_error.py

key-decisions:
  - "No production edits: Phase 7 catch chain + mapper already satisfy D-01…D-05; plan only added regression tests"
  - "Inject CookieInvalid path via base CaptionsError(exception_class=CookieInvalid) through FakeTranscriptProvider (adapter CookieInvalid case already locked in test_youtube_transcript_adapter)"

patterns-established:
  - "Captions-stage CliRunner failures assert stage/reason/message + absence of Traceback in combined output"

requirements-completed: [CAP-02]

coverage:
  - id: D1
    description: Captions CookieInvalid/unknown failure emits secret-safe JSON stderr (stage=captions, reason=unknown_captions_error) with no Traceback
    requirement: CAP-02
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py::test_cli_captions_cookie_invalid_unknown_json_stderr_no_traceback"
        status: pass
    human_judgment: false
  - id: D2
    description: Mapper message is reason+video_id only; captions/URL context allowlists frozen; proxy/SDK secrets redacted
    requirement: CAP-02
    verification:
      - kind: unit
        ref: "tests/unit/test_captions_error_mapping.py::test_map_captions_error_cookie_invalid_message_is_reason_and_video_id_only"
        status: pass
      - kind: unit
        ref: "tests/unit/test_captions_error_mapping.py::test_captions_context_allowlist_frozen"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingest_error.py::test_url_context_allowlist_frozen"
        status: pass
      - kind: unit
        ref: "tests/unit/test_youtube_transcript_adapter.py::test_adapter_maps_sdk_exception_to_captions_subtype[CookieInvalid]"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-10-02
status: complete
plan_head_before: b08b2500876b1ce95a1837d7617fadc13f19ed06
plan_head_after: 172feba24cd02b1b2454c4c0b71412ba8cdab03d
commits: 4
---

# Phase 11 Plan 01: Captions diagnostics tracer Summary

**CliRunner + mapper regression locks prove CookieInvalid/unknown captions failures stay secret-safe JSON on stderr with no traceback (CAP-02 / D-01…D-05).**

## Performance

- **Duration:** 4min
- **Started:** 2026-10-02T10:57:21Z
- **Completed:** 2026-10-02T11:01:00Z
- **Tasks:** 2/2
- **Files modified:** 3 (tests only)

## Accomplishments

- Locked end-to-end captions failure path: FakeTranscriptProvider CookieInvalid-mapped CaptionsError → stderr JSON `stage=captions` / `reason=unknown_captions_error` / message `captions unknown_captions_error for {video_id}`; no Traceback; no checkmarks.
- Froze D-01…D-03 mapper contracts: message shape for all locked reasons, CookieInvalid SDK-text discard, captions + URL `_CONTEXT_ALLOWLIST` exact frozensets; existing CAPTIONS_REASONS + CookieInvalid adapter cases remain green.
- No production changes required — Phase 7 hardening already in HEAD matched the plan’s “edit only if RED” gate.

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end captions CookieInvalid → JSON stderr unknown_captions_error** - `e87dadf` (test)
2. **Task 2: Lock captions mapper redaction and adapter CookieInvalid coverage** - `172feba` (test)

**Plan metadata:** `7762d38` (docs: complete plan)

_Note: `git rev-list` from `plan_head_before`..HEAD counts 4 commits because parallel 11-02 work landed on the same branch between the two 11-01 commits (`9375314`, `4c3e8a7`). This plan’s own commits are `e87dadf` and `172feba`._

## Files Created/Modified

- `tests/unit/test_cli_ingest_contract.py` — CliRunner captions unknown/CookieInvalid JSON stderr contract
- `tests/unit/test_captions_error_mapping.py` — message shape, CookieInvalid SDK discard, captions allowlist freeze
- `tests/unit/test_ingest_error.py` — URL context allowlist freeze

## Decisions Made

- Injected captions failure via `FakeTranscriptProvider.failures` with base `CaptionsError(..., exception_class="CookieInvalid")` rather than wiring the real adapter into CliRunner — adapter CookieInvalid→CaptionsError already covered in `test_youtube_transcript_adapter.py`.
- Left `youtube_transcript.py`, `mapping/captions.py`, and `mapping/url.py` untouched after GREEN regression tests (plan: production only if RED).

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as regression-lock; production files listed in plan were not modified because RED never proved an escape.

### Notable

**1. Immediate GREEN on new CliRunner/mapper assertions (behavior already in HEAD)**
- **Found during:** Task 1 and Task 2
- **Issue:** New tests passed on first run — Phase 7 CR-01/WR-01 catch + mapper already implement D-01…D-05.
- **Fix:** Committed tests as contract locks; skipped production edits per plan “only if RED”.
- **Files modified:** test files only
- **Commit:** `e87dadf`, `172feba`

## Auth Gates

None.

## Known Stubs

None.

## Threat Flags

None — no new endpoints, auth paths, or schema; tests only exercise existing CLI/mapper surfaces already covered by T-11-01.

## Verification Results

```text
uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_captions_error_mapping.py tests/unit/test_youtube_transcript_adapter.py -x
→ 48 passed
```

Tracer feedback gate: re-ran `test_cli_ingest_contract.py` after Task 1 — 7 passed; continued (HUMAN_VERIFY_MODE=end-of-phase, automated-only verify).

## Self-Check: PASSED

- FOUND: tests/unit/test_cli_ingest_contract.py
- FOUND: tests/unit/test_captions_error_mapping.py
- FOUND: tests/unit/test_ingest_error.py
- FOUND: 11-01-SUMMARY.md
- FOUND: commits e87dadf, 172feba
