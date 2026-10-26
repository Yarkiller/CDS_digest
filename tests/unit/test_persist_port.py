"""RED→GREEN: PersistPort, PersistResult, FakeDraftPersister (PERS-01, D-03)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from data_collection.dto.material_draft import MaterialDraft


VIDEO_ID = "dQw4w9WgXcQ"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _draft(**overrides: object) -> MaterialDraft:
    base: dict[str, object] = {
        "title": "t",
        "dek": "d",
        "body_markdown": "b",
        "source_url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
        "youtube_video_id": VIDEO_ID,
        "source_author": "Author",
        "provenance_label": "YouTube · Author",
    }
    base.update(overrides)
    return MaterialDraft(**base)


def test_concrete_persist_port_returns_persist_result() -> None:
    from ingestion_service.application.ports.persist import PersistPort, PersistResult
    from ingestion_service.tests_support.fakes import FakeDraftPersister

    result = PersistResult(
        material_id=1, slug="s", batch_id=2, rank=3, already_saved=False
    )
    port: PersistPort = FakeDraftPersister(result)
    returned = port.persist(_draft())
    assert returned == PersistResult(
        material_id=1, slug="s", batch_id=2, rank=3, already_saved=False
    )
    assert returned.material_id == 1
    assert returned.slug == "s"
    assert returned.batch_id == 2
    assert returned.rank == 3
    assert returned.already_saved is False


def test_fake_records_call_and_returns_scripted_result() -> None:
    from ingestion_service.application.ports.persist import PersistResult
    from ingestion_service.tests_support.fakes import FakeDraftPersister

    result = PersistResult(
        material_id=1, slug="s", batch_id=2, rank=3, already_saved=False
    )
    fake = FakeDraftPersister(result)
    draft = _draft()
    assert fake.persist(draft) == result
    assert fake.calls == [draft]
    assert fake.stored[VIDEO_ID] == result


def test_fake_raises_scripted_error_and_still_records_call() -> None:
    from ingestion_service.adapters.persist_errors import DraftPersistError
    from ingestion_service.application.ports.persist import PersistResult
    from ingestion_service.tests_support.fakes import FakeDraftPersister

    result = PersistResult(
        material_id=1, slug="s", batch_id=2, rank=3, already_saved=False
    )
    error = DraftPersistError("persist_conflict", video_id=VIDEO_ID)
    fake = FakeDraftPersister(result, failures={VIDEO_ID: error})
    draft = _draft()
    with pytest.raises(DraftPersistError) as exc:
        fake.persist(draft)
    assert exc.value is error
    assert fake.calls == [draft]


def test_fake_repeat_video_id_returns_already_saved_true_without_second_entry() -> None:
    from ingestion_service.application.ports.persist import PersistResult
    from ingestion_service.tests_support.fakes import FakeDraftPersister

    result = PersistResult(
        material_id=1, slug="s", batch_id=2, rank=3, already_saved=False
    )
    fake = FakeDraftPersister(result)
    first = fake.persist(_draft())
    second = fake.persist(_draft(title="other title"))
    assert first.already_saved is False
    assert second.already_saved is True
    assert second.material_id == first.material_id
    assert second.slug == first.slug
    assert second.batch_id == first.batch_id
    assert second.rank == first.rank
    assert list(fake.stored.keys()) == [VIDEO_ID]
    assert len(fake.stored) == 1
    assert len(fake.calls) == 2


def test_persist_port_is_runtime_checkable() -> None:
    from ingestion_service.application.ports.persist import PersistPort, PersistResult
    from ingestion_service.tests_support.fakes import FakeDraftPersister

    fake = FakeDraftPersister(
        PersistResult(
            material_id=1, slug="s", batch_id=2, rank=3, already_saved=False
        )
    )
    assert isinstance(fake, PersistPort)


def test_fake_has_no_supabase_import_or_environ_access() -> None:
    fake_path = (
        REPO_ROOT
        / "ingestion-service"
        / "src"
        / "ingestion_service"
        / "tests_support"
        / "fakes.py"
    )
    source = fake_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "supabase" not in imported
    assert "os" not in imported
    assert "os.environ" not in source
