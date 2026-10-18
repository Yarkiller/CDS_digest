---
phase: 13-admin-material-email-preview-honesty
plan: 05
subsystem: database
tags: [adux-04, ban-list, migration, scrub, playwright, forbidden-chrome, d-20]

requires:
  - phase: 13-admin-material-email-preview-honesty
    provides: Email HTML renderer + ban unit asserts (Plan 13-02); admin email iframe honesty (Plan 13-04); send/mailer HTML parity (Plan 13-06)
provides:
  - "Idempotent migration 010_phase13_scrub_test_header.sql for materials ban-token scrub"
  - "Runbook §4g apply/verify for shared-VM Studio SQL (postgres)"
  - "web/src/utils/forbiddenChrome.js synced with Python FORBIDDEN_LOWER"
  - "Playwright admin material modal + email iframe ban-surface asserts"
  - "Shared-VM apply evidence (2026-10-03 Studio SQL; PostgREST probe empty)"
affects:
  - Phase 13 verify-work / ROADMAP success criterion 4
  - Phase 14+ admin preview honesty regressions

actuals:
  tokens: 5871
  tasks: 3
  commits: 4
plan_head_before: 4fadd7a59f1069beeb1bbfdb589d83b343df0102
plan_head_after: 59118845015184b43bbaf5e98c349559c6292090

tech-stack:
  added: []
  patterns:
    - "Ban helpers assert-only (D-17) — no runtime strip in renderers or AdminDigestPage"
    - "Closed three-token FORBIDDEN_LOWER kept identical Python↔JS via unit sync proof (D-18)"
    - "Shared-VM scrub is operator Studio SQL apply-after-sql with dated runbook Applied line (D-20)"

key-files:
  created:
    - supabase-integration/migrations/010_phase13_scrub_test_header.sql
    - web/src/utils/forbiddenChrome.js
  modified:
    - docs/agents/local-platform-runbook.md
    - tests/unit/test_email_render.py
    - tests/admin.spec.js
    - .planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md

key-decisions:
  - "D-20 apply-after-sql: ship 010 + runbook, then operator applies once on shared knowledge-db VM (not sql-only-defer-apply)"
  - "Runbook section numbered §4g (not plan-text §4f) because §4f already documents admin shortlist/send E2E"

patterns-established:
  - "Phase scrub migrations: checked-in SQL + runbook Applied evidence + optional PostgREST probe when remaining_ban_hits SELECT not pasted"
  - "Ban list lock note lives in 12-FIX-01-LOCK.md (D-18 closed triple)"

requirements-completed: [ADUX-04]

coverage:
  - id: D1
    description: "Migration 010 + runbook scrub section + JS ban mirror synced with Python FORBIDDEN_LOWER"
    requirement: ADUX-04
    verification:
      - kind: unit
        ref: "tests/unit/test_email_render.py#forbidden/chrome/sync"
        status: pass
    human_judgment: false
  - id: D2
    description: "Playwright admin material modal and email iframe assert absence of ban tokens"
    requirement: ADUX-04
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#forbidden|chrome|ban|preview honesty"
        status: pass
    human_judgment: false
  - id: D3
    description: "Shared-VM one-way scrub applied; live honesty / ROADMAP criterion 4 claimable"
    requirement: ADUX-04
    verification:
      - kind: manual_procedural
        ref: "docs/agents/local-platform-runbook.md§4g Applied 2026-10-03 + PostgREST title ilike %test-header% → []"
        status: pass
    human_judgment: true
    rationale: "D-20 requires operator apply evidence on shared VM; automation cannot authenticate Studio SQL as postgres"

duration: 45min
completed: 2026-10-03
status: complete
---

# Phase 13 Plan 05: Ban-list sync + test-header scrub Summary

**Synced Python↔JS ban helpers, idempotent migration 010 + runbook §4g, Playwright admin ban asserts, and shared-VM Studio SQL apply evidenced for ADUX-04 / D-20 live honesty.**

## Performance

- **Duration:** ~45 min (includes human-action Studio apply gate)
- **Started:** 2026-10-03T06:00:00Z
- **Completed:** 2026-10-03T10:20:00Z
- **Tasks:** 3 (+ decision + operator apply)
- **Files modified:** 6

## Accomplishments

