"""Supabase integration public API."""

from pathlib import Path

from supabase_integration.client import create_publishable_client, create_service_role_client
from supabase_integration.digest_publisher import SupabaseDigestPublisher
from supabase_integration.ingest_source_repository import SupabaseIngestSourceRepository
from supabase_integration.ingestion_schedule_repository import (
    SupabaseIngestionScheduleRepository,
)
from supabase_integration.issue_repository import SupabaseIssueRepository
from supabase_integration.knowledge_chunk_repository import SupabaseKnowledgeChunkRepository
from supabase_integration.material_repository import SupabaseMaterialRepository
from supabase_integration.ping_recorder import SupabasePingRecorder
from supabase_integration.pipeline_config_repository import SupabasePipelineConfigRepository
from supabase_integration.profile_repository import SupabaseProfileRepository
from supabase_integration.razbor_repository import SupabaseRazborRepository
from supabase_integration.shortlist_repository import SupabaseShortlistRepository
from supabase_integration.vote_repository import SupabaseVoteRepository
from supabase_integration.voting_cycle_repository import SupabaseVotingCycleReader


def migrations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "migrations"


__all__ = [
    "SupabaseDigestPublisher",
    "SupabaseIngestSourceRepository",
    "SupabaseIngestionScheduleRepository",
    "SupabaseIssueRepository",
    "SupabaseKnowledgeChunkRepository",
    "SupabaseMaterialRepository",
    "SupabasePingRecorder",
    "SupabasePipelineConfigRepository",
    "SupabaseProfileRepository",
    "SupabaseRazborRepository",
    "SupabaseShortlistRepository",
    "SupabaseVoteRepository",
    "SupabaseVotingCycleReader",
    "create_publishable_client",
    "create_service_role_client",
    "migrations_dir",
]
