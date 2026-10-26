"""RED→GREEN: persist_draft idempotency and batch overflow against the fake port."""

from __future__ import annotations

from datetime import datetime, timezone

from data_collection.dto.material_draft import MaterialDraft


def _words(count: int) -> str:
    return " ".join(["слово"] * count)


def _draft(video_id: str, **overrides: object) -> MaterialDraft:
    base: dict[str, object] = {
        "title": f"Draft {video_id}",
        "dek": "d",
        "body_markdown": _words(200),
        "source_url": f"https://www.youtube.com/watch?v={video_id}",
        "youtube_video_id": video_id,
        "source_author": "Author",
        "provenance_label": "YouTube · Author",
    }
    base.update(overrides)
    return MaterialDraft(**base)


def _batch_fake(**kwargs: object):
    from ingestion_service.tests_support import fakes

    cls = getattr(fakes, "BatchTrackingFakePersister", None)
    assert cls is not None
    return cls(**kwargs)


def test_persist_draft_twice_same_video_id_is_idempotent() -> None:
    from ingestion_service.application.use_cases.persist_draft import persist_draft

    fake = _batch_fake(batch_size=5)
    draft = _draft("dQw4w9WgXcQ")
    first = persist_draft(draft, fake)
    second = persist_draft(draft, fake)
    assert first.already_saved is False
    assert second.already_saved is True
    assert first.material_id == second.material_id
    assert first.slug == second.slug
    assert first.batch_id == second.batch_id
    assert first.rank == second.rank
    assert list(fake.stored.keys()) == ["dQw4w9WgXcQ"]
    assert len(fake.calls) == 2


def test_overflow_creates_new_unsent_batch_at_capacity() -> None:
    from ingestion_service.application.use_cases.persist_draft import persist_draft

    fake = _batch_fake(batch_size=5)
    results = [
        persist_draft(_draft(f"vid{index:09d}"), fake) for index in range(1, 6)
    ]
    assert [item.rank for item in results] == [1, 2, 3, 4, 5]
    assert len({item.batch_id for item in results}) == 1
    overflow = persist_draft(_draft("vid00000006"), fake)
    assert overflow.batch_id != results[0].batch_id
    assert overflow.rank == 1


def test_rejected_item_counts_toward_batch_capacity() -> None:
    from ingestion_service.application.use_cases.persist_draft import persist_draft

    fake = _batch_fake(batch_size=5)
    fake.seed_batch(batch_id=7)
    fake.seed_item(7, decision="pending", video_id="already1")
    fake.seed_item(7, decision="pending", video_id="already2")
    fake.seed_item(7, decision="pending", video_id="already3")
    fake.seed_item(7, decision="rejected", video_id="rejected1")
    fake.seed_item(7, decision="pending", video_id="already4")
    next_item = persist_draft(_draft("vid00000007"), fake)
    assert next_item.batch_id != 7
    assert next_item.rank == 1


def test_batch_sent_skips_latest_sent_batch() -> None:
    from ingestion_service.application.use_cases.persist_draft import persist_draft

    fake = _batch_fake(batch_size=5)
    sent_at = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    fake.seed_batch(batch_id=3, sent_at=sent_at)
    fake.seed_item(3, decision="pending", video_id="sent-item")
    result = persist_draft(_draft("vid00000008"), fake)
    assert result.batch_id != 3
    assert fake.batches[3].sent_at == sent_at
    assert result.rank == 1
    assert fake.batches[result.batch_id].sent_at is None


def test_rerun_when_only_sent_batch_exists_returns_already_saved() -> None:
    """D-08 / CLI-02: sent-batch-only conflict returns already_saved with stored ids."""
    from ingestion_service.application.ports.persist import PersistResult
    from ingestion_service.application.use_cases.persist_draft import persist_draft

    fake = _batch_fake(batch_size=5)
    sent_at = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    fake.seed_batch(batch_id=3, sent_at=sent_at)
    fake.seed_item(3, decision="pending", video_id="published-vid")
    fake.stored["published-vid"] = PersistResult(
        material_id=9,
        slug="published-vid",
        batch_id=3,
        rank=1,
        already_saved=False,
    )

    result = persist_draft(_draft("published-vid"), fake)
    assert result.already_saved is True
    assert result.material_id == 9
    assert result.slug == "published-vid"
    assert result.batch_id == 3
    assert result.rank == 1
    assert fake.batches[3].sent_at == sent_at
    assert len(fake.calls) == 1
