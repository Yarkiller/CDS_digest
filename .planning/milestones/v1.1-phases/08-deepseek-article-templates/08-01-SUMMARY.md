---
phase: 08-deepseek-article-templates
plan: 01
subsystem: ingestion
tags: [deepseek, openai, article-generator, templates, pydantic, uv]

requires:
  - phase: 06-ports-dtos
    provides: ArticleGenerator port, ArticleDraft, TemplateKind

provides:
  - DeepSeekArticleGenerator implementing ArticleGenerator with an injected async OpenAI client
  - Repository lecture.md and podcast.md templates with D-16 Russian headings
  - load_article_templates(root) loader
  - Settings DeepSeek fields (max_transcript_chars, deepseek_api_key, deepseek_base_url, deepseek_model)
  - build_async_deepseek_client and build_deepseek_article_generator factories
  - ConfigurationError for startup misconfiguration

affects:
  - 08-02 (ArticleError mapping)
  - 08-03 (character cap enforcement)
  - 08-04 (fake failures, translation suffix)
  - 09 (persist MaterialDraft)
  - 10 (Typer one-shot and provenance label)

actuals:
  tokens: 12000
  tasks: 2
  commits: 2

tech-stack:
  added: ["openai>=3.0,<4"]
  patterns:
    - Injected async OpenAI client with explicit timeout/max_retries/trust_env
    - Adapter reads no os.environ; Settings owns env
    - Shared system prompt + chosen template markdown in user message

key-files:
  created:
    - data-collection/src/data_collection/adapters/deepseek_article.py
    - data-collection/src/data_collection/templates/lecture.md
    - data-collection/src/data_collection/templates/podcast.md
    - data-collection/src/data_collection/templates/__init__.py
    - ingestion-service/src/ingestion_service/composition/config_error.py
    - tests/unit/test_article_templates.py
    - tests/unit/test_deepseek_article_adapter.py
  modified:
    - data-collection/pyproject.toml
    - ingestion-service/pyproject.toml
    - uv.lock
    - ingestion-service/src/ingestion_service/composition/settings.py
    - ingestion-service/src/ingestion_service/composition/clients.py
    - ingestion-service/src/ingestion_service/composition/__init__.py
    - tests/unit/test_ingestion_settings.py

key-decisions:
  - Kept ArticleDraft as the adapter return type; provenance stays out of the JSON (D-12).
  - System prompt is identical for lecture and podcast; template markdown varies (D-14).
  - Disabled thinking mode via extra_body and used response_format json_object (D-11).
  - max_transcript_chars is injected; adapters do not read os.environ (D-07).
  - ConfigurationError is a plain Exception, not an IngestError stage (D-17).

patterns-established:
  - "build_async_deepseek_client is the only AsyncOpenAI construction site with timeout 120.0, max_retries 0, trust_env False."
  - "build_deepseek_article_generator loads templates before constructing the client."

requirements-completed:
  - LLM-01
  - LLM-02
  - LLM-04

coverage:
  - id: D1
    description: "Stubbed DeepSeek chat completion returns a validated ArticleDraft for lecture and podcast."
    requirement: LLM-01
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_process_returns_article_draft_for_lecture"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_process_returns_article_draft_for_podcast"
        status: pass
    human_judgment: false
  - id: D2
    description: "Extra JSON keys are ignored; ArticleDraft has only title, dek, body_markdown."
    requirement: LLM-01
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_process_returns_article_draft_for_lecture"
        status: pass
    human_judgment: false
  - id: D3
    description: "TemplateKind lecture selects lecture.md headings; podcast selects podcast.md headings."
    requirement: LLM-02
    verification:
      - kind: unit
        ref: "tests/unit/test_article_templates.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_lecture_prompt_contains_lecture_headings_not_podcast"
        status: pass
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_podcast_prompt_contains_podcast_headings_not_lecture"
        status: pass
    human_judgment: false
  - id: D4
    description: "System prompt contains honesty, always-Russian, ru/en rules, preserved terms, and the word json."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_system_prompt_contains_honesty_and_language_rules"
        status: pass
    human_judgment: false
  - id: D5
    description: "create is called with response_format json_object and extra_body thinking disabled."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_create_kwargs_include_json_object_and_disabled_thinking"
        status: pass
    human_judgment: false
  - id: D6
    description: "Preserved technical tokens pgvector, RAG, embedding round-trip unchanged for ru and en."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_deepseek_article_adapter.py#test_preserved_technical_terms_round_trip_unchanged"
        status: pass
    human_judgment: false
  - id: D7
    description: "Settings.from_env({}) yields max_transcript_chars 80000 and DeepSeek defaults; blank key is allowed at settings load."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_ingestion_settings.py#test_settings_from_env_defaults"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingestion_settings.py#test_build_async_deepseek_client_rejects_blank_key"
        status: pass
    human_judgment: false
  - id: D8
    description: "build_deepseek_article_generator loads templates and constructs the generator; blank key raises ConfigurationError before AsyncOpenAI."
    requirement: LLM-04
    verification:
      - kind: unit
        ref: "tests/unit/test_ingestion_settings.py#test_build_deepseek_article_generator_rejects_blank_key"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-09-27
