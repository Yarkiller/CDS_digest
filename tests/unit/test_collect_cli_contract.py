"""RED→GREEN: ingest-collect stdout summary contract (ING-02, ING-07, D-01, D-03)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.tests_support.fakes import (
    FakeArticleGenerator,
    FakeTranscriptProvider,
    FakeVideoMetadataProvider,
)
from ingestion_service.application.ports.persist import PersistResult
from ingestion_service.tests_support.fakes import FakeDraftPersister

REPO_ROOT = Path(__file__).resolve().parents[2]
VIDEO_ID = "dQw4w9WgXcQ"
PUBLISHED = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)
CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSMdItQ"

EXPECTED_SUMMARY_LINES = [
    "sources: read=1 unreadable=0",
    "videos: new=1 ingested=1 already=0 failed=0 skipped_limit=0",
]


def _transcript() -> Transcript:
    return Transcript(text="ok captions", language="ru", video_id=VIDEO_ID)


def _article() -> ArticleDraft:
    return ArticleDraft(title="T", dek="D", body_markdown="B")


def _metadata() -> VideoMetadata:
    return VideoMetadata(
        video_id=VIDEO_ID,
        source_url=f"https://www.youtube.com/watch?v={VIDEO_ID}",
        author="Rick Astley",
    )


def _build_deps(*, with_skip: bool = False):
    from data_collection.dto.video_ref import FeedListing, FeedSkip, VideoRef
    from ingestion_service.application.ports.collect_sources import EnabledSource
    from ingestion_service.application.use_cases.collect_batch import CollectDeps
    from ingestion_service.tests_support.fakes import FakeCollectSourceReader, FakeFeed

    skipped = (FeedSkip(None, "missing_video_id"),) if with_skip else ()
    feed = FakeFeed(
        FeedListing(videos=(VideoRef(VIDEO_ID, PUBLISHED),), skipped=skipped)
    )
    sources = FakeCollectSourceReader(
        [
            EnabledSource(
                id=1,
                kind="channel",
                source_id=CHANNEL_ID,
                last_seen_published_at=None,
                last_seen_video_id=None,
            )
        ]
    )
    return CollectDeps(
        feed=feed,
        sources=sources,
        captions=FakeTranscriptProvider(result=_transcript()),
        metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
        article=FakeArticleGenerator(result=_article()),
        persist=FakeDraftPersister(
            PersistResult(material_id=1, slug="t-dQw4w9WgXcQ", batch_id=1, rank=1)
        ),
        emit_diagnostic=lambda _line: None,
    )


def test_collect_cli_happy_path_summary_stdout(monkeypatch) -> None:
    from typer.testing import CliRunner

    from ingestion_service import collect_cli as cli_mod

    deps = _build_deps()
    monkeypatch.setattr(cli_mod, "build_collect_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == EXPECTED_SUMMARY_LINES
    assert "✓" not in result.stdout
    assert result.stderr == ""


def test_collect_cli_feed_skip_goes_to_stderr(monkeypatch) -> None:
    from typer.testing import CliRunner

    from ingestion_service import collect_cli as cli_mod
    from ingestion_service.application.use_cases.collect_batch import CollectDeps

    base = _build_deps(with_skip=True)
    deps = CollectDeps(
        feed=base.feed,
        sources=base.sources,
        captions=base.captions,
        metadata_provider=base.metadata_provider,
        article=base.article,
        persist=base.persist,
        emit_diagnostic=cli_mod.emit_diagnostic,
    )
    monkeypatch.setattr(cli_mod, "build_collect_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == EXPECTED_SUMMARY_LINES
    stderr_lines = [line for line in result.stderr.splitlines() if line.strip()]
    assert stderr_lines == ["video skipped: <unknown>: missing_video_id"]


def test_pyproject_registers_ingest_collect_entry_point() -> None:
    text = (REPO_ROOT / "ingestion-service" / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'ingest-collect = "ingestion_service.collect_cli:app"' in text


def test_cli_py_has_no_collect_specific_strings() -> None:
    body = (
        REPO_ROOT
        / "ingestion-service"
        / "src"
        / "ingestion_service"
        / "cli.py"
    ).read_text(encoding="utf-8")
    assert "collect_cli" not in body
    assert "ingest-collect" not in body
    assert "run_collect_batch" not in body
