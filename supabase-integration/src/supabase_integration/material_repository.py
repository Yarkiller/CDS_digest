"""MaterialRepository adapter — read materials via injected service_role client."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from backend.domain.errors import PersistenceError
from backend.domain.material import Material, MaterialStatus


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _require_dt(value: Any, field: str) -> datetime:
    parsed = _parse_dt(value)
    if parsed is None:
        raise PersistenceError(f"materials row missing {field}")
    return parsed


def _tag_pairs(row: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    tags_raw = row.get("material_tags") or []
    if not isinstance(tags_raw, list):
        return ()
    return tuple(
        (str(tag["tag_slug"]), str(tag["tag_label"]))
        for tag in tags_raw
        if isinstance(tag, dict)
    )


def _related_ids(row: dict[str, Any]) -> tuple[str, ...]:
    relations_raw = row.get("material_relations") or []
    if not isinstance(relations_raw, list):
        return ()
    return tuple(
        str(rel["to_material_id"])
        for rel in relations_raw
        if isinstance(rel, dict) and rel.get("to_material_id") is not None
    )


def _role_tuple(row: dict[str, Any]) -> tuple[str, ...]:
    roles_raw = row.get("roles") or []
    if not isinstance(roles_raw, list):
        return ()
    return tuple(str(role) for role in roles_raw)


def _row_to_material(row: dict[str, Any]) -> Material:
    status_raw = str(row.get("status") or "draft")
    status = MaterialStatus.READY if status_raw == "ready" else MaterialStatus.DRAFT

    return Material(
        id=int(row["id"]),
        slug=str(row["slug"]),
        title=str(row["title"]),
        dek=str(row.get("dek") or ""),
        body_markdown=str(row["body_markdown"]),
        format=str(row.get("format") or "статья"),
        status=status,
        reading_minutes=int(row.get("reading_minutes") or 0),
        provenance_label=str(row["provenance_label"]),
        source_id=int(row["source_id"]) if row.get("source_id") is not None else None,
        roles=_role_tuple(row),
        tags=_tag_pairs(row),
        related_material_ids=_related_ids(row),
        published_at=_parse_dt(row.get("published_at")),
        created_at=_require_dt(row.get("created_at"), "created_at"),
        updated_at=_require_dt(row.get("updated_at"), "updated_at"),
    )


class SupabaseMaterialRepository:
    """MaterialRepository backed by public.materials (service_role reads)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def get(self, material_id: int) -> Material | None:
        return self._fetch_one("id", material_id)

    def get_by_slug(self, slug: str) -> Material | None:
        return self._fetch_one("slug", slug)

    def save(self, material: Material) -> Material:
        """Persist an existing material's domain-owned columns.

        The live `materials` table is a superset of the domain model: migration 007
        added NOT NULL provenance columns (`source_url`, `youtube_video_id`,
        `source_author`) plus a `bigint generated always as identity` primary key.
        A full-row upsert therefore cannot work — the INSERT half is rejected with
        428C9 (explicit identity value) and 23502 (unmodelled NOT NULL columns),
        which surfaced as HTTP 503 on the admin promote route. `save` only ever
        persists an existing aggregate (publish / draft→ready triage); new
        materials are created by the `persist_draft_and_enqueue` RPC. So update the
        domain-owned columns of the row addressed by `id`, leaving provenance and
        the identity untouched.
        """
        payload = {
            "slug": material.slug,
            "title": material.title,
            "dek": material.dek,
            "body_markdown": material.body_markdown,
            "format": material.format,
            "status": material.status.value,
            "reading_minutes": material.reading_minutes,
            "provenance_label": material.provenance_label,
            "source_id": material.source_id,
            "roles": list(material.roles),
            "published_at": material.published_at.isoformat() if material.published_at else None,
            "updated_at": material.updated_at.isoformat(),
        }
        try:
            result = (
                self._client.table("materials")
                .update(payload)
                .eq("id", material.id)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"materials save failed: {exc}") from exc

        data = getattr(result, "data", None) or []
        if not data:
            raise PersistenceError("materials update matched no rows")
        # Tags/relations are owned by seed/editorial paths; return domain object as saved.
        return material

    def _fetch_one(self, column: str, value: Any) -> Material | None:
        try:
            result = (
                self._client.table("materials")
                .select(
                    "id,slug,title,dek,body_markdown,format,status,reading_minutes,"
                    "provenance_label,source_id,roles,published_at,created_at,updated_at,"
                    "material_tags(tag_slug,tag_label),"
                    "material_relations!material_relations_from_material_id_fkey(to_material_id)"
                )
                .eq(column, value)
                .limit(1)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"materials fetch by {column} failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        material = _row_to_material(rows[0])
        return self._filter_ready_relations(material)

    def _filter_ready_relations(self, material: Material) -> Material:
        """Keep related ids only when the target material is ready (MAT honesty)."""
        if not material.related_material_ids:
            return material
        ready_ids: list[str] = []
        for related_id in material.related_material_ids:
            try:
                mid = int(related_id)
            except ValueError:
                continue
            try:
                status_result = (
                    self._client.table("materials")
                    .select("id,status")
                    .eq("id", mid)
                    .limit(1)
                    .execute()
                )
            except Exception as exc:  # noqa: BLE001
                raise PersistenceError(
                    f"materials related status check failed: {exc}"
                ) from exc
            status_rows = getattr(status_result, "data", None) or []
            if status_rows and str(status_rows[0].get("status")) == "ready":
                ready_ids.append(related_id)
        if tuple(ready_ids) == material.related_material_ids:
            return material
        from dataclasses import replace

        return replace(material, related_material_ids=tuple(ready_ids))
