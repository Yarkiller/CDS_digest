---
phase: 24
review: 24-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Падение advance_cursor роняет весь batch без graded exit"
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
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "Fallback ответа PATCH обнуляет last_run_at в DTO"
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
total: 10
recorded: 2026-10-18T17:38:50.460Z
---

# Phase 24: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | Fixed in `cfe45b7` (tests `364a8e6`): cursor write wrapped in try/except; `videos_failed += 1`, `cursor advance failed` diagnostic, batch continues, exit 1. (not in the current review) |
| WR-01 | warning | fixed | 64812b7 |
| WR-02 | warning | fixed | 64812b7 |
| WR-03 | warning | fixed | 64812b7 |
| WR-04 | warning | fixed | 73c5eef |
| WR-05 | warning | fixed | 73c5eef |
| WR-06 | warning | fixed | Fixed in `744e17b` (tests `86a44af`): empty upsert representation triggers follow-up read; missing row raises `PersistenceError`. (not in the current review) |
| IN-01 | info | deferred | deferred by hand: the two tokens are intact in `deploy/systemd/digest-ingest.service` today, and pinning them belongs with the next unit change rather than a gap-closure plan |
| IN-02 | info | deferred | deferred by hand: `24-RESEARCH.md` is a historical research record, not an operative spec; rewriting its findings would falsify what the research concluded at the time. `24-UAT.md` carries the same defect history on purpose |
| IN-03 | info | fixed | 73c5eef |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently.

## Decisions dropped by id reuse

The gap-closure review (24-07 / 24-08) renumbered its findings from `WR-01`/`IN-01`, so eight ids now name different findings and only one row per id can exist. The superseded decisions are preserved here rather than deleted silently:

| Id | Prior disposition | Prior source |
|----|-------------------|--------------|
| WR-01 | skipped | Upheld D-09: failed video is skipped, visible in stderr + failed counter, manual retry via `ingest <id>` (D-13). Reversal explicitly declined by operator 2026-10-18. |
| WR-02 | fixed | `cfe45b7` (tests `364a8e6`): unexpected `list_recent` exceptions degrade to `sources_unreadable` + diagnostic. |
| WR-03 | fixed | `d6e44ec` (test `050157e`): `stamp_last_run` skipped when `len(enabled) == 0` (D-27). |
| WR-04 | fixed | `3240732` (tests `bf8b2fe`): alert unit runs as `digestcds` with `NoNewPrivileges`/`PrivateTmp`. |
| WR-05 | fixed | `0ebb64b` (tests `ac9892f`): empty time blur restores `schedule.time_of_day`, no PATCH. |
| IN-01 | deferred | Diagnostics polish — `missing_video_id` mixes absent and invalid ids. |
| IN-02 | deferred | Minor duplication in CLI composition (`Settings.from_env()` twice). |
| IN-03 | deferred | Documented limitation of the ING-07 AST guard (dynamic imports). |
