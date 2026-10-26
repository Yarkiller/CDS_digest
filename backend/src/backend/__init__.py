"""Backend public surface — domain and application entrypoints."""

from backend.domain.errors import (
    MaterialNotFoundError,
    MaterialNotReadyError,
    MaterialValidationError,
)
from backend.domain.knowledge import KnowledgeChunk, KnowledgeHit
from backend.domain.material import Material, MaterialStatus

__all__ = [
    "KnowledgeChunk",
    "KnowledgeHit",
    "Material",
    "MaterialNotFoundError",
    "MaterialNotReadyError",
    "MaterialStatus",
    "MaterialValidationError",
]
