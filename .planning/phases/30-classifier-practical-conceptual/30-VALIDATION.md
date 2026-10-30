---
phase: 30
slug: classifier-practical-conceptual
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: false
wave_0_complete: true
created: 2026-10-28
validated: 2026-10-30
---

# Phase 30 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `30-RESEARCH.md` § Validation Architecture.
> Nyquist audit 2026-10-30: PARTIAL — KIND-01/03 green; KIND-02 JSON-string unwrap escalated.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (`>=8.3.0`), Python `>=3.12`, `testpaths = ["tests/unit"]` |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` — no `pytest.ini` |
| **Quick run command** | `uv run pytest tests/unit/test_topic_kind.py tests/unit/test_article_draft_body_guide.py tests/unit/test_ingest_pipeline.py tests/unit/test_deepseek_classifier.py tests/unit/test_phase30_migration_014.py -x` |
| **Full suite command** | `uv run pytest tests/unit -q` |
| **Estimated runtime** | ~few seconds quick / existing unit-suite budget full |

---

## Sampling Rate

- **After every task commit:** Run the quick command for that requirement’s new file (see Per-Task Verification Map)
- **After every plan wave:** Run `uv run pytest tests/unit -q`
- **Before `/gsd-verify-work`:** Full unit suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 30-01-01 | 01 | 1 | KIND-02 | T-30-02 | `normalize_topic_kind` maps missing/empty/unknown/malformed → `conceptual` | unit | `uv run pytest tests/unit/test_topic_kind.py -x` | ✅ | ✅ green |
| 30-01-01 | 01 | 1 | KIND-01 | T-30-03 | Draft always has `topic_kind` in `{practical, conceptual}` after persist | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -k topic_kind -x` | ✅ | ✅ green |
| 30-01-01 | 01 | 1 | KIND-01 | — | `assemble_material_draft` copies `topic_kind` | unit | `uv run pytest tests/unit/test_assemble_material_draft.py -k topic_kind -x` | ✅ | ✅ green |
| 30-01-02 | 01 | 1 | KIND-02 | — | Required `classifier=` at pipeline/CollectDeps/CLI; `__all__` ten names; Stage seven values | unit | `uv run pytest tests/unit/test_collect_batch.py tests/unit/test_cli_ingest_contract.py tests/unit/test_data_collection_public_api.py -q` | ✅ | ✅ green |
| 30-02-01 | 02 | 2 | KIND-01 | T-30-01 | Cheap DeepSeek `json_object` + `stream=False` + `max_tokens=128`; D-01…D-08 prompt; fenced title/dek/transcript | unit | `uv run pytest tests/unit/test_deepseek_classifier.py -x` | ✅ | ✅ green |
| 30-02-01 | 02 | 2 | KIND-02 | T-30-02 | JSON array `["practical"]` is a miss → `conceptual`, no `ArticleError` | unit | `uv run pytest tests/unit/test_deepseek_classifier.py::test_json_array_content_maps_to_conceptual_without_article_error -x` | ✅ | ✅ green |
| 30-02-01 | 02 | 2 | KIND-02 | T-30-02 | JSON string `"practical"` must not launder practical (only `payload["topic_kind"]` unwraps) | unit | `uv run pytest tests/unit/test_deepseek_classifier.py::test_json_string_content_does_not_launder_practical -x` | ✅ | ⚠️ xfail — escalated (see Manual-Only) |
| 30-02-01 | 02 | 2 | KIND-02 | T-30-03 | Classifier transport / empty JSON does not raise `IngestError`; persist still `conceptual` | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -k classify -x` | ✅ | ✅ green |
| 30-02-01 | 02 | 2 | KIND-02 | T-30-05 | No Tavily/enricher/cheat-sheet call sites this phase | unit | `uv run pytest tests/unit/test_ingest_pipeline.py::test_ingest_pipeline_does_not_wire_pass2_extras -x` | ✅ | ✅ green |
| 30-02-02 | 02 | 2 | KIND-01 | — | `build_ingest_deps` / `build_collect_deps` wire `build_deepseek_topic_kind_classifier` | unit | `uv run pytest tests/unit/test_build_ingest_deps_wiring.py tests/unit/test_ingestion_clients.py -q` | ✅ | ✅ green |
| 30-03-01 | 03 | 3 | KIND-03 | T-30-01 | `## Гайд` stripped; placeholder stripped; in-prose «гайд» kept; D-12 titles kept | unit | `uv run pytest tests/unit/test_article_draft_body_guide.py -x` | ✅ | ✅ green |
| 30-03-01 | 03 | 3 | KIND-03 | T-30-01 / D-09 | Furniture-only `## Гайд` strips, then assemble + Fake persist succeed | unit | `uv run pytest tests/unit/test_article_draft_body_guide.py::test_furniture_only_guide_body_assembles_without_validation_error tests/unit/test_ingest_pipeline.py::test_furniture_only_guide_body_still_persists -x` | ✅ | ✅ green |
| 30-03-02 | 03 | 3 | KIND-03 | — | Lecture/podcast assembled messages omit `Гайд`; `SHARED_PROMPT_HEADINGS` unchanged | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py::test_assembled_user_message_omits_guide_heading tests/unit/test_deepseek_article_adapter.py::test_create_kwargs_include_json_object_and_disabled_thinking -x` | ✅ | ✅ green |
| 30-03-02 | 03 | 3 | (regress) | — | `EXPECTED_SUCCESS_LINES` unchanged; audience strip still works | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_article_draft_body_audience.py -q` | ✅ | ✅ green |
| 30-04-02 | 04 | 2 | KIND-01 | T-30-04, T-30-06 | Migration 014 ADD COLUMN + DROP 12-arg + CREATE 13-arg; `_rpc_params` sends `p_topic_kind` | unit | `uv run pytest tests/unit/test_phase30_migration_014.py tests/unit/test_supabase_draft_persister_contract.py -x` | ✅ | ✅ green |
| 30-04-03 | 04 | 2 | KIND-01 | T-30-06 | Live apply of 014 on shared knowledge-db VM | manual | runbook §4l verify SQL | ✅ Applied 2026-10-29 | ✅ done (manual) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky / xfail*

