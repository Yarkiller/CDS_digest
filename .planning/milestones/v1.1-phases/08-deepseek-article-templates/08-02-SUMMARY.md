---
phase: 08-deepseek-article-templates
plan: 02
subsystem: ingestion
tags: [deepseek, article-error, ingest-error, error-mapping, redaction]

requires:
  - phase: 08-01
    provides: DeepSeekArticleGenerator, injected client, templates

provides:
  - ArticleError hierarchy with D-13 subtypes
  - DeepSeekArticleGenerator.process maps SDK/JSON/validation failures to ArticleError
  - map_article_error converting ArticleError to IngestError(stage=llm) with locked reasons
  - LLM_REASONS exact seven-reason frozenset
  - Redaction of transcript and API key from message/context/to_dict()

affects:
  - 08-03 (ArticleBudgetError → llm_truncation)
  - 09 (persist + zero-row spy)
  - 10 (operator diagnostics)

actuals:
  tokens: 9000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - Module-local ArticleError → IngestError mapper in ingestion-service
    - Context allowlist (video_id, exception_class, status_code)
    - Message built from reason, never str(exc)

key-files:
  created:
    - data-collection/src/data_collection/errors/article.py
    - ingestion-service/src/ingestion_service/mapping/article.py
    - tests/unit/test_article_error_mapping.py
  modified:
    - data-collection/src/data_collection/adapters/deepseek_article.py
    - ingestion-service/src/ingestion_service/mapping/__init__.py
    - tests/unit/test_deepseek_article_adapter.py

key-decisions:
  - SDK class names go into context only, never into reason (D-13).
  - provider_context_length is stage=llm, not llm_truncation (D-10).
  - ArticleBudgetError raises TypeError if mapped before 08-03 branch exists.
  - No transcript text, response body, or API key in message/context/to_dict().

patterns-established:
  - "Catch specific OpenAI exception subclasses first, then APIStatusError, then generic Exception."
  - "Classify provider_context_length from status_code 400 + code/type token containing context_length."

requirements-completed:
  - LLM-03

coverage:
  - id: D1
    description: "APITimeoutError and APIConnectionError raise ArticleNetworkError."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_timeout_error_raises_article_network_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_connection_error_raises_article_network_error"
        status: pass
    human_judgment: false
  - id: D2
    description: "RateLimitError and InternalServerError raise ArticleProviderError; one create call on rate limit."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_rate_limit_error_raises_article_provider_error_and_calls_create_once"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_internal_server_error_raises_article_provider_error"
        status: pass
    human_judgment: false
  - id: D3
    description: "AuthenticationError and PermissionDeniedError raise ArticleAuthError."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_authentication_error_raises_article_auth_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_permission_denied_error_raises_article_auth_error"
        status: pass
    human_judgment: false
  - id: D4
    description: "HTTP 400 with code/type containing context_length raises ArticleContextLengthError."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_status_400_code_context_length_raises_article_context_length_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_status_400_type_context_length_raises_article_context_length_error"
        status: pass
    human_judgment: false
  - id: D5
    description: "HTTP 402 raises ArticleUnknownError."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_status_402_raises_article_unknown_error"
        status: pass
    human_judgment: false
  - id: D6
    description: "Bad JSON (fences, null, empty, array, non-object) raises ArticleInvalidJson."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_fenced_json_raises_article_invalid_json"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_null_content_raises_article_invalid_json"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_empty_content_raises_article_invalid_json"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_json_array_raises_article_invalid_json"
        status: pass
    human_judgment: false
  - id: D7
    description: "ArticleDraft validation failure raises ArticleInvalidDraft."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_blank_title_raises_article_invalid_draft"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_missing_field_raises_article_invalid_draft"
        status: pass
    human_judgment: false
  - id: D8
    description: "asyncio.gather of one raising and one successful process returns ArticleDraft only from success."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_gather_of_raising_and_successful_process_returns_only_success_draft"
        status: pass
    human_judgment: false
  - id: D9
    description: "map_article_error produces stage=llm, locked reason, exit_code 1, and no transcript/key in message/context/to_dict()."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_article_error_mapping.py"
        status: pass
    human_judgment: false
  - id: D10
    description: "LLM_REASONS is exactly the seven locked reasons."
    requirement: LLM-03
    verification:
      - kind: unit
        ref: "tests/unit/test_article_error_mapping.py#test_llm_reasons_is_exact_seven_reason_set"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-09-27
status: complete
---

# Phase 8 Plan 02: ArticleError Taxonomy & Mapping Summary

**All DeepSeek SDK, JSON, and validation failures map to IngestError(stage=llm) with a locked reason and redacted diagnostics; no ArticleDraft is returned or stored.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-27T08:46:00Z
- **Completed:** 2026-09-27T09:01:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created `ArticleError` hierarchy with `ArticleNetworkError`, `ArticleProviderError`, `ArticleAuthError`, `ArticleContextLengthError`, `ArticleInvalidJson`, `ArticleInvalidDraft`, `ArticleUnknownError`, and `ArticleBudgetError` placeholder.
- Updated `DeepSeekArticleGenerator.process` to catch OpenAI exceptions and raise the appropriate `ArticleError` subtype without returning or storing a draft.
- Implemented `map_article_error` in `ingestion_service/mapping/article.py` with the exact seven `LLM_REASONS` and context allowlist.
- Added redaction tests proving transcript text and API key sentinel never appear in `message`, `to_dict()["message"]`, or `context`.
- Exported `map_article_error` from `ingestion_service.mapping`.

## Task Commits

1. **Task 1: Raise ArticleError for SDK failures and bad JSON** - `dd21d2b` (feat)
2. **Task 2: Map ArticleError to stage=llm with redacted diagnostics** - `41f5016` (feat)

## Files Created/Modified
- `data-collection/src/data_collection/errors/article.py` - ArticleError taxonomy.
- `data-collection/src/data_collection/adapters/deepseek_article.py` - SDK exception mapping.
- `ingestion-service/src/ingestion_service/mapping/article.py` - map_article_error, LLM_REASONS.
- `ingestion-service/src/ingestion_service/mapping/__init__.py` - Export map_article_error.
- `tests/unit/test_deepseek_article_adapter.py` - Failure and gather tests.
- `tests/unit/test_article_error_mapping.py` - Mapper reason/redaction tests.

## Decisions Made
- Provider context-length rejection stays `stage=llm`/`provider_context_length`, distinct from future local `llm_truncation`.
- ArticleBudgetError is declared but intentionally not mapped to `stage=llm`; mapping it raises TypeError until 08-03 adds the `llm_truncation` branch.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` failure remains unrelated to Phase 8.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ready for 08-03: character-cap enforcement and `llm_truncation` mapping.

---
*Phase: 08-deepseek-article-templates*
*Completed: 2026-09-27*
