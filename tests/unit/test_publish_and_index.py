"""RED→GREEN: material publish gate and knowledge chunk indexing."""

from datetime import datetime, timezone

import pytest

from backend.domain.errors import MaterialNotReadyError, MaterialValidationError
from backend.domain.material import Material, MaterialStatus
from backend.application.use_cases.publish_material import publish_material
from backend.application.use_cases.index_material_chunks import index_material_chunks
from backend.tests_support.in_memory import InMemoryMaterialRepository, InMemoryKnowledgeChunkRepository


def _draft(**overrides: object) -> Material:
    base = {
        "id": 1,
        "slug": "rag-systems",
        "title": "Building Production RAG Systems",
        "dek": "Как быстро находить фрагменты регламентов.",
        "body_markdown": "## Intro\n\nParagraph one.\n\n## Search\n\nParagraph two.",
        "format": "статья",
        "status": MaterialStatus.DRAFT,
        "reading_minutes": 8,
        "provenance_label": "внешний текстовый источник",
        "source_id": 10,
        "roles": ("ds", "sva"),
        "tags": (("rag", "RAG"), ("llm", "LLM")),
        "related_material_ids": (),
        "published_at": None,
        "created_at": datetime(2026, 3, 20, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 3, 20, tzinfo=timezone.utc),
    }
    base.update(overrides)
    return Material(**base)  # type: ignore[arg-type]


def test_publish_material_sets_ready_when_quality_gate_passes() -> None:
    repo = InMemoryMaterialRepository([_draft()])
    published = publish_material(repo, material_id=1)

    assert published.status == MaterialStatus.READY
    assert published.published_at is not None


def test_publish_material_rejects_empty_body() -> None:
    repo = InMemoryMaterialRepository([_draft(body_markdown="")])

    with pytest.raises(MaterialValidationError):
        publish_material(repo, material_id=1)


def test_index_material_chunks_only_for_ready_materials() -> None:
    repo = InMemoryMaterialRepository([_draft()])
    chunks = InMemoryKnowledgeChunkRepository()

    with pytest.raises(MaterialNotReadyError):
        index_material_chunks(
            materials=repo,
            chunks=chunks,
            material_id=1,
            embedding_model_id="foundry-embed-v1",
            embed=lambda text: [0.01] * 1024,
        )


def test_index_material_chunks_creates_atomic_chunks_from_article() -> None:
    material = _draft(status=MaterialStatus.READY, published_at=datetime(2026, 3, 21, tzinfo=timezone.utc))
    repo = InMemoryMaterialRepository([material])
    chunks = InMemoryKnowledgeChunkRepository()

    created = index_material_chunks(
        materials=repo,
        chunks=chunks,
        material_id=1,
        embedding_model_id="foundry-embed-v1",
        embed=lambda text: [0.02] * 1024,
    )

    assert len(created) >= 2
    assert all(c.material_id == 1 for c in created)
    assert [c.chunk_index for c in created] == list(range(len(created)))
    assert all(len(c.embedding) == 1024 for c in created)
