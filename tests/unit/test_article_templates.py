"""RED→GREEN: pass-1 templates carry the content-shaped frame (ART-01/ART-02/ART-03, D-01…D-19)."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import pytest

from data_collection.dto.template_kind import TemplateKind

LEGACY_LECTURE_HEADINGS = ("## Тезис", "## Ход рассуждения", "## Вывод")
LEGACY_PODCAST_HEADINGS = ("## О чём разговор", "## Позиции", "## Что запомнить")
SHARED_HEADINGS = ("## Конкретика", "## Зачем это СВА", "## Аудитория")


def _template_text(kind: str) -> str:
    root = importlib.resources.files("data_collection.templates")
    return root.joinpath(f"{kind}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("heading", LEGACY_LECTURE_HEADINGS)
def test_lecture_md_omits_legacy_scaffold(heading: str) -> None:
    assert heading not in _template_text("lecture")


@pytest.mark.parametrize("heading", SHARED_HEADINGS)
def test_lecture_md_carries_the_shared_frame(heading: str) -> None:
    assert heading in _template_text("lecture")


def test_lecture_md_names_the_topics_frame() -> None:
    text = _template_text("lecture")
    assert "single speaker's argument" in text
    assert "implicit editorial chapters" in text
    assert "no fixed count" in text
    assert "do not add facts" not in text
    assert "definitions of hard terms" in text
    assert "footnotes" in text
    assert "reference data" in text
    assert "**bold**" in text
    assert "markdown blockquote" in text


def test_lecture_md_states_the_concretika_rules() -> None:
    text = _template_text("lecture")
    assert "## Конкретика" in text
    assert "interesting" in text
    assert "explanatory" in text
    assert "inventory" in text
    assert "**item** —" in text
    assert "explicit grid of numbers" in text
    assert "PostgreSQL" in text
    assert "never invent a version" in text
    assert "Omit the section entirely" in text
    assert "footnote" in text


def test_lecture_md_states_the_sva_rules() -> None:
    text = _template_text("lecture")
    assert "## Зачем это СВА" in text
    assert "working analog for СВА" in text
    assert "information security" in text
    assert "Do not invent a duty" in text
    assert "Omit the section when there is no such analog" in text


def test_lecture_md_has_only_the_intended_headings() -> None:
    text = _template_text("lecture")
    headings = [line for line in text.splitlines() if line.startswith("#")]
    assert set(headings) == set(SHARED_HEADINGS)


def test_lecture_md_keeps_the_audience_block_last() -> None:
    text = _template_text("lecture")
    headings = [line for line in text.splitlines() if line.startswith("#")]
    assert headings[-1] == "## Аудитория"
    assert text.rstrip().endswith("employee, analyst, ds.")
    assert not any(line.startswith("# ") for line in text.splitlines())


@pytest.mark.parametrize("heading", LEGACY_PODCAST_HEADINGS)
def test_podcast_md_omits_legacy_scaffold(heading: str) -> None:
    assert heading not in _template_text("podcast")


@pytest.mark.parametrize("heading", SHARED_HEADINGS)
def test_podcast_md_carries_the_shared_frame(heading: str) -> None:
    assert heading in _template_text("podcast")


def test_podcast_md_names_the_dialogue_frame() -> None:
    text = _template_text("podcast")
    assert "when it is not a dialogue" in text
    assert "positions of its participants" in text
    assert "Structure the conversation by positions of its participants" not in text
    assert "follow the topics of the conversation" in text
    assert "implicit editorial chapters" in text
    assert "no fixed count" in text
    assert "do not add facts" not in text
    assert "definitions of hard terms" in text
    assert "footnotes" in text
    assert "reference data" in text
    assert "**bold**" in text
    assert "markdown blockquote" in text


def test_podcast_md_states_the_concretika_rules() -> None:
    text = _template_text("podcast")
    assert "## Конкретика" in text
    assert "interesting" in text
    assert "explanatory" in text
    assert "inventory" in text
    assert "**item** —" in text
    assert "explicit grid of numbers" in text
    assert "PostgreSQL" in text
    assert "never invent a version" in text
    assert "Omit the section entirely" in text
    assert "footnote" in text


def test_podcast_md_states_the_sva_rules() -> None:
    text = _template_text("podcast")
    assert "## Зачем это СВА" in text
    assert "working analog for СВА" in text
    assert "information security" in text
    assert "Do not invent a duty" in text
    assert "Omit the section when there is no such analog" in text


def test_podcast_md_has_only_the_intended_headings() -> None:
    text = _template_text("podcast")
    headings = [line for line in text.splitlines() if line.startswith("#")]
    assert set(headings) == set(SHARED_HEADINGS)


def test_podcast_md_keeps_the_audience_block_last() -> None:
    text = _template_text("podcast")
    headings = [line for line in text.splitlines() if line.startswith("#")]
    assert headings[-1] == "## Аудитория"
    assert text.rstrip().endswith("employee, analyst, ds.")
    assert not any(line.startswith("# ") for line in text.splitlines())


def test_kind_sentinels_do_not_cross() -> None:
    lecture = _template_text("lecture")
    podcast = _template_text("podcast")
    assert "single speaker's argument" in lecture
    assert "single speaker's argument" not in podcast
    assert "positions of its participants" in podcast
    assert "positions of its participants" not in lecture


def test_load_article_templates_returns_both_kinds() -> None:
    from data_collection.templates import load_article_templates

    root = importlib.resources.files("data_collection.templates")
    templates = load_article_templates(root)
    assert set(templates.keys()) == set(TemplateKind)
    assert "## Конкретика" in templates[TemplateKind.LECTURE]
    assert "## Аудитория" in templates[TemplateKind.PODCAST]


def test_missing_lecture_md_raises_template_load_error(tmp_path: Path) -> None:
    from data_collection.templates import TemplateLoadError, load_article_templates

    (tmp_path / "podcast.md").write_text("## О чём разговор", encoding="utf-8")
    with pytest.raises(TemplateLoadError):
        load_article_templates(tmp_path)


def test_missing_podcast_md_raises_template_load_error(tmp_path: Path) -> None:
    from data_collection.templates import TemplateLoadError, load_article_templates

    (tmp_path / "lecture.md").write_text("## Тезис", encoding="utf-8")
    with pytest.raises(TemplateLoadError):
        load_article_templates(tmp_path)


def test_unreadable_template_raises_template_load_error() -> None:
    from data_collection.templates import TemplateLoadError, load_article_templates

    class _FailingPath:
        def is_file(self) -> bool:
            return True

        def read_text(self, *, encoding: str) -> str:
            raise OSError("cannot read")

    class _FakeRoot:
        def joinpath(self, name: str) -> _FailingPath:
            return _FailingPath()

    with pytest.raises(TemplateLoadError):
        load_article_templates(_FakeRoot())


def test_template_load_error_is_not_article_error_or_ingest_error() -> None:
    from data_collection.errors.article import ArticleError
    from data_collection.templates import TemplateLoadError
    from ingestion_service.domain.errors import IngestError

    assert not issubclass(TemplateLoadError, ArticleError)
    assert not issubclass(TemplateLoadError, IngestError)


def test_build_deepseek_article_generator_with_missing_template_does_not_construct_async_openai(
    tmp_path: Path,
) -> None:

    from openai import AsyncOpenAI

    import ingestion_service.composition.clients as clients_module
    from data_collection.templates import TemplateLoadError
    from ingestion_service.composition.clients import build_deepseek_article_generator
    from ingestion_service.composition.settings import Settings

    constructed: list[object] = []
    original = clients_module.AsyncOpenAI

    class _SpyAsyncOpenAI(AsyncOpenAI):
        def __init__(self, **kwargs: object) -> None:
            constructed.append(kwargs)
            super().__init__(**kwargs)

    clients_module.AsyncOpenAI = _SpyAsyncOpenAI
    try:
        settings = Settings.from_env({"DEEPSEEK_API_KEY": "sk-valid"})
        with pytest.raises(TemplateLoadError):
            build_deepseek_article_generator(settings, template_root=tmp_path)
        assert constructed == []
    finally:
        clients_module.AsyncOpenAI = original
