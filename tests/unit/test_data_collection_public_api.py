"""Public data_collection.__all__ whitelist + export negatives (D-01…D-04, D-06, D-21)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

PUBLIC_NAMES = frozenset(
    {
        "Transcript",
        "VideoMetadata",
        "MaterialDraft",
        "TemplateKind",
        "TranscriptProvider",
        "ArticleGenerator",
        "VideoMetadataProvider",
        "VideoRef",
        "FeedListing",
        "VideoListProvider",
    }
)

NEGATIVE_ROOT_NAMES = (
    "RoleKind",
    "ArticleDraft",
    "normalize_roles",
    "FakeTranscriptProvider",
    "FakeArticleGenerator",
    "FakeVideoMetadataProvider",
    "CaptionsError",
    "MetadataError",
    "YouTubeTranscriptAdapter",
    "YouTubeOEmbedAdapter",
    "YouTubeFeedAdapter",
    "FeedError",
    "DeepSeekArticleGenerator",
    "ArticleError",
    "TemplateLoadError",
    "YoutubeSourceDto",
    "TranscriptResultDto",
    "ArticleAssistDto",
    "TextImportDto",
    "SummaryResultDto",
    "TaggingResultDto",
    "EmbeddingResultDto",
    "EMBEDDING_DIM",
)


def test_public_all_is_exactly_ten_ingestion_names() -> None:
    """D-01, D-04, D-21: package root exports only the ten public contracts."""
    import data_collection

    importlib.reload(data_collection)
    assert set(data_collection.__all__) == PUBLIC_NAMES
    assert len(data_collection.__all__) == 10
    for name in sorted(PUBLIC_NAMES):
        assert hasattr(data_collection, name), f"missing public export: {name}"


def test_ports_package_exports_both_provider_protocols() -> None:
    """WR-01 / D-21: ports barrel re-exports both providers alongside ArticleGenerator."""
    from data_collection.ports import (
        ArticleGenerator,
        TranscriptProvider,
        VideoMetadataProvider,
    )
    from data_collection.ports.video_metadata_provider import (
        VideoMetadataProvider as ModuleLevel,
    )

    import data_collection.ports as ports

    importlib.reload(ports)
    assert "TranscriptProvider" in ports.__all__
    assert "ArticleGenerator" in ports.__all__
    assert "VideoMetadataProvider" in ports.__all__
    assert "VideoListProvider" in ports.__all__
    assert ports.TranscriptProvider is TranscriptProvider
    assert ports.ArticleGenerator is ArticleGenerator
    assert ports.VideoMetadataProvider is VideoMetadataProvider
    assert ports.VideoMetadataProvider is ModuleLevel


@pytest.mark.parametrize("name", NEGATIVE_ROOT_NAMES)
def test_negative_names_not_importable_from_package_root(name: str) -> None:
    """D-02, D-04, D-06, D-21: fakes, adapters, errors, and old DTOs stay off root."""
    import data_collection

    importlib.reload(data_collection)
    assert name not in data_collection.__all__
    with pytest.raises((ImportError, AttributeError)):
        getattr(data_collection, name)
    with pytest.raises(ImportError):
        exec(f"from data_collection import {name}")


def test_error_bases_importable_from_errors_submodules() -> None:
    """Mapper import path: errors stay reachable via data_collection.errors.*."""
    from data_collection.errors.captions import CaptionsError
    from data_collection.errors.metadata import MetadataError

    assert issubclass(CaptionsError, Exception)
    assert issubclass(MetadataError, Exception)


def test_stage_set_is_unchanged() -> None:
    from typing import get_args

    from ingestion_service.domain.errors import Stage

    assert set(get_args(Stage)) == {
        "url",
        "captions",
        "metadata",
        "consistency",
        "llm",
        "llm_truncation",
        "persist",
    }


def test_ingestion_service_has_no_typer_import() -> None:
    """Only cli.py may import typer; all other ingestion_service modules stay clean."""
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "ingestion-service" / "src" / "ingestion_service"
    for path in src_root.rglob("*.py"):
        if path.name.endswith("cli.py"):
            continue
        body = path.read_text(encoding="utf-8")
        assert "import typer" not in body, path.name
        assert "from typer" not in body, path.name


def test_data_collection_has_no_supabase_import() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "data-collection" / "src" / "data_collection"
    for path in src_root.rglob("*.py"):
        body = path.read_text(encoding="utf-8")
        assert "import supabase" not in body, path.name
        assert "from supabase" not in body, path.name
