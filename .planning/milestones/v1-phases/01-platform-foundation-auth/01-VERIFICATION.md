---
phase: 01-platform-foundation-auth
verified: 2026-09-19T20:05:07Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
verdict: PASS_WITH_GAPS
gaps: []
deferred:
  - truth: "AUTH-03 non-admin calls to admin APIs return HTTP 403"
    addressed_in: "Phase 5"
    evidence: "Phase 5 success criteria: 'non-admin gets 403'; PLAN 01-02/01-05 explicit Phase 1 deferral of admin-route 403"
  - truth: "FastAPI/SPA deployed to Cloud.ru application VM"
    addressed_in: "Post Phase 1 / ops follow-up (D-07)"
    evidence: "CONTEXT D-07 + docs/agents/cloudru-app-deploy-path.md — Phase 1 documents path only; does not deploy"
  - truth: "UI logout control (Выйти) visible in shell"
    addressed_in: "Later UX polish (non-blocking)"
    evidence: "signOut exists in web/src/services/authApi.js; no shell button — human-approved as non-blocking 2026-09-19"
decision_coverage:
  honored: 15
  total: 16
  not_honored:
    - "D-03: Phase 1 auth is email+password only; no MFA and no corporate SSO (soft warning — implementation is password-only; phrasing not mirrored in SUMMARY text)"
---

# Phase 1: Platform Foundation & Auth Verification Report

**Phase Goal:** Operators and developers have a working secured stack; СВА users can log in with corporate email and the SPA talks to real APIs  
**Verified:** 2026-09-19T20:05:07Z  
**GSD status:** `passed`  
**Product verdict:** **PASS_WITH_GAPS** (goal achieved; remaining items explicitly deferred)  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Self-hosted Supabase is up with schema/RLS; app secrets are env-only; CORS allows the SPA origin | ✓ VERIFIED | Schema+RLS in `supabase-integration/migrations/001_initial_schema.sql`; live adapters `composition/live.py` + `SupabasePingRecorder`/`SupabaseProfileRepository`; `.env.example` (no secrets) + `git check-ignore` confirms `.env.example` not ignored; CORS allowlist via `Settings.cors_origins` / `tests/unit/test_cors.py` |
| 2 | FastAPI serves health and authenticated domain endpoints without critical errors; structured logs capture failures | ✓ VERIFIED | `GET /health`, `GET /me`, `POST /me/ping` in `interface/http/`; `RequestIdMiddleware` + structlog JSON; unit tests `test_http_health.py`, `test_http_me.py`, `test_request_id.py` (31 focused tests passed this run) |
| 3 | User with allowed corporate domain can log in and land on current issue (or returnUrl); disallowed domain never gets a session | ✓ VERIFIED | FE: `emailDomain.js` + `LoginPage` + Playwright `tests/auth.spec.js`; API: `is_allowed_corporate_email` + `domain_not_allowed` 403 in `deps.py`; human live login approved 2026-09-19 (01-06-SUMMARY) |
| 4 | Frontend loads at least one protected resource from the server and can POST a mutation that persists | ✓ VERIFIED | `meApi.fetchMe` → `GET /me`; `meApi.postPing` → `POST /me/ping` → `activity_events` via live `SupabasePingRecorder`; `PlatformProofBanner` on IssuePage; human confirmed row persisted 2026-09-19 |
| 5 | Network/validation errors handled per global error UX; README/deploy docs bring up local + documented Cloud.ru path | ✓ VERIFIED | Login `ErrorPanel` + Retry (Playwright network banner); `docs/agents/local-platform-runbook.md` + `cloudru-app-deploy-path.md` linked from README; Cloud.ru is docs-only by D-07 |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | AUTH-03 admin-API 403 for non-admin | Phase 5 | Phase 5 SC #1 «non-admin gets 403»; Phase 1 plans defer admin routes |
| 2 | Cloud.ru app VM deploy of FastAPI/SPA | Docs / later ops | D-07; `cloudru-app-deploy-path.md` states Phase 1 does not deploy |
| 3 | UI logout button | Later UX (non-blocking) | `authApi.signOut` only; human accepted gap |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `backend/.../interface/http/app.py` | FastAPI factory, CORS, routers | ✓ VERIFIED | Wired health + me; live/memory container |
| `backend/.../interface/http/routes/me.py` | GET/PATCH /me, POST /me/ping | ✓ VERIFIED | JWT via `get_principal`; Phase 5 deferral noted |
| `backend/.../composition/live.py` | Live Supabase wiring | ✓ VERIFIED | service_role clients only here |
| `supabase-integration/.../ping_recorder.py` | Persist platform_ping | ✓ VERIFIED | inserts `activity_events` |
| `supabase-integration/.../profile_repository.py` | Profiles adapter | ✓ VERIFIED | get_or_upsert |
| `web/src/services/authApi.js` | Sign-in/session | ✓ VERIFIED | mock/live via `VITE_USE_MOCKS` |
| `web/src/services/meApi.js` | Bearer /me + /me/ping | ✓ VERIFIED | live fetch path when mocks false |
| `web/src/components/RequireAuth.jsx` | Auth gate | ✓ VERIFIED | redirect `/login?returnUrl=` |
| `web/src/pages/LoginPage.jsx` | Corporate login UX | ✓ VERIFIED | domain check + ErrorPanel |
| `web/src/components/PlatformProofBanner.jsx` | FE↔BE proof UI | ✓ VERIFIED | fetchMe + postPing |
| `tests/auth.spec.js` | AUTH Playwright contracts | ✓ VERIFIED | 7 contracts present |
| `docs/agents/local-platform-runbook.md` | Local bring-up | ✓ VERIFIED | D-05 path |
| `docs/agents/cloudru-app-deploy-path.md` | Deploy path docs | ✓ VERIFIED | no Phase 1 deploy |
| `.env.example` | Secret template | ✓ VERIFIED | placeholders only; not gitignored |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `LoginPage.jsx` | `authApi.signIn` | services import | ✓ WIRED | domain gate before signIn |
| `RequireAuth.jsx` | `/login?returnUrl=` | React Router `Navigate` | ✓ WIRED | gated when mocks off / force-gate |
| `meApi.js` | FastAPI `/me`, `/me/ping` | `fetch` + Bearer | ✓ WIRED | `VITE_API_BASE_URL` |
| `PlatformProofBanner` | `meApi` | IssuePage mount | ✓ WIRED | D-10 proof surface |
| `me.router` | `record_platform_ping` | use-case + container.pings | ✓ WIRED | |
| `SupabasePingRecorder` | `activity_events` | service_role insert | ✓ WIRED | `kind=platform_ping` |
| `create_app` | `build_live_container` | `APP_CONTAINER=live` | ✓ WIRED | `resolve_container` |

