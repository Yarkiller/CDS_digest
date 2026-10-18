---
phase: 08-deepseek-article-templates
plan: 04
subsystem: ingestion
tags: [fake, failure-scripts, provenance, translation-suffix, public-api, runbook]

requires:
  - phase: 08-02
    provides: ArticleError hierarchy
  - phase: 08-03
    provides: TemplateLoadError, character cap

provides:
  - FakeArticleGenerator optional failures keyed by video_id
  - ENGLISH_TRANSLATION_SUFFIX constant locked as " · пер. с англ."
  - data_collection.__all__ remains exactly seven names
  - NEGATIVE_ROOT_NAMES covers DeepSeekArticleGenerator, ArticleError, TemplateLoadError
  - docs/agents/local-platform-runbook.md documents DeepSeek env names and defaults

affects:
  - 09 (spy persist with failing generator)
  - 10 (provenance label assembly)

actuals:
  tokens: 6000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - Additive fake constructor with optional failures dict
    - Constant-only provenance marker; label builder deferred to Phase 10

key-files:
  created:
    - ingestion-service/src/ingestion_service/provenance.py
    - tests/unit/test_fake_article_generator.py
    - tests/unit/test_translation_marker.py
  modified:
    - data-collection/src/data_collection/tests_support/fakes.py
    - tests/unit/test_data_collection_public_api.py
    - docs/agents/local-platform-runbook.md

key-decisions:
  - Suffix is a constant only; Phase 10 builds the full provenance label.
  - Adapter source does not contain the suffix or provenance_label.
  - No Typer app, no Supabase writer, no migration, no new IngestError stage.

patterns-established:
  - "FakeArticleGenerator(result, failures={video_id: ArticleError}) mirrors FakeTranscriptProvider."

requirements-completed:
  - LLM-04

coverage:
  - id: D1
    description: "FakeArticleGenerator(result) still returns the scripted draft and records the call."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_fake_article_generator.py#test_fake_article_generator_without_failures_still_works"
        status: pass
    human_judgment: false
  - id: D2
    description: "FakeArticleGenerator failures map raises the scripted ArticleError after recording the call."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_fake_article_generator.py#test_fake_article_generator_failure_by_video_id"
        status: pass
    human_judgment: false
  - id: D3
    description: "ENGLISH_TRANSLATION_SUFFIX equals the exact locked string."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_translation_marker.py#test_english_translation_suffix_is_exact_string"
        status: pass
    human_judgment: false
  - id: D4
    description: "Suffix and provenance_label are absent from the adapter source."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_translation_marker.py#test_suffix_is_absent_from_adapter_source"
        status: pass
    human_judgment: false
  - id: D5
    description: "provenance.py has no label builder that interpolates metadata.author."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_translation_marker.py#test_provenance_module_has_no_label_builder"
        status: pass
    human_judgment: false
  - id: D6
    description: "data_collection.__all__ stays exactly seven names; new adapter/error/template loader are negative names."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py#test_public_all_is_exactly_seven_ingestion_names"
        status: pass
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py#test_negative_names_not_importable_from_package_root"
        status: pass
    human_judgment: false
  - id: D7
    description: "IngestError Stage set is unchanged."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py#test_stage_set_is_unchanged"
        status: pass
    human_judgment: false
  - id: D8
    description: "No ingestion-service Python file imports typer; no data-collection Python file imports supabase."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py#test_ingestion_service_has_no_typer_import"
        status: pass
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py#test_data_collection_has_no_supabase_import"
        status: pass
    human_judgment: false
  - id: D9
    description: "Runbook documents DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MAX_TRANSCRIPT_CHARS with defaults and no live key."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_data_collection_public_api.py"
        status: pass
    human_judgment: true
    rationale: "Runbook prose review is manual; automated tests verify absence of sk- live-key shape and symbol scope."

duration: 10min
completed: 2026-09-27
status: complete
---

# Phase 8 Plan 04: Fakes, Suffix & Scope Summary

**FakeArticleGenerator can script LLM failures by video id, the English translation marker is locked as a constant, the package root stays seven names, and the runbook documents DeepSeek settings without a secret.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-09-27T09:15:00Z
- **Completed:** 2026-09-27T09:25:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Extended `FakeArticleGenerator` with optional `failures: dict[str, ArticleError]` keyed by `video_id`.
- Created `ingestion_service.provenance` with `ENGLISH_TRANSLATION_SUFFIX = " · пер. с англ."`.
- Added `DeepSeekArticleGenerator`, `ArticleError`, and `TemplateLoadError` to `NEGATIVE_ROOT_NAMES`.
- Asserted the `Stage` literal set remains unchanged.
- Asserted no `typer` import in `ingestion-service/src` and no `supabase` import in `data-collection/src`.
- Documented DeepSeek env names and defaults in `docs/agents/local-platform-runbook.md`.

## Task Commits

1. **Task 1: Add fake LLM failures and lock the English suffix** - `44d9de1` (feat)
2. **Task 2: Keep new symbols private and document DeepSeek env names** - `5d05806` (feat)

## Files Created/Modified
- `data-collection/src/data_collection/tests_support/fakes.py` - FakeArticleGenerator failures.
- `ingestion-service/src/ingestion_service/provenance.py` - Translation suffix constant.
- `tests/unit/test_fake_article_generator.py` - Failure script tests.
- `tests/unit/test_translation_marker.py` - Suffix constant and adapter-source tests.
- `tests/unit/test_data_collection_public_api.py` - Negative names and scope tests.
- `docs/agents/local-platform-runbook.md` - DeepSeek env documentation.

## Decisions Made
- Kept the suffix as a bare constant; Phase 10 caller will format `f"YouTube · {author}"` and append the suffix when `language != "ru"`.
- Did not export `provenance` from any barrel; tests import it directly.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` failure remains unrelated to Phase 8.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 8 plans complete. Ready for phase verification and then Phase 9 (persist + zero-row spy) / Phase 10 (Typer one-shot + UAT).

---
*Phase: 08-deepseek-article-templates*
*Completed: 2026-09-27*
