---
status: complete
phase: 01-platform-foundation-auth
source:
  - 01-01-SUMMARY.md
  - 01-02-SUMMARY.md
  - 01-03-SUMMARY.md
  - 01-04-SUMMARY.md
  - 01-05-SUMMARY.md
  - 01-06-SUMMARY.md
  - 01-07-SUMMARY.md
  - 01-08-SUMMARY.md
started: 2026-09-19T18:50:00Z
updated: 2026-09-20T09:24:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running Vite/uvicorn. Start from scratch per docs/agents/local-platform-runbook.md: FastAPI (APP_CONTAINER=live) and Vite (VITE_USE_MOCKS=false) boot without errors; GET /health returns live JSON; SPA loads login or issue without crash.
result: pass

### 2. Manual corporate Auth users on shared Supabase dashboard
expected: 1–2 corporate test users (@sberbank.ru / @omega.sbrf.ru) exist in the shared Supabase Auth dashboard and can sign in (D-08; not automated against shared VM).
result: pass
rationale: D-08 forbids automated seed against shared VM; deferred to Plan 01-06 live proof
reason: human_judgment
coverage_id: 01-04-D5

### 3. Live FE↔BE proof + registration UX (G-01-3b retest)
expected: With VITE_USE_MOCKS=false and live API — (1) /login is email+password only (no «Имя»/«Логин»); «Регистрация» goes to /register; (2) /register has «Логин» (nickname) + email + password and can create a user; (3) after login or register, PlatformProofBanner shows identity from GET /me and Ping writes platform_ping to activity_events.
result: pass
reported: "всё прошло успешно. yarkiller@sberbank.ru / display yarkiller created in Auth Users. Remark (deferred): password <6 chars rejected without placeholder/hint."
ops_note: "2026-09-20 mailer_autoconfirm=true; SPA register confirmed"
prior_issue: "регистрация не проходит (mailer 500) — ops autoconfirm applied"
rationale: Re-test after G-01-3b ops fix
reason: human_judgment
coverage_id: 01-06-D3

### 4. GET /health returns 200 JSON status ok without auth
expected: GET /health returns 200 JSON status ok without auth
result: pass
source: automated
coverage_id: 01-01-D1

### 5. CORS allowlist from API_CORS_ORIGINS reflects allowed Origin
expected: CORS allowlist from API_CORS_ORIGINS reflects allowed Origin
result: pass
source: automated
coverage_id: 01-01-D2

### 6. X-Request-ID on responses; structlog JSON includes bound request_id
expected: X-Request-ID on responses; structlog JSON includes bound request_id
result: pass
source: automated
coverage_id: 01-01-D3

### 7. Committed .env.example with Phase 1 keys; not gitignored
expected: Committed .env.example with Phase 1 keys; not gitignored
result: pass
source: automated
coverage_id: 01-01-D4

### 8. GET /me rejects missing/invalid Bearer with 401
expected: GET /me rejects missing/invalid Bearer with 401
result: pass
source: automated
coverage_id: 01-02-D1

### 9. Valid ES256 JWT with allowed corporate email returns CurrentUser from GET /me
expected: Valid ES256 JWT with allowed corporate email returns CurrentUser from GET /me
result: pass
source: automated
coverage_id: 01-02-D2

### 10. Valid JWT with disallowed email domain returns 403 domain_not_allowed
expected: Valid JWT with disallowed email domain returns 403 domain_not_allowed
result: pass
source: automated
coverage_id: 01-02-D3

### 11. Offline ES256 JWKS verify rejects HS256/expired/wrong aud
expected: Offline ES256 JWKS verify rejects HS256/expired/wrong aud
result: pass
source: automated
coverage_id: 01-02-D4

### 12. record_platform_ping stores kind platform_ping via PingRecorder
expected: record_platform_ping stores kind platform_ping via PingRecorder
result: pass
source: automated
coverage_id: 01-03-D1

### 13. POST /me/ping without/invalid Bearer returns 401
expected: POST /me/ping without/invalid Bearer returns 401
result: pass
source: automated
coverage_id: 01-03-D2

### 14. Valid corporate JWT POST /me/ping returns 200 and records platform_ping
expected: Valid corporate JWT POST /me/ping returns 200 and records platform_ping in-memory
result: pass
source: automated
coverage_id: 01-03-D3

### 15. build_in_memory_container exposes pings on AppContainer
expected: build_in_memory_container exposes pings on AppContainer
result: pass
source: automated
coverage_id: 01-03-D4

### 16. SupabasePingRecorder inserts activity_events with kind platform_ping
expected: SupabasePingRecorder inserts activity_events with kind platform_ping via stubbed client
result: pass
source: automated
coverage_id: 01-04-D1

### 17. SupabaseProfileRepository get_or_upsert returns app_role and is idempotent
expected: SupabaseProfileRepository get_or_upsert returns app_role and is idempotent
result: pass
source: automated
coverage_id: 01-04-D2

### 18. build_live_container wires Supabase adapters; create_client only under composition
expected: build_live_container wires Supabase adapters; create_client only under composition
result: pass
source: automated
coverage_id: 01-04-D3

