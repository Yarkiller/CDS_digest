"""run_ingest_until_persist — captions → article → assemble → persist (CAP-02)."""

from __future__ import annotations

from data_collection.assemble import assemble_material_draft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider
from ingestion_service.application.ports.persist import PersistPort, PersistResult
from ingestion_service.application.use_cases.persist_draft import persist_draft


async def run_ingest_until_persist(
    video_id: str,
    captions: TranscriptProvider,
    article: ArticleGenerator,
    persist: PersistPort,
    metadata: VideoMetadata,
    *,
    template_kind: TemplateKind = TemplateKind.LECTURE,
) -> PersistResult:
    transcript = await captions.get(video_id)
    article_draft = await article.process(transcript, template_kind)
    material = assemble_material_draft(
        article_draft,
        metadata,
        f"YouTube · {metadata.author}",
    )
    return persist_draft(material, persist)
