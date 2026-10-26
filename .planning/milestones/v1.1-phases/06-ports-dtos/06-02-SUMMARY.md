---
phase: 06-ports-dtos
plan: 02
subsystem: api
tags: [pydantic, protocol, dto, ports-adapters, asyncio, validation]

requires:
  - phase: 06-ports-dtos
    provides: Tracer DTOs, ArticleGenerator fake, assembler from 06-01
provides:
  - TranscriptProvider Protocol + FakeTranscriptProvider with .calls spy
  - DTO-01 empty/blank/language/nullable published_at validation edges locked
affects: [06-03-public-api, 07-captions, 08-deepseek, 09-persist]

actuals:
  tokens: 7000
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - "FakeTranscriptProvider mirrors FakeArticleGenerator — scripted success + .calls spy"
    - "asyncio.run for async port fakes — no pytest-asyncio"
    - "DTO edge matrix extends 06-01 validators; no schema migration (D-14 deferred to Phase 9)"

key-files:
  created:
    - data-collection/src/data_collection/ports/transcript_provider.py
    - tests/unit/test_transcript_provider_fake.py
  modified:
    - data-collection/src/data_collection/tests_support/fakes.py
    - tests/unit/test_transcript_dto.py
    - tests/unit/test_video_metadata_dto.py
    - tests/unit/test_material_draft_dto.py
    - tests/unit/test_article_draft_internal.py

key-decisions:
  - "Task 2 needed no production DTO changes — 06-01 strip/blank validators already enforce D-09/D-11–D-14"
  - "Deduped overlapping edge tests after concurrent edits (duplicate defs silently overwrote)"

patterns-established:
  - "Both ingestion port fakes live in tests_support with ordered .calls spies"
  - "Nullable published_at / source_published_at locked by explicit None unit asserts"

requirements-completed: [DTO-01, DTO-02]

coverage:
  - id: D1
    description: "FakeTranscriptProvider returns scripted Transcript and records video ids in call order (DTO-02, D-15, D-17)"
    requirement: DTO-02
    verification:
      - kind: unit
        ref: "tests/unit/test_transcript_provider_fake.py#test_fake_transcript_provider_returns_scripted_and_records_calls"
        status: pass
      - kind: unit
        ref: "tests/unit/test_transcript_provider_fake.py#test_fake_transcript_provider_records_calls_in_order"
        status: pass
    human_judgment: false
  - id: D2
    description: "Transcript rejects whitespace text, blank video_id, language length out of 2–10 (D-09)"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_transcript_dto.py#test_transcript_rejects_whitespace_only_text"
        status: pass
      - kind: unit
        ref: "tests/unit/test_transcript_dto.py#test_transcript_rejects_blank_video_id"
        status: pass
      - kind: unit
        ref: "tests/unit/test_transcript_dto.py#test_transcript_language_length_bounds"
        status: pass
    human_judgment: false
  - id: D3
    description: "VideoMetadata requires author/source_url/video_id; omitting published_at → None (D-11, D-12, D-13)"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_video_metadata_dto.py#test_video_metadata_rejects_missing_required_field"
        status: pass
      - kind: unit
        ref: "tests/unit/test_video_metadata_dto.py#test_video_metadata_omitting_published_at_is_none"
        status: pass
    human_judgment: false
  - id: D4
    description: "MaterialDraft source_published_at=None constructs; blank provenance_label/title rejected (D-05, D-14)"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_material_draft_dto.py#test_material_draft_source_published_at_none_constructs"
        status: pass
      - kind: unit
        ref: "tests/unit/test_material_draft_dto.py#test_material_draft_rejects_blank_provenance_and_title"
        status: pass
    human_judgment: false
  - id: D5
    description: "ArticleDraft blank title/dek/body_markdown rejected (D-06)"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_article_draft_internal.py#test_article_draft_rejects_blank_required_strings"
        status: pass
    human_judgment: false

duration: 3min
completed: 2026-09-26
status: complete
---

# Phase 06 Plan 02: TranscriptProvider + DTO Validation Edges Summary

