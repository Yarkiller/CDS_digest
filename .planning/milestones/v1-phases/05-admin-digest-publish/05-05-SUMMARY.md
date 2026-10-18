---
phase: 05-admin-digest-publish
plan: 05
subsystem: database
tags: [supabase, shortlist, migration, service_role, stub-mailer, claim-rpc, tdd]

requires:
  - phase: 05-admin-digest-publish
    provides: ShortlistRepository ports + in-memory claim/send + admin HTTP (05-01..05-03)
  - phase: 02-current-issue-archive
    provides: digest materials seed + digest_issues tables
provides:
  - Migration 005 delivery columns + idempotent demo shortlist seed
  - SupabaseShortlistRepository + claim/publish path
  - live.py wires SupabaseShortlistRepository + StubMailer (service_role only)
  - Runbook §4e stub/seed/admin promote + operator apply confirmation
affects:
  - 05-06 live admin UAT / Playwright honesty
  - Phase verify-work against shared VM shortlist

actuals:
  tokens: 11200
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Idempotent migration 005: ADD COLUMN IF NOT EXISTS + WHERE NOT EXISTS seed"
    - "claim_and_publish_digest SECURITY INVOKER RPC granted to service_role only"
    - "live composition injects SupabaseShortlistRepository; StubMailer until SMTP opt-in"

key-files:
  created:
    - supabase-integration/migrations/005_phase5_admin_shortlist.sql
    - supabase-integration/src/supabase_integration/shortlist_repository.py
    - tests/unit/test_phase5_migration_005.py
    - tests/unit/test_supabase_shortlist_repository_contract.py
  modified:
    - docs/agents/local-platform-runbook.md
    - supabase-integration/src/supabase_integration/issue_repository.py
    - supabase-integration/src/supabase_integration/__init__.py
    - backend/src/backend/composition/live.py
    - tests/unit/test_live_container_wiring.py

key-decisions:
  - "Prefer claim_and_publish_digest RPC for atomic claim+publish; adapter falls back to ordered claim UPDATE"
  - "APP_CONTAINER=live keeps StubMailer; MAILER=smtp fail-fast at resolve_mailer (D-87)"
  - "Blocking apply: operator confirmed 005 applied on shared VM (method not specified)"

patterns-established:
  - "Pattern: Phase 5 delivery columns on digest_shortlist_batches (D-87)"
  - "Pattern: demo batch honesty only in SQL/runbook — UI silent on seed vs PIPE-01 (D-78)"
  - "Pattern: service_role client only in composition/live.py for shortlist mutations"

requirements-completed: [ADMIN-01, ADMIN-02, ADMIN-07, ADMIN-08]

coverage:
  - id: D1
    description: "Migration 005 adds delivery columns + idempotent demo batch ≤5 items with score_factors honesty"
    requirement: ADMIN-01
    verification:
      - kind: unit
        ref: "tests/unit/test_phase5_migration_005.py"
        status: pass
      - kind: other
        ref: "python -c assert delivery_status + demo batch in 005_phase5_admin_shortlist.sql"
        status: pass
    human_judgment: false
  - id: D2
    description: "SupabaseShortlistRepository + issue publish wired in live container with StubMailer"
    requirement: ADMIN-02
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_shortlist_repository_contract.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_live_container_wiring.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "Atomic claim path (RPC and/or sent_at IS NULL) for ADMIN-07 concurrency"
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_shortlist_repository_contract.py#claim"
        status: pass
    human_judgment: false
  - id: D4
    description: "Blocking schema/seed applied on shared VM before live-dependent verification"
    requirement: ADMIN-08
    verification: []
    human_judgment: true
    rationale: "Shared VM DDL/seed apply cannot be proven offline; operator resume signal required"

duration: continuation-closeout
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 05: Live Shortlist Adapters + Migration 005 Summary

**Idempotent migration 005 (delivery columns + demo shortlist seed) plus SupabaseShortlistRepository and StubMailer live wiring; operator confirmed schema applied on shared VM.**

## Performance

