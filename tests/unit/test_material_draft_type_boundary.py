"""RED→GREEN: Transcript ≠ MaterialDraft boundary (SC-3, D-CONTENT-01)."""

import pytest


def test_require_material_draft_rejects_transcript() -> None:
    from data_collection.assemble import require_material_draft
    from data_collection.dto.transcript import Transcript

    transcript = Transcript(text="hello", language="en", video_id="abc")
    with pytest.raises(TypeError):
        require_material_draft(transcript)


def test_require_material_draft_returns_valid_draft() -> None:
    from data_collection.assemble import require_material_draft
    from data_collection.dto.material_draft import MaterialDraft

    draft = MaterialDraft(
        title="Title",
        dek="Dek",
        body_markdown="# Body",
        source_url="https://example.com",
        youtube_video_id="abc",
        source_author="Author",
        provenance_label="YouTube · Author",
    )
    assert require_material_draft(draft) is draft
