---
phase: 07-captions-adapter
plan: 02
subsystem: ingestion
tags: [CaptionsError, youtube-transcript-api, map_captions_error, FakeTranscriptProvider, CAP-02, D-10, D-14]

requires:
  - phase: 07-captions-adapter
    provides: YouTubeTranscriptAdapter tracer + CaptionsEmpty/NoPreferredLanguage + IngestError envelope
provides:
  - Full CaptionsError taxonomy (9 subtypes incl. CaptionsBotChallenge)
  - Adapter SDK→CaptionsError boundary mapping for every handled failure
  - map_captions_error → IngestError(stage=captions) locked D-10 reasons + context redaction
  - FakeTranscriptProvider(failures=…) additive catalog
  - Phase 9/10 CAP-02 live persist-spy ROADMAP note (D-14)
affects: [07-03 oEmbed/metadata, 09 persist spy, 10 CLI]

actuals:
  tokens: 12000
  tasks: 4
  commits: 8

tech-stack:
  added: []
  patterns: [SDK→CaptionsError→IngestError two-hop, locked reason frozenset, context allowlist redaction, additive fake failures]

key-files:
  created:
    - ingestion-service/src/ingestion_service/mapping/captions.py
    - tests/unit/test_captions_error_mapping.py
    - tests/unit/test_fake_transcript_provider_failures.py
  modified:
    - data-collection/src/data_collection/errors/captions.py
    - data-collection/src/data_collection/adapters/youtube_transcript.py
    - data-collection/src/data_collection/tests_support/fakes.py
    - ingestion-service/src/ingestion_service/mapping/__init__.py
    - tests/unit/test_youtube_transcript_adapter.py
    - .planning/ROADMAP.md
    - .planning/STATE.md

key-decisions:
  - "Dedicated CaptionsBotChallenge subtype (not context-flagged CaptionsBlocked) per RESEARCH A4 / D-19"
  - "YouTubeRequestFailed + requests.RequestException precede CouldNotRetrieveTranscript catch-all so 5xx/transport ≠ unknown_captions_error"
  - "D-14 one-way: CAP-02 live persist.calls == [] spy recorded under Phase 9 details only"

patterns-established:
  - "Pattern: adapter except most-specific-first; exception_class in context only; no stage vocabulary in data-collection"
  - "Pattern: map_captions_error allowlists video_id/available_languages/exception_class"
  - "Pattern: FakeTranscriptProvider(failures=None) additive; Phase 6 positional/keyword construction unchanged"

requirements-completed: [CAP-01, CAP-02]

coverage:
  - id: D1
    description: "D-14 Phase 9/10 note — failing TranscriptProvider + spy PersistPort → persist.calls == []"
    requirement: CAP-02
    verification:
      - kind: other
        ref: "rg persist.calls == [] .planning/ROADMAP.md (Phase 9 section)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Full CaptionsError taxonomy + adapter SDK exception mapping (no Transcript on failure)"
    requirement: CAP-02
    verification:
      - kind: unit
        ref: "tests/unit/test_youtube_transcript_adapter.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "map_captions_error locked D-10 reasons + context redaction + to_dict envelope"
    requirement: CAP-02
    verification:
      - kind: unit
        ref: "tests/unit/test_captions_error_mapping.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "FakeTranscriptProvider additive failures catalog; Phase 6 success+spy untouched"
    requirement: CAP-02
    verification:
      - kind: unit
        ref: "tests/unit/test_fake_transcript_provider_failures.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_transcript_provider_fake.py"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-09-26
status: complete
---

# Phase 07 Plan 02: Fail-closed CaptionsError Summary

**Nine-subtype CaptionsError taxonomy with adapter SDK mapping, locked D-10 `map_captions_error` reasons, additive FakeTranscriptProvider.failures, and Phase 9 persist-spy deferral (D-14)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-26T19:03:49Z
- **Completed:** 2026-09-26T19:08:32Z
- **Tasks:** 4
- **Files modified:** 9

