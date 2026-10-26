"""RED→GREEN: build_ingest_deps wires live ports via composition factories (D-02; CLI-05)."""

from __future__ import annotations

import inspect
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs" / "agents" / "local-platform-runbook.md"


def test_build_ingest_deps_source_delegates_to_composition_factories() -> None:
    """Live builder must call Settings.from_env + composition factories (not dotenv)."""
    from ingestion_service import cli as cli_mod

    src = inspect.getsource(cli_mod.build_ingest_deps)
    assert "Settings.from_env" in src
    assert "build_youtube_captions" in src
    assert "build_youtube_metadata_provider" in src
    assert "build_deepseek_article_generator" in src
    assert "build_supabase_draft_persister" in src
    assert "load_dotenv" not in src
    assert "os.environ" not in src


def test_build_ingest_deps_wires_four_ports_via_monkeypatched_factories(monkeypatch) -> None:
    from ingestion_service import cli as cli_mod

    settings = object()
    monkeypatch.setattr(cli_mod.Settings, "from_env", staticmethod(lambda: settings))

    captions = object()
    metadata = object()
    article = object()
    persist = object()
    calls: list[str] = []

    def _track(name: str, sentinel: object):
        def _factory(received: object) -> object:
            assert received is settings
            calls.append(name)
            return sentinel

        return _factory

    monkeypatch.setattr(
        cli_mod, "build_youtube_captions", _track("captions", captions), raising=False
    )
    monkeypatch.setattr(
        cli_mod,
        "build_youtube_metadata_provider",
        _track("metadata", metadata),
        raising=False,
    )
    monkeypatch.setattr(
        cli_mod, "build_deepseek_article_generator", _track("article", article)
    )
    monkeypatch.setattr(
        cli_mod, "build_supabase_draft_persister", _track("persist", persist)
    )

    deps = cli_mod.build_ingest_deps()

    assert deps.captions is captions
    assert deps.metadata_provider is metadata
    assert deps.article is article
    assert deps.persist is persist
    assert calls == ["captions", "metadata", "article", "persist"]


def test_runbook_documents_phase10_uat_ingest_command() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "Phase 10" in text
    assert "uv run --env-file ingestion-service/.env ingest" in text
    assert "--template" in text
    assert "Do not point UAT at the root" in text or "not point UAT at the root" in text
    assert "D-02" in text or "CLI-05" in text
