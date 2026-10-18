"""RED→GREEN: TemplateKind closed Enum (D-10, DTO-01)."""

import pytest


def test_template_kind_lecture_and_podcast_only() -> None:
    from data_collection.dto.template_kind import TemplateKind

    assert TemplateKind.LECTURE == "lecture"
    assert TemplateKind.LECTURE.value == "lecture"
    assert TemplateKind.PODCAST == "podcast"
    assert TemplateKind.PODCAST.value == "podcast"
    assert {m.value for m in TemplateKind} == {"lecture", "podcast"}


def test_template_kind_rejects_unknown_member() -> None:
    from data_collection.dto.template_kind import TemplateKind

    with pytest.raises(ValueError):
        TemplateKind("webinar")

    with pytest.raises(ValueError):
        TemplateKind("LECTURE")
