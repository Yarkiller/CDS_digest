"""RED→GREEN: DraftPersistError → IngestError(stage=persist) locked reasons (D-04)."""

from __future__ import annotations


VIDEO_ID = "dQw4w9WgXcQ"
PLANTED_SECRET = "s3cr3t-k3y-09"
RAW_POSTGRES = 'relation "materials" does not exist'
LOCKED_REASONS = frozenset(
    {
        "persist_conflict",
        "batch_creation_failed",
        "rpc_error",
        "network_error",
        "unknown_persist_error",
    }
)
CONTEXT_ALLOWLIST = frozenset({"video_id", "slug", "batch_id", "reason"})


def _planted_context() -> dict[str, object]:
    return {
        "video_id": VIDEO_ID,
        "slug": "kak-ispolzovat-pgvector-dQw4w9WgXcQ",
        "batch_id": 7,
        "reason": "persist_conflict",
        "SUPABASE_SECRET_KEY": PLANTED_SECRET,
        "postgres": RAW_POSTGRES,
        "stack": "Traceback (most recent call last):",
    }


def _cases() -> list[tuple[object, str]]:
    from ingestion_service.adapters.persist_errors import (
        DraftPersistBatchError,
        DraftPersistConflictError,
        DraftPersistError,
        DraftPersistNetworkError,
        DraftPersistRpcError,
        DraftPersistUnknownError,
    )

    ctx = _planted_context()
    return [
        (
            DraftPersistConflictError(
                "persist_conflict", video_id=VIDEO_ID, context=ctx
            ),
            "persist_conflict",
        ),
        (
            DraftPersistBatchError(
                "batch_creation_failed", video_id=VIDEO_ID, context=ctx
            ),
            "batch_creation_failed",
        ),
        (
            DraftPersistRpcError("rpc_error", video_id=VIDEO_ID, context=ctx),
            "rpc_error",
        ),
        (
            DraftPersistNetworkError(
                "network_error", video_id=VIDEO_ID, context=ctx
            ),
            "network_error",
        ),
        (
            DraftPersistUnknownError(
                "unknown_persist_error", video_id=VIDEO_ID, context=ctx
            ),
            "unknown_persist_error",
        ),
        (
            DraftPersistError("something_else", video_id=VIDEO_ID, context=ctx),
            "unknown_persist_error",
        ),
    ]


def test_map_persist_error_subtype_to_locked_reason() -> None:
    from ingestion_service.mapping.persist import map_persist_error

    for error, reason in _cases():
        mapped = map_persist_error(error)
        payload = mapped.to_dict()

        assert mapped.stage == "persist"
        assert mapped.reason == reason
        assert mapped.exit_code == 1
        assert payload["ok"] is False
        assert payload["stage"] == "persist"
        assert payload["exit_code"] == 1
        assert mapped.message == f"persist {reason}"
        assert set(mapped.context).issubset(CONTEXT_ALLOWLIST)
        assert PLANTED_SECRET not in mapped.message
        assert PLANTED_SECRET not in payload["message"]
        assert PLANTED_SECRET not in str(mapped.context)
        assert RAW_POSTGRES not in mapped.message
        assert RAW_POSTGRES not in payload["message"]
        assert RAW_POSTGRES not in str(mapped.context)
        assert "SUPABASE_SECRET_KEY" not in mapped.context
        assert "Traceback" not in str(mapped.context)


def test_persist_reasons_is_exact_locked_set() -> None:
    from ingestion_service.mapping.persist import PERSIST_REASONS

    assert PERSIST_REASONS == LOCKED_REASONS


def test_mapping_package_exports_map_persist_error_alongside_existing() -> None:
    from ingestion_service import mapping

    assert mapping.map_persist_error is not None
    assert "map_persist_error" in mapping.__all__
    assert "map_captions_error" in mapping.__all__
    assert "map_article_error" in mapping.__all__
    assert "map_metadata_error" in mapping.__all__
    assert "map_url_error" in mapping.__all__
