"""Authenticated voting ballot endpoints — GET /voting/current, POST /voting/votes (D-40, D-52)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from backend.application.use_cases.cast_vote import cast_vote
from backend.application.use_cases.get_ballot import get_ballot
from backend.domain.auth_claims import AccessTokenClaims
from backend.domain.errors import (
    InvalidVoteError,
    PersistenceError,
    VoteConflictError,
    VotingCycleClosedError,
)
from backend.domain.vote import BallotSnapshot
from backend.interface.http.deps import get_principal

router = APIRouter(prefix="/voting", tags=["voting"])


class BallotCycleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: str
    opens_at: datetime
    closes_at: datetime
    progress_ratio: float


class BallotTopicResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    materials_count: int
    votes: int


class PersonalVoteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: str
    updated_at: datetime


class BallotLeaderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    votes: int


class BallotSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cycle: BallotCycleResponse | None = None
    topics: list[BallotTopicResponse] = []
    personal_vote: PersonalVoteResponse | None = None
    leaders: list[BallotLeaderResponse] = []


class CastVoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: str
    expected_updated_at: str | None = None


def _to_response(snapshot: BallotSnapshot) -> BallotSnapshotResponse:
    cycle = None
    if snapshot.cycle is not None:
        cycle = BallotCycleResponse(
            id=snapshot.cycle.id,
            status=snapshot.cycle.status,
            opens_at=snapshot.cycle.opens_at,
            closes_at=snapshot.cycle.closes_at,
            progress_ratio=snapshot.cycle.progress_ratio,
        )
    personal = None
    if snapshot.personal_vote is not None:
        personal = PersonalVoteResponse(
            topic_id=snapshot.personal_vote.topic_id,
            updated_at=snapshot.personal_vote.updated_at,
        )
    return BallotSnapshotResponse(
        cycle=cycle,
        topics=[
            BallotTopicResponse(
                id=t.id,
                title=t.title,
                description=t.description,
                materials_count=t.materials_count,
                votes=t.votes,
            )
            for t in snapshot.topics
        ],
        personal_vote=personal,
        leaders=[
            BallotLeaderResponse(title=leader.title, votes=leader.votes)
            for leader in snapshot.leaders
        ],
    )


def _require_votes(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "votes", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="votes_not_configured",
        )
    return container.votes


def _require_voting_cycles(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "voting_cycles", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="voting_cycles_not_configured",
        )
    return container.voting_cycles


@router.get(
    "/current",
    response_model=BallotSnapshotResponse,
    summary="Current ballot snapshot",
    description=(
        "Returns BallotSnapshot for the active voting cycle (VOTE-02). "
        "Requires Bearer JWT. user_id is claims.sub only (ASVS V4 / T-03-01). "
        "PersistenceError → 503 voting_unavailable."
    ),
)
def read_current_ballot(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> BallotSnapshotResponse:
    votes = _require_votes(request)
    cycles = _require_voting_cycles(request)
    try:
        snapshot = get_ballot(votes, cycles, claims.sub)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="voting_unavailable",
        ) from exc
    return _to_response(snapshot)


def _conflict_detail(
    *,
    code: str,
    message: str,
    ballot: BallotSnapshot | None,
) -> dict:
    ballot_payload = (
        _to_response(ballot).model_dump(mode="json") if ballot is not None else None
    )
    return {"code": code, "message": message, "ballot": ballot_payload}


@router.post(
    "/votes",
    response_model=BallotSnapshotResponse,
    summary="Cast or confirm vote",
    description=(
        "Upserts exactly one vote for claims.sub on the open cycle (VOTE-01/03, D-52). "
        "Returns full BallotSnapshot. Same-topic repeat is idempotent 200. "
        "Closed cycle → 409 CYCLE_CLOSED + ballot; CAS mismatch → 409 VOTE_CONFLICT + ballot. "
        "PersistenceError → 503 voting_unavailable."
    ),
)
def post_vote(
    body: CastVoteRequest,
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> BallotSnapshotResponse:
    votes = _require_votes(request)
    cycles = _require_voting_cycles(request)
    try:
        snapshot = cast_vote(
            votes,
            cycles,
            user_id=claims.sub,
            topic_id=body.topic_id,
            expected_updated_at=body.expected_updated_at,
        )
    except InvalidVoteError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_vote",
        ) from exc
    except VotingCycleClosedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_conflict_detail(
                code="CYCLE_CLOSED",
                message="Цикл голосования закрыт",
                ballot=exc.ballot if isinstance(exc.ballot, BallotSnapshot) else None,
            ),
        ) from exc
    except VoteConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_conflict_detail(
                code="VOTE_CONFLICT",
                message="Голос уже изменён на другом устройстве",
                ballot=exc.ballot if isinstance(exc.ballot, BallotSnapshot) else None,
            ),
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="voting_unavailable",
        ) from exc
    return _to_response(snapshot)
