from __future__ import annotations

from datetime import datetime, timezone

from backend.application.ports.material_repository import MaterialRepository
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material


def publish_material(repo: MaterialRepository, material_id: int, *, now: datetime | None = None) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    published_at = now or datetime.now(timezone.utc)
    ready = material.as_ready(published_at)
    return repo.save(ready)
