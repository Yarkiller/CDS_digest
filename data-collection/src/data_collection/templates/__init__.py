"""Repository markdown templates for lecture and podcast prompts (D-16, D-17)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from importlib.resources.abc import Traversable

from data_collection.dto.template_kind import TemplateKind


class TemplateLoadError(Exception):
    """Missing or unreadable template markdown at startup (D-17)."""

    def __init__(self, kind_value: str) -> None:
        self.kind_value = kind_value
        super().__init__(f"could not load template for {kind_value}")


def load_article_templates(root: Traversable) -> dict[TemplateKind, str]:
    """Load template markdown for every TemplateKind from *root*.

    Production root is ``importlib.resources.files("data_collection.templates")``.
    """
    loaded: dict[TemplateKind, str] = {}
    for kind in TemplateKind:
        path = root.joinpath(f"{kind.value}.md")
        if not path.is_file():
            raise TemplateLoadError(kind.value)
        try:
            loaded[kind] = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise TemplateLoadError(kind.value) from exc
    return loaded
