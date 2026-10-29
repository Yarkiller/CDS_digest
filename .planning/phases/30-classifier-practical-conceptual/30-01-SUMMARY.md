---
phase: 30-classifier-practical-conceptual
plan: 01
subsystem: ingestion-classifier
tags: [topic-kind, practical, conceptual, ports-adapters, tdd, fake-classifier]

requires:
  - phase: 29-pass-1-richer-templates
    provides: pass-1 ArticleDraft spine, ingest pipeline after article.process, FakeArticleGenerator
provides:
  - TopicKindClassifier Protocol with classify(transcript, article) -> object
  - normalize_topic_kind allowlist (practical | conceptual; else conceptual)
  - topic_kind on ArticleDraft and MaterialDraft with before-validators
  - FakeTopicKindClassifier plus required classifier= through pipeline, CollectDeps, and CLI tests
affects: [30-02-deepseek-adapter, 30-03-guide-strip, 30-04-migration-014, 31-tavily-quota]

actuals:
  tokens: 10815
  tasks: 2
  commits: 5

tech-stack:
  added: []
  patterns:
    - D-08 code layer: allowlist-only normalize_topic_kind; unsure is not an enum member
    - fail-soft classify: except Exception -> conceptual, persist, never stage=llm
    - required classifier= kwarg with Fake at every unit call site (Pitfall 6)

key-files:
  created:
    - data-collection/src/data_collection/ports/topic_kind.py
    - data-collection/src/data_collection/dto/topic_kind.py
    - tests/unit/test_topic_kind.py
  modified:
    - data-collection/src/data_collection/dto/article_draft.py
    - data-collection/src/data_collection/dto/material_draft.py
    - data-collection/src/data_collection/assemble.py
    - data-collection/src/data_collection/tests_support/fakes.py
    - ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
    - ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py
    - ingestion-service/src/ingestion_service/cli.py
    - tests/unit/test_assemble_material_draft.py
    - tests/unit/test_ingest_pipeline.py
    - tests/unit/test_collect_batch.py
    - tests/unit/test_collect_cli_contract.py
    - tests/unit/test_cli_ingest_contract.py
    - tests/unit/test_cli_debug_diagnostics.py
    - tests/unit/test_data_collection_public_api.py
    - tests/unit/test_article_draft_internal.py

key-decisions:
  - "normalize_topic_kind allowlists only practical|conceptual after strip+casefold; dicts/lists/unsure/None are conceptual (KIND-02, D-08 code layer)"
  - "Pipeline always overwrites article_draft.topic_kind from classifier raw, even when pass-1 leaked practical (Pitfall 4)"
  - "classifier= is required keyword-only with no None default; unit call sites pass FakeTopicKindClassifier"
  - "Live build_ingest_deps / build_collect_deps stay unwired this plan — Plan 02 owns the DeepSeek adapter factory"

patterns-established:
  - "Pattern: TopicKindClassifier is module-private; import from data_collection.ports.topic_kind, never package root or ports.__all__"
  - "Pattern: field_validator(mode=before) calls normalize_topic_kind so Literal never sees garbage (no ValidationError → stage=llm)"
  - "Pattern: classify swallow is except Exception: raw=None; never IngestError, never diagnostics.stage_failed, never a fourth on_stage name"

requirements-completed: [KIND-01, KIND-02]