- **Duration:** continuation-closeout (Tasks 1–2 earlier session; Task 3 apply + SUMMARY close-out)
- **Started:** 2026-09-21T15:36:00Z (close-out)
- **Completed:** 2026-09-21T15:40:00Z
- **Tasks:** 3
- **Files modified:** 9 (+ SUMMARY/runbook apply note)

## Accomplishments

- Migration `005_phase5_admin_shortlist.sql`: nullable `delivery_status` / `recipient_count` / `published_issue_id` / `issue_url`, optional `claim_and_publish_digest` RPC (service_role only), idempotent demo batch «demo batch для Phase 5»
- `SupabaseShortlistRepository` + issue publish adapter; `build_live_container` wires shortlist + `StubMailer` (SMTP fail-fast)
- Runbook §4e documents stub mailer, seed vs PIPE-01 honesty, admin promote, apply-once
- **[BLOCKING] Apply signal:** operator replied **applied** for `005_phase5_admin_shortlist.sql` on shared VM — **operator confirmed applied (method not specified)**; item counts not logged in resume signal

## Task Commits

Each task was committed atomically:

1. **Task 1: Migration 005 delivery columns + demo seed + runbook §4e** - `6d617fc` (test), `a4133aa` (feat)
2. **Task 2: SupabaseShortlistRepository + issue publish + live.py wiring** - `49aacbb` (test), `c512101` (feat)
3. **Task 3: [BLOCKING] Apply Phase 5 migration** - human gate; operator signal `applied` (method not specified) — recorded in runbook §4e + this SUMMARY

**Plan metadata:** `93447bc` (docs: complete plan)

_Note: TDD tasks used RED→GREEN commits (test → feat)._

## Files Created/Modified

- `supabase-integration/migrations/005_phase5_admin_shortlist.sql` — delivery columns, claim RPC, demo seed
- `supabase-integration/src/supabase_integration/shortlist_repository.py` — live ShortlistRepository
- `supabase-integration/src/supabase_integration/issue_repository.py` — publish issue + items
- `backend/src/backend/composition/live.py` — SupabaseShortlistRepository + StubMailer
- `docs/agents/local-platform-runbook.md` — §4e + Applied confirmation line
- `tests/unit/test_supabase_shortlist_repository_contract.py` — offline contract tests
- `tests/unit/test_live_container_wiring.py` — live wiring assertions
- `tests/unit/test_phase5_migration_005.py` — migration file contract

## Decisions Made

- Prefer `claim_and_publish_digest` SECURITY INVOKER RPC when present; otherwise ordered claim UPDATE then inserts
- Live mailer stays StubMailer; `MAILER=smtp` rejected at composition (D-87 / COVERAGE SMTP opt-out)
- Blocking apply recorded as operator-confirmed without method detail (resume signal did not name MCP vs Studio vs CLI)

## Deviations from Plan

None - plan executed exactly as written (Tasks 1–2 committed earlier; Task 3 closed on operator `applied` signal).

## Issues Encountered

None during close-out. Verify suite: 15 passed (`test_supabase_shortlist_repository_contract` + `test_live_container_wiring`).

## Auth Gates

- **Task 3:** blocking-human schema apply on shared VM — operator replied `applied` (method not specified). No TRUNCATE performed per operator confirmation of apply-only path.

## User Setup Required

Shared VM prerequisites already documented in runbook §4e / plan `user_setup`:

- Apply `005_phase5_admin_shortlist.sql` once (done — operator confirmed)
- Optional: `update profiles set role='admin' where email=…` for live admin proof
- `SUPABASE_URL` + `SUPABASE_SECRET_KEY` for `APP_CONTAINER=live` (never `VITE_`)

## Next Phase Readiness

- Live shortlist/send path ready for 05-06 / phase verification against shared VM
- Promote at least one admin profile if not already done for live admin UAT

## Self-Check: PASSED

- FOUND: `.planning/phases/05-admin-digest-publish/05-05-SUMMARY.md`
- FOUND: commits `6d617fc`, `a4133aa`, `49aacbb`, `c512101`
- FOUND: runbook §4e Applied line updated

---
*Phase: 05-admin-digest-publish*
*Completed: 2026-09-21*
