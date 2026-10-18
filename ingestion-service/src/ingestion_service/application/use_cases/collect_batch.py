"""run_collect_batch — due-gate → enabled sources → feed → ingest (ING-02/05/06)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import tzinfo

from data_collection.dto.template_kind import TemplateKind
from data_collection.errors.feed import FeedError
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider
from data_collection.ports.video_list_provider import VideoListProvider
from data_collection.ports.video_metadata_provider import VideoMetadataProvider
from ingestion_service.application.ports.collect_sources import (
    CollectSourceError,
    CollectSourceReader,
)
from ingestion_service.application.ports.diagnostics import Clock
from ingestion_service.application.ports.persist import PersistPort
from ingestion_service.application.use_cases.ingest_pipeline import run_ingest_pipeline
from ingestion_service.domain.schedule import advance_cursor, due_decision, select_window


@dataclass(frozen=True)
class CollectDeps:
    feed: VideoListProvider
    sources: CollectSourceReader
    captions: TranscriptProvider
    metadata_provider: VideoMetadataProvider
    article: ArticleGenerator
    persist: PersistPort
    emit_diagnostic: Callable[[str], None]
    clock: Clock
    tz: tzinfo


@dataclass(frozen=True)
class CollectCounters:
    sources_read: int
    sources_unreadable: int
    videos_new: int
    videos_ingested: int
    videos_already: int
    videos_failed: int
    videos_skipped_limit: int


@dataclass(frozen=True)
class CollectOutcome:
    counters: CollectCounters
    exit_code: int
    not_due_reason: str | None = None


def _zero_counters() -> CollectCounters:
    return CollectCounters(
        sources_read=0,
        sources_unreadable=0,
        videos_new=0,
        videos_ingested=0,
        videos_already=0,
        videos_failed=0,
        videos_skipped_limit=0,
    )


def _exit_code(
    *,
    list_failed: bool,
    sources_total: int,
    sources_unreadable: int,
    videos_failed: int,
) -> int:
    """D-12: 2 = no source readable / list failed; 1 = video failures; else 0."""
    if list_failed:
        return 2
    if sources_total > 0 and sources_unreadable == sources_total:
        return 2
    if videos_failed > 0:
        return 1
    return 0


async def run_collect_batch(
    deps: CollectDeps,
    *,
    template: TemplateKind,
    limit: int,
) -> CollectOutcome:
    try:
        schedule = deps.sources.get_schedule()
    except Exception as err:
        deps.emit_diagnostic(
            f"error: schedule read failed: {type(err).__name__}"
        )
        return CollectOutcome(counters=_zero_counters(), exit_code=2)

    decision = due_decision(
        schedule, now_utc=deps.clock.now(), tz=deps.tz
    )
    if not decision.due:
        return CollectOutcome(
            counters=_zero_counters(),
            exit_code=0,
            not_due_reason=decision.reason,
        )

    sources_read = 0
    sources_unreadable = 0
    videos_new = 0
    videos_ingested = 0
    videos_already = 0
    videos_failed = 0
    videos_skipped_limit = 0

    try:
        enabled = deps.sources.list_enabled_sources()
    except Exception as err:
        deps.emit_diagnostic(
            f"error: source list failed: {type(err).__name__}: {err}"
        )
        counters = _zero_counters()
        return CollectOutcome(counters=counters, exit_code=2)

    for source in enabled:
        try:
            listing = await deps.feed.list_recent(
                kind=source.kind, source_id=source.source_id
            )
        except (FeedError, CollectSourceError) as err:
            sources_unreadable += 1
            deps.emit_diagnostic(
                f"source unreadable: {source.source_id}: "
                f"{type(err).__name__}: {err}"
            )
            continue
        except Exception as err:  # noqa: BLE001 — adapter bug must not kill the batch
            sources_unreadable += 1
            deps.emit_diagnostic(
                f"source unreadable (unexpected): {source.source_id}: "
                f"{type(err).__name__}: {err}"
            )
            continue

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

            next_cursor = advance_cursor(
                current, (video.published, video.video_id)
            )
            try:
                deps.sources.advance_cursor(
                    source.id,
                    published=next_cursor[0],
                    video_id=next_cursor[1],
                )
            except Exception as err:  # noqa: BLE001 — cursor write is best-effort
                videos_failed += 1
                deps.emit_diagnostic(
                    f"cursor advance failed: {video.video_id}: "
                    f"{type(err).__name__}: {err}"
                )
                continue

            if result.already_saved:
                videos_already += 1
            else:
                videos_ingested += 1
            current = next_cursor

    counters = CollectCounters(
        sources_read=sources_read,
        sources_unreadable=sources_unreadable,
        videos_new=videos_new,
        videos_ingested=videos_ingested,
        videos_already=videos_already,
        videos_failed=videos_failed,
        videos_skipped_limit=videos_skipped_limit,
    )
    exit_code = _exit_code(
        list_failed=False,
        sources_total=len(enabled),
        sources_unreadable=sources_unreadable,
        videos_failed=videos_failed,
    )

    # WR-03 / D-27: a due run with zero enabled sources must not stamp, or
    # enabling a source later the same Moscow day stays blocked until tomorrow.
    # Any run that read >=1 source still stamps (including zero-new-videos runs).
    if enabled:
        try:
            deps.sources.stamp_last_run(deps.clock.now())
        except Exception as err:
            deps.emit_diagnostic(
                f"error: stamp last_run failed: {type(err).__name__}"
            )
            return CollectOutcome(counters=counters, exit_code=1)

    return CollectOutcome(counters=counters, exit_code=exit_code)
