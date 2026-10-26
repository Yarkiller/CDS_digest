"""Get razbor by id for reader detail (RAZB-02 / RAZB-04 / D-68 / D-73)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from backend.application.ports.razbor_repository import RazborRepository
from backend.domain.errors import RazborNotFoundError
from backend.domain.razbor import RazborStatus

_QUALITY_HEADING = re.compile(
    r"^##\s+(?:Качество|Оценка качества)\s*$",
    re.MULTILINE,
)
_MARKDOWN_TABLE_ROW = re.compile(r"^\|.+\|\s*$", re.MULTILINE)
_NUMERIC_CELL = re.compile(r"\d+(?:[.,]\d+)?")


@dataclass(frozen=True)
class RazborDetail:
    """Reader-facing razbor view — announcement prose stripped; content_kind honesty."""

    id: int
    title: str
    body_markdown: str
    meeting_at: datetime | None
    status: RazborStatus
    notebook_path: str | None
    created_at: datetime
    content_kind: str  # "quality" | "overview"


def detect_content_kind(body_markdown: str) -> str:
    """RAZB-04 / D-73 / RESEARCH Pattern 7: quality heading + numeric table → quality."""
    if not body_markdown or not _QUALITY_HEADING.search(body_markdown):
        return "overview"
    table_rows = _MARKDOWN_TABLE_ROW.findall(body_markdown)
    if len(table_rows) < 2:
        return "overview"
    # Skip separator rows like | --- | --- |
    data_cells = []
    for row in table_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells):
            continue
        data_cells.extend(cells)
    if any(_NUMERIC_CELL.search(cell) for cell in data_cells):
        return "quality"
    return "overview"


def get_razbor(razbors: RazborRepository, razbor_id: int) -> RazborDetail:
    """Return reader detail or raise RazborNotFoundError when missing.

    Announcement stubs never expose draft prose (D-68 / T-04-10).
    """
    razbor = razbors.get(razbor_id)
    if razbor is None:
        raise RazborNotFoundError(razbor_id)

    if razbor.status == RazborStatus.ANNOUNCEMENT:
        return RazborDetail(
            id=razbor.id,
            title=razbor.title,
            body_markdown="",
            meeting_at=razbor.meeting_at,
            status=razbor.status,
            notebook_path=razbor.notebook_path,
            created_at=razbor.created_at,
            content_kind="overview",
        )

    return RazborDetail(
        id=razbor.id,
        title=razbor.title,
        body_markdown=razbor.body_markdown,
        meeting_at=razbor.meeting_at,
        status=razbor.status,
        notebook_path=razbor.notebook_path,
        created_at=razbor.created_at,
        content_kind=detect_content_kind(razbor.body_markdown),
    )
