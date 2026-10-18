"""PersistPort — application persist contract (D-01, D-03)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from data_collection.dto.material_draft import MaterialDraft


@dataclass(frozen=True)
class PersistResult:
    material_id: int
    slug: str
    batch_id: int
    rank: int
    already_saved: bool = False


@runtime_checkable
class PersistPort(Protocol):
    def persist(self, material_draft: MaterialDraft) -> PersistResult: ...
