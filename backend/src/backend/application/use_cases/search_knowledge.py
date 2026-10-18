from __future__ import annotations

from backend.application.ports.knowledge_chunk_repository import KnowledgeChunkRepository
from backend.domain.errors import KnowledgeQueryValidationError
from backend.domain.knowledge import KnowledgeHit

MAX_QUERY_CODE_POINTS = 500  # Unicode code points; HTTP 400 query_too_long when exceeded
DEFAULT_SEARCH_LIMIT = 10
# Chip values only (D-62). materials.roles may also contain sva — that is not a filter.
ROLE_FILTER_ALLOWLIST = frozenset({"analyst", "ds"})


def normalize_role_filter(role_filter: str | None) -> str | None:
    """Map role query to analyst|ds or None («Все»).

    Null/empty/whitespace means unrestricted (KNOW-02). Any other string is
    invalid_role (T-04-05) — never a silent empty result set.
    """
    if role_filter is None:
        return None
    cleaned = role_filter.strip()
    if not cleaned:
        return None
    if cleaned not in ROLE_FILTER_ALLOWLIST:
        raise KnowledgeQueryValidationError("invalid_role")
    return cleaned


def search_knowledge(
    *,
    chunks: KnowledgeChunkRepository,
    query_embedding: list[float],
    query_text: str,
    role_filter: str | None,
    limit: int = DEFAULT_SEARCH_LIMIT,
    offset: int = 0,
) -> list[KnowledgeHit]:
    """Hybrid knowledge search via chunk repository (KNOW-01 / D-59 / D-61 / D-62).

    Blank/whitespace queries raise KnowledgeQueryValidationError before search.
    Role allowlist is analyst|ds; empty role is unrestricted (KNOW-02 / T-04-05).
    Ranking scores stay on KnowledgeHit for server-side ordering only.
    """
    q = (query_text or "").strip()
    if not q:
        raise KnowledgeQueryValidationError("empty_query")
    if len(q) > MAX_QUERY_CODE_POINTS:
        raise KnowledgeQueryValidationError("query_too_long")
    role = normalize_role_filter(role_filter)

    if limit < 1:
        limit = DEFAULT_SEARCH_LIMIT
    if offset < 0:
        offset = 0

    return chunks.search(
        query_embedding=query_embedding,
        query_text=q,
        role_filter=role,
        limit=limit,
        offset=offset,
    )
