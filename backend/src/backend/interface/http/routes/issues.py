"""Authenticated issue endpoints — current, archive, by-number (ISSUE-01 / ISSUE-04)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from backend.application.use_cases.get_current_issue import get_current_issue
from backend.application.use_cases.get_issue_by_number import get_issue_by_number
from backend.application.use_cases.list_archive_issues import list_archive_issues
from backend.domain.auth_claims import AccessTokenClaims
from backend.domain.errors import IssueNotFoundError, PersistenceError
from backend.domain.issue import Issue
from backend.domain.voting_cycle import VotingCycle
from backend.interface.http.deps import get_principal

router = APIRouter(prefix="/issues", tags=["issues"])
archive_router = APIRouter(tags=["archive"])


class IssueItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    title: str
    position: int
    format: str
    reading_minutes: int
    dek: str | None = None


class VotingCycleResponse(BaseModel):
    """Read-only cycle stub on current issue only (D-32/D-33)."""

    model_config = ConfigDict(extra="forbid")

    status: str
    closes_at: datetime


class CurrentIssueResponse(BaseModel):
    """Honest empty: number/title null and items=[] when no published issue (D-24/D-30)."""

    model_config = ConfigDict(extra="forbid")

    number: int | None = None
    period_label: str | None = None
    title: str | None = None
    editor: str | None = None
    items: list[IssueItemResponse] = []
    voting_cycle: VotingCycleResponse | None = None


class ArchiveIssueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int
    period_label: str
    title: str
    material_count: int


class ArchiveListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issues: list[ArchiveIssueResponse] = []


def _cycle_response(cycle: VotingCycle | None) -> VotingCycleResponse | None:
    if cycle is None:
        return None
    return VotingCycleResponse(status=cycle.status, closes_at=cycle.closes_at)


def _to_response(
    issue: Issue | None,
    *,
    voting_cycle: VotingCycle | None = None,
) -> CurrentIssueResponse:
    if issue is None:
        return CurrentIssueResponse(voting_cycle=_cycle_response(voting_cycle))
    return CurrentIssueResponse(
        number=issue.number,
        period_label=issue.period_label,
        title=issue.title,
        editor=issue.editor,
        items=[
            IssueItemResponse(
                slug=item.slug,
                title=item.title,
                position=item.position,
                format=item.format,
                reading_minutes=item.reading_minutes,
                dek=item.dek,
            )
            for item in issue.items
        ],
        voting_cycle=_cycle_response(voting_cycle),
    )


def _require_issues(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "issues", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="issues_not_configured",
        )
    return container.issues


def _voting_cycles(request: Request):
    container = request.app.state.container
    if container is None:
        return None
    return getattr(container, "voting_cycles", None)


@router.get(
    "/current",
    response_model=CurrentIssueResponse,
    summary="Current published issue",
    description=(
        "Returns the latest published digest issue by published_at (D-24). "
        "Includes read-only voting_cycle when present (D-33). "
        "Requires Bearer JWT. Empty published set → 200 with null fields and empty items."
    ),
)
def read_current_issue(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentIssueResponse:
    del claims  # auth gate only; content is reader-shared
    issues = _require_issues(request)
    try:
        view = get_current_issue(issues, _voting_cycles(request))
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="issues_unavailable",
        ) from exc
    return _to_response(view.issue, voting_cycle=view.voting_cycle)


@router.get(
    "/{number}",
    response_model=CurrentIssueResponse,
    summary="Published issue by number",
    description=(
        "Returns a published digest issue by number. "
        "Requires Bearer JWT. Missing or unpublished → 404. "
        "Never includes voting_cycle (D-34)."
    ),
)
def read_issue_by_number(
    number: int,
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentIssueResponse:
    del claims
    issues = _require_issues(request)
    try:
        issue = get_issue_by_number(issues, number)
    except IssueNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="issue_not_found",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="issues_unavailable",
        ) from exc
    return _to_response(issue, voting_cycle=None)


@archive_router.get(
    "/archive",
    response_model=ArchiveListResponse,
    summary="Past published issues",
    description=(
        "Returns past published issues excluding the current latest-published (D-31). "
        "Requires Bearer JWT. Empty archive → 200 with issues=[]."
    ),
)
def read_archive(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> ArchiveListResponse:
    del claims
    issues = _require_issues(request)
    try:
        archive = list_archive_issues(issues)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="issues_unavailable",
        ) from exc
    return ArchiveListResponse(
        issues=[
            ArchiveIssueResponse(
                number=issue.number,
                period_label=issue.period_label,
                title=issue.title,
                material_count=len(issue.items),
            )
            for issue in archive
        ]
    )
