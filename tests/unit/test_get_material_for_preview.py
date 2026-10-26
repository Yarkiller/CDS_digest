"""get_material_for_preview — draft-only admin preview by slug; ready/missing → not found (D-04/D-12)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.application.use_cases.get_material_for_preview import get_material_for_preview
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
        title="Draft article",
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


def test_get_material_for_preview_returns_draft_by_slug() -> None:
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    repo = InMemoryMaterialRepository([draft])
    material = get_material_for_preview(repo, "secret-draft")
    assert material.slug == "secret-draft"
    assert material.status == MaterialStatus.DRAFT


def test_get_material_for_preview_ready_raises_not_found() -> None:
    ready = _material(slug="rag-systems", status=MaterialStatus.READY)
    repo = InMemoryMaterialRepository([ready])
    with pytest.raises(MaterialNotFoundError):
        get_material_for_preview(repo, "rag-systems")


def test_get_material_for_preview_missing_slug_raises_not_found() -> None:
    repo = InMemoryMaterialRepository([])
    with pytest.raises(MaterialNotFoundError):
        get_material_for_preview(repo, "does-not-exist")