coverage:
  - id: D1
    description: "Happy-path FakeTopicKindClassifier returning practical stamps persist.calls[0].topic_kind == practical end to end (KIND-01)"
    requirement: KIND-01
    verification:
      - kind: unit
        ref: tests/unit/test_ingest_pipeline.py#test_fake_practical_persists_practical
        status: pass
      - kind: unit
        ref: tests/unit/test_assemble_material_draft.py#test_assemble_material_draft_copies_article_topic_kind
        status: pass
    human_judgment: false
  - id: D2
    description: "Invalid/missing/raising classifier output is stored as conceptual and ingest still persists (KIND-02, D-08 code layer, T-30-02, T-30-03)"
    requirement: KIND-02
    verification:
      - kind: unit
        ref: tests/unit/test_ingest_pipeline.py#test_classifier_non_allowlist_persists_conceptual
        status: pass
      - kind: unit
        ref: tests/unit/test_ingest_pipeline.py#test_classifier_runtime_error_persists_conceptual_without_ingest_error
        status: pass
      - kind: unit
        ref: tests/unit/test_topic_kind.py#test_article_draft_garbage_topic_kind_does_not_raise_validation_error
        status: pass
    human_judgment: false
  - id: D3
    description: "Pass-1 leaked practical is overwritten by the classifier stamp (Pitfall 4); Fake conceptual persists conceptual"
    requirement: KIND-01
    verification:
      - kind: unit
        ref: tests/unit/test_ingest_pipeline.py#test_classifier_stamp_overwrites_leaked_pass1_topic_kind
        status: pass
    human_judgment: false
  - id: D4
    description: "Required classifier= on run_ingest_pipeline, CollectDeps, and every unit call site; CLI stdout stays three checkmarks; public __all__ stays ten names; Stage stays seven values"
    requirement: KIND-02
    verification:
      - kind: unit
        ref: tests/unit/test_ingest_pipeline.py#test_run_ingest_pipeline_requires_classifier
        status: pass
      - kind: unit
        ref: tests/unit/test_collect_batch.py#test_collect_deps_requires_classifier
        status: pass
      - kind: unit
        ref: tests/unit/test_cli_ingest_contract.py#test_cli_happy_path_stdout_contract
        status: pass
      - kind: unit
        ref: tests/unit/test_data_collection_public_api.py#test_public_all_is_exactly_ten_ingestion_names
        status: pass
      - kind: unit
        ref: tests/unit/test_data_collection_public_api.py#test_stage_set_is_unchanged
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-10-29
status: complete
---

# Phase 30 Plan 01: Classifier Fake spine Summary

**Closed `topic_kind` (`practical` | `conceptual`) stamped through Fake classifier → assemble → persist, with invalid output stored as conceptual and ingest continuing**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-29T02:59:00Z
- **Completed:** 2026-10-29T03:10:18Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments

- After `ArticleGenerator.process`, the pipeline classifies, stamps a closed `topic_kind`, copies it through `assemble_material_draft`, and `FakeDraftPersister` records it (KIND-01).
- Invalid classifier output (`unsure` / `None` / dict / `RuntimeError`) is stored as `conceptual` and persist still runs; no `IngestError`, no `stage=llm` (KIND-02, D-08 code layer, T-30-02, T-30-03).
- Required `classifier=` at the pipeline, `CollectDeps`, and every unit call site; public `__all__` stays ten names; Stage stays seven values; CLI stdout stays three checkmarks.

## RED assertions (Task 1 tracer)

Command: `uv run pytest tests/unit/test_topic_kind.py tests/unit/test_assemble_material_draft.py tests/unit/test_ingest_pipeline.py -x`

- `test_normalize_topic_kind_keeps_practical_and_conceptual` — `ModuleNotFoundError: No module named 'data_collection.dto.topic_kind'`
- `test_assemble_material_draft_copies_article_topic_kind` — `AttributeError: 'MaterialDraft' object has no attribute 'topic_kind'`
- existing and new ingest cases — `TypeError: run_ingest_pipeline() got an unexpected keyword argument 'classifier'`
- `test_run_ingest_pipeline_requires_classifier` — `KeyError: 'classifier'`

## RED assertions (Task 2)

- `test_collect_deps_requires_classifier` — `'classifier' not in CollectDeps fields`
- CollectDeps constructors — `TypeError: CollectDeps.__init__() got an unexpected keyword argument 'classifier'`
- CLI happy path — `TypeError: run_ingest_pipeline() missing 1 required keyword-only argument: 'classifier'`

## GREEN command output

