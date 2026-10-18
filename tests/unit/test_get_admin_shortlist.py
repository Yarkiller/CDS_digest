"""get_admin_shortlist use-case — ADMIN-01/05, D-79…D-81."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from backend.application.use_cases.get_admin_shortlist import get_admin_shortlist
from backend.domain.errors import PersistenceError
from backend.domain.shortlist import ShortlistBatch, ShortlistItem
from backend.tests_support.in_memory import InMemoryShortlistRepository
import pytest


def _item(
    *,
    material_id: int = 1,
    rank: int = 1,
    title: str = "Кандидат",
    material_status: str = "ready",
    decision: str = "pending",
    score: float | None = 0.91,
    score_factors: dict | None = None,
) -> ShortlistItem:
    return ShortlistItem(
        material_id=material_id,
        rank=rank,
        title=title,
        material_status=material_status,
        decision=decision,
        score=score,
        score_factors=score_factors
        or {
            "factors": [
                {"label": "Релевантность"},
                {"label": "Свежесть"},
            ]
        },
    )


def test_get_admin_shortlist_empty_batch_returns_empty_items() -> None:
    """D-80 / D-81: no current unsent batch → honest empty DTO (not an exception)."""
    repo = InMemoryShortlistRepository(batch=None)
    result = get_admin_shortlist(repo)
    assert result.batch_id is None
    assert result.items == ()
    assert result.digest_rest is False
    assert result.days_until_next_batch is None


def test_get_admin_shortlist_after_send_returns_digest_rest() -> None:
    """G-05-2: current None + latest sent → rest DTO (not D-80 empty)."""
    sent = ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc),
        items=(_item(material_id=1, rank=1),),
    )
    repo = InMemoryShortlistRepository(batch=sent)
    assert repo.get_current_batch() is None
    assert repo.get_latest_batch() is not None
    assert repo.get_latest_batch().sent_at is not None

    result = get_admin_shortlist(repo)
    assert result.batch_id is None
    assert result.items == ()
    assert result.digest_rest is True
    assert result.days_until_next_batch == 7


def test_get_admin_shortlist_no_latest_is_not_digest_rest() -> None:
    """G-05-2: genuine empty (no latest) stays D-80-shaped."""
    result = get_admin_shortlist(InMemoryShortlistRepository(batch=None))
    assert result.digest_rest is False
    assert result.days_until_next_batch is None
    assert result.items == ()


def test_get_admin_shortlist_unsent_batch_is_not_digest_rest() -> None:
    """G-05-2: populated unsent shortlist keeps digest_rest=False."""
    batch = ShortlistBatch(
        id=10,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(_item(material_id=1, rank=1),),
    )
    result = get_admin_shortlist(InMemoryShortlistRepository(batch=batch))
    assert result.batch_id == 10
    assert len(result.items) == 1
    assert result.digest_rest is False
    assert result.days_until_next_batch is None


def test_get_admin_shortlist_caps_at_five_ranked_items() -> None:
    """ADMIN-01: ≤5 ranked candidates."""
    items = tuple(
        _item(material_id=i, rank=i, title=f"Item {i}") for i in range(1, 8)
    )
    batch = ShortlistBatch(
        id=10,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=items,
    )
    result = get_admin_shortlist(InMemoryShortlistRepository(batch=batch))
    assert result.batch_id == 10
    assert len(result.items) == 5
    assert [it.rank for it in result.items] == [1, 2, 3, 4, 5]


def test_get_admin_shortlist_maps_factor_honesty_and_passes_score() -> None:
    """ADMIN-05 / D-79: ≥2 labels kept; <2 → empty factor_labels; score passed through."""
    batch = ShortlistBatch(
        id=1,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            _item(
                material_id=1,
                rank=1,
                score=0.88,
                score_factors={"A": 1, "B": 2},
            ),
            _item(
                material_id=2,
                rank=2,
                material_status="draft",
                score=Decimal("0.5"),
                score_factors={"only": 1},
            ),
        ),
    )
    result = get_admin_shortlist(InMemoryShortlistRepository(batch=batch))
    assert result.items[0].factor_labels == ("A", "B")
    assert result.items[0].score == 0.88
    assert result.items[1].factor_labels == ()
    assert result.items[1].material_status == "draft"
    assert float(result.items[1].score) == 0.5


def test_get_admin_shortlist_propagates_persistence_error() -> None:
    class _Failing:
        def get_current_batch(self):
            raise PersistenceError("db down")

    with pytest.raises(PersistenceError):
        get_admin_shortlist(_Failing())


def test_get_admin_shortlist_includes_week_label_sent_at_and_dek() -> None:
    """WR-04: SPA consumes week_label, sent_at, and per-item dek from the live DTO."""
    batch = ShortlistBatch(
        id=10,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            ShortlistItem(
                material_id=1,
                rank=1,
                title="RAG",
                material_status="ready",
                decision="pending",
                score=0.9,
                score_factors={"A": 1, "B": 2},
                dek="Краткий dek для превью",
            ),
        ),
    )
    result = get_admin_shortlist(InMemoryShortlistRepository(batch=batch))
    assert result.week_label == "2026-09-15"
    assert result.sent_at is None
    assert result.items[0].dek == "Краткий dek для превью"
