---
phase: 30
slug: classifier-practical-conceptual
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-28
---

# Phase 30 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `30-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (`>=8.3.0`), Python `>=3.12`, `testpaths = ["tests/unit"]` |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` — no `pytest.ini` |
| **Quick run command** | `uv run pytest tests/unit/test_topic_kind.py tests/unit/test_article_draft_body_guide.py tests/unit/test_ingest_pipeline.py -x` |
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
| TBD (normalize kind) | 01 | 1 | KIND-02 | T-30-02 (malformed JSON → practical) | `normalize_topic_kind` maps missing/empty/unknown/malformed → `conceptual` | unit | `uv run pytest tests/unit/test_topic_kind.py -x` | ❌ Wave 0 | ⬜ pending |
| TBD (pipeline persist) | 01 | 1 | KIND-01 | T-30-03 (classifier fail-closes ingest) | Draft always has `topic_kind` in `{practical, conceptual}` after persist | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -k topic_kind -x` | ❌ Wave 0 | ⬜ pending |
| TBD (assemble copy) | 01 | 1 | KIND-01 | — | `assemble_material_draft` copies `topic_kind` | unit | `uv run pytest tests/unit/test_assemble_material_draft.py -k topic_kind -x` | ❌ Wave 0 (file exists, no topic_kind cases) | ⬜ pending |
| TBD (RPC param) | 01 | 1 | KIND-01 | T-30-04 (RPC executable by anon) | RPC params include `p_topic_kind`; grants stay service_role-only | unit | `uv run pytest tests/unit/test_supabase_draft_persister_contract.py -k topic_kind -x` | ❌ Wave 0 | ⬜ pending |
| TBD (migration 014) | 01 | 1 | KIND-01 | T-30-06 (CREATE OR REPLACE overload) | Migration 014 `ADD COLUMN` then `DROP FUNCTION` + recreate with `p_topic_kind` | unit | `uv run pytest tests/unit/test_phase30_migration_014.py -x` | ❌ Wave 0 | ⬜ pending |
| TBD (classifier transport) | 02 | 2 | KIND-02 | T-30-03 | Classifier transport / empty JSON does not raise `IngestError`; persist still called with `conceptual` | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -k classify -x` | ❌ Wave 0 | ⬜ pending |
| TBD (no extras) | 02 | 2 | KIND-02 | T-30-05 (kind leaking as badge) | No Tavily/enricher/cheat-sheet call sites on conceptual **or** practical this phase | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -k extras -x` | ❌ Wave 0 | ⬜ pending |
| TBD (public API pin) | 02 | 2 | KIND-02 | — | `__all__` still ten names; `Stage` still seven values | unit | `uv run pytest tests/unit/test_data_collection_public_api.py::test_public_all_is_exactly_ten_ingestion_names tests/unit/test_data_collection_public_api.py::test_stage_set_is_unchanged -x` | ✅ exists — must stay green | ⬜ pending |
| TBD (guide strip) | 03 | 3 | KIND-03 | T-30-01 (prompt injection) | `## Гайд` stripped; placeholder stripped; in-prose «гайд» kept; `Guide` kept | unit | `uv run pytest tests/unit/test_article_draft_body_guide.py -x` | ❌ Wave 0 | ⬜ pending |
| TBD (templates omit Гайд) | 03 | 3 | KIND-03 | — | Templates still omit `Гайд` | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -k SHARED_PROMPT_HEADINGS -x` | ✅ exists — add a negative `Гайд` pin | ⬜ pending |
| TBD (success lines) | 03 | 3 | (regress) | — | `EXPECTED_SUCCESS_LINES` unchanged | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -x` | ✅ exists | ⬜ pending |
| TBD (audience strip) | 03 | 3 | (regress) | — | Audience strip still works | unit | `uv run pytest tests/unit/test_article_draft_body_audience.py -x` | ✅ exists | ⬜ pending |
| TBD (pass-1 call shape) | 03 | 3 | (regress) | T-30-01 | Pass-1 call shape unchanged (`json_object`, `thinking`, `stream=True`) | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py::test_create_kwargs_include_json_object_and_disabled_thinking -x` | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_topic_kind.py` — `normalize_topic_kind` matrix (KIND-02)
- [ ] `tests/unit/test_article_draft_body_guide.py` — clone `test_article_draft_body_audience.py` (KIND-03)
- [ ] `tests/unit/test_phase30_migration_014.py` — clone `test_phase11_migration_009.py` (KIND-01 persist)
- [ ] `FakeTopicKindClassifier` in `data-collection/src/data_collection/tests_support/fakes.py`
- [ ] Pipeline / assemble / persister / `build_ingest_deps` / `NEGATIVE_ROOT_NAMES` extensions
- [ ] Framework install: none — pytest already configured

Existing infrastructure covers the runner, not the new behaviors.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Apply migration `014` on the operator VM so live `save_material_draft` gains `p_topic_kind` | KIND-01 | Live Postgres is on the operator VM; MCP `describe_table` failed without `POSTGRES_URL` this research session | Apply `014` the same way as 012/013; confirm column + 13-arg RPC exist; no leftover 12-arg overload |

Default suite: Fake + SQL contract tests cover KIND-01…03. No live DeepSeek proof in this phase.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
