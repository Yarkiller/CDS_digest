---
phase: 24-scheduled-ingestion
plan: 04
subsystem: ingestion
tags: [systemd, timer, flock, journald, ingest-collect, ing-07, tdd]

requires:
  - phase: 24-01
    provides: ingest-collect entry point + collect_cli (separate from cli.py)
  - phase: 24-03
    provides: due_decision + last_run_at stamp (makes Persistent=false safe)
provides:
  - deploy/systemd digest-ingest.service/.timer/-alert.service
  - 10-check text-contract for units + §4k↔.env.example cross-check
  - ING-07 AST + runtime sys.modules guard
  - Runbook §4k install + §5e UAT
affects:
  - 24-05 (admin schedule API; timer already polls)
  - 24-06 (UI schedule section; ops path documented)

actuals:
  tokens: 4927
  tasks: 2
  commits: 4

plan_head_before: e6035210d52f35ed51fbc11aab360367c29f3c50
plan_head_after: d7c613c6b6b144086f78905398e2f690b1228094

tech-stack:
  added: []
  patterns:
    - RuntimeDirectory=digest-ingest + flock -n -E 75 + SuccessExitStatus=0 75
    - OnFailure alert distinguishes exit 1 vs 2 via MONITOR_EXIT_CODE
    - AST Import/ImportFrom root scan + subprocess sys.modules (ING-07)

key-files:
  created:
    - deploy/systemd/digest-ingest.service
    - deploy/systemd/digest-ingest.timer
    - deploy/systemd/digest-ingest-alert.service
    - tests/unit/test_phase24_systemd_units.py
    - tests/unit/test_phase24_scheduler_guard.py
    - .planning/phases/24-scheduled-ingestion/24-04-red-evidence.json
  modified:
    - docs/agents/local-platform-runbook.md

key-decisions:
  - "§4k prose avoids non-env KEY= tokens so UPPER_SNAKE= cross-check only hits Settings.from_env keys"
  - "Secret/publish unit scans assert non-empty unit set (anti-vacuum on empty deploy/systemd)"

patterns-established:
  - "systemd text-contract mirrors migration 011 Path.exists + rglob banned-token scans"
  - "ING-07 guard is test-only helper; injection of existing root (json) proves scanner is live"

requirements-completed: [ING-06, ING-07]

coverage:
  - id: D1
    description: "Three systemd units: oneshot+flock, 15min timer Persistent=false, journald alert exit 1/2"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "No secrets or publish/send/curl in unit files; EnvironmentFile path only"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py::test_no_secrets_in_units"
        status: pass
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py::test_no_publish_surface_in_units"
        status: pass
    human_judgment: false
  - id: D3
    description: "Runbook §4k install (useradd, install -d, uv sync, enable --now) + §5e UAT checklist"
    requirement: ING-06
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_systemd_units.py::test_runbook_4k_env_keys_exist_in_env_example"
        status: pass
      - kind: manual_procedural
        ref: "docs/agents/local-platform-runbook.md§5e"
        status: unknown
    human_judgment: true
    rationale: "Live systemctl/journalctl/flock/RuntimeMaxSec and 0600 env mode require a VM"
  - id: D4
    description: "ING-07: AST + runtime sys.modules prove collect_cli cannot reach backend/publish/send"
    requirement: ING-07
    verification:
      - kind: unit
        ref: "tests/unit/test_phase24_scheduler_guard.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "ingest <url> contract unchanged (PRESERVE tripwire)"
    requirement: ING-07
    verification:
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-10-18
status: complete
---

# Phase 24 Plan 04: Systemd units + ING-07 guard Summary

