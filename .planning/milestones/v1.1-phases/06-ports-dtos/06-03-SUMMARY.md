---
phase: 06-ports-dtos
plan: 03
subsystem: api
tags: [pydantic, protocol, dto, ports-adapters, public-api]

requires:
  - phase: 06-ports-dtos
    provides: Tracer DTOs, both port fakes, assembler from 06-01/06-02
provides:
  - Public data_collection.__all__ with six ingestion names only
  - Brownfield youtube/foundry/text_import DTOs and tests deleted
  - Export-negative unit coverage for fakes, ArticleDraft, old names
affects: [07-captions, 08-deepseek, 09-persist, 10-cli]

actuals:
  tokens: 5000
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Public barrel exports only six ingestion contracts; fakes via tests_support deep import"
    - "Costly public-API replacement gated by checkpoint:decision before deletes"

key-files:
  created:
    - tests/unit/test_data_collection_public_api.py
  modified:
    - data-collection/src/data_collection/__init__.py
  deleted:
    - data-collection/src/data_collection/dto/youtube.py
    - data-collection/src/data_collection/dto/foundry.py
    - data-collection/src/data_collection/dto/text_import.py
    - tests/unit/test_youtube_source_dto.py
    - tests/unit/test_foundry_dtos.py
    - tests/unit/test_text_import_dto.py

key-decisions:
  - "User approved proceed at checkpoint:decision — delete brownfield DTOs D-01…D-03"
  - "Backend query_embedder.EMBEDDING_DIM=1024 left untouched (D-02)"
  - "No supabase-integration migrations (D-14 deferred to Phase 9)"

patterns-established:
  - "data_collection public surface is exactly six names; ArticleDraft remains dto.deep-import only"
  - "Export negatives lock fakes and old Foundry/YouTube names out of package root"

requirements-completed: [DTO-01, DTO-02]

coverage:
  - id: D1
    description: "Public data_collection.__all__ exports exactly six ingestion names (D-01, D-04)"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py#test_public_all_is_exactly_six_ingestion_names"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fakes, ArticleDraft, and old DTO names are not importable from package root (D-02, D-04, D-06)"
    requirement: DTO-02
    verification:
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py#test_negative_names_not_importable_from_package_root"
        status: pass
    human_judgment: false
  - id: D3
    description: "Brownfield dto/youtube.py, foundry.py, text_import.py and their three unit tests deleted (D-03)"
    requirement: DTO-01
    verification:
      - kind: other
        ref: "Test-Path dto/{youtube,foundry,text_import}.py and three unit tests → False"
        status: pass
    human_judgment: false

duration: 2min
completed: 2026-09-26
status: complete
---

# Phase 06 Plan 03: Public API + Brownfield Delete Summary

**Six-name data_collection public barrel; YoutubeSourceDto/Foundry/TextImport DTOs and tests deleted after checkpoint proceed**

## Performance

- **Duration:** 2 min
- **Started:** 2026-09-26T14:15:11Z
- **Completed:** 2026-09-26T14:16:45Z
- **Tasks:** 2 (1 checkpoint approved + 1 TDD)
- **Files modified:** 8

## Accomplishments

- Checkpoint:decision approved (`proceed`) — costly public-API replacement D-01…D-03
- `data_collection.__all__` = Transcript, VideoMetadata, MaterialDraft, TemplateKind, TranscriptProvider, ArticleGenerator
- Deleted brownfield modules and unit tests (D-03)
- Export negatives cover fakes, ArticleDraft, old DTO names, package EMBEDDING_DIM (D-02, D-04, D-06)
- Backend `query_embedder.EMBEDDING_DIM = 1024` unchanged; no new migrations

## Task Commits

Each task was committed atomically:

1. **Task 1: Confirm costly public-API replacement** - (checkpoint — no code commit; user: proceed)
2. **Task 2 RED: Failing public API whitelist test** - `2a83447` (test)
3. **Task 2 GREEN: Rewrite __all__ + delete brownfield DTOs** - `315ed99` (feat)

**Plan metadata:** (this commit)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified

- `tests/unit/test_data_collection_public_api.py` - __all__ whitelist + negative root imports
- `data-collection/src/data_collection/__init__.py` - six-name public barrel
- `data-collection/src/data_collection/dto/youtube.py` - deleted
- `data-collection/src/data_collection/dto/foundry.py` - deleted
- `data-collection/src/data_collection/dto/text_import.py` - deleted
- `tests/unit/test_youtube_source_dto.py` - deleted
- `tests/unit/test_foundry_dtos.py` - deleted
- `tests/unit/test_text_import_dto.py` - deleted

## Decisions Made

- User selected **proceed** at the costly checkpoint — delete brownfield public surface per D-01…D-03
- Left backend EMBEDDING_DIM and schema alone (D-02); migrations deferred (D-14 → Phase 9)
- `dto/__init__.py` needed no change (already empty convenience package)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Full `uv run pytest` reports 1 failure in `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` (extra `sent_at`/`week_label` vs expectation). Pre-existing / unrelated to data-collection public API; out of plan scope (deviation Rule scope boundary). Phase 6 verification suite (public API + ingestion DTO/port tests) is green: 49 passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 6 plans 3/3 complete — ready for `/gsd-verify-work 06` and Phase 7 captions adapter planning
- Downstream adapters must import only the six public names; fakes via `data_collection.tests_support`
- ArticleDraft remains internal (`data_collection.dto.article_draft`)

## Self-Check: PASSED

- [x] key-files.created exist on disk
- [x] `git log --grep=06-03` returns ≥1 commit (2 production + this docs)
- [x] All task acceptance_criteria verified
- [x] `test_data_collection_public_api.py` exits 0
- [x] Old DTO module files absent
- [x] `query_embedder.py` unchanged; EMBEDDING_DIM=1024
- [x] No new files under supabase-integration/migrations/
- [x] Cites D-01, D-02, D-03, D-04, D-06

---
*Phase: 06-ports-dtos*
*Completed: 2026-09-26*
