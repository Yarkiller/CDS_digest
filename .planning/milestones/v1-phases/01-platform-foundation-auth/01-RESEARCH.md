# Phase 1: Platform Foundation & Auth - Research

**Researched:** 2026-09-19
**Domain:** Self-hosted Supabase Auth (ES256 JWKS) + FastAPI JWT API + Vite/React SPA
**Confidence:** HIGH (brownfield + live JWKS probe + official docs); MEDIUM on exact PyJWT JWKS wiring details

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use Supabase Auth for login; FastAPI validates JWT on API routes (middleware/deps). — **Reversibility:** costly — switching away from Supabase Auth later rewrites SPA auth client and API verification.
- **D-02:** Client session via Supabase JS default storage (localStorage/sessionStorage). — **Reversibility:** costly — moving to httpOnly cookies needs cookie bridge and CSP/CORS revisits.
- **D-03:** Phase 1 auth is email+password only; no MFA and no corporate SSO.
- **D-04:** Allowed domains `@sberbank.ru` / `@omega.sbrf.ru` enforced defense-in-depth: Supabase Auth config/hooks + UI inline message + FastAPI email claim check. — **Reversibility:** reversible for UI layer; Auth hook is more sticky.
- **D-05:** Day-1 runtime = local Vite + local FastAPI pointed at the **existing remote VM Supabase** (schema already applied; MCP available). Do not require a second local Docker Supabase for Phase 1 success.
- **D-06:** Secrets via gitignored `.env` + committed `.env.example` (SUPABASE_URL, keys, CORS, API URL). Never commit secrets.
- **D-07:** Do **not** deploy FastAPI to Cloud.ru app VM in Phase 1; document the deploy path only (PLAT-08).
- **D-08:** Seed 1–2 corporate test users manually in Supabase Auth dashboard; document in README (shared VM — avoid reckless automated seed).
- **D-09:** Keep mocks behind `VITE_USE_MOCKS` (default true for offline Playwright; false for live platform proof).
- **D-10:** Platform FE↔BE proof = authenticated `GET /me` (read) + `POST /me/ping` (mutation that persists or records server-side). Not voting or issue APIs.
- **D-11:** Login page talks to Supabase Auth **directly** from the SPA (`@supabase/supabase-js`); FastAPI does not proxy login.
- **D-12:** After login without `returnUrl`, redirect to current **issue** route (AUTH-02 product contract); issue content may still be mock/empty until Phase 2.
- **D-13:** Minimal FastAPI surface for Phase 1: `GET /health`, `GET /me`, `POST /me/ping` only.
- **D-14:** CORS via explicit allowlist from `API_CORS_ORIGINS` env (e.g. `http://localhost:5173`).
- **D-15:** SPA discovers API via `VITE_API_BASE_URL`.
- **D-16:** Structured JSON logs on stdout + `request_id` request/response correlation (no external ELK/Sentry required in Phase 1).

### Claude's Discretion
- Exact JWT validation library/helpers, `/me/ping` persistence shape (DB row vs server memory for proof), and OpenAPI packaging — planner/researcher may choose within Ports & Adapters + TDD.

### Deferred Ideas (OUT OF SCOPE)
- MFA / Sber SSO — post Phase 1
- httpOnly cookie session bridge — security hardening later
- FastAPI deploy on Cloud.ru app VM — after local foundation green
- Live issue/vote/admin APIs — Phases 2–5
- Full OpenAPI skeleton of all future routes — not Phase 1
- Automated Auth user seed scripts against shared VM — avoid until dedicated non-prod project
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PLAT-01 | Self-hosted Supabase up with schema/RLS | VM already live (`https://knowledge-db.ru`); migration `001_initial_schema.sql` applied; Phase 1 verifies connectivity, does not re-provision Docker Supabase |
| PLAT-02 | FastAPI exposes endpoints without critical errors | New `backend/.../interface/http/` + uvicorn; routes `/health`, `/me`, `/me/ping` |
| PLAT-03 | FE authenticated reads from server | SPA Bearer → `GET /me`; `VITE_USE_MOCKS=false` proof path |
| PLAT-04 | FE mutations persist | `POST /me/ping` → `activity_events` via service_role adapter |
| PLAT-05 | Secrets only in env | `.env` + `.env.example`; fix `.gitignore` so example is commitable |
| PLAT-06 | CORS allowlist | `CORSMiddleware` + `API_CORS_ORIGINS` |
| PLAT-07 | Network/validation UX + correlated logs | `ErrorPanel` + login inline; `structlog` + `request_id` middleware |
| PLAT-08 | Docs for local + Cloud.ru deploy path | README/runbook; no live deploy (D-07) |
| AUTH-01 | Corporate domain login; reject others | UI + FastAPI email claim + Auth dashboard/hook |
| AUTH-02 | Redirect issue / returnUrl | React Router `/login?returnUrl=` per error_handling.md |
| AUTH-03 | Auth gate on protected routes; 401→login | SPA guard + FastAPI JWT deps; admin 403 deferred until admin APIs exist |
</phase_requirements>

