---
phase: 09
review: 09-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "RPC SQL tests still match comments, not executable statements"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Conflict path can return a sent batch"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "Migration 007 SQL tests match a comment, not the DDL"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "CAP-02 test never composes captions/article with persist"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Unlocked overflow can exceed p_batch_size and duplicate rank"
  - id: IN-01
    severity: info
    disposition: skipped
    title: "RPC does not enforce the closed RoleKind set"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Settings repr includes supabase_secret_key"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "Environ-access scan skips ingestion-service adapters"
open: 0
total: 8
recorded: 2026-09-27T17:20:00Z
---

# Phase 09: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 09-REVIEW-FIX.md |
| WR-02 | warning | fixed | 09-REVIEW-FIX.md |
| WR-03 | warning | fixed | prior wave + 09-REVIEW-FIX.md |
| WR-04 | warning | fixed | 09-REVIEW-FIX.md |
| WR-05 | warning | fixed | 09-REVIEW-FIX.md |
| IN-01 | info | skipped | decision A / by design (D-14a) |
| IN-02 | info | fixed | prior wave (`repr=False`) |
| IN-03 | info | deferred | low priority |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved.
