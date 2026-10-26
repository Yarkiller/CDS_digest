"""Local filesystem NotebookStorage — Path.resolve containment under NOTEBOOK_ROOT."""

from __future__ import annotations

from pathlib import Path

from backend.domain.errors import NotebookNotAvailableError, NotebookPathInvalidError


class LocalNotebookStorage:
    """Resolve relative notebook paths under a configured root (A5 / T-04-09)."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root).resolve()

    def resolve(self, notebook_path: str) -> Path:
        raw = (notebook_path or "").strip()
        if not raw:
            raise NotebookPathInvalidError(raw)
        relative = Path(raw)
        if relative.is_absolute():
            raise NotebookPathInvalidError(raw)
        if ".." in relative.parts:
            raise NotebookPathInvalidError(raw)

        candidate = (self._root / relative).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise NotebookPathInvalidError(raw) from exc

        if not candidate.is_file():
            raise NotebookNotAvailableError(path=raw)
        return candidate