## Accomplishments

- Documented CONTEXT-locked D-14: Phase 9 details note that live CAP-02 proof is `persist.calls == []` with failing TranscriptProvider + spy PersistPort
- Extended CaptionsError to nine subtypes (incl. CaptionsBotChallenge); adapter maps every handled youtube-transcript-api / requests failure at the boundary with `exception_class` context only
- Shipped `map_captions_error` with exactly the nine locked D-10 reason codes, stage=`captions`, allowlisted context (proxy/credential keys dropped)
- Added additive `FakeTranscriptProvider(failures=…)` without changing Phase 6 success+spy tests

## Task Commits

Each task was committed atomically:

1. **Task 1: D-14 Phase 9 persist-spy note** - `cca71f3` (docs)
2. **Task 2: SDK→CaptionsError mapping (RED)** - `30667f9` (test)
3. **Task 2: SDK→CaptionsError mapping (GREEN)** - `280ecae` (feat)
4. **Task 3: map_captions_error (RED)** - `bb779ca` (test)
5. **Task 3: map_captions_error (GREEN)** - `970130f` (feat)
6. **Task 4: FakeTranscriptProvider.failures (RED)** - `1875665` (test)
7. **Task 4: FakeTranscriptProvider.failures (GREEN)** - `3402f9f` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `data-collection/.../errors/captions.py` — full taxonomy (Unavailable/Disabled/Blocked/BotChallenge/VideoUnavailable/Network + existing)
- `data-collection/.../adapters/youtube_transcript.py` — most-specific-first SDK/requests mapping
- `ingestion-service/.../mapping/captions.py` — `map_captions_error` + `CAPTIONS_REASONS`
- `data-collection/.../tests_support/fakes.py` — additive `failures` catalog
- `tests/unit/test_youtube_transcript_adapter.py` / `test_captions_error_mapping.py` / `test_fake_transcript_provider_failures.py`
- `.planning/ROADMAP.md` — Phase 9 deferred-test note + plan progress 2/3
- `.planning/STATE.md` — position advanced to plan 02 complete

## Decisions Made

- Dedicated `CaptionsBotChallenge` for `PoTokenRequired` (distinct from `CaptionsBlocked` / `youtube_blocked`)
- `YouTubeRequestFailed` and `requests.exceptions.RequestException` map to `CaptionsNetworkError` before the `CouldNotRetrieveTranscript` catch-all (D-19 / Pitfall 1)
- Quoted D-14: Phase 7 seals CAP-02 at adapter/unit level; live zero-row spy belongs to Phase 9/10

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-existing failure in `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` (extra `sent_at`/`week_label`) — unrelated; not introduced by 07-02. Plan-scoped suite: 42 passed; full suite 378 passed + 1 pre-existing fail.
- gsd-tools `state.*` / `roadmap.update-plan-progress` hit EPERM on atomic rename of STATE.md / ROADMAP.md. Retried once; updated both via direct edit. Noted per sequential-executor guidance.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for `07-03` (oEmbed / VideoMetadataProvider / proxy Settings / public `__all__`)
- CAP-02 unit/adapter proof complete; live persist spy remains Phase 9/10 (ROADMAP note present)
- Shared requirement IDs CAP-01/CAP-02: mark Complete only when sibling plan 07-03 finishes (`requirements.ready-ids`)

## Self-Check: PASSED

- Key files present on disk (`captions.py` taxonomy, `mapping/captions.py`, fake failures, three test modules)
- `git log --grep=07-02` → 7 task commits + this docs commit
- Targeted pytest: 42 passed (`test_youtube_transcript_adapter` + `test_captions_error_mapping` + fake failures + Phase 6 fake)
- Acceptance: no `stage|no_captions|youtube_blocked` in data-collection errors/adapters; Phase 6 fake test file untouched; ROADMAP Phase 9 has `persist.calls == []`

---
*Phase: 07-captions-adapter*
*Completed: 2026-09-26*
