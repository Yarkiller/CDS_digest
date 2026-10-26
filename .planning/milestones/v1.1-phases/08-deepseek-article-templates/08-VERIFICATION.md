---
phase: 08-deepseek-article-templates
verified: 2026-09-27T09:30:00Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 17
  total: 17
  not_honored: []
advisory_review:
  source: null
  status: not_run
  critical: 0
  warning: 0
  info: 0
  note: "Code review capability not invoked during inline execution."
human_verification: []
next_action: "Phase 8 goal achieved. Proceed to Phase 9 (Draft Persist & Shortlist Enqueue)."
next_command: "/gsd-plan-phase 9"
---

# Phase 8: DeepSeek Article & Templates Verification Report

**Phase Goal:** Operator-facing article draft from a transcript via a DeepSeek OpenAI-compatible adapter; lecture/podcast templates; LLM failures and oversized transcripts fail closed with locked stages/reasons; no database writes.  
**Verified:** 2026-09-27T09:30:00Z  
**Status:** passed  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | DeepSeek adapter returns a validated `ArticleDraft` (title/dek/body_markdown) from a JSON object; extra keys ignored (LLM-01 / D-11 / D-12) | ✓ VERIFIED | `test_deepseek_article_adapter.py` happy-path tests; `ArticleDraft.model_validate` strips blanks |
| 2 | `TemplateKind.LECTURE` selects `lecture.md`, `PODCAST` selects `podcast.md`; chosen headings appear in user message (LLM-02 / D-14 / D-16) | ✓ VERIFIED | `test_article_templates.py` heading asserts; adapter prompt tests show correct template and absence of the other |
| 3 | System prompt enforces honesty, always-Russian, ru format-only, en translate, preserve terms; JSON mode with thinking disabled (LLM-04 / D-01…D-04) | ✓ VERIFIED | Substring tests in `test_deepseek_article_adapter.py`; `response_format={"type":"json_object"}`; `extra_body` disables thinking; preserved tokens round-trip |
| 4 | SDK/HTTP failures, bad JSON, and validation failures raise `ArticleError`, never return `ArticleDraft`, and map to `stage=llm` with D-13 reasons; no transcript or key in diagnostics (LLM-03 / D-13) | ✓ VERIFIED | Parametrized failure tests in `test_deepseek_article_adapter.py`; `test_article_error_mapping.py` reason/redaction tests; `LLM_REASONS` exact seven-reason set |
| 5 | Oversized transcripts raise `ArticleBudgetError` before SDK call and map to `stage=llm_truncation` with context `char_count`/`max_chars` only; bad caps raise `ConfigurationError` at settings load (LLM-05 / D-07…D-09) | ✓ VERIFIED | Budget boundary tests; mapping context test; invalid-cap parametrized tests |
| 6 | Provider context-length HTTP 400 maps to `stage=llm`/`provider_context_length`, not `llm_truncation` (D-10) | ✓ VERIFIED | Adapter context-length tests; mapping test |
| 7 | Missing/unreadable templates raise `TemplateLoadError` before `AsyncOpenAI` construction; not an `ArticleError`/`IngestError`/Stage (D-17) | ✓ VERIFIED | `test_article_templates.py` missing-file, unreadable, and generator-construction tests |
| 8 | `FakeArticleGenerator` supports optional `failures` keyed by `video_id`; success constructor unchanged (Phase 6 D-17) | ✓ VERIFIED | `test_fake_article_generator.py` |
| 9 | `ENGLISH_TRANSLATION_SUFFIX` locked as constant; adapter does not apply it or build a provenance label (D-05 / D-06) | ✓ VERIFIED | `test_translation_marker.py` exact string, adapter-source absence, no builder function |
| 10 | `data_collection.__all__` stays exactly seven names; adapter/errors/template loader off root; no typer/supabase imports; no new Stage (D-12 / D-17) | ✓ VERIFIED | `test_data_collection_public_api.py` negative names, Stage set, scope imports |

**Score:** 5/5 LLM must-haves verified (10 supporting truths)

### Deferred Items

