"""Typer one-shot `ingest-collect` — scheduled batch collection (ING-02, ING-07, D-01)."""

from __future__ import annotations

import asyncio

import typer
from data_collection.templates import TemplateLoadError

from ingestion_service.application.use_cases.collect_batch import (
    CollectDeps,
    run_collect_batch,
)
from ingestion_service.composition.clients import (
    build_collect_source_reader,
    build_deepseek_article_generator,
    build_supabase_draft_persister,
    build_youtube_captions,
    build_youtube_feed,
    build_youtube_metadata_provider,
)
from ingestion_service.composition.config_error import ConfigurationError
from ingestion_service.composition.settings import Settings

app = typer.Typer(add_completion=False)


def emit_diagnostic(line: str) -> None:
    """D-03 / D-25: per-video diagnostics go to stderr only — never stdout."""
    typer.echo(line, err=True)


def build_collect_deps() -> CollectDeps:
    """Composition seam for live adapters; CliRunner monkeypatches this with fakes."""
    settings = Settings.from_env()
    return CollectDeps(
        feed=build_youtube_feed(settings),
        sources=build_collect_source_reader(settings),
        captions=build_youtube_captions(settings),
        metadata_provider=build_youtube_metadata_provider(settings),
        article=build_deepseek_article_generator(settings),
        persist=build_supabase_draft_persister(settings),
        emit_diagnostic=emit_diagnostic,
    )


@app.command()
def main() -> None:
    """Collect new videos from enabled ingest sources into drafts + shortlist."""
    try:
        settings = Settings.from_env()
        deps = build_collect_deps()
        counters = asyncio.run(
            run_collect_batch(
                deps,
                template=settings.ingest_template,
                limit=settings.ingest_max_videos_per_source,
            )
        )
    except (ConfigurationError, TemplateLoadError) as err:
        typer.echo(str(err), err=True)
        raise typer.Exit(code=1) from err

    typer.echo(
        f"sources: read={counters.sources_read} "
        f"unreadable={counters.sources_unreadable}"
    )
    typer.echo(
        f"videos: new={counters.videos_new} "
        f"ingested={counters.videos_ingested} "
        f"already={counters.videos_already} "
        f"failed={counters.videos_failed} "
        f"skipped_limit={counters.videos_skipped_limit}"
    )
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
