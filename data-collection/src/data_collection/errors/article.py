"""Article adapter errors — module-local taxonomy only (D-13)."""

from __future__ import annotations

from typing import Any


class ArticleError(Exception):
    """Base article-generation failure at the adapter boundary."""

    def __init__(self, video_id: str, **context: Any) -> None:
        self.video_id = video_id
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)
        super().__init__(f"article error for {video_id}")


class ArticleNetworkError(ArticleError):
    """Timeout, DNS, or connection failure before a DeepSeek response."""


class ArticleProviderError(ArticleError):
    """HTTP 5xx or 429 from DeepSeek."""


class ArticleAuthError(ArticleError):
    """HTTP 401 or 403 from DeepSeek."""


class ArticleContextLengthError(ArticleError):
    """HTTP 400 context-length rejection from DeepSeek (D-10)."""


class ArticleInvalidJson(ArticleError):
    """Response content is not a JSON object (D-11)."""


class ArticleInvalidDraft(ArticleError):
    """JSON object does not validate as ArticleDraft (D-11)."""


class ArticleUnknownError(ArticleError):
    """Any other SDK or HTTP failure, including HTTP 402."""


class ArticleBudgetError(ArticleError):
    """Transcript exceeds the injected character cap (D-08); raised in 08-03."""
