"""RED→GREEN: IngestError envelope + map_url_error (D-05, D-11, D-13)."""

from __future__ import annotations

from typing import get_args

import pytest


def test_ingest_error_to_dict_omits_empty_context() -> None:
    from ingestion_service.domain.errors import IngestError

    err = IngestError(stage="url", reason="missing_video_id", message="no v=")
    payload = err.to_dict()

    assert payload == {
        "ok": False,
        "stage": "url",
        "reason": "missing_video_id",
        "message": "no v=",
        "exit_code": 1,
    }
    assert "context" not in payload
    assert err.exit_code == 1


def test_ingest_error_to_dict_includes_nonempty_context() -> None:
    from ingestion_service.domain.errors import IngestError

    err = IngestError(
        stage="url",
        reason="not_a_youtube_url",
        message="bad host",
        context={"value": "https://example.com/x"},
    )
    payload = err.to_dict()

    assert set(payload.keys()) == {
        "ok",
        "stage",
        "reason",
        "message",
        "exit_code",
        "context",
    }
    assert payload["context"] == {"value": "https://example.com/x"}
    assert payload["ok"] is False
    assert payload["exit_code"] == 1


def test_stage_literal_covers_seven_pipeline_stages() -> None:
    from ingestion_service.domain.errors import Stage

    stages = set(get_args(Stage))
    assert stages == {
        "url",
        "captions",
        "metadata",
        "consistency",
        "llm",
        "llm_truncation",
        "persist",
    }


def test_map_url_error_uses_exception_reason_and_stage_url() -> None:
    """Mapper reads reason from InvalidYouTubeUrl — test must not invent the code."""
    from ingestion_service.mapping.url import map_url_error
    from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

    with pytest.raises(InvalidYouTubeUrl) as exc_info:
        extract_video_id("https://example.com/watch?v=dQw4w9WgXcQ")

    err = exc_info.value
    mapped = map_url_error(err)

    assert mapped.stage == "url"
    assert mapped.reason == err.reason
    assert mapped.reason  # production-owned; not captions stage
    assert mapped.exit_code == 1


def test_url_context_allowlist_frozen() -> None:
    """D-02: URL diagnostic context allowlist stays Phase-7 locked."""
    from ingestion_service.mapping import url as url_mapping

    assert frozenset(url_mapping._CONTEXT_ALLOWLIST) == frozenset(
        {"value", "candidate"}
    )


def test_map_url_error_redacts_userinfo_credentials() -> None:
    from ingestion_service.mapping.url import map_url_error
    from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

    credentialed = "https://user:secret@evil.com/watch?v=dQw4w9WgXcQ"
    with pytest.raises(InvalidYouTubeUrl) as exc_info:
        extract_video_id(credentialed)

    mapped = map_url_error(exc_info.value)
    payload = mapped.to_dict()

    assert "secret" not in mapped.message
    assert "user:secret" not in mapped.message
    assert "secret" not in str(mapped.context)
    assert "secret" not in payload["message"]
    assert "secret" not in str(payload.get("context", {}))
    assert "secret" not in str(exc_info.value)


def test_map_url_error_redacts_userinfo_on_invalid_youtube_id() -> None:
    from ingestion_service.mapping.url import map_url_error
    from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

    credentialed = "https://user:passwd@www.youtube.com/watch?v=SHORT"
    with pytest.raises(InvalidYouTubeUrl) as exc_info:
        extract_video_id(credentialed)

    mapped = map_url_error(exc_info.value)
    payload = mapped.to_dict()

    assert "passwd" not in mapped.message
    assert "passwd" not in str(mapped.context)
    assert "passwd" not in payload["message"]
    assert "passwd" not in str(payload.get("context", {}))
    assert "passwd" not in str(exc_info.value)