*(gsd-tools `verify.key-links` reported false for descriptive PLAN from-paths; manual path/wiring checks above supersede.)*

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| PlatformProofBanner identity | `user` from `fetchMe` | live: FastAPI GET /me → ProfileRepository; mock: session email | Yes (live path + human proof) | ✓ FLOWING |
| PlatformProofBanner ping | `postPing` → `{ok,id}` | live: POST /me/ping → activity_events insert | Yes (human confirmed row) | ✓ FLOWING |
| Login session | Supabase Auth / mockSession | live: `signInWithPassword`; mock harness | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Health + CORS + request_id | `uv run pytest tests/unit/test_http_health.py tests/unit/test_cors.py tests/unit/test_request_id.py -q` | 6 passed | ✓ PASS |
| /me + JWT + ping + domain | `uv run pytest tests/unit/test_http_me.py tests/unit/test_record_platform_ping.py tests/unit/test_supabase_ping_recorder_contract.py tests/unit/test_auth_email_domain.py tests/unit/test_jwt_verify.py -q` | 25 passed | ✓ PASS |
| FE email domain helper | `node --test web/src/services/emailDomain.test.js` | 4 passed | ✓ PASS |
| Auth Playwright contracts exist | enumerate `tests/auth.spec.js` | 7 tests defined (domain, login, returnUrl, gate, network, me+ping, display_name) | ✓ PASS (existence) |
| Live FE↔BE | Human checkpoint 01-06 | Approved 2026-09-19 | ✓ PASS (human) |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase probe scripts declared | SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| PLAT-01 | 01-04, 01-06 | Self-hosted Supabase schema/RLS | COVERED | `001_initial_schema.sql` RLS; live adapters; runbook treats VM as primary (D-05) |
| PLAT-02 | 01-01 | FastAPI endpoints healthy | COVERED | `/health`, `/me`, `/me/ping`; `test_http_health.py` / `test_http_me.py` |
| PLAT-03 | 01-02, 01-05, 01-06 | Authenticated FE reads from server | COVERED | `meApi.fetchMe`; human GET /me live proof |
| PLAT-04 | 01-03, 01-04, 01-06 | Mutations persist E2E | COVERED | `postPing` → `SupabasePingRecorder` → `activity_events`; human row proof |
| PLAT-05 | 01-01 | Secrets env-only | COVERED | `.env.example` placeholders; `.env` gitignored; no `VITE_` secret key |
| PLAT-06 | 01-01 | CORS allowlist | COVERED | `CORSMiddleware` + `test_cors.py` |
| PLAT-07 | 01-01, 01-05 | Error UX + request correlation | COVERED | `X-Request-ID`/structlog; Login ErrorPanel Retry; Playwright network banner |
| PLAT-08 | 01-06 | Local + Cloud.ru docs | COVERED | `local-platform-runbook.md` + `cloudru-app-deploy-path.md` (deploy deferred by design) |
| AUTH-01 | 01-02, 01-05, 01-06 | Corporate domain login / reject | COVERED | FE+API domain gates; Playwright + pytest; live login approved |
| AUTH-02 | 01-05 | Landing `/` or returnUrl | COVERED | Playwright navigate + returnUrl tests; `sanitizeReturnUrl` |
| AUTH-03 | 01-02, 01-05 | Auth policies + redirects; admin 403 | PARTIAL | JWT deps + RequireAuth **COVERED**; admin-API 403 **DEFERRED → Phase 5** |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `LoginPage.jsx` | ~110, ~129 | HTML `placeholder=` attrs | ℹ️ Info | Form placeholders only — not stub debt |

