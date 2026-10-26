"""persist_draft — enrich MaterialDraft and call PersistPort (D-07, D-11)."""

from __future__ import annotations

from data_collection.dto.material_draft import MaterialDraft
from ingestion_service.application.ports.persist import PersistPort, PersistResult
from ingestion_service.domain.material_completion import (
    estimate_reading_minutes,
    generate_slug,
)


def persist_draft(material_draft: MaterialDraft, port: PersistPort) -> PersistResult:
    enriched = material_draft.model_copy(
        update={
            "slug": generate_slug(
                material_draft.title, material_draft.youtube_video_id
            ),
            "reading_minutes": estimate_reading_minutes(
                material_draft.body_markdown
            ),
        }
    )
    return port.persist(enriched)
