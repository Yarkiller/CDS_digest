"""Text-contract: Phase 24 systemd units (ING-06, D-18…D-24).

Reads deploy/systemd/*.service|*.timer as text (no systemctl). Mirrors
tests/unit/test_phase16_migration_011.py + rglob banned-token scans.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_UNITS = _REPO / "deploy" / "systemd"

# Phase 24 records ship with the closed v1.3 milestone. GSD archives a finished
# milestone's phases under `.planning/milestones/v<N>-phases/`, so the records are
# resolved from there -- the same layout `test_captions_error_mapping.py` already
# reads (`.planning/milestones/v1.1-ROADMAP.md`). Resolving once keeps the two
# consumers below from drifting apart when a milestone closes.
_PHASE_RECORDS = (
    _REPO / ".planning" / "milestones" / "v1.3-phases" / "24-scheduled-ingestion"
)

_UNIT_NAMES = (
    "digest-ingest.service",
    "digest-ingest.timer",
    "digest-ingest-alert.service",
)

_SECRET_TOKENS = (
    "DEEPSEEK_API_KEY=",
    "SUPABASE_SECRET_KEY=",
    "SUPABASE_URL=",
    "SMTP_PASSWORD=",
)

_PUBLISH_TOKENS = (
    "publish",
    "/admin/shortlist/send",
    "curl",
)


def _read(name: str) -> str:
    path = _UNITS / name
    assert path.exists(), f"unit missing: {path}"
    return path.read_text(encoding="utf-8")


def _iter_unit_bodies() -> list[tuple[Path, str]]:
    paths = sorted(_UNITS.rglob("*.service")) + sorted(_UNITS.rglob("*.timer"))
    return [(p, p.read_text(encoding="utf-8")) for p in paths]


def _section(runbook: str, heading: str) -> str:
    """Return the slice from ``## <heading>.`` up to the next ``## `` heading."""
    pattern = rf"^## {re.escape(heading)}\..*?(?=^## |\Z)"
    match = re.search(pattern, runbook, flags=re.M | re.S)
    assert match is not None, f"runbook §{heading} missing"
    return match.group(0)


def test_three_unit_files_exist() -> None:
    """Check 1: three files exist with exact names."""
    for name in _UNIT_NAMES:
        path = _UNITS / name
        assert path.exists(), f"unit missing: {path}"


def test_service_tokens() -> None:
    """Check 2: oneshot service pins flock, the oneshot start-phase limit, OnFailure, RuntimeDirectory."""
    body = _read("digest-ingest.service")
    for token in (
        "Type=oneshot",
        "EnvironmentFile=",
        "OnFailure=digest-ingest-alert.service",
        "TimeoutStartSec=1800",
        "RuntimeDirectory=digest-ingest",
        "flock -n",
        "-E 75",
        "SuccessExitStatus=",
    ):
        assert token in body, token


def test_service_does_not_use_runtime_limit_on_oneshot() -> None:
    """Check 2b: the runtime knob is inert on Type=oneshot, so it must never return."""
    body = _read("digest-ingest.service")
    assert "Type=oneshot" in body, "RuntimeMaxSec is only valid for a unit that reaches running"
    assert "TimeoutStartSec=1800" in body, "TimeoutStartSec=1800"
    assert "RuntimeMaxSec" not in body


def test_service_exec_start_is_absolute() -> None:
    """Check 3: ExecStart uses absolute venv path, not bare ingest-collect."""
    body = _read("digest-ingest.service")
    exec_lines = [ln for ln in body.splitlines() if ln.startswith("ExecStart=")]
    assert exec_lines, "ExecStart= missing"
    exec_line = exec_lines[0]
    assert "/opt/digest-cds/.venv/bin/ingest-collect" in exec_line
    assert "ExecStart=ingest-collect" not in body


def test_service_lock_path_via_runtime_directory() -> None:
    """Check 3b: lock is /run/digest-ingest/lock; no legacy path or chown/tmpfiles."""
    body = _read("digest-ingest.service")
    assert "/run/digest-ingest/lock" in body
    assert "/run/digest-ingest.lock" not in body
    assert "chown" not in body
    assert "tmpfiles.d" not in body


