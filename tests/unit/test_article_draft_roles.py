"""RED→GREEN: ArticleDraft.roles closed set + fallback (PERS-01, D-14)."""

from __future__ import annotations

import importlib.resources


def test_article_draft_keeps_valid_roles() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    draft = ArticleDraft.model_validate(
        {
            "title": "t",
            "dek": "d",
            "body_markdown": "b",
            "roles": ["employee", "analyst"],
        }
    )
    assert draft.roles == ["employee", "analyst"]


def test_article_draft_filters_unknown_roles() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    draft = ArticleDraft.model_validate(
        {
            "title": "t",
            "dek": "d",
            "body_markdown": "b",
            "roles": ["manager", "employee"],
        }
    )
    assert draft.roles == ["employee"]


def test_article_draft_missing_roles_falls_back_to_employee() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    draft = ArticleDraft.model_validate(
        {"title": "t", "dek": "d", "body_markdown": "b"}
    )
    assert draft.roles == ["employee"]


def test_article_draft_empty_roles_falls_back_to_employee() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    draft = ArticleDraft.model_validate(
        {"title": "t", "dek": "d", "body_markdown": "b", "roles": []}
    )
    assert draft.roles == ["employee"]


def test_article_draft_constructor_normalization() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    assert ArticleDraft(
        title="t", dek="d", body_markdown="b", roles=["employee", "analyst"]
    ).roles == ["employee", "analyst"]
    assert ArticleDraft(
        title="t", dek="d", body_markdown="b", roles=["manager", "employee"]
    ).roles == ["employee"]
    assert ArticleDraft(title="t", dek="d", body_markdown="b").roles == ["employee"]


def test_lecture_and_podcast_templates_ask_for_role_json_array() -> None:
    root = importlib.resources.files("data_collection.templates")
    for name in ("lecture.md", "podcast.md"):
        text = root.joinpath(name).read_text(encoding="utf-8")
        assert "employee" in text
        assert "analyst" in text
        assert "ds" in text
        assert "JSON array" in text
