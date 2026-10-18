"""Public liveness and readiness probes — no auth."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from backend.application.use_cases.check_readiness import check_readiness

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up. Never touches external dependencies."""
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(request: Request, response: Response) -> dict:
    """Readiness: every registered dependency probe must be healthy."""
    container = getattr(request.app.state, "container", None)
    probes = tuple(getattr(container, "health_probes", ()) or ())
    report = check_readiness(probes)
    if not report.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report.to_public_dict()
