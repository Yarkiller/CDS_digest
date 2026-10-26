from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from backend.domain.errors import MaterialValidationError


class MaterialStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"


@dataclass(frozen=True)
class Material:
    id: int
    slug: str
    title: str
    dek: str
    body_markdown: str
    format: str
    status: MaterialStatus
    reading_minutes: int
    provenance_label: str
    source_id: int | None
    roles: tuple[str, ...]
    tags: tuple[tuple[str, str], ...]
    related_material_ids: tuple[str, ...]
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def assert_publishable(self) -> None:
        if not self.title.strip():
            raise MaterialValidationError("title is required")
        if not self.body_markdown.strip():
            raise MaterialValidationError("body is required")
        if not self.provenance_label.strip():
            raise MaterialValidationError("provenance is required")
        if self.format != "статья":
            raise MaterialValidationError("format must be статья")

    def as_ready(self, published_at: datetime) -> Material:
        self.assert_publishable()
        return replace(self, status=MaterialStatus.READY, published_at=published_at, updated_at=published_at)

    def with_ready_status(self, *, now: datetime) -> Material:
        """Triage ready (ADUX-05 / D-06): flip draft→ready without publish gate or published_at."""
        if self.status == MaterialStatus.READY:
            return self
        return replace(self, status=MaterialStatus.READY, updated_at=now)
