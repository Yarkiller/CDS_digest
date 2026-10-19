"""Offline wiring tests for build_live_container + APP_CONTAINER selection."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.composition.container import AppContainer, build_in_memory_container
from backend.composition.live import build_live_container
from backend.composition.settings import Settings
from backend.interface.http.app import create_app, resolve_container
from backend.tests_support.in_memory import InMemoryPingRecorder, InMemoryProfileRepository
from backend.tests_support.in_memory import (
    InMemoryIssueRepository,
    InMemoryMaterialRepository,
    InMemoryPingRecorder,
    InMemoryProfileRepository,
)
from supabase_integration import SupabasePingRecorder, SupabaseProfileRepository


def test_build_live_container_wires_supabase_adapters(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.tests_support.in_memory import InMemoryVoteRepository
    from supabase_integration import (
        SupabaseIssueRepository,
        SupabaseMaterialRepository,
        SupabaseVoteRepository,
        SupabaseVotingCycleReader,
    )

    fake_service = object()
    fake_publishable = object()
    create_service = MagicMock(return_value=fake_service)
    create_publishable = MagicMock(return_value=fake_publishable)
    monkeypatch.setattr(
        "backend.composition.live.create_service_role_client",
        create_service,
    )
    monkeypatch.setattr(
        "backend.composition.live.create_publishable_client",
        create_publishable,
    )

    settings = Settings(
        supabase_url="https://example.test",
        supabase_secret_key="secret-key",
        supabase_publishable_key="publishable-key",
        supabase_jwks_url="https://example.test/auth/v1/.well-known/jwks.json",
        supabase_jwt_issuer="https://example.test/auth/v1",
    )

    container = build_live_container(settings)

    assert isinstance(container, AppContainer)
    assert isinstance(container.profiles, SupabaseProfileRepository)
    assert isinstance(container.pings, SupabasePingRecorder)
    assert isinstance(container.materials, SupabaseMaterialRepository)
    assert isinstance(container.issues, SupabaseIssueRepository)
    assert isinstance(container.voting_cycles, SupabaseVotingCycleReader)
    assert isinstance(container.votes, SupabaseVoteRepository)
    assert not isinstance(container.votes, InMemoryVoteRepository)
    assert not isinstance(container.materials, InMemoryMaterialRepository)
    assert not isinstance(container.issues, InMemoryIssueRepository)

    from backend.tests_support.in_memory import (
        InMemoryKnowledgeChunkRepository,
        InMemoryRazborRepository,
    )
    from supabase_integration import (
        SupabaseKnowledgeChunkRepository,
        SupabaseRazborRepository,
    )

    assert isinstance(container.chunks, SupabaseKnowledgeChunkRepository)
    assert isinstance(container.razbors, SupabaseRazborRepository)
    assert not isinstance(container.chunks, InMemoryKnowledgeChunkRepository)
    assert not isinstance(container.razbors, InMemoryRazborRepository)

    from backend.infrastructure.stub_mailer import StubMailer
    from backend.tests_support.in_memory import (
        InMemoryDigestPublisher,
        InMemoryShortlistRepository,
    )
    from supabase_integration import SupabaseDigestPublisher, SupabaseShortlistRepository

    assert isinstance(container.shortlist, SupabaseShortlistRepository)
    assert not isinstance(container.shortlist, InMemoryShortlistRepository)
    assert isinstance(container.mailer, StubMailer)
    assert isinstance(container.publisher, SupabaseDigestPublisher)
    assert not isinstance(container.publisher, InMemoryDigestPublisher)

    from backend.infrastructure.yaml_pipeline_config_validator import YamlPipelineConfigValidator
    from backend.tests_support.in_memory import InMemoryPipelineConfigRepository
    from supabase_integration import SupabasePipelineConfigRepository

    assert isinstance(container.pipeline_config, SupabasePipelineConfigRepository)
    assert not isinstance(container.pipeline_config, InMemoryPipelineConfigRepository)
    assert isinstance(container.pipeline_config_validator, YamlPipelineConfigValidator)

    from backend.tests_support.in_memory import InMemoryIngestSourceRepository
    from supabase_integration import SupabaseIngestSourceRepository

    # D-24: live wires SupabaseIngestSourceRepository (not in-memory)
    assert isinstance(container.ingest_sources, SupabaseIngestSourceRepository)
    assert not isinstance(container.ingest_sources, InMemoryIngestSourceRepository)

    create_service.assert_called_once_with(
        "https://example.test",
        "secret-key",
    )
    create_publishable.assert_called_once_with(
        "https://example.test",
        "publishable-key",
    )


def test_build_live_container_wires_ingest_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-21 / D-24 / SRC-03: live composition wires SupabaseIngestSourceRepository."""
    from backend.tests_support.in_memory import InMemoryIngestSourceRepository
    from supabase_integration import SupabaseIngestSourceRepository

    monkeypatch.setattr(
        "backend.composition.live.create_service_role_client",
        MagicMock(return_value=object()),
    )
    settings = Settings(
        supabase_url="https://example.test",
        supabase_secret_key="secret-key",
    )

    container = build_live_container(settings)

    assert isinstance(container.ingest_sources, SupabaseIngestSourceRepository)
    assert not isinstance(container.ingest_sources, InMemoryIngestSourceRepository)


