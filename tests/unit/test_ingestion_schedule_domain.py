"""RED→GREEN: ingestion schedule domain + use-case (ING-06, D-14/D-15/D-16).

Imports of not-yet-shipped symbols live inside helpers so collection succeeds
and failures stay assertion-level RED (missing symbols / wrong behaviour).
"""

from __future__ import annotations

from datetime import time

import pytest

_TIME_MSG = "Укажите время в формате ЧЧ:ММ."
_DAYS_EMPTY_MSG = "Выберите хотя бы один день недели."
_DAYS_RANGE_MSG = "Дни недели — числа от 1 (пн) до 7 (вс)."
_NO_CHANGES_MSG = "Нет изменений."


def _parse_time_of_day():
    try:
        from backend.domain.ingestion_schedule import parse_time_of_day
    except ImportError as exc:  # pragma: no cover - RED until domain ships
        pytest.fail(f"parse_time_of_day not importable: {exc}")
    return parse_time_of_day


def _normalize_days():
    try:
        from backend.domain.ingestion_schedule import normalize_days
    except ImportError as exc:  # pragma: no cover - RED until domain ships
        pytest.fail(f"normalize_days not importable: {exc}")
    return normalize_days


def _format_time_of_day():
    try:
        from backend.domain.ingestion_schedule import format_time_of_day
    except ImportError as exc:  # pragma: no cover - RED until domain ships
        pytest.fail(f"format_time_of_day not importable: {exc}")
    return format_time_of_day


def _validation_error_cls():
    try:
        from backend.domain.errors import IngestionScheduleValidationError
    except ImportError as exc:  # pragma: no cover - RED until error ships
        pytest.fail(f"IngestionScheduleValidationError not importable: {exc}")
    return IngestionScheduleValidationError


def _use_cases():
    try:
        from backend.application.use_cases.ingestion_schedule import (
            get_ingestion_schedule,
            update_ingestion_schedule,
        )
    except ImportError as exc:  # pragma: no cover - RED until use-case ships
        pytest.fail(f"ingestion_schedule use cases not importable: {exc}")
    return get_ingestion_schedule, update_ingestion_schedule


def _fake_repo():
    try:
        from backend.tests_support.in_memory import InMemoryIngestionScheduleRepository
    except ImportError as exc:  # pragma: no cover - RED until fake ships
        pytest.fail(f"InMemoryIngestionScheduleRepository not importable: {exc}")
    return InMemoryIngestionScheduleRepository()


def test_parse_time_of_day_accepts_hhmm_and_hhmmss():
    parse = _parse_time_of_day()
    assert parse("06:00") == time(6, 0)
    assert parse("06:00:00") == time(6, 0)


@pytest.mark.parametrize("raw", ["24:00", "6:0", "", None])
def test_parse_time_of_day_rejects_invalid(raw):
    parse = _parse_time_of_day()
    Err = _validation_error_cls()
    with pytest.raises(Err) as exc_info:
        parse(raw)  # type: ignore[arg-type]
    errors = exc_info.value.errors
    assert len(errors) == 1
    assert errors[0].path == "time_of_day"
    assert errors[0].message == _TIME_MSG


def test_normalize_days_dedupes_and_sorts():
    normalize = _normalize_days()
    assert normalize([7, 1, 1, 3]) == (1, 3, 7)


def test_normalize_days_rejects_empty():
    normalize = _normalize_days()
    Err = _validation_error_cls()
    with pytest.raises(Err) as exc_info:
        normalize([])
    assert exc_info.value.errors[0].path == "days_of_week"
    assert exc_info.value.errors[0].message == _DAYS_EMPTY_MSG


@pytest.mark.parametrize("raw", [[0], [8], [True]])
def test_normalize_days_rejects_out_of_range_and_bool(raw):
    normalize = _normalize_days()
    Err = _validation_error_cls()
    with pytest.raises(Err) as exc_info:
        normalize(raw)
    assert exc_info.value.errors[0].path == "days_of_week"
    assert exc_info.value.errors[0].message == _DAYS_RANGE_MSG


def test_format_time_of_day_zero_pads():
    fmt = _format_time_of_day()
    assert fmt(time(6, 0)) == "06:00"


def test_get_ingestion_schedule_defaults_on_empty_repo():
    get_schedule, _ = _use_cases()
    repo = _fake_repo()
    row = get_schedule(repo)
    assert row.enabled is True
    assert row.time_of_day == time(6, 0)
    assert row.days_of_week == (1, 2, 3, 4, 5, 6, 7)
    assert row.last_run_at is None


def test_update_merges_only_provided_fields():
    _, update = _use_cases()
    repo = _fake_repo()
    # Seed via first partial update so subsequent merge has a stored row.
    seeded = update(repo, enabled=True)
    assert seeded.time_of_day == time(6, 0)
    assert seeded.days_of_week == (1, 2, 3, 4, 5, 6, 7)

    disabled = update(repo, enabled=False)
    assert disabled.enabled is False
    assert disabled.time_of_day == time(6, 0)
    assert disabled.days_of_week == (1, 2, 3, 4, 5, 6, 7)

    days_only = update(repo, days_of_week=[5, 1, 1])
    assert days_only.enabled is False
    assert days_only.days_of_week == (1, 5)


def test_update_rejects_invalid_time_before_repo_write():
    _, update = _use_cases()
    repo = _fake_repo()
    Err = _validation_error_cls()
    with pytest.raises(Err) as exc_info:
        update(repo, time_of_day="25:00")
    assert exc_info.value.errors[0].path == "time_of_day"
    assert exc_info.value.errors[0].message == _TIME_MSG
    assert repo.update_calls == 0


def test_update_rejects_empty_patch():
    _, update = _use_cases()
    repo = _fake_repo()
    Err = _validation_error_cls()
    with pytest.raises(Err) as exc_info:
        update(repo)
    assert exc_info.value.errors[0].path == "body"
    assert exc_info.value.errors[0].message == _NO_CHANGES_MSG
    assert repo.update_calls == 0
