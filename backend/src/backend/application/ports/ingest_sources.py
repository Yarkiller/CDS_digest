"""Ingest sources port — admin-managed channel/playlist list (SRC-01/SRC-03, D-18/D-21).

Protocol only: no SDK imports. Adapters live in tests_support (in-memory) and
supabase-integration (live); wiring is composition-only.
"""

from __future__ import annotations

from typing import Protocol

from backend.domain.ingest_source import IngestSource


class IngestSourceRepository(Protocol):
    def list(self) -> list[IngestSource]:
        """All sources, stable order: created_at ascending then id ascending."""
        ...

    def add(
        self,
        *,
        kind: str,
        source_id: str,
        label: str | None,
        is_enabled: bool = True,
    ) -> IngestSource:
        """Persist a new source and return the stored row (D-01 immediate)."""
        ...

    def set_enabled(self, source_id_pk: int, *, is_enabled: bool) -> IngestSource:
        """Toggle is_enabled for an existing row; raise if missing."""
        ...

    def delete(self, source_id_pk: int) -> None:
        """Hard-delete the row (D-10); raise if missing."""
        ...
