---
phase: 08-deepseek-article-templates
plan: 03
subsystem: ingestion
tags: [deepseek, budget, truncation, template-load, configuration-error]

requires:
  - phase: 08-01
    provides: DeepSeekArticleGenerator, Settings, templates
  - phase: 08-02
    provides: ArticleError, map_article_error

provides:
  - len(transcript.text) > max_transcript_chars raises ArticleBudgetError before SDK call
  - ArticleBudgetError maps to IngestError(stage=llm_truncation, reason=transcript_too_long)
  - llm_truncation context contains only char_count and max_chars
  - Invalid MAX_TRANSCRIPT_CHARS raises ConfigurationError at Settings.from_env
  - TemplateLoadError for missing or unreadable lecture.md/podcast.md
  - TemplateLoadError is not an ArticleError or IngestError

affects:
  - 09 (persist with failing generator)
  - 10 (operator diagnostics)

actuals:
  tokens: 7000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - Adapter-side budget check on injected int before external call
    - Startup config errors outside IngestError.Stage

key-files:
  created: []
  modified:
    - data-collection/src/data_collection/adapters/deepseek_article.py
    - data-collection/src/data_collection/templates/__init__.py
    - ingestion-service/src/ingestion_service/mapping/article.py
    - ingestion-service/src/ingestion_service/composition/settings.py
    - tests/unit/test_deepseek_article_adapter.py
    - tests/unit/test_article_error_mapping.py
    - tests/unit/test_ingestion_settings.py
    - tests/unit/test_article_templates.py

key-decisions:
  - Character cap compares Python len (code points), not UTF-8 bytes or tokenizer.
  - Template text and system prompt do not count toward the cap.
  - Invalid cap values raise ConfigurationError, not llm_truncation.
  - Missing/unreadable templates fail at load before any client construction.

patterns-established:
  - "load_article_templates checks path.is_file() and wraps read_text OSError as TemplateLoadError."

requirements-completed:
  - LLM-05

coverage:
  - id: D1
    description: "len(transcript.text) > max_transcript_chars raises ArticleBudgetError before create is called."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_over_max_chars_does_not_call_create"
        status: pass
    human_judgment: false
  - id: D2
    description: "len(transcript.text) == max_transcript_chars still calls create."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_exactly_max_chars_calls_create"
        status: pass
    human_judgment: false
  - id: D3
    description: "Template length is not added to the character count."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_long_template_with_short_transcript_does_not_raise_budget_error"
        status: pass
    human_judgment: false
  - id: D4
    description: "80000 Cyrillic code points (UTF-8 byte length > cap) still call create."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_eighty_thousand_cyrillic_chars_call_create"
        status: pass
    human_judgment: false
  - id: D5
    description: "ArticleBudgetError maps to stage=llm_truncation with context char_count and max_chars only."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_article_error_mapping.py#test_article_budget_error_maps_to_llm_truncation"
        status: pass
    human_judgment: false
  - id: D6
    description: "Non-integer, zero, or negative MAX_TRANSCRIPT_CHARS raise ConfigurationError at from_env."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_ingestion_settings.py#test_invalid_max_transcript_chars_raises_configuration_error"
        status: pass
    human_judgment: false
  - id: D7
    description: "Missing lecture.md or podcast.md raises TemplateLoadError."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_article_templates.py#test_missing_lecture_md_raises_template_load_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_article_templates.py#test_missing_podcast_md_raises_template_load_error"
        status: pass
    human_judgment: false
  - id: D8
    description: "Unreadable template raises TemplateLoadError; AsyncOpenAI is not constructed."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_article_templates.py#test_unreadable_template_raises_template_load_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_article_templates.py#test_build_deepseek_article_generator_with_missing_template_does_not_construct_async_openai"
        status: pass
    human_judgment: false
  - id: D9
    description: "TemplateLoadError is not a subclass of ArticleError or IngestError."
    requirement: LLM-05
    verification:
      - kind: unit
        ref: "tests/unit/test_article_templates.py#test_template_load_error_is_not_article_error_or_ingest_error"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-27
status: complete
---

# Phase 8 Plan 03: Budget, Truncation & Template Load Summary

**Over-cap transcripts fail before DeepSeek with `stage=llm_truncation`; bad caps and missing templates fail at startup as configuration errors.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-27T09:02:00Z
- **Completed:** 2026-09-27T09:14:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added first-line `len(transcript.text) > max_transcript_chars` check in `DeepSeekArticleGenerator.process` raising `ArticleBudgetError`.
- Mapped `ArticleBudgetError` to `IngestError(stage="llm_truncation", reason="transcript_too_long")` with context limited to `char_count` and `max_chars`.
- Validated `MAX_TRANSCRIPT_CHARS` in `Settings.from_env`: unset/blank → 80000; non-integer, zero, or negative → `ConfigurationError`.
- Added `TemplateLoadError` raised when `lecture.md` or `podcast.md` is missing or unreadable.
- Proved missing templates prevent `AsyncOpenAI` construction in `build_deepseek_article_generator`.

## Task Commits

1. **Task 1: Reject over-cap transcripts before the SDK call** - `ecada9e` (feat)
2. **Task 2: Fail at template load when a markdown file is missing or unreadable** - `c3893f5` (feat)

## Files Created/Modified
- `data-collection/src/data_collection/adapters/deepseek_article.py` - ArticleBudgetError check.
- `data-collection/src/data_collection/templates/__init__.py` - TemplateLoadError.
- `ingestion-service/src/ingestion_service/mapping/article.py` - llm_truncation branch.
- `ingestion-service/src/ingestion_service/composition/settings.py` - Cap validation (already present from 08-01; tests added).
- `tests/unit/test_deepseek_article_adapter.py` - Budget boundary tests.
- `tests/unit/test_article_error_mapping.py` - Truncation mapping test.
- `tests/unit/test_ingestion_settings.py` - Invalid cap tests.
- `tests/unit/test_article_templates.py` - Template load failure tests.

## Decisions Made
- Used Python `len()` on code points; 80000 Cyrillic chars (larger UTF-8 byte size) still pass the cap.
- `llm_truncation` context excludes `video_id` per D-09.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` failure remains unrelated to Phase 8.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ready for 08-04: fake failures, translation suffix, public API scope, runbook docs.

---
*Phase: 08-deepseek-article-templates*
*Completed: 2026-09-27*
