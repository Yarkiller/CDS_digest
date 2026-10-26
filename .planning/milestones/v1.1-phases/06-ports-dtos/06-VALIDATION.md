---
phase: 6
slug: ports-dtos
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-26
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (workspace `tests/unit`) |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/unit/test_transcript_dto.py tests/unit/test_assemble_material_draft.py tests/unit/test_material_draft_type_boundary.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~1 second (68 passed in 0.53s on 2026-10-02) |

---

## Sampling Rate

- **After every task commit:** Run targeted new unit file(s) with `-x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | DTO-01 / DTO-02 / D-07 / SC-3 | T-06-01, T-06-02, T-06-03, T-06-04 | Tracer: DTOs + FakeArticleGenerator + assembler + Transcript≠MaterialDraft boundary | unit (+ async via asyncio.run) | `uv run pytest tests/unit/test_transcript_dto.py tests/unit/test_video_metadata_dto.py tests/unit/test_material_draft_dto.py tests/unit/test_template_kind.py tests/unit/test_article_draft_internal.py tests/unit/test_article_generator_fake.py tests/unit/test_assemble_material_draft.py tests/unit/test_material_draft_type_boundary.py -x` | ✅ | ✅ green |
| 06-01-02 | 01 | 1 | DTO-01 | T-06-01 | MaterialDraft missing-required + TemplateKind closed set | unit | `uv run pytest tests/unit/test_material_draft_dto.py tests/unit/test_template_kind.py -x` | ✅ | ✅ green |
| 06-02-01 | 02 | 2 | DTO-02 | T-06-03 | FakeTranscriptProvider scripted + `.calls` order | unit async | `uv run pytest tests/unit/test_transcript_provider_fake.py -x` | ✅ | ✅ green |
| 06-02-02 | 02 | 2 | DTO-01 | T-06-01, T-06-05 | DTO validation edges (blank/language/nullable published_at) | unit | `uv run pytest tests/unit/test_transcript_dto.py tests/unit/test_video_metadata_dto.py tests/unit/test_material_draft_dto.py tests/unit/test_article_draft_internal.py -x` | ✅ | ✅ green |
| 06-03-01 | 03 | 3 | D-01…D-03 | — | Checkpoint approved (`proceed`, 2026-09-26); outcome locked by 06-03-02 | checkpoint | `echo checkpoint-decision-d01-d03` | N/A | ✅ green |
| 06-03-02 | 03 | 3 | D-01…D-04 | T-06-03, T-06-07 | Old DTOs gone; public `__all__` whitelist; fakes/ArticleDraft not exported | unit / import | `uv run pytest tests/unit/test_data_collection_public_api.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] New unit test stubs listed in Per-Task Verification Map (present; 68 passed)
- [x] Delete old DTO modules/tests only after RED tests for the new surface exist (TDD)
- [x] Confirm async fake tests via `asyncio.run` without adding a pytest-asyncio package if avoidable
- [x] Assert no diffs under `supabase-integration/migrations/` or `query_embedder.py` for this phase

*Existing pytest + uv workspace infrastructure covers the runner. Wave 0 files are on disk and green.*

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-02

---

## Validation Audit 2026-10-02

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

State A audit. All six tasks already had tests (or a completed checkpoint whose outcome is locked by `test_data_collection_public_api.py`). Re-ran the phase 6 unit files: 68 passed in 0.53s. Brownfield `dto/youtube.py`, `dto/foundry.py`, `dto/text_import.py` and their three unit tests are absent. No new test files. Public `__all__` has since grown to seven names (`VideoMetadataProvider`); the whitelist test still covers the Phase 6 exports and the negative root imports.
