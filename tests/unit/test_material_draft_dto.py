"""RED→GREEN: MaterialDraft DTO (D-05, D-13, DTO-01)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


def _valid_kwargs(**overrides: object) -> dict:
    base: dict = {
        "title": "RAG for audit",
        "dek": "Как искать по регламентам СВА.",
        "body_markdown": "# Intro\n\nBody",
        "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube_video_id": "dQw4w9WgXcQ",
        "source_author": "Rick Astley",
        "provenance_label": "YouTube · Rick Astley",
    }
    base.update(overrides)
    return base


def test_material_draft_constructs_required_fields() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    dto = MaterialDraft(**_valid_kwargs())
    assert dto.title == "RAG for audit"
    assert dto.dek == "Как искать по регламентам СВА."
    assert dto.body_markdown == "# Intro\n\nBody"
    assert dto.source_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert dto.youtube_video_id == "dQw4w9WgXcQ"
    assert dto.source_author == "Rick Astley"
    assert dto.provenance_label == "YouTube · Rick Astley"
    assert dto.source_published_at is None


def test_material_draft_source_published_at_optional() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    published = datetime(2009, 10, 25, tzinfo=timezone.utc)
    dto = MaterialDraft(**_valid_kwargs(source_published_at=published))
    assert dto.source_published_at == published


def test_material_draft_rejects_naive_source_published_at() -> None:
    """WR-03: provenance source_published_at must be timezone-aware (D-14 / PERS-01)."""
    from data_collection.dto.material_draft import MaterialDraft

    with pytest.raises(ValidationError):
        MaterialDraft(**_valid_kwargs(source_published_at=datetime(2009, 10, 25)))


def test_material_draft_source_published_at_none_constructs() -> None:
    """DTO-01 nullable: explicit source_published_at=None succeeds (D-13, D-14)."""
    from data_collection.dto.material_draft import MaterialDraft

    dto = MaterialDraft(**_valid_kwargs(source_published_at=None))
    assert dto.source_published_at is None


def test_material_draft_has_no_tags_role_hints_or_model_id() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    MaterialDraft(**_valid_kwargs())
    fields = MaterialDraft.model_fields
    assert "tags" not in fields
    assert "role_hints" not in fields
    assert "model_id" not in fields


@pytest.mark.parametrize(
    "missing_field",
    [
        "title",
        "dek",
        "body_markdown",
        "source_url",
        "youtube_video_id",
        "source_author",
        "provenance_label",
    ],
)
def test_material_draft_rejects_missing_required_field(missing_field: str) -> None:
    from data_collection.dto.material_draft import MaterialDraft

    kwargs = _valid_kwargs()
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        MaterialDraft(**kwargs)


@pytest.mark.parametrize("blank_field", ["title", "provenance_label"])
def test_material_draft_rejects_blank_provenance_and_title(blank_field: str) -> None:
    """DTO-01 empty probe: blank provenance_label/title rejected (D-05)."""
    from data_collection.dto.material_draft import MaterialDraft

    with pytest.raises(ValidationError):
        MaterialDraft(**_valid_kwargs(**{blank_field: "   "}))
