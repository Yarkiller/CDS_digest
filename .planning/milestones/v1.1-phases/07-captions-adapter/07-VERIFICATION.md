---
phase: 07-captions-adapter
verified: 2026-09-26T19:30:05Z
status: passed
score: 12/12 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 26
  total: 26
  not_honored: []
advisory_review:
  source: 07-REVIEW.md
  status: issues_found
  critical: 1
  warning: 4
  info: 3
  note: "CR-01 message-field credential leak (context allowlist OK). WR-01 Cookie* SDK escape. WR-02 map_url_error raw URL. WR-03 snippet join ''. WR-04 oEmbed non-200→MetadataUnavailable. None fail CAP-01/CAP-02 or roadmap SCs; harden before Phase 10 CLI emits to_dict()."
human_verification: []
next_action: "Phase 7 goal achieved. Proceed to Phase 8 (DeepSeek Article & Templates)."
next_command: "/gsd-plan-phase 8"
---

# Phase 7: Captions Adapter Verification Report

**Phase Goal:** Operator can resolve a YouTube URL to captions, or get a loud captions-stage failure with no database side effects  
**Verified:** 2026-09-26T19:30:05Z  
**Status:** passed  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Roadmap Success Criteria (non-negotiable) plus distinct plan must-haves from 07-01…07-03. Plan truths that only restate a roadmap SC are scored under that SC.

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Given a YouTube URL, captions path resolves `video_id` and returns a `Transcript` preferring `ru` then `en` (Roadmap SC-1 / CAP-01) | ✓ VERIFIED | `extract_video_id` accept matrix; `YouTubeTranscriptAdapter` prefers ru over en, normalizes `ru-RU`/`en-US`; `test_youtube_transcript_adapter` + `test_extract_video_id` green |
| 2 | Missing, disabled, or blocked captions exit non-zero with `stage=captions` (Roadmap SC-2 / CAP-02) | ✓ VERIFIED | Full taxonomy + SDK mapping; `map_captions_error` → `stage="captions"`, `ok=False`, `exit_code=1`; nine locked D-10 reasons including `captions_disabled` / `youtube_blocked` / `no_captions` |
| 3 | Captions failure writes zero database rows — adapter/unit proof now; live persist spy Phase 9/10 (Roadmap SC-3 / D-14) | ✓ VERIFIED | No persist writers/migrations this phase; failures raise `CaptionsError` / never return `Transcript`; ROADMAP Phase 9 note has `persist.calls == []`; migrations still end at `006_…` |
| 4 | `extract_video_id` allowlist accepts watch/youtu.be/shorts/embed/bare-id; rejects playlists, channels, look-alikes, `/live|/v|/e`, bad ids; `map_url_error` → `stage=url` (D-01…D-05) | ✓ VERIFIED | `test_extract_video_id.py` (≥12 accept / ≥10 reject); `map_url_error` uses exception reason; look-alike hosts rejected |
| 5 | `IngestError` + seven-value `Stage` Literal + `to_dict()` envelope live in ingestion-service (D-11, D-13) | ✓ VERIFIED | `domain/errors.py`; `test_ingest_error.py` asserts keys, context omission, `exit_code=1` |
| 6 | Full `CaptionsError` taxonomy (9 types) + adapter SDK→error mapping; no SDK type escapes handled paths; no `Transcript` on failure (D-10, D-12, D-19) | ✓ VERIFIED | Nine subtypes on disk; parametrized SDK/requests cases in `test_youtube_transcript_adapter.py`; `IpBlocked`≠disabled; `PoTokenRequired`→`CaptionsBotChallenge`; `YouTubeRequestFailed`→network |
| 7 | `map_captions_error` locked nine D-10 reasons; context allowlist redacts credentialed proxy keys (D-10, D-13) | ✓ VERIFIED | `CAPTIONS_REASONS` exact set; redaction + envelope tests in `test_captions_error_mapping.py` |
| 8 | `FakeTranscriptProvider(failures=…)` additive; Phase 6 success+spy unchanged (D-15) | ✓ VERIFIED | `test_fake_transcript_provider_failures.py`; raised error maps to `stage=captions` |
| 9 | `VideoMetadataProvider` + `YouTubeOEmbedAdapter`: canonical watch URL, required author, `published_at=None`, fail-closed `MetadataError` (D-21…D-23, D-25) | ✓ VERIFIED | `test_youtube_oembed_adapter.py`; no fabricated author; 404/403/timeout/blank author covered |
| 10 | `map_metadata_error` → `stage=metadata` + `FakeVideoMetadataProvider` (D-26); seven-name public `__all__` (D-21) | ✓ VERIFIED | Metadata mapper + fake tests; `__all__` exactly seven including `VideoMetadataProvider` |
| 11 | `Settings.youtube_proxy_url` + composition client factories; adapters have no `os.environ` (D-16, D-17) | ✓ VERIFIED | `test_ingestion_settings.py`; `rg` clean on adapters for env reads |
| 12 | Workspace deps (`youtube-transcript-api`, `httpx[socks]`, `requests[socks]`), `integration` marker, unit-only `testpaths`, path-explicit runbook live command (D-18, D-20, D-24) | ✓ VERIFIED | `data-collection/pyproject.toml` + root pytest ini; runbook has `RUN_YOUTUBE_INTEGRATION=1 uv run pytest tests/integration -m integration`; gated stubs under `tests/integration/` |

