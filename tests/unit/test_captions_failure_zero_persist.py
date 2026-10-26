"""RED→GREEN: CAP-02 — captions/article failure must not call persist."""

from __future__ import annotations

import asyncio

import pytest

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.errors.article import ArticleError, ArticleNetworkError
from data_collection.errors.captions import CaptionsError, CaptionsUnavailable
from data_collection.tests_support.fakes import FakeArticleGenerator, FakeTranscriptProvider
from ingestion_service.application.ports.persist import PersistResult
from ingestion_service.application.use_cases.ingest_until_persist import (
    run_ingest_until_persist,
)
from ingestion_service.tests_support.fakes import FakeDraftPersister

VIDEO_ID = "dQw4w9WgXcQ"


def _transcript() -> Transcript:
    return Transcript(text="ok captions", language="ru", video_id=VIDEO_ID)


def _article() -> ArticleDraft:
    return ArticleDraft(title="T", dek="D", body_markdown="B")


def _metadata() -> VideoMetadata:
    return VideoMetadata(
        video_id=VIDEO_ID,
        source_url=f"https://www.youtube.com/watch?v={VIDEO_ID}",
        author="Rick Astley",
    )


def _persist_spy() -> FakeDraftPersister:
    return FakeDraftPersister(
        PersistResult(
            material_id=1, slug="unused", batch_id=1, rank=1, already_saved=False
        )
    )


def test_captions_failure_leaves_persist_calls_empty() -> None:
    provider = FakeTranscriptProvider(
        result=_transcript(),
        failures={VIDEO_ID: CaptionsUnavailable(VIDEO_ID)},
    )
    generator = FakeArticleGenerator(result=_article())
    spy = _persist_spy()

    with pytest.raises(CaptionsError):
        asyncio.run(
            run_ingest_until_persist(
                VIDEO_ID,
                provider,
                generator,
                spy,
                _metadata(),
                template_kind=TemplateKind.LECTURE,
            )
        )

    assert spy.calls == []
    assert generator.calls == []


def test_article_failure_leaves_persist_calls_empty() -> None:
    provider = FakeTranscriptProvider(result=_transcript())
    generator = FakeArticleGenerator(
        result=_article(),
        failures={VIDEO_ID: ArticleNetworkError(VIDEO_ID)},
    )
    spy = _persist_spy()

    with pytest.raises(ArticleError):
        asyncio.run(
            run_ingest_until_persist(
                VIDEO_ID,
                provider,
                generator,
                spy,
                _metadata(),
                template_kind=TemplateKind.LECTURE,
            )
        )

    assert spy.calls == []
    assert generator.calls == [
        {"transcript": _transcript(), "template": TemplateKind.LECTURE}
    ]
