"""Composition root wires in-memory adapters for local/unit use."""

from backend.composition import build_in_memory_container
from backend.domain.material import Material, MaterialStatus
from datetime import datetime, timezone


def test_in_memory_container_publish_and_index() -> None:
    material = Material(
        id=42,
        slug="demo",
        title="Demo",
        dek="Dek",
        body_markdown="## A\n\nAlpha.\n\n## B\n\nBeta.",
        format="статья",
        status=MaterialStatus.DRAFT,
        reading_minutes=3,
        provenance_label="test",
        source_id=None,
        roles=("sva",),
        tags=(),
        related_material_ids=(),
        published_at=None,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    app = build_in_memory_container([material])
    assert app.profiles is not None
    assert app.pings is not None
    recorded_id = app.pings.record(
        user_id="user-uuid-1",
        kind="platform_ping",
        payload={},
    )
    assert recorded_id is not None
    assert len(app.pings.entries_for("user-uuid-1")) == 1
    published = app.publish(42)
    assert published.status == MaterialStatus.READY

    chunks = app.index(42, embedding_model_id="foundry-embed-v1", embed=lambda _t: [0.0] * 1024)
    assert len(chunks) >= 2

    hits = app.search(query_embedding=[0.0] * 1024, query_text="Alpha")
    assert hits
    assert hits[0].material_id == 42

    user = app.profiles.get_or_upsert("user-uuid-1", "alice@sberbank.ru")
    assert user.id == "user-uuid-1"
    assert user.email == "alice@sberbank.ru"
    assert user.role == "employee"


def test_in_memory_container_keeps_stub_mailer_as_default() -> None:
    """D-15 tripwire: local/in-memory composition never swaps the port's default double."""
    from backend.infrastructure.stub_mailer import StubMailer

    container = build_in_memory_container([])

    assert isinstance(container.mailer, StubMailer)


def test_in_memory_container_wires_ingest_sources() -> None:
    """D-21 / D-24 AMEND: in-memory build exposes InMemoryIngestSourceRepository."""
    import pytest

    try:
        from backend.tests_support.in_memory import InMemoryIngestSourceRepository
    except ImportError as exc:
        pytest.fail(f"InMemoryIngestSourceRepository not importable: {exc}")

    container = build_in_memory_container([])

    assert hasattr(container, "ingest_sources")
    assert isinstance(container.ingest_sources, InMemoryIngestSourceRepository)
