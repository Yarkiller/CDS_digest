"""HealthProbe port — readiness checks for external dependencies (monitoring)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ComponentHealth:
    """Result of probing a single dependency (database, storage, external API)."""

    name: str
    healthy: bool
    detail: str = ""


class HealthProbe(Protocol):
    """A named readiness check. Implementations live in adapters, never in use-cases."""

    name: str

    def check(self) -> ComponentHealth: ...
