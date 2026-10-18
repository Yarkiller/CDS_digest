# Phase 1: Platform Foundation & Auth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-19
**Phase:** 1-Platform Foundation & Auth
**Areas discussed:** Auth & session, Runtime target first, FE↔BE cutover, API surface & CORS

---

## Auth & session

| Option | Description | Selected |
|--------|-------------|----------|
| Supabase Auth + FastAPI JWT | SPA login via Supabase; API verifies JWT | ✓ |
| FastAPI owns login | Backend issues session; Supabase DB-only | |
| You decide | | |

**User's choice:** Supabase Auth + FastAPI JWT

| Option | Description | Selected |
|--------|-------------|----------|
| Supabase JS default storage | localStorage/session | ✓ |
| httpOnly cookie session | Safer XSS; more complex | |
| You decide | | |

**User's choice:** Supabase JS default storage

| Option | Description | Selected |
|--------|-------------|----------|
| Email+password only | No MFA/SSO in Phase 1 | ✓ |
| Optional MFA | | |
| Plan Sber SSO later | | |

**User's choice:** Email+password only

| Option | Description | Selected |
|--------|-------------|----------|
| Supabase + UI + FastAPI | Defense in depth | ✓ |
| UI + FastAPI only | | |
| Supabase only | | |

**User's choice:** Defense in depth

---

## Runtime target first

| Option | Description | Selected |
|--------|-------------|----------|
| Local-first | With nuance: remote VM Supabase already live | ✓ |
| Cloud.ru-first | | |
| Parity both | | |

**Notes:** User clarified Supabase already on separate VM with schema + MCP.

| Option | Description | Selected |
|--------|-------------|----------|
| Local app → remote VM Supabase | | ✓ |
| Local Docker Supabase | | |
| Hybrid | | |

**User's choice:** Local Vite/API → remote VM Supabase

| Option | Description | Selected |
|--------|-------------|----------|
| .env + .env.example | | ✓ |
| MaskMCP only | | |
| Both | | |

**User's choice:** .env + .env.example

| Option | Description | Selected |
|--------|-------------|----------|
| No FastAPI Cloud.ru deploy in Phase 1 | Docs only | ✓ |
| Minimal deploy | | |
| You decide | | |

**User's choice:** No app-VM deploy in Phase 1

| Option | Description | Selected |
|--------|-------------|----------|
| Manual test user seed | | ✓ |
| Scripted seed | | |
| You decide | | |

**User's choice:** Manual seed + README

---

## FE↔BE cutover

| Option | Description | Selected |
|--------|-------------|----------|
| VITE_USE_MOCKS flag | | ✓ |
| Hard cut | | |
| Per-service | | |

**User's choice:** Env flag

| Option | Description | Selected |
|--------|-------------|----------|
| GET issue + POST vote | Scope creep risk | |
| GET /me + POST /me/ping | Platform proof | ✓ |
| Auth health + logout | | |

**User's choice:** /me + /me/ping

| Option | Description | Selected |
|--------|-------------|----------|
| SPA → Supabase Auth direct | | ✓ |
| FastAPI auth proxy | | |
| You decide | | |

**User's choice:** Direct Supabase Auth from SPA

| Option | Description | Selected |
|--------|-------------|----------|
| Redirect to issue | May stay mock | ✓ |
| Temporary /platform page | | |
| Live empty issue stub API | | |

**User's choice:** Redirect to issue

---

## API surface & CORS

| Option | Description | Selected |
|--------|-------------|----------|
| /health + /me + /me/ping | | ✓ |
| + GET /issues/current stub | | |
| Full OpenAPI skeleton | | |

**User's choice:** Minimal three endpoints

| Option | Description | Selected |
|--------|-------------|----------|
| CORS allowlist from env | | ✓ |
| Reflect origin local | | |
| Vite proxy same-origin | | |

**User's choice:** Allowlist env

| Option | Description | Selected |
|--------|-------------|----------|
| VITE_API_BASE_URL | | ✓ |
| Relative /api + proxy | | |
| Hardcoded localhost | | |

**User's choice:** VITE_API_BASE_URL

| Option | Description | Selected |
|--------|-------------|----------|
| JSON logs + request_id | | ✓ |
| Simple logging | | |
| External sink | | |

**User's choice:** Structured JSON + request_id

---

*Phase: 1-Platform Foundation & Auth*
*Discussion log: 2026-09-19*