**Score:** 12/12 truths verified (0 present, behavior-unverified)

### Deferred Items

- CAP-02 live zero-row spy (`persist.calls == []`) — Phase 9/10 (D-14; ROADMAP note present)
- Typer one-shot / DeepSeek / persist — Phases 8–10
- Advisory hardenings from 07-REVIEW (CR-01 message redaction, WR-01…WR-04) — recommended before Phase 10 operator JSON emission; do not block Phase 7 goal

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------- | ------- |
| `ingestion-service/.../url.py` | `extract_video_id` + `InvalidYouTubeUrl` | ✓ VERIFIED | Allowlist + reason codes |
| `ingestion-service/.../mapping/url.py` | `map_url_error` → `stage=url` | ✓ VERIFIED | Present |
| `ingestion-service/.../domain/errors.py` | `IngestError` + `Stage` | ✓ VERIFIED | Seven stages; `to_dict()` |
| `ingestion-service/.../mapping/captions.py` | `map_captions_error` + D-10 reasons | ✓ VERIFIED | Nine locked codes |
| `ingestion-service/.../mapping/metadata.py` | `map_metadata_error` | ✓ VERIFIED | `stage=metadata` |
| `ingestion-service/.../composition/settings.py` | `Settings.from_env` proxy | ✓ VERIFIED | `YOUTUBE_PROXY_URL` |
| `ingestion-service/.../composition/clients.py` | Proxy-aware client factories | ✓ VERIFIED | Injects ready clients |
| `data-collection/.../errors/captions.py` | Full CaptionsError taxonomy | ✓ VERIFIED | 9 types; no `stage` |
| `data-collection/.../errors/metadata.py` | MetadataError taxonomy | ✓ VERIFIED | 3 subtypes + base |
| `data-collection/.../adapters/youtube_transcript.py` | Injected-client captions adapter | ✓ VERIFIED | list-then-pick; SDK map |
| `data-collection/.../adapters/youtube_oembed.py` | oEmbed adapter | ✓ VERIFIED | Canonical URL; required author |
| `data-collection/.../ports/video_metadata_provider.py` | Protocol `get(video_id)` | ✓ VERIFIED | Mirrors transcript port |
| `data-collection/.../__init__.py` | Seven-name public barrel | ✓ VERIFIED | Exact seven names |
| `data-collection/.../tests_support/fakes.py` | Both fakes + failure catalogs | ✓ VERIFIED | D-15 + D-26 |
| `docs/agents/local-platform-runbook.md` | Proxy + live command | ✓ VERIFIED | Path-explicit integration |
| `tests/integration/test_youtube_*_live.py` | Gated stubs | ✓ VERIFIED | Skip unless env set |
| Phase-7 unit tests (10 files) | Behavioral coverage | ✓ VERIFIED | 130 passed this run |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | ---- | ------ | -------- |
| `InvalidYouTubeUrl` | `IngestError(stage=url)` | `map_url_error` | ✓ WIRED | Production-owned reasons |
| `YouTubeTranscriptAdapter.get` | `Transcript` | `TranscriptProvider` | ✓ WIRED | async + `asyncio.to_thread` |
| SDK / requests exceptions | `CaptionsError` subtype | adapter `except` chain | ✓ WIRED | Handled catalog mapped |
| `CaptionsError` | `IngestError(stage=captions)` | `map_captions_error` | ✓ WIRED | Locked D-10 reasons |
| `YouTubeOEmbedAdapter.get` | `VideoMetadata` | `VideoMetadataProvider` | ✓ WIRED | Canonical watch URL |
| `MetadataError` | `IngestError(stage=metadata)` | `map_metadata_error` | ✓ WIRED | Locked metadata reasons |
| `Settings.youtube_proxy_url` | ready SDK/httpx clients | `composition/clients.py` | ✓ WIRED | Adapters never read env |
| `FakeTranscriptProvider.failures` | `CaptionsError` raise | tests_support | ✓ WIRED | Phase 9/10 double ready |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `extract_video_id` | `video_id` | URL / bare id string | Yes (parsed allowlist) | ✓ FLOWING |
| `YouTubeTranscriptAdapter` | `Transcript` | mocked SDK tracks | Yes (joined snippet text + language base) | ✓ FLOWING |
| `map_captions_error` | `IngestError.to_dict()` | `CaptionsError` subtype | Yes (locked stage/reason/exit_code) | ✓ FLOWING |
| `YouTubeOEmbedAdapter` | `VideoMetadata` | stub httpx oEmbed JSON | Yes (author_name → author) | ✓ FLOWING |
| `FakeTranscriptProvider` | raise / return | scripted failures map | Yes (in-memory catalog) | ✓ FLOWING |
| Persist / DB | rows | — | N/A this phase (D-14) | ✓ DEFERRED |

