"""ADUX-05 / D-06 / D-09 / D-10: status-only mark_material_ready (triage ready ≠ publish)."""

from datetime import datetime, timezone

import pytest

from backend.application.use_cases.mark_material_ready import mark_material_ready
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material, MaterialStatus
from backend.tests_support.in_memory import InMemoryMaterialRepository


def _draft(**overrides: object) -> Material:
    base = {
        "id": 1,
        "slug": "triage-draft",
        "title": "Triage draft",
        "dek": "dek",
        "body_markdown": "",
        "format": "статья",
        "status": MaterialStatus.DRAFT,
        "reading_minutes": 5,
        "provenance_label": "внешний текстовый источник",
        "source_id": 10,
        "roles": ("ds",),
        "tags": (),
        "related_material_ids": (),
        "published_at": None,
        "created_at": datetime(2026, 3, 20, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 3, 20, tzinfo=timezone.utc),
    }
    base.update(overrides)
    return Material(**base)  # type: ignore[arg-type]


def test_mark_material_ready_empty_body_draft_sets_ready_leaves_published_at() -> None:
    """D-06 / D-10: empty body still promotes; published_at untouched (ADUX-05)."""
    repo = InMemoryMaterialRepository([_draft(body_markdown="")])
    now = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)

    ready = mark_material_ready(repo, material_id=1, now=now)

    assert ready.status == MaterialStatus.READY
    assert ready.published_at is None
    assert ready.updated_at == now
    assert repo.get(1) is not None
    assert repo.get(1).status == MaterialStatus.READY


def test_mark_material_ready_missing_raises_not_found() -> None:
    repo = InMemoryMaterialRepository([])

    with pytest.raises(MaterialNotFoundError):
        mark_material_ready(repo, material_id=999)


def test_mark_material_ready_already_ready_is_noop() -> None:
    """D-09: already-ready returns same status without rewriting published_at (ADUX-05)."""
    published_at = datetime(2026, 9, 1, tzinfo=timezone.utc)
    material = _draft(
        status=MaterialStatus.READY,
        published_at=published_at,
        body_markdown="kept",
    )
    repo = InMemoryMaterialRepository([material])
    before = repo.get(1)

    result = mark_material_ready(repo, material_id=1, now=datetime(2026, 10, 3, tzinfo=timezone.utc))

    assert result.status == MaterialStatus.READY
    assert result.published_at == published_at
    assert result is before or result == before


def test_mark_materials_ready_order_preserving_partial_results() -> None:
    """D-08 / ADUX-05: batch never aborts; order matches ids; missing → material_not_found."""
    import backend.application.use_cases.mark_material_ready as mod

    assert hasattr(mod, "mark_materials_ready"), "mark_materials_ready batch helper missing (D-08)"
    mark_materials_ready = mod.mark_materials_ready

    found = _draft(id=10, slug="batch-10")
    repo = InMemoryMaterialRepository([found])
    now = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)

    results = mark_materials_ready(repo, [10, 999, 10], now=now)

    assert [r.material_id for r in results] == [10, 999, 10]
    assert results[0].ok is True
    assert results[0].status == MaterialStatus.READY.value
    assert results[0].error is None
    assert results[1].ok is False
    assert results[1].status is None
    assert results[1].error == "material_not_found"
    assert results[2].ok is True
    assert results[2].status == MaterialStatus.READY.value
    assert repo.get(10) is not None
    assert repo.get(10).status == MaterialStatus.READY


def test_mark_materials_ready_empty_ids_returns_empty() -> None:
    """D-08 / ADUX-05 empty probe: material_ids=[] → []."""
    import backend.application.use_cases.mark_material_ready as mod

    assert hasattr(mod, "mark_materials_ready"), "mark_materials_ready batch helper missing (D-08)"
    results = mod.mark_materials_ready(InMemoryMaterialRepository([]), [])
    assert results == []


def test_mark_materials_ready_persistence_error_is_per_id_never_aborts() -> None:
    """WR-01 / D-08: PersistenceError on one id must not abort the batch."""
    from backend.application.use_cases.mark_material_ready import mark_materials_ready
    from backend.domain.errors import PersistenceError

    class FlakyMaterialRepository(InMemoryMaterialRepository):
        def save(self, material: Material) -> Material:
            if material.id == 20:
                raise PersistenceError("db down")
            return super().save(material)

    repo = FlakyMaterialRepository(
        [
            _draft(id=10, slug="batch-ok-10"),
            _draft(id=20, slug="batch-fail-20"),
            _draft(id=30, slug="batch-ok-30"),
        ]
    )
    now = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)

    results = mark_materials_ready(repo, [10, 20, 30], now=now)

    assert [r.material_id for r in results] == [10, 20, 30]
    assert results[0].ok is True
    assert results[0].status == MaterialStatus.READY.value
    assert results[1].ok is False
    assert results[1].status is None
    assert results[1].error == "materials_unavailable"
    assert results[2].ok is True
    assert results[2].status == MaterialStatus.READY.value
    assert repo.get(10).status == MaterialStatus.READY
    assert repo.get(20).status == MaterialStatus.DRAFT
    assert repo.get(30).status == MaterialStatus.READY
