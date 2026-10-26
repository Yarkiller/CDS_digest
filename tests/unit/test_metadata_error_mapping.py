"""RED→GREEN: MetadataError → IngestError(stage=metadata) locked reasons (D-23, D-25, D-13)."""

from __future__ import annotations

import pytest

from data_collection.errors.metadata import (
    MetadataError,
    MetadataInvalidResponse,
    MetadataNetworkError,
    MetadataUnavailable,
)


VIDEO_ID = "dQw4w9WgXcQ"

LOCKED_METADATA_REASONS = frozenset(
    {
        "metadata_unavailable",
        "network_error",
        "metadata_invalid_response",
    }
)


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (MetadataUnavailable(VIDEO_ID, status_code=404), "metadata_unavailable"),
        (MetadataNetworkError(VIDEO_ID, exception_class="TimeoutException"), "network_error"),
        (MetadataInvalidResponse(VIDEO_ID), "metadata_invalid_response"),
        (MetadataError(VIDEO_ID), "metadata_unavailable"),
    ],
)
def test_map_metadata_error_subtype_to_locked_reason(
    error: MetadataError, reason: str
) -> None:
    from ingestion_service.mapping.metadata import map_metadata_error

    mapped = map_metadata_error(error)

    assert mapped.stage == "metadata"
    assert mapped.reason == reason
    assert mapped.context.get("video_id") == VIDEO_ID
    payload = mapped.to_dict()
    assert payload["ok"] is False
    assert payload["stage"] == "metadata"
    assert payload["exit_code"] == 1


def test_locked_metadata_reason_set_exactly_three_plus_base_fallback() -> None:
    from ingestion_service.mapping import metadata as metadata_mapping

    assert frozenset(metadata_mapping.METADATA_REASONS) == LOCKED_METADATA_REASONS
    assert "MetadataUnavailable" not in metadata_mapping.METADATA_REASONS
    assert "MetadataNetworkError" not in metadata_mapping.METADATA_REASONS
    assert "MetadataInvalidResponse" not in metadata_mapping.METADATA_REASONS


def test_map_metadata_error_redacts_credentialed_proxy_context() -> None:
    from ingestion_service.mapping.metadata import map_metadata_error

    error = MetadataNetworkError(
        VIDEO_ID,
        exception_class="ConnectError",
        proxy_url="socks5://user:secret@192.168.1.68:1080",
        YOUTUBE_PROXY_URL="socks5://user:secret@192.168.1.68:1080",
    )

    mapped = map_metadata_error(error)
    payload = mapped.to_dict()

    assert mapped.context.get("video_id") == VIDEO_ID
    assert mapped.context.get("exception_class") == "ConnectError"
    assert "proxy_url" not in mapped.context
    assert "YOUTUBE_PROXY_URL" not in mapped.context
    assert "secret" not in str(mapped.context)
    assert "socks5://" not in str(mapped.context)
    assert "secret" not in mapped.message
    assert "socks5://" not in mapped.message
    assert "secret" not in payload["message"]
    assert "socks5://" not in payload["message"]
    assert "secret" not in str(error)
    assert "socks5://" not in str(error)


def test_map_metadata_error_forwards_status_code_allowlist() -> None:
    from ingestion_service.mapping.metadata import map_metadata_error

    error = MetadataUnavailable(VIDEO_ID, status_code=403)
    mapped = map_metadata_error(error)
    assert mapped.context.get("status_code") == 403
    assert mapped.context.get("video_id") == VIDEO_ID