- Live DeepSeek draft quality (Russian, headings, honesty) — Phase 10 UAT with a real key.
- Real HTTP 400 body shape for context length — optional integration; unit stubs cover the classification predicate.
- Wheel packaging contains `lecture.md`/`podcast.md` — not verified; source-tree tests are the gate.
- Live zero-row spy (`persist.calls == []`) — Phase 9.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------- | ------- |
| `data-collection/.../adapters/deepseek_article.py` | DeepSeekArticleGenerator + SDK mapping | ✓ VERIFIED | Happy path + D-13 failure taxonomy |
| `data-collection/.../errors/article.py` | ArticleError hierarchy | ✓ VERIFIED | 8 subtypes incl. ArticleBudgetError |
| `data-collection/.../templates/lecture.md` | D-16 lecture headings | ✓ VERIFIED | Package markdown |
| `data-collection/.../templates/podcast.md` | D-16 podcast headings | ✓ VERIFIED | Package markdown |
| `data-collection/.../templates/__init__.py` | load_article_templates + TemplateLoadError | ✓ VERIFIED | Fail-at-load |
| `data-collection/.../tests_support/fakes.py` | FakeArticleGenerator failures | ✓ VERIFIED | Additive optional arg |
| `ingestion-service/.../composition/settings.py` | DeepSeek settings + cap validation | ✓ VERIFIED | Defaults + ConfigurationError |
| `ingestion-service/.../composition/config_error.py` | ConfigurationError | ✓ VERIFIED | Plain Exception |
| `ingestion-service/.../composition/clients.py` | build_async_deepseek_client / build_deepseek_article_generator | ✓ VERIFIED | timeout 120, max_retries 0, trust_env False |
| `ingestion-service/.../mapping/article.py` | map_article_error + LLM_REASONS | ✓ VERIFIED | Seven reasons + llm_truncation branch |
| `ingestion-service/.../mapping/__init__.py` | Exports map_article_error | ✓ VERIFIED | Added to __all__ |
| `ingestion-service/.../provenance.py` | ENGLISH_TRANSLATION_SUFFIX | ✓ VERIFIED | Constant only |
| `docs/agents/local-platform-runbook.md` | DeepSeek env names + defaults | ✓ VERIFIED | No live key |
| Phase-8 unit tests (6 files) | Behavioral coverage | ✓ VERIFIED | 73 passed this run |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | ---- | ------ | -------- |
| `Transcript` + `TemplateKind` | `ArticleDraft` | `DeepSeekArticleGenerator.process` | ✓ WIRED | Injected client, JSON mode, model_validate |
| SDK exceptions | `ArticleError` subtype | adapter `except` chain | ✓ WIRED | Specific subclasses + APIStatusError fallback |
| `ArticleError` | `IngestError(stage=llm)` | `map_article_error` | ✓ WIRED | Locked reasons + context allowlist |
| `ArticleBudgetError` | `IngestError(stage=llm_truncation)` | `map_article_error` | ✓ WIRED | char_count/max_chars only |
| `Settings.from_env` | `AsyncOpenAI` | `build_async_deepseek_client` | ✓ WIRED | Blank key raises ConfigurationError before construction |
| `load_article_templates` | template strings | `build_deepseek_article_generator` | ✓ WIRED | Called before client construction |
| `FakeArticleGenerator.failures` | `ArticleError` raise | tests_support | ✓ WIRED | Keyed by video_id |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `DeepSeekArticleGenerator` | `ArticleDraft` | stub OpenAI client JSON | Yes (validated three-field object) | ✓ FLOWING |
| `build_article_messages` | `messages` | system prompt + template + transcript.language + transcript.text | Yes | ✓ FLOWING |
| `map_article_error` | `IngestError.to_dict()` | `ArticleError` subtype | Yes (locked stage/reason/exit_code) | ✓ FLOWING |
| `FakeArticleGenerator` | raise / return | scripted failures map | Yes (in-memory catalog) | ✓ FLOWING |
| Persist / DB | rows | — | N/A this phase | ✓ DEFERRED |

No hollow stubs on the DeepSeek happy or fail-closed unit paths.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase-8 targeted unit suite | `uv run pytest tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_error_mapping.py tests/unit/test_article_templates.py tests/unit/test_ingestion_settings.py tests/unit/test_fake_article_generator.py tests/unit/test_translation_marker.py tests/unit/test_data_collection_public_api.py -q` | **73 passed** | ✓ PASS |
| Full unit suite | `uv run pytest` | **497 passed, 1 failed** | ⚠️ ADVISORY |
| Pre-existing failure | `tests/unit/test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` | Extra `sent_at`/`week_label` keys in response | ⚠️ UNRELATED |

