"""RED→GREEN: ingestion Settings + proxy clients + 07-01 verify-only (D-16…D-20)."""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_settings_from_env_reads_youtube_proxy_url() -> None:
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env(
        {"YOUTUBE_PROXY_URL": "socks5://192.168.1.68:1080"}
    )
    assert settings.youtube_proxy_url == "socks5://192.168.1.68:1080"


def test_settings_from_env_unset_youtube_proxy_url_is_none() -> None:
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({})
    assert settings.youtube_proxy_url is None


def test_build_youtube_transcript_api_injects_generic_proxy_when_set() -> None:
    from ingestion_service.composition.clients import build_youtube_transcript_api
    from ingestion_service.composition.settings import Settings
    from youtube_transcript_api.proxies import GenericProxyConfig

    settings = Settings.from_env(
        {"YOUTUBE_PROXY_URL": "socks5://192.168.1.68:1080"}
    )
    api = build_youtube_transcript_api(settings)
    proxy_config = api._fetcher._proxy_config
    assert proxy_config is not None
    assert isinstance(proxy_config, GenericProxyConfig)


def test_build_youtube_transcript_api_direct_when_unset() -> None:
    from ingestion_service.composition.clients import build_youtube_transcript_api
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({})
    api = build_youtube_transcript_api(settings)
    assert api._fetcher._proxy_config is None


def test_build_httpx_client_uses_proxy_when_set() -> None:
    import asyncio

    import httpx
    from ingestion_service.composition.clients import build_httpx_client
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env(
        {"YOUTUBE_PROXY_URL": "socks5://192.168.1.68:1080"}
    )
    client = build_httpx_client(settings)
    assert isinstance(client, httpx.AsyncClient)
    # httpx 0.28 stores proxy as mounted AsyncHTTPTransport entries
    assert len(client._mounts) > 0
    asyncio.run(client.aclose())


def test_build_httpx_client_direct_when_unset() -> None:
    import asyncio

    import httpx
    from ingestion_service.composition.clients import build_httpx_client
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({})
    client = build_httpx_client(settings)
    assert isinstance(client, httpx.AsyncClient)
    assert len(client._mounts) == 0
    asyncio.run(client.aclose())


