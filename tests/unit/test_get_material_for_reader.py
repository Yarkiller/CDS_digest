"""get_material_for_reader — ready-only by slug; draft treated as not found (D-39)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.application.use_cases.get_material_for_reader import get_material_for_reader
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material, MaterialStatus
from backend.tests_support.in_memory import InMemoryMaterialRepository


def _material(
    *,
    slug: str,
    status: MaterialStatus,
    material_id: int = 1,
    related: tuple[str, ...] = (),
) -> Material:
    now = datetime(2026, 3, 20, tzinfo=timezone.utc)
    return Material(
        id=material_id,
        slug=slug,
        title="Ready article",
        dek="",
        body_markdown="## Intro\n\nBody.",
        format="статья",
        status=status,
        reading_minutes=5,
        provenance_label="внутренний разбор",
        source_id=None,
        roles=("ds",),
        tags=(("RAG", "rag"),),
        related_material_ids=related,
        published_at=now if status == MaterialStatus.READY else None,
        created_at=now,
        updated_at=now,
    )


def test_get_material_for_reader_returns_ready_by_slug() -> None:
    ready = _material(slug="rag-systems", status=MaterialStatus.READY)
    repo = InMemoryMaterialRepository([ready])
    material = get_material_for_reader(repo, "rag-systems")
    assert material.slug == "rag-systems"
    assert material.status == MaterialStatus.READY


def test_get_material_for_reader_draft_raises_not_found() -> None:
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    repo = InMemoryMaterialRepository([draft])
    with pytest.raises(MaterialNotFoundError):
        get_material_for_reader(repo, "secret-draft")


def test_get_material_for_reader_missing_slug_raises_not_found() -> None:
    repo = InMemoryMaterialRepository([])
    with pytest.raises(MaterialNotFoundError):
        get_material_for_reader(repo, "does-not-exist")
