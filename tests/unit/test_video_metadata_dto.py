"""RED→GREEN: VideoMetadata DTO (D-11, DTO-01)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


def test_video_metadata_constructs_required_fields() -> None:
    from data_collection.dto.video_metadata import VideoMetadata

    dto = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        author="Rick Astley",
    )
    assert dto.video_id == "dQw4w9WgXcQ"
    assert dto.source_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert dto.author == "Rick Astley"
    assert dto.published_at is None


def test_video_metadata_published_at_optional() -> None:
    from data_collection.dto.video_metadata import VideoMetadata

    published = datetime(2009, 10, 25, tzinfo=timezone.utc)
    dto = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        author="Rick Astley",
        published_at=published,
    )
    assert dto.published_at == published


def test_video_metadata_rejects_naive_published_at() -> None:
    """WR-03: provenance published_at must be timezone-aware (D-14 / PERS-01)."""
    from data_collection.dto.video_metadata import VideoMetadata

    with pytest.raises(ValidationError):
        VideoMetadata(
            video_id="dQw4w9WgXcQ",
            source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            author="Rick Astley",
            published_at=datetime(2009, 10, 25),
        )


def test_video_metadata_omitting_published_at_is_none() -> None:
    """DTO-01 nullable: omit published_at → None OK (D-11, D-13)."""
    from data_collection.dto.video_metadata import VideoMetadata

    dto = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        author="Rick Astley",
    )
    assert dto.published_at is None


@pytest.mark.parametrize("missing_field", ["video_id", "source_url", "author"])
def test_video_metadata_rejects_missing_required_field(missing_field: str) -> None:
    """DTO-01: author/source_url/video_id required (D-11, D-12)."""
    from data_collection.dto.video_metadata import VideoMetadata

    kwargs = {
        "video_id": "dQw4w9WgXcQ",
        "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "author": "Rick Astley",
    }
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        VideoMetadata(**kwargs)


def test_video_metadata_rejects_blank_required_strings() -> None:
    """DTO-01 empty probe: blank video_id/author/source_url rejected (D-11)."""
    from data_collection.dto.video_metadata import VideoMetadata

    with pytest.raises(ValidationError):
        VideoMetadata(
            video_id="   ",
            source_url="https://example.com",
            author="Author",
        )
    with pytest.raises(ValidationError):
        VideoMetadata(
            video_id="dQw4w9WgXcQ",
            source_url="https://example.com",
            author="   ",
        )
    with pytest.raises(ValidationError):
        VideoMetadata(
            video_id="dQw4w9WgXcQ",
            source_url="   ",
            author="Rick Astley",
        )
