"""Ingestion composition package — Settings and ready-client factories."""

from ingestion_service.composition.clients import (
    build_async_deepseek_client,
    build_deepseek_article_generator,
    build_httpx_client,
    build_supabase_draft_persister,
    build_supabase_service_client,
    build_youtube_transcript_api,
)
from ingestion_service.composition.config_error import ConfigurationError
from ingestion_service.composition.settings import Settings

__all__ = [
    "Settings",
    "ConfigurationError",
    "build_youtube_transcript_api",
    "build_httpx_client",
    "build_async_deepseek_client",
    "build_deepseek_article_generator",
    "build_supabase_service_client",
    "build_supabase_draft_persister",
]
