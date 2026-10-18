---
phase: 07-captions-adapter
plan: 03
subsystem: ingestion
tags: [VideoMetadataProvider, YouTubeOEmbedAdapter, MetadataError, map_metadata_error, FakeVideoMetadataProvider, YOUTUBE_PROXY_URL, httpx]

requires:
  - phase: 07-captions-adapter
    provides: CaptionsError taxonomy + FakeTranscriptProvider.failures (07-02) + SOCKS deps/integration marker (07-01)
provides:
  - VideoMetadataProvider Protocol (async get(video_id) -> VideoMetadata)
  - YouTubeOEmbedAdapter with canonical watch URL + required author_name
  - MetadataError taxonomy + map_metadata_error → IngestError(stage=metadata)
  - FakeVideoMetadataProvider (D-26) parallel to transcript fake
  - data_collection.__all__ exactly seven names including VideoMetadataProvider
  - Settings.youtube_proxy_url + composition client factories + gated live stubs + runbook
affects: [08-llm, 09-persist, 10-cli]

actuals:
  tokens: 14000
  tasks: 4
  commits: 9

tech-stack:
  added: []
  patterns: [oEmbed canonical URL construction, MetadataError→IngestError two-hop, Settings.from_env proxy injection, path-explicit integration gate]

key-files:
  created:
    - data-collection/src/data_collection/ports/video_metadata_provider.py
    - data-collection/src/data_collection/adapters/youtube_oembed.py
    - data-collection/src/data_collection/errors/metadata.py
    - ingestion-service/src/ingestion_service/mapping/metadata.py
    - ingestion-service/src/ingestion_service/composition/settings.py
    - ingestion-service/src/ingestion_service/composition/clients.py
    - ingestion-service/src/ingestion_service/composition/__init__.py
    - tests/unit/test_youtube_oembed_adapter.py
    - tests/unit/test_metadata_error_mapping.py
    - tests/unit/test_fake_video_metadata_provider.py
    - tests/unit/test_ingestion_settings.py
    - tests/integration/test_youtube_captions_live.py
    - tests/integration/test_youtube_oembed_live.py
  modified:
    - data-collection/src/data_collection/ports/__init__.py
    - data-collection/src/data_collection/__init__.py
    - data-collection/src/data_collection/tests_support/fakes.py
    - ingestion-service/src/ingestion_service/mapping/__init__.py
    - tests/unit/test_data_collection_public_api.py
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "Adapter builds canonical https://www.youtube.com/watch?v={id}; oEmbed endpoint fixed — no operator URL reaches HTTP (D-22, T-07-SSRF)"
  - "Missing/blank author_name → MetadataInvalidResponse; no fabricated author (D-23)"
  - "Base/unknown MetadataError maps to metadata_unavailable (not a fourth reason code)"
  - "07-01 httpx[socks]/requests[socks] + integration marker verified present — not re-added (D-18, D-20)"

patterns-established:
  - "Pattern: VideoMetadataProvider mirrors TranscriptProvider (async get(video_id))"
  - "Pattern: composition/clients.py builds YouTubeTranscriptApi(GenericProxyConfig) + httpx.AsyncClient(proxy=) when YOUTUBE_PROXY_URL set"
  - "Pattern: live stubs under tests/integration skip unless RUN_YOUTUBE_INTEGRATION=1; documented command is path-explicit"

requirements-completed: [CAP-01, CAP-02]