def test_build_live_container_wires_pipeline_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-10 / PIPE-03: live composition wires the Supabase adapter + the real YAML validator."""
    from backend.infrastructure.yaml_pipeline_config_validator import YamlPipelineConfigValidator
    from backend.tests_support.in_memory import InMemoryPipelineConfigRepository
    from supabase_integration import SupabasePipelineConfigRepository

    monkeypatch.setattr(
        "backend.composition.live.create_service_role_client",
        MagicMock(return_value=object()),
    )
    settings = Settings(
        supabase_url="https://example.test",
        supabase_secret_key="secret-key",
    )

    container = build_live_container(settings)

    assert isinstance(container.pipeline_config, SupabasePipelineConfigRepository)
    assert not isinstance(container.pipeline_config, InMemoryPipelineConfigRepository)
    assert isinstance(container.pipeline_config_validator, YamlPipelineConfigValidator)


def test_build_live_container_rejects_incomplete_smtp_mailer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-16: MAILER=smtp without SMTP_* fail-fasts at live container build."""
    from backend.composition.config_error import ConfigurationError

    monkeypatch.setattr(
        "backend.composition.live.create_service_role_client",
        MagicMock(return_value=object()),
    )
    settings = Settings(
        supabase_url="https://example.test",
        supabase_secret_key="secret-key",
        mailer="smtp",
    )
    with pytest.raises(ConfigurationError, match="SMTP_HOST"):
        build_live_container(settings)


def test_build_live_container_wires_smtp_mailer_when_settings_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-15: with complete SMTP_* the live container wires the real SmtpMailer."""
    from backend.infrastructure.smtp_mailer import SmtpMailer

    monkeypatch.setattr(
        "backend.composition.live.create_service_role_client",
        MagicMock(return_value=object()),
    )
    settings = Settings(
        supabase_url="https://example.test",
        supabase_secret_key="secret-key",
        mailer="smtp",
        smtp_host="relay.example.test",
        smtp_port=587,
        smtp_user="digest-bot",
        smtp_pass="s3cret",
        smtp_from="digest@knowledge-db.ru",
    )

    container = build_live_container(settings)

    assert isinstance(container.mailer, SmtpMailer)


def test_settings_exposes_jwks_url_and_issuer_from_env() -> None:
    settings = Settings.from_env(
        {
            "SUPABASE_JWKS_URL": "https://jwks.example/jwks.json",
            "SUPABASE_JWT_ISSUER": "https://issuer.example/auth/v1",
            "APP_CONTAINER": "live",
        }
    )
    assert settings.supabase_jwks_url == "https://jwks.example/jwks.json"
    assert settings.supabase_jwt_issuer == "https://issuer.example/auth/v1"
    assert settings.app_container == "live"


def test_resolve_container_defaults_to_in_memory() -> None:
    settings = Settings()
    container = resolve_container(settings)
    assert isinstance(container.profiles, InMemoryProfileRepository)
    assert isinstance(container.pings, InMemoryPingRecorder)


def test_resolve_container_live_uses_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = build_in_memory_container()
    monkeypatch.setattr(
        "backend.composition.live.build_live_container",
        lambda _settings: sentinel,
    )
    settings = Settings(app_container="live")
    assert resolve_container(settings) is sentinel


def test_create_app_without_container_uses_memory_default() -> None:
    app = create_app(Settings())
    assert isinstance(app.state.container.profiles, InMemoryProfileRepository)
    assert isinstance(app.state.container.pings, InMemoryPingRecorder)


def test_auth_jwt_uses_settings_jwks_url_not_hardcoded_host() -> None:
    from pathlib import Path

    import backend.infrastructure.auth_jwt as auth_jwt

    source = Path(auth_jwt.__file__).read_text(encoding="utf-8")
    assert "knowledge-db.ru" not in source
    assert "PyJWKClient" in source
