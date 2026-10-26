from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KnowledgeChunk:
    id: int
    material_id: int
    chunk_index: int
    heading: str | None
    content_md: str
    embedding: list[float]
    embedding_model_id: str
    content_sha256: str
    created_at: datetime


@dataclass(frozen=True)
class KnowledgeHit:
    material_id: int
    material_slug: str
    chunk_index: int
    snippet: str
    score: float
