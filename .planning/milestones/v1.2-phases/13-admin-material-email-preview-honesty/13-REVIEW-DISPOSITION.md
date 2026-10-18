---
phase: 13
review: 13-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Empty slug produces a dead `/materials/` link in mail — and the mock hides it"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Material preview invents «~1 мин» when `reading_minutes` is missing"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Send unlocks even if the preview was closed before it rendered"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Post-publish mail/audit only tolerates `PersistenceError`"
  - id: IN-01
    severity: info
    disposition: open
    title: "Mock email HTML re-implements the backend renderer (drift risk)"
  - id: IN-02
    severity: info
    disposition: open
    title: "Mock `escapeHtml` omits apostrophe escaping"
  - id: IN-03
    severity: info
    disposition: open
    title: "`render_interstitial_html` does not handle CRLF line endings"
  - id: IN-04
    severity: info
    disposition: open
    title: "Numeric casts at the Supabase boundary can raise uncaught `ValueError`"
open: 8
total: 8
recorded: 2026-10-04T16:50:00Z
---

# Phase 13: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
