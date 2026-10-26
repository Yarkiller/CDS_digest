---
phase: 8
slug: deepseek-article-templates
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-27
validated: 2026-10-02
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Commands sourced from `08-RESEARCH.md` Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | root `pyproject.toml` — `testpaths = ["tests/unit"]`; `integration` marker already registered |
| **Quick run command** | `uv run pytest tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_error_mapping.py tests/unit/test_article_templates.py tests/unit/test_ingestion_settings.py tests/unit/test_fake_article_generator.py tests/unit/test_translation_marker.py tests/unit/test_data_collection_public_api.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run the new unit file(s) with `-x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green. No live DeepSeek call required
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-draft | 01 | 1 | LLM-01 | T-08-INPUT | Mocked JSON object → `ArticleDraft`; extra keys ignored; provenance not read from JSON | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py tests/unit/test_assemble_material_draft.py -x` | ✅ | ✅ green |
| 08-templates | 01 | 1 | LLM-02 | — | `lecture` / `podcast` headings in package markdown; missing file raises before any client call | unit | `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py -x` | ✅ | ✅ green |
| 08-fail | 02 | 2 | LLM-03 | T-08-LEAK | Network, 429, 5xx, 401/403, fences, non-object JSON, blank field → `ArticleError`; message has no transcript or body | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_error_mapping.py -x` | ✅ | ✅ green |
| 08-budget | 03 | 3 | LLM-05 | T-08-CAP | `len == 80000` calls SDK; `80001` does not; context is only `char_count` + `max_chars` | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_error_mapping.py tests/unit/test_ingestion_settings.py -x` | ✅ | ✅ green |
| 08-honesty | 04 | 4 | LLM-04 | T-08-INJECT | System prompt: transcript-only, always Russian; `ru` format-only; `en` translate; preserve terms; exact suffix ` · пер. с англ.` | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py tests/unit/test_translation_marker.py -x` | ✅ | ✅ green |
| 08-fake | 04 | 4 | D-15 | — | Additive `FakeArticleGenerator(failures=…)` keyed by `video_id` | unit | `uv run pytest tests/unit/test_fake_article_generator.py tests/unit/test_article_generator_fake.py -x` | ✅ | ✅ green |
| 08-public | 04 | 4 | D-17 | T-08-KEY | Adapter modules do not read `os.environ`; new adapter and `ArticleError` stay off the package root `__all__` | unit | `uv run pytest tests/unit/test_data_collection_public_api.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

LLM-02 Typer `--template` and LLM-03 live zero-row persist proof are Phase 10 and Phase 9. They are not gates for this phase.

---

## Wave 0 Requirements

- [x] RED tests for `MAX_TRANSCRIPT_CHARS` default, blank, and invalid values without breaking `from_env({})`
- [x] RED tests for template headings and missing-file load
- [x] RED tests for mocked happy path, prompt rules, `ru`/`en` language passthrough, preserved tokens
- [x] RED tests for D-13 failures, fence rejection, budget boundary, SDK not called when over cap
- [x] RED tests for `map_article_error` allowlists and message redaction (`message` and `to_dict()`, not only `context`)
- [x] RED test for the exact English suffix constant ` · пер. с англ.`
- [x] RED test for additive `FakeArticleGenerator` failures
- [x] `uv add --package data-collection "openai>=3.0,<4"` then `uv sync` (when tests first import `openai`)
- [x] Extend runbook §1 with `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `MAX_TRANSCRIPT_CHARS` (names and defaults only)
- [x] Extend `NEGATIVE_ROOT_NAMES` with the new adapter and `ArticleError`
- [x] Assert this phase adds no Typer app, no Supabase writer, no migration, no `IngestError` stage

*Existing infrastructure: pytest + `tests/unit/` covers Phase 6 ports and Phase 7 adapters — extend, do not replace.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live DeepSeek draft quality (headings, Russian, honesty) | LLM-04 | Needs a key and a human reader | Phase 10 UAT, including one English source video |
| Real HTTP 400 body shape for context length | LLM-05 | Docs page did not yield a stable code sample | Optional integration; unit test stubs `status_code` and `code` |
| Wheel contains `lecture.md` / `podcast.md` | LLM-02 | Packaging | Check if a wheel is built; source-tree tests are the gate |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-02

---

## Validation Audit 2026-10-02

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Audit notes:
- State A: draft `08-VALIDATION.md` still marked pending after phase execution.
- Cross-check vs PLAN/SUMMARY/VERIFICATION + filesystem: all Per-Task automated commands resolve to existing unit files.
- Targeted Phase 8 unit files: **123 passed**.
- Manual-only rows unchanged (live DeepSeek quality, real HTTP 400 shape, wheel packaging).
- No auditor spawn — zero COVERED→MISSING/PARTIAL gaps.
