---
phase: "12"
slug: "admin-shortlist-empty-batch-contract"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-02"
validated: "2026-10-05"
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python units) + Playwright (admin E2E) |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]`; Playwright via root `package.json` |
| **Quick run command** | `uv run pytest tests/unit/test_http_admin.py::test_admin_shortlist_no_batches_returns_null_batch_id tests/unit/test_http_admin.py::test_admin_shortlist_empty_unsent_batch_returns_batch_id -x` |
| **Full suite command** | `uv run pytest tests/unit/test_http_admin.py -q` and `npm run test:web -- tests/admin.spec.js` (empty / empty-unsent cases) |
| **Estimated runtime** | ~2–3 seconds (unit pair + module); ~2 min for the full `admin.spec.js` Playwright file |

---

## Sampling Rate

- **After every task commit:** Run quick FIX-01 pytest pair above
- **After every plan wave:** Run `uv run pytest tests/unit/test_http_admin.py -q` + Playwright empty/empty-unsent cases
- **Before `/gsd-verify-work`:** FIX-01 pair green; lock doc present; no new suite failures introduced (D-02)
- **Max feedback latency:** <5 seconds (unit); Playwright separately

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | FIX-01 | T-12-01 / T-12-03 | Empty-unsent HTTP 200; required keys; no schema 500 | unit | `uv run pytest tests/unit/test_http_admin.py::test_admin_shortlist_empty_unsent_batch_returns_batch_id -x` | ✅ | ✅ green |
| 12-01-02 | 01 | 1 | FIX-01 | T-12-01 | No-batch rename + required-key asserts; both proofs green | unit | `uv run pytest tests/unit/test_http_admin.py::test_admin_shortlist_no_batches_returns_null_batch_id tests/unit/test_http_admin.py::test_admin_shortlist_empty_unsent_batch_returns_batch_id -x` | ✅ | ✅ green |
| 12-02-01 | 02 | 2 | FIX-01 | T-12-04 | Lock doc both shapes + D-08/D-09 + both D-05 names | docs | `rg -n "test_admin_shortlist_no_batches_returns_null_batch_id\|test_admin_shortlist_empty_unsent_batch_returns_batch_id\|extra=.forbid\|week_start.isoformat" .planning/milestones/v1.2-phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` | ✅ | ✅ green |
| 12-02-02 | 02 | 2 | FIX-01 | T-12-05 | REQUIREMENTS/ROADMAP/PROJECT cite both D-05 names | docs | `rg -n "test_admin_shortlist_no_batches_returns_null_batch_id\|test_admin_shortlist_empty_unsent_batch_returns_batch_id" .planning/milestones/v1.2-REQUIREMENTS.md .planning/milestones/v1.2-ROADMAP.md .planning/PROJECT.md` | ✅ | ✅ green |
| 12-03-01 | 03 | 2 | FIX-01 | T-12-06 / T-12-07 | emptyUnsentDto + EMPTY_UNSENT branch + reset clear | docs/static | `rg -n "emptyUnsentDto\|__DIGEST_ADMIN_EMPTY_UNSENT__" web/src/services/adminApi.js` | ✅ | ✅ green |
| 12-03-02 | 03 | 2 | FIX-01 | T-12-06 / T-12-07 | Playwright empty-unsent mirrors D-80; digest_rest absent | e2e | `npm run test:web -- tests/admin.spec.js` (empty-unsent case: `tests/admin.spec.js:148`) | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Rename `test_admin_shortlist_empty_batch_returns_200_empty_items` → `test_admin_shortlist_no_batches_returns_null_batch_id` (required-key asserts)
- [x] Add `test_admin_shortlist_empty_unsent_batch_returns_batch_id` in `tests/unit/test_http_admin.py`
- [x] Add `emptyUnsentDto` + `__DIGEST_ADMIN_EMPTY_UNSENT__` + reset clear in `web/src/services/adminApi.js`
- [x] Add Playwright empty-unsent case in `tests/admin.spec.js`
- [x] Create `12-FIX-01-LOCK.md` with both shapes + assert rules
- [x] Update `.planning/REQUIREMENTS.md` FIX-01 and `.planning/ROADMAP.md` Phase 12 success criteria proof names

*Existing infrastructure covers runners/fixtures — gaps are phase-specific tests/docs only.*

---

## Manual-Only Verifications

All phase behaviors have automated verification (unit + Playwright + lock-doc presence).

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s for unit pair
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-05

---

## Validation Audit 2026-10-05

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Audit method:** State A — re-ran every Per-Task Map automated command against the current working tree.

- FIX-01 HTTP pair: `uv run pytest ...no_batches... ...empty_unsent... -q` → **2 passed** (1.06s).
- Full module: `uv run pytest tests/unit/test_http_admin.py -q` → **31 passed** (2.07s) — no new suite failures (D-02 scope-bound green).
- Playwright: `npm run test:web -- tests/admin.spec.js` → **50 passed** (1.9m), including `tests/admin.spec.js:148` empty-unsent (D-80 empty UI, zero `admin-digest-rest`).
- Doc greps: `12-FIX-01-LOCK.md`, `.planning/milestones/v1.2-REQUIREMENTS.md`, `.planning/milestones/v1.2-ROADMAP.md`, `.planning/PROJECT.md`, `web/src/services/adminApi.js` all contain the required proof strings / symbols.

**Path corrections applied this audit:** the seeded VALIDATION/PLAN verify commands pointed at pre-milestone paths that no longer resolve. Corrected to the current layout:
- `.planning/phases/12-…/12-FIX-01-LOCK.md` → `.planning/milestones/v1.2-phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md`
- `.planning/REQUIREMENTS.md` → `.planning/milestones/v1.2-REQUIREMENTS.md`
- `.planning/ROADMAP.md` → `.planning/milestones/v1.2-ROADMAP.md`
- `.planning/PROJECT.md` unchanged (root path still valid)

No MISSING or PARTIAL rows: every FIX-01 requirement has a green automated proof. `nyquist_compliant: true`.
