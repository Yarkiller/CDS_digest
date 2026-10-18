from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime, timezone

from backend.application.ports.knowledge_chunk_repository import KnowledgeChunkRepository
from backend.application.ports.material_repository import MaterialRepository
from backend.domain.errors import MaterialNotFoundError, MaterialNotReadyError
from backend.domain.knowledge import KnowledgeChunk
from backend.domain.material import MaterialStatus

def _heading_title(line: str) -> str | None:
    """ATX heading title, or None. Linear scan — no backtracking quantifiers."""
    marks = 0
    while marks < len(line) and line[marks] == "#":
        marks += 1
    if marks < 1 or marks > 6:
        return None
    if marks >= len(line) or line[marks] not in " \t":
        return None
    return line[marks + 1 :].strip()


def _flush_atom(
    atoms: list[tuple[str | None, str]],
    heading: str | None,
    lines: list[str],
    *,
    seen_heading: bool,
) -> None:
    body = "\n".join(lines).strip()
    if not seen_heading:
        if body:
            atoms.append((None, body))
        return
    if body:
        atoms.append((heading, body))
    elif heading:
        atoms.append((heading, heading))


def split_article_into_atoms(body_markdown: str) -> list[tuple[str | None, str]]:
    """Split published article markdown into atomic (heading, content) chunks."""
    text = body_markdown.strip()
    if not text:
        return []

    atoms: list[tuple[str | None, str]] = []
    heading: str | None = None
    buffer: list[str] = []
    seen_heading = False
    for line in text.splitlines():
        title = _heading_title(line)
        if title is None:
            buffer.append(line)
            continue
        _flush_atom(atoms, heading, buffer, seen_heading=seen_heading)
        seen_heading = True
        heading = title
        buffer = []
    _flush_atom(atoms, heading, buffer, seen_heading=seen_heading)
    if not atoms:
        atoms.append((None, text))
    return atoms


def index_material_chunks(
    *,
    materials: MaterialRepository,
    chunks: KnowledgeChunkRepository,
    material_id: int,
    embedding_model_id: str,
    embed: Callable[[str], list[float]],
    now: datetime | None = None,
) -> list[KnowledgeChunk]:
    material = materials.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    if material.status != MaterialStatus.READY:
        raise MaterialNotReadyError(material_id)

    created_at = now or datetime.now(timezone.utc)
    built: list[KnowledgeChunk] = []
    for index, (heading, content) in enumerate(split_article_into_atoms(material.body_markdown)):
        payload = f"{heading or ''}\n{content}".strip()
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        built.append(
            KnowledgeChunk(
                id=0,
                material_id=material_id,
                chunk_index=index,
                heading=heading,
                content_md=content,
                embedding=embed(payload),
                embedding_model_id=embedding_model_id,
                content_sha256=digest,
                created_at=created_at,
            )
        )
    return chunks.replace_for_material(material_id, built)
