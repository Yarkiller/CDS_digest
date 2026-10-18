---
phase: "23"
slug: "admin-managed-ingest-sources"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-17"
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (unit/contract) + Playwright `@playwright/test` ^1.62.1 (e2e) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| **Quick run command** | `uv run pytest tests/unit/test_http_ingest_sources.py tests/unit/test_phase23_migration_012.py -x` |
| **Full suite command** | `uv run pytest tests/unit -q` then `npm run test:web` (kill stale `:5174` first — STATE.md) |
| **Estimated runtime** | ~60–180 seconds |

---

## Sampling Rate

- **After every task commit:** Run focused pytest file(s) for the RED under edit
- **After every plan wave:** Run `uv run pytest tests/unit -q` + targeted Playwright admin describes
- **Before `/gsd-verify-work`:** Full unit suite + `npm run test:web` must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 23-01-T1 | 01 | 1 | SRC-01, SRC-03, ADUX-10 | T-23-01…05 | Tracer list/add + port + dirty OR | unit HTTP | `uv run pytest tests/unit/test_http_ingest_sources.py tests/unit/test_composition_container.py -x` | ❌ W0 | ⬜ pending |
| 23-01-T2 | 01 | 1 | SRC-01 | T-23-01 | Playwright add journey; D-22 PRESERVE | e2e | `npm run test:web -- tests/admin.spec.js -g "ingest source\|Источники ингеста\|pipeline config no execution controls"` | ❌ W0 | ⬜ pending |
| 23-02-T2 | 02 | 2 | SRC-01, SRC-02 | T-23-06…09 | 400 `{errors:[…]}` zero writes; PATCH/DELETE | unit HTTP | `uv run pytest tests/unit/test_http_ingest_sources.py -x` | ❌ W0 | ⬜ pending |
| 23-02-T3 | 02 | 2 | SRC-01 | T-23-09 | CORS DELETE advertised | unit | `uv run pytest tests/unit/test_cors.py -q` | ✅ | ⬜ pending |
| 23-03-T2 | 03 | 3 | SRC-01, SRC-03 | T-23-11…15 | Migration 012 + adapter + live wire | unit | `uv run pytest tests/unit/test_phase23_migration_012.py tests/unit/test_supabase_ingest_source_repository_contract.py tests/unit/test_live_container_wiring.py -q` | ❌ W0 | ⬜ pending |
| 23-03-T3 | 03 | 3 | SRC-01 | T-23-14 | [BLOCKING] apply 012 on shared VM | human + unit | `uv run pytest tests/unit/test_phase23_migration_012.py -q` + Studio verify | ❌ W0 | ⬜ pending |
| 23-04-T1 | 04 | 3 | SRC-01, SRC-02 | T-23-16…20 | Full UI section + row lifecycle | e2e | `npm run test:web -- tests/admin.spec.js -g "ingest source\|Источники ингеста\|Где взять id\|zero-enabled\|pipeline config no execution controls"` | ❌ W0 | ⬜ pending |
| 23-04-T2 | 04 | 3 | ADUX-10 | T-23-17 | Source-form dirty arms Phase 19 guard | e2e | `npm run test:web -- tests/admin.spec.js -g "dirty editor blocks\|ingest source\|unsaved\|Дайджест"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*  
*Task IDs filled by planner when PLAN.md waves are authored.*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_phase23_migration_012.py` — covers D-17 / SRC-01 storage
- [ ] `tests/unit/test_http_ingest_sources.py` — covers SRC-02/SRC-01 HTTP + zero writes + admin gate
- [ ] `tests/unit/test_supabase_ingest_source_repository_contract.py` — adapter boundary
- [ ] Amend `tests/unit/test_live_container_wiring.py` (+ composition if exact asserts) — SRC-03 / D-24
- [ ] Amend `tests/admin.spec.js` with sources journey + dirty cases — **without** editing D-22 tripwire body
- [ ] `web/src/services/ingestSourcesApi.js` mock harness (required for Playwright)

*Existing pytest + Playwright infrastructure covers the harness; Wave 0 is new/amended test files, not framework install.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| UI copy: where to obtain UC…/PL… id | SRC-02 | Copy clarity judgment | Open add-source form; confirm help text points to YouTube channel/playlist id location |

*All functional CRUD / validation / dirty-guard behaviors have automated verification planned.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
