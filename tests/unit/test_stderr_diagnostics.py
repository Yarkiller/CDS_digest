"""RED→GREEN: deterministic StderrDiagnostics formatting with a FakeClock (D-03, DBG-01)."""

from __future__ import annotations

import io
from collections.abc import Sequence
from datetime import datetime

from ingestion_service.adapters.stderr_diagnostics import StderrDiagnostics
from ingestion_service.tests_support.fakes import FakeClock


def _sink(
    monotonic_values: Sequence[float],
    *,
    now: datetime,
) -> tuple[StderrDiagnostics, io.StringIO]:
    stream = io.StringIO()
    clock = FakeClock(monotonic_values, now=now)
    return StderrDiagnostics(clock=clock, stream=stream), stream


def test_stage_completed_formats_exact_timestamp_and_elapsed_ms() -> None:
    """A scripted clock makes the timestamp and elapsed_ms exactly assertable."""
    sink, stream = _sink([0.0, 0.010], now=datetime(2026, 10, 4, 12, 3, 44))

    sink.stage_started("captions")
    sink.stage_completed("captions", {"video_id": "vid", "transcript_chars": 10})

    assert stream.getvalue() == (
        "[12:03:44] debug stage=captions elapsed_ms=10 "
        "video_id=vid transcript_chars=10\n"
    )


def test_control_characters_cannot_forge_extra_lines() -> None:
    """Embedded newline/ANSI escapes are stripped — exactly one output line."""
    sink, stream = _sink([0.0, 0.0], now=datetime(2026, 10, 4, 12, 3, 44))

    sink.stage_started("captions")
    sink.stage_completed("captions", {"video_id": "va\nl\x1bue"})

    output = stream.getvalue()
    assert output.count("\n") == 1
    assert "\x1b" not in output
    assert "[12:03:44] debug stage=captions elapsed_ms=0 video_id=value" in output


def test_non_allowlisted_keys_are_dropped() -> None:
    """A signal key absent from ALLOWED_KEYS never reaches the emitted line."""
    sink, stream = _sink([0.0, 0.0], now=datetime(2026, 10, 4, 12, 3, 44))

    sink.stage_started("captions")
    sink.stage_completed("captions", {"bogus_key": "leak", "video_id": "vid"})

    output = stream.getvalue()
    assert "bogus_key" not in output
    assert "leak" not in output
    assert "video_id=vid" in output