## Summary

Phase 1 wires a brownfield Ports & Adapters codebase that today has domain/use-cases and an in-memory composition root, but **no FastAPI HTTP layer**, **no Supabase SDK adapters**, and **no React login**. The remote self-hosted Supabase VM is already the system of record: schema/RLS from `supabase-integration/migrations/001_initial_schema.sql` is applied, and the project's gitignored `.env` already names `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, and `SUPABASE_JWKS_URL`.

A live probe of `SUPABASE_JWKS_URL` returned HTTP 200 with **one ES256 (EC) signing key**. That locks the FastAPI verification approach for this environment: verify access tokens locally against JWKS (PyJWT + cryptography), not shared-secret HS256 decode, and not a network hop to `/auth/v1/user` on every request (still useful as a fallback diagnostic). The SPA logs in with `@supabase/supabase-js` `signInWithPassword`, keeps the default persisted session, and sends `Authorization: Bearer <access_token>` to the local API.

**Primary recommendation:** Add thin FastAPI under `backend/src/backend/interface/http/`, JWKS-based JWT dependency, live composition wiring that constructs Supabase clients only in `composition/`, FE auth/API clients under `web/src/services/` behind `VITE_USE_MOCKS`, persist `/me/ping` as an `activity_events` row via `service_role`, and TDD every behavior before production code.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Email/password login | Browser / Client | Supabase Auth (remote) | D-11: SPA → Auth direct; FastAPI does not proxy login |
| Session persistence | Browser / Client | — | D-02: supabase-js default storage |
| Domain allowlist UX | Browser / Client | API / Backend | Inline on login; FastAPI re-checks JWT `email` claim (D-04) |
| JWT signature verify | API / Backend | Database / Storage (Auth JWKS) | FastAPI deps; JWKS from Auth endpoint |
| `GET /me` identity DTO | API / Backend | Database / Storage | Claims (+ optional `profiles` read) |
| `POST /me/ping` persist | API / Backend | Database / Storage | Use-case + port; adapter writes `activity_events` |
| `GET /health` liveness | API / Backend | — | No auth; ops probe |
| CORS policy | API / Backend | — | Explicit allowlist (D-14) |
| Structured logs + `request_id` | API / Backend | — | Middleware at HTTP edge (D-16) |
| Mock vs live FE data | Browser / Client | — | `VITE_USE_MOCKS` (D-09) |
| Schema/RLS ownership | Database / Storage | — | Already on VM; Phase 1 avoids reckless DDL on shared instance |
| Cloud.ru app deploy | CDN / Static + API (docs only) | — | Document only (D-07) |

## Project Constraints (from `.cursor/rules/`)

| Rule | Directive for planner/executor |
|------|--------------------------------|
| `architecture.mdc` | Ports & Adapters; no `fastapi`/`httpx`/`supabase` in domain/use-cases; wire only in `composition/`; FE calls only via `web/src/services/` |
| `tdd.mdc` / `AGENTS.md` | `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`; Red→Green→Refactor |
| `python-uv.mdc` | Add Python deps only with `uv add` / `uv sync` — never raw pip/poetry for project deps |
| `context7.mdc` | Prefer Context7 for library/API docs during implementation |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastapi` | 0.141.1 | HTTP API | Architecture target; thin routers |
| `uvicorn` | 0.53.0 | ASGI server | Standard FastAPI runner |
| `PyJWT` | 2.14.0 | JWT decode + `PyJWKClient` | Official JWT lib; FastAPI security tutorials use it |
| `cryptography` | 50.0.1 | ES256 verify support for PyJWT | Required for EC JWKS keys |
| `httpx` | 0.28.1 | JWKS fetch / optional Auth `/user` fallback; TestClient peer | FastAPI test stack |
| `supabase` (PyPI) | 2.31.0 | Server SDK for profile/ping adapters | Official Python client; pin in `supabase-integration` only |
| `@supabase/supabase-js` | 2.116.0 | SPA Auth client | Locked by D-01/D-11 |
| `structlog` | 26.1.0 | JSON logs + bound `request_id` | Lightweight stdout JSON without ELK |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-multipart` | 0.0.32 | FastAPI form parsing | If any form endpoints appear; safe to include with FastAPI |
| `pydantic` | 2.13.5 | Request/response DTOs at HTTP edge | Already used in `data-collection`; FastAPI dependency |
| `pytest` | ≥8.3.0 (workspace) | Unit/API tests | Existing `tests/unit` |
| `@playwright/test` | ^1.62.1 | Login/redirect/FE↔BE E2E | Existing root harness |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JWKS local verify (ES256) | `GET /auth/v1/user` every request | Official for HS256; slower; Auth region latency — use as fallback only |
| JWKS local verify | Local HS256 `JWT_SECRET` decode | Official docs strongly discourage; VM already serves ES256 JWKS |
| `structlog` | stdlib `logging` + JSON formatter | Works; more boilerplate for contextvars binding |
| `activity_events` ping | In-process memory list | Faster to green; weaker PLAT-04 “persists” proof across restarts |

