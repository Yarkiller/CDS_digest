---
phase: 30-classifier-practical-conceptual
plan: 02
subsystem: ingestion-classifier
tags: [topic-kind, practical, conceptual, deepseek, json_object, ports-adapters, tdd]

requires:
  - phase: 30-classifier-practical-conceptual
    provides: TopicKindClassifier Protocol, normalize_topic_kind, required classifier= spine
provides:
  - DeepSeekTopicKindClassifier cheap json_object adapter (stream=False, max_tokens=128)
  - D-01…D-08 classifier system prompt with fenced transcript head+tail
  - build_deepseek_topic_kind_classifier wired into build_ingest_deps and build_collect_deps
affects: [30-03-guide-strip, 30-04-migration-014, 31-tavily-quota]

actuals:
  tokens: 5279
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - Cheap classifier call inverts pass-1: stream=False + max_tokens=128, never ArticleError
    - Unwrap only payload["topic_kind"]; sibling keys and empty content stay KIND-02 conceptual
    - Composition factory clones build_async_deepseek_client (trust_env=False), no new env var

key-files:
  created:
    - data-collection/src/data_collection/adapters/deepseek_classifier.py
    - tests/unit/test_deepseek_classifier.py
  modified:
    - ingestion-service/src/ingestion_service/composition/clients.py
    - ingestion-service/src/ingestion_service/composition/__init__.py
    - ingestion-service/src/ingestion_service/cli.py
    - ingestion-service/src/ingestion_service/collect_cli.py
    - tests/unit/test_build_ingest_deps_wiring.py
    - tests/unit/test_ingestion_clients.py

key-decisions:
  - "Classifier create is json_object + thinking.disabled + stream=False + max_tokens=128; pass-1 stays stream=True with no max_tokens"
  - "Adapter unwraps only topic_kind; sibling key kind and empty content return a KIND-02 miss, never ArticleError"
  - "build_deepseek_topic_kind_classifier reuses build_async_deepseek_client and settings.deepseek_model; no templates, no new env var"
  - "D-08 unsure→practical lives only in the prompt sentence; code still allowlists via Plan 01 normalize_topic_kind"

patterns-established:
  - "Pattern: classifier adapter is module-private; composition is the only live constructor"
  - "Pattern: transcript is fenced untrusted data; body_markdown is never sent (Pitfall 3 / T-30-01)"
  - "Pattern: transport errors raise generic Exception (pipeline swallows); empty JSON returns None"

requirements-completed: [KIND-01, KIND-02]

coverage:
  - id: D1
    description: "DeepSeekTopicKindClassifier issues one non-stream json_object create with thinking.disabled and max_tokens=128; prompt contains json plus {\"topic_kind\": \"conceptual\"} (KIND-01)"
    requirement: KIND-01
    verification:
      - kind: unit
        ref: tests/unit/test_deepseek_classifier.py#test_create_kwargs_are_json_object_non_stream_with_max_tokens
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_classifier.py#test_messages_contain_json_word_and_topic_kind_example
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_article_adapter.py#test_create_kwargs_include_json_object_and_disabled_thinking
        status: pass
    human_judgment: false
  - id: D2
    description: "Classifier system prompt encodes D-01…D-08 literals (named product, followable without the video, named products, job of the page, do vs understand, minutes not counted, unsure→practical)"
    requirement: KIND-01
    verification:
      - kind: unit
        ref: tests/unit/test_deepseek_classifier.py#test_system_prompt_encodes_d01_through_d08_literals
        status: pass
    human_judgment: false
  - id: D3
    description: "Adapter unwraps only topic_kind; sibling key kind, empty content, and transport errors are KIND-02 misses with no ArticleError (T-30-02, T-30-03)"
    requirement: KIND-02
    verification:
      - kind: unit
        ref: tests/unit/test_deepseek_classifier.py#test_topic_kind_practical_payload_unwraps_to_practical
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_classifier.py#test_sibling_kind_key_does_not_launder_practical
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_classifier.py#test_empty_content_maps_to_conceptual_without_article_error
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_classifier.py#test_transport_error_does_not_raise_article_error
        status: pass
      - kind: unit
        ref: tests/unit/test_deepseek_classifier.py#test_adapter_source_does_not_import_article_errors
        status: pass
    human_judgment: false
  - id: D4
    description: "build_ingest_deps and build_collect_deps wire build_deepseek_topic_kind_classifier; composition.__all__ exports the factory; blank DEEPSEEK_API_KEY still raises ConfigurationError (KIND-01)"
    requirement: KIND-01
    verification:
      - kind: unit
        ref: tests/unit/test_build_ingest_deps_wiring.py#test_build_ingest_deps_wires_four_ports_via_monkeypatched_factories
        status: pass
      - kind: unit
        ref: tests/unit/test_build_ingest_deps_wiring.py#test_build_collect_deps_source_wires_classifier_factory
        status: pass
      - kind: unit
        ref: tests/unit/test_ingestion_clients.py#test_composition_exports_supabase_factories
        status: pass
      - kind: unit
        ref: tests/unit/test_ingestion_clients.py#test_build_deepseek_topic_kind_classifier_rejects_blank_key
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-29
status: complete
---

