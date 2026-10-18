"""UtcClock — aware UTC now() for collect due-gate (ING-06, D-22)."""

from __future__ import annotations

import time
from datetime import datetime, timezone


class UtcClock:
    """Production Clock with timezone-aware UTC ``now()`` (unlike SystemClock)."""

    def monotonic(self) -> float:
        return time.monotonic()

    def now(self) -> datetime:
        return datetime.now(timezone.utc)
