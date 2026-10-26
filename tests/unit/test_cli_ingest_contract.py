"""RED→GREEN: Typer ingest happy-path stdout contract (D-01…D-07, D-09, D-11; CLI-01; CLI-04)."""

from __future__ import annotations

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

VIDEO_ID = "dQw4w9WgXcQ"
URL = f"https://youtu.be/{VIDEO_ID}"
EXPECTED_SLUG = "kak-ispolzovat-pgvector-dQw4w9WgXcQ"

EXPECTED_SUCCESS_LINES = [
    "✓ transcript",
    "✓ LLM",
    "✓ saved",
    "material_id: 42",
    f"slug: {EXPECTED_SLUG}",
    "batch_id: 7",
    "rank: 1",
    "already_saved: false",
]


def _transcript() -> Transcript:
    return Transcript(text="ok captions", language="ru", video_id=VIDEO_ID)


def _article() -> ArticleDraft:
    return ArticleDraft(
        title="Как использовать pgvector",
        dek="dek",
        body_markdown="body text here",
    )


def _metadata() -> VideoMetadata:
    return VideoMetadata(
        video_id=VIDEO_ID,
        source_url=f"https://www.youtube.com/watch?v={VIDEO_ID}",
        author="Rick Astley",
    )


def _persist_result(*, already_saved: bool = False) -> PersistResult:
    return PersistResult(
        material_id=42,
        slug=EXPECTED_SLUG,
        batch_id=7,
        rank=1,
        already_saved=already_saved,
    )


def _fake_deps(persist: FakeDraftPersister | None = None) -> object:
    from types import SimpleNamespace

    return SimpleNamespace(
        captions=FakeTranscriptProvider(result=_transcript()),
        metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
        article=FakeArticleGenerator(result=_article()),
        persist=persist or FakeDraftPersister(_persist_result()),
    )


def test_cli_happy_path_stdout_contract(monkeypatch) -> None:
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    deps = _fake_deps()
    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == EXPECTED_SUCCESS_LINES
    assert result.stderr == ""


def test_cli_requires_template_flag(monkeypatch) -> None:
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: _fake_deps())

    result = CliRunner().invoke(cli_mod.app, [URL])
    assert result.exit_code != 0
    assert "material_id:" not in result.stdout


