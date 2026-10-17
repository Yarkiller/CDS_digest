"""Ingest source domain entity — SRC-01 (D-06, D-07, D-08, D-10, D-14).

Admin-managed YouTube channel/playlist subscription row. No fastapi/httpx/
supabase imports — persistence lives behind IngestSourceRepository.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IngestSource:
    """One admin-managed ingest subscription (channel or playlist)."""

    id: int
    kind: str
    source_id: str
    label: str | None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