No `TBD`/`FIXME`/`XXX` blockers in phase production files. No empty stub handlers on auth/me proof path.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/unit/test_http_health.py` | PLAT-02 | yes | 0 | no | Status/value | OK |
| `tests/unit/test_cors.py` | PLAT-06 | yes | 0 | no | Value (ACA-O) | OK |
| `tests/unit/test_request_id.py` | PLAT-07 | yes | 0 | no | Value | OK |
| `tests/unit/test_http_me.py` | PLAT-03, AUTH-01/03 | yes | 0 | no | Behavioral (401/200/403/ping) | OK |
| `tests/unit/test_auth_email_domain.py` | AUTH-01 | yes | 0 | no | Value | OK |
| `tests/unit/test_jwt_verify.py` | AUTH-03 | yes | 0 | no | Value | OK |
| `tests/unit/test_record_platform_ping.py` | PLAT-04 | yes | 0 | no | Behavioral | OK |
| `tests/unit/test_supabase_ping_recorder_contract.py` | PLAT-04 | yes | 0 | no | Behavioral (stub client) | OK |
| `web/src/services/emailDomain.test.js` | AUTH-01 | yes | 0 | no | Value | OK |
| `tests/auth.spec.js` | AUTH-01/02/03, PLAT-03/07 | yes | 0 | no | Behavioral (UI) | OK |

**Disabled tests on requirements:** 0  
**Circular patterns detected:** 0  
**Insufficient assertions:** 0

### Decision Coverage

### Decision Coverage (warning)

1 decision(s) not found in shipped artifacts:

- **D-03** (Auth & session): Phase 1 auth is email+password only; no MFA and no corporate SSO.

This is a soft warning — verification status unchanged. Implementation uses `signInWithPassword` only (honored in practice); SUMMARY text did not echo the “no MFA/SSO” phrase.

### Human Verification Required

N/A for pending items — live FE↔BE human checkpoint **already approved** 2026-09-19 (01-06-SUMMARY): corporate login, GET /me, POST /me/ping, `activity_events` row; email acceptable as shell identity; optional `display_name` present.

Phase includes user-facing login, but the blocking manual proof is complete. No further human gate required to close Phase 1.

### Gaps Summary

**No blocking gaps.** Goal-backward truths all hold in the codebase with automated + human evidence.

Explicit non-blocking / deferred:

1. **AUTH-03 admin 403** — no admin routes in Phase 1; tracked to Phase 5 ADMIN-01 / SC «non-admin gets 403».
2. **Cloud.ru deploy** — intentionally docs-only (D-07 / PLAT-08 path documentation).
3. **Logout UI** — `signOut` API exists; shell button absent; accepted as non-blocking.

**Product verdict: PASS_WITH_GAPS** — Phase 1 roadmap goal achieved; proceed to Phase 2.

---

_Verified: 2026-09-19T20:05:07Z_  
_Verifier: Claude (gsd-verifier)_
