---
phase: 03-voting-cycle
plan: 02
subsystem: database
tags: [supabase, votes, migration, trigger, service-role, ballot-seed, tdd]

requires:
  - phase: 03-voting-cycle
    provides: VoteRepository Protocol, AppContainer.votes, get_ballot/cast_vote use-cases
  - phase: 02-issue-materials-archive
    provides: open voting_cycles row, materials seed, live composition pattern
provides:
  - migration 003 (votes_enforce_open_and_topic + topic seed + tally index)
  - SupabaseVoteRepository (list topics+counts, get_vote, CAS upsert)
  - live.py wires votes=SupabaseVoteRepository(admin_client)
  - shared VM seed+DDL applied (PostgREST seed + Studio SQL trigger)
affects: [03-04-ab-cas-closed, live ballot verification]

actuals:
  tokens: 8200
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Option-a: DB BEFORE INSERT OR UPDATE trigger + use-case closed check (defense in depth for service_role)"
    - "Idempotent topic seed via WHERE NOT EXISTS on name+cycle; ON CONFLICT DO NOTHING for topic_materials"
    - "Vote CAS: update … eq updated_at expected; 0 rows → conflict signal; insert when expected null"
    - "Shared VM apply: MCP PostgREST for DML when raw_sql lacks POSTGRES_URL; Studio SQL for DDL"

key-files:
  created:
    - supabase-integration/migrations/003_phase3_voting_ballot.sql
    - supabase-integration/src/supabase_integration/vote_repository.py
    - tests/unit/test_supabase_vote_repository_contract.py
  modified:
    - supabase-integration/src/supabase_integration/__init__.py
    - backend/src/backend/composition/live.py
    - tests/unit/test_live_container_wiring.py
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "Option-a locked: votes_enforce_open_and_topic trigger + use-case (not use-case-only)"
  - "Seed applied via MCP PostgREST insert (service_role); DDL via Studio SQL (CLI db push / raw_sql unavailable)"
  - "AutoML topic deliberately has zero topic_materials (VOTE-04)"

patterns-established:
  - "SupabaseVoteRepository injects client only via composition/live.py (service_role)"
  - "Runbook §4c records apply method after blocking human apply"
  - "materials_count from COUNT topic_materials — never invent cover tables"

requirements-completed: [VOTE-01, VOTE-03, VOTE-04]

coverage:
  - id: D1
    description: "Idempotent migration 003 seeds ≥3 topics with audit descriptions; AutoML has zero topic_materials (VOTE-04)"
    requirement: VOTE-04
    verification:
      - kind: other
        ref: "supabase MCP query topics cycle_id=1 + topic_materials counts (LLM=3, RAG=5, AutoML=0)"
        status: pass
      - kind: manual_procedural
        ref: "docs/agents/local-platform-runbook.md §4c Applied (2026-09-20)"
        status: pass
    human_judgment: false
  - id: D2
    description: "BEFORE INSERT OR UPDATE trigger votes_enforce_open_and_topic rejects closed-cycle / cross-cycle topic writes (option-a)"
    requirement: VOTE-03
    verification:
      - kind: manual_procedural
        ref: "Studio SQL DDL Success. No rows returned (function/trigger/index) — operator 2026-09-20"
        status: pass
      - kind: other
        ref: "supabase-integration/migrations/003_phase3_voting_ballot.sql#votes_enforce_open_and_topic"
        status: pass
    human_judgment: true
    rationale: "Trigger presence on shared Postgres cannot be asserted via PostgREST; Studio DDL success + migration source are the audit trail"
  - id: D3
    description: "build_live_container wires SupabaseVoteRepository via service_role admin_client; CAS/upsert contract tests green"
    requirement: VOTE-01
    verification:
      - kind: unit
        ref: "tests/unit/test_live_container_wiring.py#live container votes type"
        status: pass
      - kind: unit
        ref: "tests/unit/test_supabase_vote_repository_contract.py"
        status: pass
    human_judgment: false

duration: 45min
completed: 2026-09-20
status: complete
---

# Phase 03 Plan 02: Migration 003 + SupabaseVoteRepository Summary

**Option-a open-cycle vote trigger + idempotent topic seed (LLM/RAG/AutoML) and live SupabaseVoteRepository wiring via service_role**

## Performance

- **Duration:** ~45 min (includes blocking human apply across seed + Studio DDL)
- **Started:** 2026-09-20T15:00:00Z (approx — Task 2 wave)
- **Completed:** 2026-09-20T16:30:00Z
- **Tasks:** 3/3
- **Files modified:** 7 (+ SUMMARY/runbook close-out)

## Accomplishments