### 19. README documents remote VM connectivity, APP_CONTAINER=live, manual Auth seed
expected: README documents remote VM connectivity, APP_CONTAINER=live, manual Auth seed (PLAT-01/D-08)
result: pass
source: automated
coverage_id: 01-04-D4

### 20. Corporate email domain helper rejects non-ADR-0003 domains
expected: Corporate email domain helper rejects non-ADR-0003 domains
result: pass
source: automated
coverage_id: 01-05-D1

### 21. Disallowed domain shows inline message; signIn not invoked
expected: Disallowed domain shows inline message; signIn not invoked
result: pass
source: automated
coverage_id: 01-05-D2

### 22. Successful login without returnUrl navigates to current issue /
expected: Successful login without returnUrl navigates to current issue /
result: pass
source: automated
coverage_id: 01-05-D3

### 23. returnUrl=/voting returns to /voting after login
expected: returnUrl=/voting returns to /voting after login
result: pass
source: automated
coverage_id: 01-05-D4

### 24. Auth gate redirects unauthenticated users to /login?returnUrl=…
expected: Auth gate redirects unauthenticated users to /login?returnUrl=…
result: pass
source: automated
coverage_id: 01-05-D5

### 25. meApi mock identity + platform ping proof on IssuePage
expected: meApi mock identity + platform ping proof on IssuePage
result: pass
source: automated
coverage_id: 01-05-D6

### 26. Login network failure shows ErrorPanel + Retry (PLAT-07)
expected: Login network failure shows ErrorPanel + Retry (PLAT-07)
result: pass
source: automated
coverage_id: 01-05-D7

### 27. Local platform runbook covers env, uv/uvicorn, Vite, Auth seed, live checklist
expected: Local platform runbook covers env, uv/uvicorn, Vite, Auth seed, live checklist
result: pass
source: automated
coverage_id: 01-06-D1

### 28. Cloud.ru deploy-path doc states Phase 1 does not deploy; linked from README
expected: Cloud.ru deploy-path doc states Phase 1 does not deploy; linked from README
result: pass
source: automated
coverage_id: 01-06-D2

## Summary

total: 28
passed: 28
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

```yaml
- gap_id: G-01-3
  truth: "Corporate login → GET /me → POST /me/ping works; login UX is email+password only; registration is a separate form with a clear name field (ФИО or Имя)"
  status: resolved
  resolved_by: 01-07-PLAN.md, 01-08-PLAN.md
  resolved_at: 2026-09-19
  reason: "User reported: кнопка Регистрация не активна и не ведёт к регистрации. Форма для входа не должна иметь поля Имя..."
  severity: major
  test: 3
  root_cause: "SPA had dead Регистрация CTA and name-on-login; fixed by 01-07/01-08."
  artifacts: []
  missing: []
  debug_session: g-01-3-registration-ux

- gap_id: G-01-3b
  truth: "Self-service /register creates an Auth user (Логин + corporate email) and can proceed to live /me + ping"
  status: resolved
  resolved_by: "ops: Confirm email OFF (mailer_autoconfirm=true) on knowledge-db.ru"
  resolved_at: 2026-09-20
  reason: "User reported: регистрация не проходит. Новый пользователь в Supabase не появился. UI shows NETWORK ErrorPanel."
  severity: blocker
  test: 3
  root_cause: "GoTrue POST /auth/v1/signup returns 500 unexpected_failure «Error sending confirmation email» — mailer_autoconfirm=false and SMTP/mailer broken on knowledge-db.ru; user not created. SPA correctly calls signUp; maps 500 to retryable network copy."
  artifacts:
    - .planning/debug/g-01-3b-signup-mailer.md
    - web/src/services/authApi.js
    - web/src/pages/RegisterPage.jsx
  missing: []
  ops_verified_at: 2026-09-20
  ops_verified: "mailer_autoconfirm=true; POST /auth/v1/signup → 200; SPA register yarkiller@sberbank.ru created"
  retest: pass
  debug_session: g-01-3b-signup-mailer
  decision: |
    Option 3 split (2026-09-19): (1) autoconfirm now to unblock UAT — DONE 2026-09-20;
    (2) SPA honest mailer error UX = deferred follow-up;
    (3) SMTP = ops ticket outside Phase 1 — no email-dependent product features until fixed.
```

## Deferred Follow-Ups

```yaml
- test: 3
  idea: "SPA: map GoTrue confirmation-mailer / unexpected_failure signup errors to honest Russian copy (not generic NETWORK «Сервис входа временно недоступен»)"
  deferred_at: 2026-09-19
  tracks: G-01-3b-spa-copy
- test: 3
  idea: "Ops ticket: configure working SMTP for GoTrue on knowledge-db.ru; until then do not ship password-reset / invite / confirm-email product features"
  deferred_at: 2026-09-19
  tracks: G-01-3b-smtp-ops
- test: 3
  idea: "Register password field: surface GoTrue min length (6) in placeholder and/or helper text so rejection is not a surprise"
  deferred_at: 2026-09-20
  tracks: G-01-3-password-hint
```
