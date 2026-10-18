---
phase: 12-admin-shortlist-empty-batch-contract
plan: 01
subsystem: api
tags: [fastapi, pytest, admin-shortlist, http-contract, tdd]

requires:
  - phase: 05-admin-digest-publish
    provides: AdminShortlistResponse + get_admin_shortlist empty/digest_rest paths
provides:
  - "Green FIX-01 HTTP proofs: no-batch null batch_id + empty-unsent batch_id=7"
  - "Required-key assert style for empty shortlist shapes (D-08)"
affects:
  - 12-02 (FIX-01 lock docs / REQUIREMENTS proof strings)
  - 12-03 (FE mock + Playwright empty-unsent)

actuals:
  tokens: 737
  tasks: 2
  commits: 2

plan_head_before: 72f8935ead5f7b3cca92fc7c71f05391ca8d1005
plan_head_after: 4e1e40d1d9d4df5bbf0b9fded7f47c7640f43764

tech-stack:
  added: []
  patterns:
    - "Required-key HTTP asserts for AdminShortlistResponse (not full-body dict equality)"
    - "Empty-unsent seed: ShortlistBatch(sent_at=None, items=()) via InMemoryShortlistRepository"

key-files:
  created: []
  modified:
    - tests/unit/test_http_admin.py

key-decisions:
  - "D-03: no production edits — empty-unsent already returned D-04 #2 via get_admin_shortlist"
  - "Both empty proofs use required-key asserts (D-08); AdminShortlistResponse keeps extra=forbid (D-09)"

patterns-established:
  - "FIX-01 proof pair names: test_admin_shortlist_no_batches_returns_null_batch_id + test_admin_shortlist_empty_unsent_batch_returns_batch_id"

requirements-completed: [FIX-01]

coverage:
  - id: D1
    description: "Empty-unsent GET /admin/shortlist returns HTTP 200 with batch_id int, ISO week_label, empty items, digest_rest false"
    requirement: FIX-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_shortlist_empty_unsent_batch_returns_batch_id"
        status: pass
    human_judgment: false
  - id: D2
    description: "No-batch GET /admin/shortlist returns HTTP 200 with null batch_id and empty items under required-key asserts"
    requirement: FIX-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_shortlist_no_batches_returns_null_batch_id"
        status: pass
    human_judgment: false

duration: 2min
completed: 2026-10-02
status: complete
---

# Phase 12 Plan 01: HTTP empty-batch contract Summary

**Locked both empty GET /admin/shortlist shapes via in-memory HTTP units (no-batch null batch_id vs empty-unsent batch_id) with required-key asserts; production untouched.**

## Performance

- **Duration:** 2min
- **Started:** 2026-10-02T16:07:00Z
- **Completed:** 2026-10-02T16:09:16Z
- **Tasks:** 2/2
- **Files modified:** 1

## Accomplishments

- Added `test_admin_shortlist_empty_unsent_batch_returns_batch_id` proving D-04 #2 (batch_id=7, week_label=`2026-10-06`, items=[], sent_at null, digest_rest false).
- Renamed no-batch proof to `test_admin_shortlist_no_batches_returns_null_batch_id` with D-04 #1 / D-08 required-key asserts.
- Confirmed production already satisfies both shapes (D-03) — no use-case/route edits; `AdminShortlistResponse` still `extra="forbid"` (D-09).

## Task Commits

1. **Task 1: End-to-end empty-unsent GET /admin/shortlist HTTP 200 contract** - `7b29da2` (test)
2. **Task 2: Rename no-batch proof to required-key asserts** - `4e1e40d` (test)

**Plan metadata:** `838b8b8` (SUMMARY) / `8d46661` (STATE/ROADMAP/REQUIREMENTS)

## TDD Cycle

### RED
- **Evidence:** `uv run pytest …::test_admin_shortlist_empty_unsent_batch_returns_batch_id` → exit 4, `ERROR: not found` (missing coverage before test existed).
- **Note:** Collection miss is INVALID_RED for authorizing production GREEN; used only to prove the coverage gap. Production path already correct — no GREEN production commit.

### GREEN
- Wrote empty-unsent HTTP unit with required-key asserts; 1 passed without production changes (verify+harden / D-03).

### REFACTOR
- None required beyond Task 2 rename + assert-style alignment.

## Files Created/Modified

- `tests/unit/test_http_admin.py` — empty-unsent proof + renamed no-batch proof with required-key asserts

## Decisions Made

- No production change: `get_admin_shortlist` already returns distinct no-batch vs empty-unsent shapes when seeded via `InMemoryShortlistRepository` (D-03).
- Kept in-memory-only FIX-01 proofs (D-07); auth still via `_seed_profile` + `_mint` / `require_admin` (T-12-02).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Full `tests/unit/test_http_admin.py -q`: **22 passed**. Per D-02, no deferred unrelated failures in this module.

## Threat Mitigations

| Threat | Disposition | Evidence |
|--------|-------------|---------|
| T-12-01 Information Disclosure | mitigate | `AdminShortlistResponse` still `ConfigDict(extra="forbid")`; tests assert declared keys only |
| T-12-02 Elevation of Privilege | mitigate | Empty-edge tests mint admin JWT; `Depends(require_admin)` untouched |
| T-12-03 Denial of Service | mitigate | Empty-unsent returns HTTP 200 (not schema 500) |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 12-02 can author `12-FIX-01-LOCK.md` and update REQUIREMENTS/ROADMAP/PROJECT proof strings to the D-05 names.
- 12-03 can mirror D-04 #2 in FE `__DIGEST_ADMIN_EMPTY_UNSENT__` + Playwright.

---
*Phase: 12-admin-shortlist-empty-batch-contract*
*Completed: 2026-10-02*

## Self-Check: PASSED

- FOUND: `.planning/phases/12-admin-shortlist-empty-batch-contract/12-01-SUMMARY.md`
- FOUND: commit `7b29da2`
- FOUND: commit `4e1e40d`
- FOUND: both proof tests green (2 passed)
