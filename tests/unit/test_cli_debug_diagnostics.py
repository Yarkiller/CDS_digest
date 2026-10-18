"""RED→GREEN: opt-in `--debug` stage diagnostics on stderr (DBG-01, DBG-02; D-01…D-03, D-13)."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from types import SimpleNamespace

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

_DEBUG_CAPTIONS_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}\] debug stage=captions ")


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


def _persist_result() -> PersistResult:
    return PersistResult(material_id=42, slug=EXPECTED_SLUG, batch_id=7, rank=1)


def _fake_deps() -> object:
    return SimpleNamespace(
        captions=FakeTranscriptProvider(result=_transcript()),
        metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
        article=FakeArticleGenerator(result=_article()),
        persist=FakeDraftPersister(_persist_result()),
    )


def test_debug_off_is_byte_identical(monkeypatch) -> None:
    """D-13 / DBG-02: without --debug stderr is empty and stdout is the frozen contract."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: _fake_deps())

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == EXPECTED_SUCCESS_LINES


def test_debug_success_emits_stage_lines(monkeypatch) -> None:
    """D-01/D-02/D-03: --debug prints a captions line on stderr; stdout unchanged."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: _fake_deps())

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture", "--debug"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == EXPECTED_SUCCESS_LINES

    lines = [line for line in result.stderr.splitlines() if line.strip()]
    captions_lines = [line for line in lines if _DEBUG_CAPTIONS_RE.match(line)]
    assert len(captions_lines) == 1
    captions_line = captions_lines[0]
    assert "elapsed_ms=" in captions_line
    assert "transcript_chars=" in captions_line


def _debug_lines(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if " debug stage=" in line]


def _stage_line(lines: list[str], stage: str) -> str:
    matches = [line for line in lines if re.search(rf"\bdebug stage={stage}\b", line)]
    assert len(matches) == 1, (stage, lines)
    return matches[0]


def test_debug_success_emits_all_stage_lines(monkeypatch) -> None:
    """D-04: --debug prints exactly one line for each of captions/metadata/llm/persist."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: _fake_deps())

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture", "--debug"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == EXPECTED_SUCCESS_LINES

    lines = _debug_lines(result.stderr)
    assert len(lines) == 4
    for stage in ("captions", "metadata", "llm", "persist"):
        _stage_line(lines, stage)


def test_debug_metadata_line_minimized(monkeypatch) -> None:
    """D-06: the metadata line exposes only video_id — never author or source URL."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: _fake_deps())

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture", "--debug"])
    line = _stage_line(_debug_lines(result.stderr), "metadata")
    assert "video_id=" in line
    assert "Rick Astley" not in line
    assert f"https://www.youtube.com/watch?v={VIDEO_ID}" not in line


def test_debug_stage_lines_carry_allowlisted_signals(monkeypatch) -> None:
    """D-04: llm carries template/response_chars; persist carries the identifiers."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: _fake_deps())

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture", "--debug"])
    lines = _debug_lines(result.stderr)

    llm_line = _stage_line(lines, "llm")
    assert "template=lecture" in llm_line
    assert f"response_chars={len(_article().body_markdown)}" in llm_line
    assert "prompt" not in llm_line
    assert "token" not in llm_line

    persist_line = _stage_line(lines, "persist")
    assert "material_id=42" in persist_line
    assert f"slug={EXPECTED_SLUG}" in persist_line
    assert "batch_id=7" in persist_line
    assert "rank=1" in persist_line
    assert "already_saved=False" in persist_line


