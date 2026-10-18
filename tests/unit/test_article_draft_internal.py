"""RED→GREEN: internal ArticleDraft (D-06) — title/dek/body only."""

import pytest
from pydantic import ValidationError


def test_article_draft_constructs_article_fields_only() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    draft = ArticleDraft(
        title="RAG for audit",
        dek="Как искать по регламентам СВА.",
        body_markdown="# Intro\n\nBody",
    )
    assert draft.title == "RAG for audit"
    assert draft.dek == "Как искать по регламентам СВА."
    assert draft.body_markdown == "# Intro\n\nBody"
    assert set(ArticleDraft.model_fields) == {"title", "dek", "body_markdown", "roles"}
    assert draft.roles == ["employee"]


@pytest.mark.parametrize("field", ["title", "dek", "body_markdown"])
def test_article_draft_rejects_blank_required_strings(field: str) -> None:
    """D-06: blank title/dek/body_markdown rejected like MaterialDraft (DTO-01)."""
    from data_collection.dto.article_draft import ArticleDraft

    kwargs = {
        "title": "RAG for audit",
        "dek": "Как искать по регламентам СВА.",
        "body_markdown": "# Intro\n\nBody",
    }
    kwargs[field] = "   "
    with pytest.raises(ValidationError):
        ArticleDraft(**kwargs)
