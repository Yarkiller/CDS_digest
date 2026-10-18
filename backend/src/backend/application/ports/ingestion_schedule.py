"""Ingestion schedule port — singleton auto-collect settings (ING-06, D-14).

Protocol only: no SDK imports. Missing row → domain defaults on get(); first
update inserts id=1 (upsert). Adapters: tests_support in-memory + supabase-integration.
Wiring is composition-only.
"""

from __future__ import annotations

from datetime import time
from typing import Protocol

from backend.domain.ingestion_schedule import IngestionSchedule


class IngestionScheduleRepository(Protocol):
    def get(self) -> IngestionSchedule:
        """Current schedule, or domain defaults when the singleton row is absent (D-14)."""
        ...

    def update(
        self,
        *,
        enabled: bool,
        time_of_day: time,
        days_of_week: tuple[int, ...],
    ) -> IngestionSchedule:
        """Upsert the full schedule (id=1) and return the stored row (D-16)."""
        ...
