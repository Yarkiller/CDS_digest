---
phase: 07-captions-adapter
plan: 01
subsystem: ingestion
tags: [youtube-transcript-api, ingestion-service, captions, url-parser, IngestError, uv-workspace]

requires:
  - phase: 06-ports-dtos
    provides: Transcript DTO + TranscriptProvider Protocol + FakeTranscriptProvider
provides:
  - ingestion-service uv workspace member depending on data-collection
  - extract_video_id allowlist parser + InvalidYouTubeUrl reason codes
  - IngestError/Stage + to_dict() operator envelope + map_url_error
  - YouTubeTranscriptAdapter (injected SDK, ru→en list-then-pick) + CaptionsEmpty / CaptionsNoPreferredLanguage
affects: [07-02 captions taxonomy, 07-03 oEmbed/metadata, 08-llm, 10-cli]

actuals:
  tokens: 8500
  tasks: 3
  commits: 5

tech-stack:
  added: [youtube-transcript-api>=1.2.0,<2, httpx[socks]==0.28.1, requests[socks], ingestion-service package]
  patterns: [injected SDK clients (no os.environ in adapters), list-then-pick language base, IngestError.to_dict envelope, map_url_error stage=url]

key-files:
  created:
    - ingestion-service/pyproject.toml
    - ingestion-service/src/ingestion_service/url.py
    - ingestion-service/src/ingestion_service/domain/errors.py
    - ingestion-service/src/ingestion_service/mapping/url.py
    - data-collection/src/data_collection/adapters/youtube_transcript.py
    - data-collection/src/data_collection/errors/captions.py
    - tests/unit/test_extract_video_id.py
    - tests/unit/test_ingest_error.py
    - tests/unit/test_youtube_transcript_adapter.py
  modified:
    - pyproject.toml
    - uv.lock
    - data-collection/pyproject.toml

key-decisions:
  - "List-then-pick (api.list + dialect base) over fetch(languages=…) for available_languages + rue/enm reject"
  - "Exact-netloc host allowlist (no endswith) for SSRF look-alike hosts"
  - "Explicit /live|/v|/e reject branch (D-02) even when fallthrough already failed closed"

patterns-established:
  - "Pattern: adapters take ready clients; composition owns proxy/env (D-17)"
  - "Pattern: data-collection raises CaptionsError subtypes; ingestion-service maps to IngestError(stage=…)"
  - "Pattern: asyncio.to_thread wraps sync youtube-transcript-api inside async get"

requirements-completed: [CAP-01, CAP-02]

coverage:
  - id: D1
    description: "ingestion-service workspace member + captions/SOCKS deps + integration marker"
    requirement: CAP-01
    verification:
      - kind: other
        ref: "uv sync && import ingestion_service / youtube_transcript_api / socks"
        status: pass
    human_judgment: false
  - id: D2
    description: "extract_video_id accept/reject allowlist matrix with stage=url mapping"
    requirement: CAP-01
    verification:
      - kind: unit
        ref: "tests/unit/test_extract_video_id.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingest_error.py#test_map_url_error_uses_exception_reason_and_stage_url"
        status: pass
    human_judgment: false
  - id: D3
    description: "IngestError.to_dict envelope + seven Stage Literal values"
    requirement: CAP-01
    verification:
      - kind: unit
        ref: "tests/unit/test_ingest_error.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "YouTubeTranscriptAdapter ru→en happy path + dialect base + fail-closed empty/non-preferred"
    requirement: CAP-02
    verification:
      - kind: unit
        ref: "tests/unit/test_youtube_transcript_adapter.py"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-09-26
status: complete
---

# Phase 07 Plan 01: Captions Adapter Tracer Summary

**ingestion-service workspace + extract_video_id allowlist + IngestError envelope + mocked YouTubeTranscriptAdapter (ru→en)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-26T18:56:55Z
- **Completed:** 2026-09-26T19:00:39Z
- **Tasks:** 3
- **Files modified:** 17

## Accomplishments

