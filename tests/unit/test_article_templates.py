"""RED→GREEN: article templates are package markdown with D-16 headings (LLM-02, D-17)."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import pytest

from data_collection.dto.template_kind import TemplateKind


def test_lecture_md_contains_russian_headings() -> None:
    root = importlib.resources.files("data_collection.templates")
    text = root.joinpath("lecture.md").read_text(encoding="utf-8")
    assert "## Тезис" in text
    assert "## Ход рассуждения" in text
    assert "## Вывод" in text


def test_podcast_md_contains_russian_headings() -> None:
    root = importlib.resources.files("data_collection.templates")
    text = root.joinpath("podcast.md").read_text(encoding="utf-8")
    assert "## О чём разговор" in text
    assert "## Позиции" in text
    assert "## Что запомнить" in text


def test_load_article_templates_returns_both_kinds() -> None:
    from data_collection.templates import load_article_templates

    root = importlib.resources.files("data_collection.templates")
    templates = load_article_templates(root)
    assert set(templates.keys()) == set(TemplateKind)
    assert "## Тезис" in templates[TemplateKind.LECTURE]
    assert "## О чём разговор" in templates[TemplateKind.PODCAST]


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
