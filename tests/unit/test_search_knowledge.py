"""RED→GREEN: hybrid knowledge search returns material-facing hits (KNOW-01 / D-59 / D-61)."""

from datetime import datetime, timezone

import pytest

from backend.application.ports.query_embedder import StubQueryEmbedder
from backend.application.use_cases.search_knowledge import search_knowledge
from backend.domain.errors import KnowledgeQueryValidationError
from backend.domain.knowledge import KnowledgeChunk
from backend.domain.material import Material, MaterialStatus
from backend.tests_support.in_memory import (
    InMemoryKnowledgeChunkRepository,
    InMemoryMaterialRepository,
)


def _ready(
    *,
    material_id: int,
    slug: str,
    title: str = "Title",
    roles: tuple[str, ...] = ("ds", "sva"),
) -> Material:
    now = datetime(2026, 3, 17, tzinfo=timezone.utc)
    return Material(
        id=material_id,
        slug=slug,
        title=title,
        dek="dek",
        body_markdown="## Setup\n\nUse HNSW indexes for semantic search.",
        format="статья",
        status=MaterialStatus.READY,
        reading_minutes=6,
        provenance_label="внешний текстовый источник",
        source_id=None,
        roles=roles,
        tags=(("pgvector", "pgvector"),),
        related_material_ids=(),
        published_at=now,
        created_at=now,
        updated_at=now,
    )


def _chunk(
    *,
    material_id: int,
    chunk_index: int,
    content_md: str,
    embedding: list[float],
    chunk_id: int = 1,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=chunk_id,
        material_id=material_id,
        chunk_index=chunk_index,
        heading="Setup",
        content_md=content_md,
        embedding=embedding,
        embedding_model_id="foundry-embed-v1",
        content_sha256="sha",
        created_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
    )


def test_stub_query_embedder_returns_length_1024() -> None:
    """RESEARCH Q1 RESOLVED: StubQueryEmbedder emits 1024-d vectors."""
    vec = StubQueryEmbedder().embed("HNSW semantic search")
    assert isinstance(vec, list)
    assert len(vec) == 1024
    assert all(isinstance(x, float) for x in vec)


def test_search_knowledge_returns_material_id_and_snippet() -> None:
    material = _ready(
        material_id=7,
        slug="pgvector",
        title="pgvector for Enterprise Search",
    )
    materials = InMemoryMaterialRepository([material])
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    embedding = [0.9] + [0.0] * 1023
    chunks.replace_for_material(
        7,
        [
            _chunk(
                material_id=7,
                chunk_index=0,
                content_md="Use HNSW indexes for semantic search.",
                embedding=embedding,
            )
        ],
    )

    hits = search_knowledge(
        chunks=chunks,
        query_embedding=embedding,
        query_text="HNSW",
        role_filter=None,
        limit=5,
    )

    assert len(hits) == 1
    assert hits[0].material_id == 7
    assert hits[0].material_slug == "pgvector"
    assert hits[0].chunk_index == 0
    assert "HNSW" in hits[0].snippet


def test_search_knowledge_dedupes_by_material_keeping_best_score() -> None:
    """D-61 / Pitfall 2: collapse chunks to one hit per material_id."""
    material = _ready(material_id=7, slug="pgvector")
    materials = InMemoryMaterialRepository([material])
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    strong = [0.95] + [0.0] * 1023
    # Orthogonal-ish weak vector vs strong query embedding.
    weak = [0.0] * 512 + [0.9] + [0.0] * 511
    chunks.replace_for_material(
        7,
        [
            _chunk(
                material_id=7,
                chunk_index=0,
                content_md="Unrelated audit workflow notes without the keyword.",
                embedding=weak,
                chunk_id=1,
            ),
            _chunk(
                material_id=7,
                chunk_index=1,
                content_md="Use HNSW indexes for semantic search — best chunk.",
                embedding=strong,
                chunk_id=2,
            ),
        ],
    )

    hits = search_knowledge(
        chunks=chunks,
        query_embedding=strong,
        query_text="HNSW",
        role_filter=None,
        limit=10,
    )

    assert len(hits) == 1
    assert hits[0].chunk_index == 1
    assert "best chunk" in hits[0].snippet


def test_search_knowledge_has_more_via_limit_plus_one_fetch() -> None:
    """D-61: caller may request limit+1; use-case returns at most `limit` items.

    has_more is computed by the HTTP layer when len(raw) > limit.
    Here we assert pagination slices materials (not raw chunks).
    """
    materials_list = [
        _ready(material_id=i, slug=f"mat-{i}", title=f"Material {i}")
        for i in range(1, 4)
    ]
    materials = InMemoryMaterialRepository(materials_list)
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    embedding = [0.9] + [0.0] * 1023
    for i in range(1, 4):
        chunks.replace_for_material(
            i,
            [
                _chunk(
                    material_id=i,
                    chunk_index=0,
                    content_md=f"HNSW topic material {i}",
                    embedding=embedding,
                    chunk_id=i,
                )
            ],
        )

    page0 = search_knowledge(
        chunks=chunks,
        query_embedding=embedding,
        query_text="HNSW",
        role_filter=None,
        limit=2,
        offset=0,
    )
    assert len(page0) == 2

    page1 = search_knowledge(
        chunks=chunks,
        query_embedding=embedding,
        query_text="HNSW",
        role_filter=None,
        limit=2,
        offset=2,
    )
    assert len(page1) == 1
    assert {h.material_id for h in page0}.isdisjoint({h.material_id for h in page1})


