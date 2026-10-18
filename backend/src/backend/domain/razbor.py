"""Razbor domain entity — chronology list + longread (RAZB-01 / D-68)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RazborStatus(str, Enum):
    ANNOUNCEMENT = "announcement"
    PUBLISHED = "published"


@dataclass(frozen=True)
class Razbor:
    id: int
    title: str
    body_markdown: str
    meeting_at: datetime | None
    status: RazborStatus
    notebook_path: str | None
    created_at: datetime
