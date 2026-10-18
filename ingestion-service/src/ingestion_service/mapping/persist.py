"""Map DraftPersistError → IngestError(stage=persist) with locked reasons (D-04)."""

from __future__ import annotations

from typing import Any

from ingestion_service.adapters.persist_errors import (
    DraftPersistBatchError,
    DraftPersistConflictError,
    DraftPersistError,
    DraftPersistNetworkError,
    DraftPersistRpcError,
)
from ingestion_service.domain.errors import IngestError

PERSIST_REASONS: frozenset[str] = frozenset(
    {
        "persist_conflict",
        "batch_creation_failed",
        "rpc_error",
        "network_error",
        "unknown_persist_error",
    }
)

_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "video_id",
        "slug",
        "batch_id",
        "reason",
    }
)

_REASON_BY_TYPE: dict[type[DraftPersistError], str] = {
    DraftPersistConflictError: "persist_conflict",
    DraftPersistBatchError: "batch_creation_failed",
    DraftPersistNetworkError: "network_error",
    DraftPersistRpcError: "rpc_error",
}


def _forward_context(error: DraftPersistError) -> dict[str, Any]:
    forwarded: dict[str, Any] = {}
    if error.video_id is not None:
        forwarded["video_id"] = error.video_id
    raw = dict(error.context)
    for key in _CONTEXT_ALLOWLIST:
        if key == "video_id" and key in forwarded:
            continue
        if key in raw:
            forwarded[key] = raw[key]
    return forwarded


def map_persist_error(error: DraftPersistError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "unknown_persist_error")
    return IngestError(
        stage="persist",
        reason=reason,
        message=f"persist {reason}",
        context=_forward_context(error),
    )
