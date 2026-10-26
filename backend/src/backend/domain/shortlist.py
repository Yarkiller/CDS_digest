"""Admin shortlist domain DTOs and ADMIN-05 score_factors honesty (D-79)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping


def honest_factor_labels(score_factors: Mapping[str, Any] | None) -> list[str]:
    """Return readable factor labels only when ≥2 exist; else [] for «обоснование недоступно».

    Accepts either ``{"factors": [{"label": "..."}, ...]}`` or a flat map whose keys
    are human labels (excluding the reserved ``factors`` key).
    """
    if not score_factors:
        return []
    factors = score_factors.get("factors")
    # WR-02: structured ``factors`` is authoritative only when it yields ≥1 readable
    # label. Empty list or blank/non-dict entries must fall through to flat keys
    # so ≥2 readable flat labels are not shadowed by «обоснование недоступно».
    if isinstance(factors, list) and factors:
        labels = [
            str(f.get("label", "")).strip()
            for f in factors
            if isinstance(f, dict)
        ]
        labels = [x for x in labels if x]
        if not labels:
            labels = [
                str(k).strip()
                for k, _v in score_factors.items()
                if str(k).strip() and k != "factors"
            ]
    else:
        labels = [
            str(k).strip()
            for k, _v in score_factors.items()
            if str(k).strip() and k != "factors"
        ]
    if len(labels) < 2:
        return []
    return labels


@dataclass(frozen=True)
class ShortlistItem:
    material_id: int
    rank: int
    title: str
    material_status: str
    decision: str
    score: float | None
    score_factors: Mapping[str, Any]
    decided_by: str | None = None
    decided_at: datetime | None = None
    dek: str | None = None
    # Phase 13 ADUX-01 / D-02 — material preview columns via shortlist join
    body_markdown: str | None = None
    provenance_label: str | None = None
    slug: str | None = None
    reading_minutes: int | None = None


@dataclass(frozen=True)
class ShortlistBatch:
    id: int
    week_start: date
    sent_at: datetime | None
    items: tuple[ShortlistItem, ...]


def material_counts(body_markdown: str | None) -> tuple[int, int]:
    """Return (char_count, word_count) for admin preview (ADUX-01; RESEARCH A1).

    ``char_count`` is ``len(body_markdown or "")`` (Python code-unit length).
    ``word_count`` uses ``str.split()`` whitespace tokens — same split as
    ``estimate_reading_minutes`` in ingestion material_completion.
    """
    text = body_markdown or ""
    return len(text), len(text.split())


@dataclass(frozen=True)
class AdminShortlistItem:
    material_id: int
    rank: int
    title: str
    material_status: str
    decision: str
    score: float | None
    factor_labels: tuple[str, ...]
    dek: str | None = None
    body_markdown: str | None = None
    provenance_label: str | None = None
    slug: str | None = None
    reading_minutes: int | None = None
    char_count: int = 0
    word_count: int = 0


@dataclass(frozen=True)
class AdminShortlist:
    batch_id: int | None
    items: tuple[AdminShortlistItem, ...]
    digest_rest: bool = False
    days_until_next_batch: int | None = None
    week_label: str | None = None
    sent_at: datetime | None = None


# Locked product weekly cadence (PROJECT.md / ROADMAP «weekly» digest) — G-05-2.
DIGEST_WEEKLY_CADENCE_DAYS = 7

# ADMIN-01 / D-78: admin-visible shortlist and send/preview pool cap.
MAX_SHORTLIST_ITEMS = 5


def visible_shortlist_items(items: tuple[ShortlistItem, ...]) -> tuple[ShortlistItem, ...]:
    """Top-N by rank — shared by GET shortlist, preview, and send (WR-05)."""
    return tuple(sorted(items, key=lambda item: item.rank)[:MAX_SHORTLIST_ITEMS])
