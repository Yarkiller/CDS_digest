"""RED→GREEN: generate_slug and estimate_reading_minutes (D-12, D-13)."""

from __future__ import annotations

import ast
from pathlib import Path


VIDEO_ID = "dQw4w9WgXcQ"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _words(count: int) -> str:
    return " ".join(["слово"] * count)


def test_generate_slug_transliterates_title_and_appends_video_id() -> None:
    from ingestion_service.domain.material_completion import generate_slug

    assert (
        generate_slug("Как использовать pgvector", VIDEO_ID)
        == "kak-ispolzovat-pgvector-dQw4w9WgXcQ"
    )


def test_generate_slug_truncates_slugified_title_to_50_chars() -> None:
    from ingestion_service.domain.material_completion import generate_slug

    title = "Как использовать pgvector для семантического поиска по регламентам "
    title += "внутреннего аудита Сбербанка и смежных контуров"
    slug = generate_slug(title, VIDEO_ID)
    prefix, separator, suffix = slug.rpartition(f"-{VIDEO_ID}")
    assert separator == f"-{VIDEO_ID}"
    assert suffix == ""
    assert len(prefix) == 50


def test_estimate_reading_minutes_100_words_is_one() -> None:
    from ingestion_service.domain.material_completion import estimate_reading_minutes

    assert estimate_reading_minutes(_words(100)) == 1


def test_estimate_reading_minutes_400_words_is_two() -> None:
    from ingestion_service.domain.material_completion import estimate_reading_minutes

    assert estimate_reading_minutes(_words(400)) == 2


def test_material_completion_has_no_environ_access() -> None:
    path = (
        REPO_ROOT
        / "ingestion-service"
        / "src"
        / "ingestion_service"
        / "domain"
        / "material_completion.py"
    )
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "os" not in imported
    assert "os.environ" not in source
