"""Record a platform proof ping via PingRecorder (ports only)."""

from __future__ import annotations

from backend.application.ports.ping_recorder import PingRecorder

PLATFORM_PING_KIND = "platform_ping"


def record_platform_ping(pings: PingRecorder, user_id: str | None) -> str:
    return pings.record(user_id=user_id, kind=PLATFORM_PING_KIND, payload={})
