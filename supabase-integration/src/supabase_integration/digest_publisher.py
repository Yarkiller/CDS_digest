"""DigestPublisher adapter — atomic claim+publish via claim_and_publish_digest RPC (CR-01/WR-01).

Wraps migration 006's ``public.claim_and_publish_digest(..., p_material_ids bigint[])``
SECURITY INVOKER function (service_role only). The RPC claims the unsent batch, inserts
digest_issues + items for approved∩ready (optionally ordered by ``p_material_ids``), and
stamps delivery columns — all in a single transaction.

When ``material_ids`` is provided (G-05-1), they are passed as ``p_material_ids`` so issue
positions are assigned inside the RPC — never via separate shortlist rank UPDATEs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from backend.application.ports.digest_publisher import DigestPublication
from backend.domain.errors import AlreadySentError, EmptySendPoolError, PersistenceError


class _SupabaseClient(Protocol):
    def rpc(self, name: str, params: dict[str, Any]) -> Any: ...


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _map_rpc_error(exc: Exception, batch_id: int) -> Exception | None:
    """Translate Postgres errcodes raised by claim_and_publish_digest into domain errors.

    The RPC raises SQLSTATE ``P0001`` when the batch is already sent/missing (D-89) and a
    ``check_violation`` (``23514``) for an empty approved∩ready pool. PostgREST surfaces these
    as an APIError carrying ``code``/``message``; we also match on message text as a fallback.
    """
    code = str(getattr(exc, "code", "") or "")
    message = str(getattr(exc, "message", "") or exc)
    text = f"{code} {message}".lower()
    if code == "P0001" or "already sent" in text or "already claimed" in text:
        return AlreadySentError(batch_id)
    if code == "23514" or "check_violation" in text or "empty approved" in text:
        return EmptySendPoolError(batch_id=batch_id)
    return None


class SupabaseDigestPublisher:
    """DigestPublisher against the claim_and_publish_digest RPC (service_role client)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def claim_and_publish(
        self,
        *,
        batch_id: int,
        sent_at: datetime,
        period_label: str,
        title: str,
        material_ids: list[int] | None = None,
        recipient_count: int = 0,
    ) -> DigestPublication:
        params: dict[str, Any] = {
            "p_batch_id": batch_id,
            "p_sent_at": _iso(sent_at),
            "p_period_label": period_label,
            "p_title": title,
            # D-06 option i: stamp the planned audience M at claim. The live N/status ride
            # the API result + pings — p_delivery_status stays at the RPC default (no
            # post-mail update_delivery in this phase).
            "p_recipient_count": recipient_count,
        }
        if material_ids:
            params["p_material_ids"] = list(material_ids)
        try:
            result = self._client.rpc("claim_and_publish_digest", params).execute()
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK/Postgres failures at boundary
            mapped = _map_rpc_error(exc, batch_id)
            if mapped is not None:
                raise mapped from exc
            raise PersistenceError(f"claim_and_publish_digest failed: {exc}") from exc

        data = getattr(result, "data", None)
        row = data[0] if isinstance(data, list) and data else data
        if not isinstance(row, dict):
            raise PersistenceError("claim_and_publish_digest returned no row")

        return DigestPublication(
            batch_id=int(row.get("batch_id", batch_id)),
            issue_number=int(row["issue_number"]),
            issue_url=str(row["issue_url"]),
            delivery_status=str(row.get("delivery_status") or "stubbed"),
            recipient_count=int(row.get("recipient_count") or 0),
        )
