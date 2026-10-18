---
phase: 16
review: 16-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: fixed
    title: "`_TOO_DEEP_MESSAGE` is English while every other hand-authored document-level message is Russian"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Deep-nesting tests pin a depth coupled to the interpreter recursion limit and duplicate message literals"
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Deep-nesting fix is incomplete — bare `yaml.YAMLError` (`ReaderError`) still escapes as HTTP 500"
  - id: WR-01
    severity: warning
    disposition: open
    title: "pydantic imported directly but not declared as a dependency"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Validator only catches MarkedYAMLError; deep documents escape as 500"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Length cap does not mitigate YAML alias expansion as the comment claims"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "window.confirm inside beforeunload is unreliable"
  - id: WR-05
    severity: warning
    disposition: deferred
    title: "Unsaved edits are lost on in-app (SPA) navigation"
  - id: IN-03
    severity: info
    disposition: open
    title: "Mocks default to ON, so the new service silently no-ops"
  - id: IN-04
    severity: info
    disposition: open
    title: "Migration relies solely on RLS; consider revoking default grants"
open: 4
total: 10
recorded: 2026-10-04T19:24:43.499Z
---

# Phase 16: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | fixed | 16-REVIEW-FIX.md |
| IN-02 | info | fixed | 16-REVIEW-FIX.md |
| CR-01 | critical | fixed | 16-REVIEW-FIX.md (not in the current review) |
| WR-01 | warning | open | - (not in the current review) |
| WR-02 | warning | fixed | fixed in commit 758ddac (catch RecursionError -> structured 400) (not in the current review) |
| WR-03 | warning | open | - (not in the current review) |
| WR-04 | warning | deferred | accepted known limitation; ROADMAP backlog 999.6 (not in the current review) |
| WR-05 | warning | deferred | accepted known limitation; ROADMAP backlog 999.6 (not in the current review) |
| IN-03 | info | open | - (not in the current review) |
| IN-04 | info | open | - (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
