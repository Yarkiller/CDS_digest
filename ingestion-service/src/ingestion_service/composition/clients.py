"""Ready YouTube / httpx / DeepSeek clients — proxy only here, never in adapters (D-17)."""

from __future__ import annotations

import httpx
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from supabase import Client, create_client
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
from data_collection.adapters.deepseek_classifier import DeepSeekTopicKindClassifier
from data_collection.adapters.youtube_feed import YouTubeFeedAdapter
from data_collection.adapters.youtube_oembed import YouTubeOEmbedAdapter
from data_collection.adapters.youtube_transcript import YouTubeTranscriptAdapter
from data_collection.templates import load_article_templates

from ingestion_service.adapters.supabase_collect_sources import (
    SupabaseCollectSourceReader,
)
from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister
from ingestion_service.composition.config_error import ConfigurationError
from ingestion_service.composition.settings import Settings

_DEFAULT_TIMEOUT = 30.0
_DEEPSEEK_TIMEOUT = 120.0


def build_youtube_transcript_api(settings: Settings) -> YouTubeTranscriptApi:
    proxy = settings.youtube_proxy_url
    if proxy:
        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(http_url=proxy, https_url=proxy)
        )
    return YouTubeTranscriptApi()


def build_httpx_client(settings: Settings) -> httpx.AsyncClient:
    proxy = settings.youtube_proxy_url
    if proxy:
        return httpx.AsyncClient(proxy=proxy, timeout=_DEFAULT_TIMEOUT)
    return httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)


def build_youtube_captions(settings: Settings) -> YouTubeTranscriptAdapter:
    """Wire YouTube captions adapter from Settings (D-02; adapters never read os.environ)."""
    return YouTubeTranscriptAdapter(build_youtube_transcript_api(settings))


def build_youtube_metadata_provider(settings: Settings) -> YouTubeOEmbedAdapter:
    """Wire YouTube oEmbed metadata adapter from Settings (D-02)."""
    return YouTubeOEmbedAdapter(build_httpx_client(settings))


def build_youtube_feed(settings: Settings) -> YouTubeFeedAdapter:
    """Wire YouTube Atom feed adapter from Settings (ING-02)."""
    return YouTubeFeedAdapter(build_httpx_client(settings))


def build_collect_source_reader(settings: Settings) -> SupabaseCollectSourceReader:
    """Wire CollectSourceReader against pipeline_ingest_sources (ING-02)."""
    return SupabaseCollectSourceReader(build_supabase_service_client(settings))


def build_async_deepseek_client(
    api_key: str, base_url: str, timeout: float
) -> AsyncOpenAI:
    if not api_key or not api_key.strip():
        raise ConfigurationError("DEEPSEEK_API_KEY is required")
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        max_retries=0,
        http_client=DefaultAsyncHttpxClient(trust_env=False),
    )


def build_deepseek_article_generator(
    settings: Settings,
    template_root: object | None = None,
) -> DeepSeekArticleGenerator:
    import importlib.resources

    root = (
        template_root
        if template_root is not None
        else importlib.resources.files("data_collection.templates")
    )
    templates = load_article_templates(root)
    client = build_async_deepseek_client(
        settings.deepseek_api_key or "",
        settings.deepseek_base_url,
        _DEEPSEEK_TIMEOUT,
    )
    return DeepSeekArticleGenerator(
        client=client,
        model=settings.deepseek_model,
        templates=templates,
        max_transcript_chars=settings.max_transcript_chars,
    )


def build_deepseek_topic_kind_classifier(
    settings: Settings,
) -> DeepSeekTopicKindClassifier:
    client = build_async_deepseek_client(
        settings.deepseek_api_key or "",
        settings.deepseek_base_url,
        _DEEPSEEK_TIMEOUT,
    )
    return DeepSeekTopicKindClassifier(
        client=client,
        model=settings.deepseek_model,
    )


def build_supabase_service_client(settings: Settings) -> Client:
    url = settings.supabase_url
    key = settings.supabase_secret_key
    if not url or not url.strip() or not key or not key.strip():
        raise ConfigurationError("SUPABASE_URL and SUPABASE_SECRET_KEY are required")
    return create_client(url, key)


def build_supabase_draft_persister(settings: Settings) -> SupabaseDraftPersister:
    client = build_supabase_service_client(settings)
    return SupabaseDraftPersister(client, batch_size=settings.shortlist_batch_size)