coverage:
  - id: D1
    description: "VideoMetadataProvider + YouTubeOEmbedAdapter canonical URL, required author, published_at=None, fail-closed MetadataError"
    requirement: CAP-01
    verification:
      - kind: unit
        ref: "tests/unit/test_youtube_oembed_adapter.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "map_metadata_error stage=metadata locked reasons + context allowlist redaction"
    requirement: CAP-02
    verification:
      - kind: unit
        ref: "tests/unit/test_metadata_error_mapping.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "FakeVideoMetadataProvider failures catalog (D-26); 07-02 FakeTranscriptProvider.failures untouched"
    requirement: CAP-02
    verification:
      - kind: unit
        ref: "tests/unit/test_fake_video_metadata_provider.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_fake_transcript_provider_failures.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "data_collection.__all__ exactly seven names including VideoMetadataProvider; negatives hide fakes/adapters/errors"
    requirement: CAP-01
    verification:
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Settings.youtube_proxy_url + client factories; 07-01 SOCKS/marker verify-only; runbook + gated live stubs"
    requirement: CAP-01
    verification:
      - kind: unit
        ref: "tests/unit/test_ingestion_settings.py"
        status: pass
      - kind: other
        ref: "uv run pytest tests/integration -q (2 skipped)"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-09-26
status: complete
---

# Phase 7 Plan 03: Metadata Port / oEmbed / Settings Summary

**VideoMetadataProvider + YouTubeOEmbedAdapter ship with fail-closed MetadataError mapping, seven-name public barrel, and composition-injected YOUTUBE_PROXY_URL — Phase 7 captions+oEmbed complete.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-26T19:10:49Z
- **Completed:** 2026-09-26T19:19:04Z
- **Tasks:** 4
- **Files modified:** 19

## Accomplishments

- `VideoMetadataProvider` Protocol + `YouTubeOEmbedAdapter` build canonical watch URL, require non-blank `author_name`, set `published_at=None`, and raise `MetadataUnavailable` / `MetadataNetworkError` / `MetadataInvalidResponse` with no fabricated author
- `map_metadata_error` → `IngestError(stage="metadata")` with locked reasons + allowlisted context; `FakeVideoMetadataProvider` (D-26) added without reworking D-15 transcript failures
- `data_collection.__all__` grew to exactly seven names; fakes/adapters/error classes stay off the root barrel
- `Settings.from_env` + `clients.py` inject optional proxy; 07-01 SOCKS extras and `integration` marker confirmed present; runbook documents path-explicit live command

## Task Commits

1. **Task 1: VideoMetadataProvider + YouTubeOEmbedAdapter + MetadataError** — `78063f9` (test) / `de3b962` (feat)
2. **Task 2: map_metadata_error + FakeVideoMetadataProvider** — `4bae1e3` (test) / `532a5a5` (feat)
3. **Task 3: seven-name public __all__** — `4763ebc` (test) / `b1ff98b` (feat)
4. **Task 4: Settings/proxy + live stubs + runbook** — `5343b83` (test) / `fc41007` (feat)

**Plan metadata:** (this commit)

## Deviations from Plan

None - plan executed exactly as written.

**Note (out of scope):** Full `uv run pytest` still reports 1 pre-existing failure in `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` (`sent_at`/`week_label` extras) — unrelated to 07-03; confirmed failing without this plan's changes. All 07-03 plan verification commands and D-15 regression tests pass.

**Total deviations:** 0 auto-fixed. **Impact:** none on plan deliverables.

## Issues Encountered

None for plan scope. Pre-existing admin shortlist assertion drift noted above.

## User Setup Required

None — `user_setup: []`. Optional operator config: `YOUTUBE_PROXY_URL` and `RUN_YOUTUBE_INTEGRATION=1` documented in runbook §1 / §5c.

## Next Phase Readiness

Phase 7 plans 01–03 complete. Ready for `/gsd-verify-work 7` then Phase 8 (DeepSeek article & templates). Both ports + error mappers + Settings/proxy are available for CLI composition in Phase 10.

## Self-Check: PASSED

- [x] key-files.created exist on disk
- [x] `git log --oneline --grep="07-03"` returns ≥1 commit (8 task commits + this docs commit)
- [x] Plan `<verification>` unit suite for 07-03 files: 51 passed
- [x] Acceptance criteria for Tasks 1–4 re-checked (rg guards, integration collect/skip, SOCKS/marker verify-only)
