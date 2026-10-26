---
phase: 24-scheduled-ingestion
plan: 08
subsystem: infra
tags: [systemd, onfailure, journald, exit-code, runbook, text-contract, gap-closure]

# Dependency graph
requires:
  - phase: 24-04
    provides: "the checked-in oneshot service, timer and OnFailure alert unit, plus runbook §4k/§5e"
  - phase: 24-07
    provides: "the module-level `_section(runbook, heading)` slicer reused by this plan's drift gate"
provides:
  - "digest-ingest-alert.service reads the numeric exit status from MONITOR_EXIT_STATUS (fallback EXIT_STATUS)"
  - "inverted alert text contract: the numeric substitution is required, MONITOR_EXIT_CODE / EXIT_CODE:- are forbidden"
  - "§5e item 8 copy-pasteable exit-1/exit-2 runtime-drop-in recipe + §4k qualifier-vs-number explanation"
  - "runbook + verification-record drift gate (whole-file scan executed inside pytest)"
  - "live before/after proof: the same exit-2 run wrote 'unexpected failure (exit exited)' before the reinstall and 'no source could be read (exit 2)' after"
affects: [24-UAT, "phase-24 verify-work", "runbook §4k/§5e", "24-SECURITY.md", "24-VERIFICATION.md"]

# Actuals (#2632) — chars/4 over the realized diff (git diff c1246a0..HEAD, 23,883 chars)
actuals:
  tokens: 5971
  tasks: 3
  commits: 4
commits: 4
plan_head_before: c1246a0
plan_head_after: 2aed0a2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "systemd OnFailure monitor variables: MONITOR_EXIT_CODE is the qualifier (exited|killed|dumped), MONITOR_EXIT_STATUS is the number; the legacy EXIT_CODE/EXIT_STATUS names are unset on systemd 255"
    - "text contract inversion: pin the full nested substitution positively, then forbid the old tokens — a bare EXIT_STATUS:- substring is never asserted because it also occurs inside MONITOR_EXIT_STATUS:-"
    - "record drift gate: whole-file planning-record scan executed inside pytest, never a shell `!` negation (PowerShell host)"

key-files:
  created:
    - .planning/phases/24-scheduled-ingestion/24-08-red-evidence-task1.json
  modified:
    - deploy/systemd/digest-ingest-alert.service
    - tests/unit/test_phase24_systemd_units.py
    - docs/agents/local-platform-runbook.md
    - .planning/phases/24-scheduled-ingestion/24-SECURITY.md
    - .planning/phases/24-scheduled-ingestion/24-VERIFICATION.md

key-decisions:
  - "G-24-4 / T-24-34: the alert reads MONITOR_EXIT_STATUS (fallback EXIT_STATUS), because on systemd 255 MONITOR_EXIT_CODE carries the qualifier `exited` and EXIT_CODE is unset, so every run fell into the `*)` arm"
  - "the contract is inverted, not extended: the positive assertion pins the full nested expression `${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}` and the negative gate forbids `MONITOR_EXIT_CODE` and `EXIT_CODE:-`"
  - "no `killed)` arm is added (D-12 scope): a SIGTERM from the run limit legitimately falls to `*)` with the numeric code, e.g. `unexpected failure (exit 15)`"
  - "the qualifier explanation lives in §4k only — §5e stays free of the token so the drift gate can forbid it there"
  - "the record drift gate lives inside pytest because the execution host is PowerShell, where a leading `!` is a parse error"

requirements-completed: [ING-06]

coverage:
  - id: D1
    description: "digest-ingest-alert.service computes the numeric code from MONITOR_EXIT_STATUS (fallback EXIT_STATUS); the qualifier is forbidden by an inverted text contract"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py#test_alert_unit"
        status: pass
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py#test_alert_unit_does_not_read_exit_qualifier"
        status: pass
    human_judgment: false
  - id: D2
    description: "runbook §5e item 8 / §4k, 24-SECURITY.md T-24-34 and 24-VERIFICATION.md row 9 name the numeric variable and carry the live recipe; a drift gate keeps 24-VERIFICATION.md free of the qualifier"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py#test_runbook_and_verification_name_numeric_status"
        status: pass
    human_judgment: false
  - id: D3
    description: "on the real WSL2 systemd 255 host forcing exit 1 and exit 2 writes two distinct alert lines, and the same exit-2 run differs before vs after the reinstall"
    requirement: ING-06
    verification:
      - kind: manual_procedural
        ref: "24-08-PLAN.md checkpoint T3 steps 0-4 on WSL2 Ubuntu 24.04.2 / systemd 255.4-1ubuntu8.18 (operator-reported)"
        status: pass
    human_judgment: true
    rationale: "Requires sudo with a password, an interactive `systemctl edit --runtime` drop-in, and a live systemd host — none of which an executor can establish."

