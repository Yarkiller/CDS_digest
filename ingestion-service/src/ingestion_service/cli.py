"""Typer one-shot `ingest` — operator CLI for the ingestion pipeline (D-01…D-07, D-09)."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Annotated, Any

import typer
from data_collection.dto.template_kind import TemplateKind
from data_collection.templates import TemplateLoadError

from ingestion_service.adapters.stderr_diagnostics import StderrDiagnostics, SystemClock
from ingestion_service.application.ports.diagnostics import (
    NullDiagnostics,
    StageDiagnostics,
)
from ingestion_service.application.use_cases.ingest_pipeline import run_ingest_pipeline
from ingestion_service.composition.clients import (
    build_deepseek_article_generator,
    build_supabase_draft_persister,
    build_youtube_captions,
    build_youtube_metadata_provider,
)
from ingestion_service.composition.config_error import ConfigurationError
from ingestion_service.composition.settings import Settings
from ingestion_service.domain.errors import IngestError

app = typer.Typer(add_completion=False)

_STAGE_CHECKMARKS = {
    "transcript": "✓ transcript",
    "llm": "✓ LLM",
    "saved": "✓ saved",
}


def build_ingest_deps() -> Any:
    """Composition seam for live adapters; CliRunner monkeypatches this with fakes."""
    settings = Settings.from_env()
    return SimpleNamespace(
        captions=build_youtube_captions(settings),
        metadata_provider=build_youtube_metadata_provider(settings),
        article=build_deepseek_article_generator(settings),
        persist=build_supabase_draft_persister(settings),
        settings=settings,
    )


def _settings_secrets(settings: Settings | None) -> list[str]:
    """Non-empty runtime secret values used to seed the redaction registry (D-08)."""
    if settings is None:
        return []
    candidates = (
        settings.deepseek_api_key,
        settings.supabase_secret_key,
        settings.youtube_proxy_url,
    )
    return [value for value in candidates if value]


def _on_stage(name: str) -> None:
    typer.echo(_STAGE_CHECKMARKS[name])


def _emit_debug(line: str) -> None:
    """D-01: debug lines go to stderr only — never stdout."""
    typer.echo(line, err=True)


@app.command()
def main(
    url: Annotated[str, typer.Argument(help="YouTube URL or video id")],
    template: Annotated[
        TemplateKind,
        typer.Option("--template", help="Prompt template: lecture or podcast"),
    ],
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Emit secret-safe stage diagnostics on stderr"),
    ] = False,
) -> None:
    """Ingest a YouTube URL into a materials draft + shortlist row."""
    diagnostics: StageDiagnostics = (
        StderrDiagnostics(clock=SystemClock(), emit=_emit_debug)
        if debug
        else NullDiagnostics()
    )
    try:
        deps = build_ingest_deps()
        if debug:
            diagnostics = StderrDiagnostics(
                clock=SystemClock(),
                secrets=_settings_secrets(getattr(deps, "settings", None)),
                emit=_emit_debug,
            )
        result = asyncio.run(
            run_ingest_pipeline(
                url,
                template,
                captions=deps.captions,
                metadata_provider=deps.metadata_provider,
                article=deps.article,
                persist=deps.persist,
                on_stage=_on_stage,
                diagnostics=diagnostics,
            )
        )
    except (ConfigurationError, TemplateLoadError) as err:
        # D-08/D-12: pre-video failures stay human text — never mint a new IngestError stage.
        diagnostics.config_error(error_type=type(err).__name__, message=str(err))
        typer.echo(str(err), err=True)
        raise typer.Exit(code=1) from err
    except IngestError as err:
        typer.echo(json.dumps(err.to_dict()), err=True)
        raise typer.Exit(code=err.exit_code) from err

    typer.echo(f"material_id: {result.material_id}")
    typer.echo(f"slug: {result.slug}")
    typer.echo(f"batch_id: {result.batch_id}")
    typer.echo(f"rank: {result.rank}")
    typer.echo(f"already_saved: {'true' if result.already_saved else 'false'}")


if __name__ == "__main__":
    app()
