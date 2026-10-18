---
phase: 14
review: 14-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "`honest_factor_labels` fabricates labels for non-string structured entries"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Live `markReady` still rolls a persisted promote back on JSON parse failure"
  - id: WR-03
    severity: warning
    disposition: open
    title: "The PGRST201 regression test does not lock the FK hint name"
  - id: IN-01
    severity: info
    disposition: open
    title: "Batch-promote client/harness surface is now dead code"
  - id: IN-02
    severity: info
    disposition: open
    title: "`_filter_ready_relations` couples per-related lookup failures to the whole read"
  - id: IN-03
    severity: info
    disposition: open
    title: "`MarkReadyBatchRequest.material_ids` is unbounded"
  - id: IN-04
    severity: info
    disposition: open
    title: "Broad `except Exception` in batch promote masks defects without logging"
  - id: IN-05
    severity: info
    disposition: open
    title: "Mock `sendDigest` order validation is weaker than the backend"
  - id: IN-06
    severity: info
    disposition: open
    title: "Stale-refetch regression test relies on a fixed sleep (timing-dependent false-pass window)"
open: 9
total: 9
recorded: 2026-10-04T16:55:00Z
---

# Phase 14: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
