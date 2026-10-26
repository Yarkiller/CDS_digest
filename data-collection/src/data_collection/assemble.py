"""Pure assembler: ArticleDraft + VideoMetadata + provenance_label → MaterialDraft."""

from __future__ import annotations

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.material_draft import MaterialDraft
from data_collection.dto.video_metadata import VideoMetadata


def assemble_material_draft(
    article: ArticleDraft,
    metadata: VideoMetadata,
    provenance_label: str,
) -> MaterialDraft:
    return MaterialDraft(
        title=article.title,
        dek=article.dek,
        body_markdown=article.body_markdown,
        source_url=metadata.source_url,
        youtube_video_id=metadata.video_id,
        source_author=metadata.author,
        provenance_label=provenance_label,
        source_published_at=metadata.published_at,
        roles=article.roles,
    )


def require_material_draft(value: object) -> MaterialDraft:
    if not isinstance(value, MaterialDraft):
        raise TypeError("MaterialDraft required")
    return value
