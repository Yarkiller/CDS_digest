---
phase: 1
slug: platform-foundation-auth
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: 2026-09-20
verified: 2026-09-20
register_authored_at_plan_time: true
---

# Phase 1 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> L1 ASVS grep-depth verification (workflow.security_asvs_level=1). Plan-time STRIDE registers present → auditor short-circuit when threats_open=0.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser → GoTrue (knowledge-db.ru) | Publishable-client Auth (signIn / signUp) | email, password, access/refresh tokens |
| Browser → FastAPI | JWT Bearer on `/me`, `/me/ping` | access_token, CurrentUser, ping ack |
| FastAPI → Supabase PostgREST | service_role client (composition/live only) | profiles upsert, activity_events insert |
| FastAPI → JWKS | ES256 signature verify | JWKS keys, JWT claims |
| Operator → Auth dashboard | Manual seed fallback (D-08) | Auth user rows |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Spoofing | auth_jwt / get_principal /me /ping | high | mitigate | ES256 JWKS verify + exp/aud/iss; invalid → 401; same gate on GET/POST | closed |
| T-01-02 | Elevation of Privilege | email domain gate | high | mitigate | FastAPI `is_allowed_corporate_email` → 403 `domain_not_allowed` | closed |
| T-01-03 | Information Disclosure | structured logs | medium | mitigate | RequestIdMiddleware logs method/path/status/request_id only — never Authorization | closed |
| T-01-04 | Information Disclosure | CORS | medium | mitigate | Explicit `API_CORS_ORIGINS` allowlist — no wildcard with credentials | closed |
| T-01-05 | Tampering | package installs | high | mitigate | Plan 01 legitimacy checkpoint before uv/npm add (executed) | closed |
| T-01-SC | Tampering | uv/npm installs | high | mitigate | Human confirms Approved packages; gap plans accepted no new packages | closed |
| T-01-06 | Elevation of Privilege | service_role client | critical | mitigate | `create_service_role_client` only in `composition/live.py`; never VITE_ | closed |
| T-01-07 | Tampering | shared VM data | high | mitigate | Manual Auth seed only (D-08); no DROP/migrate automation in Phase 1 | closed |
| T-01-08 | Spoofing | JWKS fetch | medium | mitigate | `PyJWKClient` / injectable resolver; fail closed on InvalidTokenError | closed |
| T-01-09 | Spoofing | localStorage session | medium | accept | D-02 locked; httpOnly bridge deferred — see Accepted Risks | closed |
| T-01-10 | Information Disclosure | Vite env | critical | mitigate | `.env.example`: only publishable VITE_ keys; comment forbids SECRET behind VITE_ | closed |
| T-01-11 | Elevation of Privilege | LoginPage domain check | medium | mitigate | UI `isAllowedCorporateEmail` + API gate + Auth config | closed |
| T-01-12 | Spoofing | returnUrl | medium | mitigate | `sanitizeReturnUrl` — relative same-app paths only | closed |
| T-01-07-01 | Spoofing | RegisterPage email | high | mitigate | `isAllowedCorporateEmail` before `signUp`; FastAPI still rejects disallowed JWT | closed |
| T-01-07-02 | Elevation of Privilege | authApi / SPA bundle | critical | mitigate | Publishable supabase-js only; no service_role import under `web/` | closed |
| T-01-07-03 | Information Disclosure | signUp error messages | medium | mitigate | Map Auth errors to generic Russian credential/network copy (signIn pattern) | closed |
| T-01-07-04 | Tampering | Логин / display_name | low | accept | React text rendering; PATCH /me max_length server-side — see Accepted Risks | closed |
| T-01-07-SC | Tampering | npm installs | high | accept | No new packages in 01-07 — see Accepted Risks | closed |
| T-01-08-01 | Information Disclosure | runbook / COVERAGE | medium | mitigate | Admin Auth API / service_role OPT-OUT; publishable `signUp` only documented | closed |
| T-01-08-02 | Elevation of Privilege | CONTEXT D-08 seed | low | mitigate | Dashboard seed optional fallback; no automated shared-VM seed scripts | closed |
| T-01-08-SC | Tampering | npm/pip installs | high | accept | Docs-only 01-08; no package installs — see Accepted Risks | closed |
| T-01-13 | Information Disclosure | runbook/docs | medium | mitigate | Env-only secrets; no real keys in markdown (runbook + `.env.example`) | closed |
| T-01-14 | Tampering | live proof on shared VM | medium | mitigate | Checklist insert-only ping; no DROP/reset instructions | closed |
| T-01-15 | Denial of Service | documented deploy | low | accept | Docs only — no automated deploy in Phase 1 — see Accepted Risks | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `block_on: high` count toward `threats_open`*
*Disposition: mitigate · accept · transfer*

### Evidence (L1)

- `backend/.../infrastructure/auth_jwt.py` — ES256 / PyJWKClient
- `backend/.../interface/http/deps.py` — `get_principal` + domain gate
- `backend/.../interface/http/middleware.py` — no Authorization in logs
- `backend/.../composition/live.py` — sole service_role construction
- `web/src/services/authEnv.js` — `sanitizeReturnUrl`
- `web/src/services/emailDomain.js` + Login/Register pages — UI domain gate
- `web/` — no `service_role` / `SUPABASE_SECRET` imports (comment-only mention in authApi)
- `.env.example` + runbook §4 — publishable-only Vite; autoconfirm/SMTP ops notes
- `COVERAGE.md` — admin.* OPT-OUT
- `docs/agents/local-platform-runbook.md` + Cloud.ru path doc — no secret paste / no Phase 1 deploy

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-09 | T-01-09 | SPA session in localStorage per D-02; XSS → token theft; httpOnly BFF deferred past Phase 1 | plan disposition + secure-phase | 2026-09-20 |
| AR-01-07-04 | T-01-07-04 | Display nickname is non-privileged UI text; server PATCH validates length | plan disposition + secure-phase | 2026-09-20 |
| AR-01-07-SC | T-01-07-SC | Gap plan added no npm packages | plan disposition + secure-phase | 2026-09-20 |
| AR-01-08-SC | T-01-08-SC | Docs-only plan; no installs | plan disposition + secure-phase | 2026-09-20 |
| AR-01-15 | T-01-15 | Phase 1 documents Cloud.ru path only; no automated deploy | plan disposition + secure-phase | 2026-09-20 |

*Deferred (not threats, ops/UX follow-ups from UAT): SPA honest mailer error copy; SMTP ops ticket; password min-length hint — see `01-UAT.md` Deferred Follow-Ups. SMTP unhealthy is gated by autoconfirm + no email-dependent product features (CONTEXT D-17).*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-20 | 24 | 24 | 0 | gsd-secure-phase (L1 short-circuit) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-20