def test_timer_tokens() -> None:
    """Check 4: 15-minute OnCalendar, Persistent=false, no ExecStart."""
    body = _read("digest-ingest.timer")
    assert "OnCalendar=*:0/15" in body
    assert "Persistent=false" in body
    assert "Unit=digest-ingest.service" in body
    assert "ExecStart=" not in body


def test_alert_unit() -> None:
    """Check 5: oneshot alert distinguishes exit 1 vs 2 via the numeric MONITOR_EXIT_STATUS.

    Also pinned as check 10 (WR-04): the alert must not run as root.
    """
    body = _read("digest-ingest-alert.service")
    assert "Type=oneshot" in body
    assert "journalctl -u digest-ingest.service" in body
    assert "${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}" in body
    assert "1)" in body
    assert "2)" in body
    assert "partial failure" in body
    assert "no source could be read" in body


def test_alert_unit_does_not_read_exit_qualifier() -> None:
    """Check 5b (G-24-4): the alert reads the number, never the exited/killed qualifier.

    MONITOR_EXIT_CODE is the qualifier on systemd 255 and EXIT_CODE is unset, so
    reading either one forces every case arm into ``*)``. The positive assertion
    pins the *full nested* expression: a bare ``EXIT_STATUS:-`` substring would
    also match inside ``MONITOR_EXIT_STATUS:-``, so it cannot prove the fallback.
    """
    body = _read("digest-ingest-alert.service")
    assert "${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}" in body
    assert "MONITOR_EXIT_CODE" not in body
    assert "EXIT_CODE:-" not in body
    assert "journalctl -u digest-ingest.service" in body


def test_alert_unit_runs_unprivileged() -> None:
    """Check 10 (WR-04): alert hardening mirrors the main service."""
    body = _read("digest-ingest-alert.service")
    assert "User=digestcds" in body
    assert "Group=digestcds" in body
    assert "NoNewPrivileges=true" in body
    assert "PrivateTmp=true" in body


def test_no_secrets_in_units() -> None:
    """Check 6: credentials live only in EnvironmentFile, never in unit text."""
    bodies = _iter_unit_bodies()
    assert bodies, "no unit files under deploy/systemd"
    for path, body in bodies:
        for token in _SECRET_TOKENS:
            assert token not in body, path.name


def test_no_publish_surface_in_units() -> None:
    """Check 7: units must not reach publish/send or curl webhooks (ING-07 / D-24)."""
    bodies = _iter_unit_bodies()
    assert bodies, "no unit files under deploy/systemd"
    for path, body in bodies:
        for token in _PUBLISH_TOKENS:
            assert token not in body, path.name


def test_service_hardening() -> None:
    """Check 8: SuccessExitStatus includes 75; non-root user; TZ=UTC; NoNewPrivileges."""
    body = _read("digest-ingest.service")
    assert "SuccessExitStatus=0 75" in body
    assert "User=digestcds" in body
    assert "Group=digestcds" in body
    assert "Environment=TZ=UTC" in body
    assert "NoNewPrivileges=true" in body
    assert "PrivateTmp=true" in body


def test_runbook_4k_env_keys_exist_in_env_example() -> None:
    """Check 9: every UPPER_SNAKE= key named in §4k exists in .env.example."""
    runbook = (_REPO / "docs" / "agents" / "local-platform-runbook.md").read_text(
        encoding="utf-8"
    )
    section = _section(runbook, "4k")
    keys = sorted(set(re.findall(r"\b([A-Z][A-Z0-9_]+)=", section)))
    assert keys, "§4k must name at least one UPPER_SNAKE= key"
    example = (_REPO / "ingestion-service" / ".env.example").read_text(encoding="utf-8")
    for key in keys:
        assert f"{key}=" in example, f"{key}= missing from .env.example"


