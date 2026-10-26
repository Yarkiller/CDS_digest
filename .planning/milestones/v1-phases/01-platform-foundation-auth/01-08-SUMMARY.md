---
phase: 01-platform-foundation-auth
plan: 08
subsystem: docs
tags: [coverage, context, runbook, g-01-3, signup, register, d-08]

requires:
  - phase: 01-platform-foundation-auth
    provides: Plan 01-07 SPA /register + slim /login; operator G-01-3 amend-D-08 decision
provides:
  - COVERAGE signUp INTEGRATE notes aligned with self-service primary path
  - CONTEXT D-08 amended for /register + Логин; dashboard seed optional fallback
  - local-platform-runbook live checklist for /login vs /register UX
affects:
  - Phase 1 UAT G-01-3 docs closure
  - Future ops onboarding (no Имя-on-login)

actuals:
  tokens: 2142
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - Docs amend gap-closure: planning artifacts + ops runbook stay in sync with SPA Auth UX

key-files:
  created: []
  modified:
    - .planning/phases/01-platform-foundation-auth/COVERAGE.md
    - .planning/phases/01-platform-foundation-auth/01-CONTEXT.md
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "D-08 primary path is self-service /register (publishable signUp + Логин); dashboard seed optional shared-VM fallback only"
  - "Login remains email+password; nickname collected at registration only"
  - "admin.* / service_role stay OPT-OUT forever in SPA"

patterns-established:
  - "Gap-closure docs plans: amend CONTEXT decision + COVERAGE reason + runbook checklist together"

requirements-completed: [AUTH-01, AUTH-02, PLAT-08]

coverage:
  - id: D1
    description: "COVERAGE lists supabase-js signUp as INTEGRATE with G-01-3 / amended D-08 reason"
    requirement: AUTH-02
    verification:
      - kind: other
        ref: "rg signUp COVERAGE.md | INTEGRATE"
        status: pass
    human_judgment: false
  - id: D2
    description: "CONTEXT D-08 documents self-service /register primary path; dashboard seed optional"
    requirement: AUTH-01
    verification:
      - kind: other
        ref: ".planning/phases/01-platform-foundation-auth/01-CONTEXT.md#D-08"
        status: pass
    human_judgment: false
  - id: D3
    description: "Runbook live proof uses /login email+password and /register with Логин (no Имя-on-login)"
    requirement: PLAT-08
    verification:
      - kind: other
        ref: "docs/agents/local-platform-runbook.md#5"
        status: pass
    human_judgment: false

duration: 2min
completed: 2026-09-19
status: complete
---

# Phase 01 Plan 08: G-01-3 Docs Amend Summary

**Planning and ops docs now match Plan 01-07 self-service registration: signUp INTEGRATE, amended D-08, runbook `/register` + «Логин».**

## Performance

- **Duration:** 2 min
- **Started:** 2026-09-19T22:30:07Z
- **Completed:** 2026-09-19T22:32:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Confirmed COVERAGE `signUp` row is **INTEGRATE**; Notes now describe self-service `/register` as primary Auth path with dashboard seed as optional fallback.
- Rewrote CONTEXT **D-08** under Auth decisions for G-01-3 (Логин at registration; email+password-only login).
- Updated `local-platform-runbook.md` live FE↔BE checklist: `/login` vs `/register` + «Логин»; removed Имя-on-login; kept `APP_CONTAINER=live` / `VITE_USE_MOCKS=false` and no automated shared-VM seed scripts.

## Task Commits

Each task was committed atomically:

1. **Task 1: Amend COVERAGE signUp + CONTEXT D-08** - `149719b` (docs)
2. **Task 2: Update local platform runbook for register UX** - `d5fe1ab` (docs)

**Plan metadata:** `517805c` (docs: complete plan)

## Files Created/Modified

- `.planning/phases/01-platform-foundation-auth/COVERAGE.md` — Notes aligned with amended D-08 / self-service primary path
- `.planning/phases/01-platform-foundation-auth/01-CONTEXT.md` — D-08 rewritten for `/register` + Логин
- `docs/agents/local-platform-runbook.md` — Auth users section + live proof checklist for register UX

## Decisions Made

- Primary Auth path remains publishable-client `signUp` on `/register`; dashboard seed is ops fallback only (T-01-08-02).
- `admin.*` Auth Admin API stays OPT-OUT in SPA (T-01-08-01).

## Deviations from Plan

None - plan executed exactly as written.

**Note:** COVERAGE `signUp` INTEGRATE row was already present from Plan 01-07; Task 1 amended Notes + CONTEXT D-08 to close the planning/docs gap.

## Threat Flags

None beyond plan threat model (docs-only; service_role / admin OPT-OUT restated).

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: `.planning/phases/01-platform-foundation-auth/COVERAGE.md`
- FOUND: `.planning/phases/01-platform-foundation-auth/01-CONTEXT.md`
- FOUND: `docs/agents/local-platform-runbook.md`
- FOUND: commit `149719b`
- FOUND: commit `d5fe1ab`
- Verify: `signUp` INTEGRATE in COVERAGE; runbook matches `/register` + Логин; no Имя-on-login in live checklist
