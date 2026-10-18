"""In-memory PersistPort double with call spy and scripted failures (D-03, D-11)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import TYPE_CHECKING

from data_collection.dto.material_draft import MaterialDraft
from data_collection.dto.video_ref import FeedListing
from ingestion_service.adapters.persist_errors import DraftPersistError
from ingestion_service.application.ports.collect_sources import (
    CollectSourceError,
    EnabledSource,
)
from ingestion_service.application.ports.diagnostics import DebugValue
from ingestion_service.application.ports.persist import PersistResult

if TYPE_CHECKING:
    from ingestion_service.domain.schedule import IngestionSchedule


class FakeFeed:
    """VideoListProvider double returning a scripted FeedListing."""

    def __init__(
        self,
        listing: FeedListing,
        *,
        failures: dict[str, BaseException] | None = None,
    ) -> None:
        self._listing = listing
        self._failures = failures or {}
        self.calls: list[dict[str, str]] = []

    async def list_recent(self, *, kind: str, source_id: str) -> FeedListing:
        self.calls.append({"kind": kind, "source_id": source_id})
        failure = self._failures.get(source_id)
        if failure is not None:
            raise failure
        return self._listing


def _default_always_due_schedule() -> IngestionSchedule:
    from ingestion_service.domain.schedule import IngestionSchedule

    return IngestionSchedule(
        enabled=True,
        time_of_day=time(0, 0),
        days_of_week=(1, 2, 3, 4, 5, 6, 7),
        last_run_at=None,
    )


class FakeCollectSourceReader:
    """CollectSourceReader double with call spy and scripted failures."""

    def __init__(
        self,
        sources: list[EnabledSource] | None = None,
        *,
        list_error: CollectSourceError | None = None,
        schedule: IngestionSchedule | None = None,
        schedule_error: CollectSourceError | None = None,
        stamp_error: CollectSourceError | None = None,
        advance_error: BaseException | None = None,
    ) -> None:
        self._sources = list(sources or [])
        self._list_error = list_error
        self._schedule = schedule
        self._schedule_error = schedule_error
        self._stamp_error = stamp_error
        self._advance_error = advance_error
        self.advance_calls: list[dict[str, object]] = []
        self.stamped: list[datetime] = []

    def list_enabled_sources(self) -> list[EnabledSource]:
        if self._list_error is not None:
            raise self._list_error
        return list(self._sources)

    def get_schedule(self) -> IngestionSchedule:
        if self._schedule_error is not None:
            raise self._schedule_error
        if self._schedule is not None:
            return self._schedule
        return _default_always_due_schedule()

    def stamp_last_run(self, at: datetime) -> None:
        if self._stamp_error is not None:
            raise self._stamp_error
        self.stamped.append(at)

    def advance_cursor(
        self, source_pk: int, *, published: datetime, video_id: str
    ) -> None:
        # Scripted cursor-write failure: raise once, then behave normally (CR-01).
        if self._advance_error is not None:
            error = self._advance_error
            self._advance_error = None
            raise error
        self.advance_calls.append(
            {
                "source_pk": source_pk,
                "published": published,
                "video_id": video_id,
            }
        )


class FakeDraftPersister:
    def __init__(
        self,
        result: PersistResult,
        failures: dict[str, DraftPersistError] | None = None,
    ) -> None:
        self._result = result
        self._failures = failures or {}
        self.calls: list[MaterialDraft] = []
        self.stored: dict[str, PersistResult] = {}

    def persist(self, material_draft: MaterialDraft) -> PersistResult:
        self.calls.append(material_draft)
        failure = self._failures.get(material_draft.youtube_video_id)
        if failure is not None:
            raise failure
        existing = self.stored.get(material_draft.youtube_video_id)
        if existing is not None:
            return PersistResult(
                material_id=existing.material_id,
                slug=existing.slug,
                batch_id=existing.batch_id,
                rank=existing.rank,
                already_saved=True,
            )
        stored = PersistResult(
            material_id=self._result.material_id,
            slug=self._result.slug,
            batch_id=self._result.batch_id,
            rank=self._result.rank,
            already_saved=False,
        )
        self.stored[material_draft.youtube_video_id] = stored
        return stored


class FakeClock:
    """Scripted Clock double; monotonic pops a sequence, now is fixed."""

    def __init__(self, monotonic_values: Sequence[float], now: datetime) -> None:
        self._monotonic = list(monotonic_values)
        self._now = now
        self.calls: list[float] = []

    def monotonic(self) -> float:
        value = self._monotonic.pop(0)
        self.calls.append(value)
        return value

    def now(self) -> datetime:
        return self._now


class RecordingDiagnostics:
    """Call-spy StageDiagnostics double recording every event for order assertions."""

    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def stage_started(self, stage: str) -> None:
        self.calls.append(("started", stage))

    def stage_completed(self, stage: str, signals: Mapping[str, DebugValue]) -> None:
        self.calls.append(("completed", stage, dict(signals)))

    def stage_failed(self, stage: str, *, reason: str, exit_code: int) -> None:
        self.calls.append(("failed", stage, reason, exit_code))

    def config_error(self, *, error_type: str, message: str) -> None:
        self.calls.append(("config_error", error_type, message))


@dataclass
class FakeShortlistBatch:
    batch_id: int
    sent_at: datetime | None = None
    items: list[dict[str, object]] = field(default_factory=list)


class BatchTrackingFakePersister:
    """PersistPort double that models unsent-batch overflow and sent-batch skip."""

    def __init__(self, batch_size: int = 5) -> None:
        self.batch_size = batch_size
        self.calls: list[MaterialDraft] = []
        self.stored: dict[str, PersistResult] = {}
        self.batches: dict[int, FakeShortlistBatch] = {}
        self._next_batch_id = 1
        self._next_material_id = 1

    def seed_batch(
        self, batch_id: int, *, sent_at: datetime | None = None
    ) -> FakeShortlistBatch:
        batch = FakeShortlistBatch(batch_id=batch_id, sent_at=sent_at)
        self.batches[batch_id] = batch
        self._next_batch_id = max(self._next_batch_id, batch_id + 1)
        return batch

    def seed_item(
        self,
        batch_id: int,
        *,
        decision: str = "pending",
        video_id: str | None = None,
    ) -> None:
        batch = self.batches[batch_id]
        batch.items.append(
            {
                "video_id": video_id,
                "rank": len(batch.items) + 1,
                "decision": decision,
            }
        )

    def persist(self, material_draft: MaterialDraft) -> PersistResult:
        self.calls.append(material_draft)
        existing = self.stored.get(material_draft.youtube_video_id)
        if existing is not None:
            # D-08: sent-batch-only conflict returns stored ids with already_saved
            # (mirrors migration 009 RPC). New materials still skip sent batches below.
            return PersistResult(
                material_id=existing.material_id,
                slug=existing.slug,
                batch_id=existing.batch_id,
                rank=existing.rank,
                already_saved=True,
            )
        batch = self._target_unsent_batch()
        rank = len(batch.items) + 1
        result = PersistResult(
            material_id=self._next_material_id,
            slug=material_draft.slug,
            batch_id=batch.batch_id,
            rank=rank,
            already_saved=False,
        )
        self._next_material_id += 1
        batch.items.append(
            {
                "video_id": material_draft.youtube_video_id,
                "rank": rank,
                "decision": "pending",
                "material_id": result.material_id,
            }
        )
        self.stored[material_draft.youtube_video_id] = result
        return result

    def _target_unsent_batch(self) -> FakeShortlistBatch:
        unsent = [batch for batch in self.batches.values() if batch.sent_at is None]
        if not unsent:
            return self._create_batch()
        latest = max(unsent, key=lambda batch: batch.batch_id)
        if len(latest.items) >= self.batch_size:
            return self._create_batch()
        return latest

    def _create_batch(self) -> FakeShortlistBatch:
        batch_id = self._next_batch_id
        self._next_batch_id += 1
        batch = FakeShortlistBatch(batch_id=batch_id)
        self.batches[batch_id] = batch
        return batch
