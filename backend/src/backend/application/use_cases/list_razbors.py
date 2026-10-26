"""List razbors for reader chronology — ordering lives in repository (RAZB-01)."""

from __future__ import annotations

from backend.application.ports.razbor_repository import RazborRepository
from backend.domain.razbor import Razbor


def list_razbors(razbors: RazborRepository) -> list[Razbor]:
    """Return reader-visible razbors in repository order."""
    return razbors.list_for_reader()