# Metrics
duration: 20min
completed: 2026-10-18
status: complete
---

# Phase 24 Plan 08: numeric alert exit-status Summary

**The `OnFailure=` alert now reads `MONITOR_EXIT_STATUS` instead of the `exited`/`killed` qualifier, so exit 1 and exit 2 produce distinct journald lines — proven on the same host where the pre-fix exit-2 run had printed «unexpected failure (exit exited)».**

## Performance

- **Duration:** 20 min (T1+T2 executor work plus the operator's live T3 probe)
- **Started:** 2026-10-18T17:16Z
- **Completed:** 2026-10-18T17:24Z
- **Tasks:** 3 of 3
- **Files modified:** 6 (1 created, 5 modified)

## What Changed

- `deploy/systemd/digest-ingest-alert.service`: one line. `code="${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}"` → `code="${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}"`. `Type=oneshot`, `User=digestcds`, `Group=digestcds`, `NoNewPrivileges=true`, `PrivateTmp=true`, the `1)`/`2)`/`*)` arms with their exact messages, and the trailing `journalctl -u digest-ingest.service` hint are byte-identical. No `killed)` arm, no comment line, no new notification channel, no package change.
- `tests/unit/test_phase24_systemd_units.py`: `test_alert_unit` now pins the numeric substitution (its docstring says the alert distinguishes exit 1/2 via the numeric `MONITOR_EXIT_STATUS`). New `test_alert_unit_does_not_read_exit_qualifier` asserts, in order, the full nested expression, then the absence of `MONITOR_EXIT_CODE`, then the absence of `EXIT_CODE:-`, then that the `journalctl` hint survives. New `test_runbook_and_verification_name_numeric_status` calls the shared `_section(runbook, "5e")` helper from 24-07 (no duplicated regex) and scans `24-VERIFICATION.md` whole-file for the qualifier.
- `docs/agents/local-platform-runbook.md`: §4k gains an **OnFailure monitor variables (G-24-4)** paragraph (qualifier vs number, legacy names unset, why a future edit must not switch back). §5e item 8 becomes **Alert codes (G-24-4)** with the copy-pasteable runtime-drop-in recipe for exit 1 and exit 2, the expected lines, and the `systemctl revert` / `reset-failed` cleanup; §5e names the number only.
- `.planning/phases/24-scheduled-ingestion/24-SECURITY.md`: T-24-34 mitigation rewritten around `MONITOR_EXIT_STATUS` (fallback `EXIT_STATUS`), explicitly noting `MONITOR_EXIT_CODE` is only the qualifier, citing the text contract and §5e item 8; stays `closed`. A **Re-verification T-24-34 (G-24-4, 24-08)** note was added beside the 24-07 T-24-32 note. The `T-24-46` alias from 24-07 is untouched — no second alias line, no new register row, no audit-count change.
- `.planning/phases/24-scheduled-ingestion/24-VERIFICATION.md`: every alert record now names the number — frontmatter `human_verification` item 4 `why_human`, body item 4 `**Why human:**`, and requirement row 9's alert clause plus its evidence cell (now «15 text-проверок»). The ING-06 coverage row's Source Plan cell ends `…, 24-07, 24-08` and its evidence cell reads `units + 15 text-checks`. `verified:`/`status:`, the 24-07 `TimeoutStartSec` wording, `24-UAT.md` and `24-SECURITY.md`'s history were left alone; `24-UAT.md` and `24-SECURITY.md` are deliberately excluded from the drift scan because they keep the defect description as history.

## RED Evidence

TDD RED was observed before any production/doc edit and recorded verbatim:

| Task | Command | Result | First failing assertion |
|------|---------|--------|-------------------------|
| T1 | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | **2 failed, 12 passed** | `test_alert_unit` → `AssertionError` on `assert "${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}" in body` (line 121); `test_alert_unit_does_not_read_exit_qualifier` → the **same positive** assertion (line 137); its `MONITOR_EXIT_CODE` absence check was never reached |
| T2 | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | **1 failed, 14 passed** | `test_runbook_and_verification_name_numeric_status` → `AssertionError: §5e must name MONITOR_EXIT_STATUS` (line 230) |

Both REDs are the *missing positive token*, never the stale negative one — exactly as the plan specifies. Evidence file: `24-08-red-evidence-task1.json` (keys `expected_result`, `actual_result`, `failing_test`, `exit_code`, `command`). Neither run showed an import, connection or `unit missing` error.

The test contains no bare `EXIT_STATUS:-` assertion: that substring is also a literal substring of `MONITOR_EXIT_STATUS:-`, so it could never fail once the positive token passes; the full nested expression is what proves the fallback.

## Live T3 Evidence (WSL2 Ubuntu 24.04.2 LTS, systemd 255.4-1ubuntu8.18)

| Step | Observed | Verdict |
|------|----------|---------|
| 0 | corrected units installed from the repo (`install -m 644`, `daemon-reload`); timer stopped; stale `/run/systemd/system/digest-ingest.service.d` removed; installed alert unit mtime `2026-10-18 20:20:57.529 +0300`; installed line reads `code="${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}"` | PASS |
| 1 | `systemctl cat digest-ingest-alert.service`: `Type=oneshot`, `User=digestcds`, `Group=digestcds`, `NoNewPrivileges=true`, `PrivateTmp=true`; `MONITOR_EXIT_STATUS` present, `MONITOR_EXIT_CODE` absent | PASS — hardening intact |
| 2 (exit 1 drop-in) | `Result=exit-code`, `ExecMainStatus=1`; alert line `… partial failure: a video failed or the run state could not be recorded (exit 1); journalctl -u digest-ingest.service` | PASS |
| 3 (exit 2 drop-in) | `Result=exit-code`, `ExecMainStatus=2`; alert line `… no source could be read or the schedule was unreadable (exit 2); journalctl -u digest-ingest.service` | PASS — a *different* line |
| 4 (cleanup) | drop-in gone (`ls /run/systemd/system/digest-ingest.service.d` → No such file or directory); real `ExecStart=/usr/bin/flock -n -E 75 /run/digest-ingest/lock /opt/digest-cds/.venv/bin/ingest-collect` restored; `systemctl is-active digest-ingest.timer` → `active` | PASS |

**Before/after on the same host, same unit, same forced codes** (the discriminating proof for G-24-4; the alert unit was reinstalled at 20:20:57 +03:00):

```text
# PRE-FIX (alert unit dated 18:55) — every code collapsed to the qualifier
20:10:13  digest-ingest.service failed: unexpected failure (exit exited)   <- 24-07 control run, exit 2
20:10:16  digest-ingest.service failed: unexpected failure (exit killed)   <- 24-07 killed run
20:13:50  digest-ingest.service failed: unexpected failure (exit exited)   <- 24-07 control run, exit 2
20:13:51  digest-ingest.service failed: unexpected failure (exit killed)   <- 24-07 killed run
20:13:53  digest-ingest.service failed: unexpected failure (exit exited)   <- 24-07 post-revert run, exit 2

# POST-FIX (alert unit installed 20:20:57.529)
20:20:57  ... partial failure: ... (exit 1)
20:20:59  ... no source could be read ... (exit 2)
```

An exit-2 run that printed «unexpected failure (exit exited)» at 20:10:13 and 20:13:50/53 printed «no source could be read … (exit 2)» at 20:20:59. That is the discriminating proof: not merely "two different lines exist", but the *same* forced code producing the *correct* line after the fix and the qualifier line before it.

Two consequences recorded deliberately:

- The pre-fix `exit killed` lines confirm the qualifier was a moving target (`exited` / `killed`), which is exactly why reading it could never feed a number to the `case`.
- After the fix a killed run falls to the `*)` arm with the numeric code (e.g. `unexpected failure (exit 15)`). The plan deliberately adds no `killed)` arm and no unit comment; that arm is out of scope for G-24-4. The unit's whole-body negative gate stays possible because the explanation lives in §4k / SECURITY instead.

## Verification

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | **15 passed** |
| `uv run pytest tests/unit/test_phase24_systemd_units.py -q -k runbook_and_verification_name_numeric_status` | **1 passed**, 14 deselected |
| `uv run pytest tests/unit/test_collect_cli_contract.py tests/unit/test_phase24_scheduler_guard.py -q` | **17 passed** |
| `uv run pytest -q` (full suite) | **1151 passed**, 1 pre-existing starlette DeprecationWarning |

`git diff -- deploy/systemd/digest-ingest-alert.service` is a single changed line; `git status --porcelain` after each task listed only that task's files plus the evidence JSON.

## Task Commits

Each task was committed atomically:

1. **T1 RED — pin the numeric exit status in the alert contract** — `30e0231` (test; includes `24-08-red-evidence-task1.json`)
2. **T1 GREEN — read MONITOR_EXIT_STATUS in the alert unit** — `121d16b` (fix)
3. **T2 RED — pin the alert's numeric status in the runbook** — `9ee2400` (test)
4. **T2 GREEN — correct the alert mechanism in runbook, security and verification** — `2aed0a2` (docs)
5. **T3 — live exit-1 vs exit-2 re-verification** — operator-executed, no commit (no code change)

**Plan metadata:** this SUMMARY commit (docs: complete numeric alert exit-status plan)

`commits` is measured: `git rev-list --count c1246a0..HEAD` = **4**. No ledger file existed at `$(git rev-parse --git-dir)/gsd-plan-head-before-24-08`, so the base is the dispatch-time HEAD **`c1246a0`** (`docs(24-07): complete oneshot start-phase bound plan`), the commit immediately preceding `30e0231`. `plan_head_before: c1246a0`, `plan_head_after: 2aed0a2`.

## Decisions Made

- **G-24-4 / T-24-34:** read `MONITOR_EXIT_STATUS` (fallback `EXIT_STATUS`). On systemd 255 the failing unit's environment provides `MONITOR_EXIT_CODE=exited` (a qualifier) and `MONITOR_EXIT_STATUS=2` (the number) while `EXIT_CODE`/`EXIT_STATUS` are unset, so the old expression made every `case` fall to `*)`. The live probe confirmed exactly this: `EXIT_CODE=[] EXIT_STATUS=[] MONITOR_EXIT_CODE=[exited] MONITOR_EXIT_STATUS=[2]`.
- **Inverted contract, not extended:** the positive assertion pins the whole nested expression and the negative gate forbids `MONITOR_EXIT_CODE` and `EXIT_CODE:-`. Asserting a bare `EXIT_STATUS:-` is forbidden — it is a substring of `MONITOR_EXIT_STATUS:-` and would be vacuously true.
- **No `killed)` arm (D-12 scope):** G-24-4 needs the exit-1/exit-2 distinction only. A SIGTERM from the run limit correctly falls through to `*)` with the numeric code, which is strictly better than the pre-fix `(exit killed)`.
- **D-20 upheld:** the alert stays journald-only — no `curl`, webhook or SMTP channel was added, and `test_no_publish_surface_in_units` remains green.
- **The record drift gate lives inside pytest.** The execution host is PowerShell, where a leading `!` is a parse error, so a negated `rg` would report a correct edit as a failure.

## Deviations from Plan

None — plan executed exactly as written. Both REDs fired on the intended positive assertions, the doc edits stayed inside the plan's `files_modified`, the alert diff is the single substituted line, and every verification target was green on the first post-edit run.

## Issues Encountered

None. The only environmental detail worth noting is that the host's installed alert unit predated the fix (installed 18:55), which is precisely what made the before/after journal comparison possible; step 0 reinstalled the corrected units.

## Known Stubs

None — the plan added no placeholder values, hardcoded empties or unwired components.

## User Setup Required

None — no external service configuration introduced. The live recipe now lives in runbook §4k/§5e for future hosts.

## Next Phase Readiness

- The alert distinguishes exit 1 from exit 2 on a live systemd 255 host; G-24-4 is closable by `/gsd-verify-work` against the two distinct journal lines recorded above.
- `24-VERIFICATION.md` row 9 and ING-06 are re-verifiable from the text contract (`15 text-проверок`), and the drift gate keeps the qualifier out of that record.
- Phase 24 was the last plan in the phase; `/gsd-verify-work 24` owns the final status reconciliation. `.planning/STATE.md` and `.planning/ROADMAP.md` were intentionally left untouched for the orchestrator.

---

## Self-Check: PASSED

- `24-08-SUMMARY.md` exists at the expected path; `24-08-red-evidence-task1.json` exists.
- Commits found as HEAD ancestors: `30e0231`, `121d16b`, `9ee2400`, `2aed0a2`.
- Verification re-run on the final tree: 15 passed / 1 passed / 17 passed / 1151 passed.

---
*Phase: 24-scheduled-ingestion*
*Completed: 2026-10-18*
