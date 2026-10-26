---
phase: 08-deepseek-article-templates
fixed: 2026-09-27T11:30:00Z
iteration: 1
fix_scope: critical_warning
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 08: Code Review Fix Report

**Fixed:** 2026-09-27T11:30:00Z
**Iteration:** 1
**Fix Scope:** critical_warning
**Findings in Scope:** 1
**Fixed:** 1
**Skipped:** 0
**Status:** all_fixed

## Summary

One warning from `08-REVIEW.md` was in scope for `--fix` (default: critical + warning). The empty-`response.choices` handling was fixed and a new unit test was added to lock the behavior.

## Applied Fixes

### WR-01: Empty `response.choices` now raises `ArticleInvalidJson`

**Finding:** `data-collection/src/data_collection/adapters/deepseek_article.py:149` — the adapter indexed `response.choices[0]` without checking for an empty choices list. An empty list caused an unhandled `IndexError` instead of the expected `ArticleError`.

**Fix:**
```python
content = response.choices[0].message.content if response.choices else None
```

This makes the existing `isinstance(content, str)` / empty-string guard raise `ArticleInvalidJson`, consistent with null and empty content handling.

**Files changed:**
- `data-collection/src/data_collection/adapters/deepseek_article.py`
- `tests/unit/test_deepseek_article_adapter.py`

**Test added:** `test_empty_choices_raises_article_invalid_json` — asserts that a stub client returning `choices=[]` raises `ArticleInvalidJson`.

## Verification

```bash
uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_error_mapping.py tests/unit/test_fake_article_generator.py tests/unit/test_translation_marker.py tests/unit/test_data_collection_public_api.py tests/unit/test_ingestion_settings.py -q
```

Result: **101 passed**.

## Skipped Findings

None.

---

_Fixed: 2026-09-27T11:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
