"""ArticleGenerator port — LLM prepares ArticleDraft from Transcript (D-16)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript


class ArticleGenerator(Protocol):
    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft: ...
