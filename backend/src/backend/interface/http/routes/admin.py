"""Admin shortlist endpoints — GET/decision/preview/send behind require_admin (ADMIN-01…08)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.application.use_cases.get_admin_shortlist import get_admin_shortlist
from backend.application.use_cases.get_material_for_preview import get_material_for_preview
from backend.application.use_cases.mark_material_ready import (
    mark_material_ready,
    mark_materials_ready,
)
from backend.application.use_cases.ingest_sources import (
    add_ingest_source,
    list_ingest_sources,
)
from backend.application.use_cases.pipeline_config import (
    get_pipeline_config,
    save_pipeline_config,
)
from backend.application.use_cases.preview_digest_email import (
    PreviewMaterialBlock,
    PreviewTextBlock,
    preview_digest_email,
)
from backend.application.use_cases.send_digest import send_digest
from backend.application.use_cases.set_shortlist_decision import set_shortlist_decision
from backend.domain.current_user import CurrentUser
from backend.domain.errors import (
    AlreadySentError,
    DraftInSendPoolError,
    EmptySendPoolError,
    IngestSourceValidationError,
    InvalidPreviewCompositionError,
    InvalidSendOrderError,
    InvalidShortlistDecisionError,
    MaterialNotFoundError,
    PersistenceError,
    PipelineConfigValidationError,
    ShortlistNotFoundError,
)
from backend.domain.ingest_source import IngestSource
from backend.domain.material import Material
from backend.domain.shortlist import AdminShortlist
from backend.interface.http.deps import require_admin
from backend.interface.http.routes.materials import MaterialReaderResponse, _SLUG_PATTERN

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminShortlistItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: int
    rank: int
    title: str
    material_status: str
    decision: str
    score: float | None = None
    factor_labels: list[str] = []
    dek: str | None = None
    body_markdown: str | None = None
    provenance_label: str | None = None
    slug: str | None = None
    reading_minutes: int | None = None
    char_count: int = 0
    word_count: int = 0


class AdminShortlistResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int | None = None
    items: list[AdminShortlistItemResponse] = []
    digest_rest: bool = False
    days_until_next_batch: int | None = None
    week_label: str | None = None
    sent_at: datetime | None = None


class SetShortlistDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(
        ...,
        min_length=1,
        description="shortlist_decision: pending|approved|rejected (D-82; allowlist in use-case)",
    )


class DigestPreviewItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: int
    rank: int
    title: str


class DigestPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int
    subject: str
    body: str
    html: str
    items: list[DigestPreviewItemResponse] = []


class DigestPreviewMaterialBlockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(..., pattern="^material$")
    material_id: int


class DigestPreviewTextBlockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(..., pattern="^text$")
    text: str


class DigestPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intro: str = ""
    blocks: list[DigestPreviewMaterialBlockRequest | DigestPreviewTextBlockRequest] | None = None


class SendDigestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_ids: list[int] | None = None
    intro: str = ""
    blocks: list[DigestPreviewMaterialBlockRequest | DigestPreviewTextBlockRequest] | None = None


class SendDigestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: int
    issue_number: int
    issue_url: str
    delivery_status: str
    recipient_count: int = 0
    delivered_count: int = 0
    message: str


class MarkReadyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: int
    status: str


class MarkReadyBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_ids: list[int]


class MarkReadyBatchItemResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: int
    ok: bool
    status: str | None = None
    error: str | None = None


class MarkReadyBatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[MarkReadyBatchItemResult]


class PipelineConfigSaveRequest(BaseModel):
    """PUT /admin/pipeline/config body — the raw YAML document only (D-11, D-13)."""

    model_config = ConfigDict(extra="forbid")

    yaml: str


class PipelineConfigResponse(BaseModel):
    """Read DTO {yaml, updated_at} — no version, no secret/credential key (D-11; PIPE-03)."""

    model_config = ConfigDict(extra="forbid")

    yaml: str
    updated_at: datetime | None = None


class IngestSourceCreateRequest(BaseModel):
    """POST /admin/ingest-sources body (D-18; extra=forbid → 422)."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    source_id: str
    label: str | None = None


