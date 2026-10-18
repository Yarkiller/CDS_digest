---
phase: 06-ports-dtos
plan: 01
subsystem: api
tags: [pydantic, protocol, dto, ports-adapters, asyncio]

requires:
  - phase: 05-admin-digest
    provides: Ports & Adapters patterns; tests_support fakes; Material provenance_label
provides:
  - Transcript, VideoMetadata, MaterialDraft, TemplateKind DTOs
  - Internal ArticleDraft
  - ArticleGenerator Protocol + FakeArticleGenerator
  - assemble_material_draft + require_material_draft type boundary
affects: [06-02-validation-edges, 06-03-public-api, 07-captions, 08-deepseek, 09-persist]

actuals:
  tokens: 9000
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Pydantic v2 Field + strip/non-blank validators for ingestion DTOs"
    - "Async Protocol ports with Fake*.calls spy via asyncio.run in sync pytest"
    - "Pure assemble_material_draft; require_material_draft isinstance TypeError boundary"

key-files:
  created:
    - data-collection/src/data_collection/dto/transcript.py
    - data-collection/src/data_collection/dto/video_metadata.py
    - data-collection/src/data_collection/dto/material_draft.py
    - data-collection/src/data_collection/dto/article_draft.py
    - data-collection/src/data_collection/dto/template_kind.py
    - data-collection/src/data_collection/ports/article_generator.py
    - data-collection/src/data_collection/assemble.py
    - data-collection/src/data_collection/tests_support/fakes.py
    - tests/unit/test_transcript_dto.py
    - tests/unit/test_video_metadata_dto.py
    - tests/unit/test_material_draft_dto.py
    - tests/unit/test_template_kind.py
    - tests/unit/test_article_draft_internal.py
    - tests/unit/test_article_generator_fake.py
    - tests/unit/test_assemble_material_draft.py
    - tests/unit/test_material_draft_type_boundary.py
  modified: []

key-decisions:
  - "require_material_draft lives in assemble.py for Phase 9 reuse (OQ1)"
  - "Async fakes tested with asyncio.run — no pytest-asyncio"
  - "ArticleDraft internal only; public __all__ rewrite deferred to 06-03"

patterns-established:
  - "Ingestion DTOs under data_collection.dto with strip validators"
  - "Port fakes only in data_collection.tests_support"
  - "Assembler never invents provenance_label; copies published_at even when None"

requirements-completed: [DTO-01, DTO-02]

coverage:
  - id: D1
    description: "Transcript, VideoMetadata, MaterialDraft, TemplateKind construct and validate (DTO-01)"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_transcript_dto.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_video_metadata_dto.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_material_draft_dto.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_template_kind.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "FakeArticleGenerator returns scripted ArticleDraft and records {transcript, template} in .calls (DTO-02)"
    requirement: DTO-02
    verification:
      - kind: unit
        ref: "tests/unit/test_article_generator_fake.py#test_fake_article_generator_returns_scripted_draft_and_records_calls"
        status: pass
    human_judgment: false
  - id: D3
    description: "assemble_material_draft maps fields; source_published_at None OK; provenance_label caller-only"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_assemble_material_draft.py#test_assemble_material_draft_maps_fields_and_caller_provenance"
        status: pass
    human_judgment: false
  - id: D4
    description: "require_material_draft raises TypeError for Transcript (SC-3)"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_material_draft_type_boundary.py#test_transcript_rejected_where_material_draft_required"
        status: pass
    human_judgment: false
  - id: D5
    description: "MaterialDraft missing-required and TemplateKind closed-set locked"
    requirement: DTO-01
    verification:
      - kind: unit
        ref: "tests/unit/test_material_draft_dto.py#test_material_draft_rejects_missing_required_field"
        status: pass
      - kind: unit
        ref: "tests/unit/test_template_kind.py#test_template_kind_rejects_unknown_member"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-09-26
status: complete
---

# Phase 06 Plan 01: Tracer DTOs + ArticleGenerator + Assembler Summary

**Ingestion contracts locked: Transcript≠MaterialDraft via Pydantic DTOs, FakeArticleGenerator spy, pure assembler, and require_material_draft TypeError boundary**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-26T13:18:06Z
- **Completed:** 2026-09-26T13:21:57Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments

- Four public-path types (`Transcript`, `VideoMetadata`, `MaterialDraft`, `TemplateKind`) with strip/blank validators and closed Enum
- Internal `ArticleDraft` + `ArticleGenerator` Protocol + `FakeArticleGenerator` (scripted success + `.calls`)
- `assemble_material_draft` copies nullable `published_at` and never invents `provenance_label`
- `require_material_draft` rejects `Transcript` with `TypeError` (Roadmap SC-3)
- Missing-required MaterialDraft fields and unknown TemplateKind members covered by unit tests

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tracer tests** - `45db99f` (test)
2. **Task 1 GREEN: DTOs + port + fake + assembler** - `80d91ab` (feat)
3. **Task 2: MaterialDraft requiredness + TemplateKind closed set** - `56805a9` (test)

**Plan metadata:** (this commit)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified

- `data-collection/src/data_collection/dto/transcript.py` - Transcript (text, language, video_id)
- `data-collection/src/data_collection/dto/video_metadata.py` - VideoMetadata with optional published_at
- `data-collection/src/data_collection/dto/material_draft.py` - MaterialDraft provenance fields
- `data-collection/src/data_collection/dto/article_draft.py` - Internal LLM article shape
- `data-collection/src/data_collection/dto/template_kind.py` - lecture|podcast Enum
- `data-collection/src/data_collection/ports/article_generator.py` - ArticleGenerator Protocol
- `data-collection/src/data_collection/assemble.py` - assemble + require helpers
- `data-collection/src/data_collection/tests_support/fakes.py` - FakeArticleGenerator
- `tests/unit/test_*.py` (8 files) - unit coverage for tracer + Task 2 edge asserts

## Decisions Made

- Followed plan/CONTEXT locks: `require_material_draft` in `assemble.py`; `asyncio.run` for async fake; ArticleDraft not in package `__all__` (06-03 owns rewrite)
- Task 2 needed no production changes — Pydantic required fields and Enum already enforce D-05/D-10

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for `06-02` (TranscriptProvider fake + full DTO validation edge matrix)
- Do not rewrite public `__all__` until `06-03`
- Old Foundry/YouTube DTOs intentionally retained until 06-03 deletion

## Self-Check: PASSED

- [x] key-files.created exist on disk
- [x] `git log --grep=06-01` returns ≥1 commit
- [x] All task acceptance_criteria verified (25 unit tests green)
- [x] Plan-level verification pytest command exits 0
- [x] No httpx/supabase/fastapi in new DTOs/ports/assembler
- [x] ArticleDraft and FakeArticleGenerator not in package `__all__`

---
*Phase: 06-ports-dtos*
*Completed: 2026-09-26*
