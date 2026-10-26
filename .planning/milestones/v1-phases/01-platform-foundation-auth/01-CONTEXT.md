# Phase 1: Platform Foundation & Auth - Context

**Gathered:** 2026-09-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a working secured foundation: local Vite + local FastAPI against the existing remote self-hosted Supabase VM; corporate email/password auth (Supabase Auth); JWT-protected minimal API (`/health`, `/me`, `/me/ping`); FE can prove live read+mutation via `/me` + `/me/ping` with mocks switchable by env; CORS allowlist; secrets in `.env`; structured logs with `request_id`; docs for local run + future Cloud.ru app deploy. Editorial issue/vote/admin features stay in later phases (issue page may remain mock after login redirect).

</domain>

<decisions>
## Implementation Decisions

### Auth & session
- **D-01:** Use Supabase Auth for login; FastAPI validates JWT on API routes (middleware/deps). — **Reversibility:** costly — switching away from Supabase Auth later rewrites SPA auth client and API verification.
- **D-02:** Client session via Supabase JS default storage (localStorage/sessionStorage). — **Reversibility:** costly — moving to httpOnly cookies needs cookie bridge and CSP/CORS revisits.
- **D-03:** Phase 1 auth is email+password only; no MFA and no corporate SSO.
- **D-04:** Allowed domains `@sberbank.ru` / `@omega.sbrf.ru` enforced defense-in-depth: Supabase Auth config/hooks + UI inline message + FastAPI email claim check. — **Reversibility:** reversible for UI layer; Auth hook is more sticky.
- **D-08 (amended G-01-3):** Primary path is self-service registration on `/register` via publishable-client `signUp` (email + password + display nickname «Логин»). Login on `/login` stays email+password only — nickname is collected at registration, not on every sign-in. Optional manual Auth dashboard seed remains an ops fallback for shared-VM test users; do **not** add automated seed scripts against the shared VM (that idea stays deferred).
- **D-17 (G-01-3b):** Shared VM Auth uses **mailer autoconfirm** for Phase 1 so `/register` does not depend on SMTP. SMTP remains an **ops ticket outside Phase 1**; until mailer works, do not expose email-dependent product features (reset/invite/confirm). SPA must later map mailer failures to honest copy (deferred follow-up — not generic NETWORK).

### Runtime target first
- **D-05:** Day-1 runtime = local Vite + local FastAPI pointed at the **existing remote VM Supabase** (schema already applied; MCP available). Do not require a second local Docker Supabase for Phase 1 success.
- **D-06:** Secrets via gitignored `.env` + committed `.env.example` (SUPABASE_URL, keys, CORS, API URL). Never commit secrets.
- **D-07:** Do **not** deploy FastAPI to Cloud.ru app VM in Phase 1; document the deploy path only (PLAT-08).

### FE↔BE cutover
- **D-09:** Keep mocks behind `VITE_USE_MOCKS` (default true for offline Playwright; false for live platform proof).
- **D-10:** Platform FE↔BE proof = authenticated `GET /me` (read) + `POST /me/ping` (mutation that persists or records server-side). Not voting or issue APIs.
- **D-11:** Login page talks to Supabase Auth **directly** from the SPA (`@supabase/supabase-js`); FastAPI does not proxy login.
- **D-12:** After login without `returnUrl`, redirect to current **issue** route (AUTH-02 product contract); issue content may still be mock/empty until Phase 2.

### API surface & CORS
- **D-13:** Minimal FastAPI surface for Phase 1: `GET /health`, `GET /me`, `POST /me/ping` only.
- **D-14:** CORS via explicit allowlist from `API_CORS_ORIGINS` env (e.g. `http://localhost:5173`).
- **D-15:** SPA discovers API via `VITE_API_BASE_URL`.
- **D-16:** Structured JSON logs on stdout + `request_id` request/response correlation (no external ELK/Sentry required in Phase 1).

### Claude's Discretion
- Exact JWT validation library/helpers, `/me/ping` persistence shape (DB row vs server memory for proof), and OpenAPI packaging — planner/researcher may choose within Ports & Adapters + TDD.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, PLAT-*/AUTH-* mapping
- `.planning/REQUIREMENTS.md` — PLAT-01…08, AUTH-01…03
- `.planning/PROJECT.md` — success metric, constraints, locked ADR-0001
- `CONTEXT.md` — domain language (СВА, CDS, разрешённый домен, etc.)

### ADRs
- `docs/adr/0003-email-domain-restriction.md` — fixed corporate domains
- `docs/adr/0004-self-hosted-supabase-on-vm.md` — self-hosted Supabase (VM already running)
- `docs/adr/0001-public-leaderboard-gamification.md` — locked out of v1 (do not build)
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — stack contour (pipeline not Phase 1)

### Specs & UX contracts
- `docs/digest-cds/error_handling.md` — 401→login?returnUrl=, inline validation, banners/Retry
- `docs/digest-cds/acceptance_criteria.md` — US-01 / US-02 Given/When/Then
- `docs/digest-cds/technical_specification.md` — stack/NFR overview

### Architecture & brownfield map
- `.cursor/rules/architecture.mdc` — Ports & Adapters, composition root only
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor mandatory
- `.planning/codebase/ARCHITECTURE.md`, `STRUCTURE.md`, `CONCERNS.md`, `INTEGRATIONS.md`, `TESTING.md`

### Schema
- `supabase-integration/migrations/001_initial_schema.sql` — already applied on VM

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/.../composition/container.py` — extend with env-selected live container; keep in-memory for unit tests
- `backend/.../application/ports/` — wire adapters; do not put Supabase/FastAPI in domain
- `web/src/services/` — intended home for API clients (today voting is mock-oriented)
- `web/` login/issue routes — hook Auth + redirect; keep Editorial UI patterns

### Established Patterns
- TDD: failing test first (pytest for backend; Playwright for UI flows)
- Frontend must not embed business rules; DTOs from API
- Secrets never in source; `.env` already present (do not commit)

### Integration Points
- New FastAPI `interface/http/` under `backend/`
- Supabase adapters in `supabase-integration/` implementing ports
- SPA: Supabase Auth client + `Authorization: Bearer` to FastAPI
- Existing remote Supabase VM (URL/keys via `.env`)

</code_context>

<specifics>
## Specific Ideas

- Supabase on a **separate VM is already up**, schema created, MCP access works — treat as the primary DB/Auth for Phase 1 development.
- Local-first means **app processes local**, not “spin up another Supabase”.

</specifics>

<deferred>
## Deferred Ideas

- MFA / Sber SSO — post Phase 1
- httpOnly cookie session bridge — security hardening later
- FastAPI deploy on Cloud.ru app VM — after local foundation green
- Live issue/vote/admin APIs — Phases 2–5
- Full OpenAPI skeleton of all future routes — not Phase 1
- Automated Auth user seed scripts against shared VM — avoid until dedicated non-prod project

</deferred>

---

*Phase: 1-Platform Foundation & Auth*
*Context gathered: 2026-09-19*
