"""Live composition: construct Supabase clients only here (never in use-cases)."""

from __future__ import annotations

from backend.composition.container import AppContainer
from backend.composition.mailer_factory import resolve_mailer
from backend.composition.settings import Settings
from backend.application.ports.query_embedder import StubQueryEmbedder
from backend.infrastructure.local_notebook_storage import LocalNotebookStorage
from backend.infrastructure.yaml_pipeline_config_validator import YamlPipelineConfigValidator
from supabase_integration import (
    SupabaseDigestPublisher,
    SupabaseIngestSourceRepository,
    SupabaseIssueRepository,
    SupabaseKnowledgeChunkRepository,
    SupabaseMaterialRepository,
    SupabasePingRecorder,
    SupabasePipelineConfigRepository,
    SupabaseProfileRepository,
    SupabaseRazborRepository,
    SupabaseShortlistRepository,
    SupabaseVoteRepository,
    SupabaseVotingCycleReader,
    create_publishable_client,
    create_service_role_client,
)


def build_live_container(settings: Settings) -> AppContainer:
    """Wire service_role adapters for profiles, pings, issues, materials, cycles."""
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise ValueError(
            "live container requires SUPABASE_URL and SUPABASE_SECRET_KEY "
            "(construct clients only in composition/live.py — never expose via VITE_)"
        )

    # service_role: RLS bypass for content reads + activity_events / profiles (T-02-03)
    admin_client = create_service_role_client(
        settings.supabase_url,
        settings.supabase_secret_key,
    )
    # optional publishable client kept for future user-scoped reads; constructed in composition only
    if settings.supabase_publishable_key:
        create_publishable_client(
            settings.supabase_url,
            settings.supabase_publishable_key,
        )

    return AppContainer(
        materials=SupabaseMaterialRepository(admin_client),
        chunks=SupabaseKnowledgeChunkRepository(admin_client),
        profiles=SupabaseProfileRepository(admin_client),
        pings=SupabasePingRecorder(admin_client),
        issues=SupabaseIssueRepository(admin_client),
        voting_cycles=SupabaseVotingCycleReader(admin_client),
        votes=SupabaseVoteRepository(admin_client),
        embedder=StubQueryEmbedder(),
        razbors=SupabaseRazborRepository(admin_client),
        notebook_storage=LocalNotebookStorage(settings.notebook_root or "."),
        shortlist=SupabaseShortlistRepository(admin_client),
        # PIPE-03: validated config persists to the pipeline_config singleton behind the port (D-08/D-10)
        pipeline_config=SupabasePipelineConfigRepository(admin_client),
        pipeline_config_validator=YamlPipelineConfigValidator(),
        # SRC-03 / D-21 / D-24: ingest sources behind the port (pipeline_ingest_sources, migration 012)
        ingest_sources=SupabaseIngestSourceRepository(admin_client),
        # StubMailer or live SmtpMailer via resolve_mailer — MAILER=smtp fail-fast (D-15/D-16)
        mailer=resolve_mailer(settings),
        # Atomic claim+publish via claim_and_publish_digest RPC (CR-01/WR-01, migration 005)
        publisher=SupabaseDigestPublisher(admin_client),
    )
