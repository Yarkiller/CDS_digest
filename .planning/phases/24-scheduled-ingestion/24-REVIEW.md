---
phase: 24-scheduled-ingestion
reviewed: 2026-10-18T17:45:00Z
depth: standard
scope: "gap closure 24-07 (G-24-3) + 24-08 (G-24-4), diff 97e3b2d..HEAD (78422c7)"
files_reviewed: 4
files_reviewed_list:
  - deploy/systemd/digest-ingest.service
  - deploy/systemd/digest-ingest-alert.service
  - tests/unit/test_phase24_systemd_units.py
  - docs/agents/local-platform-runbook.md
records_reviewed:
  - .planning/phases/24-scheduled-ingestion/24-07-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-08-PLAN.md
  - .planning/phases/24-scheduled-ingestion/24-07-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-08-SUMMARY.md
  - .planning/phases/24-scheduled-ingestion/24-VERIFICATION.md
  - .planning/phases/24-scheduled-ingestion/24-SECURITY.md
  - .planning/phases/24-scheduled-ingestion/24-PATTERNS.md
  - .planning/phases/24-scheduled-ingestion/24-VALIDATION.md
  - .planning/phases/24-scheduled-ingestion/24-CONTEXT.md
  - .planning/phases/24-scheduled-ingestion/24-UAT.md
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 24: Code Review Report (gap closure 24-07 / 24-08)

**Reviewed:** 2026-10-18T17:45:00Z
**Depth:** standard
**Files Reviewed:** 4 source/doc files + 10 planning records
**Status:** issues_found
**Scope:** `97e3b2d..HEAD` — plan 24-07 (G-24-3, oneshot start-phase bound) and plan 24-08 (G-24-4, numeric alert exit status). Earlier phase code is carried over from the previous report (see “Prior review findings”).

## Summary

Both mechanism fixes are correct and the two new negative text gates are genuinely load-bearing: mutation testing (bad token restored, good+inert token coexisting, alert qualifier restored, runbook/record regression) makes every one of the four gates fail, and restoring the tree returns 15/15. `deploy/systemd/digest-ingest.service` now uses `TimeoutStartSec=1800` with no `RuntimeMaxSec`; the alert reads `${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}`. Untouched-byte constraints are intact.

The remaining defects are not in the runtime units: one runbook recipe still prescribes a 2 s limit that the plan's own live evidence showed stamps `last_run_at`, one living record still advertises the inert token outside every gate, and the §5e cleanup command is over-broad. Two lower-severity notes cover an unpinned security-relevant unit token and historical records that still prescribe the superseded mechanisms.

## Critical Issues

None.

## Warnings

### WR-01: §5e run-limit recipe prescribes a 2 s limit whose “no stamp” expectation the recorded probe disproved

**File:** `docs/agents/local-platform-runbook.md:721-725` (also `24-07-SUMMARY.md:181-182`)
**Issue:** The runbook tells the operator to apply a `TimeoutStartSec=2` runtime drop-in and “confirm `Result=timeout` with `last_run_at` still at the seeded value”. The plan’s own live evidence records the opposite: at `TimeoutStartSec=2` the unit ended `Result=timeout ExecMainStatus=15` at 2162 ms **and** `last_run_at` had advanced (`24-07-SUMMARY.md:179`). A run whose work (one unreadable source → exit 2 → `stamp_last_run`) finishes in ≈2.0–2.1 s is signalled in its shutdown tail, and the in-flight REST write completes before the process dies; only `TimeoutStartSec=500ms` (530 ms) kept the stamp at the seeded value. The same unconditional claim (“`last_run_at` is not stamped”) appears in §4k (`:606`) and §5e item 5 (`:721`), and `24-07-SUMMARY.md:181-182` claims “the §5e recipe already documents the 500 ms fallback” — it does not: the runbook contains no 500 ms token, and the plan’s fallback (`24-07-PLAN.md` T3 step 5d) triggers only on `Result=success`, not on the observed `Result=timeout` + advanced stamp.
**Why it matters:** An operator following the recipe on the same host sees a stamped `last_run_at` and concludes the D-23 mitigation is broken (or that the probe is unreliable). The documented acceptance step cannot be satisfied with 2 s on this host.
**Fix:** Prescribe `TimeoutStartSec=500ms` — or “a limit short enough to precede `stamp_last_run`; 2 s was observed to land in the shutdown tail and still stamp” — and qualify the “not stamped” claim with “when the kill lands before `stamp_last_run`”. Make the retry branch fire on `Result=timeout` + a moved stamp as well, and correct the SUMMARY sentence that says the runbook already carries the fallback.

