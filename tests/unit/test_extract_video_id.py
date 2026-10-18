"""RED→GREEN: extract_video_id accept/reject matrix (CAP-01, D-01…D-05)."""

from __future__ import annotations

import re

import pytest

VIDEO_ID = "dQw4w9WgXcQ"
VIDEO_ID_DASH = "dQw4w9-gXcQ"
VIDEO_ID_UNDERSCORE = "dQw4w9_gXcQ"

_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


@pytest.mark.parametrize(
    "value",
    [
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtube.com/watch?v={VIDEO_ID}",
        f"https://www.youtube.com/watch?v={VIDEO_ID}&t=30&list=PLxx&si=abc&feature=share&ab_channel=Rick",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}?t=42",
        f"https://youtu.be/{VIDEO_ID}?si=xyz",
        f"https://m.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/shorts/{VIDEO_ID}/",
        f"https://youtube.com/embed/{VIDEO_ID}",
        f"https://www.youtube.com/embed/{VIDEO_ID}?start=10",
        f"  https://www.youtube.com/watch?v={VIDEO_ID}  ",
        VIDEO_ID,
        VIDEO_ID_DASH,
        VIDEO_ID_UNDERSCORE,
        f"https://www.youtube.com/watch?v={VIDEO_ID_DASH}",
        f"https://youtu.be/{VIDEO_ID_UNDERSCORE}",
    ],
)
def test_extract_video_id_accepts_url_families(value: str) -> None:
    from ingestion_service.url import extract_video_id

    expected = value.strip()
    if len(expected) == 11 and re.fullmatch(r"[A-Za-z0-9_-]{11}", expected):
        assert extract_video_id(value) == expected
    elif VIDEO_ID_DASH in value:
        assert extract_video_id(value) == VIDEO_ID_DASH
    elif VIDEO_ID_UNDERSCORE in value:
        assert extract_video_id(value) == VIDEO_ID_UNDERSCORE
    else:
        assert extract_video_id(value) == VIDEO_ID


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch",
        "https://www.youtube.com/playlist?list=PLxxxxxxxx",
        "https://www.youtube.com/channel/UCxxxxxxxx",
        "https://www.youtube.com/@handle",
        "https://www.youtube.com/user/someuser",
        "https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ",
        "https://notyoutube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
        "https://www.youtube.com/v/dQw4w9WgXcQ",
        "https://www.youtube.com/e/dQw4w9WgXcQ",
        "dQw4w9WgXc",  # 10 chars
        "dQw4w9WgXcQ1",  # 12 chars
        "dQw4w9WgXc!",  # illegal char
        "",
        "   ",
    ],
)
def test_extract_video_id_rejects_invalid_inputs(value: str) -> None:
    from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

    with pytest.raises(InvalidYouTubeUrl) as exc_info:
        extract_video_id(value)

    err = exc_info.value
    assert isinstance(err.reason, str)
    assert _SNAKE.fullmatch(err.reason), err.reason


def test_lookalike_hosts_rejected() -> None:
    from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

    for host_url in (
        "https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ",
        "https://notyoutube.com/watch?v=dQw4w9WgXcQ",
    ):
        with pytest.raises(InvalidYouTubeUrl):
            extract_video_id(host_url)


def test_deferred_path_forms_rejected() -> None:
    from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

    for path_url in (
        "https://www.youtube.com/live/dQw4w9WgXcQ",
        "https://www.youtube.com/v/dQw4w9WgXcQ",
        "https://www.youtube.com/e/dQw4w9WgXcQ",
    ):
        with pytest.raises(InvalidYouTubeUrl):
            extract_video_id(path_url)


def test_rejection_maps_to_stage_url_with_snake_reason() -> None:
    from ingestion_service.mapping.url import map_url_error
    from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

    with pytest.raises(InvalidYouTubeUrl) as exc_info:
        extract_video_id("https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ")

    err = exc_info.value
    mapped = map_url_error(err)

    assert mapped.stage == "url"
    assert mapped.reason == err.reason
    assert _SNAKE.fullmatch(mapped.reason)
    # reason must not look like a Python exception class name
    assert mapped.reason[0].islower()
    assert not mapped.reason.endswith("Error")
    assert "Exception" not in mapped.reason
