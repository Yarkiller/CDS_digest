"""TopicKindClassifier port — cheap classify of practical | conceptual (KIND-01)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.transcript import Transcript


class TopicKindClassifier(Protocol):
    async def classify(self, transcript: Transcript, article: ArticleDraft) -> object: ...