No hollow stubs on the captions/metadata happy or fail-closed unit paths. Live integration stubs intentionally assert gate only (IN-02 advisory).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase-7 targeted unit suite | `uv run pytest` on 10 planned test files `-q` | **130 passed** in 0.95s | ✓ PASS |
| CAP-01 ru preference | `test_adapter_prefers_ru_over_en_and_returns_transcript` | `language == "ru"` | ✓ PASS |
| CAP-02 locked reasons | `test_locked_reason_set_equals_d10_exactly` | Exact nine codes | ✓ PASS |
| D-14 roadmap note | `test_roadmap_records_cap02_live_persist_spy_deferral` + `rg persist.calls` | Phase 9 section match | ✓ PASS |
| Public surface | `test_data_collection_public_api` | Exactly seven names | ✓ PASS |

### Probe Execution

No phase-declared `scripts/*/tests/probe-*.sh` for Phase 7. Step 7c SKIPPED. Edge probes authored into unit matrices (URL noise params, dialect bases, per-subtype CAP-02 mapping) — covered by the 130-test run.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| CAP-01 | 07-01, 07-02, 07-03 | Operator can pass a YouTube URL; resolve `video_id` and fetch captions with `ru`/`en` preference | ✓ SATISFIED | URL parser + adapter happy path + oEmbed port ready; REQUIREMENTS.md Phase 7 Complete |
| CAP-02 | 07-01, 07-02, 07-03 | Missing/disabled/blocked captions exit non-zero with `stage=captions` and write zero database rows | ✓ SATISFIED | Taxonomy + mapper + unit fail-closed; live zero-row spy deferred D-14 to Phase 9/10 |

**Orphaned requirements:** None — REQUIREMENTS.md Phase 7 lists only CAP-01, CAP-02; both claimed by all three plans and marked Complete.

### Decision Coverage (07-CONTEXT.md)

