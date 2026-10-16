"""Contract tests for digest recipients adapters (offline fakes — no network).

- ``SupabaseProfileRepository.list_digest_recipients`` maps usable ``profiles`` rows to
  ``Recipient`` (D-01/D-02/D-03) and maps SDK failures to ``PersistenceError``.
- ``SupabaseDigestPublisher`` forwards planned M as ``p_recipient_count`` and leaves
  ``p_delivery_status`` at the RPC default (D-06 option i / RESEARCH Q1) — no
  ``update_delivery``, no new migration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from backend.domain.errors import PersistenceError
from backend.domain.recipient import Recipient


class _FakeResult:
    def __init__(self, data: Any) -> None:
        self.data = data


class _FakeSelect:
    def __init__(self, rows: list[dict[str, Any]], error: Exception | None = None) -> None:
        self._rows = rows
        self._error = error

    def select(self, _cols: str = "*") -> "_FakeSelect":
        return self

    def execute(self) -> _FakeResult:
        if self._error is not None:
            raise self._error
        return _FakeResult(list(self._rows))


class _FakeProfileClient:
    """Minimal supabase Client stub exposing table(...).select(...).execute()."""

    def __init__(
        self,
        *,
        rows: list[dict[str, Any]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.rows = list(rows or [])
        self.error = error
        self.tables: list[str] = []

    def table(self, name: str) -> _FakeSelect:
        self.tables.append(name)
        return _FakeSelect(self.rows, self.error)


class _FakeRpc:
    def __init__(self, data: Any) -> None:
        self._data = data

    def execute(self) -> _FakeResult:
        return _FakeResult(self._data)


class _FakeRpcClient:
    def __init__(self, data: Any) -> None:
        self._data = data
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def rpc(self, name: str, params: dict[str, Any]) -> _FakeRpc:
        self.calls.append((name, dict(params)))
        return _FakeRpc(self._data)


_SENT_AT = datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc)

_PROFILE_ROWS = [
    {"id": "1", "email": "admin@sberbank.ru", "role": "admin", "display_name": "Админ"},
    {"id": "2", "email": "emp@sberbank.ru", "role": "employee", "display_name": None},
    {"id": "3", "email": "", "role": "employee", "display_name": None},
    {"id": "4", "email": "broken", "role": "employee", "display_name": None},
    {"id": "5", "email": "@nodomain", "role": "employee", "display_name": None},
]


def test_list_digest_recipients_selects_profiles_and_maps_usable_rows() -> None:
    """D-01/D-02/D-03: usable emails become Recipients; empty/malformed rows are dropped."""
    from supabase_integration.profile_repository import SupabaseProfileRepository

    client = _FakeProfileClient(rows=_PROFILE_ROWS)
    repo = SupabaseProfileRepository(client)

    recipients = list(repo.list_digest_recipients())

    assert all(isinstance(r, Recipient) for r in recipients)
    assert {r.email for r in recipients} == {"admin@sberbank.ru", "emp@sberbank.ru"}
    assert client.tables == ["profiles"]


def test_list_digest_recipients_maps_sdk_failure_to_persistence_error() -> None:
    """MAIL-04 boundary: an SDK failure on the list path is a PersistenceError, not raw."""
    from supabase_integration.profile_repository import SupabaseProfileRepository

    repo = SupabaseProfileRepository(_FakeProfileClient(error=RuntimeError("db down")))

    with pytest.raises(PersistenceError):
        repo.list_digest_recipients()


def test_claim_and_publish_forwards_planned_recipient_count() -> None:
    """D-06 option i: planned M rides ``p_recipient_count``; status stays RPC-default."""
    from supabase_integration.digest_publisher import SupabaseDigestPublisher

    payload = {
        "batch_id": 42,
        "issue_number": 4,
        "issue_url": "/issues/4",
        "delivery_status": "stubbed",
        "recipient_count": 5,
    }
    client = _FakeRpcClient(payload)
    publisher = SupabaseDigestPublisher(client)

    publication = publisher.claim_and_publish(
        batch_id=42,
        sent_at=_SENT_AT,
        period_label="2026-09-15",
        title="Digest CDS — 2026-09-15",
        recipient_count=5,
    )

    assert publication.recipient_count == 5
    name, params = client.calls[0]
    assert name == "claim_and_publish_digest"
    assert params["p_recipient_count"] == 5
    # D-06: no post-mail rewrite in this phase — leave the RPC default status.
    assert "p_delivery_status" not in params