def test_cli_rerun_prints_already_saved_true_with_stored_ids(monkeypatch) -> None:
    """D-09, D-10: second invoke exits 0 with already_saved: true and same id lines."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    persist = FakeDraftPersister(_persist_result())
    deps = _fake_deps(persist)
    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: deps)

    runner = CliRunner()
    first = runner.invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert first.exit_code == 0
    assert first.stdout.splitlines() == EXPECTED_SUCCESS_LINES

    second = runner.invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert second.exit_code == 0
    assert second.stderr == ""
    second_lines = second.stdout.splitlines()
    assert second_lines == [
        "✓ transcript",
        "✓ LLM",
        "✓ saved",
        "material_id: 42",
        f"slug: {EXPECTED_SLUG}",
        "batch_id: 7",
        "rank: 1",
        "already_saved: true",
    ]
    assert len(persist.stored) == 1
    assert list(persist.stored.keys()) == [VIDEO_ID]


def test_cli_sent_batch_rerun_prints_checkmarks_and_already_saved(monkeypatch) -> None:
    """D-08; CLI-02; CLI-04: sent-batch-only shortlist re-run exits 0 with checkmarks + already_saved."""
    from datetime import datetime, timezone

    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod
    from ingestion_service.application.ports.persist import PersistResult
    from ingestion_service.tests_support.fakes import BatchTrackingFakePersister

    persist = BatchTrackingFakePersister(batch_size=5)
    sent_at = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    persist.seed_batch(batch_id=3, sent_at=sent_at)
    persist.seed_item(3, decision="pending", video_id=VIDEO_ID)
    persist.stored[VIDEO_ID] = PersistResult(
        material_id=9,
        slug=EXPECTED_SLUG,
        batch_id=3,
        rank=1,
        already_saved=False,
    )

    deps = _fake_deps(persist)
    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "✓ transcript",
        "✓ LLM",
        "✓ saved",
        "material_id: 9",
        f"slug: {EXPECTED_SLUG}",
        "batch_id: 3",
        "rank: 1",
        "already_saved: true",
    ]
    assert len(persist.stored) == 1
    assert list(persist.stored.keys()) == [VIDEO_ID]


def test_cli_mid_pipeline_llm_error_keeps_transcript_checkmark_json_stderr(
    monkeypatch,
) -> None:
    """D-05, D-07: after ✓ transcript, IngestError(stage=llm) → JSON stderr, no later marks."""
    import json

    from data_collection.errors.article import ArticleNetworkError
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    deps = _fake_deps()
    deps.article = FakeArticleGenerator(
        result=_article(),
        failures={VIDEO_ID: ArticleNetworkError(VIDEO_ID)},
    )
    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code != 0
    stdout_lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert stdout_lines == ["✓ transcript"]
    assert "✓ LLM" not in result.stdout
    assert "✓ saved" not in result.stdout
    payload = json.loads(result.stderr.strip())
    assert payload["ok"] is False
    assert payload["stage"] == "llm"


def test_cli_captions_cookie_invalid_unknown_json_stderr_no_traceback(
    monkeypatch,
) -> None:
    """D-01, D-04, D-05; CAP-02: CookieInvalid-mapped CaptionsError → JSON stderr, no Traceback."""
    import json

    from data_collection.errors.captions import CaptionsError
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    deps = _fake_deps()
    deps.captions = FakeTranscriptProvider(
        result=_transcript(),
        failures={
            VIDEO_ID: CaptionsError(
                VIDEO_ID,
                exception_class="CookieInvalid",
            ),
        },
    )
    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code != 0
    assert "✓ transcript" not in result.stdout
    assert "✓ LLM" not in result.stdout
    assert "✓ saved" not in result.stdout
    combined = f"{result.stdout}{result.stderr}"
    assert "Traceback" not in combined
    payload = json.loads(result.stderr.strip())
    assert payload["ok"] is False
    assert payload["stage"] == "captions"
    assert payload["reason"] == "unknown_captions_error"
    assert payload["message"] == f"captions unknown_captions_error for {VIDEO_ID}"
    assert "CookieInvalid" not in payload["message"]


def test_cli_configuration_error_is_human_stderr_without_json_envelope(
    monkeypatch,
) -> None:
    """D-08: ConfigurationError before video work → human stderr, no checkmarks, no stage/ok JSON."""
    import json

    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod
    from ingestion_service.composition.config_error import ConfigurationError

    def _raise_config() -> object:
        raise ConfigurationError("SUPABASE_URL is required")

    monkeypatch.setattr(cli_mod, "build_ingest_deps", _raise_config)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code != 0
    assert "✓ transcript" not in result.stdout
    assert "✓ LLM" not in result.stdout
    assert "✓ saved" not in result.stdout
    err = result.stderr.strip()
    assert err
    assert "SUPABASE_URL" in err
    try:
        payload = json.loads(err)
    except json.JSONDecodeError:
        payload = None
    if payload is not None:
        assert "stage" not in payload or "ok" not in payload


def test_cli_template_load_error_is_human_stderr_without_json_envelope(
    monkeypatch,
) -> None:
    """D-08: TemplateLoadError before video work → human stderr, no IngestError stage."""
    import json

    from data_collection.templates import TemplateLoadError
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    def _raise_template() -> object:
        raise TemplateLoadError("lecture")

    monkeypatch.setattr(cli_mod, "build_ingest_deps", _raise_template)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code != 0
    assert "✓ transcript" not in result.stdout
    err = result.stderr.strip()
    assert err
    assert "lecture" in err.lower() or "template" in err.lower()
    try:
        payload = json.loads(err)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        assert not ({"stage", "ok"} <= set(payload.keys()))
