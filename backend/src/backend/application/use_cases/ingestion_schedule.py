"""Ingestion schedule use cases — validate-then-persist (ING-06, D-14/D-16).

Reads current via repo.get(), merges only provided PATCH fields, validates before
any write. Empty patch → IngestionScheduleValidationError(path=body).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import time

from backend.application.ports.ingestion_schedule import IngestionScheduleRepository
from backend.domain.errors import IngestionScheduleValidationError
from backend.domain.ingestion_schedule import (
    MSG_NO_CHANGES,
    IngestionSchedule,
    normalize_days,
    parse_time_of_day,
)
from backend.domain.pipeline_config import PipelineConfigError


def get_ingestion_schedule(repo: IngestionScheduleRepository) -> IngestionSchedule:
    """Return current schedule (defaults when the singleton row is absent)."""
    return repo.get()


def update_ingestion_schedule(
    repo: IngestionScheduleRepository,
    *,
    enabled: bool | None = None,
    time_of_day: str | None = None,
    days_of_week: Sequence[int] | None = None,
) -> IngestionSchedule:
    """Merge PATCH fields onto current, validate, then persist the full set.

    Raises IngestionScheduleValidationError before any ``repo.update`` call.
    """
    if enabled is None and time_of_day is None and days_of_week is None:
        raise IngestionScheduleValidationError(
            (PipelineConfigError(path="body", message=MSG_NO_CHANGES),)
        )

    # Validate provided fields first — never touch the repo write path on reject.
    next_enabled = enabled
    next_time: time | None = None
    next_days: tuple[int, ...] | None = None
    if time_of_day is not None:
        next_time = parse_time_of_day(time_of_day)
    if days_of_week is not None:
        next_days = normalize_days(days_of_week)

    current = repo.get()
    return repo.update(
        enabled=current.enabled if next_enabled is None else next_enabled,
        time_of_day=current.time_of_day if next_time is None else next_time,
        days_of_week=current.days_of_week if next_days is None else next_days,
    )