**Checked-in ingest timer (15 min, Persistent=false), flock oneshot with RuntimeMaxSec/exit-75 success, journald alert distinguishing exit 1 vs 2, and dual-level ING-07 proof that collect_cli cannot reach publish/send.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-10-18T15:16:13+03:00
- **Completed:** 2026-10-18
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Three unit files under `deploy/systemd/` pin ING-06 ops path (flock, RuntimeDirectory, OnFailure).
- Ten text-contract checks + §4k↔`.env.example` cross-check; §5e UAT checklist for VM smoke.
- ING-07 AST + runtime guard with anti-vacuum and injection probe; `test_cli_ingest_contract.py` untouched and green.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: systemd text-contract** - `fb81c98` (test)
2. **Task 1 GREEN: units + runbook §4k/§5e** - `763ccc9` (feat)
3. **Task 2 RED: ING-07 guard stub scanner** - `f4da914` (test)
4. **Task 2 GREEN: AST import-graph scanner** - `d7c613c` (feat)

**Plan metadata:** `36e64ea` (docs: complete plan); ledger follow-ups through `b4852d3`

## Files Created/Modified

- `deploy/systemd/digest-ingest.service` — oneshot under flock `-E 75`, RuntimeMaxSec=1800, SuccessExitStatus=0 75
- `deploy/systemd/digest-ingest.timer` — OnCalendar=*:0/15, Persistent=false
- `deploy/systemd/digest-ingest-alert.service` — journald-only alert with exit 1/2 messages
- `tests/unit/test_phase24_systemd_units.py` — 10-check text-contract
- `tests/unit/test_phase24_scheduler_guard.py` — ING-07 AST + runtime guard
- `docs/agents/local-platform-runbook.md` — §4k install, §5e UAT
- `.planning/phases/24-scheduled-ingestion/24-04-red-evidence.json` — RED evidence for Task 1

## Decisions Made

- §4k describes systemd directives in prose (no stray `KEY=` besides env keys) so check 9 only validates `Settings.from_env` keys against `.env.example`.
- Banned-token unit scans require a non-empty unit set so an empty `deploy/systemd/` cannot vacuously pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Anti-vacuum on secret/publish unit scans**
- **Found during:** Task 1 (RED)
- **Issue:** With no unit files, `rglob` loops passed vacuously (2 green on empty tree).
- **Fix:** `assert bodies, "no unit files under deploy/systemd"` before banned-token loops.
- **Files modified:** `tests/unit/test_phase24_systemd_units.py`
- **Commit:** `fb81c98`

**2. [Rule 2 - Missing critical functionality] §4k prose avoids non-env KEY= tokens**
- **Found during:** Task 1 (GREEN)
- **Issue:** Phrases like `User=digestcds` / `Persistent=true` would fail check 9 against `.env.example`.
- **Fix:** Rewrote §4k Do-not/Prerequisites to name directives without `UPPER_SNAKE=` except env keys.
- **Files modified:** `docs/agents/local-platform-runbook.md`
- **Commit:** `763ccc9`

## TDD Gate Compliance

| Task | RED commit | GREEN commit | RED evidence |
|------|------------|--------------|--------------|
| 1 systemd units | `fb81c98` | `763ccc9` | `24-04-red-evidence.json` — `test_three_unit_files_exist` → unit missing |
| 2 ING-07 guard | `f4da914` | `d7c613c` | intentionally failing `test_guard_catches_injected_violation` (stub scanner) |

## Known Stubs

None — units and guards are complete text/test artifacts; live `systemctl` UAT remains operator §5e (documented, not stubbed in code).

## Threat Flags

None beyond plan threat model (T-24-30…T-24-35 mitigated by EnvironmentFile scan, flock/RuntimeMaxSec, User=digestcds, ING-07 guard).

## Self-Check: PASSED

- FOUND: `deploy/systemd/digest-ingest.service`
- FOUND: `deploy/systemd/digest-ingest.timer`
- FOUND: `deploy/systemd/digest-ingest-alert.service`
- FOUND: `tests/unit/test_phase24_systemd_units.py`
- FOUND: `tests/unit/test_phase24_scheduler_guard.py`
- FOUND: commits `fb81c98`, `763ccc9`, `f4da914`, `d7c613c`
- VERIFY: `uv run pytest` units+guard+preserve contracts → 35 passed
