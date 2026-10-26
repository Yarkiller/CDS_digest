"""RED→GREEN: assemble_material_draft (D-07, D-08, D-13)."""


def test_assemble_material_draft_maps_fields_and_caller_provenance() -> None:
    from data_collection.assemble import assemble_material_draft
    from data_collection.dto.article_draft import ArticleDraft
    from data_collection.dto.video_metadata import VideoMetadata

    article = ArticleDraft(
        title="Prepared title",
        dek="Prepared dek",
        body_markdown="# Body",
    )
    metadata = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        author="Rick Astley",
        published_at=None,
    )
    label = "YouTube · Rick Astley · пер. с англ."

    draft = assemble_material_draft(article, metadata, label)

    assert draft.title == "Prepared title"
    assert draft.dek == "Prepared dek"
    assert draft.body_markdown == "# Body"
    assert draft.source_url == metadata.source_url
    assert draft.youtube_video_id == metadata.video_id
    assert draft.source_author == metadata.author
    assert draft.source_published_at is None
    assert draft.provenance_label == label
    assert draft.provenance_label != metadata.author


def test_assemble_material_draft_copies_article_roles() -> None:
    from data_collection.assemble import assemble_material_draft
    from data_collection.dto.article_draft import ArticleDraft
    from data_collection.dto.video_metadata import VideoMetadata

    article = ArticleDraft(
        title="Prepared title",
        dek="Prepared dek",
        body_markdown="# Body",
        roles=["analyst"],
    )
    metadata = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        author="Rick Astley",
        published_at=None,
    )

    draft = assemble_material_draft(article, metadata, "label")

    assert draft.roles == ["analyst"]
