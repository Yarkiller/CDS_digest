---
status: resolved
resolved:
  at: 2026-10-16
  evidence: "Phase 20 Plan 20-01 shipped path (B) honest CONFIRM_MESSAGE + Playwright letter-claim forbid; path (A) relay procedure documented in runbook §4.1 (Plan 20-02)"
trigger: "Diagnose UAT G-01-3b signup 500 Error sending confirmation email; decide honest end state for MAIL-02"
created: 2026-09-19T00:00:00Z
updated: 2026-10-16T00:00:00Z
goal: find_root_cause_and_close_with_honest_end_state
gap_id: G-01-3b
audit_acknowledged:
  milestone: v1
  at: 2026-09-22
  status: closed
---

# Debug: G-01-3b registration signup 500

**Date:** 2026-09-19  
**Symptom:** SPA shows retryable «Сервис входа временно недоступен»; user `test3@sberbank.ru` never appears in Auth Users.

## Probe (reproduce)

`POST https://knowledge-db.ru/auth/v1/signup` with publishable apikey:

```json
{"code":500,"error_code":"unexpected_failure","msg":"Error sending confirmation email"}
```

`GET /auth/v1/settings`:

- `disable_signup`: false (signups allowed)
- `mailer_autoconfirm`: **false** (confirmation email required)
- `external.email`: true

`GET /auth/v1/health`: 200 GoTrue v2.196.0

## Root cause

Self-service `signUp` reaches GoTrue, but Auth fails while **sending the confirmation email** (SMTP / mailer misconfigured or unreachable on the shared VM). GoTrue returns HTTP 500 → supabase-js surfaces as retryable / AuthRetryableFetchError → SPA maps to NETWORK ErrorPanel. User row is not persisted (or is rolled back) because confirmation mail send failed.

This is **not** an SPA routing/UI bug from 01-07; the FE correctly calls `supabase.auth.signUp`. Login with existing dashboard-seeded users can still work (no confirmation mail on password grant).

## Fix options (operator decision 2026-09-19)

**Chosen path = option 3, split:**

1. **Autoconfirm now** — unblock UAT Test 3 (`Confirm email` OFF / `GOTRUE_MAILER_AUTOCONFIRM=true`). See runbook §4.1.
2. **SPA error UX** — **deferred follow-up** (not blocking Phase 1 seal): map confirmation-mailer failures to honest Russian copy; never lie with generic NETWORK «Сервис входа временно недоступен».
3. **SMTP** — **ops ticket, not Phase 1.** Document and do not ship email-dependent features until mailer is healthy. Revisit later.

## Verification (2026-09-20)

- `GET /auth/v1/settings` → `mailer_autoconfirm: true`
- `POST /auth/v1/signup` (`uat3.20260920121318@sberbank.ru`) → **HTTP 200**, `access_token` issued, `email_confirmed_at` set, user id `88953191-e3ed-4623-9326-9d47dda35ca8`

## Evidence artifacts

- Browser: RegisterPage ErrorPanel + Retry
- Auth Users: only `test@sberbank.ru`, `test2@omega.sbrf.ru` (no test3)
- curl signup 500 body above

## Resolution

root_cause: "GoTrue returned HTTP 500 unexpected_failure «Error sending confirmation email» when mailer_autoconfirm was false and SMTP was broken; the Auth user was not persisted. Operators later set mailer_autoconfirm true (path B runtime). SPA still claimed a confirmation letter on null-session register until Phase 20."
fix: "D-02/D-07 path (B): honest CONFIRM_MESSAGE in RegisterPage.jsx — «Регистрация завершена. Аккаунт активен — войдите.» — so null-session post-register never claims mail was sent. Playwright D-09/D-10 via armSignUpWithoutSession. D-01: path (A) working confirmation email through the corporate relay remains the target end state once GOTRUE_SMTP_* is operator-supplied and proven (runbook §4.1; criterion-4 proof deferred to Phase 21). SPA authApi NETWORK error-mapping honesty stays deferred."
verification: "Plan 20-01: npx playwright test tests/auth.spec.js --project=web -g \"shell identity after register|post-register copy|Регистрация завершена|confirmation letter\" (2 passed); uv run pytest tests/unit/test_auth_email_domain.py -x (5 passed, zero edits). Current runtime: GET /auth/v1/settings mailer_autoconfirm true."
files_changed:
  - web/src/pages/RegisterPage.jsx
  - web/src/services/authApi.js
  - web/src/main.jsx
  - tests/auth.spec.js
  - docs/agents/local-platform-runbook.md
oracle_type: specified
specialist_hint: gotrue-ops + react
