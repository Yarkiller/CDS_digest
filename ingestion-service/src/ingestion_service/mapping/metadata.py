"""Map MetadataError → IngestError(stage=metadata) with locked reasons (D-23, D-25, D-13)."""

from __future__ import annotations

from typing import Any

from data_collection.errors.metadata import (
    MetadataError,
    MetadataInvalidResponse,
    MetadataNetworkError,
    MetadataUnavailable,
)
from ingestion_service.domain.errors import IngestError

METADATA_REASONS: frozenset[str] = frozenset(
    {
        "metadata_unavailable",
        "network_error",
        "metadata_invalid_response",
    }
)

_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "video_id",
        "status_code",
        "exception_class",
    }
)

_REASON_BY_TYPE: dict[type[MetadataError], str] = {
    MetadataUnavailable: "metadata_unavailable",
    MetadataNetworkError: "network_error",
    MetadataInvalidResponse: "metadata_invalid_response",
}


def _forward_context(error: MetadataError) -> dict[str, Any]:
    forwarded: dict[str, Any] = {"video_id": error.video_id}
    raw = dict(error.context)
    for key in _CONTEXT_ALLOWLIST:
        if key == "video_id":
            continue
        if key in raw:
            forwarded[key] = raw[key]
    return forwarded


def map_metadata_error(error: MetadataError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "metadata_unavailable")
    return IngestError(
        stage="metadata",
        reason=reason,
        message=f"metadata {reason} for {error.video_id}",
        context=_forward_context(error),
    )
