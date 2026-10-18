"""Authenticated knowledge search — JWT-gated, score omitted (KNOW-01 / D-59 / D-61)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict

from backend.application.use_cases.search_knowledge import DEFAULT_SEARCH_LIMIT
from backend.domain.auth_claims import AccessTokenClaims
from backend.domain.errors import KnowledgeQueryValidationError, PersistenceError
from backend.domain.knowledge import KnowledgeHit
from backend.domain.material import Material
from backend.interface.http.deps import get_principal

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeHitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    title: str
    snippet: str
    tags: list[str]
    cover_url: str | None = None
    roles: list[str]


class KnowledgeSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[KnowledgeHitResponse]
    has_more: bool
    limit: int
    offset: int


def _require_container(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "chunks", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="knowledge_not_configured",
        )
    if getattr(container, "embedder", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="knowledge_not_configured",
        )
    return container


def _to_item(material: Material | None, hit: KnowledgeHit) -> KnowledgeHitResponse:
    title = material.title if material is not None else hit.material_slug
    tags = [label for label, _slug in material.tags] if material is not None else []
    roles = list(material.roles) if material is not None else []
    return KnowledgeHitResponse(
        slug=hit.material_slug,
        title=title,
        snippet=hit.snippet,
        tags=tags,
        cover_url=None,
        roles=roles,
    )


@router.get(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Semantic knowledge search",
    description=(
        "Hybrid search over ready materials. Requires Bearer JWT. "
        "Omits relevance scores from JSON (D-59). Default limit=10 with has_more (D-61). "
        "role allowlist: analyst | ds; omit or empty is unrestricted (KNOW-02 / D-62). "
        "Any other role is 400 invalid_role (T-04-05)."
    ),
)
def search_knowledge_http(
    request: Request,
    q: str = Query(default=""),
    role: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_SEARCH_LIMIT, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    claims: AccessTokenClaims = Depends(get_principal),
) -> KnowledgeSearchResponse:
    del claims
    container = _require_container(request)
    try:
        # Fetch limit+1 to compute has_more without a separate count query.
        raw = container.search(
            query_text=q,
            role_filter=role,
            limit=limit + 1,
            offset=offset,
        )
    except KnowledgeQueryValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.code,
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="knowledge_unavailable",
        ) from exc

    has_more = len(raw) > limit
    page = raw[:limit]
    items: list[KnowledgeHitResponse] = []
    for hit in page:
        material = container.materials.get(hit.material_id)
        items.append(_to_item(material, hit))

    return KnowledgeSearchResponse(
        items=items,
        has_more=has_more,
        limit=limit,
        offset=offset,
    )
