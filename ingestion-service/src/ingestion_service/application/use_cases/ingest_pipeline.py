"""run_ingest_pipeline — URL → captions → metadata → LLM → persist (CLI-01)."""

from __future__ import annotations

from collections.abc import Callable

from data_collection.assemble import assemble_material_draft
from data_collection.dto.template_kind import TemplateKind
from data_collection.errors.article import ArticleError
from data_collection.errors.captions import CaptionsError
from data_collection.errors.metadata import MetadataError
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider
from data_collection.ports.video_metadata_provider import VideoMetadataProvider
from ingestion_service.adapters.persist_errors import DraftPersistError
from ingestion_service.application.ports.diagnostics import StageDiagnostics
from ingestion_service.application.ports.persist import PersistPort, PersistResult
from ingestion_service.application.use_cases.persist_draft import persist_draft
from ingestion_service.mapping.article import map_article_error
from ingestion_service.mapping.captions import map_captions_error
from ingestion_service.mapping.metadata import map_metadata_error
from ingestion_service.mapping.persist import map_persist_error
from ingestion_service.domain.errors import IngestError
from ingestion_service.mapping.url import map_url_error
from ingestion_service.provenance import ENGLISH_TRANSLATION_SUFFIX
from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

OnStage = Callable[[str], None]


async def run_ingest_pipeline(
    url: str,
    template: TemplateKind,
    *,
    captions: TranscriptProvider,
    metadata_provider: VideoMetadataProvider,
    article: ArticleGenerator,
    persist: PersistPort,
    on_stage: OnStage | None = None,
    diagnostics: StageDiagnostics | None = None,
) -> PersistResult:
    try:
        video_id = extract_video_id(url)
    except InvalidYouTubeUrl as err:
        mapped = map_url_error(err)
        if diagnostics is not None:
            diagnostics.stage_failed(
                mapped.stage, reason=mapped.reason, exit_code=mapped.exit_code
            )
        raise mapped from err

    if diagnostics is not None:
        diagnostics.stage_started("captions")
    try:
        transcript = await captions.get(video_id)
    except CaptionsError as err:
        mapped = map_captions_error(err)
        if diagnostics is not None:
            diagnostics.stage_failed(
                mapped.stage, reason=mapped.reason, exit_code=mapped.exit_code
            )
        raise mapped from err
    if diagnostics is not None:
        diagnostics.stage_completed(
            "captions",
            {
                "video_id": transcript.video_id,
                "transcript_chars": len(transcript.text),
                "transcript_words": len(transcript.text.split()),
                "language": transcript.language,
            },
        )
    if on_stage is not None:
        on_stage("transcript")

    if diagnostics is not None:
        diagnostics.stage_started("metadata")
    try:
        metadata = await metadata_provider.get(video_id)
    except MetadataError as err:
        mapped = map_metadata_error(err)
        if diagnostics is not None:
            diagnostics.stage_failed(
                mapped.stage, reason=mapped.reason, exit_code=mapped.exit_code
            )
        raise mapped from err
    if diagnostics is not None:
        diagnostics.stage_completed("metadata", {"video_id": metadata.video_id})

    # CONSISTENCY-01: fail closed before LLM when DTO video ids diverge.
    if transcript.video_id != metadata.video_id:
        consistency_error = IngestError(
            stage="consistency",
            reason="video_id_mismatch",
            message="transcript and metadata video_id mismatch",
            context={
                "transcript_video_id": transcript.video_id,
                "metadata_video_id": metadata.video_id,
            },
        )
        if diagnostics is not None:
            diagnostics.stage_failed(
                consistency_error.stage,
                reason=consistency_error.reason,
                exit_code=consistency_error.exit_code,
            )
        raise consistency_error

    provenance = f"YouTube · {metadata.author}"
    if transcript.language != "ru":
        provenance = f"{provenance}{ENGLISH_TRANSLATION_SUFFIX}"

    if diagnostics is not None:
        diagnostics.stage_started("llm")
    try:
        article_draft = await article.process(transcript, template)
    except ArticleError as err:
        mapped = map_article_error(err)
        if diagnostics is not None:
            diagnostics.stage_failed(
                mapped.stage, reason=mapped.reason, exit_code=mapped.exit_code
            )
        raise mapped from err
    if diagnostics is not None:
        diagnostics.stage_completed(
            "llm",
            {
                "template": template.value,
                "response_chars": len(article_draft.body_markdown),
            },
        )
    if on_stage is not None:
        on_stage("llm")

    material = assemble_material_draft(article_draft, metadata, provenance)
    if diagnostics is not None:
        diagnostics.stage_started("persist")
    try:
        result = persist_draft(material, persist)
    except DraftPersistError as err:
        mapped = map_persist_error(err)
        if diagnostics is not None:
            diagnostics.stage_failed(
                mapped.stage, reason=mapped.reason, exit_code=mapped.exit_code
            )
        raise mapped from err
    if diagnostics is not None:
        diagnostics.stage_completed(
            "persist",
            {
                "material_id": result.material_id,
                "slug": result.slug,
                "batch_id": result.batch_id,
                "rank": result.rank,
                "already_saved": result.already_saved,
            },
        )
    if on_stage is not None:
        on_stage("saved")
    return result
