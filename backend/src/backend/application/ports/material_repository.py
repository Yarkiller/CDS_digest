from __future__ import annotations

from typing import Protocol

from backend.domain.material import Material


class MaterialRepository(Protocol):
    def get(self, material_id: int) -> Material | None: ...

    def get_by_slug(self, slug: str) -> Material | None: ...

    def save(self, material: Material) -> Material: ...