- Tracer: `46 passed` (`uv run pytest tests/unit/test_topic_kind.py tests/unit/test_assemble_material_draft.py tests/unit/test_ingest_pipeline.py -x`)
- Plan gate: `135 passed`
- Wave gate: `1238 passed, 1 warning` (`uv run pytest tests/unit -q`)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: failing tests for topic_kind ingest spine** - `0343943` (test)
2. **Task 1 GREEN: implement topic_kind ingest spine** - `c2291b0` (feat)
3. **Task 2 RED: failing tests for required classifier call sites** - `4f4efdd` (test)
4. **Task 2 GREEN: require classifier at collect and CLI call sites** - `cdd9e4a` (feat)
5. **Rule 1: include topic_kind in ArticleDraft field pin** - `279d82a` (fix)

**Plan metadata:** (docs commit after this file)

_Note: TDD tasks have multiple commits (test → feat)_

## Files Created/Modified

- `data-collection/src/data_collection/ports/topic_kind.py` — `TopicKindClassifier` Protocol
- `data-collection/src/data_collection/dto/topic_kind.py` — `TopicKind`, `VALID_TOPIC_KINDS`, `normalize_topic_kind`
- `data-collection/src/data_collection/dto/article_draft.py` — `topic_kind` field + before-validator
- `data-collection/src/data_collection/dto/material_draft.py` — `topic_kind` field + before-validator
- `data-collection/src/data_collection/assemble.py` — copies `article.topic_kind`
- `data-collection/src/data_collection/tests_support/fakes.py` — `FakeTopicKindClassifier`
- `ingestion-service/.../ingest_pipeline.py` — required `classifier=`; fail-soft stamp
- `ingestion-service/.../collect_batch.py` — `CollectDeps.classifier`; forwards to pipeline
- `ingestion-service/src/ingestion_service/cli.py` — forwards `deps.classifier`
- `tests/unit/test_topic_kind.py` — allowlist + DTO garbage matrix
- `tests/unit/test_ingest_pipeline.py` — KIND-01/02 spine, Pitfall 4, extras unwired
- `tests/unit/test_data_collection_public_api.py` — five negative root names

## Decisions Made

- D-08 prompt default (unsure → practical) is **not** in Python; `normalize_topic_kind` only keeps the two tokens.
- Dict payloads are malformed here (no key unwrap); Plan 02 adapter may unwrap `topic_kind` then still normalize.
- Live composition factories left untouched; Plan 02 adds `build_deepseek_topic_kind_classifier`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ArticleDraft exact field-set pin**
- **Found during:** Task 2 wave-gate (`uv run pytest tests/unit -q`)
- **Issue:** `test_article_draft_constructs_article_fields_only` asserted `model_fields == {title, dek, body_markdown, roles}`; adding `topic_kind` reddened it.
- **Fix:** include `topic_kind` in the set and pin default `conceptual`.
- **Files modified:** `tests/unit/test_article_draft_internal.py`
- **Verification:** full unit suite 1238 passed
- **Committed in:** `279d82a`

---

**Total deviations:** 1 auto-fixed (1 Rule 1)
**Impact on plan:** Necessary pin update; no scope creep. Live `build_collect_deps` / `build_ingest_deps` still omit the classifier by plan (Plan 02).

## Issues Encountered

None beyond the field-set pin above.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Fake spine is proven; Plan 02 can add the cheap DeepSeek adapter and wire `build_ingest_deps` / `build_collect_deps`.
- Plan 03 owns the `## Гайд` strip; Plan 04 owns migration 014 / `p_topic_kind`.
- KIND-01 / KIND-02 remain shared with later plans — do not mark Complete until `requirements.ready-ids` says so.

## Self-Check: PASSED

- FOUND: `data-collection/src/data_collection/ports/topic_kind.py`
- FOUND: `data-collection/src/data_collection/dto/topic_kind.py`
- FOUND: `tests/unit/test_topic_kind.py`
- FOUND: `0343943` `c2291b0` `4f4efdd` `cdd9e4a` `279d82a`

---
*Phase: 30-classifier-practical-conceptual*
*Completed: 2026-10-29*
