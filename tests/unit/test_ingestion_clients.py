"""RED→GREEN: composition factories for the Supabase service-role client (D-02)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INGESTION_ENV_EXAMPLE = REPO_ROOT / "ingestion-service" / ".env.example"


def _install_create_client_spy(clients_module: object) -> tuple[list[tuple[str, str]], object, object]:
    created: list[tuple[str, str]] = []
    sentinel = object()

    def _spy(url: str, key: str) -> object:
        created.append((url, key))
        return sentinel

    original = getattr(clients_module, "create_client", None)
    clients_module.create_client = _spy  # type: ignore[attr-defined]
    return created, sentinel, original


def _restore_create_client(clients_module: object, original: object) -> None:
    if original is not None:
        clients_module.create_client = original  # type: ignore[attr-defined]
    elif hasattr(clients_module, "create_client"):
        delattr(clients_module, "create_client")


def test_build_supabase_service_client_rejects_blank_and_does_not_create_client() -> None:
    from ingestion_service.composition.config_error import ConfigurationError
    from ingestion_service.composition.settings import Settings
    import ingestion_service.composition.clients as clients_module

    created, _sentinel, original = _install_create_client_spy(clients_module)
    try:
        build = clients_module.build_supabase_service_client
        with pytest.raises(ConfigurationError):
            build(Settings.from_env({}))
        assert created == []
    finally:
        _restore_create_client(clients_module, original)


@pytest.mark.parametrize(
    "env",
    [
        {"SUPABASE_URL": "", "SUPABASE_SECRET_KEY": "x"},
        {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SECRET_KEY": ""},
        {"SUPABASE_URL": "   ", "SUPABASE_SECRET_KEY": "x"},
        {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SECRET_KEY": "   "},
    ],
)
def test_build_supabase_service_client_rejects_blank_url_or_key(env: dict[str, str]) -> None:
    from ingestion_service.composition.config_error import ConfigurationError
    from ingestion_service.composition.settings import Settings
    import ingestion_service.composition.clients as clients_module

    created, _sentinel, original = _install_create_client_spy(clients_module)
    try:
        build = clients_module.build_supabase_service_client
        with pytest.raises(ConfigurationError):
            build(Settings.from_env(env))
        assert created == []
    finally:
        _restore_create_client(clients_module, original)


def test_build_supabase_service_client_calls_create_client_with_url_and_key() -> None:
    from ingestion_service.composition.settings import Settings
    import ingestion_service.composition.clients as clients_module

    created, sentinel, original = _install_create_client_spy(clients_module)
    try:
        build = clients_module.build_supabase_service_client
        settings = Settings.from_env(
            {
                "SUPABASE_URL": "https://x.supabase.co",
                "SUPABASE_SECRET_KEY": "x",
            }
        )
        client = build(settings)
        assert created == [("https://x.supabase.co", "x")]
        assert client is sentinel
    finally:
        _restore_create_client(clients_module, original)


def test_build_supabase_draft_persister_uses_settings_batch_size() -> None:
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister
    from ingestion_service.composition.settings import Settings
    import ingestion_service.composition.clients as clients_module

    created, sentinel, original = _install_create_client_spy(clients_module)
    try:
        build = clients_module.build_supabase_draft_persister
        settings = Settings.from_env(
            {
                "SUPABASE_URL": "https://x.supabase.co",
                "SUPABASE_SECRET_KEY": "x",
                "SHORTLIST_BATCH_SIZE": "3",
            }
        )
        persister = build(settings)
        assert isinstance(persister, SupabaseDraftPersister)
        assert persister._batch_size == settings.shortlist_batch_size
        assert persister._batch_size == 3
        assert created == [("https://x.supabase.co", "x")]
        assert persister._client is sentinel
    finally:
        _restore_create_client(clients_module, original)


def test_composition_exports_supabase_factories() -> None:
    import ingestion_service.composition as composition

    assert "build_supabase_service_client" in composition.__all__
    assert "build_supabase_draft_persister" in composition.__all__
    assert composition.build_supabase_service_client is not None
    assert composition.build_supabase_draft_persister is not None
    for name in (
        "Settings",
        "ConfigurationError",
        "build_youtube_transcript_api",
        "build_httpx_client",
        "build_async_deepseek_client",
        "build_deepseek_article_generator",
    ):
        assert name in composition.__all__


def test_ingestion_env_example_documents_supabase_placeholders() -> None:
    assert INGESTION_ENV_EXAMPLE.is_file()
    text = INGESTION_ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "SUPABASE_URL=" in text
    assert "SUPABASE_SECRET_KEY=" in text
    assert "SHORTLIST_BATCH_SIZE=5" in text
    assert "s3cr3t" not in text
    assert "eyJ" not in text