# Phase 30 Plan 02: Cheap DeepSeek classifier adapter Summary

**Separate DeepSeek `json_object` classifier (`stream=False`, `max_tokens=128`) with D-01…D-08 prompt, fail-soft unwrap, and live `build_ingest_deps` / `build_collect_deps` wiring**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-29T03:14:00Z
- **Completed:** 2026-10-29T03:20:32Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- `DeepSeekTopicKindClassifier` issues one non-stream `chat.completions.create` with `json_object`, `thinking.disabled`, `stream=False`, and `max_tokens=128`; the prompt contains `json` plus `{"topic_kind": "conceptual"}`.
- System prompt pins D-01…D-08 (named product + followable without the video, named products, job of the page, do vs understand, do not count minutes, unsure→practical). User message sends title, dek, and a fenced transcript head 8000 + tail 4000; `body_markdown` is never sent.
- Adapter unwraps only `topic_kind`. Sibling key `kind`, empty content, and transport errors are KIND-02 misses — no `ArticleError`, no `stage=llm`. Pass-1 stays streamed and fail-closed.
- `build_deepseek_topic_kind_classifier` reuses `build_async_deepseek_client` (`trust_env=False`) and is wired into ingest and collect composition. No new packages or env vars.

## RED assertions (Task 1)

Command: `uv run pytest tests/unit/test_deepseek_classifier.py -x`

- `test_create_kwargs_are_json_object_non_stream_with_max_tokens` — `ModuleNotFoundError: No module named 'data_collection.adapters.deepseek_classifier'`

## RED assertions (Task 2)

Command: `uv run pytest tests/unit/test_build_ingest_deps_wiring.py tests/unit/test_ingestion_clients.py -x`

- `test_build_ingest_deps_source_delegates_to_composition_factories` — `'build_deepseek_topic_kind_classifier' not in build_ingest_deps source`

## GREEN command output

- Task 1: `14 passed` (`uv run pytest tests/unit/test_deepseek_classifier.py tests/unit/test_deepseek_article_adapter.py::test_create_kwargs_include_json_object_and_disabled_thinking -x`)
- Task 2: `35 passed` (`uv run pytest tests/unit/test_build_ingest_deps_wiring.py tests/unit/test_ingestion_clients.py tests/unit/test_cli_ingest_contract.py tests/unit/test_collect_cli_contract.py -q`)
- Plan gate: `37 passed`
- Wave gate: `1254 passed, 1 warning` (`uv run pytest tests/unit -q`)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: failing tests for DeepSeekTopicKindClassifier** - `68cea60` (test)
2. **Task 1 GREEN: implement DeepSeekTopicKindClassifier** - `bf5347e` (feat)
3. **Task 2 RED: failing tests for classifier composition wiring** - `296b6ad` (test)
4. **Task 2 GREEN: wire DeepSeek topic-kind classifier in composition** - `41a6684` (feat)

**Plan metadata:** (docs commit after this file)

_Note: TDD tasks have multiple commits (test → feat)_

## Files Created/Modified

- `data-collection/src/data_collection/adapters/deepseek_classifier.py` — module-private adapter; D-01…D-08 prompt; fenced head+tail transcript
- `tests/unit/test_deepseek_classifier.py` — create-kwargs, prompt literals, unwrap, fail-soft, pass-1 isolation
- `ingestion-service/src/ingestion_service/composition/clients.py` — `build_deepseek_topic_kind_classifier`
- `ingestion-service/src/ingestion_service/composition/__init__.py` — exports the factory
- `ingestion-service/src/ingestion_service/cli.py` — `classifier=` on `build_ingest_deps`
- `ingestion-service/src/ingestion_service/collect_cli.py` — `classifier=` on `CollectDeps`
- `tests/unit/test_build_ingest_deps_wiring.py` — fifth factory track + collect source pin
- `tests/unit/test_ingestion_clients.py` — `__all__`, factory client pin, blank-key pin

## Decisions Made

- Classifier call shape is the COVERAGE.md INTEGRATE set (`json_object`, `thinking.disabled`, `stream=False`, `max_tokens=128`). Pass-1 `_stream_content` is untouched.
- Unwrap happens in the adapter (`payload["topic_kind"]` only). Pipeline `normalize_topic_kind` remains the D-08 code layer.
- Transport `RuntimeError` is not mapped to `ArticleError`; empty content returns `None`.
- Factory clones the article factory's DeepSeek client (`trust_env=False`) and does not call `build_httpx_client`.

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** No scope creep.

## Issues Encountered

None.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Live classifier adapter is behind the Plan 01 port; ingest and collect composition construct it.
- Plan 03 owns the `## Гайд` strip; Plan 04 owns migration 014 / `p_topic_kind`.
- KIND-01 / KIND-02 remain shared with later plans — do not mark Complete until `requirements.ready-ids` says so.

## Self-Check: PASSED

- FOUND: `data-collection/src/data_collection/adapters/deepseek_classifier.py`
- FOUND: `tests/unit/test_deepseek_classifier.py`
- FOUND: `ingestion-service/src/ingestion_service/composition/clients.py`
- FOUND: `68cea60` `bf5347e` `296b6ad` `41a6684`

---
*Phase: 30-classifier-practical-conceptual*
*Completed: 2026-10-29*
