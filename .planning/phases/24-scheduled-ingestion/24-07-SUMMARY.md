---
phase: 24-scheduled-ingestion
plan: 07
subsystem: infra
tags: [systemd, oneshot, timers, timeoutstartsec, runbook, text-contract]

# Dependency graph
requires:
  - phase: 24-04
    provides: "the checked-in oneshot service + timer + alert unit, the unit text contract, and runbook §4k/§5e"
provides:
  - "digest-ingest.service bounds its whole useful life with TimeoutStartSec=1800 (no inert RuntimeMaxSec)"
  - "inverted text contract: TimeoutStartSec=1800 required, RuntimeMaxSec forbidden on the oneshot"
  - "shared _section(runbook, heading) slicer + whole-file record drift gate inside pytest"
  - "runbook §4k run-limit note and §5e item 5 live kill recipe"
  - "corrected T-24-32 mitigation and VERIFICATION row 9 mechanism"
  - "live proof that a killed run does not stamp last_run_at (500 ms limit) and the next tick is due"
affects: [24-08, "phase-24 verify-work", "runbook §4k/§5e", "24-SECURITY.md", "24-VERIFICATION.md"]

# Actuals (#2632) — chars/4 over the realized diff (git diff 97e3b2d..HEAD, 99,591 chars)
actuals:
  tokens: 24898
  tasks: 3
  commits: 4
commits: 4
plan_head_before: 97e3b2d
plan_head_after: b4771fa

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "systemd: a Type=oneshot's only bound is its start phase (TimeoutStartSec); RuntimeMaxSec applies only to units that reach running"
    - "text contract: positive token + negative absence gate coupled to the unit Type, so the broken token cannot return"
    - "record drift gate: whole-file scan of planning records executed inside pytest, never a shell `!` negation (PowerShell host)"

key-files:
  created:
    - .planning/phases/24-scheduled-ingestion/24-07-red-evidence-task1.json
    - .planning/phases/24-scheduled-ingestion/24-07-red-evidence-task2.json
  modified:
    - deploy/systemd/digest-ingest.service
    - tests/unit/test_phase24_systemd_units.py
    - docs/agents/local-platform-runbook.md
    - .planning/phases/24-scheduled-ingestion/24-SECURITY.md
    - .planning/phases/24-scheduled-ingestion/24-VERIFICATION.md
    - .planning/phases/24-scheduled-ingestion/24-PATTERNS.md
    - .planning/phases/24-scheduled-ingestion/24-VALIDATION.md
    - .planning/phases/24-scheduled-ingestion/24-CONTEXT.md

key-decisions:
  - "D-23 / G-24-3: the bound moves to TimeoutStartSec=1800 because systemd 255 ignores RuntimeMaxSec= on Type=oneshot (it only applies to units that reach running)"
  - "T-24-32: the mitigation is now the start-phase bound plus flock -n -E 75 and SuccessExitStatus=0 75; the inert token is forbidden by test_service_does_not_use_runtime_limit_on_oneshot"
  - "the binding property is the STAMP, not the unit's Result: a run killed in its shutdown tail can still stamp last_run_at, so the probe asserts on last_run_at (live evidence: 2 s stamped, 500 ms did not)"
  - "the record drift gate lives inside pytest because the execution host is PowerShell, where a leading `!` is a parse error"

requirements-completed: [ING-06]

coverage:
  - id: D1
    description: "digest-ingest.service bounds the oneshot start phase with TimeoutStartSec=1800 and carries no RuntimeMaxSec"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py#test_service_tokens"
        status: pass
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py#test_service_does_not_use_runtime_limit_on_oneshot"
        status: pass
    human_judgment: false
  - id: D2
    description: "runbook §4k/§5e, 24-SECURITY.md T-24-32, 24-VERIFICATION.md row 9, 24-PATTERNS.md and 24-VALIDATION.md name the working mechanism; 24-CONTEXT.md D-19/D-23 carry SUPERSEDED notes"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py#test_runbook_and_records_name_the_oneshot_start_limit"
        status: pass
    human_judgment: false
  - id: D3
    description: "on the real systemd host a oneshot longer than the limit is killed, a killed run does not stamp last_run_at, and the next tick is due from the same cursor"
    requirement: ING-06
    verification:
      - kind: manual_procedural
        ref: "24-07-PLAN.md checkpoint T3 steps 0-5f on WSL2 Ubuntu 24.04 / systemd 255 (operator-reported)"
        status: pass
    human_judgment: true
    rationale: "The kill, the cgroup SIGTERM/SIGKILL path and the absence of a DB stamp require a live systemd host, sudo and a seeded ingestion_schedule row — none of which an executor can establish."

