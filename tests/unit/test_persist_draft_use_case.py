"""RED→GREEN: persist_draft enriches MaterialDraft and delegates to PersistPort (D-07, D-11)."""

from __future__ import annotations

import ast
from pathlib import Path

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.material_draft import MaterialDraft
from data_collection.dto.video_metadata import VideoMetadata


VIDEO_ID = "dQw4w9WgXcQ"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _words(count: int) -> str:
    return " ".join(["слово"] * count)


def _draft(**overrides: object) -> MaterialDraft:
    base: dict[str, object] = {
        "title": "Как использовать pgvector",
        "dek": "d",
        "body_markdown": _words(400),
        "source_url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "youtube_video_id": VIDEO_ID,
        "source_author": "Author",
        "provenance_label": "YouTube · Author",
    }
    base.update(overrides)
    return MaterialDraft(**base)


def test_material_draft_defaults_slug_and_reading_minutes() -> None:
    draft = _draft()
    assert draft.slug == ""
    assert draft.reading_minutes == 1


def test_assemble_material_draft_still_constructs_without_slug() -> None:
    from data_collection.assemble import assemble_material_draft

    article = ArticleDraft(
        title="Prepared title",
        dek="Prepared dek",
        body_markdown="# Body",
    )
    metadata = VideoMetadata(
        video_id=VIDEO_ID,
        source_url=f"https://www.youtube.com/watch?v={VIDEO_ID}",
        author="Rick Astley",
        published_at=None,
    )
    draft = assemble_material_draft(article, metadata, "YouTube · Rick Astley")
    assert draft.slug == ""
    assert draft.reading_minutes == 1


def test_persist_draft_returns_port_result_and_enriches_draft() -> None:
    from ingestion_service.application.ports.persist import PersistResult
    from ingestion_service.application.use_cases.persist_draft import persist_draft
    from ingestion_service.tests_support.fakes import FakeDraftPersister

    result = PersistResult(
        material_id=11, slug="s", batch_id=4, rank=1, already_saved=False
    )
    fake = FakeDraftPersister(result)
    draft = _draft()
    assert persist_draft(draft, fake) == result
    passed = fake.calls[0]
    assert passed.slug == "kak-ispolzovat-pgvector-dQw4w9WgXcQ"
    assert passed.reading_minutes == 2
    assert draft.slug == ""
    assert draft.reading_minutes == 1


def test_persist_draft_overwrites_existing_slug_and_reading_minutes() -> None:
    from ingestion_service.application.ports.persist import PersistResult
    from ingestion_service.application.use_cases.persist_draft import persist_draft
    from ingestion_service.tests_support.fakes import FakeDraftPersister

    fake = FakeDraftPersister(
        PersistResult(
            material_id=1, slug="s", batch_id=2, rank=3, already_saved=False
        )
    )
    persist_draft(_draft(slug="old-slug", reading_minutes=99), fake)
    passed = fake.calls[0]
    assert passed.slug == "kak-ispolzovat-pgvector-dQw4w9WgXcQ"
    assert passed.reading_minutes == 2


def test_persist_draft_twice_same_video_id_returns_same_result() -> None:
    from ingestion_service.application.ports.persist import PersistResult
    from ingestion_service.application.use_cases.persist_draft import persist_draft
    from ingestion_service.tests_support.fakes import FakeDraftPersister

    result = PersistResult(
        material_id=11, slug="s", batch_id=4, rank=1, already_saved=False
    )
    fake = FakeDraftPersister(result)
    draft = _draft()
    first = persist_draft(draft, fake)
    second = persist_draft(draft, fake)
    assert first.already_saved is False
    assert second.already_saved is True
    assert second.material_id == first.material_id == result.material_id
    assert second.slug == first.slug == result.slug
    assert second.batch_id == first.batch_id == result.batch_id
    assert second.rank == first.rank == result.rank
    assert list(fake.stored.keys()) == [VIDEO_ID]
    assert len(fake.calls) == 2


def test_persist_draft_has_no_video_id_precheck_or_environ() -> None:
    path = (
        REPO_ROOT
        / "ingestion-service"
        / "src"
        / "ingestion_service"
        / "application"
        / "use_cases"
        / "persist_draft.py"
    )
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "os" not in imported
    assert "os.environ" not in source
    assert "stored" not in source
    assert "existing" not in source
