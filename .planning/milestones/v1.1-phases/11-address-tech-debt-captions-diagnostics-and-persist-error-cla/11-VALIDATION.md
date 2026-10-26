---
phase: "11"
slug: "address-tech-debt-captions-diagnostics-and-persist-error-cla"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-02"
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`) |
| **Quick run command** | `uv run pytest tests/unit/test_captions_error_mapping.py tests/unit/test_youtube_transcript_adapter.py tests/unit/test_cli_ingest_contract.py tests/unit/test_supabase_draft_persister_contract.py tests/unit/test_persist_idempotency_overflow.py tests/unit/test_phase11_migration_009.py -q` |
| **Full suite command** | `uv run pytest tests/unit -q` |
| **Estimated runtime** | ~30–90 seconds |

---

## Sampling Rate

- **After every task commit:** Run the quick run command (or the touched-file subset)
- **After every plan wave:** Run `uv run pytest tests/unit -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | CAP-02 / D-04 / D-05 | T-11-01 | CookieInvalid/unknown → JSON stderr; no Traceback | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -x` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | CAP-02 / D-01…D-03 | T-11-01 | message free of proxy/SDK secrets; allowlists frozen | unit | `uv run pytest tests/unit/test_captions_error_mapping.py tests/unit/test_youtube_transcript_adapter.py -x` | ✅ | ⬜ pending |
| 11-02-01 | 02 | 1 | PERS-02 / D-06 | T-11-02 | `23514` → batch_creation_failed | unit | `uv run pytest tests/unit/test_supabase_draft_persister_contract.py -x` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | PERS-02 / D-06 / D-07 | T-11-02 / T-11-04 | int HTTP → rpc_error; PERSIST_REASONS frozen | unit | `uv run pytest tests/unit/test_supabase_draft_persister_contract.py -x` | ❌ W0 | ⬜ pending |
| 11-03-01 | 03 | 1 | CLI-02 / D-09 | T-11-03 | One-way decision gate before authoring 009 | checkpoint | `git ls-files -- supabase-integration/migrations/008_phase10_persist_already_saved.sql` | ✅ | ⬜ pending |
| 11-03-02 | 03 | 1 | CLI-02 / D-08–D-09 | T-11-03 / T-11-05 | Sent-batch conflict → already_saved true (SQL) | unit | `uv run pytest tests/unit/test_phase11_migration_009.py -x` | ❌ W0 | ⬜ pending |
| 11-03-03 | 03 | 1 | CLI-02 / D-08 | T-11-03 | Fake overflow path returns already_saved | unit | `uv run pytest tests/unit/test_persist_idempotency_overflow.py -x` | ✅ flip | ⬜ pending |
| 11-04-01 | 04 | 2 | CLI-02 / CLI-04 / D-08 | — | Checkmarks + already_saved on sent-batch re-run | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -x` | ❌ W0 | ⬜ pending |
| 11-04-02 | 04 | 2 | CLI-02 / D-09 | T-11-07 | Migration 009 applied on shared VM | human | Studio/psql apply + `git ls-files -- .../009_...sql` | ❌ apply | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_cli_ingest_contract.py` — captions failure → stderr JSON `unknown_captions_error`, no Traceback (11-01-01)
- [ ] `tests/unit/test_supabase_draft_persister_contract.py` — `code="23514"` → batch error; `code=503` (int) → rpc_error; keep `check_violation` (11-02)
- [ ] `tests/unit/test_phase11_migration_009.py` — offline SQL: sent-batch fallback; `'already_saved', true`; grants; no edit of 008 (11-03-02)
- [ ] Invert `tests/unit/test_persist_idempotency_overflow.py` sent-batch raise test + fake (11-03-03)
- [ ] `tests/unit/test_cli_ingest_contract.py` — sent-batch re-run checkmarks + already_saved (11-04-01)
- [ ] Framework install: none — pytest already available

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Migration 009 applied on shared VM | CLI-02 / D-09 | Shared Studio/psql apply; no CI migrate | Human applies `009` via Studio/`psql` against knowledge-db.ru; confirm RPC returns already_saved on sent-batch-only re-run (task 11-04-02) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter after execution+validate

**Approval:** pending
