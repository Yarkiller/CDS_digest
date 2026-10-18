"""Ingestion schedule domain — singleton settings for auto-collect (ING-06, D-14/D-16).

Pure value object + normalizers. No fastapi/supabase/httpx imports.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, time

from backend.domain.errors import IngestionScheduleValidationError
from backend.domain.pipeline_config import PipelineConfigError

DEFAULT_TIME_OF_DAY = time(6, 0)
ALL_WEEKDAYS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7)

MSG_TIME_OF_DAY = "Укажите время в формате ЧЧ:ММ."
MSG_DAYS_EMPTY = "Выберите хотя бы один день недели."
MSG_DAYS_RANGE = "Дни недели — числа от 1 (пн) до 7 (вс)."
MSG_NO_CHANGES = "Нет изменений."

_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?$")


@dataclass(frozen=True)
class IngestionSchedule:
    """Singleton auto-collect schedule (D-14). Missing DB row → domain defaults."""

    enabled: bool
    time_of_day: time
    days_of_week: tuple[int, ...]
    last_run_at: datetime | None
    updated_at: datetime | None = None


def parse_time_of_day(raw: str) -> time:
    """Accept ``HH:MM`` or ``HH:MM:SS``; reject everything else with Russian message."""
    if not isinstance(raw, str) or not raw:
        raise IngestionScheduleValidationError(
            (PipelineConfigError(path="time_of_day", message=MSG_TIME_OF_DAY),)
        )
    match = _HHMM_RE.fullmatch(raw)
    if match is None:
        raise IngestionScheduleValidationError(
            (PipelineConfigError(path="time_of_day", message=MSG_TIME_OF_DAY),)
        )
    hour = int(match.group(1))
    minute = int(match.group(2))
    return time(hour, minute)


def format_time_of_day(value: time) -> str:
    """Normalize wall-clock time to zero-padded ``HH:MM`` for API responses."""
    return f"{value.hour:02d}:{value.minute:02d}"


def normalize_days(raw: Sequence[int]) -> tuple[int, ...]:
    """Dedupe + ascending sort; reject empty / out-of-range / bool entries."""
    if raw is None or len(raw) == 0:
        raise IngestionScheduleValidationError(
            (PipelineConfigError(path="days_of_week", message=MSG_DAYS_EMPTY),)
        )
    cleaned: set[int] = set()
    for day in raw:
        # bool is a subclass of int — reject explicitly (True/False are not weekdays).
        if isinstance(day, bool) or not isinstance(day, int) or day < 1 or day > 7:
            raise IngestionScheduleValidationError(
                (PipelineConfigError(path="days_of_week", message=MSG_DAYS_RANGE),)
            )
        cleaned.add(day)
    return tuple(sorted(cleaned))


def default_ingestion_schedule() -> IngestionSchedule:
    """Code-side defaults when the singleton row is absent (D-14, migration 013)."""
    return IngestionSchedule(
        enabled=True,
        time_of_day=DEFAULT_TIME_OF_DAY,
        days_of_week=ALL_WEEKDAYS,
        last_run_at=None,
        updated_at=None,
    )
