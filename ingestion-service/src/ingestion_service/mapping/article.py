"""Map ArticleError → IngestError(stage=llm) with locked reasons (D-13)."""

from __future__ import annotations

from typing import Any

from data_collection.errors.article import (
    ArticleAuthError,
    ArticleBudgetError,
    ArticleContextLengthError,
    ArticleError,
    ArticleInvalidDraft,
    ArticleInvalidJson,
    ArticleNetworkError,
    ArticleProviderError,
    ArticleUnknownError,
)
from ingestion_service.domain.errors import IngestError

LLM_REASONS: frozenset[str] = frozenset(
    {
        "network_error",
        "provider_error",
        "auth_error",
        "invalid_json",
        "invalid_article_draft",
        "provider_context_length",
        "unknown_llm_error",
    }
)

_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "video_id",
        "exception_class",
        "status_code",
    }
)

_REASON_BY_TYPE: dict[type[ArticleError], str] = {
    ArticleNetworkError: "network_error",
    ArticleProviderError: "provider_error",
    ArticleAuthError: "auth_error",
    ArticleInvalidJson: "invalid_json",
    ArticleInvalidDraft: "invalid_article_draft",
    ArticleContextLengthError: "provider_context_length",
}


def _forward_context(error: ArticleError) -> dict[str, Any]:
    forwarded: dict[str, Any] = {"video_id": error.video_id}
    raw = dict(error.context)
    for key in _CONTEXT_ALLOWLIST:
        if key == "video_id":
            continue
        if key in raw:
            forwarded[key] = raw[key]
    return forwarded


def map_article_error(error: ArticleError) -> IngestError:
    if isinstance(error, ArticleBudgetError):
        return IngestError(
            stage="llm_truncation",
            reason="transcript_too_long",
            message="llm_truncation transcript_too_long",
            context={
                "char_count": error.context["char_count"],
                "max_chars": error.context["max_chars"],
            },
        )
    reason = _REASON_BY_TYPE.get(type(error), "unknown_llm_error")
    return IngestError(
        stage="llm",
        reason=reason,
        message=f"llm {reason}",
        context=_forward_context(error),
    )