def test_runbook_and_records_name_the_oneshot_start_limit() -> None:
    """Check 11: the runbook and the phase records name the working run limit.

    The record scan is deliberately a whole-file read, not a §-slice: frontmatter
    and the checklist block count too. It lives inside pytest because the
    execution host is PowerShell, where a leading `!` is a parse error.
    """
    runbook = (_REPO / "docs" / "agents" / "local-platform-runbook.md").read_text(
        encoding="utf-8"
    )
    section_4k = _section(runbook, "4k")
    assert "TimeoutStartSec=1800" in section_4k, "§4k must name TimeoutStartSec=1800"

    section_5e = _section(runbook, "5e")
    assert "TimeoutStartSec" in section_5e, "§5e must name TimeoutStartSec"
    assert "RuntimeMaxSec" not in section_5e, "§5e must not name the inert runtime knob"
    # The recipe must prescribe a limit the probe PROVED kills before the stamp. The live
    # WSL2 probe recorded `Result=timeout` with `last_run_at` still ADVANCED at
    # `TimeoutStartSec=2` -- the unreadable-feed path finished its REST writes as the
    # timeout fired -- and a kill before the stamp only at 500ms. A 2s recipe therefore
    # cannot demonstrate what it claims to demonstrate, and would read as a regression.
    assert "TimeoutStartSec=2" not in section_5e, "§5e must not prescribe a 2s limit: 2s stamps"
    assert "TimeoutStartSec=500ms" in section_5e, "§5e must prescribe the proven 500ms limit"
    # The run-limit recipe applies a `--runtime` drop-in, so it must be self-contained: show the
    # path it removes. The alert recipe (item 8) carries the same line; before WR-05 item 5
    # pointed at a whole-unit revert instead, which is why this is pinned positively as well as
    # by the negative token ban below.
    assert (
        "rm -f /run/systemd/system/digest-ingest.service.d/override.conf" in section_5e
    ), "§5e must show how to remove the runtime drop-in"
    # The unconditional "not stamped" claim is FALSE for a kill that lands inside the shutdown
    # tail, so the qualifier is part of the contract rather than prose.
    assert (
        "when the kill lands before `stamp_last_run`" in section_5e
    ), "§5e must qualify the no-stamp claim"
    # `systemctl revert` deletes EVERY drop-in for the unit, persistent ones included -- so it
    # is not a safe cleanup for a recipe that only ever created a `--runtime` drop-in. The
    # hazard is written up in §4k (outside this slice); §5e is prescriptive only.
    assert "systemctl revert" not in section_5e, "§5e must not prescribe systemctl revert"

    for name in ("24-VERIFICATION.md", "24-PATTERNS.md", "24-VALIDATION.md"):
        body = (_PHASE_RECORDS / name).read_text(encoding="utf-8")
        assert "RuntimeMaxSec" not in body, f"{name} still asserts the inert runtime knob"


def test_runbook_and_verification_name_numeric_status() -> None:
    """Check 12 (G-24-4): the runbook and the verification record name the number, not the qualifier.

    The §5e slice is the operator recipe, so it pins the exact substitution. The
    verification-record scan is deliberately whole-file (frontmatter included):
    every record that claimed the alert distinguishes exit 1 from exit 2 must now
    name the variable that makes it true. It runs inside pytest because the
    execution host is PowerShell, where a leading `!` is a parse error.
    """
    runbook = (_REPO / "docs" / "agents" / "local-platform-runbook.md").read_text(
        encoding="utf-8"
    )
    section_5e = _section(runbook, "5e")
    assert "MONITOR_EXIT_STATUS" in section_5e, "§5e must name MONITOR_EXIT_STATUS"
    assert (
        "${MONITOR_EXIT_STATUS:-${EXIT_STATUS:-unknown}}" in section_5e
    ), "§5e must pin the full numeric substitution"
    assert "MONITOR_EXIT_CODE" not in section_5e, "§5e must not name the qualifier"

    body = (_PHASE_RECORDS / "24-VERIFICATION.md").read_text(encoding="utf-8")
    assert "MONITOR_EXIT_CODE" not in body, "24-VERIFICATION.md still names the qualifier"