def test_search_knowledge_blank_query_raises_validation_error() -> None:
    """KNOW-01: whitespace-only q must not execute search."""
    materials = InMemoryMaterialRepository([])
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    with pytest.raises(KnowledgeQueryValidationError) as exc_info:
        search_knowledge(
            chunks=chunks,
            query_embedding=[0.0] * 1024,
            query_text="   \t  ",
            role_filter=None,
        )
    assert "empty_query" in str(exc_info.value)


def test_search_knowledge_overlong_query_raises_validation_error() -> None:
    """Max length 500 Unicode code points (encoding probe / KNOW-02)."""
    materials = InMemoryMaterialRepository([])
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    overlong = "я" * 501
    assert len(overlong) == 501
    with pytest.raises(KnowledgeQueryValidationError) as exc_info:
        search_knowledge(
            chunks=chunks,
            query_embedding=[0.0] * 1024,
            query_text=overlong,
            role_filter=None,
        )
    assert "query_too_long" in str(exc_info.value)


def test_search_knowledge_role_analyst_excludes_ds_only_materials() -> None:
    """KNOW-02 / D-62: role=analyst keeps membership matches and drops ds-only hits."""
    analyst = _ready(material_id=1, slug="sql-notes", title="SQL notes", roles=("analyst",))
    ds_only = _ready(material_id=2, slug="ml-experiment", title="ML experiment", roles=("ds",))
    materials = InMemoryMaterialRepository([analyst, ds_only])
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    embedding = [0.9] + [0.0] * 1023
    for material_id, chunk_id in ((1, 1), (2, 2)):
        chunks.replace_for_material(
            material_id,
            [
                _chunk(
                    material_id=material_id,
                    chunk_index=0,
                    content_md="HNSW indexes for this role-filter probe.",
                    embedding=embedding,
                    chunk_id=chunk_id,
                )
            ],
        )

    hits = search_knowledge(
        chunks=chunks,
        query_embedding=embedding,
        query_text="HNSW",
        role_filter="analyst",
        limit=10,
    )

    assert [hit.material_slug for hit in hits] == ["sql-notes"]


def test_search_knowledge_empty_role_filter_is_unrestricted() -> None:
    """KNOW-02: omitted or blank role means «Все» — no role filter."""
    analyst = _ready(material_id=1, slug="sql-notes", roles=("analyst",))
    ds_only = _ready(material_id=2, slug="ml-experiment", roles=("ds",))
    materials = InMemoryMaterialRepository([analyst, ds_only])
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    embedding = [0.9] + [0.0] * 1023
    for material_id, chunk_id in ((1, 1), (2, 2)):
        chunks.replace_for_material(
            material_id,
            [
                _chunk(
                    material_id=material_id,
                    chunk_index=0,
                    content_md="HNSW indexes for unrestricted role probe.",
                    embedding=embedding,
                    chunk_id=chunk_id,
                )
            ],
        )

    def slugs(role_filter: str | None) -> set[str]:
        found = search_knowledge(
            chunks=chunks,
            query_embedding=embedding,
            query_text="HNSW",
            role_filter=role_filter,
            limit=10,
        )
        return {hit.material_slug for hit in found}

    assert slugs(None) == {"sql-notes", "ml-experiment"}
    assert slugs("") == {"sql-notes", "ml-experiment"}
    assert slugs("   ") == {"sql-notes", "ml-experiment"}


def test_search_knowledge_invalid_role_raises_validation_error() -> None:
    """T-04-05 / D-62: only analyst|ds are filters; UI labels and sva are rejected."""
    material = _ready(material_id=1, slug="sql-notes", roles=("analyst", "sva"))
    materials = InMemoryMaterialRepository([material])
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    embedding = [0.9] + [0.0] * 1023
    chunks.replace_for_material(
        1,
        [
            _chunk(
                material_id=1,
                chunk_index=0,
                content_md="HNSW indexes.",
                embedding=embedding,
            )
        ],
    )

    for bad in ("sva", "Analyst", "ml"):
        with pytest.raises(KnowledgeQueryValidationError) as exc_info:
            search_knowledge(
                chunks=chunks,
                query_embedding=embedding,
                query_text="HNSW",
                role_filter=bad,
            )
        assert exc_info.value.code == "invalid_role"


def test_search_knowledge_analyst_empty_does_not_backfill_ds_materials() -> None:
    """KNOW-04: analyst filter with no matches stays empty — never substitute ds tops.

    The same query matches the ds-only material when role is unrestricted, so an
    empty analyst result is exclusion, not a miss.
    """
    ds_only = _ready(material_id=2, slug="ml-experiment", title="ML experiment", roles=("ds",))
    materials = InMemoryMaterialRepository([ds_only])
    chunks = InMemoryKnowledgeChunkRepository(materials=materials)
    embedding = [0.9] + [0.0] * 1023
    chunks.replace_for_material(
        2,
        [
            _chunk(
                material_id=2,
                chunk_index=0,
                content_md="HNSW indexes for the ML experiment.",
                embedding=embedding,
            )
        ],
    )

    unrestricted = search_knowledge(
        chunks=chunks,
        query_embedding=embedding,
        query_text="HNSW",
        role_filter=None,
        limit=10,
    )
    assert [hit.material_slug for hit in unrestricted] == ["ml-experiment"]

    analyst_hits = search_knowledge(
        chunks=chunks,
        query_embedding=embedding,
        query_text="HNSW",
        role_filter="analyst",
        limit=10,
    )
    assert analyst_hits == []