### WR-02: `24-CONTEXT.md` In-scope list still advertises the inert `RuntimeMaxSec=`

**File:** `.planning/phases/24-scheduled-ingestion/24-CONTEXT.md:19`
**Issue:** D-19 (`:63`) and D-23 (`:67`) carry the SUPERSEDED notes, but the In-scope bullet still says “… `flock -n`, `RuntimeMaxSec=`.” with no marker. The new gates scan only `24-VERIFICATION.md`, `24-PATTERNS.md` and `24-VALIDATION.md`, so this drift cannot turn the suite red, and a planner reading the scope gets the mechanism systemd 255 ignores.
**Why it matters:** Exactly the record-drift class the gap plans were meant to eliminate; a future plan can re-derive the inert knob from the living context file.
**Fix:** Replace the token with `TimeoutStartSec=1800` (or `TimeoutStartSec=`) or append the same one-line `SUPERSEDED (mechanism token only, 24-07)` marker used beside D-19/D-23.

### WR-03: `systemctl revert` cleanup in §5e deletes every drop-in, not just the runtime one

**File:** `docs/agents/local-platform-runbook.md:725,732`
**Issue:** Both run-limit and alert recipes clean up with `sudo systemctl revert digest-ingest.service`. On systemd 255, `revert` removes the unit’s *entire* `*.service.d/` trees below both `/etc/systemd/system` and `/run/systemd/system`, plus unit-file overrides — not only the `--runtime` drop-in the recipe created. The unit file itself survives (it has no vendor copy), but any operator-authored persistent drop-in (a tuned `TimeoutStartSec`, extra `Environment=`, `set-property` limits) is silently deleted. The runbook does not warn.
**Why it matters:** A verification recipe must not mutate unrelated production configuration; silently dropping a persistent override changes production behaviour after a test.
**Fix:** Remove only the runtime drop-in used by the recipe (`sudo rm -rf /run/systemd/system/digest-ingest.service.d` then `daemon-reload`), or keep `revert` and add “this also removes any persistent drop-in for this unit”.

## Info

### IN-01: Text contract does not pin `RuntimeDirectoryMode=0750` or the exact `EnvironmentFile=` path

**File:** `tests/unit/test_phase24_systemd_units.py:61-82`; `deploy/systemd/digest-ingest.service:12,15`
**Issue:** The gap plan lists `EnvironmentFile=/etc/digest-cds/ingest.env` and `RuntimeDirectoryMode=0750` among the preserved security bytes, but the tests assert only the `EnvironmentFile=` prefix and `RuntimeDirectory=digest-ingest`. A regression to `RuntimeDirectoryMode=0777` (a local user could then squat or remove `/run/digest-ingest/lock`) or to a repo-local env file would leave 15/15 green. The bytes are intact today — this is a contract-coverage gap, not a current defect.
**Fix:** Add `"EnvironmentFile=/etc/digest-cds/ingest.env"` and `"RuntimeDirectoryMode=0750"` to the token tuple in `test_service_tokens`.

### IN-02: Historical planning records still prescribe the superseded mechanisms

**File:** `.planning/phases/24-scheduled-ingestion/24-RESEARCH.md:881,915,927` (also `24-04-SUMMARY.md:33,142`, `24-03-PLAN.md:45`, `24-DISCUSSION-LOG.md:272`)
**Issue:** Research acceptance criteria still require `RuntimeMaxSec=1800`, A8 still says “Ubuntu 24.04 = systemd 255, где применим” (the opposite of the finding), and `:927` prescribes `${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}` for the alert. These are historical artifacts and are not scanned, but 24-08’s source audit never mentions the research’s alert expression, so a future planner can re-derive the broken contract from the research file.
**Fix:** Append SUPERSEDED markers to A8 and the alert sentence (the same “mechanism token only” style), or record in the plan/source audit that research and summaries are immutable history. Do not add these files to the whole-file negative gates — they must keep the defect description.

## Checked and Found Sound

**Negative/positive gate strength (mutation-proven, then restored byte-exact):**

