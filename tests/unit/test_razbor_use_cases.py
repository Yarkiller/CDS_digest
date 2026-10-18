"""list_razbors / get_razbor use-cases — ordering + not-found (RAZB-01)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.application.use_cases.get_razbor import get_razbor
from backend.application.use_cases.list_razbors import list_razbors
from backend.domain.errors import RazborNotFoundError
from backend.domain.razbor import Razbor, RazborStatus
from backend.tests_support.in_memory import InMemoryRazborRepository


def _razbor(
    *,
    razbor_id: int,
    title: str = "Razbor",
    status: RazborStatus = RazborStatus.PUBLISHED,
    meeting_at: datetime | None = None,
    created_at: datetime | None = None,
) -> Razbor:
    created = created_at or datetime(2026, 3, 1, tzinfo=timezone.utc)
    return Razbor(
        id=razbor_id,
        title=title,
        body_markdown="",
        meeting_at=meeting_at,
        status=status,
        notebook_path=None,
        created_at=created,
    )


def test_list_razbors_orders_meeting_at_desc_nulls_last_then_created_at() -> None:
    """RAZB-01: meeting_at DESC NULLS LAST, created_at DESC; equal meeting keeps created secondary."""
    shared_meeting = datetime(2026, 4, 14, tzinfo=timezone.utc)
    repo = InMemoryRazborRepository(
        [
            _razbor(
                razbor_id=1,
                title="null meeting newer",
                meeting_at=None,
                created_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
            ),
            _razbor(
                razbor_id=2,
                title="same meeting older created",
                meeting_at=shared_meeting,
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            ),
            _razbor(
                razbor_id=3,
                title="same meeting newer created",
                meeting_at=shared_meeting,
                created_at=datetime(2026, 3, 10, tzinfo=timezone.utc),
            ),
            _razbor(
                razbor_id=4,
                title="earlier meeting",
                meeting_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                created_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            ),
        ]
    )
    result = list_razbors(repo)
    assert [r.id for r in result] == [3, 2, 4, 1]


def test_list_razbors_empty_returns_empty_list() -> None:
    """RAZB-01 empty ASSUMPTION: empty repository → []."""
    assert list_razbors(InMemoryRazborRepository()) == []


def test_get_razbor_missing_raises_not_found() -> None:
    """RAZB-02: missing id → RazborNotFoundError (soft 404 upstream)."""
    with pytest.raises(RazborNotFoundError):
        get_razbor(InMemoryRazborRepository(), 99)


def test_get_razbor_returns_published_with_body() -> None:
    """RAZB-02: published detail exposes title, status, body_markdown, meeting_at."""
    meeting = datetime(2026, 3, 17, tzinfo=timezone.utc)
    body = "## Intro\n\nProse.\n\n## Next\n\nMore."
    repo = InMemoryRazborRepository(
        [
            Razbor(
                id=2,
                title="Anomaly Detection",
                body_markdown=body,
                meeting_at=meeting,
                status=RazborStatus.PUBLISHED,
                notebook_path=None,
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
        ]
    )
    detail = get_razbor(repo, 2)
    assert detail.id == 2
    assert detail.title == "Anomaly Detection"
    assert detail.status == RazborStatus.PUBLISHED
    assert detail.meeting_at == meeting
    assert detail.body_markdown == body


def test_get_razbor_announcement_returns_empty_body() -> None:
    """D-68 / T-04-10: announcement stub ignores prose — body_markdown emptied."""
    repo = InMemoryRazborRepository(
        [
            Razbor(
                id=4,
                title="RAG в корпоративной среде",
                body_markdown="## Secret draft\n\nShould not leak.",
                meeting_at=datetime(2026, 4, 14, tzinfo=timezone.utc),
                status=RazborStatus.ANNOUNCEMENT,
                notebook_path=None,
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
        ]
    )
    detail = get_razbor(repo, 4)
    assert detail.status == RazborStatus.ANNOUNCEMENT
    assert detail.title == "RAG в корпоративной среде"
    assert detail.body_markdown == ""


_QUALITY_BODY = """## Введение

Контекст.

## Качество

| Метрика | Значение |
| --- | --- |
| Precision | 0.82 |
| Recall | 0.71 |
"""

_OVERVIEW_BODY = """## Контекст

Обзор темы без таблицы метрик.

## Подход

Как мы думаем об этом.
"""


def test_get_razbor_content_kind_quality_when_heading_and_numeric_table() -> None:
    """RAZB-04 / D-73: ## Качество + numeric markdown table → content_kind=quality."""
    from backend.application.use_cases.get_razbor import detect_content_kind

    assert detect_content_kind(_QUALITY_BODY) == "quality"
    repo = InMemoryRazborRepository(
        [
            Razbor(
                id=2,
                title="Anomaly",
                body_markdown=_QUALITY_BODY,
                meeting_at=datetime(2026, 3, 17, tzinfo=timezone.utc),
                status=RazborStatus.PUBLISHED,
                notebook_path=None,
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
        ]
    )
    detail = get_razbor(repo, 2)
    assert detail.content_kind == "quality"


def test_get_razbor_content_kind_overview_without_metrics() -> None:
    """RAZB-04 / D-73: published without metrics table → content_kind=overview."""
    from backend.application.use_cases.get_razbor import detect_content_kind

    assert detect_content_kind(_OVERVIEW_BODY) == "overview"
    # Quality heading alone without numeric table is still overview
    assert (
        detect_content_kind("## Оценка качества\n\nПока без цифр.\n") == "overview"
    )
    repo = InMemoryRazborRepository(
        [
            Razbor(
                id=3,
                title="LLM overview",
                body_markdown=_OVERVIEW_BODY,
                meeting_at=datetime(2026, 3, 31, tzinfo=timezone.utc),
                status=RazborStatus.PUBLISHED,
                notebook_path=None,
                created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            )
        ]
    )
    detail = get_razbor(repo, 3)
    assert detail.content_kind == "overview"