- Closed ban tokens (`test-header`, `test_header`, `testheader`) synced Python↔JS with unit proof; FIX-01 lock documents the list (D-18)
- Checked-in `010_phase13_scrub_test_header.sql` + runbook apply/verify; no runtime strip (D-17)
- Playwright asserts material modal + email iframe surfaces stay ban-clean (D-19)
- Operator applied 010 via Studio SQL (postgres) on shared knowledge-db VM; PostgREST title probe empty — D-20 / criterion 4 live honesty claimable

## Task Commits

Each task was committed atomically:

1. **Task 1: Confirm one-way shared-VM scrub apply (D-20)** — decision `apply-after-sql` (no code commit; recorded in STATE / this SUMMARY)
2. **Task 2 RED: Python↔JS ban sync proof** — `301ea48` (test)
3. **Task 2 GREEN: Migration 010 + runbook §4g + JS ban mirror** — `fcc4fcb` (feat)
4. **Task 3: Playwright ban-surface asserts** — `3fca7f7` (test)
5. **Task 3b: Shared-VM apply evidence (runbook Applied)** — `5911884` (docs)

**Plan metadata:** (final docs commit after STATE/ROADMAP update)

## Files Created/Modified

- `supabase-integration/migrations/010_phase13_scrub_test_header.sql` — idempotent materials scrub SQL
- `docs/agents/local-platform-runbook.md` — §4g Phase 13 scrub + Applied 2026-10-03
- `web/src/utils/forbiddenChrome.js` — TS `FORBIDDEN_LOWER` + `containsForbiddenChrome`
- `tests/unit/test_email_render.py` — Python↔JS sync proof
- `tests/admin.spec.js` — admin preview ban-surface asserts
- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` — D-18 ban list note

## Decisions Made

- **apply-after-sql** (recommended): ship SQL + runbook, then operator applies 010 once on shared VM so ROADMAP success criterion 4 and D-20 live DoD complete in this phase — not `sql-only-defer-apply`.
- Runbook landed as **§4g** because **§4f** already covers admin shortlist/send E2E (plan text said §4f).

## Shared-VM apply evidence (D-20)

| Field | Value |
|-------|-------|
| Decision | `apply-after-sql` |
| Method | Studio SQL Editor (postgres role) |
| File | `010_phase13_scrub_test_header.sql` |
| Date | 2026-10-03 |
| Operator signal | «готово» / done |
| Post-apply probe | Supabase MCP PostgREST: materials `title ilike %test-header%` → `[]` |
| Note | Full `remaining_ban_hits` SELECT not pasted; accepted per prior-phase pattern (operator confirm + empty probe) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Runbook section §4g instead of plan-named §4f**
- **Found during:** Task 2 (Migration 010 + runbook)
- **Issue:** Plan/objective text said `## 4f`, but `## 4f` already documents admin shortlist/send E2E; colliding would break runbook navigation and prior-phase refs.
- **Fix:** Added `## 4g. Phase 13 test-header scrub (ADUX-04)` with the same apply/verify contract the plan required under §4f.
- **Files modified:** `docs/agents/local-platform-runbook.md`
- **Verification:** `rg` finds `4g.` + `010_phase13_scrub_test_header`; Applied line dated after operator gate
- **Committed in:** `fcc4fcb` (Task 2); Applied update `5911884`

---

**Total deviations:** 1 auto-fixed (missing critical / correctness of docs structure)
**Impact on plan:** Naming only — contract (SQL path, Studio steps, verify SELECT, Applied evidence) delivered as specified.

## Issues Encountered

- Shared-VM apply required human-action gate (Studio SQL as postgres); CLI/`raw_sql` unavailable without `POSTGRES_URL` — expected; operator completed 2026-10-03.

## Auth Gates

- Task 3b human-action: operator applied migration via Studio SQL. Outcome: confirmed; Applied line updated; live DoD claimable.

## User Setup Required

None remaining — shared-VM apply completed. Historical steps remain in runbook §4g for re-verify.

## Next Phase Readiness

- ADUX-04 / D-20 complete for Phase 13 Wave 4
- Phase 13 plans 01–06 all have SUMMARYs — ready for phase verify / milestone continuation into Phase 14

## Self-Check: PASSED

- FOUND: `supabase-integration/migrations/010_phase13_scrub_test_header.sql`
- FOUND: `web/src/utils/forbiddenChrome.js`
- FOUND: `docs/agents/local-platform-runbook.md` (§4g Applied dated 2026-10-03)
- FOUND: commit `301ea48`
- FOUND: commit `fcc4fcb`
- FOUND: commit `3fca7f7`
- FOUND: commit `5911884`

---
*Phase: 13-admin-material-email-preview-honesty*
*Completed: 2026-10-03*
