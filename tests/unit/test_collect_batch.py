"""RED→GREEN: run_collect_batch happy path + FeedSkip diagnostics (ING-02, D-03, D-25)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.tests_support.fakes import (
    FakeArticleGenerator,
    FakeTranscriptProvider,
    FakeVideoMetadataProvider,
)
from ingestion_service.application.ports.persist import PersistResult
from ingestion_service.tests_support.fakes import FakeDraftPersister

VIDEO_ID = "dQw4w9WgXcQ"
PUBLISHED = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)
CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSMdItQ"


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


def _persist() -> FakeDraftPersister:
    return FakeDraftPersister(
        PersistResult(material_id=1, slug="t-dQw4w9WgXcQ", batch_id=1, rank=1)
    )


def test_run_collect_batch_ingests_one_new_video_and_advances_cursor() -> None:
    from data_collection.dto.video_ref import FeedListing, VideoRef
    from ingestion_service.application.ports.collect_sources import EnabledSource
    from ingestion_service.application.use_cases.collect_batch import (
        CollectCounters,
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    feed = FakeFeed(
        FeedListing(
            videos=(VideoRef(VIDEO_ID, PUBLISHED),),
            skipped=(),
        )
    )
    sources = FakeCollectSourceReader(
        [
            EnabledSource(
                id=1,
                kind="channel",
                source_id=CHANNEL_ID,
                last_seen_published_at=None,
                last_seen_video_id=None,
            )
        ]
    )
    persist = _persist()
    diagnostics: list[str] = []

    deps = CollectDeps(
        feed=feed,
        sources=sources,
        captions=FakeTranscriptProvider(result=_transcript()),
        metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
        article=FakeArticleGenerator(result=_article()),
        persist=persist,
        emit_diagnostic=diagnostics.append,
    )

    counters = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert counters == CollectCounters(
        sources_read=1,
        sources_unreadable=0,
        videos_new=1,
        videos_ingested=1,
        videos_already=0,
        videos_failed=0,
        videos_skipped_limit=0,
    )
    assert VIDEO_ID in persist.stored
    assert len(sources.advance_calls) == 1
    assert sources.advance_calls[0]["source_pk"] == 1
    assert sources.advance_calls[0]["video_id"] == VIDEO_ID
    assert sources.advance_calls[0]["published"] == PUBLISHED
    assert diagnostics == []


def test_run_collect_batch_uses_domain_advance_cursor_not_raw_candidate() -> None:
    from data_collection.dto.video_ref import FeedListing, VideoRef
    from ingestion_service.application.ports.collect_sources import EnabledSource
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    older_id = "aaaaaaaaaaa"
    feed = FakeFeed(
        FeedListing(
            videos=(VideoRef(older_id, PUBLISHED),),
            skipped=(),
        )
    )
    sources = FakeCollectSourceReader(
        [
            EnabledSource(
                id=1,
                kind="channel",
                source_id=CHANNEL_ID,
                last_seen_published_at=PUBLISHED,
                last_seen_video_id="zzzzzzzzzzz",
            )
        ]
    )
    captions = FakeTranscriptProvider(
        result=Transcript(text="ok", language="ru", video_id=older_id)
    )
    metadata = FakeVideoMetadataProvider(
        result=VideoMetadata(
            video_id=older_id,
            source_url=f"https://www.youtube.com/watch?v={older_id}",
            author="A",
        )
    )
    deps = CollectDeps(
        feed=feed,
        sources=sources,
        captions=captions,
        metadata_provider=metadata,
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
    )

    asyncio.run(run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5))

    assert len(sources.advance_calls) == 1
    assert sources.advance_calls[0]["video_id"] == "zzzzzzzzzzz"
    assert sources.advance_calls[0]["published"] == PUBLISHED


def test_run_collect_batch_emits_one_diagnostic_per_feed_skip() -> None:
    from data_collection.dto.video_ref import FeedListing, FeedSkip, VideoRef
    from ingestion_service.application.ports.collect_sources import EnabledSource
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    feed = FakeFeed(
        FeedListing(
            videos=(VideoRef(VIDEO_ID, PUBLISHED),),
            skipped=(
                FeedSkip(None, "missing_video_id"),
                FeedSkip("xxxxxxxxxxx", "invalid_published"),
            ),
        )
    )
    sources = FakeCollectSourceReader(
        [
            EnabledSource(
                id=1,
                kind="channel",
                source_id=CHANNEL_ID,
                last_seen_published_at=None,
                last_seen_video_id=None,
            )
        ]
    )
    persist = _persist()
    diagnostics: list[str] = []

    deps = CollectDeps(
        feed=feed,
        sources=sources,
        captions=FakeTranscriptProvider(result=_transcript()),
        metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
        article=FakeArticleGenerator(result=_article()),
        persist=persist,
        emit_diagnostic=diagnostics.append,
    )

    counters = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert counters.videos_failed == 0
    assert counters.videos_new == 1
    assert counters.videos_ingested == 1
    assert VIDEO_ID in persist.stored
    assert diagnostics == [
        "video skipped: <unknown>: missing_video_id",
        "video skipped: xxxxxxxxxxx: invalid_published",
    ]
