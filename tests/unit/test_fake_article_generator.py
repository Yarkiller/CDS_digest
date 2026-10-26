"""RED→GREEN: FakeArticleGenerator optional failure scripts (D-17)."""

from __future__ import annotations

import asyncio

import pytest

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.errors.article import ArticleNetworkError


def test_fake_article_generator_without_failures_still_works() -> None:
    from data_collection.tests_support.fakes import FakeArticleGenerator

    scripted = ArticleDraft(title="T", dek="D", body_markdown="B")
    transcript = Transcript(text="hello", language="ru", video_id="abc")
    fake = FakeArticleGenerator(result=scripted)

    out = asyncio.run(fake.process(transcript, TemplateKind.LECTURE))

    assert out is scripted
    assert fake.calls == [{"transcript": transcript, "template": TemplateKind.LECTURE}]


def test_fake_article_generator_failure_by_video_id() -> None:
    from data_collection.tests_support.fakes import FakeArticleGenerator

    scripted = ArticleDraft(title="T", dek="D", body_markdown="B")
    failure = ArticleNetworkError("fail-id", exception_class="APITimeoutError")
    fake = FakeArticleGenerator(result=scripted, failures={"fail-id": failure})

    transcript = Transcript(text="hello", language="ru", video_id="fail-id")

    with pytest.raises(ArticleNetworkError):
        asyncio.run(fake.process(transcript, TemplateKind.LECTURE))

    assert len(fake.calls) == 1
    assert fake.calls[0]["transcript"].video_id == "fail-id"


def test_fake_article_generator_returns_scripted_roles_unchanged() -> None:
    from data_collection.tests_support.fakes import FakeArticleGenerator

    scripted = ArticleDraft(
        title="T", dek="D", body_markdown="B", roles=["analyst"]
    )
    transcript = Transcript(text="hello", language="ru", video_id="abc")
    fake = FakeArticleGenerator(result=scripted)

    out = asyncio.run(fake.process(transcript, TemplateKind.LECTURE))

    assert out is scripted
    assert out.roles == ["analyst"]
    assert len(fake.calls) == 1
    assert fake.calls == [{"transcript": transcript, "template": TemplateKind.LECTURE}]