**FakeTranscriptProvider spy completes DTO-02 ports; DTO-01 empty/blank/language/nullable published_at edges locked without schema migration**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-26T13:25:08Z
- **Completed:** 2026-09-26T13:28:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- `TranscriptProvider` Protocol (`async get(video_id) -> Transcript`) + `FakeTranscriptProvider` with ordered `.calls` spy (D-15, D-17)
- DTO-01 empty probe: whitespace/blank Transcript fields, language length bounds
- DTO-01 nullable: `VideoMetadata.published_at` omit → None; `MaterialDraft(source_published_at=None)` OK (D-13, D-14)
- Blank MaterialDraft provenance/title and ArticleDraft title/dek/body rejected
- Both port fakes injectible without network/DB; no failure catalog on fakes

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing FakeTranscriptProvider tests** - `5fae6c5` (test)
2. **Task 1 GREEN: TranscriptProvider + FakeTranscriptProvider** - `a61695b` (feat)
3. **Task 2: DTO-01 empty/blank/nullable edge matrix** - `e15e571` (test)
4. **Task 2 cleanup: Dedupe overlapping edge tests** - `fd863d8` (refactor)

**Plan metadata:** (this commit)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified

- `data-collection/src/data_collection/ports/transcript_provider.py` - TranscriptProvider Protocol (D-15)
- `data-collection/src/data_collection/tests_support/fakes.py` - FakeTranscriptProvider alongside FakeArticleGenerator
- `tests/unit/test_transcript_provider_fake.py` - scripted success + ordering probe via asyncio.run
- `tests/unit/test_transcript_dto.py` - empty/blank/language edge asserts (D-09)
- `tests/unit/test_video_metadata_dto.py` - missing/blank required + nullable published_at (D-11–D-13)
- `tests/unit/test_material_draft_dto.py` - None published_at + blank provenance/title (D-05, D-14)
- `tests/unit/test_article_draft_internal.py` - blank article field rejects (D-06)

## Decisions Made

- Followed plan: no production DTO changes for Task 2 — validators from 06-01 already satisfy edge matrix
- No schema migration (D-14 Phase 9); no `__all__` rewrite (06-03); no failure scripts on fakes (D-17)
- Deduped concurrent duplicate test definitions that silently overwrote earlier defs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Deduped overwritten duplicate test functions**
- **Found during:** Task 2 (DTO validation edge matrix)
- **Issue:** Concurrent edge-matrix edits produced duplicate function names; Python kept only the last definition, leaving dead earlier bodies
- **Fix:** Collapsed to one test per behavior (whitespace text, blank ids, missing required, None published_at, blank provenance/title)
- **Files modified:** `tests/unit/test_transcript_dto.py`, `test_video_metadata_dto.py`, `test_material_draft_dto.py`
- **Verification:** Plan verification pytest — 31 passed
- **Committed in:** `fd863d8` (refactor)

---

**Total deviations:** 1 auto-fixed (1 bug/quality)
**Impact on plan:** Cleanup only; no scope creep; acceptance criteria still met.

## Issues Encountered

None beyond the concurrent-edit duplicate tests (resolved above).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for `06-03` (public `__all__` rewrite + brownfield DTO delete)
- Do not export fakes or ArticleDraft from package barrel until 06-03
- DTO-01/DTO-02 shared-ID gate: mark Complete only after 06-03 finishes

## Self-Check: PASSED

- [x] key-files.created exist on disk
- [x] `git log --grep=06-02` returns ≥1 commit (4 production + this docs)
- [x] All task acceptance_criteria verified (31 unit tests green)
- [x] Plan-level verification pytest command exits 0
- [x] `.calls` records video ids in call order
- [x] MaterialDraft(... source_published_at=None) succeeds
- [x] Whitespace-only Transcript.text raises ValidationError
- [x] No failure catalog on fakes; no URL parsing in TranscriptProvider

---
*Phase: 06-ports-dtos*
*Completed: 2026-09-26*
