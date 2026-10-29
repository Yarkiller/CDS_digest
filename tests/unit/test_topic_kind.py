"""RED→GREEN: topic_kind closed set + KIND-02 conceptual default."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


def _material_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "title": "t",
        "dek": "d",
        "body_markdown": "b",
        "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube_video_id": "dQw4w9WgXcQ",
        "source_author": "Author",
        "provenance_label": "YouTube · Author",
    }
    base.update(overrides)
    return base


def test_normalize_topic_kind_keeps_practical_and_conceptual() -> None:
    from data_collection.dto.topic_kind import normalize_topic_kind

    assert normalize_topic_kind("practical") == "practical"
    assert normalize_topic_kind("conceptual") == "conceptual"
    assert normalize_topic_kind(" Practical ") == "practical"
    assert normalize_topic_kind("CONCEPTUAL") == "conceptual"


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "   ",
        "unsure",
        "howto",
        "cherry",
        1,
        True,
        {"kind": "practical"},
        {"topic_kind": "practical"},
        [],
    ],
)
def test_normalize_topic_kind_garbage_is_conceptual(raw: object) -> None:
    from data_collection.dto.topic_kind import normalize_topic_kind

    assert normalize_topic_kind(raw) == "conceptual"


def test_article_draft_keeps_valid_topic_kind() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    practical = ArticleDraft.model_validate(
        {"title": "t", "dek": "d", "body_markdown": "b", "topic_kind": "practical"}
    )
    conceptual = ArticleDraft.model_validate(
        {"title": "t", "dek": "d", "body_markdown": "b", "topic_kind": "conceptual"}
    )
    stripped = ArticleDraft.model_validate(
        {"title": "t", "dek": "d", "body_markdown": "b", "topic_kind": " Practical "}
    )
    assert practical.topic_kind == "practical"
    assert conceptual.topic_kind == "conceptual"
    assert stripped.topic_kind == "practical"


def test_article_draft_missing_topic_kind_defaults_conceptual() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    draft = ArticleDraft.model_validate({"title": "t", "dek": "d", "body_markdown": "b"})
    assert draft.topic_kind == "conceptual"


def test_article_draft_empty_none_and_non_string_topic_kind_are_conceptual() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    for raw in (None, "", {"kind": "practical"}, ["practical"]):
        draft = ArticleDraft.model_validate(
            {"title": "t", "dek": "d", "body_markdown": "b", "topic_kind": raw}
        )
        assert draft.topic_kind == "conceptual"


def test_article_draft_garbage_topic_kind_does_not_raise_validation_error() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    try:
        draft = ArticleDraft.model_validate(
            {"title": "t", "dek": "d", "body_markdown": "b", "topic_kind": "cherry"}
        )
    except ValidationError as err:
        raise AssertionError("KIND-02 forbids ValidationError on garbage topic_kind") from err
    assert draft.topic_kind == "conceptual"


def test_article_draft_constructor_normalization() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    assert (
        ArticleDraft(title="t", dek="d", body_markdown="b", topic_kind="practical").topic_kind
        == "practical"
    )
    assert ArticleDraft(title="t", dek="d", body_markdown="b").topic_kind == "conceptual"
    assert (
        ArticleDraft(title="t", dek="d", body_markdown="b", topic_kind="unsure").topic_kind
        == "conceptual"
    )


def test_material_draft_keeps_valid_topic_kind() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    draft = MaterialDraft.model_validate(_material_kwargs(topic_kind="practical"))
    assert draft.topic_kind == "practical"


def test_material_draft_missing_topic_kind_defaults_conceptual() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    draft = MaterialDraft.model_validate(_material_kwargs())
    assert draft.topic_kind == "conceptual"


def test_material_draft_garbage_topic_kind_does_not_raise_validation_error() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    try:
        draft = MaterialDraft.model_validate(_material_kwargs(topic_kind="cherry"))
    except ValidationError as err:
        raise AssertionError("KIND-02 forbids ValidationError on garbage topic_kind") from err
    assert draft.topic_kind == "conceptual"


def test_material_draft_constructor_normalization() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    assert MaterialDraft(**_material_kwargs(topic_kind="conceptual")).topic_kind == "conceptual"
    assert MaterialDraft(**_material_kwargs(topic_kind="unsure")).topic_kind == "conceptual"
    assert MaterialDraft(**_material_kwargs()).topic_kind == "conceptual"
