"""Authenticated material reader endpoint — ready-only by slug (MAT-01 / MAT-02)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import BaseModel, ConfigDict

from backend.application.use_cases.get_material_for_reader import get_material_for_reader
from backend.domain.auth_claims import AccessTokenClaims
from backend.domain.errors import MaterialNotFoundError, PersistenceError
from backend.domain.material import Material, MaterialStatus
from backend.interface.http.deps import get_principal

router = APIRouter(prefix="/materials", tags=["materials"])

_SLUG_PATTERN = r"^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$"
EDITOR_BYLINE = "Редакция Digest CDS"


class RelatedMaterialResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    title: str


class MaterialReaderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    title: str
    dek: str
    body_markdown: str
    format: str
    provenance: str
    tags: list[str]
    related: list[RelatedMaterialResponse]
    reading_minutes: int
    published_at: datetime | None
    editor: str = EDITOR_BYLINE


def _require_materials(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "materials", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="materials_not_configured",
        )
    return container.materials


def _related_ready(repo, material: Material) -> list[RelatedMaterialResponse]:
    """Map related ids to {slug, title} only for ready targets — never invent (D-37)."""
    related: list[RelatedMaterialResponse] = []
    for related_id in material.related_material_ids:
        try:
            mid = int(related_id)
        except ValueError:
            continue
        target = repo.get(mid)
        if target is None or target.status != MaterialStatus.READY:
            continue
        related.append(RelatedMaterialResponse(slug=target.slug, title=target.title))
    return related


def _to_response(repo, material: Material) -> MaterialReaderResponse:
    return MaterialReaderResponse(
        slug=material.slug,
        title=material.title,
        dek=material.dek,
        body_markdown=material.body_markdown,
        format=material.format,
        provenance=material.provenance_label,
        tags=[label for label, _slug in material.tags],
        related=_related_ready(repo, material),
        reading_minutes=material.reading_minutes,
        published_at=material.published_at,
        editor=EDITOR_BYLINE,
    )


@router.get(
    "/{slug}",
    response_model=MaterialReaderResponse,
    summary="Ready material by slug",
    description=(
        "Returns a ready digest material for reading. "
        "Requires Bearer JWT. Missing or draft → 404 material_not_found."
    ),
)
def read_material_by_slug(
    request: Request,
    slug: str = Path(..., pattern=_SLUG_PATTERN),
    claims: AccessTokenClaims = Depends(get_principal),
) -> MaterialReaderResponse:
    del claims
    materials = _require_materials(request)
    try:
        material = get_material_for_reader(materials, slug)
    except MaterialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="material_not_found",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="materials_unavailable",
        ) from exc
    return _to_response(materials, material)
