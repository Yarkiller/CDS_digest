"""RED→GREEN: MaterialDraft.roles closed set + fallback (PERS-01, D-14)."""

from __future__ import annotations


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "title": "t",
        "dek": "d",
        "body_markdown": "b",
        "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube_video_id": "dQw4w9WgXcQ",
        "source_author": "Author",
        "provenance_label": "YouTube · Author",
    }
    base.update(overrides)
    return base


def test_material_draft_keeps_valid_roles() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    draft = MaterialDraft.model_validate(
        _valid_kwargs(roles=["employee", "analyst"])
    )
    assert draft.roles == ["employee", "analyst"]


def test_material_draft_filters_unknown_roles() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    draft = MaterialDraft.model_validate(_valid_kwargs(roles=["manager", "employee"]))
    assert draft.roles == ["employee"]


def test_material_draft_missing_roles_falls_back_to_employee() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    draft = MaterialDraft.model_validate(_valid_kwargs())
    assert draft.roles == ["employee"]


def test_material_draft_empty_roles_falls_back_to_employee() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    draft = MaterialDraft.model_validate(_valid_kwargs(roles=[]))
    assert draft.roles == ["employee"]


def test_material_draft_constructor_normalization() -> None:
    from data_collection.dto.material_draft import MaterialDraft

    assert MaterialDraft(
        **_valid_kwargs(roles=["employee", "analyst"])
    ).roles == ["employee", "analyst"]
    assert MaterialDraft(
        **_valid_kwargs(roles=["manager", "employee"])
    ).roles == ["employee"]
    assert MaterialDraft(**_valid_kwargs()).roles == ["employee"]