| Mutation applied | Result |
|---|---|
| `digest-ingest.service`: `TimeoutStartSec=1800` → `RuntimeMaxSec=1800` | `test_service_tokens` + `test_service_does_not_use_runtime_limit_on_oneshot` failed (2 failed) |
| good token kept **and** `RuntimeMaxSec=1800` appended | only `test_service_does_not_use_runtime_limit_on_oneshot` failed (1 failed, 1 passed) — the negative gate is not shadowed by the positive one |
| alert: numeric substitution → `${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}` | `test_alert_unit` + `test_alert_unit_does_not_read_exit_qualifier` failed (2 failed) |
| runbook §4k/§5e `TimeoutStartSec` → `RuntimeMaxSec`, §5e `MONITOR_EXIT_STATUS` → `MONITOR_EXIT_CODE` | `test_runbook_and_records_name_the_oneshot_start_limit` + `test_runbook_and_verification_name_numeric_status` failed (2 failed) |
| restored tree | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` → **15 passed**; full suite → **1151 passed** |

The gates read the right files (`_read()` on the exact unit name; whole-file record reads, not a slice), the shared `_section()` helper resolves `## 4k.` / `## 5e.` correctly, and no assertion relies on a bare `EXIT_STATUS:-` substring (the nested expression is pinned, and `EXIT_CODE:-` is the negative token).

**Text-check counts:** the file collects **15** tests; `24-VERIFICATION.md:130` and the ING-06 row (`:233`) both say **15** text checks. The string “13/15” does not occur in the record; the only 13 is the unrelated `score: 13/13` must-have count. No `10 text-проверок` / `10 text-checks` claim remains.

**Untouched-byte constraints** — all present in `digest-ingest.service`: `Type=oneshot`, `flock -n -E 75 /run/digest-ingest/lock <venv>/ingest-collect`, `SuccessExitStatus=0 75`, `RuntimeDirectory=digest-ingest`, `RuntimeDirectoryMode=0750`, `OnFailure=digest-ingest-alert.service`, `User/Group=digestcds`, `EnvironmentFile=/etc/digest-cds/ingest.env`, `TZ=UTC`, `NoNewPrivileges`, `PrivateTmp`; the timer keeps `OnCalendar=*:0/15`, `Persistent=false`, `Unit=digest-ingest.service`. Pinning coverage is complete except for IN-01.

**Alert `case` for a killed run:** a SIGTERM kill yields `MONITOR_EXIT_STATUS=15`; there is no `15)` arm, so it falls to `*)` and prints `unexpected failure (exit 15)` with the numeric code. The plan explicitly excludes a `killed)` arm; this is acceptable and matches the recorded pre-fix `(exit killed)`/post-fix `(exit 15)` behaviour.

**Records:** `24-VERIFICATION.md`, `24-PATTERNS.md` and `24-VALIDATION.md` are clean of the inert token; `24-VERIFICATION.md` is clean of the qualifier; `24-SECURITY.md` T-24-32/T-24-34 name the working mechanisms, keep `closed`, and the alias/audit-trail edits are consistent (30 distinct + 2 aliases). `24-UAT.md` and the SECURITY re-verification notes intentionally keep the defect history and are correctly excluded from the gates; `ROADMAP.md` criterion 3 intentionally keeps the milestone wording per the 24-07 source audit.

**The four live probes reported by the orchestrator are not re-litigated:** `TimeoutStartUSec=30min` / `RuntimeMaxUSec=infinity`, the scratch-unit kill (`Result=timeout`, `ExecMainStatus=15`, ≈3115 ms), the `RuntimeMaxSec` control (`Result=success`, ≈10011 ms), the 500 ms real-unit kill without a stamp followed by a stamping run, and the exit-1/exit-2 alert lines with hardening intact.

## Prior review findings (refreshed against the current tree)

**Resolved and dropped from the active findings:** CR-01 (cursor write is now wrapped in its own `try/except`, `collect_batch.py:192-202`), WR-02 (unexpected feed exceptions isolated, `:138-145`), WR-03 (zero-source due run no longer stamps), WR-04 (alert runs as `digestcds` with hardening), WR-05 (cleared time restores the saved value), WR-06 (empty upsert re-reads the row). These are fixed in the current tree per `24-VERIFICATION.md` and re-checked here; they are not repeated.

**Carried over, unchanged and outside this diff (not counted above):**
- The previous **WR-01** (cursor advances past a failed video) remains an accepted risk under D-09; reversal was explicitly declined by the operator.
- The previous **IN-01..IN-03** (feed skip-reason taxonomy, double `Settings.from_env()`, AST blind spot for dynamic imports) remain deferred polish; they are recorded in `24-VERIFICATION.md`’s anti-patterns table.

---

_Reviewed: 2026-10-18T17:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
