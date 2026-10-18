"""run_collect_batch — enabled sources → feed → ingest pipeline (ING-02, ING-05)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from data_collection.dto.template_kind import TemplateKind
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider
from data_collection.ports.video_list_provider import VideoListProvider
from data_collection.ports.video_metadata_provider import VideoMetadataProvider
from ingestion_service.application.ports.collect_sources import CollectSourceReader
from ingestion_service.application.ports.persist import PersistPort
from ingestion_service.application.use_cases.ingest_pipeline import run_ingest_pipeline
from ingestion_service.domain.schedule import advance_cursor, select_window


@dataclass(frozen=True)
class CollectDeps:
    feed: VideoListProvider
    sources: CollectSourceReader
    captions: TranscriptProvider
    metadata_provider: VideoMetadataProvider
    article: ArticleGenerator
    persist: PersistPort
    emit_diagnostic: Callable[[str], None]


@dataclass(frozen=True)
class CollectCounters:
    sources_read: int
    sources_unreadable: int
    videos_new: int
    videos_ingested: int
    videos_already: int
    videos_failed: int
    videos_skipped_limit: int


async def run_collect_batch(
    deps: CollectDeps,
    *,
    template: TemplateKind,
    limit: int,
) -> CollectCounters:
    sources_read = 0
    sources_unreadable = 0
    videos_new = 0
    videos_ingested = 0
    videos_already = 0
    videos_failed = 0
    videos_skipped_limit = 0

    enabled = deps.sources.list_enabled_sources()
    for source in enabled:
        listing = await deps.feed.list_recent(
            kind=source.kind, source_id=source.source_id
        )
        sources_read += 1

        for skip in listing.skipped:
            deps.emit_diagnostic(
                f"video skipped: {skip.video_id or '<unknown>'}: {skip.reason}"
            )

        current = (
            (source.last_seen_published_at, source.last_seen_video_id or "")
            if source.last_seen_published_at is not None
            else None
        )
        last_published = current[0] if current is not None else None
        last_video_id = current[1] if current is not None else None

        window, skipped_limit = select_window(
            listing.videos,
            last_published=last_published,
            last_video_id=last_video_id,
            limit=limit,
        )
        videos_skipped_limit += skipped_limit

        for video in window:
            videos_new += 1
            try:
                result = await run_ingest_pipeline(
                    video.video_id,
                    template,
                    captions=deps.captions,
                    metadata_provider=deps.metadata_provider,
                    article=deps.article,
                    persist=deps.persist,
                    on_stage=None,
                    diagnostics=None,
                )
            except Exception as err:
                videos_failed += 1
                deps.emit_diagnostic(
                    f"video failed: {video.video_id}: {type(err).__name__}: {err}"
                )
                continue

            if result.already_saved:
                videos_already += 1
            else:
                videos_ingested += 1

            next_cursor = advance_cursor(
                current, (video.published, video.video_id)
            )
            deps.sources.advance_cursor(
                source.id,
                published=next_cursor[0],
                video_id=next_cursor[1],
            )
            current = next_cursor

    return CollectCounters(
        sources_read=sources_read,
        sources_unreadable=sources_unreadable,
        videos_new=videos_new,
        videos_ingested=videos_ingested,
        videos_already=videos_already,
        videos_failed=videos_failed,
        videos_skipped_limit=videos_skipped_limit,
    )
