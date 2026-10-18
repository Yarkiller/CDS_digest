"""IssueRepository adapter — read/publish digest_issues via injected service_role client."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Protocol, Sequence

from backend.domain.errors import PersistenceError
from backend.domain.issue import Issue, IssueItem

_MATERIAL_ID_SLUG = re.compile(r"^material-(\d+)$")
_ISSUE_COLUMNS = "id,number,period_label,title,published_at"


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_material_id(client: _SupabaseClient, slug: str) -> int:
    """Resolve IssueItem.slug to materials.id (supports material-{id} from send_digest)."""
    match = _MATERIAL_ID_SLUG.match(slug)
    if match:
        return int(match.group(1))
    try:
        result = (
            client.table("materials")
            .select("id")
            .eq("slug", slug)
            .limit(1)
            .execute()
        )
    except PersistenceError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PersistenceError(f"materials lookup for publish failed: {exc}") from exc
    rows = getattr(result, "data", None) or []
    if not rows:
        raise PersistenceError(f"material slug not found for publish: {slug}")
    return int(rows[0]["id"])



def _row_to_issue(row: dict[str, Any], items: tuple[IssueItem, ...]) -> Issue:
    return Issue(
        id=str(row["id"]),
        number=int(row["number"]),
        period_label=str(row["period_label"]),
        title=str(row["title"]),
        editor=None,
        published_at=_parse_dt(row["published_at"]),
        items=items,
    )


def _item_from_join(row: dict[str, Any]) -> IssueItem | None:
    material = row.get("materials")
    if not isinstance(material, dict):
        return None
    return IssueItem(
        slug=str(material["slug"]),
        title=str(material["title"]),
        position=int(row["position"]),
        format=str(material.get("format") or "статья"),
        reading_minutes=int(material.get("reading_minutes") or 0),
        dek=str(material["dek"]) if material.get("dek") else None,
    )


class SupabaseIssueRepository:
    """IssueRepository against digest_issues + items (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def get_latest_published(self) -> Issue | None:
        try:
            result = (
                self._client.table("digest_issues")
                .select(_ISSUE_COLUMNS)
                .not_.is_("published_at", "null")
                .order("published_at", desc=True)
                .limit(1)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"digest_issues get_latest_published failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        return self._with_items(rows[0])

    def get_by_number(self, number: int) -> Issue | None:
        try:
            result = (
                self._client.table("digest_issues")
                .select(_ISSUE_COLUMNS)
                .eq("number", number)
                .not_.is_("published_at", "null")
                .limit(1)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"digest_issues get_by_number failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        return self._with_items(rows[0])

    def list_past_published(self) -> list[Issue]:
        current = self.get_latest_published()
        try:
            result = (
                self._client.table("digest_issues")
                .select(_ISSUE_COLUMNS)
                .not_.is_("published_at", "null")
                .order("published_at", desc=True)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"digest_issues list_past_published failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if current is not None:
            rows = [r for r in rows if str(r["id"]) != current.id]
        return [self._with_items(row) for row in rows]

    def _with_items(self, row: dict[str, Any]) -> Issue:
        issue_id = row["id"]
        try:
            items_result = (
                self._client.table("digest_issue_items")
                .select(
                    "position,material_id,"
                    "materials(slug,title,format,reading_minutes,dek)"
                )
                .eq("issue_id", issue_id)
                .order("position")
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"digest_issue_items load failed: {exc}") from exc

        item_rows = getattr(items_result, "data", None) or []
        items: list[IssueItem] = []
        for item_row in sorted(item_rows, key=lambda r: int(r.get("position") or 0)):
            parsed = _item_from_join(item_row)
            if parsed is not None:
                items.append(parsed)
        return _row_to_issue(row, tuple(items))

    def publish(
        self,
        *,
        period_label: str,
        title: str,
        editor: str | None,
        published_at: datetime,
        items: Sequence[IssueItem],
    ) -> Issue:
        """Insert digest_issues + digest_issue_items for approved ready set (D-88)."""
        # Schema has no editor column; byline stays on the returned Issue DTO only.
        try:
            existing = (
                self._client.table("digest_issues")
                .select("number")
                .order("number", desc=True)
                .limit(1)
                .execute()
            )
            existing_rows = getattr(existing, "data", None) or []
            next_number = int(existing_rows[0]["number"]) + 1 if existing_rows else 1

            insert_result = (
                self._client.table("digest_issues")
                .insert(
                    {
                        "number": next_number,
                        "period_label": period_label,
                        "title": title,
                        "published_at": _iso(published_at),
                    }
                )
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"digest_issues publish failed: {exc}") from exc

        issue_rows = getattr(insert_result, "data", None) or []
        if not issue_rows:
            raise PersistenceError("digest_issues publish returned no row")
        issue_id = int(issue_rows[0]["id"])

        item_payloads: list[dict[str, Any]] = []
        for item in items:
            material_id = _resolve_material_id(self._client, item.slug)
            item_payloads.append(
                {
                    "issue_id": issue_id,
                    "material_id": material_id,
                    "position": int(item.position),
                }
            )
        if item_payloads:
            try:
                self._client.table("digest_issue_items").insert(item_payloads).execute()
            except PersistenceError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise PersistenceError(f"digest_issue_items publish failed: {exc}") from exc

        return Issue(
            id=str(issue_id),
            number=next_number,
            period_label=period_label,
            title=title,
            editor=editor,
            published_at=published_at,
            items=tuple(items),
        )
