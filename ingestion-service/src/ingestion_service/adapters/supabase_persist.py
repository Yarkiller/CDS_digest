"""SupabaseDraftPersister — PersistPort adapter via persist_draft_and_enqueue (D-01, D-05)."""

from __future__ import annotations

from typing import Any

import httpx
from postgrest.exceptions import APIError as PostgrestAPIError
from supabase import Client

from data_collection.dto.material_draft import MaterialDraft
from ingestion_service.adapters.persist_errors import (
    DraftPersistBatchError,
    DraftPersistConflictError,
    DraftPersistError,
    DraftPersistNetworkError,
    DraftPersistRpcError,
    DraftPersistUnknownError,
)
from ingestion_service.application.ports.persist import PersistResult

_RPC_NAME = "persist_draft_and_enqueue"
_RESULT_KEYS = ("material_id", "slug", "batch_id", "rank", "already_saved")
_CONFLICT_CODES = frozenset({"23505"})
_BATCH_CODES = frozenset({"P0001", "check_violation", "23514"})


class SupabaseDraftPersister:
    """Implements PersistPort with a single named-parameter RPC call."""

    def __init__(self, client: Client, batch_size: int) -> None:
        self._client = client
        self._batch_size = batch_size

    def persist(self, material_draft: MaterialDraft) -> PersistResult:
        params = _rpc_params(material_draft, self._batch_size)
        try:
            result = self._client.rpc(_RPC_NAME, params).execute()
            return _persist_result(result.data)
        except DraftPersistError:
            raise
        except Exception as exc:
            raise _map_exception(exc, material_draft) from None


def _rpc_params(draft: MaterialDraft, batch_size: int) -> dict[str, Any]:
    published = draft.source_published_at
    return {
        "p_title": draft.title,
        "p_dek": draft.dek,
        "p_body_markdown": draft.body_markdown,
        "p_slug": draft.slug,
        "p_reading_minutes": draft.reading_minutes,
        "p_provenance_label": draft.provenance_label,
        "p_source_url": draft.source_url,
        "p_youtube_video_id": draft.youtube_video_id,
        "p_source_author": draft.source_author,
        "p_source_published_at": published.isoformat() if published is not None else None,
        "p_roles": list(draft.roles),
        "p_batch_size": batch_size,
    }


def _persist_result(data: object) -> PersistResult:
    payload = data[0] if isinstance(data, list) and data else data
    if not isinstance(payload, dict) or any(key not in payload for key in _RESULT_KEYS):
        raise DraftPersistRpcError("rpc_error")
    return PersistResult(
        material_id=int(payload["material_id"]),
        slug=str(payload["slug"]),
        batch_id=int(payload["batch_id"]),
        rank=int(payload["rank"]),
        already_saved=bool(payload["already_saved"]),
    )


def _safe_context(draft: MaterialDraft, reason: str) -> dict[str, Any]:
    return {"slug": draft.slug, "reason": reason}


def _sdk_code(exc: BaseException) -> str | None:
    code = getattr(exc, "code", None)
    if isinstance(code, str) and code:
        return code
    return None


def _http_status_code(exc: BaseException) -> int | None:
    code = getattr(exc, "code", None)
    return code if isinstance(code, int) else None


def _is_network_error(exc: BaseException) -> bool:
    if type(exc).__name__ == "APIConnectionError":
        return True
    return isinstance(exc, (httpx.NetworkError, httpx.TimeoutException))


def _is_sdk_error(exc: BaseException) -> bool:
    if isinstance(exc, PostgrestAPIError):
        return True
    return type(exc).__name__ in {"APIError", "PostgrestAPIError"}


def _map_exception(exc: BaseException, draft: MaterialDraft) -> DraftPersistError:
    video_id = draft.youtube_video_id
    code = _sdk_code(exc)
    if _is_network_error(exc):
        return DraftPersistNetworkError(
            "network_error",
            video_id=video_id,
            context=_safe_context(draft, "network_error"),
        )
    if code in _CONFLICT_CODES:
        return DraftPersistConflictError(
            "persist_conflict",
            video_id=video_id,
            context=_safe_context(draft, "persist_conflict"),
        )
    if code in _BATCH_CODES:
        return DraftPersistBatchError(
            "batch_creation_failed",
            video_id=video_id,
            context=_safe_context(draft, "batch_creation_failed"),
        )
    # D-06: numeric HTTP gateway statuses (int code) → rpc_error, not network_error
    if _http_status_code(exc) is not None and _is_sdk_error(exc):
        return DraftPersistRpcError(
            "rpc_error",
            video_id=video_id,
            context=_safe_context(draft, "rpc_error"),
        )
    if _is_sdk_error(exc):
        return DraftPersistRpcError(
            "rpc_error",
            video_id=video_id,
            context=_safe_context(draft, "rpc_error"),
        )
    return DraftPersistUnknownError(
        "unknown_persist_error",
        video_id=video_id,
        context=_safe_context(draft, "unknown_persist_error"),
    )
