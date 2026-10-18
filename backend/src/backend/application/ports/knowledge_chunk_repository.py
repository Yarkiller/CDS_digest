from __future__ import annotations

from typing import Protocol

from backend.domain.knowledge import KnowledgeChunk, KnowledgeHit


class KnowledgeChunkRepository(Protocol):
    def replace_for_material(self, material_id: int, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]: ...

    def list_all(self) -> list[KnowledgeChunk]: ...

    def search(
        self,
        *,
        query_embedding: list[float],
        query_text: str,
        role_filter: str | None,
        limit: int,
        offset: int,
    ) -> list[KnowledgeHit]: ...
