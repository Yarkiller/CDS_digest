---
phase: 08-deepseek-article-templates
reviewed: 2026-09-27T11:20:00Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - data-collection/pyproject.toml
  - data-collection/src/data_collection/adapters/deepseek_article.py
  - data-collection/src/data_collection/errors/article.py
  - data-collection/src/data_collection/templates/__init__.py
  - data-collection/src/data_collection/templates/lecture.md
  - data-collection/src/data_collection/templates/podcast.md
  - data-collection/src/data_collection/tests_support/fakes.py
  - docs/agents/local-platform-runbook.md
  - ingestion-service/pyproject.toml
  - ingestion-service/src/ingestion_service/composition/__init__.py
  - ingestion-service/src/ingestion_service/composition/clients.py
  - ingestion-service/src/ingestion_service/composition/config_error.py
  - ingestion-service/src/ingestion_service/composition/settings.py
  - ingestion-service/src/ingestion_service/mapping/__init__.py
  - ingestion-service/src/ingestion_service/mapping/article.py
  - ingestion-service/src/ingestion_service/provenance.py
  - tests/unit/test_article_error_mapping.py
  - tests/unit/test_article_templates.py
  - tests/unit/test_data_collection_public_api.py
  - tests/unit/test_deepseek_article_adapter.py
  - tests/unit/test_fake_article_generator.py
  - tests/unit/test_ingestion_settings.py
  - tests/unit/test_translation_marker.py
  - uv.lock
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
---

# Phase 08: Code Review Report

**Reviewed:** 2026-09-27T11:20:00Z
**Depth:** standard
**Files Reviewed:** 24
**Status:** issues_found

## Summary

Phase 8 introduces the DeepSeek article generator, error taxonomy, template loader, settings/composition factories, and provenance suffix. The implementation is solid: secrets are redacted, SDK errors are mapped to locked reasons, templates are loaded before client construction, and the public API surface is preserved. The test suite covers happy paths, failure modes, budget boundaries, and redaction.

One warning was found: the adapter indexes `response.choices[0]` without guarding against an empty choices list. The broad `except Exception` fallback prevents a crash but misclassifies the failure as `ArticleUnknownError` with an `IndexError` context instead of the more accurate `ArticleInvalidJson`. Two minor info items note weak typing / duplicated literals that do not affect runtime behavior.

## Warnings

### WR-01: Empty `response.choices` is not handled explicitly

**File:** `data-collection/src/data_collection/adapters/deepseek_article.py:149`
**Issue:** After a successful SDK call the code reads `response.choices[0].message.content` without first checking that `choices` is non-empty. If the API ever returns an empty choices list, Python raises `IndexError`, which is caught by the final `except Exception` block and mapped to `ArticleUnknownError` with `exception_class="IndexError"`. That classification is misleading for an invalid/malformed LLM response; it should be treated as invalid output, consistent with empty/null content handling.
**Fix:**
```python
content = response.choices[0].message.content if response.choices else None
if not isinstance(content, str) or content == "":
    raise ArticleInvalidJson(transcript.video_id)
```

## Info

### IN-01: `client` parameter typed as `Any` in adapter constructor

**File:** `data-collection/src/data_collection/adapters/deepseek_article.py:79`
**Issue:** The constructor accepts `client: Any`, weakening the module-boundary type contract. The adapter immediately calls OpenAI-SDK-specific methods, so a more specific type (e.g., a small protocol or `AsyncOpenAI`) would preserve static checks without changing runtime behavior.
**Fix:** Define a minimal protocol for the required `chat.completions.create` coroutine, or type the client as `AsyncOpenAI` if the project accepts the coupling.

### IN-02: Default DeepSeek base URL is duplicated

**File:** `ingestion-service/src/ingestion_service/composition/settings.py:34,49`
**Issue:** The literal `"https://api.deepseek.com"` appears twice in `Settings` defaults. This creates a maintenance hazard if the default ever changes.
**Fix:** Extract a module-level constant `_DEFAULT_DEEPSEEK_BASE_URL` and reference it in both places.

---

_Reviewed: 2026-09-27T11:20:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
