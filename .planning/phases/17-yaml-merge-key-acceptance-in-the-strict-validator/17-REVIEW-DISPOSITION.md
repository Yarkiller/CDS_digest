---
phase: 17
review: 17-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Duplicate keys inside a merge source are silently accepted"
  - id: WR-01
    severity: warning
    disposition: open
    title: "`_anchor_holder_keys` misses anchor holders referenced only by a nested merge"
  - id: IN-01
    severity: info
    disposition: open
    title: "`_anchor_holder_keys` over-matches alias copies of the merge-source node"
  - id: IN-02
    severity: info
    disposition: open
    title: "New test file fails `ruff check` (I001, ISC004)"
  - id: IN-03
    severity: info
    disposition: open
    title: "Wall-clock timing assertions make two tests load-sensitive"
open: 5
total: 5
recorded: 2026-10-14T12:24:55.530Z
---

# Phase 17: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