- Locked option-a: DB trigger `votes_enforce_open_and_topic` as last-line defense alongside use-case checks (service_role bypasses RLS).
- Landed migration `003_phase3_voting_ballot.sql` (idempotent seed, trigger/function, tally index) and `SupabaseVoteRepository` with offline contract tests.
- Wired `build_live_container` → `votes=SupabaseVoteRepository(admin_client)`.
- **[BLOCKING] apply confirmed on shared VM:** 3 topics on `cycle_id=1`; AutoML materials_count=0; Studio SQL DDL for trigger/index succeeded.

## Task Commits

1. **Task 1: Confirm trigger (option-a)** - decision (no code commit)
2. **Task 2: Migration 003 + SupabaseVoteRepository + live wiring** - `42cf0be` (test) → `23ed51e` (feat)
3. **Task 3: [BLOCKING] Apply to shared DB** - human-action (seed MCP PostgREST; DDL Studio SQL) + docs close-out

**Plan metadata:** `48e3735` (docs: complete plan)

_Note: TDD RED→GREEN for Task 2 (`42cf0be` then `23ed51e`)._

## Files Created/Modified

- `supabase-integration/migrations/003_phase3_voting_ballot.sql` — trigger + seed + index
- `supabase-integration/src/supabase_integration/vote_repository.py` — VoteRepository adapter
- `supabase-integration/src/supabase_integration/__init__.py` — export
- `backend/src/backend/composition/live.py` — live votes wiring
- `tests/unit/test_supabase_vote_repository_contract.py` — offline stubs
- `tests/unit/test_live_container_wiring.py` — asserts SupabaseVoteRepository
- `docs/agents/local-platform-runbook.md` — §4c apply + Applied line

## Decisions Made

- **Option-a** (trigger + use-case) over use-case-only — matches RESEARCH Pitfall 1–2.
- Apply path split: **DML seed via MCP PostgREST** (service_role); **DDL via Studio SQL** because `raw_sql` needs `POSTGRES_URL` and interactive `db push` was unavailable.
- AutoML kept at zero materials for VOTE-04 empty-state honesty.

## Deviations from Plan

### Auto-fixed Issues

None during close-out.

### Planned path variance (documented, not Rule 1–3)

**1. [Apply method] Split seed (MCP) vs DDL (Studio) instead of single `supabase db push`**
- **Found during:** Task 3
- **Issue:** CLI/`raw_sql` unavailable on shared VM path without token/`POSTGRES_URL`
- **Fix:** Operator applied seed via PostgREST insert earlier; Studio SQL for function/trigger/index; runbook Applied line records both
- **Files modified:** `docs/agents/local-platform-runbook.md`
- **Verification:** PostgREST topics+counts re-query 2026-09-20; Studio `Success. No rows returned`

---

**Total deviations:** 0 auto-fixed; 1 documented apply-path variance
**Impact on plan:** Goal achieved; live verification unblocked. No scope creep.

## Issues Encountered

- Blocking human-action checkpoint for shared DB apply (expected).
- Seed already present before DDL; re-seed skipped on resume (idempotent / already applied).

## User Setup Required

**Shared VM apply completed** for this plan. See [local-platform-runbook.md §4c](../../../docs/agents/local-platform-runbook.md) for re-apply notes. Ongoing env vars remain Phase 1: `SUPABASE_URL`, `SUPABASE_SECRET_KEY` (server only); optional `SUPABASE_ACCESS_TOKEN` for future CLI push.

## Live verification snapshot (2026-09-20)

| Topic id | Name | materials_count |
|----------|------|-----------------|
| 1 | LLM для анализа аудиторских данных | 3 |
| 2 | RAG в корпоративной среде | 5 |
| 3 | AutoML для прогнозирования рисков | 0 |

Trigger/index: Studio SQL confirmed applied (`votes_enforce_open_and_topic`, `votes_cycle_id_topic_id_idx`).

## Next Phase Readiness

- Live container can serve BallotSnapshot from Supabase topics/votes.
- Ready for plans that depend on live CAS/closed-cycle behavior (e.g. 03-04) and end-to-end live ballot checks.
- Do not re-apply seed/DDL unless intentionally refreshing shared VM.

## Self-Check: PASSED

- FOUND: `supabase-integration/migrations/003_phase3_voting_ballot.sql`
- FOUND: `supabase-integration/src/supabase_integration/vote_repository.py`
- FOUND: `42cf0be`, `23ed51e`
- FOUND: `.planning/phases/03-voting-cycle/03-02-SUMMARY.md`
- FOUND: runbook §4c Applied (2026-09-20)

---
*Phase: 03-voting-cycle*
*Completed: 2026-09-20*