status: complete
---

# Phase 8 Plan 01: DeepSeek Happy Path & Templates Summary

**Stubbed DeepSeek OpenAI-compatible adapter returns validated ArticleDrafts using repository markdown lecture/podcast templates and an injected async client; Settings and composition factories own all DeepSeek env values.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-27T08:29:00Z
- **Completed:** 2026-09-27T08:45:00Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Added `openai>=3.0,<4` to `data-collection` and `ingestion-service`.
- Created `lecture.md` and `podcast.md` with locked D-16 Russian headings.
- Implemented `load_article_templates(root)` using `importlib.resources`.
- Implemented `DeepSeekArticleGenerator` with shared system prompt, template user message, `response_format={"type":"json_object"}`, and `extra_body={"thinking":{"type":"disabled"}}`.
- Extended `Settings` with `MAX_TRANSCRIPT_CHARS`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`.
- Added `ConfigurationError` and `build_async_deepseek_client`/`build_deepseek_article_generator` factories.
- Exported new composition symbols while keeping the public `data_collection.__all__` at seven names.

## Task Commits

1. **Task 1: Tracer — mocked DeepSeek JSON becomes ArticleDraft** - `8f8ed2b` (feat)
2. **Task 2: Inject DeepSeek settings and build client** - `79a15ca` (feat)

## Files Created/Modified
- `data-collection/src/data_collection/adapters/deepseek_article.py` - DeepSeekArticleGenerator, ARTICLE_SYSTEM_PROMPT, build_article_messages.
- `data-collection/src/data_collection/templates/lecture.md` - D-16 lecture headings.
- `data-collection/src/data_collection/templates/podcast.md` - D-16 podcast headings.
- `data-collection/src/data_collection/templates/__init__.py` - load_article_templates.
- `ingestion-service/src/ingestion_service/composition/config_error.py` - ConfigurationError.
- `ingestion-service/src/ingestion_service/composition/settings.py` - DeepSeek settings fields.
- `ingestion-service/src/ingestion_service/composition/clients.py` - Client and generator factories.
- `ingestion-service/src/ingestion_service/composition/__init__.py` - Re-exports.
- `tests/unit/test_article_templates.py` - Template file/loader tests.
- `tests/unit/test_deepseek_article_adapter.py` - Mocked adapter and prompt tests.
- `tests/unit/test_ingestion_settings.py` - Settings and factory tests.

## Decisions Made
- Followed D-12: adapter returns `ArticleDraft` only; provenance is caller-supplied in Phase 10.
- Used lowercase "json" in the system prompt to satisfy DeepSeek JSON-mode requirement.
- Set `timeout=120.0`, `max_retries=0`, and `trust_env=False` on the DeepSeek HTTP client.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `uv run pytest` full suite shows one pre-existing failure in `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` (response contains extra `sent_at`/`week_label` keys). This is unrelated to Phase 8 changes and was present before execution.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ready for 08-02: ArticleError taxonomy and `map_article_error`.
- Ready for 08-03: character-cap enforcement and `llm_truncation` mapping.

---
*Phase: 08-deepseek-article-templates*
*Completed: 2026-09-27*
