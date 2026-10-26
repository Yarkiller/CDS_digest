"""RED→GREEN: FakeVideoMetadataProvider success+spy+failures catalog (D-26)."""

from __future__ import annotations

import asyncio

import pytest

from data_collection.dto.video_metadata import VideoMetadata
from data_collection.errors.metadata import MetadataUnavailable


VIDEO_ID = "dQw4w9WgXcQ"
OTHER_ID = "abcdefghijk"
CANONICAL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


def _scripted() -> VideoMetadata:
    return VideoMetadata(
        video_id=VIDEO_ID,
        source_url=CANONICAL,
        author="Rick Astley",
        published_at=None,
    )


def test_failures_raises_scripted_error_and_records_call() -> None:
    from data_collection.tests_support.fakes import FakeVideoMetadataProvider

    err = MetadataUnavailable(VIDEO_ID, status_code=404)
    fake = FakeVideoMetadataProvider(_scripted(), failures={VIDEO_ID: err})

    with pytest.raises(MetadataUnavailable) as exc_info:
        asyncio.run(fake.get(VIDEO_ID))

    assert exc_info.value is err
    assert fake.calls == [VIDEO_ID]


def test_unmapped_id_still_returns_scripted_video_metadata() -> None:
    from data_collection.tests_support.fakes import FakeVideoMetadataProvider

    err = MetadataUnavailable(VIDEO_ID, status_code=404)
    fake = FakeVideoMetadataProvider(_scripted(), failures={VIDEO_ID: err})

    out = asyncio.run(fake.get(OTHER_ID))

    assert out.author == "Rick Astley"
    assert isinstance(out, VideoMetadata)
    assert fake.calls == [OTHER_ID]


def test_positional_only_construction_still_works() -> None:
    from data_collection.tests_support.fakes import FakeVideoMetadataProvider

    fake = FakeVideoMetadataProvider(_scripted())
    out = asyncio.run(fake.get(VIDEO_ID))
    assert out.video_id == VIDEO_ID
    assert fake.calls == [VIDEO_ID]


def test_raised_failure_maps_to_metadata_stage_and_locked_reason() -> None:
    from data_collection.tests_support.fakes import FakeVideoMetadataProvider
    from ingestion_service.mapping.metadata import METADATA_REASONS, map_metadata_error

    err = MetadataUnavailable(VIDEO_ID, status_code=404)
    fake = FakeVideoMetadataProvider(_scripted(), failures={VIDEO_ID: err})

    with pytest.raises(MetadataUnavailable) as exc_info:
        asyncio.run(fake.get(VIDEO_ID))

    mapped = map_metadata_error(exc_info.value)
    assert mapped.stage == "metadata"
    assert mapped.reason in METADATA_REASONS
    assert mapped.reason == "metadata_unavailable"