| Decision | Status | Evidence |
| -------- | ------ | -------- |
| D-01…D-03 URL accept/reject + bare id | ✓ Honored | extract_video_id matrix tests |
| D-04 parser in ingestion-service only | ✓ Honored | Not on provider ports |
| D-05 stage=url vs captions | ✓ Honored | map_url_error / map_captions_error |
| D-06…D-09 language preference + fail-closed | ✓ Honored | adapter dialect + no_preferred_language |
| D-10 locked captions reasons | ✓ Honored | CAPTIONS_REASONS exact nine |
| D-11 IngestError stages in ingestion-service | ✓ Honored | domain/errors.py; no stage in data-collection |
| D-12 CaptionsError taxonomy | ✓ Honored | nine types incl. BotChallenge |
| D-13 diagnostic envelope | ✓ Honored for context keys | to_dict(); CR-01 advisory on message |
| D-14 CAP-02 unit now / live spy later | ✓ Honored | ROADMAP Phase 9 note present |
| D-15 FakeTranscriptProvider.failures | ✓ Honored | additive catalog tests |
| D-16…D-18 proxy Settings + SOCKS deps | ✓ Honored | Settings/clients + pyproject |
| D-19 bot_challenge distinct | ✓ Honored | CaptionsBotChallenge / bot_challenge |
| D-20 integration gate + runbook | ✓ Honored | marker + path-explicit docs |
| D-21…D-26 metadata port/oEmbed/fake/barrel | ✓ Honored | 07-03 artifacts + tests |

### Prohibitions

| Prohibition | Tier | Status | Evidence |
| ----------- | ---- | ------ | -------- |
| No `os.environ`/`os.getenv` in adapters | test | ✓ Held | `rg` clean under adapters/ |
| No `stage` vocabulary in data-collection errors | test | ✓ Held | `rg stage` clean under errors/ |
| No Whisper / ASR / transcription fallback | test | ✓ Held | No matches under adapters/ingestion |
| No SDK class names as operator `reason` | test | ✓ Held | disjoint from SDK names in mapping test |
| No database writes / migrations this phase | test | ✓ Held | No new supabase migrations; no persist ports |
| No typer / openai deps this phase | judgment | ✓ Held (non-authoritative) | Plans/summaries; scaffold acceptance |
| No fabricated metadata author | test | ✓ Held | blank/missing → MetadataInvalidResponse |
| Fakes/adapters/errors off public `__all__` | test | ✓ Held | public-api negatives |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `errors/captions.py` / `metadata.py` + mappers | — | Exception `message` embeds raw context; `str(error)` → `IngestError.message` | ⚠️ Advisory (CR-01) | Context allowlist OK; credentials can still appear in `message` — fix before Phase 10 CLI |
| `youtube_transcript.py` | catch chain | `CookieInvalid` / base SDK exceptions escape | ℹ️ Advisory (WR-01) | Outside locked handled catalog; rare cookie path |
| `mapping/url.py` | — | Forwards raw operator URL incl. userinfo | ℹ️ Advisory (WR-02) | URL-stage diagnostics may leak pasted credentials |
| `youtube_transcript.py` | ~116 | Snippets joined with `""` | ℹ️ Advisory (WR-03) | Multi-snippet glue; single-snippet tests still green |
| `youtube_oembed.py` | — | Non-200 (5xx/429) → MetadataUnavailable | ℹ️ Advisory (WR-04) | Ops misread risk; CAP-01/02 captions path unaffected |

No stub blockers for roadmap SCs. Live integration stubs are intentional Phase-7 gates (IN-02).

### Human Verification Required

None — all must-haves are unit-testable contracts; 130 phase-7 unit tests passed. Advisory CR-01/WR-* do not require a human gate for phase completion (harden in follow-up before Phase 10 operator emission).

### Gaps Summary

**No gaps found against phase goal / CAP-01 / CAP-02 / roadmap SCs.** Phase goal achieved. Ready to proceed to Phase 8.

Advisory follow-ups (non-blocking): CR-01 message redaction; WR-01 Cookie\* catch-all; WR-02 URL value sanitization; WR-03 snippet join spacing; WR-04 oEmbed 5xx/429 → network.

---

## Verification Metadata

**Verification approach:** Goal-backward (roadmap SCs + PLAN must_haves from 07-01/02/03)  
**Must-haves source:** ROADMAP.md Phase 7 Success Criteria + three PLAN frontmatters  
**Automated checks:** 130 passed, 0 failed (targeted Phase-7 unit suite)  
**Human checks required:** 0  
**Advisory review:** 07-REVIEW.md — 1 critical, 4 warnings, 3 info (non-blocking for goal)

---
_Verified: 2026-09-26T19:30:05Z_  
_Verifier: Claude (gsd-verifier)_
