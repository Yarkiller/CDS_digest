# Debug: alert cannot distinguish exit 1 from exit 2

- **Gap:** G-24-4 (UAT test 4)
- **Date:** 2026-10-18
- **Environment:** WSL2 Ubuntu 24.04, systemd 255

## Symptom

Forcing exit 1 and exit 2 on `digest-ingest.service` produces the same alert line:

```text
digest-ingest.service failed: unexpected failure (exit exited); journalctl -u digest-ingest.service
```

UAT test 4 requires distinct messages for partial failure (exit 1) and "no source could be
read" (exit 2). Threat T-24-34 claims this distinction exists.

## Evidence

Probe: a scratch `OnFailure=` target ran

```sh
echo "EXIT_CODE=[$EXIT_CODE] EXIT_STATUS=[$EXIT_STATUS] MONITOR_EXIT_CODE=[$MONITOR_EXIT_CODE] MONITOR_EXIT_STATUS=[$MONITOR_EXIT_STATUS]"
```

and the failing unit exited 2. Observed:

```text
PROBE EXIT_CODE=[] EXIT_STATUS=[] MONITOR_EXIT_CODE=[exited] MONITOR_EXIT_STATUS=[2]
```

## Root cause

`MonitorExitCode=`-derived variables are not what the unit assumes:

- `MONITOR_EXIT_CODE` is the **qualifier** (`exited`, `killed`, `dumped`), not a number.
- `MONITOR_EXIT_STATUS` is the **numeric** status (`2`, `15`, …).
- `EXIT_CODE` / `EXIT_STATUS` are the legacy names and are unset on this systemd.

`deploy/systemd/digest-ingest-alert.service:10` reads
`code="${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}"`, so `code` is always `exited` and every
`case` arm falls through to the `*)` branch. The alert text is permanently
"unexpected failure".

## Affected artifacts

- `deploy/systemd/digest-ingest-alert.service:10` — wrong env var.
- `tests/unit/test_phase24_systemd_units.py:105` — pins the broken expression
  `${MONITOR_EXIT_CODE:-${EXIT_CODE:-unknown}}`, so the text contract protects the defect.
- `.planning/phases/24-scheduled-ingestion/24-SECURITY.md` T-24-34, `24-VERIFICATION.md`,
  runbook §5e item 8.

## Fix direction (non-binding)

Read the numeric status instead, e.g.
`code="${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}"`, and keep the existing `case` arms.
Optional hardening: an explicit `killed)` arm so a SIGTERM from the run limit reports
"run killed" rather than "unexpected failure (exit 15)".

Validation: force exit 1 and exit 2 through `systemctl start` and compare
`journalctl -u digest-ingest-alert.service` — the two lines must differ.
