---
phase: 06-ports-dtos
reviewed: 2026-09-26T14:22:00Z
depth: standard
files_reviewed: 22
files_reviewed_list:
  - data-collection/src/data_collection/__init__.py
  - data-collection/src/data_collection/assemble.py
  - data-collection/src/data_collection/dto/article_draft.py
  - data-collection/src/data_collection/dto/material_draft.py
  - data-collection/src/data_collection/dto/template_kind.py
  - data-collection/src/data_collection/dto/transcript.py
  - data-collection/src/data_collection/dto/video_metadata.py
  - data-collection/src/data_collection/ports/__init__.py
  - data-collection/src/data_collection/ports/article_generator.py
  - data-collection/src/data_collection/ports/transcript_provider.py
  - data-collection/src/data_collection/tests_support/__init__.py
  - data-collection/src/data_collection/tests_support/fakes.py
  - tests/unit/test_article_draft_internal.py
  - tests/unit/test_article_generator_fake.py
  - tests/unit/test_assemble_material_draft.py
  - tests/unit/test_data_collection_public_api.py
  - tests/unit/test_material_draft_dto.py
  - tests/unit/test_material_draft_type_boundary.py
  - tests/unit/test_template_kind.py
  - tests/unit/test_transcript_dto.py
  - tests/unit/test_transcript_provider_fake.py
  - tests/unit/test_video_metadata_dto.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues
---

# Phase 06: Code Review Report

**Reviewed:** 2026-09-26T14:22:00Z
**Depth:** standard
**Files Reviewed:** 22
**Status:** issues_found

## Summary

Adversarial review of Phase 06 Ports & DTOs (`data-collection` ingestion DTOs, Protocol ports, assembler, `tests_support` fakes, unit tests). Architecture checks pass on the main path: no SDK imports in DTOs/ports/assembler, fakes only under `tests_support`, package `__all__` is exactly the six public names, brownfield YouTube/Foundry/text_import modules are gone, and TDD unit coverage locks the tracer + edge matrix.

Three maintainability/correctness risks remain: incomplete `ports` subpackage barrel after adding `TranscriptProvider`, `Transcript.language` Field length constraints applying before strip (rejects padded-but-valid tags), and timezone-naive `datetime` accepted on provenance timestamps that Phase 9 maps to `timestamptz`.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `ports` package barrel omits `TranscriptProvider`

**File:** `data-collection/src/data_collection/ports/__init__.py:3-5`
**Issue:** After 06-02 added `TranscriptProvider`, `data_collection.ports.__all__` still exports only `ArticleGenerator`. `from data_collection.ports import TranscriptProvider` fails (`hasattr` is False) while the package root correctly re-exports both ports. Callers following the ports package (mirroring backend `application.ports`) hit an asymmetric, incomplete surface.
**Fix:**
```python
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider

__all__ = ["ArticleGenerator", "TranscriptProvider"]
```

### WR-02: `Transcript.language` length bounds apply before strip

**File:** `data-collection/src/data_collection/dto/transcript.py:8-25`
**Issue:** D-09 specifies language length 2–10 (and other string fields strip before blank checks). `language` uses `Field(min_length=2, max_length=10)` on the raw value, then strips in `_strip_language`. Padded valid tags fail Field first — e.g. `"  zh-Hans  "` (11 chars) raises “at most 10 characters” even though the stripped value `"zh-Hans"` is valid. `"  en  "` works only because raw length ≤ 10. Length semantics are therefore inconsistent with `text`/`video_id` strip-first validation.
**Fix:** Drop Field length constraints (or set loose upper bound) and enforce 2–10 only after strip:
```python
language: str

@field_validator("language")
@classmethod
def _strip_language(cls, value: str) -> str:
    cleaned = value.strip()
    if not (2 <= len(cleaned) <= 10):
        raise ValueError("language length must be 2–10")
    return cleaned
```
Add a unit assert that `"  zh-Hans  "` constructs as `"zh-Hans"`.

### WR-03: Naive `datetime` accepted for provenance timestamps

**File:** `data-collection/src/data_collection/dto/video_metadata.py:12`
**File:** `data-collection/src/data_collection/dto/material_draft.py:16`
**Issue:** `published_at` / `source_published_at` accept timezone-naive `datetime` (verified: `tzinfo is None` constructs). D-14 / PERS-01 target `timestamptz NULL`. Naive values will be ambiguous at Phase 9 persist and can silently shift across environments. Assembler copies the value unchanged (`assemble.py:23`), so the footgun propagates.
**Fix:** Reject naive datetimes (or normalize to UTC) on both fields:
```python
from datetime import datetime, timezone
from pydantic import field_validator

@field_validator("published_at")
@classmethod
def _require_aware(cls, value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        raise ValueError("published_at must be timezone-aware")
    return value
```
Mirror on `MaterialDraft.source_published_at`. Prefer keeping aware fixtures in unit tests (`timezone.utc` already used in happy paths).

## Info

### IN-01: Duplicated `_strip_non_blank` validators across DTOs

**File:** `data-collection/src/data_collection/dto/article_draft.py:11-17`
**File:** `data-collection/src/data_collection/dto/material_draft.py:28-32`
**File:** `data-collection/src/data_collection/dto/transcript.py:11-17`
**File:** `data-collection/src/data_collection/dto/video_metadata.py:14-20`
**Issue:** Identical strip/non-blank `field_validator` bodies are copy-pasted four times. Drift risk when tightening blank rules (e.g. Unicode whitespace).
**Fix:** Extract a shared helper under `data_collection.dto` (e.g. `_validators.strip_non_blank`) and reuse; keep behavior identical.

### IN-02: `FakeArticleGenerator.calls` typed as bare `list[dict]`

**File:** `data-collection/src/data_collection/tests_support/fakes.py:23`
**Issue:** Architecture forbids loose typing at module boundaries. Spy entries are always `{"transcript": Transcript, "template": TemplateKind}`, but `list[dict]` erases that contract for type checkers and future failure-script extensions (D-17).
**Fix:**
```python
from typing import TypedDict

class ArticleGeneratorCall(TypedDict):
    transcript: Transcript
    template: TemplateKind

self.calls: list[ArticleGeneratorCall] = []
```

### IN-03: `require_material_draft` parameter type hides the runtime guard

**File:** `data-collection/src/data_collection/assemble.py:27-30`
**Issue:** Signature is `value: MaterialDraft`, so static checkers reject `Transcript` before the `isinstance` path runs. The runtime `TypeError` (SC-3) is only exercised via `# type: ignore` / dynamic callers. The guard is still correct at runtime; the annotation understates the intended “accept object, assert MaterialDraft” contract.
**Fix:** Annotate input as `object` (or `MaterialDraft | object`) and keep the return as `MaterialDraft`:
```python
def require_material_draft(value: object) -> MaterialDraft:
    if not isinstance(value, MaterialDraft):
        raise TypeError("MaterialDraft required")
    return value
```

---

_Reviewed: 2026-09-26T14:22:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
