"""Contract tests for SupabaseDigestPublisher (offline stubs — no network).

CR-01 / WR-01 — atomic claim + publish + delivery stamp via claim_and_publish_digest RPC.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from backend.domain.errors import AlreadySentError, EmptySendPoolError, PersistenceError


class _FakeRpc:
    def __init__(self, *, data: Any = None, error: Exception | None = None) -> None:
        self._data = data
        self._error = error

    def execute(self) -> Any:
        if self._error is not None:
            raise self._error
        return type("_Result", (), {"data": self._data})()


class _FakeClient:
    def __init__(self, *, data: Any = None, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.table_calls: list[str] = []
        self._data = data
        self._error = error

    def rpc(self, name: str, params: dict[str, Any]) -> _FakeRpc:
        self.calls.append((name, params))
        return _FakeRpc(data=self._data, error=self._error)

    def table(self, name: str) -> Any:
        """Record table access — CR-01 forbids pre-RPC rank rewrites via table()."""
        self.table_calls.append(name)
        raise AssertionError(f"unexpected table access before/during claim RPC: {name}")


class _ApiError(Exception):
    """Mimics postgrest APIError carrying a Postgres errcode + message."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


_SENT_AT = datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc)


def test_claim_and_publish_returns_publication_from_rpc_payload() -> None:
    from supabase_integration.digest_publisher import SupabaseDigestPublisher

    payload = {
        "batch_id": 42,
        "issue_id": 7,
        "issue_number": 4,
        "issue_url": "/issues/4",
        "delivery_status": "stubbed",
        "recipient_count": 0,
        "item_count": 3,
    }
    client = _FakeClient(data=payload)
    publisher = SupabaseDigestPublisher(client)

    publication = publisher.claim_and_publish(
        batch_id=42,
        sent_at=_SENT_AT,
        period_label="2026-09-15",
        title="Digest CDS — 2026-09-15",
    )

    assert publication.batch_id == 42
    assert publication.issue_number == 4
    assert publication.issue_url == "/issues/4"
    assert publication.delivery_status == "stubbed"
    assert publication.recipient_count == 0

    # RPC invoked with the migration-005 parameter names.
    name, params = client.calls[0]
    assert name == "claim_and_publish_digest"
    assert params["p_batch_id"] == 42
    assert params["p_period_label"] == "2026-09-15"
    assert params["p_title"] == "Digest CDS — 2026-09-15"
    assert "p_sent_at" in params


def test_claim_and_publish_wraps_scalar_jsonb_in_list() -> None:
    """PostgREST may surface the jsonb payload directly (not list-wrapped)."""
    from supabase_integration.digest_publisher import SupabaseDigestPublisher

    payload = [
        {
            "batch_id": 42,
            "issue_number": 4,
            "issue_url": "/issues/4",
            "delivery_status": "stubbed",
            "recipient_count": 0,
        }
    ]
    publisher = SupabaseDigestPublisher(_FakeClient(data=payload))
    publication = publisher.claim_and_publish(
        batch_id=42, sent_at=_SENT_AT, period_label="2026-09-15", title="t"
    )
    assert publication.issue_number == 4


def test_already_sent_rpc_error_maps_to_already_sent() -> None:
    from supabase_integration.digest_publisher import SupabaseDigestPublisher

    error = _ApiError("P0001", "claim_and_publish_digest: batch 42 already sent or missing")
    publisher = SupabaseDigestPublisher(_FakeClient(error=error))

    with pytest.raises(AlreadySentError):
        publisher.claim_and_publish(
            batch_id=42, sent_at=_SENT_AT, period_label="2026-09-15", title="t"
        )


def test_empty_pool_rpc_error_maps_to_empty_send_pool() -> None:
    from supabase_integration.digest_publisher import SupabaseDigestPublisher

    error = _ApiError("23514", "claim_and_publish_digest: empty approved∩ready pool for batch 42")
    publisher = SupabaseDigestPublisher(_FakeClient(error=error))

    with pytest.raises(EmptySendPoolError):
        publisher.claim_and_publish(
            batch_id=42, sent_at=_SENT_AT, period_label="2026-09-15", title="t"
        )


def test_generic_sdk_error_maps_to_persistence_error() -> None:
    from supabase_integration.digest_publisher import SupabaseDigestPublisher

    publisher = SupabaseDigestPublisher(_FakeClient(error=RuntimeError("connection reset")))

    with pytest.raises(PersistenceError):
        publisher.claim_and_publish(
            batch_id=42, sent_at=_SENT_AT, period_label="2026-09-15", title="t"
        )


def test_claim_and_publish_passes_material_ids_to_rpc_without_rank_rewrite() -> None:
    """CR-01: material order must go into the RPC; no separate shortlist UPDATEs."""
    from supabase_integration.digest_publisher import SupabaseDigestPublisher

    payload = {
        "batch_id": 42,
        "issue_number": 4,
        "issue_url": "/issues/4",
        "delivery_status": "stubbed",
        "recipient_count": 0,
    }
    client = _FakeClient(data=payload)
    publisher = SupabaseDigestPublisher(client)

    publication = publisher.claim_and_publish(
        batch_id=42,
        sent_at=_SENT_AT,
        period_label="2026-09-15",
        title="Digest CDS — 2026-09-15",
        material_ids=[102, 101],
    )

    assert publication.issue_number == 4
    assert client.table_calls == []
    name, params = client.calls[0]
    assert name == "claim_and_publish_digest"
    assert params["p_material_ids"] == [102, 101]
