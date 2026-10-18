---
phase: "09"
slug: "draft-persist-shortlist-enqueue"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-27"
updated: "2026-09-27T19:29"
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Audited by `/gsd-validate-phase` on 2026-09-27 (initial + re-audit). PERS-01, PERS-02, and the Phase 7 CAP-02 deferred spy are covered by unit tests. Live Studio apply of migration 007 stays manual-only.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (≥8.3) via `uv` |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["tests/unit"]` |
| **Quick run command** | `uv run pytest tests/unit/test_phase9_migration_007.py tests/unit/test_supabase_draft_persister_contract.py tests/unit/test_persist_idempotency_overflow.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task's `<automated>` verify command
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | PERS-01 | T-09-02 | RoleKind closed set; unknown filtered; empty → `["employee"]`; assembler copies roles | unit | `uv run pytest tests/unit/test_article_draft_roles.py tests/unit/test_material_draft_roles.py tests/unit/test_assemble_material_draft.py tests/unit/test_deepseek_article_adapter.py tests/unit/test_fake_article_generator.py -x` | ✅ exists | ✅ green |
| 09-01-02 | 01 | 1 | PERS-01 | T-09-01 | RoleKind / ArticleDraft stay off `data_collection.__all__` | unit | `uv run pytest tests/unit/test_data_collection_public_api.py -x` | ✅ exists | ✅ green |
| 09-02-01 | 02 | 2 | PERS-01 | T-09-08 | PersistPort + FakeDraftPersister: one stored result per video_id | unit | `uv run pytest tests/unit/test_persist_port.py -x` | ✅ exists | ✅ green |
| 09-02-02 | 02 | 2 | PERS-01 | T-09-05 | map_persist_error locked reasons; no secret / raw Postgres / traceback | unit | `uv run pytest tests/unit/test_persist_error_mapping.py -x` | ✅ exists | ✅ green |
| 09-02-03 | 02 | 2 | PERS-02 | T-09-06 | persist_draft writes slug + reading_minutes; no Python video_id pre-check | unit | `uv run pytest tests/unit/test_material_completion.py tests/unit/test_persist_draft_use_case.py -x` | ✅ exists | ✅ green |
| 09-03-01 | 03 | 3 | D-05/D-06/D-09 | — | One-way schema gate (decision checkpoint) | checkpoint | N/A | N/A | ✅ green |
| 09-03-02 | 03 | 3 | PERS-01 / D-09 | T-09-10 | youtube_video_id NOT NULL UNIQUE via ALTER/CONSTRAINT DDL, not a comment | unit | `uv run pytest tests/unit/test_phase9_migration_007.py -x` | ✅ exists | ✅ green |
| 09-03-03 | 03 | 3 | PERS-01 | T-09-09 | persist() forwards provenance params; never forwards status/ready | unit | `uv run pytest tests/unit/test_supabase_draft_persister_contract.py -x` | ✅ exists | ✅ green |
| 09-03-04 | 03 | 3 | PERS-02 | T-09-11 | Migration 007 live on shared VM | manual | Studio SQL + `pg_proc` / column / grant checks | N/A | ✅ green |
| 09-04-01 | 04 | 4 | PERS-01 | T-09-13 | Settings loads optional Supabase fields; SHORTLIST_BATCH_SIZE positive int | unit | `uv run pytest tests/unit/test_ingestion_settings.py -x` | ✅ exists | ✅ green |
| 09-04-02 | 04 | 4 | PERS-01 | T-09-15 | Blank url/key fail closed; factories exported; `.env.example` has no live key | unit | `uv run pytest tests/unit/test_ingestion_clients.py -x` | ✅ exists | ✅ green |
| 09-04-03 | 04 | 4 | PERS-02 | T-09-16 | Idempotent re-run; overflow at capacity; rejected counts; skip sent batch | unit | `uv run pytest tests/unit/test_persist_idempotency_overflow.py -x` | ✅ exists | ✅ green |
| 09-04-04 | 04 | 4 | PERS-01 / CAP-02 | — | Captions or article failure leaves persist.calls empty | unit | `uv run pytest tests/unit/test_captions_failure_zero_persist.py -x` | ✅ exists | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Planned stub names (`test_persist_mapper.py`, `test_supabase_persist_adapter.py`) landed as `tests/unit/test_persist_error_mapping.py` and `tests/unit/test_supabase_draft_persister_contract.py`.

- [x] Role contract tests for ArticleDraft / MaterialDraft / templates / adapter
- [x] PersistPort, FakeDraftPersister, persist_draft, slug/reading-minutes
- [x] Persist error mapping with planted-secret redaction
- [x] Migration 007 SQL contract (comment-stripped D-09 DDL)
- [x] SupabaseDraftPersister mocked-client contract (provenance + no status)
- [x] Settings / composition factories / `.env.example`
- [x] Idempotency, overflow, batch_sent, CAP-02 spy

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Migration 007 applies cleanly to shared VM | PERS-01 / PERS-02 | Shared dev database; executor must not run `supabase db push` | Already applied via Studio SQL (09-03). Re-check: `persist_draft_and_enqueue` exists, four provenance columns present, unique index `materials_youtube_video_id_key`, execute granted to `service_role` |

*Otherwise: All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-09-27 (`nyquist_compliant: true`)

---

## Validation Audit 2026-09-27

| Metric | Count |
|--------|-------|
| Gaps found | 3 |
| Resolved | 3 |
| Escalated | 0 |

Requirement classification (COVERED = test exists, targets the behavior, and ran green):

| Requirement | Status | Evidence |
|-------------|--------|----------|
| PERS-01 | COVERED | Role normalization + public-API negatives; persist mapper redaction; comment-stripped D-09 DDL; adapter forwards `p_source_url` / `p_source_author` / `p_provenance_label` and omits `status`/`ready`; CAP-02 spy |
| PERS-02 | COVERED | persist_draft enrichment + no video_id pre-check; overflow / rejected-capacity / batch_sent; SQL `sent_at IS NULL` contract |
| CAP-02 (deferred from Phase 7) | COVERED | `test_captions_failure_zero_persist.py` — captions/article failure → `persist.calls == []` |

Nyquist auditor: 16 targeted tests passed on `test_phase9_migration_007.py` + `test_supabase_draft_persister_contract.py`. Implementation files unchanged.

## Validation Audit 2026-09-27 (re-audit)

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Re-audit of State A (`09-VALIDATION.md` already validated). PLAN/SUMMARY artifacts, per-task map, and live tests were cross-checked. Phase 9 mapped suite: **160 passed**. No new MISSING/PARTIAL automated gaps. Live Studio apply of migration 007 remains the only manual-only item.

Requirement classification (COVERED = test exists, targets the behavior, and ran green):

| Requirement | Status | Evidence |
|-------------|--------|----------|
| PERS-01 | COVERED | Role normalization + public-API negatives; persist mapper redaction; comment-stripped D-09 DDL; adapter forwards `p_source_url` / `p_source_author` / `p_provenance_label` and omits `status`/`ready`; CAP-02 spy |
| PERS-02 | COVERED | persist_draft enrichment + no video_id pre-check; overflow / rejected-capacity / batch_sent; SQL `sent_at IS NULL` contract |
| CAP-02 (deferred from Phase 7) | COVERED | `test_captions_failure_zero_persist.py` — captions/article failure → `persist.calls == []` |
