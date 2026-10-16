---
phase: "20"
slug: "mail-02-signup-confirmation-mail"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-16"
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright `@playwright/test` ^1.62.1 + pytest via `uv` |
| **Config file** | `playwright.config.js` (web project forces `VITE_USE_MOCKS=true`) |
| **Quick run command** | `npx playwright test tests/auth.spec.js --project=web` |
| **Full suite command** | `npm test` (Playwright) and `npm run test:unit` (pytest) |
| **Estimated runtime** | ~60–120 seconds (auth.spec.js alone ~30s) |

---

## Sampling Rate

- **After every task commit:** Run `npx playwright test tests/auth.spec.js --project=web`
- **After every plan wave:** Run `npm run test:web` + `uv run pytest tests/unit/test_auth_email_domain.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 20-01 | 1 | MAIL-02 | T-20-01, T-20-02 | Honest (B) copy + letter-claim forbid under null-session harness | e2e | `npx playwright test tests/auth.spec.js --project=web -g "post-register copy\|Регистрация завершена\|confirmation letter"` | ❌ W0 | ⬜ pending |
| 20-01-02 | 20-01 | 1 | MAIL-02 | T-20-03 | Autoconfirm happy path + full auth.spec green; domain gate PRESERVE | e2e + unit | `npx playwright test tests/auth.spec.js --project=web` then `uv run pytest tests/unit/test_auth_email_domain.py -x` | ✅ happy path / ✅ domain | ⬜ pending |
| 20-02-01 | 20-02 | 2 | MAIL-02 | T-20-08 | Debug session closed with fix ref (not deleted) | doc + rg | `git ls-files -- ".planning/debug/**/g-01-3b-signup-mailer.md"` + `rg` Resolution/diagnosis | ✅ | ⬜ pending |
| 20-02-02 | 20-02 | 2 | MAIL-02 | T-20-05, T-20-06, T-20-07 | Runbook SMTP shape/smoke/rollback; criterion-4 → Phase 21 | doc + unit | `rg` GOTRUE_SMTP_/rollback/Phase 21 in runbook; `uv run pytest tests/unit/test_auth_email_domain.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Amend/add `tests/auth.spec.js` coverage for honest `CONFIRM_MESSAGE` (D-09) — owned by **20-01** Task 1 (RED first)
- [ ] New D-10 regression (negative letter-claim assert) — owned by **20-01** Task 1 (same test)
- [ ] Harness `armSignUpWithoutSession` in `authApi.js` + `main.jsx` — owned by **20-01** Task 1 (DOM path chosen)
- [ ] Framework install: none

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Debug session closed with fix ref | MAIL-02 | Doc artifact | Review `.planning/debug/g-01-3b-signup-mailer.md` — status closed, links shipped fix |
| Runbook SMTP/smoke/rollback section | MAIL-02 | Ops doc; relay values unavailable in-session | Review `docs/agents/local-platform-runbook.md` §4.1+ for GoTrue mailer shape, smoke, one-command rollback |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
