"""FastAPI application factory — HTTP edge only."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.composition.container import AppContainer, build_in_memory_container
from backend.composition.settings import Settings
from backend.interface.http.middleware import (
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    configure_structlog,
    resolve_log_level,
)
from backend.interface.http.routes import admin, health, issues, knowledge, materials, me, razbory, voting


def resolve_container(settings: Settings) -> AppContainer:
    """Select in-memory (default) or live Supabase wiring from Settings.app_container."""
    if settings.app_container == "live":
        from backend.composition.live import build_live_container

        return build_live_container(settings)
    return build_in_memory_container(notebook_root=settings.notebook_root or None)


def create_app(
    settings: Settings,
    container: Any | None = None,
    *,
    signing_key_resolver: Callable[[str], Mapping[str, Any] | Any] | None = None,
) -> FastAPI:
    """Build the public API app with health + authenticated /me and /me/ping."""
    configure_structlog(resolve_log_level(settings.log_level))
    app = FastAPI(title="Digest CDS API", version="0.1.0")
    app.state.container = container if container is not None else resolve_container(settings)
    app.state.settings = settings
    app.state.signing_key_resolver = signing_key_resolver

    # Starlette runs the last added middleware first. CORS must be outermost.
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(issues.router)
    app.include_router(issues.archive_router)
    app.include_router(materials.router)
    app.include_router(knowledge.router)
    app.include_router(razbory.router)
    app.include_router(voting.router)
    app.include_router(admin.router)
    return app


def create_default_app() -> FastAPI:
    """Uvicorn factory: load Settings from environment and wire the selected container."""
    settings = Settings.from_env()
    return create_app(settings, container=resolve_container(settings))
