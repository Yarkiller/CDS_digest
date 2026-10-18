"""HTTP middleware: request_id correlation and structured logging."""

from __future__ import annotations

import logging
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = structlog.get_logger("backend.http")

_LOG_LEVELS: dict[str, int] = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


def resolve_log_level(level: str | None) -> int:
    """Map a LOG_LEVEL name to a logging level; unknown/empty defaults to INFO."""
    if not level:
        return logging.INFO
    return _LOG_LEVELS.get(level.strip().lower(), logging.INFO)


def level_for_status(status_code: int) -> str:
    """Log level for a response status: 5xx -> error, 4xx -> warning, else info."""
    if status_code >= 500:
        return "error"
    if status_code >= 400:
        return "warning"
    return "info"


def _event_for_status(status_code: int) -> str:
    if status_code >= 500:
        return "request_server_error"
    if status_code >= 400:
        return "request_client_error"
    return "request_finished"


def configure_structlog(level: int = logging.INFO) -> None:
    """JSON logs on stdout; merge contextvars for request_id; filter below `level`."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        # Log method/path/status/request_id only — never Authorization (T-01-03).
        status_code = response.status_code
        emit = getattr(log, level_for_status(status_code))
        emit(
            _event_for_status(status_code),
            method=request.method,
            path=request.url.path,
            status=status_code,
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP A05: baseline security response headers for the JSON API."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), browsing-topics=()",
        )
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        return response
