# Debug: RuntimeMaxSec ignored for Type=oneshot

- **Gap:** G-24-3 (UAT test 3)
- **Date:** 2026-10-18
- **Environment:** WSL2 Ubuntu 24.04, systemd 255 (255.4-1ubuntu8.18)

## Symptom

`deploy/systemd/digest-ingest.service` sets `RangeMaxSec` — concretely `RuntimeMaxSec=1800` —
but a hung run is never killed. D-23 and threat T-24-32 assume it bounds the run.

## Evidence

1. Every start of the real unit logs:

```text
digest-ingest.service: RuntimeMaxSec= has no effect in combination with Type=oneshot. Ignoring.
```

2. Scratch probe — `Type=oneshot`, `RuntimeMaxSec=2`, `ExecStart=/bin/sleep 8`:

```text
start_rc=0 elapsed=8s
Result=success
ExecMainStatus=0
uat-runtimemax.service: RuntimeMaxSec= has no effect in combination with Type=oneshot. Ignoring.
```

3. Control probe — identical unit with `TimeoutStartSec=2` instead:

```text
start_rc=1 elapsed=3s
Result=timeout
ExecMainStatus=15
ActiveState=failed
uat-timeoutstart.service: start operation timed out. Terminating.
```

## Root cause

systemd only enforces `RuntimeMaxSec=` for services that have a runtime (i.e. that stay in
`running` state). A `Type=oneshot` unit is in `activating` until `ExecStart` exits, so the
runtime limit is inapplicable and systemd ignores it with a warning. The correct knob for a
oneshot is `TimeoutStartSec=` (or `TimeoutStartSec=infinity` + an explicit killer), because the
whole useful life of a oneshot is its start phase.

Consequence: D-23 is unimplemented, T-24-32 stays open, and a hung `ingest-collect` holds
`/run/digest-ingest/lock` forever — every later tick then exits 75 and is treated as success
(`SuccessExitStatus=0 75`), so the timer silently stops collecting with no alert.

## Affected artifacts

- `deploy/systemd/digest-ingest.service:18` — `RuntimeMaxSec=1800`
- `tests/unit/test_phase24_systemd_units.py:60` — pins `RuntimeMaxSec=1800` as a token, so the
  text contract *protects the broken configuration* and must be inverted (assert
  `TimeoutStartSec=1800`, assert `RuntimeMaxSec` absent).
- `docs/agents/local-platform-runbook.md` §4k (unit inventory / why-timer note) and §5e item 5.
- `.planning/phases/24-scheduled-ingestion/24-SECURITY.md` T-24-32 mitigation text.
- `.planning/phases/24-scheduled-ingestion/24-VERIFICATION.md` requirement row 9.

## Fix direction (non-binding)

Replace `RuntimeMaxSec=1800` with `TimeoutStartSec=1800` on the oneshot. Keep the 1800 s
property, `SuccessExitStatus=0 75`, `flock`, and `OnFailure=` untouched. On timeout the unit
ends `Result=timeout` / `SIGTERM`, `ingest-collect` never reaches `stamp_last_run`, so the next
tick is due again from the same cursor — exactly the D-23 property. `last_run_at` non-stamping
still needs the live re-check in UAT test 3.
