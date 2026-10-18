---
phase: 24
review: 24-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "§5e prescribes a 2s limit that the probe recorded stamping"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "24-CONTEXT.md still advertises RuntimeMaxSec= outside every gate"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "systemctl revert deletes persistent drop-ins too"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "24-VERIFICATION.md still states the unconditional 'not stamped' invariant, and its own instruction invites the limit that stamps"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "The §5e negative bans suppress the prohibition they encode, and item 5 lost its drop-in removal command"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Text contract still does not pin RuntimeDirectoryMode=0750 or the exact EnvironmentFile= path"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "Historical research records still prescribe the superseded mechanisms"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "The 'kill lands before stamp_last_run' qualification is itself unpinned"
open: 0
total: 8
recorded: 2026-10-18T17:38:50.460Z
---

# Phase 24: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 64812b7 |
| WR-02 | warning | fixed | 64812b7 |
| WR-03 | warning | fixed | 64812b7 |
| WR-04 | warning | fixed | 73c5eef |
| WR-05 | warning | fixed | 73c5eef |
| IN-01 | info | deferred | deferred by hand: the two tokens are intact in `deploy/systemd/digest-ingest.service` today, and pinning them belongs with the next unit change rather than a gap-closure plan — a positive pin now would still need the same one-line edit later |
| IN-02 | info | deferred | deferred by hand: `24-RESEARCH.md` is a historical research record, not an operative spec; rewriting its findings would falsify what the research concluded at the time. `24-UAT.md` carries the same defect history on purpose |
| IN-03 | info | fixed | 73c5eef |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently.
