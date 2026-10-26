"""RED→GREEN: run_collect_batch window, isolation, exit codes (ING-02/05/06)."""

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
        CollectOutcome,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert isinstance(outcome, CollectOutcome)
    assert outcome.exit_code == 0
    assert outcome.counters == CollectCounters(
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
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.videos_new == 0
    assert outcome.exit_code == 0
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
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.videos_failed == 0
    assert outcome.counters.videos_new == 1
    assert outcome.counters.videos_ingested == 1
    assert outcome.exit_code == 0
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
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.exit_code == 0
    assert outcome.counters == CollectCounters(
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
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert captions.calls == [_vid(i) for i in range(11, 16)]
    assert outcome.counters.videos_skipped_limit == 0
    assert outcome.counters.videos_new == 5
    assert outcome.exit_code == 0


def test_run_collect_batch_cursor_on_twelfth_limit_two_skips_one() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=2)
    )

    assert captions.calls == [_vid(13), _vid(14)]
    assert outcome.counters.videos_skipped_limit == 1
    assert outcome.counters.videos_new == 2
    assert outcome.exit_code == 0


def test_rescan_at_feed_head_makes_zero_llm_calls() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    first = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )
    assert first.counters.videos_ingested == 5
    assert first.exit_code == 0
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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )
    second = asyncio.run(
        run_collect_batch(deps2, template=TemplateKind.LECTURE, limit=5)
    )

    assert second.counters.videos_new == 0
    assert second.counters.videos_ingested == 0
    assert second.exit_code == 0
    assert article2.calls == []
    assert persist2.calls == []
    assert sources2.advance_calls == []
    assert len(persist.calls) == persist_after_first


def test_run_collect_batch_passes_bare_video_id_to_pipeline() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
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
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

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
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.videos_failed == 1
    assert outcome.counters.videos_ingested == 2
    assert outcome.exit_code == 1
    assert captions.calls == [v1, v2, v3]
    # Cursor ends on v3 (newest success); never stuck on failed v2.
    assert sources.advance_calls[-1]["video_id"] == v3
    assert sources.advance_calls[-1]["published"] == t3
    # Failed video must not appear as a cursor write of its own pair alone
    # without a later success — all advance video_ids are successes only.
    advanced_ids = [c["video_id"] for c in sources.advance_calls]
    assert v2 not in advanced_ids
    assert any(v2 in line for line in diagnostics)


