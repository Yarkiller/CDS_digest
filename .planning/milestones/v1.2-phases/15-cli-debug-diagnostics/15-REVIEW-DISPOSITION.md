---
phase: 15
review: 15-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Denylist cannot redact secret_key=/access_token=/client_secret= style credentials"
  - id: WR-01
    severity: warning
    disposition: open
    title: "Control characters are stripped after the token patterns, so a split credential leaks its tail"
  - id: WR-02
    severity: warning
    disposition: open
    title: "The exact-value registry wiring (_settings_secrets) is never tested end-to-end"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Several tests assert field presence rather than value/behavior"
  - id: IN-01
    severity: info
    disposition: open
    title: "key=value line format has no quoting, so an allowlisted string value can inject pseudo-fields"
  - id: IN-02
    severity: info
    disposition: open
    title: "StderrDiagnostics is constructed twice in cli.py"
  - id: IN-03
    severity: info
    disposition: open
    title: "MAX_VALUE_LENGTH caps the whole assembled line, not each value"
  - id: IN-04
    severity: info
    disposition: open
    title: "pattern is _CONTROL_CHARS is fragile identity coupling inside sanitize"
open: 8
total: 8
recorded: 2026-10-04T11:30:00.000Z
---

# Phase 15: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved.
