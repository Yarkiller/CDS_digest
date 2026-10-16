---
phase: "20"
slug: "mail-02-signup-confirmation-mail"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-16"
validated: "2026-10-16"
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright `@playwright/test` ^1.62.1 + pytest via `uv` |
| **Config file** | `playwright.config.js` (web project forces `VITE_USE_MOCKS=true`) |
| **Quick run command** | `npx playwright test tests/auth.spec.js --project=web -g "shell identity after register\|post-register copy\|Регистрация завершена\|confirmation letter"` |
| **Full suite command** | `npm test` (Playwright) and `npm run test:unit` (pytest) |
| **Estimated runtime** | ~60–120 seconds (auth.spec.js alone ~30s; fence unit ~1s) |

---

## Sampling Rate

- **After every task commit:** Run that task's filtered `<automated>` smoke (Plan 20-01 Task 2: `npx playwright test tests/auth.spec.js --project=web -g "shell identity after register|post-register copy|Регистрация завершена|confirmation letter"` + domain/fence pytest when listed)
- **After every plan wave:** Run full `npx playwright test tests/auth.spec.js --project=web` / `npm run test:web` + `uv run pytest tests/unit/test_auth_email_domain.py tests/unit/test_signup_confirmation_mail_fence.py`
- **Before `/gsd-verify-work`:** Full suite must be green (`npm run test:web` + unit suite)
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 20-01 | 1 | MAIL-02 | T-20-01, T-20-02 | Honest (B) copy + letter-claim forbid + Mailer fence | e2e + unit | `npx playwright test tests/auth.spec.js --project=web -g "post-register copy\|Регистрация завершена\|confirmation letter" && uv run pytest tests/unit/test_signup_confirmation_mail_fence.py -x` | ✅ | ✅ green |
| 20-01-02 | 20-01 | 1 | MAIL-02 | T-20-03 | Autoconfirm happy-path + honest-copy filtered smoke; domain gate PRESERVE | e2e + unit | `npx playwright test tests/auth.spec.js --project=web -g "shell identity after register\|post-register copy\|Регистрация завершена\|confirmation letter" && uv run pytest tests/unit/test_auth_email_domain.py -x` | ✅ | ✅ green |
| 20-02-01 | 20-02 | 2 | MAIL-02 | T-20-08 | Debug session closed with fix ref (not deleted) | doc smoke | `git ls-files -- ".planning/debug/**/g-01-3b-signup-mailer.md" && rg -n "## Resolution\|mailer_autoconfirm\|unexpected_failure\|CONFIRM_MESSAGE" .planning/debug --glob "*g-01-3b-signup-mailer.md"` | ✅ | ✅ green |
| 20-02-02 | 20-02 | 2 | MAIL-02 | T-20-05, T-20-06, T-20-07 | Runbook SMTP shape/smoke/rollback; criterion-4 → Phase 21 | doc smoke + unit | `rg -n "GOTRUE_SMTP_\|GOTRUE_MAILER_AUTOCONFIRM\|SMTP_\|Phase 21\|mailer_autoconfirm\|/auth/v1/settings" docs/agents/local-platform-runbook.md && uv run pytest tests/unit/test_auth_email_domain.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Amend/add `tests/auth.spec.js` coverage for honest `CONFIRM_MESSAGE` (D-09) — owned by **20-01** Task 1 (RED first)
- [x] New D-10 regression (negative letter-claim assert) — owned by **20-01** Task 1 (same test)
- [x] Harness `armSignUpWithoutSession` in `authApi.js` + `main.jsx` — owned by **20-01** Task 1 (DOM path chosen)
- [x] Framework install: none
- [x] Nyquist gap fill: `tests/unit/test_signup_confirmation_mail_fence.py` (SC3 Mailer fence + D-07/D-08 constant ownership)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | — | All in-scope Phase 20 behaviors have automated verification. ROADMAP SC4 live corporate-relay smoke proof is an acknowledged deferred gap → Phase 21 (documented in runbook §4.1.3); not a Phase 20 Nyquist gap. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-16 (Nyquist validate-phase audit)

---

## Validation Audit 2026-10-16

| Metric | Count |
|--------|-------|
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

### Gap detail

| Gap | Classification | Resolution |
|-----|----------------|------------|
| MAIL-02 SC3 / T-20-02 Mailer fence + D-07/D-08 constant ownership had no dedicated automated tripwire (only UAT/human ack + Playwright for copy) | MISSING → FILLED | Added `tests/unit/test_signup_confirmation_mail_fence.py` (3 passed) |

### Re-run evidence (this audit)

```text
npx playwright test tests/auth.spec.js --project=web -g "shell identity after register|post-register copy|Регистрация завершена|confirmation letter"
→ 2 passed

uv run pytest tests/unit/test_auth_email_domain.py -x
→ 5 passed

uv run pytest tests/unit/test_signup_confirmation_mail_fence.py -x
→ 3 passed

git ls-files -- ".planning/debug/**/g-01-3b-signup-mailer.md"
→ .planning/debug/g-01-3b-signup-mailer.md

rg Resolution/mailer tokens in debug + runbook
→ all required tokens present
```