def test_cursor_write_failure_is_isolated_and_batch_completes() -> None:
    """CR-01: cursor-write SDK failure → failed counter, diagnostic, graded exit 1."""
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

    v1, v2 = _vid(1), _vid(2)
    t1 = BASE + timedelta(hours=1)
    t2 = BASE + timedelta(hours=2)
    listing = FeedListing(
        videos=(VideoRef(v2, t2), VideoRef(v1, t1)),
        skipped=(),
    )
    captions = _EchoCaptions()
    # First cursor write raises; the second succeeds (batch must keep going).
    sources = FakeCollectSourceReader(
        [_enabled()], advance_error=RuntimeError("sdk down")
    )
    diagnostics: list[str] = []
    deps = CollectDeps(
        feed=FakeFeed(listing),
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=diagnostics.append,
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    # Both videos ran through the pipeline; only the cursor write failed.
    assert captions.calls == [v1, v2]
    assert outcome.counters.videos_new == 2
    assert outcome.counters.videos_ingested == 1
    assert outcome.counters.videos_failed == 1
    assert outcome.exit_code == 1
    # The failed write is not recorded; the later success still advances.
    assert [c["video_id"] for c in sources.advance_calls] == [v2]
    assert any(
        line.startswith(f"cursor advance failed: {v1}: RuntimeError: sdk down")
        for line in diagnostics
    )


def test_unreadable_source_continues_to_next_source() -> None:
    from data_collection.errors.feed import FeedError
    from ingestion_service.application.ports.collect_sources import EnabledSource
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

    src_a = "UCaaaaaaaaaaaaaaaaaaaa"
    src_b = "UCbbbbbbbbbbbbbbbbbbbb"
    captions = _EchoCaptions()
    diagnostics: list[str] = []
    sources = FakeCollectSourceReader(
        [
            EnabledSource(
                id=1,
                kind="channel",
                source_id=src_a,
                last_seen_published_at=None,
                last_seen_video_id=None,
            ),
            EnabledSource(
                id=2,
                kind="channel",
                source_id=src_b,
                last_seen_published_at=None,
                last_seen_video_id=None,
            ),
        ]
    )
    deps = CollectDeps(
        feed=FakeFeed(
            FeedListing(videos=(VideoRef(VIDEO_ID, PUBLISHED),), skipped=()),
            failures={src_a: FeedError(src_a, reason="feed_status")},
        ),
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=diagnostics.append,
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.sources_unreadable == 1
    assert outcome.counters.sources_read == 1
    assert outcome.counters.videos_ingested == 1
    assert outcome.exit_code == 0
    assert captions.calls == [VIDEO_ID]
    assert any(src_a in line for line in diagnostics)


def test_all_sources_unreadable_exit_code_2() -> None:
    from data_collection.errors.feed import FeedError
    from ingestion_service.application.ports.collect_sources import EnabledSource
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

    src_a = "UCaaaaaaaaaaaaaaaaaaaa"
    src_b = "UCbbbbbbbbbbbbbbbbbbbb"
    sources = FakeCollectSourceReader(
        [
            EnabledSource(
                id=1,
                kind="channel",
                source_id=src_a,
                last_seen_published_at=None,
                last_seen_video_id=None,
            ),
            EnabledSource(
                id=2,
                kind="channel",
                source_id=src_b,
                last_seen_published_at=None,
                last_seen_video_id=None,
            ),
        ]
    )
    deps = CollectDeps(
        feed=FakeFeed(
            FeedListing(videos=(), skipped=()),
            failures={
                src_a: FeedError(src_a, reason="feed_status"),
                src_b: FeedError(src_b, reason="network"),
            },
        ),
        sources=sources,
        captions=_EchoCaptions(),
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.sources_read == 0
    assert outcome.counters.sources_unreadable == 2
    assert outcome.exit_code == 2


def test_unexpected_feed_exception_is_isolated_per_source() -> None:
    """WR-02: adapter bug (non-FeedError) degrades to unreadable + continue."""
    from ingestion_service.application.ports.collect_sources import EnabledSource
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

    src_a = "UCaaaaaaaaaaaaaaaaaaaa"
    src_b = "UCbbbbbbbbbbbbbbbbbbbb"
    captions = _EchoCaptions()
    diagnostics: list[str] = []
    sources = FakeCollectSourceReader(
        [
            EnabledSource(
                id=1,
                kind="channel",
                source_id=src_a,
                last_seen_published_at=None,
                last_seen_video_id=None,
            ),
            EnabledSource(
                id=2,
                kind="channel",
                source_id=src_b,
                last_seen_published_at=None,
                last_seen_video_id=None,
            ),
        ]
    )
    deps = CollectDeps(
        feed=FakeFeed(
            FeedListing(videos=(VideoRef(VIDEO_ID, PUBLISHED),), skipped=()),
            failures={src_a: RuntimeError("adapter bug")},
        ),
        sources=sources,
        captions=captions,
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=diagnostics.append,
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.sources_unreadable == 1
    assert outcome.counters.sources_read == 1
    assert outcome.counters.videos_ingested == 1
    assert outcome.exit_code == 0
    assert captions.calls == [VIDEO_ID]
    assert any(
        src_a in line and "RuntimeError" in line and "adapter bug" in line
        for line in diagnostics
    )


def test_unexpected_feed_exception_only_source_exit_code_2() -> None:
    """WR-02: an adapter bug on every source grades exit 2, not a traceback."""
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

    sources = FakeCollectSourceReader(
        [_enabled()]
    )
    deps = CollectDeps(
        feed=FakeFeed(
            FeedListing(videos=(), skipped=()),
            failures={CHANNEL_ID: RuntimeError("adapter bug")},
        ),
        sources=sources,
        captions=_EchoCaptions(),
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.sources_read == 0
    assert outcome.counters.sources_unreadable == 1
    assert outcome.exit_code == 2


def test_list_enabled_sources_failure_exit_2_no_feed_calls() -> None:
    from ingestion_service.application.ports.collect_sources import CollectSourceError
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

    feed = FakeFeed(FeedListing(videos=(), skipped=()))
    diagnostics: list[str] = []
    deps = CollectDeps(
        feed=feed,
        sources=FakeCollectSourceReader(
            list_error=CollectSourceError("база недоступна")
        ),
        captions=_EchoCaptions(),
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=diagnostics.append,
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.sources_read == 0
    assert outcome.counters.sources_unreadable == 0
    assert outcome.exit_code == 2
    assert feed.calls == []
    assert len(diagnostics) == 1
    assert "source list failed" in diagnostics[0]


def test_empty_feed_zero_videos_exit_0() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

    deps = CollectDeps(
        feed=FakeFeed(FeedListing(videos=(), skipped=())),
        sources=FakeCollectSourceReader([_enabled()]),
        captions=_EchoCaptions(),
        metadata_provider=_EchoMetadata(),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
        emit_diagnostic=lambda _line: None,
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.videos_new == 0
    assert outcome.exit_code == 0


def test_already_saved_counts_as_already_and_advances_cursor() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectDeps,
        run_collect_batch,
    )
    from ingestion_service.tests_support.fakes import FakeClock, FakeCollectSourceReader, FakeFeed

    persist = _persist()
    persist.stored[VIDEO_ID] = PersistResult(
        material_id=1, slug="t-dQw4w9WgXcQ", batch_id=1, rank=1, already_saved=True
    )
    sources = FakeCollectSourceReader([_enabled()])
    deps = CollectDeps(
        feed=FakeFeed(
            FeedListing(videos=(VideoRef(VIDEO_ID, PUBLISHED),), skipped=())
        ),
        sources=sources,
        captions=FakeTranscriptProvider(result=_transcript()),
        metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
        article=FakeArticleGenerator(result=_article()),
        persist=persist,
        emit_diagnostic=lambda _line: None,
        clock=FakeClock([0.0], datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)),
        tz=timezone(timedelta(hours=3)),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.videos_already == 1
    assert outcome.counters.videos_ingested == 0
    assert outcome.exit_code == 0
    assert len(sources.advance_calls) == 1
    assert sources.advance_calls[0]["video_id"] == VIDEO_ID


# --- due gate + last_run_at (ING-06, D-21/D-23) ---

_MSK = timezone(timedelta(hours=3))


def _always_due_schedule():
    from datetime import time

    from ingestion_service.domain.schedule import IngestionSchedule

    return IngestionSchedule(
        enabled=True,
        time_of_day=time(0, 0),
        days_of_week=(1, 2, 3, 4, 5, 6, 7),
        last_run_at=None,
    )


def _not_due_schedule(*, reason: str = "disabled"):
    from datetime import time

    from ingestion_service.domain.schedule import IngestionSchedule

    if reason == "disabled":
        return IngestionSchedule(
            enabled=False,
            time_of_day=time(0, 0),
            days_of_week=(1, 2, 3, 4, 5, 6, 7),
            last_run_at=None,
        )
    raise AssertionError(f"unsupported reason fixture: {reason}")


def _deps_with_schedule(
    *,
    sources,
    feed=None,
    schedule=None,
    now: datetime | None = None,
    diagnostics=None,
    captions=None,
    article=None,
    persist=None,
):
    from ingestion_service.application.use_cases.collect_batch import CollectDeps
    from ingestion_service.tests_support.fakes import FakeClock, FakeFeed

    clock_now = now or datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)
    return CollectDeps(
        feed=feed or FakeFeed(FeedListing(videos=(), skipped=())),
        sources=sources,
        captions=captions or _EchoCaptions(),
        metadata_provider=_EchoMetadata(),
        article=article or FakeArticleGenerator(result=_article()),
        persist=persist or _persist(),
        emit_diagnostic=diagnostics if diagnostics is not None else (lambda _l: None),
        clock=FakeClock([0.0], clock_now),
        tz=_MSK,
    )


def test_not_due_skips_feed_and_returns_reason() -> None:
    from ingestion_service.application.use_cases.collect_batch import run_collect_batch
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    feed = FakeFeed(
        FeedListing(videos=(VideoRef(VIDEO_ID, PUBLISHED),), skipped=())
    )
    sources = FakeCollectSourceReader(
        [_enabled()], schedule=_not_due_schedule(reason="disabled")
    )
    deps = _deps_with_schedule(sources=sources, feed=feed)

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.exit_code == 0
    assert outcome.not_due_reason == "disabled"
    assert outcome.counters.sources_read == 0
    assert feed.calls == []
    assert sources.stamped == []


def test_due_empty_run_stamps_last_run_at() -> None:
    from ingestion_service.application.use_cases.collect_batch import run_collect_batch
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    feed = FakeFeed(FeedListing(videos=(), skipped=()))
    sources = FakeCollectSourceReader(
        [_enabled()], schedule=_always_due_schedule()
    )
    now = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)
    deps = _deps_with_schedule(sources=sources, feed=feed, now=now)

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.exit_code == 0
    assert outcome.not_due_reason is None
    assert outcome.counters.videos_new == 0
    assert sources.stamped == [now]


def test_due_zero_enabled_sources_does_not_stamp_and_zeros() -> None:
    from ingestion_service.application.use_cases.collect_batch import (
        CollectCounters,
        run_collect_batch,
    )
    from ingestion_service.domain.schedule import due_decision
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    feed = FakeFeed(FeedListing(videos=(), skipped=()))
    sources = FakeCollectSourceReader([], schedule=_always_due_schedule())
    now = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)
    deps = _deps_with_schedule(sources=sources, feed=feed, now=now)

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.exit_code == 0
    assert outcome.counters == CollectCounters(
        sources_read=0,
        sources_unreadable=0,
        videos_new=0,
        videos_ingested=0,
        videos_already=0,
        videos_failed=0,
        videos_skipped_limit=0,
    )
    assert sources.stamped == []
    assert feed.calls == []

    # WR-03: enabling a source later the same Moscow day must still be due.
    still_due = due_decision(sources.get_schedule(), now_utc=now, tz=_MSK)
    assert still_due.due is True
    assert still_due.reason == "ok"


def test_get_schedule_failure_exit_2_no_feed_no_stamp() -> None:
    from ingestion_service.application.ports.collect_sources import CollectSourceError
    from ingestion_service.application.use_cases.collect_batch import run_collect_batch
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    feed = FakeFeed(FeedListing(videos=(), skipped=()))
    diagnostics: list[str] = []
    sources = FakeCollectSourceReader(
        [_enabled()],
        schedule_error=CollectSourceError("schedule down"),
    )
    deps = _deps_with_schedule(
        sources=sources, feed=feed, diagnostics=diagnostics.append
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.exit_code == 2
    assert feed.calls == []
    assert sources.stamped == []
    assert len(diagnostics) == 1
    assert diagnostics[0].startswith("error: schedule read failed:")


def test_stamp_last_run_failure_keeps_counters_exit_1() -> None:
    from ingestion_service.application.ports.collect_sources import CollectSourceError
    from ingestion_service.application.use_cases.collect_batch import run_collect_batch
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    feed = FakeFeed(
        FeedListing(videos=(VideoRef(VIDEO_ID, PUBLISHED),), skipped=())
    )
    diagnostics: list[str] = []
    sources = FakeCollectSourceReader(
        [_enabled()],
        schedule=_always_due_schedule(),
        stamp_error=CollectSourceError("stamp down"),
    )
    deps = _deps_with_schedule(
        sources=sources,
        feed=feed,
        diagnostics=diagnostics.append,
        captions=FakeTranscriptProvider(result=_transcript()),
        article=FakeArticleGenerator(result=_article()),
        persist=_persist(),
    )

    outcome = asyncio.run(
        run_collect_batch(deps, template=TemplateKind.LECTURE, limit=5)
    )

    assert outcome.counters.videos_ingested == 1
    assert outcome.exit_code == 1
    assert len(diagnostics) == 1
    assert diagnostics[0].startswith("error: stamp last_run failed:")
