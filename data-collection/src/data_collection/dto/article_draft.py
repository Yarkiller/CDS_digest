"""Internal ArticleDraft — LLM output only; not public package API (D-06)."""

from pydantic import BaseModel, Field, field_validator

from data_collection.dto._body import strip_audience_section, strip_guide_section
from data_collection.dto._validators import strip_non_blank
from data_collection.dto.role_kind import RoleKind, normalize_roles
from data_collection.dto.topic_kind import TopicKind, normalize_topic_kind


class ArticleDraft(BaseModel):
    title: str = Field(min_length=1)
    dek: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)
    roles: list[RoleKind] = ["employee"]
    topic_kind: TopicKind = "conceptual"

    @field_validator("title", "dek", "body_markdown")
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        return strip_non_blank(value)

    @field_validator("body_markdown")
    @classmethod
    def _strip_audience_scaffolding(cls, value: str) -> str:
        # `## Аудитория` is prompt scaffolding for the `roles` key, not article
        # content; models sometimes leak it (as JSON or the echoed instruction).
        return strip_audience_section(value)

    @field_validator("body_markdown")
    @classmethod
    def _strip_guide_scaffolding(cls, value: str) -> str:
        # `## Гайд` is pass-2 extras furniture (KIND-03, D-09…D-12). Strip on
        # every pass-1 body, including practical drafts (D-11). Never raises.
        return strip_guide_section(value)

    @field_validator("roles", mode="before")
    @classmethod
    def _normalize_roles(cls, value: object) -> list[RoleKind]:
        return normalize_roles(value)

    @field_validator("topic_kind", mode="before")
    @classmethod
    def _normalize_topic_kind(cls, value: object) -> TopicKind:
        return normalize_topic_kind(value)
