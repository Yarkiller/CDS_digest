"""Query embedding port — application boundary for search vectors."""

from __future__ import annotations

import hashlib
from typing import Protocol

EMBEDDING_DIM = 1024


class QueryEmbedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class StubQueryEmbedder:
    """Deterministic length-1024 embedder for Phase 4 (RESEARCH Q1 RESOLVED).

    No FoundryModels HTTP client this phase — honesty path uses seeded vectors
    that match this stub's algorithm in unit/demo fixtures.
    """

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Map 32 digest bytes into a unit-ish float vector; pad to 1024 dims.
        base = [((b / 255.0) * 2.0 - 1.0) for b in digest]
        vec = (base * ((EMBEDDING_DIM // len(base)) + 1))[:EMBEDDING_DIM]
        return [float(x) for x in vec]