class IngestSourceResponse(BaseModel):
    """One ingest-source row DTO (D-08 / D-18)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    kind: str
    source_id: str
    label: str | None = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class IngestSourcesListResponse(BaseModel):
    """GET /admin/ingest-sources envelope — exactly {sources:[…]} (D-18)."""

    model_config = ConfigDict(extra="forbid")

    sources: list[IngestSourceResponse]


def _ingest_source_to_response(row: IngestSource) -> IngestSourceResponse:
    return IngestSourceResponse(
        id=row.id,
        kind=row.kind,
        source_id=row.source_id,
        label=row.label,
        is_enabled=row.is_enabled,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _require_shortlist(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "shortlist", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="shortlist_not_configured",
        )
    return container.shortlist


def _require_pipeline_config(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "pipeline_config", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pipeline_config_not_configured",
        )
    return container.pipeline_config


def _require_ingest_sources(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "ingest_sources", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ingest_sources_not_configured",
        )
    return container.ingest_sources


def _require_container(request: Request):
    container = request.app.state.container
    if container is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="container_not_configured",
        )
    return container


def _require_materials(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "materials", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="materials_not_configured",
        )
    return container.materials


def _to_preview_blocks(
    blocks: list[DigestPreviewMaterialBlockRequest | DigestPreviewTextBlockRequest] | None,
) -> list[PreviewMaterialBlock | PreviewTextBlock] | None:
    if blocks is None:
        return None
    uc_blocks: list[PreviewMaterialBlock | PreviewTextBlock] = []
    for block in blocks:
        if isinstance(block, DigestPreviewMaterialBlockRequest):
            uc_blocks.append(PreviewMaterialBlock(material_id=block.material_id))
        else:
            uc_blocks.append(PreviewTextBlock(text=block.text))
    return uc_blocks


def _to_response(dto: AdminShortlist) -> AdminShortlistResponse:
    return AdminShortlistResponse(
        batch_id=dto.batch_id,
        items=[
            AdminShortlistItemResponse(
                material_id=item.material_id,
                rank=item.rank,
                title=item.title,
                material_status=item.material_status,
                decision=item.decision,
                score=item.score,
                factor_labels=list(item.factor_labels),
                dek=item.dek,
                body_markdown=item.body_markdown,
                provenance_label=item.provenance_label,
                slug=item.slug,
                reading_minutes=item.reading_minutes,
                char_count=item.char_count,
                word_count=item.word_count,
            )
            for item in dto.items
        ],
        digest_rest=dto.digest_rest,
        days_until_next_batch=dto.days_until_next_batch,
        week_label=dto.week_label,
        sent_at=dto.sent_at,
    )


def _to_preview_response(material: Material) -> MaterialReaderResponse:
    """Build the preview payload from the reader DTO (D-02).

    D-08: `tags`/`related` ship empty so no unpublished taxonomy or neighbour leaks —
    deliberately omitted, not filtered (the reader's `_related_ready` stays the reader's).
    `editor` is left to the DTO default so the payload stays byte-shaped like the reader's.
    """
    return MaterialReaderResponse(
        slug=material.slug,
        title=material.title,
        dek=material.dek,
        body_markdown=material.body_markdown,
        format=material.format,
        provenance=material.provenance_label,
        tags=[],
        related=[],
        reading_minutes=material.reading_minutes,
        published_at=material.published_at,
    )


@router.post(
    "/materials/ready",
    response_model=MarkReadyBatchResponse,
    summary="Batch promote materials draft→ready (partial success)",
    description=(
        "One-call batch ready with per-id results (ADUX-05; D-08). "
        "HTTP 200 even when some ids are missing — never 207; never abort the batch. "
        "Requires admin. Unknown JSON fields → 422 (extra=forbid)."
    ),
)
def post_materials_ready_batch(
    body: MarkReadyBatchRequest,
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> MarkReadyBatchResponse:
    # Missing materials repo → 503 via _require_materials. Per-id PersistenceError
    # is mapped inside mark_materials_ready (WR-01 / D-08 — never abort batch → 200).
    materials = _require_materials(request)
    items = mark_materials_ready(materials, body.material_ids)
    return MarkReadyBatchResponse(
        results=[
            MarkReadyBatchItemResult(
                material_id=item.material_id,
                ok=item.ok,
                status=item.status,
                error=item.error,
            )
            for item in items
        ]
    )


@router.post(
    "/materials/{material_id}/ready",
    response_model=MarkReadyResponse,
    summary="Promote one material draft→ready (status-only)",
    description=(
        "Triage ready without publish gate or published_at (ADUX-05; D-06, D-07, D-09, D-10). "
        "Missing material → 404 material_not_found. Already-ready → 200 no-op. Requires admin."
    ),
)
def post_material_ready(
    material_id: int,
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> MarkReadyResponse:
    materials = _require_materials(request)
    try:
        material = mark_material_ready(materials, material_id)
    except MaterialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="material_not_found",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="materials_unavailable",
        ) from exc
    return MarkReadyResponse(material_id=material.id, status=material.status.value)


@router.get(
    "/materials/{slug}",
    response_model=MaterialReaderResponse,
    summary="Draft material preview for admins",
    description=(
        "Admin-gated preview of a draft material in the reader DTO shape (D-01/D-02, ADUX-07). "
        "Draft only — every other status (unknown or ready) answers 404 material_not_found, so "
        "403 comes only from the role gate and never becomes a slug-existence oracle (D-03/D-04/"
        "D-12). Requires profiles.role=admin. Response is served non-cacheable (D-07)."
    ),
)
def read_material_preview(
    request: Request,
    response: Response,
    slug: str = Path(..., pattern=_SLUG_PATTERN),
    _admin: CurrentUser = Depends(require_admin),
) -> MaterialReaderResponse:
    materials = _require_materials(request)
    try:
        material = get_material_for_preview(materials, slug)
    except MaterialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="material_not_found",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="materials_unavailable",
        ) from exc
    response.headers["Cache-Control"] = "no-store"  # D-07
    return _to_preview_response(material)


@router.get(
    "/shortlist",
    response_model=AdminShortlistResponse,
    summary="Current admin shortlist batch",
    description=(
        "Returns ≤5 ranked shortlist candidates for the current unsent batch "
        "(ADMIN-01, D-81). Requires profiles.role=admin (D-74). "
        "Empty batch → items=[] (D-80). PersistenceError → 503 shortlist_unavailable."
    ),
)
def read_admin_shortlist(
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> AdminShortlistResponse:
    shortlist = _require_shortlist(request)
    try:
        dto = get_admin_shortlist(shortlist)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="shortlist_unavailable",
        ) from exc
    return _to_response(dto)


@router.post(
    "/shortlist/items/{material_id}/decision",
    response_model=AdminShortlistResponse,
    summary="Set shortlist decision for one material",
    description=(
        "Persists shortlist_decision pending|approved|rejected (ADMIN-02, D-82). "
        "Approve allowed on draft (D-85). Actor is authenticated admin id (T-05-07). "
        "Unknown material → 404; invalid body → 400; PersistenceError → 503."
    ),
)
def post_shortlist_decision(
    material_id: int,
    body: SetShortlistDecisionRequest,
    request: Request,
    admin: CurrentUser = Depends(require_admin),
) -> AdminShortlistResponse:
    shortlist = _require_shortlist(request)
    try:
        dto = set_shortlist_decision(
            shortlist,
            material_id=material_id,
            decision=body.decision,
            actor_user_id=admin.id,
        )
    except InvalidShortlistDecisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_decision",
        ) from exc
    except ShortlistNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="shortlist_item_not_found",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="shortlist_unavailable",
        ) from exc
    return _to_response(dto)


@router.post(
    "/shortlist/preview",
    response_model=DigestPreviewResponse,
    summary="Preview digest email for approved∩ready pool",
    description=(
        "Returns subject/body/items for approved ready materials only (ADMIN-04, D-86, G-05-1). "
        "Optional intro + ordered blocks compose the body. Never marks batch sent. "
        "Empty pool → 400; invalid composition → 400. Requires admin."
    ),
)
def post_shortlist_preview(
    request: Request,
    body: DigestPreviewRequest | None = None,
    _admin: CurrentUser = Depends(require_admin),
) -> DigestPreviewResponse:
    shortlist = _require_shortlist(request)
    payload = body or DigestPreviewRequest()
    uc_blocks = _to_preview_blocks(payload.blocks)
    settings = getattr(request.app.state, "settings", None)
    site_url = getattr(settings, "site_url", None) or "http://127.0.0.1:5173"
    try:
        preview = preview_digest_email(
            shortlist,
            intro=payload.intro,
            blocks=uc_blocks,
            site_url=site_url,
        )
    except EmptySendPoolError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="empty_send_pool",
        ) from exc
    except InvalidPreviewCompositionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_preview_composition",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="shortlist_unavailable",
        ) from exc
    return DigestPreviewResponse(
        batch_id=preview.batch_id,
        subject=preview.subject,
        body=preview.body,
        html=preview.html,
        items=[
            DigestPreviewItemResponse(
                material_id=item.material_id,
                rank=item.rank,
                title=item.title,
            )
            for item in preview.items
        ],
    )


@router.post(
    "/shortlist/send",
    response_model=SendDigestResponse,
    summary="Send digest: claim, publish issue, deliver mail",
    description=(
        "Publish-on-send (D-88): claim batch, publish digest_issues, then best-effort mail "
        "(StubMailer by default, live SMTP when MAILER=smtp). Draft in pool → 400; empty → 400; "
        "already sent → 409. Success is HTTP 200 with honest planned M (recipient_count), "
        "delivered N (delivered_count), and a two-sentence message (D-09/D-10/D-12); a "
        "contained mail partial/fail after publish never becomes 5xx (D-11)."
    ),
)
def post_shortlist_send(
    request: Request,
    body: SendDigestRequest | None = None,
    admin: CurrentUser = Depends(require_admin),
) -> SendDigestResponse:
    container = _require_container(request)
    shortlist = _require_shortlist(request)
    payload = body or SendDigestRequest()
    settings = getattr(request.app.state, "settings", None)
    site_url = getattr(settings, "site_url", None) or "http://127.0.0.1:5173"
    try:
        result = send_digest(
            shortlist,
            container.publisher,
            container.mailer,
            container.pings,
            container.profiles,
            actor_user_id=admin.id,
            material_ids=payload.material_ids,
            intro=payload.intro,
            blocks=_to_preview_blocks(payload.blocks),
            site_url=site_url,
        )
    except DraftInSendPoolError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "draft_in_send_pool",
                "draft_material_ids": exc.draft_material_ids,
            },
        ) from exc
    except InvalidSendOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_send_order",
        ) from exc
    except EmptySendPoolError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="empty_send_pool",
        ) from exc
    except AlreadySentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="already_sent",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="shortlist_unavailable",
        ) from exc
    return SendDigestResponse(
        batch_id=result.batch_id,
        issue_number=result.issue_number,
        issue_url=result.issue_url,
        delivery_status=result.delivery_status,
        recipient_count=result.recipient_count,
        delivered_count=result.delivered_count,
        message=result.message,
    )


@router.get(
    "/pipeline/config",
    response_model=PipelineConfigResponse,
    summary="Read the saved pipeline config",
    description=(
        "Returns the current raw-YAML pipeline config as {yaml, updated_at} (PIPE-01/PIPE-03, "
        "D-11). An absent singleton row returns the empty state {yaml:'', updated_at:null}. "
        "Requires profiles.role=admin (D-10). PersistenceError → 503 pipeline_config_unavailable."
    ),
)
def read_pipeline_config(
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> PipelineConfigResponse:
    repo = _require_pipeline_config(request)
    try:
        config = get_pipeline_config(repo)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pipeline_config_unavailable",
        ) from exc
    if config is None:
        return PipelineConfigResponse(yaml="", updated_at=None)
    return PipelineConfigResponse(yaml=config.yaml, updated_at=config.updated_at)


@router.put(
    "/pipeline/config",
    response_model=PipelineConfigResponse,
    summary="Save the pipeline config (server-authoritative, no execution)",
    description=(
        "Validates then persists the raw-YAML pipeline config and returns the saved "
        "{yaml, updated_at} (PIPE-01/PIPE-03, D-08/D-11). Requires admin (D-10). "
        "Unknown JSON fields → 422 (extra=forbid). This surface never triggers a pipeline run."
    ),
)
def put_pipeline_config(
    body: PipelineConfigSaveRequest,
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> PipelineConfigResponse:
    repo = _require_pipeline_config(request)
    validator = getattr(request.app.state.container, "pipeline_config_validator", None)
    if validator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pipeline_config_not_configured",
        )
    try:
        config = save_pipeline_config(repo, validator, yaml_text=body.yaml)
    except PipelineConfigValidationError as exc:
        # D-05 / RESEARCH Pitfall 2: top-level {"errors":[...]}, never nested under detail.
        # Repository is not called on reject (D-03/D-07) — zero writes.
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"errors": [error.to_dict() for error in exc.errors]},
        )
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pipeline_config_unavailable",
        ) from exc
    return PipelineConfigResponse(yaml=config.yaml, updated_at=config.updated_at)


@router.get(
    "/ingest-sources",
    response_model=IngestSourcesListResponse,
    summary="List admin-managed ingest sources",
    description=(
        "Returns {sources:[…]} for the admin-managed channel/playlist list (SRC-01, D-18). "
        "Requires profiles.role=admin. Missing repo → 503 ingest_sources_not_configured."
    ),
)
def get_ingest_sources(
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> IngestSourcesListResponse:
    repo = _require_ingest_sources(request)
    try:
        rows = list_ingest_sources(repo)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ingest_sources_unavailable",
        ) from exc
    return IngestSourcesListResponse(
        sources=[_ingest_source_to_response(row) for row in rows],
    )


@router.post(
    "/ingest-sources",
    response_model=IngestSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an ingest source (immediate persist)",
    description=(
        "Validates then persists a channel/playlist source and returns the created row "
        "(SRC-01, D-01/D-14/D-18). Requires admin. Validation rejects → top-level "
        "{errors:[…]} 400 (never under detail). Unknown JSON fields → 422."
    ),
)
def post_ingest_source(
    body: IngestSourceCreateRequest,
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> IngestSourceResponse | JSONResponse:
    repo = _require_ingest_sources(request)
    try:
        row = add_ingest_source(
            repo,
            kind=body.kind,
            source_id=body.source_id,
            label=body.label,
        )
    except IngestSourceValidationError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"errors": [error.to_dict() for error in exc.errors]},
        )
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ingest_sources_unavailable",
        ) from exc
    return _ingest_source_to_response(row)