def test_debug_secret_registry_masks_settings_secret(monkeypatch) -> None:
    """W-2: Settings -> _settings_secrets -> SecretRegistry -> sanitize -> stderr."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod
    from ingestion_service.composition.settings import Settings

    deps = _fake_deps()
    deps.settings = Settings(deepseek_api_key=VIDEO_ID)
    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture", "--debug"])
    assert result.exit_code == 0

    captions_line = _stage_line(_debug_lines(result.stderr), "captions")
    assert "video_id=[redacted]" in captions_line
    assert VIDEO_ID not in result.stderr


def test_debug_failure_prints_completed_and_failed(monkeypatch) -> None:
    """D-10/D-11: completed stages + failed reason/exit_code/elapsed precede the JSON line."""
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

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture", "--debug"])
    assert result.exit_code != 0
    assert [line for line in result.stdout.splitlines() if line.strip()] == ["✓ transcript"]

    stderr_lines = result.stderr.strip().splitlines()
    payload = json.loads(stderr_lines[-1])
    assert payload["ok"] is False
    assert payload["stage"] == "llm"

    lines = _debug_lines(result.stderr)
    _stage_line(lines, "captions")
    _stage_line(lines, "metadata")
    llm_line = _stage_line(lines, "llm")
    assert "reason=network_error" in llm_line
    assert "exit_code=1" in llm_line
    assert "elapsed_ms=" in llm_line
    assert payload["message"] not in llm_line

    json_index = next(
        index for index, line in enumerate(stderr_lines) if line.startswith("{")
    )
    for debug_line in lines:
        assert stderr_lines.index(debug_line) < json_index


def test_debug_url_failure_prints_stage_line_with_zero_elapsed(monkeypatch) -> None:
    """RESEARCH Pattern 4: a url failure has no prior stage → elapsed_ms=0."""
    import json

    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: _fake_deps())

    bad_url = "https://example.com/watch?v=dQw4w9WgXcQ"
    result = CliRunner().invoke(cli_mod.app, [bad_url, "--template", "lecture", "--debug"])
    assert result.exit_code != 0

    url_line = _stage_line(_debug_lines(result.stderr), "url")
    assert "elapsed_ms=0" in url_line

    payload = json.loads(result.stderr.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["stage"] == "url"


def test_debug_config_error_line(monkeypatch) -> None:
    """D-12: a pre-video ConfigurationError emits stage=config, no IngestError envelope."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod
    from ingestion_service.composition.config_error import ConfigurationError

    def _raise_config() -> object:
        raise ConfigurationError("SUPABASE_URL is required")

    monkeypatch.setattr(cli_mod, "build_ingest_deps", _raise_config)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture", "--debug"])
    assert result.exit_code != 0

    config_line = _stage_line(_debug_lines(result.stderr), "config")
    assert "error_type=ConfigurationError" in config_line
    assert "SUPABASE_URL is required" in result.stderr

    stderr_lines = result.stderr.splitlines()
    human_line = next(line for line in stderr_lines if line == "SUPABASE_URL is required")
    assert stderr_lines.index(config_line) < stderr_lines.index(human_line)
    assert '"ok"' not in result.stderr


def test_debug_template_load_error_line(monkeypatch) -> None:
    """D-12: TemplateLoadError emits stage=config error_type=TemplateLoadError."""
    from data_collection.templates import TemplateLoadError
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    def _raise_template() -> object:
        raise TemplateLoadError("lecture")

    monkeypatch.setattr(cli_mod, "build_ingest_deps", _raise_template)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture", "--debug"])
    assert result.exit_code != 0

    config_line = _stage_line(_debug_lines(result.stderr), "config")
    assert "error_type=TemplateLoadError" in config_line
    assert '"ok"' not in result.stderr


def test_config_error_without_debug_has_no_debug_line(monkeypatch) -> None:
    """DBG-02: with --debug off the config-error path stays human-text only."""
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod
    from ingestion_service.composition.config_error import ConfigurationError

    def _raise_config() -> object:
        raise ConfigurationError("SUPABASE_URL is required")

    monkeypatch.setattr(cli_mod, "build_ingest_deps", _raise_config)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code != 0
    assert "debug stage=" not in result.stderr
    assert "SUPABASE_URL is required" in result.stderr


def test_ingest_pipeline_retains_no_infra_imports() -> None:
    """Structural guard: the use-case stays free of clock/stream/CLI imports."""
    import ingestion_service.application.use_cases.ingest_pipeline as pipeline_mod

    source = Path(pipeline_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"time", "sys", "typer", "datetime"})
