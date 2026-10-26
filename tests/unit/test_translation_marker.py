"""RED→GREEN: English translation suffix constant is locked (D-05, D-06)."""

from __future__ import annotations

from pathlib import Path


def test_english_translation_suffix_is_exact_string() -> None:
    from ingestion_service.provenance import ENGLISH_TRANSLATION_SUFFIX

    assert ENGLISH_TRANSLATION_SUFFIX == " · пер. с англ."


def test_suffix_is_absent_from_adapter_source() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    adapter_path = repo_root / "data-collection" / "src" / "data_collection" / "adapters" / "deepseek_article.py"
    body = adapter_path.read_text(encoding="utf-8")
    assert " · пер. с англ." not in body
    assert "provenance_label" not in body


def test_provenance_module_has_no_label_builder() -> None:
    from ingestion_service import provenance

    assert not hasattr(provenance, "build_provenance_label")
    source = Path(provenance.__file__).read_text(encoding="utf-8")
    assert "metadata.author" not in source
