"""RED→GREEN: FakeTranscriptProvider additive failures catalog (D-15, D-14)."""

from __future__ import annotations

import asyncio

import pytest

from data_collection.dto.transcript import Transcript
from data_collection.errors.captions import CaptionsUnavailable
from data_collection.tests_support.fakes import FakeTranscriptProvider
from ingestion_service.mapping.captions import CAPTIONS_REASONS, map_captions_error


VIDEO_ID = "dQw4w9WgXcQ"
OTHER_ID = "abcdefghijk"


def _scripted() -> Transcript:
    return Transcript(text="ok", language="ru", video_id=VIDEO_ID)


def test_failures_raises_scripted_error_and_records_call() -> None:
    err = CaptionsUnavailable(VIDEO_ID)
    fake = FakeTranscriptProvider(_scripted(), failures={VIDEO_ID: err})

    with pytest.raises(CaptionsUnavailable) as exc_info:
        asyncio.run(fake.get(VIDEO_ID))

    assert exc_info.value is err
    assert fake.calls == [VIDEO_ID]


def test_unmapped_id_still_returns_scripted_transcript() -> None:
    err = CaptionsUnavailable(VIDEO_ID)
    fake = FakeTranscriptProvider(_scripted(), failures={VIDEO_ID: err})

    out = asyncio.run(fake.get(OTHER_ID))

    assert out.text == "ok"
    assert fake.calls == [OTHER_ID]


def test_positional_only_construction_still_works() -> None:
    fake = FakeTranscriptProvider(_scripted())
    out = asyncio.run(fake.get(VIDEO_ID))
    assert out.video_id == VIDEO_ID
    assert fake.calls == [VIDEO_ID]


def test_raised_failure_maps_to_captions_stage_and_locked_reason() -> None:
    err = CaptionsUnavailable(VIDEO_ID)
    fake = FakeTranscriptProvider(_scripted(), failures={VIDEO_ID: err})

    with pytest.raises(CaptionsUnavailable) as exc_info:
        asyncio.run(fake.get(VIDEO_ID))

    mapped = map_captions_error(exc_info.value)
    assert mapped.stage == "captions"
    assert mapped.reason in CAPTIONS_REASONS
    assert mapped.reason == "no_captions"
