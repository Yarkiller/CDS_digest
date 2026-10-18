---
status: complete
phase: 08-deepseek-article-templates
source:
  - 08-01-SUMMARY.md
  - 08-02-SUMMARY.md
  - 08-03-SUMMARY.md
  - 08-04-SUMMARY.md
started: 2026-09-27T11:29:08.780Z
updated: 2026-09-27T11:36:00.000Z
---

## Current Test

[testing complete]

## Tests

### 1. Stubbed DeepSeek chat completion returns a validated ArticleDraft for lecture and podcast.
expected: |
  Stubbed DeepSeek chat completion returns a validated ArticleDraft for lecture and podcast.
result: pass
source: automated
coverage_id: D1
requirement: LLM-01
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_process_returns_article_draft_for_lecture (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_process_returns_article_draft_for_podcast (pass)

### 2. Extra JSON keys are ignored; ArticleDraft has only title, dek, body_markdown.
expected: |
  Extra JSON keys are ignored; ArticleDraft has only title, dek, body_markdown.
result: pass
source: automated
coverage_id: D2
requirement: LLM-01
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_process_returns_article_draft_for_lecture (pass)

### 3. TemplateKind lecture selects lecture.md headings; podcast selects podcast.md headings.
expected: |
  TemplateKind lecture selects lecture.md headings; podcast selects podcast.md headings.
result: pass
source: automated
coverage_id: D3
requirement: LLM-02
verification:
  - unit: tests/unit/test_article_templates.py (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_lecture_prompt_contains_lecture_headings_not_podcast (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_podcast_prompt_contains_podcast_headings_not_lecture (pass)

### 4. System prompt contains honesty, always-Russian, ru/en rules, preserved terms, and the word json.
expected: |
  System prompt contains honesty, always-Russian, ru/en rules, preserved terms, and the word json.
result: pass
source: automated
coverage_id: D4
requirement: LLM-04
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_system_prompt_contains_honesty_and_language_rules (pass)

### 5. create is called with response_format json_object and extra_body thinking disabled.
expected: |
  create is called with response_format json_object and extra_body thinking disabled.
result: pass
source: automated
coverage_id: D5
requirement: LLM-04
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_create_kwargs_include_json_object_and_disabled_thinking (pass)

### 6. Preserved technical tokens pgvector, RAG, embedding round-trip unchanged for ru and en.
expected: |
  Preserved technical tokens pgvector, RAG, embedding round-trip unchanged for ru and en.
result: pass
source: automated
coverage_id: D6
requirement: LLM-04
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_preserved_technical_terms_round_trip_unchanged (pass)

### 7. Settings.from_env({}) yields max_transcript_chars 80000 and DeepSeek defaults; blank key is allowed at settings load.
expected: |
  Settings.from_env({}) yields max_transcript_chars 80000 and DeepSeek defaults; blank key is allowed at settings load.
result: pass
source: automated
coverage_id: D7
requirement: LLM-04
verification:
  - unit: tests/unit/test_ingestion_settings.py#test_settings_from_env_defaults (pass)
  - unit: tests/unit/test_ingestion_settings.py#test_build_async_deepseek_client_rejects_blank_key (pass)

### 8. build_deepseek_article_generator loads templates and constructs the generator; blank key raises ConfigurationError before AsyncOpenAI.
expected: |
  build_deepseek_article_generator loads templates and constructs the generator; blank key raises ConfigurationError before AsyncOpenAI.
result: pass
source: automated
coverage_id: D8
requirement: LLM-04
verification:
  - unit: tests/unit/test_ingestion_settings.py#test_build_deepseek_article_generator_rejects_blank_key (pass)

### 9. APITimeoutError and APIConnectionError raise ArticleNetworkError.
expected: |
  APITimeoutError and APIConnectionError raise ArticleNetworkError.
result: pass
source: automated
coverage_id: D1
requirement: LLM-03
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_timeout_error_raises_article_network_error (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_connection_error_raises_article_network_error (pass)

### 10. RateLimitError and InternalServerError raise ArticleProviderError; one create call on rate limit.
expected: |
  RateLimitError and InternalServerError raise ArticleProviderError; one create call on rate limit.
result: pass
source: automated
coverage_id: D2
requirement: LLM-03
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_rate_limit_error_raises_article_provider_error_and_calls_create_once (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_internal_server_error_raises_article_provider_error (pass)

### 11. AuthenticationError and PermissionDeniedError raise ArticleAuthError.
expected: |
  AuthenticationError and PermissionDeniedError raise ArticleAuthError.
result: pass
source: automated
coverage_id: D3
requirement: LLM-03
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_authentication_error_raises_article_auth_error (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_permission_denied_error_raises_article_auth_error (pass)

### 12. HTTP 400 with code/type containing context_length raises ArticleContextLengthError.
expected: |
  HTTP 400 with code/type containing context_length raises ArticleContextLengthError.
result: pass
source: automated
coverage_id: D4
requirement: LLM-03
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_status_400_code_context_length_raises_article_context_length_error (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_status_400_type_context_length_raises_article_context_length_error (pass)

### 13. HTTP 402 raises ArticleUnknownError.
expected: |
  HTTP 402 raises ArticleUnknownError.
result: pass
source: automated
coverage_id: D5
requirement: LLM-03
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_status_402_raises_article_unknown_error (pass)

### 14. Bad JSON (fences, null, empty, array, non-object) raises ArticleInvalidJson.
expected: |
  Bad JSON (fences, null, empty, array, non-object) raises ArticleInvalidJson.
result: pass
source: automated
coverage_id: D6
requirement: LLM-03
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_fenced_json_raises_article_invalid_json (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_null_content_raises_article_invalid_json (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_empty_content_raises_article_invalid_json (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_json_array_raises_article_invalid_json (pass)

### 15. ArticleDraft validation failure raises ArticleInvalidDraft.
expected: |
  ArticleDraft validation failure raises ArticleInvalidDraft.
result: pass
source: automated
coverage_id: D7
requirement: LLM-03
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_blank_title_raises_article_invalid_draft (pass)
  - unit: tests/unit/test_deepseek_article_adapter.py#test_missing_field_raises_article_invalid_draft (pass)

### 16. asyncio.gather of one raising and one successful process returns ArticleDraft only from success.
expected: |
  asyncio.gather of one raising and one successful process returns ArticleDraft only from success.
result: pass
source: automated
coverage_id: D8
requirement: LLM-03
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_gather_of_raising_and_successful_process_returns_only_success_draft (pass)

### 17. map_article_error produces stage=llm, locked reason, exit_code 1, and no transcript/key in message/context/to_dict().
expected: |
  map_article_error produces stage=llm, locked reason, exit_code 1, and no transcript/key in message/context/to_dict().
result: pass
source: automated
coverage_id: D9
requirement: LLM-03
verification:
  - unit: tests/unit/test_article_error_mapping.py (pass)

### 18. LLM_REASONS is exactly the seven locked reasons.
expected: |
  LLM_REASONS is exactly the seven locked reasons.
result: pass
source: automated
coverage_id: D10
requirement: LLM-03
verification:
  - unit: tests/unit/test_article_error_mapping.py#test_llm_reasons_is_exact_seven_reason_set (pass)

### 19. len(transcript.text) > max_transcript_chars raises ArticleBudgetError before create is called.
expected: |
  len(transcript.text) > max_transcript_chars raises ArticleBudgetError before create is called.
result: pass
source: automated
coverage_id: D1
requirement: LLM-05
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_over_max_chars_does_not_call_create (pass)

### 20. len(transcript.text) == max_transcript_chars still calls create.
expected: |
  len(transcript.text) == max_transcript_chars still calls create.
result: pass
source: automated
coverage_id: D2
requirement: LLM-05
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_exactly_max_chars_calls_create (pass)

### 21. Template length is not added to the character count.
expected: |
  Template length is not added to the character count.
result: pass
source: automated
coverage_id: D3
requirement: LLM-05
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_long_template_with_short_transcript_does_not_raise_budget_error (pass)

### 22. 80000 Cyrillic code points (UTF-8 byte length > cap) still call create.
expected: |
  80000 Cyrillic code points (UTF-8 byte length > cap) still call create.
result: pass
source: automated
coverage_id: D4
requirement: LLM-05
verification:
  - unit: tests/unit/test_deepseek_article_adapter.py#test_eighty_thousand_cyrillic_chars_call_create (pass)

### 23. ArticleBudgetError maps to stage=llm_truncation with context char_count and max_chars only.
expected: |
  ArticleBudgetError maps to stage=llm_truncation with context char_count and max_chars only.
result: pass
source: automated
coverage_id: D5
requirement: LLM-05
verification:
  - unit: tests/unit/test_article_error_mapping.py#test_article_budget_error_maps_to_llm_truncation (pass)

### 24. Non-integer, zero, or negative MAX_TRANSCRIPT_CHARS raise ConfigurationError at from_env.
expected: |
  Non-integer, zero, or negative MAX_TRANSCRIPT_CHARS raise ConfigurationError at from_env.
result: pass
source: automated
coverage_id: D6
requirement: LLM-05
verification:
  - unit: tests/unit/test_ingestion_settings.py#test_invalid_max_transcript_chars_raises_configuration_error (pass)

### 25. Missing lecture.md or podcast.md raises TemplateLoadError.
expected: |
  Missing lecture.md or podcast.md raises TemplateLoadError.
result: pass
source: automated
coverage_id: D7
requirement: LLM-05
verification:
  - unit: tests/unit/test_article_templates.py#test_missing_lecture_md_raises_template_load_error (pass)
  - unit: tests/unit/test_article_templates.py#test_missing_podcast_md_raises_template_load_error (pass)

### 26. Unreadable template raises TemplateLoadError; AsyncOpenAI is not constructed.
expected: |
  Unreadable template raises TemplateLoadError; AsyncOpenAI is not constructed.
result: pass
source: automated
coverage_id: D8
requirement: LLM-05
verification:
  - unit: tests/unit/test_article_templates.py#test_unreadable_template_raises_template_load_error (pass)
  - unit: tests/unit/test_article_templates.py#test_build_deepseek_article_generator_with_missing_template_does_not_construct_async_openai (pass)

### 27. TemplateLoadError is not a subclass of ArticleError or IngestError.
expected: |
  TemplateLoadError is not a subclass of ArticleError or IngestError.
result: pass
source: automated
coverage_id: D9
requirement: LLM-05
verification:
  - unit: tests/unit/test_article_templates.py#test_template_load_error_is_not_article_error_or_ingest_error (pass)

### 28. FakeArticleGenerator(result) still returns the scripted draft and records the call.
expected: |
  FakeArticleGenerator(result) still returns the scripted draft and records the call.
result: pass
source: automated
coverage_id: D1
requirement: LLM-04
verification:
  - unit: tests/unit/test_fake_article_generator.py#test_fake_article_generator_without_failures_still_works (pass)

### 29. FakeArticleGenerator failures map raises the scripted ArticleError after recording the call.
expected: |
  FakeArticleGenerator failures map raises the scripted ArticleError after recording the call.
result: pass
source: automated
coverage_id: D2
requirement: LLM-04
verification:
  - unit: tests/unit/test_fake_article_generator.py#test_fake_article_generator_failure_by_video_id (pass)

### 30. ENGLISH_TRANSLATION_SUFFIX equals the exact locked string.
expected: |
  ENGLISH_TRANSLATION_SUFFIX equals the exact locked string.
result: pass
source: automated
coverage_id: D3
requirement: LLM-04
verification:
  - unit: tests/unit/test_translation_marker.py#test_english_translation_suffix_is_exact_string (pass)

### 31. Suffix and provenance_label are absent from the adapter source.
expected: |
  Suffix and provenance_label are absent from the adapter source.
result: pass
source: automated
coverage_id: D4
requirement: LLM-04
verification:
  - unit: tests/unit/test_translation_marker.py#test_suffix_is_absent_from_adapter_source (pass)

### 32. provenance.py has no label builder that interpolates metadata.author.
expected: |
  provenance.py has no label builder that interpolates metadata.author.
result: pass
source: automated
coverage_id: D5
requirement: LLM-04
verification:
  - unit: tests/unit/test_translation_marker.py#test_provenance_module_has_no_label_builder (pass)

### 33. data_collection.__all__ stays exactly seven names; new adapter/error/template loader are negative names.
expected: |
  data_collection.__all__ stays exactly seven names; new adapter/error/template loader are negative names.
result: pass
source: automated
coverage_id: D6
requirement: LLM-04
verification:
  - unit: tests/unit/test_data_collection_public_api.py#test_public_all_is_exactly_seven_ingestion_names (pass)
  - unit: tests/unit/test_data_collection_public_api.py#test_negative_names_not_importable_from_package_root (pass)

### 34. IngestError Stage set is unchanged.
expected: |
  IngestError Stage set is unchanged.
result: pass
source: automated
coverage_id: D7
requirement: LLM-04
verification:
  - unit: tests/unit/test_data_collection_public_api.py#test_stage_set_is_unchanged (pass)

### 35. No ingestion-service Python file imports typer; no data-collection Python file imports supabase.
expected: |
  No ingestion-service Python file imports typer; no data-collection Python file imports supabase.
result: pass
source: automated
coverage_id: D8
requirement: LLM-04
verification:
  - unit: tests/unit/test_data_collection_public_api.py#test_ingestion_service_has_no_typer_import (pass)
  - unit: tests/unit/test_data_collection_public_api.py#test_data_collection_has_no_supabase_import (pass)

### 36. Runbook documents DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MAX_TRANSCRIPT_CHARS with defaults and no live key.
expected: |
  Runbook documents DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MAX_TRANSCRIPT_CHARS with defaults and no live key.
result: pass
coverage_id: D9
requirement: LLM-04
rationale: Runbook prose review is manual; automated tests verify absence of sk- live-key shape and symbol scope.

## Summary

total: 36
passed: 36
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
