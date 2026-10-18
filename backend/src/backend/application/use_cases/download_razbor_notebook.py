"""Download razbor notebook — path-safe FileResponse source (RAZB-03 / D-70)."""

from __future__ import annotations

from pathlib import Path

from backend.application.ports.notebook_storage import NotebookStorage
from backend.application.ports.razbor_repository import RazborRepository
from backend.domain.errors import NotebookNotAvailableError, RazborNotFoundError


def download_razbor_notebook(
    repo: RazborRepository,
    storage: NotebookStorage,
    razbor_id: int,
) -> Path:
    """Return a contained Path for the razbor's notebook, or raise domain errors."""
    razbor = repo.get(razbor_id)
    if razbor is None:
        raise RazborNotFoundError(razbor_id)
    if not razbor.notebook_path or not razbor.notebook_path.strip():
        raise NotebookNotAvailableError(razbor_id=razbor_id)
    return storage.resolve(razbor.notebook_path)
