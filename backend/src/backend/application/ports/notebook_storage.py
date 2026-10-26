"""NotebookStorage port — path-safe resolve under NOTEBOOK_ROOT (RAZB-03 / T-04-09)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class NotebookStorage(Protocol):
    def resolve(self, notebook_path: str) -> Path:
        """Resolve notebook_path under the configured root.

        Raises domain errors when the path escapes the root, is absolute,
        or the file does not exist. Never returns a path outside the root.
        """
        ...
