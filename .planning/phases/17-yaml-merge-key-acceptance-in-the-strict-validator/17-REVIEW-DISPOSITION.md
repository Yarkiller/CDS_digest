---
phase: 17
review: 17-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Duplicate keys inside a merge source are silently accepted"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`_anchor_holder_keys` misses anchor holders referenced only by a nested merge"
  - id: IN-01
    severity: info
    disposition: skipped
    title: "`_anchor_holder_keys` over-matches alias copies of the merge-source node"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "New test file fails `ruff check` (I001, ISC004)"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "Wall-clock timing assertions make two tests load-sensitive"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "`_merge_source_ids` treats sequences as opaque, so a holder referenced only by a merge inside a list still misses the D-07 teaching message"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "`tests/unit/test_http_pipeline_config.py` still fails `ruff check` (I001, UP017)"
  - id: IN-05
    severity: info
    disposition: deferred
    title: "Duplicate *collection* keys are still not reported as duplicates (pre-existing, retained by the refactor)"
open: 0
total: 8
recorded: 2026-10-14T13:58:00.000Z
---

# Phase 17: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | 17-03 Task 1 + Task 2 — commits `04ac410`, `c7afe1b` |
| WR-01 | warning | fixed | 17-03 Task 3 — commit `9604645` |
| IN-01 | info | skipped | Accepted by design and pinned: the set is keyed on value-node identity, so an alias of a merge source is reported too; precise disambiguation needs composer-event data PyYAML discards. Pinned by `test_anchor_holder_keys_matches_alias_copies_by_identity_design` — commit `9604645` |
| IN-02 | info | fixed | 17-03 Task 3 — `ruff` clean on the merge test file, commit `9604645` |
| IN-03 | info | fixed | 17-03 Task 3 — both wall-clock ceilings raised to `5.0` s with the row-equality guard named as primary, commit `9604645` |
| WR-02 | warning | fixed | Re-review finding. `_merge_source_ids` now descends into `SequenceNode`s, so a holder referenced only by a merge inside a list (`items: [- <<: *c]`) gets the D-07 message; pinned by `test_anchor_holder_keys_reaches_a_merge_nested_under_a_sequence` — commit `e3cb84c` |
| IN-04 | info | fixed | Re-review finding (pre-existing debt, touched file). `ruff check --fix` on the HTTP test file (I001, UP017) — commit `5e68801`. Only the import block and one `datetime.UTC` call site changed; the D-09 tripwire body stays byte-identical |
| IN-05 | info | deferred | Deliberate: duplicate detection among **unhashable** key nodes is not attempted. Comparing collection keys needs an O(n²) equality scan over attacker-controlled collections — a new CPU-exhaustion path, exactly what PIPE-05 forbids. The document is already refused by PyYAML with exactly one structured row, and the 400 body now carries curated copy instead of its raw English text; the decision is pinned by `test_unhashable_duplicate_keys_are_rejected_with_curated_copy` — commit `e3cb84c` |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
