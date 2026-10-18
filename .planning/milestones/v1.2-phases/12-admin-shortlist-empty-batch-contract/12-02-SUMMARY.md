---
phase: 12-admin-shortlist-empty-batch-contract
plan: 02
subsystem: docs
tags: [fix-01, admin-shortlist, contract-lock, proof-strings]

requires:
  - phase: 12-admin-shortlist-empty-batch-contract
    provides: "Green FIX-01 HTTP proofs (12-01): test_admin_shortlist_no_batches_returns_null_batch_id + test_admin_shortlist_empty_unsent_batch_returns_batch_id"
provides:
  - "12-FIX-01-LOCK.md authoritative empty-shape tables (D-04/D-08/D-09/D-10)"
  - "REQUIREMENTS/ROADMAP/PROJECT cite both D-05 proof names"
affects:
  - 12-03 (FE mock + Playwright empty-unsent; lock as read_first)

actuals:
  tokens: 1762
  tasks: 2
  commits: 2

plan_head_before: 095bcb30ed869b367088d5ded0239098cb526f5d
plan_head_after: 8a40e0eefc4a00d11951304b903df9159d412282

tech-stack:
  added: []
  patterns:
    - "Phase contract-lock artifact with dual empty-shape tables + required-key assert rules"
    - "FIX-01 proof strings always cite both D-05 names (never sole pre-rename name)"

key-files:
  created:
    - .planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md
  modified:
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/PROJECT.md

key-decisions:
  - "D-10 lock tables mirror D-04 #1/#2; digest_rest called out as third non-empty shape (G-05-2)"
  - "REQUIREMENTS FIX-01 rephrased per RESEARCH Q2: no-batch + empty-unsent under required-key asserts"

patterns-established:
  - "Downstream executors/verifiers read 12-FIX-01-LOCK.md before empty shortlist changes"

requirements-completed: [FIX-01]

coverage:
  - id: D1
    description: "12-FIX-01-LOCK.md documents both D-04 empty shapes, D-08 required-key rules, D-09 extra=forbid, and both D-05 proof names"
    requirement: FIX-01
    verification:
      - kind: other
        ref: "rg -n test_admin_shortlist_no_batches_returns_null_batch_id|test_admin_shortlist_empty_unsent_batch_returns_batch_id|extra=.forbid|week_start.isoformat 12-FIX-01-LOCK.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "REQUIREMENTS/ROADMAP/PROJECT cite both D-05 proof names; old sole proof name cleared from active checklist"
    requirement: FIX-01
    verification:
      - kind: other
        ref: "rg -n both D-05 names in REQUIREMENTS.md ROADMAP.md PROJECT.md"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-02
status: complete
---

# Phase 12 Plan 02: Lock doc + proof-string updates Summary

**Authoritative `12-FIX-01-LOCK.md` empty-shape tables plus REQUIREMENTS/ROADMAP/PROJECT proof strings citing both 12-01 D-05 HTTP unit names.**

## Performance

- **Duration:** 5min
- **Started:** 2026-10-02T16:13:45Z
- **Completed:** 2026-10-02T16:18:30Z
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments

- Created `12-FIX-01-LOCK.md` with D-04 #1 (no-batch) and D-04 #2 (empty-unsent) field tables, D-08 required-key assert rules, D-09 `extra="forbid"`, D-05 proof names, and G-05-2 digest_rest distinction.
- Updated FIX-01 in REQUIREMENTS to “no-batch + empty-unsent HTTP contracts under required-key asserts” citing both proof names.
- Updated ROADMAP Phase 12 success criterion #1 to both D-05 names; kept criteria #2–#3.
- Aligned PROJECT.md target-features and Active checklist off the pre-rename sole proof name.

## Task Commits

1. **Task 1: Author 12-FIX-01-LOCK.md contract tables** - `d932652` (docs)
2. **Task 2: Update REQUIREMENTS ROADMAP PROJECT proof strings** - `8a40e0e` (docs)

**Plan metadata:** `7b3317a` (docs: complete plan)

## Files Created/Modified

- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` — authoritative FIX-01 empty-shape contract (D-10)
- `.planning/REQUIREMENTS.md` — FIX-01 proof-string rewrite (D-05 / RESEARCH Q2)
- `.planning/ROADMAP.md` — Phase 12 success #1 cites both D-05 names
- `.planning/PROJECT.md` — checklist/target features cite both D-05 names

## Decisions Made

- Lock doc forbids collapsed single empty shape; keeps null-vs-int `batch_id` distinction (D-04).
- Proof strings cite `test_admin_shortlist_no_batches_returns_null_batch_id` and `test_admin_shortlist_empty_unsent_batch_returns_batch_id` from 12-01 SUMMARY (D-05).
- Archived milestone SUMMARYs / Phase 10 deferred-items history left untouched.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Threat Mitigations

| Threat | Disposition | Evidence |
|--------|-------------|---------|
| T-12-04 Tampering (lock vs live tests) | mitigate | Lock tables mirror D-04/D-08; greps both 12-01 proof names |
| T-12-05 Repudiation (proof strings) | accept | Docs-only; archives left intact |
| T-12-SC Package installs | mitigate | No package installs |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 12-03: FE `__DIGEST_ADMIN_EMPTY_UNSENT__` + Playwright empty-unsent; lock doc is read_first authority.
- FIX-01 docs/lock complete; HTTP units green from 12-01.

---
*Phase: 12-admin-shortlist-empty-batch-contract*
*Completed: 2026-10-02*

## Self-Check: PASSED

- FOUND: `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md`
- FOUND: `.planning/phases/12-admin-shortlist-empty-batch-contract/12-02-SUMMARY.md`
- FOUND: commit `d932652`
- FOUND: commit `8a40e0e`
- FOUND: both D-05 proof names in LOCK + REQUIREMENTS + ROADMAP + PROJECT
