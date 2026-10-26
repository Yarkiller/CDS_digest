"""RED→GREEN: SupabaseDraftPersister mocked-client contract (D-01, D-04, D-05)."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from typing import Any

from data_collection.dto.material_draft import MaterialDraft


VIDEO_ID = "dQw4w9WgXcQ"
SLUG = "kak-ispolzovat-pgvector-dQw4w9WgXcQ"
PLANTED_SECRET = "SUPABASE_SECRET_KEY=s3cr3t-k3y-09"
RAW_POSTGRES = 'duplicate key value violates unique constraint "materials_youtube_video_id_key"'


class APIConnectionError(Exception):
    """Mock of the supabase/httpx network failure type."""


class PostgrestAPIError(Exception):
    """Mock PostgREST/Postgres error with a SQLSTATE or HTTP `.code`."""

    def __init__(self, code: str | int, message: str = RAW_POSTGRES) -> None:
        self.code = code
        super().__init__(message)


class _FakeExecuteResult:
    def __init__(self, data: object) -> None:
        self.data = data


class _FakeRpc:
    def __init__(self, owner: "_FakeClient") -> None:
        self._owner = owner

    def execute(self) -> _FakeExecuteResult:
        if self._owner.error is not None:
            raise self._owner.error
        return _FakeExecuteResult(self._owner.data)


class _FakeClient:
    def __init__(self, data: object, error: BaseException | None = None) -> None:
        self.data = data
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def rpc(self, name: str, params: dict[str, Any]) -> _FakeRpc:
        self.calls.append((name, params))
        return _FakeRpc(self)


def _draft(**overrides: object) -> MaterialDraft:
    published = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)
    base: dict[str, object] = {
        "title": "Как использовать pgvector",
        "dek": "dek",
        "body_markdown": "body",
        "source_url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "youtube_video_id": VIDEO_ID,
        "source_author": "Author",
        "provenance_label": "YouTube · Author",
        "source_published_at": published,
        "roles": ["employee", "ds"],
        "slug": SLUG,
        "reading_minutes": 2,
    }
    base.update(overrides)
    return MaterialDraft(**base)


def _happy_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "material_id": 101,
        "slug": SLUG,
        "batch_id": 7,
        "rank": 3,
        "already_saved": False,
    }
    data.update(overrides)
    return data


def test_persist_returns_result_from_mocked_rpc() -> None:
    spec = importlib.util.find_spec("ingestion_service.adapters.supabase_persist")
    assert spec is not None, "supabase_persist adapter must exist"

    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister
    from ingestion_service.application.ports.persist import PersistResult

    client = _FakeClient(_happy_data())
    persister = SupabaseDraftPersister(client, batch_size=5)
    result = persister.persist(_draft())

    assert result == PersistResult(101, SLUG, 7, 3, already_saved=False)
    assert client.calls[0][0] == "persist_draft_and_enqueue"
    params = client.calls[0][1]
    draft = _draft()
    assert params["p_youtube_video_id"] == VIDEO_ID
    assert params["p_slug"] == SLUG
    assert params["p_roles"] == ["employee", "ds"]
    assert params["p_batch_size"] == 5
    assert params["p_source_published_at"] == "2026-03-20T12:00:00+00:00"
    assert params["p_source_url"] == draft.source_url
    assert params["p_source_author"] == draft.source_author
    assert params["p_provenance_label"] == draft.provenance_label
    assert params["p_title"] == draft.title
    assert params["p_dek"] == draft.dek
    assert params["p_body_markdown"] == draft.body_markdown
    assert params["p_reading_minutes"] == draft.reading_minutes


def test_persist_maps_already_saved_true_with_stored_slug() -> None:
    """D-09 / D-12: conflict RPC returns stored slug + already_saved true (CLI-02)."""
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister
    from ingestion_service.application.ports.persist import PersistResult

    stored_slug = "stored-slug-from-materials"
    client = _FakeClient(_happy_data(slug=stored_slug, already_saved=True))
    result = SupabaseDraftPersister(client, batch_size=5).persist(_draft())

    assert result == PersistResult(101, stored_slug, 7, 3, already_saved=True)


def test_persist_missing_already_saved_raises_rpc_error() -> None:
    """Adapter requires already_saved in RPC payload (CLI-02)."""
    from ingestion_service.adapters.persist_errors import DraftPersistRpcError
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    payload = {
        "material_id": 101,
        "slug": SLUG,
        "batch_id": 7,
        "rank": 3,
    }
    client = _FakeClient(payload)
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistRpcError as exc:
        assert "rpc_error" in str(exc) or (
            exc.args and exc.args[0] == "rpc_error"
        )
        return
    raise AssertionError("expected DraftPersistRpcError")


def test_persist_forwards_required_provenance_params() -> None:
    """PERS-01: a successful persist must carry source_url, video id, author, published_at, label."""
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    draft = _draft()
    client = _FakeClient(_happy_data())
    SupabaseDraftPersister(client, batch_size=5).persist(draft)

    assert client.calls[0][0] == "persist_draft_and_enqueue"
    params = client.calls[0][1]
    assert params["p_source_url"] == draft.source_url
    assert params["p_youtube_video_id"] == draft.youtube_video_id
    assert params["p_source_author"] == draft.source_author
    assert params["p_source_published_at"] == "2026-03-20T12:00:00+00:00"
    assert params["p_provenance_label"] == draft.provenance_label
    assert params["p_title"] == draft.title
    assert params["p_dek"] == draft.dek
    assert params["p_body_markdown"] == draft.body_markdown
    assert params["p_reading_minutes"] == draft.reading_minutes


def test_persist_never_forwards_status_or_ready_to_rpc() -> None:
    """PERS-01: status is hard-coded to draft inside Postgres; adapter must not send it."""
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(_happy_data())
    SupabaseDraftPersister(client, batch_size=5).persist(_draft())

    params = client.calls[0][1]
    keys = {key.lower() for key in params}
    assert "status" not in keys
    assert "p_status" not in keys
    assert "ready" not in keys
    assert "p_ready" not in keys
    assert not any("status" in key.lower() for key in params)
    assert all(str(value).lower() != "ready" for value in params.values())


def test_persist_passes_none_published_at() -> None:
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(_happy_data())
    SupabaseDraftPersister(client, batch_size=5).persist(
        _draft(source_published_at=None)
    )
    assert client.calls[0][1]["p_source_published_at"] is None


def test_api_connection_error_maps_to_network_error() -> None:
    from ingestion_service.adapters.persist_errors import DraftPersistNetworkError
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(_happy_data(), error=APIConnectionError(PLANTED_SECRET))
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistNetworkError as exc:
        _assert_safe_error(exc)
        return
    raise AssertionError("expected DraftPersistNetworkError")


def test_unique_violation_23505_maps_to_conflict_error() -> None:
    from ingestion_service.adapters.persist_errors import DraftPersistConflictError
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(
        _happy_data(), error=PostgrestAPIError("23505", RAW_POSTGRES)
    )
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistConflictError as exc:
        _assert_safe_error(exc)
        return
    raise AssertionError("expected DraftPersistConflictError")


def test_rpc_p0001_maps_to_batch_error() -> None:
    from ingestion_service.adapters.persist_errors import DraftPersistBatchError
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(
        _happy_data(), error=PostgrestAPIError("P0001", RAW_POSTGRES)
    )
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistBatchError as exc:
        _assert_safe_error(exc)
        return
    raise AssertionError("expected DraftPersistBatchError")


def test_check_violation_maps_to_batch_error() -> None:
    from ingestion_service.adapters.persist_errors import DraftPersistBatchError
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(
        _happy_data(),
        error=PostgrestAPIError("check_violation", RAW_POSTGRES),
    )
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistBatchError as exc:
        _assert_safe_error(exc)
        return
    raise AssertionError("expected DraftPersistBatchError")


def test_sqlstate_23514_maps_to_batch_error() -> None:
    """D-06 / PERS-02: SQLSTATE 23514 classifies like check_violation → batch_creation_failed."""
    from ingestion_service.adapters.persist_errors import DraftPersistBatchError
    from ingestion_service.adapters.supabase_persist import (
        _BATCH_CODES,
        SupabaseDraftPersister,
    )

    assert "check_violation" in _BATCH_CODES
    assert "23514" in _BATCH_CODES
    assert "P0001" in _BATCH_CODES

    client = _FakeClient(
        _happy_data(),
        error=PostgrestAPIError("23514", RAW_POSTGRES),
    )
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistBatchError as exc:
        _assert_safe_error(exc)
        assert exc.reason == "batch_creation_failed"
        assert exc.context.get("reason") == "batch_creation_failed"
        return
    raise AssertionError("expected DraftPersistBatchError")


def test_other_sdk_error_maps_to_rpc_error() -> None:
    from ingestion_service.adapters.persist_errors import DraftPersistRpcError
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(
        _happy_data(), error=PostgrestAPIError("PGRST116", RAW_POSTGRES)
    )
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistRpcError as exc:
        _assert_safe_error(exc)
        return
    raise AssertionError("expected DraftPersistRpcError")


def test_int_http_503_maps_to_rpc_error_not_network() -> None:
    """D-06 / PERS-02: numeric HTTP gateway status → rpc_error (not network_error)."""
    from ingestion_service.adapters import supabase_persist as persist_mod
    from ingestion_service.adapters.persist_errors import (
        DraftPersistNetworkError,
        DraftPersistRpcError,
    )
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    err = PostgrestAPIError(503, RAW_POSTGRES)
    http_status = getattr(persist_mod, "_http_status_code", None)
    assert callable(http_status), "D-06: _http_status_code must recognize int HTTP status"
    assert http_status(err) == 503

    client = _FakeClient(_happy_data(), error=err)
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistNetworkError as exc:
        raise AssertionError(
            "D-06: int HTTP must be rpc_error, not network_error"
        ) from exc
    except DraftPersistRpcError as exc:
        _assert_safe_error(exc)
        assert exc.reason == "rpc_error"
        assert exc.context.get("reason") == "rpc_error"
        return
    raise AssertionError("expected DraftPersistRpcError")


def test_unexpected_exception_maps_to_unknown_error() -> None:
    from ingestion_service.adapters.persist_errors import DraftPersistUnknownError
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(_happy_data(), error=RuntimeError(PLANTED_SECRET))
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistUnknownError as exc:
        _assert_safe_error(exc)
        return
    raise AssertionError("expected DraftPersistUnknownError")


def _assert_safe_error(exc: Any) -> None:
    assert exc.video_id == VIDEO_ID
    dumped = f"{exc} {exc.context}"
    assert PLANTED_SECRET not in dumped
    assert "SUPABASE_SECRET_KEY" not in dumped
    assert RAW_POSTGRES not in dumped
    assert "Traceback" not in dumped
    assert set(exc.context).issubset({"video_id", "slug", "batch_id", "reason"})
