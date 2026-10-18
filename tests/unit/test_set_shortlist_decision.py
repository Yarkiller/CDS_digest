"""set_shortlist_decision use-case — Approve/Reject persist (ADMIN-02/03, D-82, D-85)."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from backend.application.use_cases.set_shortlist_decision import set_shortlist_decision
from backend.domain.errors import InvalidShortlistDecisionError, ShortlistNotFoundError
from backend.domain.shortlist import ShortlistBatch, ShortlistItem
from backend.tests_support.in_memory import InMemoryShortlistRepository


def _item(
    *,
    material_id: int = 101,
    rank: int = 1,
    title: str = "RAG в продакшене",
    material_status: str = "ready",
    decision: str = "pending",
    score: float | None = 0.92,
) -> ShortlistItem:
    return ShortlistItem(
        material_id=material_id,
        rank=rank,
        title=title,
        material_status=material_status,
        decision=decision,
        score=score,
        score_factors={
            "factors": [
                {"label": "Релевантность"},
                {"label": "Свежесть"},
            ]
        },
    )


def _seeded_batch() -> ShortlistBatch:
    return ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=(
            _item(material_id=101, rank=1, material_status="ready"),
            _item(
                material_id=102,
                rank=2,
                title="Черновик",
                material_status="draft",
                score=0.4,
            ),
        ),
    )


def test_approve_persists_decision_and_returns_snapshot() -> None:
    """ADMIN-02 / D-82: approved writes via set_decision; GET snapshot reflects it."""
    repo = InMemoryShortlistRepository(batch=_seeded_batch())
    actor = "admin-uuid-1"
    decided_at = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)

    snapshot = set_shortlist_decision(
        repo,
        material_id=101,
        decision="approved",
        actor_user_id=actor,
        now=decided_at,
    )

    assert snapshot.batch_id == 42
    approved = next(i for i in snapshot.items if i.material_id == 101)
    assert approved.decision == "approved"
    assert approved.material_status == "ready"

    batch = repo.get_current_batch()
    assert batch is not None
    stored = next(i for i in batch.items if i.material_id == 101)
    assert stored.decision == "approved"
    assert stored.decided_by == actor
    assert stored.decided_at == decided_at


def test_reject_persists_decision_on_subsequent_get() -> None:
    """ADMIN-02 / D-82: rejected persists and is visible on get_current_batch."""
    repo = InMemoryShortlistRepository(batch=_seeded_batch())

    snapshot = set_shortlist_decision(
        repo,
        material_id=101,
        decision="rejected",
        actor_user_id="admin-uuid-1",
    )

    assert next(i for i in snapshot.items if i.material_id == 101).decision == "rejected"
    batch = repo.get_current_batch()
    assert batch is not None
    assert next(i for i in batch.items if i.material_id == 101).decision == "rejected"


def test_approve_allowed_on_draft_material() -> None:
    """D-02 / D-85 / ADUX-05: Approve ≠ ready — draft material_status stays draft after approve."""
    repo = InMemoryShortlistRepository(batch=_seeded_batch())

    snapshot = set_shortlist_decision(
        repo,
        material_id=102,
        decision="approved",
        actor_user_id="admin-uuid-1",
    )

    draft = next(i for i in snapshot.items if i.material_id == 102)
    assert draft.decision == "approved"
    # D-02: decision path must not flip triage ready
    assert draft.material_status == "draft"


def test_set_shortlist_decision_does_not_import_ready_path() -> None:
    """D-02 / ADUX-05: decision use-case must not import MaterialRepository or mark_material_ready."""
    import ast
    from pathlib import Path

    source_path = (
        Path(__file__).resolve().parents[2]
        / "backend"
        / "src"
        / "backend"
        / "application"
        / "use_cases"
        / "set_shortlist_decision.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported.add(module)
            for alias in node.names:
                imported.add(f"{module}.{alias.name}" if module else alias.name)

    assert not any("material_repository" in name for name in imported)
    assert not any("mark_material_ready" in name for name in imported)


def test_pending_resets_decision() -> None:
    """D-82: pending is a valid allowlisted decision."""
    repo = InMemoryShortlistRepository(batch=_seeded_batch())
    set_shortlist_decision(
        repo,
        material_id=101,
        decision="approved",
        actor_user_id="admin-uuid-1",
    )

    snapshot = set_shortlist_decision(
        repo,
        material_id=101,
        decision="pending",
        actor_user_id="admin-uuid-1",
    )

    assert next(i for i in snapshot.items if i.material_id == 101).decision == "pending"


def test_unknown_material_raises_shortlist_not_found() -> None:
    repo = InMemoryShortlistRepository(batch=_seeded_batch())

    with pytest.raises(ShortlistNotFoundError):
        set_shortlist_decision(
            repo,
            material_id=999,
            decision="approved",
            actor_user_id="admin-uuid-1",
        )


def test_missing_batch_raises_shortlist_not_found() -> None:
    repo = InMemoryShortlistRepository(batch=None)

    with pytest.raises(ShortlistNotFoundError):
        set_shortlist_decision(
            repo,
            material_id=101,
            decision="approved",
            actor_user_id="admin-uuid-1",
        )


def test_invalid_decision_raises() -> None:
    repo = InMemoryShortlistRepository(batch=_seeded_batch())

    with pytest.raises(InvalidShortlistDecisionError):
        set_shortlist_decision(
            repo,
            material_id=101,
            decision="include",
            actor_user_id="admin-uuid-1",
        )
