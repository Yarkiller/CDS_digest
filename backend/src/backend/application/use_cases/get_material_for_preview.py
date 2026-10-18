"""Load a draft material by slug for the admin preview — ready/missing → not found (D-04/D-12)."""

from __future__ import annotations

from backend.application.ports.material_repository import MaterialRepository
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material, MaterialStatus


def get_material_for_preview(repo: MaterialRepository, slug: str) -> Material:
    """Draft-only admin read (D-04): any other status is not previewable (D-12 → 404)."""
    material = repo.get_by_slug(slug)
    if material is None or material.status != MaterialStatus.DRAFT:
        raise MaterialNotFoundError(slug)
    return material
