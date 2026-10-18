"""RED→GREEN: run_collect_batch window, cursor, FeedSkip (ING-02, ING-05, D-03–D-09)."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.dto.video_ref import FeedListing, VideoRef
from data_collection.errors.captions import CaptionsError, CaptionsUnavailable
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
BASE = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)


def _vid(n: int) -> str:
    return f"vid{n:08d}"


def _feed_n_desc(n: int) -> tuple[VideoRef, ...]:
    asc = tuple(VideoRef(_vid(i), BASE + timedelta(hours=i)) for i in range(1, n + 1))
    return tuple(reversed(asc))


class _EchoCaptions:
    """TranscriptProvider that echoes the requested video_id (multi-video batches)."""

    def __init__(self, failures: dict[str, CaptionsError] | None = None) -> None:
        self.calls: list[str] = []
        self._failures = failures or {}

    async def get(self, video_id: str) -> Transcript:
        self.calls.append(video_id)
        if video_id in self._failures:
            raise self._failures[video_id]
        return Transcript(text="ok captions", language="ru", video_id=video_id)


class _EchoMetadata:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get(self, video_id: str) -> VideoMetadata:
        self.calls.append(video_id)
        return VideoMetadata(
            video_id=video_id,
            source_url=f"https://www.youtube.com/watch?v={video_id}",
            author="A",
        )


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


def test_run_collect_batch_filters_older_than_cursor_before_pipeline() -> None:
    """D-07 / select_window: older-than-cursor never reaches pipeline or advance."""
    from ingestion_service.application.ports.collect_sources import EnabledSource
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    older_id = "aaaaaaaaaaa"
    article = FakeArticleGenerator(result=_article())
    captions = _EchoCaptions()
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
    deps = CollectDeps(
        feed=feed,
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=article,
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
    )

    counters = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert counters.videos_new == 0
    assert captions.calls == []
    assert article.calls == []
    assert sources.advance_calls == []


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


def _enabled(cursor_pub: datetime | None = None, cursor_id: str | None = None):
    from ingestion_service.application.ports.collect_sources import EnabledSource

    return EnabledSource(
        id=1,
        kind="channel",
        source_id=CHANNEL_ID,
        last_seen_published_at=cursor_pub,
        last_seen_video_id=cursor_id,
    )


def test_run_collect_batch_first_run_processes_oldest_five_in_asc_order() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectCounters,
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    captions = _EchoCaptions()
    article = FakeArticleGenerator(result=_article())
    sources = FakeCollectSourceReader([_enabled()])
    deps = CollectDeps(
        feed=FakeFeed(FeedListing(videos=_feed_n_desc(15), skipped=())),
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=article,
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
    )

    counters = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert counters == CollectCounters(
        sources_read=1,
        sources_unreadable=0,
        videos_new=5,
        videos_ingested=5,
        videos_already=0,
        videos_failed=0,
        videos_skipped_limit=10,
    )
    assert captions.calls == [_vid(i) for i in range(1, 6)]
    assert sources.advance_calls[-1]["video_id"] == _vid(5)
    assert sources.advance_calls[-1]["published"] == BASE + timedelta(hours=5)
    for call in sources.advance_calls:
        assert re.fullmatch(r"[A-Za-z0-9_-]{11}", str(call["video_id"]))


def test_run_collect_batch_cursor_on_tenth_takes_eleven_through_fifteen() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    captions = _EchoCaptions()
    sources = FakeCollectSourceReader(
        [_enabled(BASE + timedelta(hours=10), _vid(10))]
    )
    deps = CollectDeps(
        feed=FakeFeed(FeedListing(videos=_feed_n_desc(15), skipped=())),
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
    )

    counters = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert captions.calls == [_vid(i) for i in range(11, 16)]
    assert counters.videos_skipped_limit == 0
    assert counters.videos_new == 5


def test_run_collect_batch_cursor_on_twelfth_limit_two_skips_one() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    captions = _EchoCaptions()
    sources = FakeCollectSourceReader(
        [_enabled(BASE + timedelta(hours=12), _vid(12))]
    )
    deps = CollectDeps(
        feed=FakeFeed(FeedListing(videos=_feed_n_desc(15), skipped=())),
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
    )

    counters = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=2)
    )

    assert captions.calls == [_vid(13), _vid(14)]
    assert counters.videos_skipped_limit == 1
    assert counters.videos_new == 2


def test_rescan_at_feed_head_makes_zero_llm_calls() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    captions = _EchoCaptions()
    article = FakeArticleGenerator(result=_article())
    persist = _persist()
    sources = FakeCollectSourceReader([_enabled()])
    listing = FeedListing(videos=_feed_n_desc(5), skipped=())
    deps = CollectDeps(
        feed=FakeFeed(listing),
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=article,
        persist=persist,
        emit_diagnostic=lambda _line: None,
    )

    first = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )
    assert first.videos_ingested == 5
    assert sources.advance_calls[-1]["video_id"] == _vid(5)
    head_pub = BASE + timedelta(hours=5)
    head_id = _vid(5)
    persist_after_first = len(persist.calls)

    # Second run: cursor already at feed head (newest of the 5).
    sources2 = FakeCollectSourceReader([_enabled(head_pub, head_id)])
    article2 = FakeArticleGenerator(result=_article())
    persist2 = _persist()
    deps2 = CollectDeps(
        feed=FakeFeed(listing),
        sources=sources2,
        captions=_EchoCaptions(),
        metadata_provider=_EchoMetadata(),
        article=article2,
        persist=persist2,
        emit_diagnostic=lambda _line: None,
    )
    second = asyncio.run(
        run_collect_batch(deps2, template=TemplateKind.LECTURE, limit=5)
    )

    assert second.videos_new == 0
    assert second.videos_ingested == 0
    assert article2.calls == []
    assert persist2.calls == []
    assert sources2.advance_calls == []
    assert len(persist.calls) == persist_after_first


def test_run_collect_batch_passes_bare_video_id_to_pipeline() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    captions = _EchoCaptions()
    deps = CollectDeps(
        feed=FakeFeed(
            FeedListing(videos=(VideoRef(VIDEO_ID, PUBLISHED),), skipped=())
        ),
        sources=FakeCollectSourceReader([_enabled()]),
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
    )

    asyncio.run(run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5))

    assert captions.calls == [VIDEO_ID]
    assert re.fullmatch(r"[A-Za-z0-9_-]{11}", captions.calls[0])


def test_run_collect_batch_failed_video_does_not_advance_cursor() -> None:
    """D-09: failed mid-video keeps cursor; later success advances past it."""
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    v1, v2, v3 = _vid(1), _vid(2), _vid(3)
    t1 = BASE + timedelta(hours=1)
    t2 = BASE + timedelta(hours=2)
    t3 = BASE + timedelta(hours=3)
    # Newest-first Atom order.
    listing = FeedListing(
        videos=(
            VideoRef(v3, t3),
            VideoRef(v2, t2),
            VideoRef(v1, t1),
        ),
        skipped=(),
    )
    captions = _EchoCaptions(failures={v2: CaptionsUnavailable(v2)})
    sources = FakeCollectSourceReader([_enabled()])
    diagnostics: list[str] = []
    deps = CollectDeps(
        feed=FakeFeed(listing),
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=diagnostics.append,
    )

    counters = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert counters.videos_failed == 1
    assert counters.videos_ingested == 2
    assert captions.calls == [v1, v2, v3]
    # Cursor ends on v3 (newest success); never stuck on failed v2.
    assert sources.advance_calls[-1]["video_id"] == v3
    assert sources.advance_calls[-1]["published"] == t3
    # Failed video must not appear as a cursor write of its own pair alone
    # without a later success — all advance video_ids are successes only.
    advanced_ids = [c["video_id"] for c in sources.advance_calls]
    assert v2 not in advanced_ids
    assert any(v2 in line for line in diagnostics)
