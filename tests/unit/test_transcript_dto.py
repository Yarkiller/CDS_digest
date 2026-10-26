"""RED→GREEN: Transcript DTO (D-09, DTO-01)."""

import pytest
from pydantic import ValidationError


def test_transcript_constructs_with_text_language_video_id() -> None:
    from data_collection.dto.transcript import Transcript

    dto = Transcript(text="hello world", language="en", video_id="dQw4w9WgXcQ")
    assert dto.text == "hello world"
    assert dto.language == "en"
    assert dto.video_id == "dQw4w9WgXcQ"


def test_transcript_strips_text_and_video_id() -> None:
    from data_collection.dto.transcript import Transcript

    dto = Transcript(text="  hello  ", language="ru", video_id="  abc123  ")
    assert dto.text == "hello"
    assert dto.video_id == "abc123"


def test_transcript_rejects_whitespace_only_text() -> None:
    """DTO-01 empty probe: whitespace-only text → ValidationError (D-09)."""
    from data_collection.dto.transcript import Transcript

    with pytest.raises(ValidationError):
        Transcript(text="   ", language="en", video_id="abc")


def test_transcript_rejects_blank_video_id() -> None:
    """DTO-01 empty probe: blank/empty video_id rejected (D-09)."""
    from data_collection.dto.transcript import Transcript

    with pytest.raises(ValidationError):
        Transcript(text="hello", language="en", video_id="   ")
    with pytest.raises(ValidationError):
        Transcript(text="hello", language="en", video_id="")


def test_transcript_language_length_bounds() -> None:
    """DTO-01: language too short/long rejected (D-09)."""
    from data_collection.dto.transcript import Transcript

    ok = Transcript(text="hello", language="zh-Hans", video_id="abc")
    assert ok.language == "zh-Hans"

    with pytest.raises(ValidationError):
        Transcript(text="hello", language="x", video_id="abc")

    with pytest.raises(ValidationError):
        Transcript(text="hello", language="x" * 11, video_id="abc")


def test_transcript_language_strips_before_length_bounds() -> None:
    """WR-02: padded valid BCP-47 tags pass after strip (D-09)."""
    from data_collection.dto.transcript import Transcript

    dto = Transcript(text="hello", language="  zh-Hans  ", video_id="abc")
    assert dto.language == "zh-Hans"
