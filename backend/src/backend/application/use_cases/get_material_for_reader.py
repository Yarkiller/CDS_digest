"""Load a ready material by slug for the reader — draft/missing → not found."""

from __future__ import annotations

from backend.application.ports.material_repository import MaterialRepository
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material, MaterialStatus


def get_material_for_reader(repo: MaterialRepository, slug: str) -> Material:
    material = repo.get_by_slug(slug)
    if material is None or material.status != MaterialStatus.READY:
        raise MaterialNotFoundError(slug)
    return material
