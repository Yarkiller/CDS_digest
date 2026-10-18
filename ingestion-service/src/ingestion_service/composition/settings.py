"""Env-backed settings for ingestion composition (D-16)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from data_collection.dto.template_kind import TemplateKind

from ingestion_service.composition.config_error import ConfigurationError


_DEFAULT_MAX_TRANSCRIPT_CHARS = 80000
_DEFAULT_SHORTLIST_BATCH_SIZE = 5
_DEFAULT_INGEST_MAX_VIDEOS_PER_SOURCE = 5


def _ingest_template(env: dict[str, str]) -> TemplateKind:
    raw = env.get("INGEST_TEMPLATE")
    if raw is None or raw.strip() == "":
        return TemplateKind.LECTURE
    try:
        return TemplateKind(raw.strip())
    except ValueError as exc:
        raise ConfigurationError(
            "INGEST_TEMPLATE must be one of: lecture, podcast"
        ) from exc


def _ingest_max_videos_per_source(env: dict[str, str]) -> int:
    raw = env.get("INGEST_MAX_VIDEOS_PER_SOURCE")
    if raw is None or raw.strip() == "":
        return _DEFAULT_INGEST_MAX_VIDEOS_PER_SOURCE
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigurationError(
            "INGEST_MAX_VIDEOS_PER_SOURCE must be a positive integer"
        ) from exc
    if value <= 0:
        raise ConfigurationError(
            "INGEST_MAX_VIDEOS_PER_SOURCE must be a positive integer"
        )
    return value


def _max_transcript_chars(env: dict[str, str]) -> int:
    raw = env.get("MAX_TRANSCRIPT_CHARS")
    if raw is None or raw.strip() == "":
        return _DEFAULT_MAX_TRANSCRIPT_CHARS
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigurationError(
            "MAX_TRANSCRIPT_CHARS must be a positive integer"
        ) from exc
    if value <= 0:
        raise ConfigurationError("MAX_TRANSCRIPT_CHARS must be a positive integer")
    return value


def _shortlist_batch_size(env: dict[str, str]) -> int:
    raw = env.get("SHORTLIST_BATCH_SIZE")
    if raw is None or raw.strip() == "":
        return _DEFAULT_SHORTLIST_BATCH_SIZE
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigurationError(
            "SHORTLIST_BATCH_SIZE must be a positive integer"
        ) from exc
    if value <= 0:
        raise ConfigurationError("SHORTLIST_BATCH_SIZE must be a positive integer")
    return value


def _optional_stripped(env: dict[str, str], key: str) -> str | None:
    raw = env.get(key)
    value = raw.strip() if raw is not None else None
    return value or None


@dataclass(frozen=True)
class Settings:
    youtube_proxy_url: str | None = None
    max_transcript_chars: int = _DEFAULT_MAX_TRANSCRIPT_CHARS
    deepseek_api_key: str | None = field(default=None, repr=False)
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    supabase_url: str | None = None
    supabase_secret_key: str | None = field(default=None, repr=False)
    shortlist_batch_size: int = _DEFAULT_SHORTLIST_BATCH_SIZE
    ingest_template: TemplateKind = TemplateKind.LECTURE
    ingest_max_videos_per_source: int = _DEFAULT_INGEST_MAX_VIDEOS_PER_SOURCE

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        env = environ if environ is not None else os.environ
        raw_proxy = env.get("YOUTUBE_PROXY_URL")
        proxy = raw_proxy.strip() if raw_proxy is not None else None
        proxy = proxy or None

        raw_key = env.get("DEEPSEEK_API_KEY")
        key = raw_key.strip() if raw_key is not None else None
        key = key or None

        raw_base = env.get("DEEPSEEK_BASE_URL")
        base_url = raw_base.strip() if raw_base is not None else "https://api.deepseek.com"

        raw_model = env.get("DEEPSEEK_MODEL")
        model = raw_model.strip() if raw_model is not None else "deepseek-flash"

        return cls(
            youtube_proxy_url=proxy,
            max_transcript_chars=_max_transcript_chars(env),
            deepseek_api_key=key,
            deepseek_base_url=base_url,
            deepseek_model=model,
            supabase_url=_optional_stripped(env, "SUPABASE_URL"),
            supabase_secret_key=_optional_stripped(env, "SUPABASE_SECRET_KEY"),
            shortlist_batch_size=_shortlist_batch_size(env),
            ingest_template=_ingest_template(env),
            ingest_max_videos_per_source=_ingest_max_videos_per_source(env),
        )
