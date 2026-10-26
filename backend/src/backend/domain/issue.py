"""Issue read-models for current/archive content (no FastAPI/Supabase)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IssueItem:
    slug: str
    title: str
    position: int
    format: str
    reading_minutes: int
    dek: str | None = None


@dataclass(frozen=True)
class Issue:
    id: str
    number: int
    period_label: str
    title: str
    editor: str | None
    published_at: datetime
    items: tuple[IssueItem, ...] = ()
