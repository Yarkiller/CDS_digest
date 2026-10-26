"""Draft persist adapter errors — module-local taxonomy (D-04)."""

from __future__ import annotations

from typing import Any


class DraftPersistError(Exception):
    """Base persist failure at the adapter boundary."""

    def __init__(
        self,
        reason: str,
        *,
        video_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.reason = reason
        self.video_id = video_id
        self.context = context or {}
        super().__init__(f"persist {reason}")


class DraftPersistConflictError(DraftPersistError):
    """Unexpected unique violation or data conflict."""


class DraftPersistBatchError(DraftPersistError):
    """RPC could not create or select an unsent batch."""


class DraftPersistNetworkError(DraftPersistError):
    """Could not reach Supabase."""


class DraftPersistRpcError(DraftPersistError):
    """RPC raised a PostgREST or Postgres exception."""


class DraftPersistUnknownError(DraftPersistError):
    """Fallback persist failure."""