The single failing test is in the backend admin shortlist path and is unrelated to Phase 8 changes; it was failing before Phase 8 execution began.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| LLM-01 | 08-01 | DeepSeek returns validated article output (ArticleDraft) | ✓ SATISFIED | Adapter happy path + assembler unchanged |
| LLM-02 | 08-01 | TemplateKind selects lecture/podcast markdown | ✓ SATISFIED | Template loader + prompt tests |
| LLM-03 | 08-02 | Failures exit non-zero stage=llm, no partial output, no DB rows | ✓ SATISFIED | ArticleError + mapper + unit proof |
| LLM-04 | 08-01, 08-04 | Always-Russian honesty prompt + translation suffix constant | ✓ SATISFIED | System prompt tests + suffix constant |
| LLM-05 | 08-03 | Over-budget transcripts fail stage=llm_truncation | ✓ SATISFIED | Budget check + mapping |

**Orphaned requirements:** None.

### Decision Coverage (08-CONTEXT.md)

| Decision | Status | Evidence |
| -------- | ------ | -------- |
| D-01 Always Russian output | ✓ Honored | System prompt + tests |
| D-02 ru format-only / en translate | ✓ Honored | Prompt substrings + language passthrough |
| D-03 No runtime language detector | ✓ Honored | No detector module added |
| D-04 Preserved terms (pgvector/RAG/embedding) | ✓ Honored | Round-trip equality tests |
| D-05 Suffix constant only | ✓ Honored | `provenance.py` constant; adapter source clean |
| D-06 English-only marker map | ✓ Honored | Single suffix constant |
| D-07 MAX_TRANSCRIPT_CHARS default/validation | ✓ Honored | Settings tests |
| D-08 Cap on transcript.text only | ✓ Honored | Budget check first line; template ignored |
| D-09 llm_truncation context | ✓ Honored | char_count + max_chars only |
| D-10 Provider context-length is stage=llm | ✓ Honored | Adapter + mapping tests |
| D-11 JSON object via response_format/json.loads | ✓ Honored | Adapter implementation + fence-rejection tests |
| D-12 ArticleDraft only, no provenance in JSON | ✓ Honored | Happy path + translation-marker tests |
| D-13 Locked LLM reason set | ✓ Honored | LLM_REASONS exact seven |
| D-14 Shared system prompt | ✓ Honored | Same constant for both templates |
| D-15 No heading validation | ✓ Honored | Plain body test passes |
| D-16 Russian heading strings | ✓ Honored | Template file tests |
| D-17 Missing template is startup error, not stage | ✓ Honored | TemplateLoadError + ConfigurationError |

### Prohibitions

| Prohibition | Tier | Status | Evidence |
| ----------- | ---- | ------ | -------- |
| No `os.environ`/`os.getenv` in adapters | test | ✓ Held | `test_adapters_do_not_read_environ` covers deepseek_article.py |
| No `stage` vocabulary in data-collection | test | ✓ Held | No stage imports in adapter/errors |
| No partial `ArticleDraft` on failure | test | ✓ Held | Every failure path raises before return |
| No transcript/API key in message/context | test | ✓ Held | Redaction tests in mapping suite |
| No SDK class names as operator `reason` | test | ✓ Held | LLM_REASONS exact locked set |
| No database writes / migrations this phase | test | ✓ Held | No supabase migrations; no persist ports |
| No Typer app / supabase import in data-collection | test | ✓ Held | Scope tests pass |
| No fence-stripping / JSON salvage | test | ✓ Held | Fenced content → ArticleInvalidJson |
| No tokenizer / chunker / silent truncation | test | ✓ Held | Python `len()` only; no slice |
| No provenance label builder in Phase 8 | test | ✓ Held | provenance.py constant only |

### Anti-Patterns Found

None blocking.

### Human Verification Required

None — all must-haves are unit-testable contracts. Live draft quality remains Phase 10 UAT.

### Gaps Summary

No gaps found against phase goal / LLM-01…LLM-05 / roadmap success criteria. Phase goal achieved.

Advisory note: one unrelated pre-existing unit failure in `test_http_admin.py` remains; it does not affect Phase 8 contracts.

---

## Verification Metadata

**Verification approach:** Goal-backward (roadmap SCs + PLAN must_haves from 08-01…08-04)  
**Must-haves source:** `.planning/ROADMAP.md` Phase 8 Success Criteria + four PLAN frontmatters  
**Automated checks:** 73 phase-8 tests passed; full suite 497 passed, 1 unrelated failure  
**Human checks required:** 0  
**Advisory review:** Not run (inline execution)

---
_Verified: 2026-09-27T09:30:00Z_  
_Verifier: Claude (inline orchestrator)_