def test_verify_07_01_socks_deps_remain_in_data_collection_pyproject() -> None:
    """D-18 verify-only: do not re-add — confirm leftovers from 07-01."""
    text = (REPO_ROOT / "data-collection" / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert "httpx[socks]" in text
    assert "requests[socks]" in text or "PySocks" in text


def test_verify_07_01_integration_marker_registered() -> None:
    """D-20 verify-only: root pytest still registers integration marker."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "integration:" in text or '"integration"' in text
    assert "integration" in text


def test_adapters_do_not_read_environ() -> None:
    adapter_root = (
        REPO_ROOT / "data-collection" / "src" / "data_collection" / "adapters"
    )
    for path in adapter_root.glob("*.py"):
        if path.name == "__init__.py":
            continue
        body = path.read_text(encoding="utf-8")
        assert "os.environ" not in body, path.name
        assert "os.getenv" not in body, path.name


def test_settings_from_env_defaults() -> None:
    from data_collection.dto.template_kind import TemplateKind
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({})
    assert settings.max_transcript_chars == 80000
    assert settings.deepseek_api_key is None
    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.deepseek_model == "deepseek-flash"
    assert settings.ingest_template is TemplateKind.LECTURE
    assert settings.ingest_max_videos_per_source == 5


def test_settings_from_env_reads_ingest_template_podcast() -> None:
    from data_collection.dto.template_kind import TemplateKind
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({"INGEST_TEMPLATE": "podcast"})
    assert settings.ingest_template is TemplateKind.PODCAST


@pytest.mark.parametrize("raw", ["webinar", "LECTURE", ""])
def test_invalid_ingest_template_raises_configuration_error(raw: str) -> None:
    from ingestion_service.composition.config_error import ConfigurationError
    from ingestion_service.composition.settings import Settings
    from ingestion_service.domain.errors import IngestError

    with pytest.raises(ConfigurationError) as exc_info:
        Settings.from_env({"INGEST_TEMPLATE": raw})
    assert not isinstance(exc_info.value, IngestError)


@pytest.mark.parametrize("raw", ["0", "-1", "abc", "5.5"])
def test_invalid_ingest_max_videos_per_source_raises_configuration_error(
    raw: str,
) -> None:
    from ingestion_service.composition.config_error import ConfigurationError
    from ingestion_service.composition.settings import Settings
    from ingestion_service.domain.errors import IngestError

    with pytest.raises(ConfigurationError) as exc_info:
        Settings.from_env({"INGEST_MAX_VIDEOS_PER_SOURCE": raw})
    assert not isinstance(exc_info.value, IngestError)


def test_settings_from_env_blank_max_transcript_chars_defaults() -> None:
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({"MAX_TRANSCRIPT_CHARS": "  "})
    assert settings.max_transcript_chars == 80000


def test_settings_from_env_reads_deepseek_values() -> None:
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env(
        {
            "DEEPSEEK_API_KEY": "sk-test-key",
            "DEEPSEEK_BASE_URL": "https://custom.example.com",
            "DEEPSEEK_MODEL": "deepseek-v4-pro",
            "MAX_TRANSCRIPT_CHARS": "5000",
        }
    )
    assert settings.deepseek_api_key == "sk-test-key"
    assert settings.deepseek_base_url == "https://custom.example.com"
    assert settings.deepseek_model == "deepseek-v4-pro"
    assert settings.max_transcript_chars == 5000


def test_build_async_deepseek_client_rejects_blank_key() -> None:
    from ingestion_service.composition.clients import build_async_deepseek_client
    from ingestion_service.composition.config_error import ConfigurationError

    with pytest.raises(ConfigurationError):
        build_async_deepseek_client("", "https://api.deepseek.com", 120.0)


def test_build_async_deepseek_client_rejects_blank_key_without_constructing() -> None:
    from ingestion_service.composition.clients import build_async_deepseek_client
    from ingestion_service.composition.config_error import ConfigurationError

    constructed: list[object] = []
    sentinel_key = "sk-sentinel-key-for-construction-test"

    real_async_openai = None
    try:
        from openai import AsyncOpenAI

        real_async_openai = AsyncOpenAI
    except ImportError:
        pass

    if real_async_openai is not None:
        import ingestion_service.composition.clients as clients_module

        original = clients_module.AsyncOpenAI

        class _SpyAsyncOpenAI(AsyncOpenAI):
            def __init__(self, **kwargs: object) -> None:
                constructed.append(kwargs)
                super().__init__(**kwargs)

        clients_module.AsyncOpenAI = _SpyAsyncOpenAI
        try:
            with pytest.raises(ConfigurationError):
                build_async_deepseek_client("", "https://api.deepseek.com", 120.0)
            assert constructed == []
            # valid key should construct
            build_async_deepseek_client(sentinel_key, "https://api.deepseek.com", 120.0)
            assert len(constructed) == 1
            assert constructed[0]["api_key"] == sentinel_key
            assert constructed[0]["max_retries"] == 0
            assert constructed[0]["timeout"] == 120.0
            assert constructed[0]["http_client"]._trust_env is False
        finally:
            clients_module.AsyncOpenAI = original


def test_build_deepseek_article_generator_rejects_blank_key() -> None:
    from ingestion_service.composition.clients import build_deepseek_article_generator
    from ingestion_service.composition.config_error import ConfigurationError
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({})
    with pytest.raises(ConfigurationError):
        build_deepseek_article_generator(settings)


def test_build_deepseek_article_generator_does_not_construct_async_openai_for_blank_key() -> None:
    from ingestion_service.composition.clients import build_deepseek_article_generator
    from ingestion_service.composition.config_error import ConfigurationError
    from ingestion_service.composition.settings import Settings

    constructed: list[object] = []

    from openai import AsyncOpenAI

    import ingestion_service.composition.clients as clients_module

    original = clients_module.AsyncOpenAI

    class _SpyAsyncOpenAI(AsyncOpenAI):
        def __init__(self, **kwargs: object) -> None:
            constructed.append(kwargs)
            super().__init__(**kwargs)

    clients_module.AsyncOpenAI = _SpyAsyncOpenAI
    try:
        settings = Settings.from_env({})
        with pytest.raises(ConfigurationError):
            build_deepseek_article_generator(settings)
        assert constructed == []
    finally:
        clients_module.AsyncOpenAI = original


@pytest.mark.parametrize("raw", ["0", "-1", "abc", "80.5"])
def test_invalid_max_transcript_chars_raises_configuration_error(raw: str) -> None:
    from ingestion_service.composition.config_error import ConfigurationError
    from ingestion_service.composition.settings import Settings
    from ingestion_service.domain.errors import IngestError

    with pytest.raises(ConfigurationError) as exc_info:
        Settings.from_env({"MAX_TRANSCRIPT_CHARS": raw})
    assert not isinstance(exc_info.value, IngestError)


def test_blank_max_transcript_chars_yields_default() -> None:
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({"MAX_TRANSCRIPT_CHARS": "   "})
    assert settings.max_transcript_chars == 80000


def test_settings_from_env_unset_supabase_fields_and_default_batch_size() -> None:
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({})
    assert settings.supabase_url is None
    assert settings.supabase_secret_key is None
    assert settings.shortlist_batch_size == 5


def test_settings_from_env_reads_supabase_url_verbatim() -> None:
    from ingestion_service.composition.settings import Settings

    url = "https://example.supabase.co"
    settings = Settings.from_env({"SUPABASE_URL": url})
    assert settings.supabase_url == url


def test_settings_from_env_loads_supabase_secret_key_when_set() -> None:
    from ingestion_service.composition.settings import Settings

    env = {"SUPABASE_SECRET_KEY": "placeholder-service-role"}
    settings = Settings.from_env(env)
    assert settings.supabase_secret_key is not None
    assert settings.supabase_secret_key == env["SUPABASE_SECRET_KEY"]


def test_settings_from_env_shortlist_batch_size_three() -> None:
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({"SHORTLIST_BATCH_SIZE": "3"})
    assert settings.shortlist_batch_size == 3


@pytest.mark.parametrize("raw", ["0", "-1", "abc", "5.5"])
def test_invalid_shortlist_batch_size_raises_configuration_error(raw: str) -> None:
    from ingestion_service.composition.config_error import ConfigurationError
    from ingestion_service.composition.settings import Settings
    from ingestion_service.domain.errors import IngestError

    with pytest.raises(ConfigurationError) as exc_info:
        Settings.from_env({"SHORTLIST_BATCH_SIZE": raw})
    assert not isinstance(exc_info.value, IngestError)


def test_shortlist_batch_size_trailing_space_yields_five() -> None:
    from ingestion_service.composition.settings import Settings

    settings = Settings.from_env({"SHORTLIST_BATCH_SIZE": "5 "})
    assert settings.shortlist_batch_size == 5


def test_settings_source_does_not_log_or_print_secret_key() -> None:
    settings_src = (
        REPO_ROOT
        / "ingestion-service"
        / "src"
        / "ingestion_service"
        / "composition"
        / "settings.py"
    )
    body = settings_src.read_text(encoding="utf-8")
    lowered = body.lower()
    assert "print(" not in lowered
    assert "logging" not in lowered
    assert "logger" not in lowered


def test_settings_repr_and_str_omit_secret_fields() -> None:
    from ingestion_service.composition.settings import Settings

    secret = "s3cr3t-k3y-t-09-13"
    llm_key = "sk-deepseek-t-09-13"
    settings = Settings.from_env(
        {
            "SUPABASE_SECRET_KEY": secret,
            "DEEPSEEK_API_KEY": llm_key,
        }
    )
    rendered = f"{settings!r} {settings!s}"
    assert secret not in rendered
    assert llm_key not in rendered
    assert settings.supabase_secret_key == secret
    assert settings.deepseek_api_key == llm_key
