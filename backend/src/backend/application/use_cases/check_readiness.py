"""Readiness aggregation use-case — pure, no infrastructure imports."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from backend.application.ports.health_probe import ComponentHealth, HealthProbe


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    components: tuple[ComponentHealth, ...]

    def to_dict(self) -> dict:
        return {
            "status": "ready" if self.ready else "not_ready",
            "components": {
                component.name: {
                    "healthy": component.healthy,
                    "detail": component.detail,
                }
                for component in self.components
            },
        }

    def to_public_dict(self) -> dict:
        """HTTP-safe view: never expose dependency error details (security).

        Connection strings / SDK errors are useful in logs, not to anonymous callers.
        """
        return {
            "status": "ready" if self.ready else "not_ready",
            "components": {
                component.name: {
                    "healthy": component.healthy,
                    "detail": "ok" if component.healthy else "unhealthy",
                }
                for component in self.components
            },
        }


def check_readiness(probes: Sequence[HealthProbe]) -> ReadinessReport:
    """Run every probe; a probe that raises is reported as unhealthy (never propagates)."""
    components: list[ComponentHealth] = []
    for probe in probes:
        try:
            components.append(probe.check())
        except Exception as exc:  # noqa: BLE001 — any probe failure means "not ready"
            name = getattr(probe, "name", "probe")
            components.append(ComponentHealth(name=name, healthy=False, detail=str(exc)))
    return ReadinessReport(
        ready=all(component.healthy for component in components),
        components=tuple(components),
    )
