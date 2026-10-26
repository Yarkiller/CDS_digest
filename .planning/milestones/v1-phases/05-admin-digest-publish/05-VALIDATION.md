---
phase: 5
slug: admin-digest-publish
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-21
updated: 2026-09-22
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Audited by `/gsd-validate-phase` on 2026-09-22. ADMIN-01…08 and the AUTH-03 admin gate are covered by existing unit and Playwright tests (including gap-closure plans 05-07…09).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (≥8.3) + Playwright (@playwright/test ^1.62.1) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]`; Playwright via `package.json` scripts |
| **Quick run command** | `uv run pytest tests/unit/test_http_admin.py -x` |
| **Full suite command** | `uv run pytest` && `npm run test:web` |
| **Phase gate (05-06)** | `uv run pytest -q` && `npx playwright test tests/admin.spec.js --reporter=line` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run targeted unit file(s) for the behavior (`-x`)
- **After every plan wave:** Run `uv run pytest` + affected Playwright project
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-W0-me | 00 | 0 | D-76 | T-05-spoof | `/me.role` is app_role | unit | `uv run pytest tests/unit/test_http_me.py -x` | ✅ exists | ✅ green |
| 05-01-shortlist | 01 | 1 | ADMIN-01 | — | Admin GET ≤5; empty honesty | unit HTTP | `uv run pytest tests/unit/test_http_admin.py -k shortlist -x` | ✅ exists | ✅ green |
| 05-01-403-api | 01 | 1 | AUTH-03 | T-05-eop | Non-admin → 403 API | unit HTTP | `uv run pytest tests/unit/test_http_admin.py -k forbidden -x` | ✅ exists | ✅ green |
| 05-01-403-ui | 01 / 06 | 1 | AUTH-03 / D-77 | T-05-21 | Employee deep-link → 403 page | e2e | `npx playwright test tests/admin.spec.js -g "403"` | ✅ exists | ✅ green |
| 05-02-decision | 02 | 2 | ADMIN-02 | — | Approve/Reject persists | unit | `uv run pytest tests/unit/test_set_shortlist_decision.py -x` | ✅ exists | ✅ green |
| 05-03-draft-block | 03 / 06 | 2 | ADMIN-03 | T-05-draft | Send blocked on approved draft | unit + e2e | `uv run pytest tests/unit/test_send_digest.py -k draft -x`; admin draft hint | ✅ exists | ✅ green |
| 05-04-preview | 04 / 06 | 2 | ADMIN-04 | — | Preview match; fail ≠ verified | unit + e2e | `uv run pytest tests/unit/test_preview_digest.py -x`; preview fail keeps send locked | ✅ exists | ✅ green |
| 05-05-factors | 02 | 2 | ADMIN-05 | — | Factors ≥2 or недоступно | unit | `uv run pytest tests/unit/test_score_factors.py -x` | ✅ exists | ✅ green |
| 05-06-batch | 05 / 06 | 3 | ADMIN-06 | — | Select-all / top-N checkboxes | e2e | `npx playwright test tests/admin.spec.js -g "топ"` | ✅ exists | ✅ green |
| 05-07-send | 03 / 06 | 2 | ADMIN-07 | T-05-double | Send success; repeat 409 | unit + e2e | `uv run pytest tests/unit/test_send_digest.py -x`; Отправка записана / Уже отправлено | ✅ exists | ✅ green |
| 05-08-link | 03 / 06 | 2 | ADMIN-08 / D-90 | T-05-20 | Stub body `/issues/{n}` + returnUrl | unit + e2e | `uv run pytest tests/unit/test_stub_mailer.py -x`; `tests/auth.spec.js` ADMIN-08 | ✅ exists | ✅ green |
| 05-05-adapter | 05 | 4 | ADMIN-01, ADMIN-02, ADMIN-07, ADMIN-08 | T-05-09 | Live shortlist claim + issue publish contract; SMTP fail-fast | unit | `uv run pytest tests/unit/test_supabase_shortlist_repository_contract.py tests/unit/test_live_container_wiring.py -x` | ✅ exists | ✅ green |
| 05-07-intro | 07 | 1 | ADMIN-04, ADMIN-03 | — | Preview body includes intro + ordered blocks | unit + e2e | `uv run pytest tests/unit/test_preview_digest.py tests/unit/test_http_admin.py -q --tb=short`; Playwright «Вводный текст» | ✅ exists | ✅ green |
| 05-08-blocks | 08 | 2 | ADMIN-04, ADMIN-07, ADMIN-08 | — | Reorder / interstitial drives preview; send honors material order | unit + e2e | `uv run pytest tests/unit/test_send_digest.py tests/unit/test_http_admin.py -q --tb=short`; Playwright «блок» | ✅ exists | ✅ green |
| 05-09-rest | 09 | 3 | ADMIN-01, ADMIN-07 | — | Post-send `digest_rest` hides shortlist until the next batch | unit + e2e | `uv run pytest tests/unit/test_get_admin_shortlist.py tests/unit/test_http_admin.py -q --tb=short`; rest-copy e2e | ✅ exists | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Coverage notes (05-06, audited 2026-09-22):** ADMIN-01…08 closed via unit plans + the honesty gate, then extended by gap-closure plans. Playwright cites D-77 (403 UI), D-80 (empty), D-85 (draft), D-86 (preview fingerprint), D-87/D-90 (stub send + issue CTA / returnUrl), G-05-1 (intro + reorderable blocks), and G-05-2 (`digest_rest`).

---

## Wave 0 Requirements

- [x] Align `InMemoryProfileRepository` + `meApi` mocks + `test_http_me` to `app_role` (`employee` default)
- [x] `tests/unit/test_http_admin.py` — 403 matrix for all admin routes
- [x] `tests/unit/test_send_digest.py` / `test_preview_digest.py` / `test_set_shortlist_decision.py`
- [x] `tests/admin.spec.js` — 403 page, empty state, draft block, preview gate, select-all/top-N (mocks)
- [x] Migration `005_phase5_admin_shortlist.sql` — delivery columns + seed batch (comment «demo batch для Phase 5»)
- [x] Runbook **§4e** stub mailer + seed honesty + promote admin profile
- [x] `require_admin` dependency + `routes/admin.py` router registered in `app.py`
- [x] In-memory `ShortlistRepository` + `StubMailer` fakes in `tests_support`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Promote a live Auth user to `admin` for ops proof | AUTH-03 / runbook | Environment-specific profile row | Follow runbook §4e after migrate; verify `/admin/digest` loads |
| Optional live FE↔BE admin proof under mocks=false | ADMIN-01…07 | Shared VM credentials | Runbook §4e + CI gate remains mocks |

*Otherwise: All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-09-22 (`nyquist_compliant: true`)

---

## Validation Audit 2026-09-22

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Requirement classification (COVERED = test exists, targets the behavior, and ran green):

| Requirement | Status | Evidence |
|-------------|--------|----------|
| ADMIN-01 | COVERED | `test_get_admin_shortlist.py`, `test_http_admin.py` (≤5, empty, `digest_rest`); `admin.spec.js` empty + rest |
| ADMIN-02 | COVERED | `test_set_shortlist_decision.py`, `test_http_admin.py` approve/reject; `admin.spec.js` «Одобрить выбранные» |
| ADMIN-03 | COVERED | `test_send_digest.py` draft block; `test_http_admin.py` 400; `admin.spec.js` draft hint |
| ADMIN-04 | COVERED | `test_preview_digest.py` (pool, intro, blocks, fail leaves unsent); `admin.spec.js` preview gate + intro + blocks |
| ADMIN-05 | COVERED | `test_score_factors.py`; `admin.spec.js` «обоснование недоступно» |
| ADMIN-06 | COVERED | `admin.spec.js` select-all, top-3, manual uncheck keeps siblings |
| ADMIN-07 | COVERED | `test_send_digest.py` (publish, 409, order, mismatch, claim release); `admin.spec.js` «Отправка записана» / «Уже отправлено» |
| ADMIN-08 | COVERED | `test_stub_mailer.py` + send issue path; `auth.spec.js` returnUrl `/issues/{n}`; success CTA href |
| AUTH-03 (admin gate) | COVERED | `test_http_admin.py` 403 matrix; `test_http_me.py` `app_role`; `admin.spec.js` employee 403 page |

Run on 2026-09-22: 79 phase-5 unit tests passed; 7 live-wiring tests passed; 20 `admin.spec.js` tests passed; ADMIN-08 auth returnUrl passed. No new test files. Manual-only rows stay environment proofs (live admin promote, optional mocks=false).
