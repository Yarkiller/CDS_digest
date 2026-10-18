"""VideoMetadata DTO — YouTube provenance fields (D-11)."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from data_collection.dto._validators import strip_non_blank


class VideoMetadata(BaseModel):
    video_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    author: str = Field(min_length=1)
    published_at: datetime | None = None

    @field_validator("video_id", "source_url", "author")
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        return strip_non_blank(value)

    @field_validator("published_at")
    @classmethod
    def _require_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("published_at must be timezone-aware")
        return value
