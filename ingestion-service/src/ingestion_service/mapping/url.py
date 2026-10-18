"""Map InvalidYouTubeUrl → IngestError(stage=url) (D-05, D-11)."""

from __future__ import annotations

from typing import Any

from ingestion_service.domain.errors import IngestError
from ingestion_service.url import InvalidYouTubeUrl

_CONTEXT_ALLOWLIST: frozenset[str] = frozenset({"value", "candidate"})


def _forward_context(error: InvalidYouTubeUrl) -> dict[str, Any]:
    raw = dict(error.context)
    return {key: raw[key] for key in _CONTEXT_ALLOWLIST if key in raw}


def map_url_error(error: InvalidYouTubeUrl) -> IngestError:
    return IngestError(
        stage="url",
        reason=error.reason,
        message=f"url {error.reason}",
        context=_forward_context(error),
    )
