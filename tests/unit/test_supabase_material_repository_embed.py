"""Offline regression for the live `materials` write/read path (G-14-1 / G-14-4).

Two independent live-only failures produced the same HTTP 503 on
`POST /admin/materials/{id}/ready`:

1. **Read** — `materials` <-> `material_relations` has two foreign keys
   (`from_material_id` / `to_material_id`), so a bare
   `material_relations(to_material_id)` embed is ambiguous and PostgREST rejects
   it with PGRST201; every live `get()` / `get_by_slug()` raised `PersistenceError`.
2. **Write** — the live `materials` table is a superset of the domain model.
   Migration 007 added `source_url` / `youtube_video_id` / `source_author` as NOT
   NULL, and `id` is `bigint generated always as identity`. A full-row upsert is
   therefore impossible: the INSERT half fails with 428C9 (explicit identity) and
   23502 (unmodelled NOT NULL column). `save` only ever persists an existing
   aggregate, so it must UPDATE the domain-owned columns and leave provenance and
   the identity untouched.

These tests use a fake client that simulates those live rejections, so the real
shapes are exercised without a network/DB round-trip.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from backend.domain.errors import PersistenceError
from backend.domain.material import Material, MaterialStatus


class _PGRST201Error(Exception):
    """Mimics `postgrest.exceptions.APIError` for an ambiguous embed."""

    code = "PGRST201"


class _GeneratedAlwaysError(Exception):
    """Mimics the Postgres 428C9 rejection of a write to a GENERATED ALWAYS identity."""

    code = "428C9"


class _NotNullViolationError(Exception):
    """Mimics a Postgres 23502 NOT NULL violation on a full-row INSERT."""

    code = "23502"


class _FakeResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op = "select"
        self._select_cols = "*"
        self._filters: list[tuple[str, Any]] = []
        self._limit: int | None = None
        self._write_payload: dict[str, Any] | None = None
        self._on_conflict: str | None = None

    def select(self, cols: str = "*") -> "_FakeQuery":
        self._select_cols = cols
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        return self

    def limit(self, n: int) -> "_FakeQuery":
        self._limit = n
        return self

    def upsert(
        self, payload: dict[str, Any], *, on_conflict: str | None = None
    ) -> "_FakeQuery":
        self._op = "upsert"
        self._write_payload = dict(payload)
        self._on_conflict = on_conflict
        return self

    def update(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "update"
        self._write_payload = dict(payload)
        return self

    def execute(self) -> _FakeResult:
        if self._op in ("upsert", "update"):
            return self._write()
        return self._read()

    def _write(self) -> _FakeResult:
        assert self._write_payload is not None
        self._table.write_calls.append(
            {
                "op": self._op,
                "payload": dict(self._write_payload),
                "on_conflict": self._on_conflict,
                "filters": list(self._filters),
            }
        )
        if self._op == "upsert" and self._table.name == "materials":
            # A full-row INSERT must satisfy every NOT NULL column on the live
            # table, including the migration-007 provenance columns the domain
            # does not model, and must not write the generated identity.
            for required in ("source_url", "youtube_video_id", "source_author"):
                if not self._write_payload.get(required):
                    raise _NotNullViolationError(
                        f'null value in column "{required}" violates not-null constraint'
                    )
            if "id" in self._write_payload:
                raise _GeneratedAlwaysError(
                    'cannot insert a non-DEFAULT value into column "id"'
                )
        matched = list(self._table.rows)
        for column, value in self._filters:
            matched = [r for r in matched if r.get(column) == value]
        for row in matched:
            row.update(self._write_payload)
        return _FakeResult(matched)

    def _read(self) -> _FakeResult:
        self._table.select_specs.append(self._select_cols)
        # PostgREST rejects the ambiguous embed before returning any rows.
        if self._table.name == "materials" and "material_relations(" in self._select_cols:
            raise _PGRST201Error(
                "Could not embed because more than one relationship was found "
                "for 'materials' and 'material_relations'"
            )
        matched = list(self._table.rows)
        for column, value in self._filters:
            matched = [r for r in matched if r.get(column) == value]
        if self._limit is not None:
            matched = matched[: self._limit]
        return _FakeResult(matched)


class _FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: list[dict[str, Any]] = []
        self.select_specs: list[str] = []
        self.write_calls: list[dict[str, Any]] = []

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class _FakeClient:
    def __init__(self) -> None:
        self.tables = {"materials": _FakeTable("materials")}

    def table(self, name: str) -> _FakeQuery:
        return self.tables[name].query()


def _seed_ready_material(client: _FakeClient) -> None:
    client.tables["materials"].rows.append(
        {
            "id": 1,
            "slug": "rag-systems",
            "title": "Building Production RAG Systems",
            "dek": "",
            "body_markdown": "## Body\n\nText.",
            "format": "статья",
            "status": "ready",
            "reading_minutes": 5,
            "provenance_label": "внешний текстовый источник",
            "source_id": None,
            "roles": [],
            "published_at": "2026-03-20T12:00:00+00:00",
            "created_at": "2026-03-20T12:00:00+00:00",
            "updated_at": "2026-03-20T12:00:00+00:00",
            # Migration-007 provenance columns — NOT NULL live, unmodelled by the domain.
            "source_url": "https://example.invalid/legacy-rag-systems",
            "youtube_video_id": "legacy-rag-systems",
            "source_author": "legacy",
            "source_published_at": None,
            # Empty embeds: `_filter_ready_relations` short-circuits (no extra queries).
            "material_tags": [],
            "material_relations": [],
        }
    )


def _draft_repo(client: _FakeClient):
    """Return a repo plus a fetched draft material ready to be promoted to ready."""
    from supabase_integration import SupabaseMaterialRepository

    _seed_ready_material(client)
    client.tables["materials"].rows[0]["status"] = "draft"
    repo = SupabaseMaterialRepository(client)
    material = repo.get(1)
    assert material is not None
    assert material.status == MaterialStatus.DRAFT
    return repo, material.with_ready_status(now=material.updated_at)


def test_get_returns_material_under_ambiguous_embed_rejection() -> None:
    from supabase_integration import SupabaseMaterialRepository

    client = _FakeClient()
    _seed_ready_material(client)
    repo = SupabaseMaterialRepository(client)

    material = repo.get(1)

    assert isinstance(material, Material)
    assert material.slug == "rag-systems"
    assert material.status == MaterialStatus.READY


def test_get_by_slug_returns_material_under_ambiguous_embed_rejection() -> None:
    from supabase_integration import SupabaseMaterialRepository

    client = _FakeClient()
    _seed_ready_material(client)
    repo = SupabaseMaterialRepository(client)

    material = repo.get_by_slug("rag-systems")

    assert isinstance(material, Material)
    assert material.slug == "rag-systems"


def test_fetch_one_disambiguates_relations_embed_and_keeps_tags_unhinted() -> None:
    from supabase_integration import SupabaseMaterialRepository

    client = _FakeClient()
    _seed_ready_material(client)
    repo = SupabaseMaterialRepository(client)

    repo.get(1)

    specs = client.tables["materials"].select_specs
    assert specs, "materials.select(...) was never called"
    spec = specs[-1]
    # Disambiguated by an FK hint, e.g. material_relations!<fk>(to_material_id).
    assert "material_relations!" in spec
    assert re.search(r"material_relations![^(]+\(to_material_id\)", spec)
    assert "material_relations(to_material_id)" not in spec
    # Single FK -> intentionally left unhinted.
    assert "material_tags(tag_slug,tag_label)" in spec


def test_save_updates_owned_columns_by_id_instead_of_full_row_upsert() -> None:
    """A full-row write is impossible live (identity + NOT NULL provenance)."""
    client = _FakeClient()
    repo, updated = _draft_repo(client)

    # Must not raise _NotNullViolationError / _GeneratedAlwaysError.
    repo.save(updated)

    call = client.tables["materials"].write_calls[-1]
    assert call["op"] == "update"
    assert ("id", updated.id) in call["filters"]
    payload = call["payload"]
    assert "id" not in payload
    assert "source_url" not in payload
    assert "youtube_video_id" not in payload
    assert payload["status"] == "ready"


def test_save_preserves_unmodelled_provenance_columns_on_the_live_row() -> None:
    client = _FakeClient()
    repo, updated = _draft_repo(client)

    repo.save(updated)

    row = client.tables["materials"].rows[0]
    assert row["status"] == "ready"
    # The update must not clobber columns the domain does not own.
    assert row["source_url"] == "https://example.invalid/legacy-rag-systems"
    assert row["youtube_video_id"] == "legacy-rag-systems"
    assert row["source_author"] == "legacy"
    assert row["id"] == 1


def test_save_signals_when_no_row_matches() -> None:
    client = _FakeClient()
    repo, updated = _draft_repo(client)

    with pytest.raises(PersistenceError):
        repo.save(_with_id(updated, 999))


def _with_id(material: Material, new_id: int) -> Material:
    from dataclasses import replace

    return replace(material, id=new_id)
