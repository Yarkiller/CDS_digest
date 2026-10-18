"""Feed adapter errors — module-local taxonomy only (D-25, D-26)."""

from __future__ import annotations

from typing import Any


class FeedError(Exception):
    """Base feed failure at the adapter boundary."""

    def __init__(self, source_id: str, *, reason: str, **context: Any) -> None:
        self.source_id = source_id
        self.reason = reason
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)
        super().__init__(f"feed error for {source_id}: {reason}")