# Metrics
duration: 35min
completed: 2026-10-18
status: complete
---

# Phase 24 Plan 07: the oneshot start-phase bound Summary

**Replaced the inert `RuntimeMaxSec=1800` with `TimeoutStartSec=1800`, inverted the text contract so the broken token cannot return, corrected every record that asserted it, and proved on a live systemd 255 host that a killed run does not stamp `last_run_at`.**

## Performance

- **Duration:** 35 min (T1+T2 executor work plus the operator's live T3 probe)
- **Started:** 2026-10-18T16:55Z
- **Completed:** 2026-10-18T17:14Z
- **Tasks:** 3 of 3
- **Files modified:** 10 (2 created, 8 modified)

## What Changed

- `deploy/systemd/digest-ingest.service`: `RuntimeMaxSec=1800` → `TimeoutStartSec=1800`, and the `# D-23:` comment reworded to say the **oneshot start phase** is bounded. Diff is exactly two lines; `Type=oneshot`, `User=`/`Group=digestcds`, `WorkingDirectory=`, `EnvironmentFile=`, `Environment=TZ=UTC`, `RuntimeDirectory=digest-ingest`, `RuntimeDirectoryMode=0750`, the `flock -n -E 75 …/ingest-collect` `ExecStart=`, `SuccessExitStatus=0 75`, `NoNewPrivileges=true`, `PrivateTmp=true` are byte-identical. The timer (`OnCalendar=*:0/15`, `Persistent=false`) and the alert unit have zero diff.
- `tests/unit/test_phase24_systemd_units.py`: `test_service_tokens` now pins `TimeoutStartSec=1800`; new `test_service_does_not_use_runtime_limit_on_oneshot` asserts `Type=oneshot`, then `TimeoutStartSec=1800`, then the absence of `RuntimeMaxSec`. New module-level `_section(runbook, heading)` slicer (the refactored `test_runbook_4k_env_keys_exist_in_env_example` and the new drift test both use it — no inline `re.search` slicing remains). New `test_runbook_and_records_name_the_oneshot_start_limit` asserts §4k names `TimeoutStartSec=1800`, §5e names `TimeoutStartSec` and not `RuntimeMaxSec`, and scans `24-VERIFICATION.md`, `24-PATTERNS.md`, `24-VALIDATION.md` whole-file for the inert token.
- `docs/agents/local-platform-runbook.md`: §4k gains a **Run limit (D-23)** paragraph (why the runtime knob is inert on a oneshot, SIGTERM→SIGKILL after `TimeoutStopSec`, no stamp, next tick due); §5e item 5 becomes a copy-pasteable three-part recipe (`TimeoutStartUSec` check, clean journald, scratch-unit kill) plus a pointer to the discriminating T3 step-5 round-trip.
- `.planning/phases/24-scheduled-ingestion/24-SECURITY.md`: T-24-32 mitigation names `TimeoutStartSec=1800` + `flock` + `SuccessExitStatus`, cites both tests, stays `closed`; a **Re-verification T-24-32 (G-24-3, 24-07)** note records the UAT observation and declares `T-24-45 → T-24-32` / `T-24-46 → T-24-34` as aliases; the audit-trail `Threats Total` cell reads `30 distinct threats + 2 plan-local aliases`.
- `.planning/phases/24-scheduled-ingestion/24-VERIFICATION.md`: every `RuntimeMaxSec` mention renamed to `TimeoutStartSec` (frontmatter `human_verification`, body item 3, truth-table row 9, requirement row 9); row 9 evidence names the new negative test and reads «13 text-проверок»; ING-06 source plan and evidence cell updated to `24-07` / `units + 13 text-checks`. Frontmatter `verified:`/`status:` untouched.
- `.planning/phases/24-scheduled-ingestion/24-PATTERNS.md`: the unit excerpt and the «Обязательные токены» sentence now say `TimeoutStartSec=1800`.
- `.planning/phases/24-scheduled-ingestion/24-VALIDATION.md`: T13 secure-behavior cell says `TimeoutStartSec=` instead of `RuntimeMaxSec=`.
- `.planning/phases/24-scheduled-ingestion/24-CONTEXT.md`: D-19 and D-23 each gained a one-line **SUPERSEDED (mechanism token only, 24-07)** note naming `TimeoutStartSec=1800`, in the D-27 marker style; decision bodies otherwise untouched, and D-20/D-21/D-27 are byte-identical.

## RED Evidence

TDD RED was observed before any production/doc edit and recorded verbatim:

| Task | Command | Result | First failing assertion |
|------|---------|--------|-------------------------|
| T1 | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | **2 failed, 10 passed** | `test_service_tokens` → `AssertionError: TimeoutStartSec=1800` (line 66); `test_service_does_not_use_runtime_limit_on_oneshot` → `AssertionError: TimeoutStartSec=1800` (line 73, its first positive assertion; the negative never ran) |
| T2 | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | **1 failed, 12 passed** | `test_runbook_and_records_name_the_oneshot_start_limit` → `AssertionError: §4k must name TimeoutStartSec=1800` (line 190) |

Both REDs are the *missing positive token*, not the stale negative one — exactly as the plan specifies. Evidence files: `24-07-red-evidence-task1.json`, `24-07-red-evidence-task2.json`. The `_section` helper refactor was verified green (12 passed) *before* the new drift test was added.

## Live T3 Evidence (WSL2 Ubuntu 24.04.2 LTS, systemd 255.4-1ubuntu8.18)

| Step | Observed | Verdict |
|------|----------|---------|
| 1 | `Type=oneshot  TimeoutStartUSec=30min  RuntimeMaxUSec=infinity` | PASS |
| 2 | no «has no effect in combination with Type=oneshot» warning in journald for a fresh start | PASS |
| 3 (scratch `TimeoutStartSec=3` + `sleep 10`) | `start_rc=1 elapsed_ms=3115 Result=timeout ExecMainStatus=15` | PASS |
| 4 (control `RuntimeMaxSec=3` + `sleep 10`) | `control_rc=0 control_elapsed_ms=10011 Result=success ExecMainStatus=0` | PASS — the old knob is provably inert |
| 5c control (real unit, no drop-in) | `Result=exit-code ExecMainStatus=2`; `last_run_at` → `T_control=2026-10-18T17:13:50.23877+00:00` | PASS — stamped |
| 5d killed run (`TimeoutStartSec=500ms` drop-in) | `Result=timeout ExecMainStatus=15 elapsed_ms=530`; `last_run_at` = `T_backdated2=2026-10-16T17:13:45+00:00` | PASS — NOT stamped |
| 5e after `systemctl revert` | `Result=exit-code ExecMainStatus=2`; `T_postkill=2026-10-18T17:13:53.246284+00:00` | PASS — still due, and it stamped |
| 5f cleanup | schedule row restored to `{enabled:true, time_of_day:06:00:00, days_of_week:[1,3,6,7], last_run_at:null}`; seeded source deleted; timer `active` | PASS |

Four-value comparison: `T_backdated` (2026-10-16T17:13:45) `<` `T_control` (2026-10-18T17:13:50); `last_run_at` after the kill `==` `T_backdated2`; `T_postkill` (2026-10-18T17:13:53) `>` `T_backdated2`. All four hold — the killed run did not advance the cursor and the next tick was due from the same cursor.

## Verification

| Command | Result |
|---------|--------|
| `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | **13 passed** |
| `uv run pytest tests/unit/test_phase24_systemd_units.py -q -k runbook_and_records_name_the_oneshot_start_limit` | **1 passed** (12 deselected) |
| `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_phase24_scheduler_guard.py -q` | **13 passed** |
| `uv run pytest -q` (full suite) | **1149 passed**, 1 pre-existing starlette DeprecationWarning |

## Task Commits

Each task was committed atomically:

1. **T1 RED — invert the service text contract** — `cc643db` (test)
2. **T1 GREEN — bound the oneshot start phase** — `c48a306` (fix)
3. **T2 RED — pin the runbook to the oneshot start limit** — `e535f28` (test)
4. **T2 GREEN — correct the run-limit mechanism in runbook, security and verification** — `b4771fa` (docs)
5. **T3 — live re-verification** — operator-executed, no commit (no code change)

**Plan metadata:** this SUMMARY commit (docs: complete oneshot start-phase bound plan)

`commits` is measured: `git rev-list --count 97e3b2d..HEAD` = **4**. No ledger file existed at `$(git rev-parse --git-dir)/gsd-plan-head-before-24-07`, so the base used is the dispatch-time HEAD `97e3b2d` (the commit immediately preceding `cc643db`). `plan_head_before: 97e3b2d`, `plan_head_after: b4771fa`.

## Decisions Made

- **D-23 / G-24-3:** the bound is `TimeoutStartSec=1800`, not `RuntimeMaxSec=1800`. systemd enforces `RuntimeMaxSec=` only for units that reach `running`; a oneshot stays `activating` until `ExecStart` exits, so its only bound is the start timeout (systemd 255 logs the «has no effect» warning and ignores the runtime knob). The property D-19/D-23 required — a bounded run that does not stamp `last_run_at` — is preserved at 1800 s.
- **T-24-32:** mitigation is the start-phase bound plus `flock -n -E 75` and `SuccessExitStatus=0 75`; the text contract couples the negative gate to `Type=oneshot`, because `RuntimeMaxSec` would be legitimate on a unit that reaches `running`.
- **The binding property is the stamp, not the unit's `Result`** (see Deviations). The live probe therefore asserts on `last_run_at`, and the limit that discriminates is 500 ms, not 2 s.
- **The record drift gate lives inside pytest.** The execution host is PowerShell, where a leading `!` is a parse error, so a negated `rg` would report a correct edit as a failure on any shell-agnostic run.

## Deviations from Plan

### 1. [Observation, no code impact] `Result=timeout` alone does not prove `last_run_at` was not stamped

- **Found during:** T3 step 5d (live probe).
- **Observation:** the first attempt used `TimeoutStartSec=2` and produced `Result=timeout ExecMainStatus=15 elapsed_ms=2162` — yet `last_run_at` **had** moved (17:10:08 → `2026-10-18T17:10:16.235729+00:00`). A one-source run whose feed is unreadable finishes its work (read source → exit 2 → `stamp_last_run`) in ≈2.0–2.1 s, so a 2 s start-limit expiry lands in the *shutdown tail*: systemd SIGTERMs the cgroup at the limit, the process can still complete an in-flight REST write before it dies, and systemd records `Result=timeout` because the start phase overran. This is a real systemd/DB behaviour, not a script artifact.
- **Consequence:** `Result=timeout` alone is **not** evidence for D-23 / T-24-32. The binding property is the **stamp**: `last_run_at` must not advance. The probe asserts on `last_run_at`, and 500 ms is the limit that actually produced the discriminating result (`last_run_at` stayed at `T_backdated2`, elapsed 530 ms).
- **Why this does not weaken the plan's must_haves:** the mitigation — a bounded run that cannot hold `/run/digest-ingest/lock` forever — is unaffected and is exactly what the checkpoint proves at 500 ms. The runbook §5e item 5 recipe and `24-VERIFICATION.md` item 3 describe the expected sequence (killed → no stamp → next tick due) and it holds at any limit short enough to precede the stamp; the recipe's re-backdate-and-retry-with-500 ms branch existed for this case and was used as designed.
- **Files modified:** none (observation only; the §5e recipe already documents the 500 ms fallback).
- **Committed in:** n/a.

### 2. [Environment hygiene, no code impact] Two leftovers from an earlier live UAT on the host

- **Found during:** T3 step 0.
- **Observation:** the host still had the **pre-fix** `RuntimeMaxSec=1800` installed at `/etc/systemd/system/digest-ingest.service` (so the repo fix had to be re-installed), and a stale `/etc/systemd/system/digest-ingest.timer.d/uat-speed.conf` with `OnCalendar=*:0/1` made the timer fire every minute.
- **Fix:** both removed/reinstalled by step 0 (`install -m 644`, `daemon-reload`, drop-in removed); the timer was stopped for the probe and restarted in 5f (`is-active` = `active`).
- **Files modified:** none in the repository — host state only. Nothing committed for this.

---

**Total deviations:** 0 auto-fixed; 1 live-behaviour observation and 1 environment-hygiene note, both documented above.
**Impact on plan:** none on scope or code. The observation sharpens the acceptance criterion (assert the stamp, not `Result=`), which the live evidence already satisfies.

## Issues Encountered

None. The REDs fired on the intended assertions, the doc edits stayed inside the plan's `files_modified`, and every verification target was green on the first post-edit run.

## User Setup Required

None — no external service configuration introduced. The live checklist remains part of the runbook for future hosts.

## Next Phase Readiness

- The unit installed on the WSL2 host now reports `TimeoutStartUSec=30min` and produces no inert-knob warning; the timer is active again with its normal 15-minute `OnCalendar`.
- `24-VERIFICATION.md` row 9 and ING-06 are re-verifiable from the text contract; `/gsd-verify-work` owns the final status reconciliation.
- Plan 24-08 (G-24-4) is untouched by this plan and remains the next wave.

---

## Self-Check: PASSED

- `24-07-SUMMARY.md` exists at the expected path.
- Commits found: `cc643db`, `c48a306`, `e535f28`, `b4771fa` (all HEAD ancestors).
- Created evidence files exist: `24-07-red-evidence-task1.json`, `24-07-red-evidence-task2.json`.
- Verification re-run on the final tree: 13 passed / 13 passed / 1149 passed.

---
*Phase: 24-scheduled-ingestion*
*Completed: 2026-10-18*
