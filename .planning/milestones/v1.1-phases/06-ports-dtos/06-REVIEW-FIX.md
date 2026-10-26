---
phase: 06-ports-dtos
fixed_at: 2026-09-26T15:37:16.237Z
review_path: .planning/phases/06-ports-dtos/06-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 3
skipped: 0
already_fixed: 3
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-09-26T15:37:16.237Z
**Source review:** `.planning/phases/06-ports-dtos/06-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (Critical + Warning + Info; `fix_scope: all`)
- Fixed this pass: 3 (IN-01, IN-02, IN-03)
- Already fixed (prior pass): 3 (WR-01, WR-02, WR-03)
- Skipped: 0

**Verification:** Pure refactor / annotation changes gated by existing unit suite; 53 phase-06 unit tests passed after fixes.

## Already Fixed (prior pass — verified still present)

### WR-01: `ports` package barrel omits `TranscriptProvider`

**Files verified:** `data-collection/src/data_collection/ports/__init__.py`, `tests/unit/test_data_collection_public_api.py`
**Commit:** `c91d0cf`
**Status:** still present — `__all__` exports both `ArticleGenerator` and `TranscriptProvider`.

### WR-02: `Transcript.language` length bounds apply before strip

**Files verified:** `data-collection/src/data_collection/dto/transcript.py`, `tests/unit/test_transcript_dto.py`
**Commit:** `97f4501`
**Status:** still present — length 2–10 enforced after strip; `"  zh-Hans  "` → `"zh-Hans"`.

### WR-03: Naive `datetime` accepted for provenance timestamps

**Files verified:** `data-collection/src/data_collection/dto/video_metadata.py`, `data-collection/src/data_collection/dto/material_draft.py`, related unit tests
**Commit:** `38b1024`
**Status:** still present — `_require_aware` rejects naive `published_at` / `source_published_at`.

## Fixed Issues (this pass)

### IN-01: Duplicated `_strip_non_blank` validators across DTOs

**Files modified:** `data-collection/src/data_collection/dto/_validators.py` (new), `transcript.py`, `video_metadata.py`, `material_draft.py`, `article_draft.py`
**Commit:** `0753916`
**Applied fix:** Shared private `strip_non_blank` helper; DTOs call it from field validators. `_validators` kept out of public `__all__`.

### IN-02: `FakeArticleGenerator.calls` typed as bare `list[dict]`

**Files modified:** `data-collection/src/data_collection/tests_support/fakes.py`
**Commit:** `56dd087`
**Applied fix:** `ArticleGeneratorCall` TypedDict; `calls: list[ArticleGeneratorCall]`. `FakeTranscriptProvider.calls` remains `list[str]`.

### IN-03: `require_material_draft` parameter type hides the runtime guard

**Files modified:** `data-collection/src/data_collection/assemble.py`, `tests/unit/test_material_draft_type_boundary.py`
**Commit:** `d9f6f20`
**Applied fix:** Annotation `value: object` → `MaterialDraft`; runtime `isinstance` / `TypeError` unchanged. Removed obsolete `# type: ignore[arg-type]` in boundary test.

---

_Fixed: 2026-09-26T15:37:16.237Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
