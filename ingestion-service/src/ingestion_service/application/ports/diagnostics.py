"""StageDiagnostics + Clock ports for opt-in CLI diagnostics (D-01…D-13, DBG-01).

The use-case depends only on these ``typing.Protocol`` ports; it never imports
``time``, ``sys``, ``typer``, or ``datetime``. No ``Any`` crosses the boundary.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol, runtime_checkable

DebugValue = str | int | float | bool


@runtime_checkable
class Clock(Protocol):
    def monotonic(self) -> float: ...

    def now(self) -> datetime: ...


@runtime_checkable
class StageDiagnostics(Protocol):
    def stage_started(self, stage: str) -> None: ...

    def stage_completed(self, stage: str, signals: Mapping[str, DebugValue]) -> None: ...

    def stage_failed(self, stage: str, *, reason: str, exit_code: int) -> None: ...

    def config_error(self, *, error_type: str, message: str) -> None: ...


class NullDiagnostics:
    """D-13: true no-op — zero debug output when ``--debug`` is off."""

    def stage_started(self, stage: str) -> None: ...

    def stage_completed(self, stage: str, signals: Mapping[str, DebugValue]) -> None: ...

    def stage_failed(self, stage: str, *, reason: str, exit_code: int) -> None: ...

    def config_error(self, *, error_type: str, message: str) -> None: ...
