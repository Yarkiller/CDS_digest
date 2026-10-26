"""RED→GREEN: FakeArticleGenerator spy (D-16, D-17, DTO-02)."""

import asyncio


def test_fake_article_generator_returns_scripted_and_records_calls() -> None:
    from data_collection.dto.article_draft import ArticleDraft
    from data_collection.dto.template_kind import TemplateKind
    from data_collection.dto.transcript import Transcript
    from data_collection.tests_support.fakes import FakeArticleGenerator

    scripted = ArticleDraft(
        title="Prepared",
        dek="Dek",
        body_markdown="# Body",
    )
    transcript = Transcript(text="hello", language="en", video_id="abc")
    fake = FakeArticleGenerator(result=scripted)

    out = asyncio.run(fake.process(transcript, TemplateKind.LECTURE))

    assert out is scripted
    assert fake.calls == [{"transcript": transcript, "template": TemplateKind.LECTURE}]