- Scaffolded `ingestion-service` as a uv workspace member; added `youtube-transcript-api`, `httpx[socks]`, `requests[socks]` to `data-collection`; registered pytest `integration` marker with unit-only `testpaths`
- Shipped CAP-01 tracer: `extract_video_id` → `video_id`, `map_url_error` → `IngestError(stage="url")`, injected `YouTubeTranscriptAdapter` returning `Transcript(language="ru")` when ru+en tracks exist
- Hardened URL matrix (≥12 accept / ≥10 reject) including look-alike hosts, noise query params, `-`/`_` ids, and explicit `/live|/v|/e` rejection

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold ingestion-service + deps + marker** - `8f9ff60` (chore)
2. **Task 2: Tracer slice (RED tests)** - `0f71a30` (test)
3. **Task 2: Tracer slice (GREEN impl)** - `caf8667` (feat)
4. **Task 2: captions docstring rg gate** - `dcb50cb` (refactor)
5. **Task 3: Harden URL accept/reject matrix** - `1e7c56b` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `ingestion-service/` — new workspace member (`url.py`, `domain/errors.py`, `mapping/url.py`)
- `data-collection/.../adapters/youtube_transcript.py` — injected-client captions adapter
- `data-collection/.../errors/captions.py` — `CaptionsError` / `CaptionsNoPreferredLanguage` / `CaptionsEmpty`
- `tests/unit/test_extract_video_id.py` / `test_ingest_error.py` / `test_youtube_transcript_adapter.py`
- `pyproject.toml` / `uv.lock` / `data-collection/pyproject.toml`

## Decisions Made

- Kept list-then-pick as the only captions path so `available_languages` and dialect bases work (RESEARCH A1)
- Host allowlist is exact netloc membership (blocks `youtube.com.evil.test`)
- Explicit deferred-form branch for `/live|/v|/e` (D-02) for maintainability

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Docstring contained the word `stage`**
- **Found during:** Task 2 acceptance (`rg stage captions.py` must be empty)
- **Issue:** Module docstring said "pipeline stage vocabulary"
- **Fix:** Reworded docstring; committed separately
- **Files modified:** `data-collection/src/data_collection/errors/captions.py`
- **Verification:** `rg stage` on file → no match; suite green
- **Committed in:** `dcb50cb`

**2. [TDD note] Task 3 RED did not fail**
- **Found during:** Task 3 (harden matrix)
- **Issue:** Tracer `url.py` already satisfied the expanded accept/reject rows
- **Fix:** Kept expanded tests as contract documentation; added explicit deferred-form reject branch
- **Files modified:** `tests/unit/test_extract_video_id.py`, `ingestion-service/.../url.py`
- **Verification:** 35 extract_video_id tests + full unit suite (minus pre-existing) green
- **Committed in:** `1e7c56b`

---

**Total deviations:** 2 auto-fixed (1 acceptance gate, 1 TDD RED-already-green)
**Impact on plan:** No scope creep; CAP-01 tracer and hardened matrix shipped as specified.

## Issues Encountered

- Pre-existing failure in `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` (response includes extra `sent_at`/`week_label` vs fixture) — unrelated dirty/working-tree drift; not introduced by 07-01. Plan verification ran targeted 07-01 files + full suite with that file ignored (324 passed).
- gsd-tools `state.*` / `roadmap.update-plan-progress` hit EPERM on atomic rename of STATE.md / ROADMAP.md (file lock). Retried once; updated both files via direct edit instead. Noted per sequential-executor guidance.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for `07-02` (full CaptionsError taxonomy + SDK→error mapping + `map_captions_error`)
- CAP-02 live persist spy remains deferred to Phase 9/10 (D-14)
- Shared requirement IDs CAP-01/CAP-02: mark Complete only when sibling plans finish (`requirements.ready-ids`)

## Self-Check: PASSED

- Key files present on disk
- `git log --grep=07-01` → 5 commits
- Tracer pytest files: 45 passed
- Acceptance rg gates: no `os.environ`/`os.getenv` in adapters/; no `stage` in captions.py

---
*Phase: 07-captions-adapter*
*Completed: 2026-09-26*
