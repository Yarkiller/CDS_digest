"""RED→GREEN: FakeTranscriptProvider spy (D-15, D-17, DTO-02)."""

import asyncio


def test_fake_transcript_provider_returns_scripted_and_records_calls() -> None:
    from data_collection.dto.transcript import Transcript
    from data_collection.tests_support.fakes import FakeTranscriptProvider

    scripted = Transcript(text="caption text", language="en", video_id="vid-a")
    fake = FakeTranscriptProvider(result=scripted)

    out = asyncio.run(fake.get("vid-a"))

    assert out is scripted
    assert fake.calls == ["vid-a"]


def test_fake_transcript_provider_records_calls_in_order() -> None:
    """Ordering probe: .calls append order equals get call order (D-15)."""
    from data_collection.dto.transcript import Transcript
    from data_collection.tests_support.fakes import FakeTranscriptProvider

    scripted = Transcript(text="caption text", language="ru", video_id="x")
    fake = FakeTranscriptProvider(result=scripted)

    asyncio.run(fake.get("id-1"))
    asyncio.run(fake.get("id-2"))

    assert fake.calls == ["id-1", "id-2"]
