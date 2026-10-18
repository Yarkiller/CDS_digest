---
phase: 01-platform-foundation-auth
plan: 06
subsystem: infra
tags: [docs, runbook, cloudru, plat-08, live-proof, d-05, d-07, d-08, d-10]

requires:
  - phase: 01-platform-foundation-auth
    provides: Live Supabase adapters (01-04); SPA Auth + meApi (01-05); FastAPI /me + /me/ping
provides:
  - docs/agents/local-platform-runbook.md (local Vite+API against remote Supabase + Auth seed + live checklist)
  - docs/agents/cloudru-app-deploy-path.md (future app VM path; Phase 1 does not deploy)
  - README links + npm run platform:runbook helper
affects:
  - Phase 1 verification / human UAT for ROADMAP success criteria 3–5
  - Later Cloud.ru app deploy plans

actuals:
  tokens: 4200
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - PLAT-08 docs split: local runbook vs Cloud.ru path-only
    - Auth seed steps live in runbook (D-08), not automated against shared VM
    - Vite loads env from web/; live proof uses web/.env.local + uv --env-file .env

key-files:
  created:
    - docs/agents/local-platform-runbook.md
    - docs/agents/cloudru-app-deploy-path.md
  modified:
    - README.md
    - package.json

key-decisions:
  - "Auth dashboard seed steps (1–2 corporate users) documented in runbook §4, deferred from 01-04"
  - "npm platform:runbook prints paths/commands only — no secret-bearing scripts"
  - "Human approved live FE↔BE proof 2026-09-19 (login + /me + /me/ping → activity_events)"
  - "Display name optional; email is acceptable shell identity"

patterns-established:
  - "Operator live proof checklist in docs/agents; CI not gated on live credentials (RESOLVED RESEARCH Q3)"

requirements-completed: [PLAT-03, PLAT-04, PLAT-08, AUTH-01]

coverage:
  - id: D1
    description: "Local platform runbook covers env, uv/uvicorn, Vite, Auth seed, live checklist"
    requirement: PLAT-08
    verification:
      - kind: other
        ref: "Test-Path docs/agents/local-platform-runbook.md; README link local-platform-runbook"
        status: pass
    human_judgment: false
  - id: D2
    description: "Cloud.ru deploy-path doc states Phase 1 does not deploy; linked from README"
    requirement: PLAT-08
    verification:
      - kind: other
        ref: "docs/agents/cloudru-app-deploy-path.md#Phase 1 does not deploy"
        status: pass
    human_judgment: false
  - id: D3
    description: "Live FE↔BE proof: corporate login → GET /me → POST /me/ping → activity_events"
    requirement: PLAT-03
    verification:
      - kind: human
        ref: "Operator approved 2026-09-19 after live checklist"
        status: pass
    human_judgment: true
    rationale: "Blocking-human checkpoint; operator confirmed login, ping, and activity_events row."

duration: ~follow-up after halt
completed: 2026-09-19
status: complete
---

# Phase 01 Plan 06: Local/Cloud.ru Docs + Live Proof Summary

**PLAT-08 runbooks shipped; live FE↔BE proof human-approved (login → /me → /me/ping → activity_events).**

## Performance

- **Tasks:** 3/3 (docs + human checkpoint)
- **Files modified:** runbooks, README, package.json; follow-up display_name + env wiring during live assist

## Accomplishments

- `docs/agents/local-platform-runbook.md` — D-05 local Vite+API vs remote Supabase; `--env-file`; `web/.env.local` for Vite
- `docs/agents/cloudru-app-deploy-path.md` — Phase 1 does not deploy (D-07)
- Human live proof **approved** 2026-09-19

## Task Commits

1. **Task 1:** `3b91b10` — local platform runbook
2. **Task 2:** `5818056` — Cloud.ru deploy path
3. **Task 3:** human `approved` — live FE↔BE proof

## User Setup

| Item | Status |
|------|--------|
| `.env` + `web/.env.local` live vars | Done (operator) |
| Auth users on knowledge-db.ru | Done |
| Live checklist | **Approved** |

## Next Phase Readiness

Phase 1 plans 01–06 complete. Ready for goal-backward verification (`01-VERIFICATION.md`), then Phase 2.

## Known gaps (non-blocking for Phase 1 gate)

- No UI «Выйти» yet (`signOut` exists in `authApi` only)
- Session in localStorage (D-02); TTL from GoTrue on VM

---
*Phase: 01-platform-foundation-auth*
*Completed: 2026-09-19*
