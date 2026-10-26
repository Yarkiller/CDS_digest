"""MaterialDraft DTO — prepared article + provenance for draft persist (D-05, D-13)."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from data_collection.dto._validators import strip_non_blank
from data_collection.dto.role_kind import RoleKind, normalize_roles


class MaterialDraft(BaseModel):
    title: str = Field(min_length=1)
    dek: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    youtube_video_id: str = Field(min_length=1)
    source_author: str = Field(min_length=1)
    provenance_label: str = Field(min_length=1)
    source_published_at: datetime | None = None
    roles: list[RoleKind] = ["employee"]
    slug: str = ""
    reading_minutes: int = 1

    @field_validator(
        "title",
        "dek",
        "body_markdown",
        "source_url",
        "youtube_video_id",
        "source_author",
        "provenance_label",
    )
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        return strip_non_blank(value)

    @field_validator("source_published_at")
    @classmethod
    def _require_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("source_published_at must be timezone-aware")
        return value

    @field_validator("roles", mode="before")
    @classmethod
    def _normalize_roles(cls, value: object) -> list[RoleKind]:
        return normalize_roles(value)
