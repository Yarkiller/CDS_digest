"""PingRecorder port — persist platform proof mutations (D-10 / PLAT-04)."""

from __future__ import annotations

from typing import Protocol


class PingRecorder(Protocol):
    def record(
        self,
        *,
        user_id: str | None,
        kind: str,
        payload: dict,
    ) -> str: ...
