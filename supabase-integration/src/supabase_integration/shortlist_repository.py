"""ShortlistRepository adapter — digest_shortlist_* via injected service_role client."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Mapping, Protocol

from backend.domain.errors import AlreadySentError, PersistenceError, ShortlistNotFoundError
from backend.domain.shortlist import ShortlistBatch, ShortlistItem


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value)[:10])


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _item_from_row(row: dict[str, Any]) -> ShortlistItem:
    material = row.get("materials")
    if not isinstance(material, dict):
        material = {}
    factors: Mapping[str, Any] = row.get("score_factors") or {}
    if not isinstance(factors, Mapping):
        factors = {}
    score_raw = row.get("score")
    reading_raw = material.get("reading_minutes")
    reading_minutes: int | None = None
    if reading_raw is not None:
        try:
            reading_minutes = int(reading_raw)
        except (TypeError, ValueError) as exc:
            # W-5: a malformed joined column must map to the domain error at the
            # adapter boundary — never escape as an unhandled ValueError -> HTTP 500.
            raise PersistenceError(
                "shortlist item material_id="
                f"{row.get('material_id')!r} has non-numeric reading_minutes {reading_raw!r}"
            ) from exc
    return ShortlistItem(
        material_id=int(row["material_id"]),
        rank=int(row["rank"]),
        title=str(material.get("title") or ""),
        material_status=str(material.get("status") or "draft"),
        decision=str(row.get("decision") or "pending"),
        score=float(score_raw) if score_raw is not None else None,
        score_factors=dict(factors),
        decided_by=str(row["decided_by"]) if row.get("decided_by") else None,
        decided_at=_parse_dt(row.get("decided_at")),
        dek=(str(material["dek"]) if material.get("dek") is not None else None),
        body_markdown=(
            str(material["body_markdown"])
            if material.get("body_markdown") is not None
            else None
        ),
        provenance_label=(
            str(material["provenance_label"])
            if material.get("provenance_label") is not None
            else None
        ),
        slug=(str(material["slug"]) if material.get("slug") is not None else None),
        reading_minutes=reading_minutes,
    )


class SupabaseShortlistRepository:
    """ShortlistRepository against digest_shortlist_batches/items (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def get_current_batch(self) -> ShortlistBatch | None:
        try:
            result = (
                self._client.table("digest_shortlist_batches")
                .select("*")
                .is_("sent_at", "null")
                .order("week_start", desc=True)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"shortlist get_current_batch failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        return self._batch_with_items(rows[0])

    def get_latest_batch(self) -> ShortlistBatch | None:
        """Most recent batch regardless of sent_at (D-89 already-sent signal, WR-03).

        Same ordering as get_current_batch but WITHOUT the `sent_at IS NULL` filter, so
        send_digest can distinguish an already-sent latest batch (→ AlreadySentError / 409)
        from a genuinely empty pool (→ EmptySendPoolError / 400).
        """
        try:
            result = (
                self._client.table("digest_shortlist_batches")
                .select("*")
                .order("week_start", desc=True)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"shortlist get_latest_batch failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        return self._batch_with_items(rows[0])

    def set_decision(
        self,
        *,
        batch_id: int,
        material_id: int,
        decision: str,
        actor_user_id: str,
        decided_at: datetime,
    ) -> ShortlistBatch:
        try:
            result = (
                self._client.table("digest_shortlist_items")
                .update(
                    {
                        "decision": decision,
                        "decided_by": actor_user_id,
                        "decided_at": _iso(decided_at),
                    }
                )
                .eq("batch_id", batch_id)
                .eq("material_id", material_id)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"shortlist set_decision failed: {exc}") from exc

        updated = getattr(result, "data", None) or []
        if not updated:
            raise ShortlistNotFoundError(batch_id=batch_id, material_id=material_id)

        batch = self.get_current_batch()
        if batch is None or batch.id != batch_id:
            raise ShortlistNotFoundError(batch_id=batch_id, material_id=material_id)
        return batch

    def claim_sent(
        self,
        *,
        batch_id: int,
        sent_at: datetime,
    ) -> ShortlistBatch:
        """Atomic claim: UPDATE … WHERE sent_at IS NULL (ADMIN-07 / D-89).

        Zero-row update → AlreadySentError. Full claim_and_publish_digest RPC is
        available in migration 005 for single-transaction publish; this adapter
        matches the use-case split (claim then IssueRepository.publish).
        """
        try:
            result = (
                self._client.table("digest_shortlist_batches")
                .update({"sent_at": _iso(sent_at)})
                .eq("id", batch_id)
                .is_("sent_at", "null")
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"shortlist claim_sent failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            raise AlreadySentError(batch_id)

        return self._batch_with_items(rows[0])

    def release_claim(self, *, batch_id: int) -> None:
        """Clear sent_at after a failed publish (CR-01 compensation).

        Called by send_digest when IssueRepository.publish fails after a claim, so the
        batch returns to the unsent pool and a retry can succeed instead of being wedged
        as claimed-but-unpublished. Best-effort single UPDATE; SDK errors map to
        PersistenceError at the boundary.
        """
        try:
            (
                self._client.table("digest_shortlist_batches")
                .update({"sent_at": None})
                .eq("id", batch_id)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"shortlist release_claim failed: {exc}") from exc

    def _batch_with_items(self, row: dict[str, Any]) -> ShortlistBatch:
        batch_id = int(row["id"])
        try:
            items_result = (
                self._client.table("digest_shortlist_items")
                .select(
                    "batch_id,material_id,rank,score,score_factors,decision,"
                    "decided_by,decided_at,"
                    "materials(title,status,dek,body_markdown,slug,"
                    "provenance_label,reading_minutes)"
                )
                .eq("batch_id", batch_id)
                .order("rank")
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"shortlist items load failed: {exc}") from exc

        item_rows = getattr(items_result, "data", None) or []
        items = tuple(_item_from_row(item_row) for item_row in item_rows)
        return ShortlistBatch(
            id=batch_id,
            week_start=_parse_date(row["week_start"]),
            sent_at=_parse_dt(row.get("sent_at")),
            items=items,
        )