**Installation (prescriptive):**

```bash
# from repo root — backend HTTP stack
uv add --package backend fastapi "uvicorn[standard]" pyjwt cryptography httpx structlog python-multipart

# adapters package
uv add --package supabase-integration supabase

# frontend Auth client
npm install --prefix web @supabase/supabase-js@2.116.0
```

**Version verification:** PyPI JSON API + `npm view @supabase/supabase-js version` on 2026-09-19. [VERIFIED: pypi.org/pypi/*/json] [VERIFIED: npm registry via npm view]

## Package Legitimacy Audit

> Seam `package-legitimacy check` returned **SUS** for all candidates (reasons: `unknown-downloads` / `too-new` / missing repo metadata on PyPI). None returned **SLOP**. Cross-checked against PyPI project pages + Context7 official IDs + GitHub.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| fastapi | PyPI | mature | n/a (seam) | github.com/fastapi/fastapi | SUS* | Approved — official; Context7 `/websites/fastapi_tiangolo` |
| uvicorn | PyPI | mature | n/a | github.com/Kludex/uvicorn | SUS* | Approved |
| pyjwt | PyPI | mature | n/a | github.com/jpadilla/pyjwt | SUS* | Approved — Context7 `/jpadilla/pyjwt` |
| cryptography | PyPI | mature | n/a | github.com/pyca/cryptography | — | Approved (required for ES256) |
| httpx | PyPI | mature | n/a | github.com/encode/httpx | — | Approved |
| supabase | PyPI | mature | n/a | github.com/supabase/supabase-py | SUS* | Approved — Context7 `/supabase/supabase-py` |
| structlog | PyPI | mature | n/a | github.com/hynek/structlog | SUS* | Approved |
| python-multipart | PyPI | mature | n/a | github.com/Kludex/python-multipart | SUS* | Approved |
| @supabase/supabase-js | npm | mature | ~19.7M/wk | github.com/supabase/supabase-js | SUS* (too-new) | Approved — no postinstall; Context7 `/supabase/supabase-js` |

\*Heuristic false positive from missing PyPI download stats / recent release timestamps — not slopsquat.

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** all above — planner should add a single `checkpoint:human-verify` before first `uv add` / `npm install` wave (confirm versions), not per-package deep review.

## Architecture Patterns

### System Architecture Diagram

```text
Browser (Vite :5173 / Playwright :5174)
  │
  ├─ LoginPage ──signInWithPassword──► Supabase Auth (knowledge-db.ru)
  │                                      │ issues ES256 access_token
  │                                      ▼
  │                                 localStorage session (supabase-js default)
  │
  ├─ AuthGuard (session?) ──no──► /login?returnUrl=
  │
  └─ meApi / other services
        Authorization: Bearer <access_token>
        VITE_API_BASE_URL
              │
              ▼
       FastAPI (local :8000)
         │ CORS allowlist (API_CORS_ORIGINS)
         │ request_id middleware → JSON logs
         │
         ├─ GET /health          (public)
         ├─ HTTPBearer + JWKS verify (SUPABASE_JWKS_URL)
         │     email domain gate (@sberbank.ru | @omega.sbrf.ru)
         ├─ GET /me              → CurrentUser DTO (claims ± profiles)
         └─ POST /me/ping        → PingRecorder port
                                      │
                                      ▼
                         supabase-integration adapter
                         (service_role client in composition only)
                                      │
                                      ▼
                         Postgres activity_events (+ profiles)
```

### Recommended Project Structure

```text
backend/src/backend/
├── domain/                    # existing — add AuthDomainError / AllowedEmail if needed
├── application/
│   ├── ports/
│   │   ├── profile_repository.py      # NEW Protocol
│   │   └── ping_recorder.py           # NEW Protocol
│   └── use_cases/
│       ├── get_current_user.py        # NEW
│       └── record_platform_ping.py    # NEW
├── interface/http/                    # NEW (missing today)
│   ├── app.py                         # create_app()
│   ├── deps.py                        # get_current_principal, container
│   ├── middleware.py                  # request_id + logging
│   └── routes/
│       ├── health.py
│       └── me.py
├── composition/
│   ├── container.py                   # extend AppContainer OR HttpAppContainer
│   ├── live.py                        # build_live_container() — NEW
│   └── settings.py                    # env parsing — NEW
└── tests_support/
    └── in_memory.py                   # add InMemory ping/profile fakes

supabase-integration/src/supabase_integration/
├── __init__.py                        # export adapters + migrations_dir
├── client.py                          # create_supabase_client helpers — NEW
├── profile_repository.py              # NEW
└── ping_recorder.py                   # NEW (activity_events insert)

web/src/
├── services/
│   ├── supabaseClient.js              # NEW — only place that imports @supabase/supabase-js
│   ├── authApi.js                     # NEW — signIn/signOut/getSession/getAccessToken
│   ├── meApi.js                       # NEW — GET /me, POST /me/ping
│   └── votingApi.js                   # keep mock path behind VITE_USE_MOCKS
├── pages/
│   └── LoginPage.jsx                  # NEW (port UX from design-frontend/pages/login.html)
├── components/
│   └── RequireAuth.jsx                # NEW
└── App.jsx                            # add /login + guard

.env.example                           # NEW (committed; fix gitignore)
docs/agents/ or README sections        # local run + Cloud.ru deploy path
```

### Pattern 1: JWKS JWT dependency (FastAPI)

**What:** Extract Bearer token, resolve signing key from remote JWKS, decode with audience/`role` checks, then enforce corporate email domains.  
**When to use:** Every protected route (`/me`, `/me/ping`).  
**Example:**

```python
# Source: https://supabase.com/docs/guides/auth/jwts + PyJWT PyJWKClient
# Live JWKS on this project: ES256, kid present [VERIFIED: GET knowledge-db.ru JWKS 200]

from jwt import PyJWKClient, decode, InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=True)
ALLOWED_DOMAINS = ("@sberbank.ru", "@omega.sbrf.ru")  # ADR-0003 / D-04

def verify_access_token(token: str, *, jwks_url: str, issuer: str) -> dict:
    client = PyJWKClient(jwks_url)  # cache internally; do not cache longer than ~10m across process restarts poorly
    key = client.get_signing_key_from_jwt(token)
    return decode(
        token,
        key.key,
        algorithms=["ES256"],  # match live JWKS alg
        audience="authenticated",
        issuer=issuer,  # e.g. https://knowledge-db.ru/auth/v1
        options={"require": ["exp", "sub", "role"]},
    )

async def get_principal(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    try:
        claims = verify_access_token(creds.credentials, jwks_url=..., issuer=...)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    email = (claims.get("email") or "").lower()
    if not email.endswith(ALLOWED_DOMAINS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="domain_not_allowed")
    if claims.get("role") != "authenticated":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_role")
    return claims
```

**Note:** JWT verification helpers may live in `backend/.../interface/http/deps.py` or `backend/.../infrastructure/auth_jwt.py` — **not** in `domain/` / `use_cases/`. Map failures to HTTP at the edge.

### Pattern 2: Composition live wiring

**What:** Keep `build_in_memory_container` for unit tests; add env-selected live builder that constructs Supabase clients and adapters.  
**When to use:** ASGI lifespan / `create_app()`.

```python
# Target shape — extend backend/src/backend/composition/container.py
# Existing today [VERIFIED: backend/src/backend/composition/container.py:17-57]:
# class AppContainer: materials, chunks; build_in_memory_container(...)

def build_live_container(settings: Settings) -> AppContainer:
    # create_client ONLY here — never in use_cases
    user_client = create_anon_or_publishable_client(settings)      # optional profile reads with user JWT
    admin_client = create_service_role_client(settings)            # ping insert bypasses RLS
    return AppContainer(
        materials=...,  # still in-memory OR stub — Phase 1 does not need material adapters
        chunks=...,
        profiles=SupabaseProfileRepository(admin_client),
        pings=SupabasePingRecorder(admin_client),
    )
```

### Pattern 3: FE Auth client behind services/

**What:** Pages never import `@supabase/supabase-js`; only `web/src/services/supabaseClient.js` does. Login uses `authApi.signIn`; API calls attach Bearer from `getSession().access_token`.  
**When to use:** All Auth + FastAPI traffic.

```javascript
// Source: https://supabase.com/docs — signInWithPassword + createClient defaults
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY,
  // persistSession: true is DEFAULT — honors D-02
)

export async function signIn(email, password) {
  return supabase.auth.signInWithPassword({ email, password })
}

export async function getAccessToken() {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}
```

```javascript
// meApi.js — pattern mirrors votingApi.js error class style
const base = import.meta.env.VITE_API_BASE_URL
export async function fetchMe(accessToken) {
  const res = await fetch(`${base}/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (res.status === 401) throw Object.assign(new Error('unauthorized'), { code: 'UNAUTHORIZED', retryable: false })
  if (!res.ok) throw Object.assign(new Error('network'), { code: 'NETWORK', retryable: true })
  return res.json()
}
```

### Pattern 4: `/me/ping` persistence

**Recommendation (discretion):** Persist to `activity_events` with `kind='platform_ping'` using **service_role** client.

Schema quote [VERIFIED: supabase-integration/migrations/001_initial_schema.sql:227-235]:

```sql
create table if not exists activity_events (
  id bigint generated always as identity primary key,
  user_id uuid references profiles (id) on delete set null,
  kind text not null,
  entity_type text,
  entity_id text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

RLS is enabled on `activity_events` but **no INSERT policy** exists for `authenticated` in the migration (policies stop at `profiles_select_own`). Therefore user-JWT inserts will fail; service_role in composition is correct and keeps the browser free of secret keys.

Ensure `profiles` row exists for the user (Auth trigger or upsert on first `/me`) so `user_id` FK is valid — if missing, insert ping with `user_id=null` is allowed by FK (`on delete set null` / nullable), but prefer upserting profile on first authenticated contact.

### Anti-Patterns to Avoid

- **Supabase SDK / httpx / FastAPI in `domain/` or `use_cases/`** — violates architecture.mdc.
- **`VITE_` / `PUBLIC_` prefix on secret or JWT signing material** — official JWTs guide warns this leaks HS256 secrets; never put `SUPABASE_SECRET_KEY` in Vite env.
- **Pages calling `createClient` or raw `fetch` to Supabase** — must go through `web/src/services/`.
- **Calling unit tests against live VM without an integration marker** — keep default `tests/unit` offline.
- **Automated mass user seed on shared VM** — deferred (D-08 / deferred ideas).
- **Expanding API surface beyond `/health|/me|/me/ping`** — locked D-13.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT crypto / JWKS cache | Custom ES256 verifier | PyJWT `PyJWKClient` | Key rotation, kid matching, timing bugs |
| Password auth | Custom password tables | Supabase Auth `signInWithPassword` | Session refresh, hashing, audit |
| CORS | Manual OPTIONS handlers | FastAPI `CORSMiddleware` | Preflight edge cases |
| JSON request logs | print() ad hoc | `structlog` processors | Correlation + stable fields |
| HTTP Bearer parsing | Split header strings | `HTTPBearer` | Spec-compliant 401s |
| FE session storage | Custom cookie/localStorage protocol | supabase-js defaults | Refresh + multi-tab |

**Key insight:** Auth and JWT verification look “simple” until key rotation, audience/issuer mismatches, and CORS+credentials interact — libraries exist because the failure modes are expensive.

## Common Pitfalls

### Pitfall 1: HS256 local secret verify on an ES256 project
**What goes wrong:** `jwt.decode(..., algorithms=["HS256"], key=JWT_SECRET)` fails or is insecure.  
**Why:** Live JWKS is ES256 [VERIFIED: JWKS probe alg=ES256]. Official docs recommend Auth `/user` for shared-secret projects and JWKS for asymmetric.  
**How to avoid:** Decode with `algorithms=["ES256"]` and `PyJWKClient(SUPABASE_JWKS_URL)`.  
**Warning signs:** `InvalidSignatureError` / empty JWKS `keys: []`.

### Pitfall 2: `.env.example` ignored by git
**What goes wrong:** Example env never commits → onboarding fails PLAT-05/08.  
**Why:** `.gitignore` has `.env.*` which matches `.env.example` [VERIFIED: `git check-ignore -v .env.example` → `.gitignore:2:.env.*`].  
**How to avoid:** Add `!.env.example` (and optionally `!.env*.example`) under the `.env.*` rule.

### Pitfall 3: Playwright ports vs CORS allowlist
**What goes wrong:** Dev works on `:5173` but E2E on `:5174` is blocked.  
**Why:** `web/vite.config.js` uses port 5173; Playwright boots 5174 [VERIFIED: playwright.config.js webServer port 5174].  
**How to avoid:** `API_CORS_ORIGINS` includes both `http://127.0.0.1:5173` and `http://127.0.0.1:5174` (and `localhost` variants if used).

### Pitfall 4: `activity_events` insert with user JWT
**What goes wrong:** Ping “succeeds” in UI but DB write returns 0 / RLS denial.  
**Why:** No INSERT policy for `activity_events`.  
**How to avoid:** Service_role adapter in composition; never expose secret key to SPA.

### Pitfall 5: Breaking offline Playwright by defaulting mocks off
**What goes wrong:** CI/local `npm run test:web` needs network Auth.  
**Why:** D-09 defaults `VITE_USE_MOCKS=true` for offline Playwright.  
**How to avoid:** Keep default true; document live proof with env override; add separate Playwright project/spec for live only when credentials exist.

### Pitfall 6: Audience / issuer mismatch
**What goes wrong:** Valid tokens rejected after login.  
**Why:** Self-hosted `iss` is `https://knowledge-db.ru/auth/v1` (not `*.supabase.co`); `aud` is typically `authenticated`.  
**How to avoid:** Configure `SUPABASE_JWT_ISSUER` from env; assert in a unit test with a fixture token minted for tests (not production secret).

### Pitfall 7: Shared VM damage
**What goes wrong:** Destructive seed/migrate scripts wipe colleague data.  
**Why:** Single remote Supabase for the team.  
**How to avoid:** Manual 1–2 users (D-08); no DROP; no automated Auth seed; integration tests opt-in.

### Pitfall 8: Putting business rules in routers or React
**What goes wrong:** Domain checks drift.  
**Why:** Architecture anti-pattern.  
**How to avoid:** Domain email policy helper or use-case; routers only map HTTP↔DTO.

## Code Examples

### FastAPI CORS allowlist

```python
# Source: https://fastapi.tiangolo.com/tutorial/cors/
from fastapi.middleware.cors import CORSMiddleware

origins = [o.strip() for o in settings.api_cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
```

### request_id middleware (sketch)

```python
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger()

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        log.info("request_finished", method=request.method, path=request.url.path, status=response.status_code)
        return response
```

### Env shape (names only)

```bash
# .env.example — commit this; never commit .env values
SUPABASE_URL=https://knowledge-db.ru
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
SUPABASE_JWKS_URL=https://knowledge-db.ru/auth/v1/.well-known/jwks.json
SUPABASE_JWT_ISSUER=https://knowledge-db.ru/auth/v1
API_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5174
ALLOWED_EMAIL_DOMAINS=@sberbank.ru,@omega.sbrf.ru
# Vite (publishable only)
VITE_SUPABASE_URL=https://knowledge-db.ru
VITE_SUPABASE_PUBLISHABLE_KEY=
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_USE_MOCKS=true
```

Existing local `.env` **key names** already present (values not recorded): `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWKS_URL`, `MASKMCP_MASTER_KEY`. [VERIFIED: env key names via PowerShell name-only scan]

### Profiles table (for `/me`)

[VERIFIED: supabase-integration/migrations/001_initial_schema.sql:39-45]:

```sql
create table if not exists profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  role app_role not null default 'employee',
  display_name text,
  created_at timestamptz not null default now()
);
```

`app_role` enum: `'employee' | 'analyst' | 'ds' | 'admin'` [VERIFIED: lines 9-10].

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Shared JWT secret (HS256) for all tokens | Asymmetric signing keys + JWKS (ES256/RS256) | Supabase JWT Signing Keys rollout; self-host docs add `JWT_JWKS` | Prefer JWKS verify; avoid shipping JWT_SECRET to app fleets |
| Verify via dashboard JWT secret in app | Official: Auth `/user` for HS256; JWKS for asymmetric | Documented in Auth JWTs guide | Matches this VM (ES256 JWKS live) |
| Proxy login through API | SPA → Auth direct | Product decision D-11 | FastAPI only validates tokens |

**Deprecated/outdated:**
- Local HS256 verification with project JWT secret as the primary path — discouraged by Supabase for security/compliance; use only if JWKS empty and Auth `/user` is the verifier.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `aud` claim is exactly `"authenticated"` on user access tokens for this self-host | JWT pattern | Tokens rejected until audience config adjusted — confirm with one real token decode in Wave 0 |
| A2 | `iss` equals `https://knowledge-db.ru/auth/v1` | JWT pattern | Same — make issuer env-configurable |
| A3 | Supabase Auth dashboard/hook can enforce email domains without code deploy | AUTH-01 | If hooks unavailable on self-host build, rely on UI+API only until hook configured |
| A4 | First authenticated `/me` can upsert `profiles` via service_role without new migration | `/me` | FK failures on ping if profile missing and null user_id undesired |
| A5 | `structlog` JSON on stdout satisfies PLAT-07 correlation without ELK | Logging | Ops may want extra fields later — fine for Phase 1 |

## Open Questions (RESOLVED)

1. **Auth Hook availability on self-hosted GoTrue build**
   - What we know: D-04 wants Auth config/hooks + UI + API.
   - What's unclear: Whether this VM’s Auth image supports signup email domain allowlist / Hook without upgrade.
   - Recommendation: Ship UI+API gates first; document manual Auth setting; treat hook as hardening checkpoint.
   - **RESOLVED:** Phase 1 ships UI + FastAPI email-claim gates as the required AUTH-01 path (Plans 02 + 05). Auth dashboard/hook is optional hardening only — Plan 04 seed checkpoint documents enabling it if available; Phase 1 success does **not** depend on GoTrue hook presence (aligns with Assumption A3 fallback).

2. **Profile creation trigger**
   - What we know: `profiles` FK to `auth.users`; select-own RLS exists.
   - What's unclear: Whether a DB trigger already creates profiles on signup.
   - Recommendation: Wave 0 MCP/SQL check; if absent, upsert in `get_current_user` use-case via port.
   - **RESOLVED:** Always upsert via `ProfileRepository.get_or_upsert` on authenticated `GET /me` (Plans 02–04). Plan 04 task precondition: MCP/SQL check for an existing `auth.users` → `profiles` trigger; if present, upsert stays an idempotent safety net. No new migration required for Phase 1.

3. **Live Playwright credentials in CI**
   - What we know: Shared VM; no CI workflows yet.
   - What's unclear: Where test user secrets will live for optional live E2E.
   - Recommendation: Keep live FE↔BE as manual/documented proof + optional local Playwright project; do not block Phase 1 on CI secrets.
   - **RESOLVED:** Default `VITE_USE_MOCKS=true` offline Playwright remains the CI/local automated gate (Plan 05). Live FE↔BE proof is Plan 06 human-verify + local runbook only; optional local Playwright live project may be added later when credentials exist — **do not** block Phase 1 on CI secrets.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Backend | ✓ | 3.14.0 | — |
| uv | Deps | ✓ | 0.10.9 | — |
| Node/npm | Vite/Playwright | ✓ | Node 22.13.0 / npm 11.18.0 | — |
| Remote Supabase URL | Auth+DB | ✓ | knowledge-db.ru | None — Phase 1 requires it (D-05) |
| JWKS endpoint | JWT verify | ✓ | ES256, 1 key | Auth `/user` verify fallback |
| Local Docker Supabase | — | n/a | — | Explicitly **not** required (D-05) |
| `.env.example` | PLAT-05 | ✗ | — | Create + fix gitignore |
| FastAPI tree | PLAT-02 | ✗ | — | Create under `interface/http/` |
| Cloud.ru app VM deploy | PLAT-08 | docs only | — | Document path; no deploy (D-07) |

**Missing dependencies with no fallback:**
- Reachable remote Supabase (already available in this environment)

**Missing dependencies with fallback:**
- Auth domain hook → UI+API enforcement
- Live E2E credentials → manual proof + mock-default Playwright

## Validation Architecture

> `.planning/config.json` absent → treat `nyquist_validation` as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥8.3.0; Playwright @playwright/test ^1.62.1 |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| Quick run command | `uv run pytest tests/unit/test_<new>.py -x` |
| Full suite command | `npm run test:unit` && `npm run test:web` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLAT-02 | `/health` returns 200 | API unit (TestClient) | `uv run pytest tests/unit/test_http_health.py -x` | ❌ Wave 0 |
| PLAT-03 / AUTH-03 | `/me` 401 without token; 200 with valid claims | API unit | `uv run pytest tests/unit/test_http_me.py -x` | ❌ Wave 0 |
| AUTH-01 | Disallowed email claim → 403 | API unit | same | ❌ Wave 0 |
| PLAT-04 | `/me/ping` records via port (in-memory fake) | use-case unit | `uv run pytest tests/unit/test_record_platform_ping.py -x` | ❌ Wave 0 |
| PLAT-06 | CORS reflects allowlist origin | API unit | `uv run pytest tests/unit/test_cors.py -x` | ❌ Wave 0 |
| PLAT-07 | response includes `X-Request-ID`; log bind | API unit | `uv run pytest tests/unit/test_request_id.py -x` | ❌ Wave 0 |
| AUTH-02 | login redirect to `/` or returnUrl | Playwright | `npx playwright test --project=web tests/auth.spec.js` | ❌ Wave 0 |
| AUTH-01 UI | inline domain message; no session | Playwright | same | ❌ Wave 0 |
| PLAT-03/04 live | optional live proof | manual / marked integration | document in README | ❌ |
| PLAT-01 | schema contract still holds | unit contract | `uv run pytest tests/unit/test_schema_migration_contract.py` | ✅ |
| PLAT-05 | `.env.example` present; secrets not in git | doc/file assert or review | — | ❌ Wave 0 |
| PLAT-08 | README run + deploy path sections | manual review | — | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** focused pytest file(s) for the behavior
- **Per wave merge:** `npm run test:unit` (+ Playwright web if FE touched)
- **Phase gate:** full unit + web Playwright green; live `/me`+`/me/ping` proof documented

### Wave 0 Gaps

- [ ] `tests/unit/test_http_health.py` — PLAT-02
- [ ] `tests/unit/test_http_me.py` — AUTH-01/03, PLAT-03
- [ ] `tests/unit/test_record_platform_ping.py` — PLAT-04
- [ ] `tests/unit/test_cors.py` / `test_request_id.py` — PLAT-06/07
- [ ] `tests/unit/test_jwt_verify.py` — JWKS/ES256 with local test keys or mocked `PyJWKClient`
- [ ] In-memory fakes for new ports in `backend/src/backend/tests_support/in_memory.py`
- [ ] `tests/auth.spec.js` (or extend `web-app.spec.js`) — AUTH-01/02 with mocks
- [ ] `!.env.example` gitignore exception + file create
- [ ] `uv add` FastAPI stack to `backend`; `supabase` to `supabase-integration`
- [ ] Optional: `tests/integration/` marker excluded from default `testpaths`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Supabase Auth email/password; SPA session via supabase-js |
| V3 Session Management | yes | Short-lived JWT + auto refresh (client); no custom session store |
| V4 Access Control | yes | FastAPI JWT deps; RLS on DB; domain allowlist; admin 403 later |
| V5 Input Validation | yes | Pydantic DTOs; email domain checks; OpenAPI types |
| V6 Cryptography | yes | ES256 via PyJWT/cryptography — never hand-roll |

### Known Threat Patterns for Supabase Auth + FastAPI + Vite

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Stolen `service_role` in browser | Information Disclosure / Elevation | Never `VITE_` secret; only publishable key in SPA |
| JWT forgery | Spoofing | JWKS signature verify + `exp`/`aud`/`iss` |
| Disallowed corporate email session | Elevation | UI + API domain check + Auth config (D-04) |
| CORS `*` with credentials | Information Disclosure | Explicit `API_CORS_ORIGINS` allowlist |
| XSS → localStorage session theft | Spoofing | Editorial CSP later; Phase 1 accept D-02 risk; defer httpOnly |
| Shared VM data wipe | Tampering / DoS | Manual seed only; no destructive automation |
| Using `user_metadata` for authz | Elevation | Prefer `app_metadata` / `profiles.role` (Supabase skill checklist) |
| Logging secrets / tokens | Information Disclosure | Structured logs: request_id, path, status — never Authorization header |

## Sources

### Primary (HIGH confidence)

- Live JWKS probe `https://knowledge-db.ru/auth/v1/.well-known/jwks.json` — ES256, 1 key, HTTP 200
- Repo files read this session: `01-CONTEXT.md`, `ROADMAP.md`, `REQUIREMENTS.md`, `PROJECT.md`, codebase maps, `container.py`, `App.jsx`, `001_initial_schema.sql`, `.gitignore`, `playwright.config.js`, `web/vite.config.js`, ADRs 0003/0004
- Context7: `/websites/fastapi_tiangolo` (CORS, HTTPBearer), `/jpadilla/pyjwt` (decode/audience), `/supabase/supabase-js` (createClient defaults, getSession), `/websites/supabase` + WebFetch JWTs guide
- PyPI/npm version queries 2026-09-19

### Secondary (MEDIUM confidence)

- Supabase self-hosting auth keys doc (JWT_JWKS / backward compatible JWT_SECRET) via Tavily → supabase.com
- Design login UX: `design-frontend/pages/login.html` domain helper copy
- `docs/digest-cds/error_handling.md` 401→login?returnUrl=

### Tertiary (LOW confidence)

- Community FastAPI+Supabase blog posts (HS256 local decode) — superseded by official JWKS guidance for this VM

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified on registries; packages match locked decisions
- Architecture: HIGH — maps to existing Ports & Adapters + missing HTTP gap
- Pitfalls: HIGH — gitignore, CORS ports, ES256 JWKS, RLS on activity_events verified in-repo/live
- Auth hook on self-host: MEDIUM/LOW — needs Wave 0 confirmation (A3)

**Research date:** 2026-09-19  
**Valid until:** 2026-10-19 (JWT signing / supabase-js move quickly — re-check JWKS alg if Auth upgraded)

---

*Phase: 1 — Platform Foundation & Auth*  
*Researcher: gsd-phase-researcher*  
*Commit: skipped per orchestrator instruction*