---

## Wave 0 Requirements

- [x] `tests/unit/test_topic_kind.py` — `normalize_topic_kind` matrix (KIND-02)
- [x] `tests/unit/test_article_draft_body_guide.py` — clone `test_article_draft_body_audience.py` (KIND-03)
- [x] `tests/unit/test_phase30_migration_014.py` — clone `test_phase11_migration_009.py` (KIND-01 persist)
- [x] `FakeTopicKindClassifier` in `data-collection/src/data_collection/tests_support/fakes.py`
- [x] Pipeline / assemble / persister / `build_ingest_deps` / `NEGATIVE_ROOT_NAMES` extensions
- [x] Framework install: none — pytest already configured

Existing infrastructure covers the runner and the new behaviors (Wave 0 complete after execute-phase).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Apply migration `014` on the operator VM so live `persist_draft_and_enqueue` gains `p_topic_kind` | KIND-01 | Live Postgres is on the operator VM | Done 2026-10-29: Studio SQL Editor, `n=1` `pronargs=13`. Re-verify via runbook §4l if the VM is rebuilt. |
| JSON string `"practical"` from the classifier must not persist as `practical` | KIND-02 | Implementation bug: `DeepSeekTopicKindClassifier.classify` returns non-dict JSON as-is (`deepseek_classifier.py:118-119`). Nyquist pin `test_json_string_content_does_not_launder_practical` is `xfail(strict=True)`. Automated suite cannot go green on this pin until impl returns `None` for non-dict payloads. | After the adapter fix: remove the `xfail`, run `uv run pytest tests/unit/test_deepseek_classifier.py::test_json_string_content_does_not_launder_practical -x`, then `/gsd-validate-phase 30` again. |

Default suite: Fake + SQL contract tests cover KIND-01…03 except the JSON-string unwrap. No live DeepSeek proof in this phase.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter — **blocked on KIND-02 JSON-string launder**

**Approval:** validated 2026-10-30 (partial)

---

## Validation Audit 2026-10-30

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 1 (KIND-03 furniture persist) + JSON-array half of KIND-02 |
| Escalated | 1 (KIND-02 JSON string `"practical"` launders via non-dict `return payload`) |

Auditor: gsd-nyquist-auditor. Implementation files were not edited.

| Gap | Task | Requirement | Result |
|-----|------|-------------|--------|
| 1 furniture persist | 30-03-01 | KIND-03 / D-09 | **FILLED.** Empty and filled `## Гайд`-only bodies assemble and persist; stored body is non-blank and has no `Гайд`. |
| 2 JSON array | 30-02-01 | KIND-02 | **FILLED.** `json.dumps(["practical"])` → no `ArticleError`, `normalize_topic_kind(raw) == "conceptual"`. |
| 2 JSON string | 30-02-01 | KIND-02 | **ESCALATED (BLOCKER).** `json.dumps("practical")` → `normalize_topic_kind(raw) == "practical"`. Adapter `return payload` on non-dict JSON. Pin kept as `xfail(strict=True)`. |

`nyquist_compliant` stays `false` until the JSON-string BLOCKER is fixed in `deepseek_classifier.py` (return `None` for non-dict payloads).
