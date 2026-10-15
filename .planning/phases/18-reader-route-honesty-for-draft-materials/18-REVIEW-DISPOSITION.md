---
phase: 18
review: 18-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "A stale `redirectToReader` survives the D-12 redirect — the reader route (and every later material navigation) renders nothing"
  - id: WR-01
    severity: warning
    disposition: open
    title: "`forbidden` is never reset either — latent today, the same defect class as CR-01"
  - id: WR-02
    severity: warning
    disposition: open
    title: "The D-12 redirect test asserts only the URL, so it cannot detect CR-01"
  - id: IN-01
    severity: info
    disposition: open
    title: "`loadMaterial` is an unused prop — dead injection surface"
  - id: IN-02
    severity: info
    disposition: open
    title: "`no-store` is set only on the success path"
  - id: IN-03
    severity: info
    disposition: open
    title: "`_SLUG_PATTERN` is imported across route modules while its sibling helper is duplicated"
  - id: IN-04
    severity: info
    disposition: open
    title: "`mockSeatRole()` re-implements `meApi`'s role resolution"
  - id: IN-05
    severity: info
    disposition: open
    title: "An expired session on the preview endpoint is reported as a network failure"
open: 8
total: 8
recorded: 2026-10-15T12:06:00Z
---

# Phase 18: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
