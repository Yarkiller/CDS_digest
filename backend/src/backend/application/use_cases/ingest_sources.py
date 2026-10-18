"""Ingest-source use cases — validate-then-persist (SRC-01/SRC-02, D-14/D-15).

List/add/set_enabled/delete. Rejects never write (D-20); DELETE is hard (D-10).
"""

from __future__ import annotations

import re

from backend.application.ports.ingest_sources import IngestSourceRepository
from backend.domain.errors import IngestSourceNotFoundError, IngestSourceValidationError
from backend.domain.ingest_source import IngestSource
from backend.domain.pipeline_config import PipelineConfigError

_CHANNEL_ID_RE = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
_PLAYLIST_ID_RE = re.compile(r"^PL[A-Za-z0-9_-]{32}$")
_LABEL_MAX = 120

_INVALID_SOURCE_ID = "Укажите канонический id: UC… для канала или PL… для плейлиста."
_KIND_MISMATCH = "Тип источника не совпадает с префиксом идентификатора."
_LABEL_TOO_LONG = "Название не длиннее 120 символов."
_DUPLICATE = "Этот источник уже добавлен"


def list_ingest_sources(repo: IngestSourceRepository) -> list[IngestSource]:
    return repo.list()


def add_ingest_source(
    repo: IngestSourceRepository,
    *,
    kind: str,
    source_id: str,
    label: str | None = None,
) -> IngestSource:
    """Validate then persist. Raises IngestSourceValidationError before any write."""
    errors = _validate_add(kind=kind, source_id=source_id, label=label, existing=repo.list())
    if errors:
        raise IngestSourceValidationError(tuple(errors))
    normalized_label = _normalize_label(label)
    return repo.add(
        kind=kind,
        source_id=source_id.strip(),
        label=normalized_label,
        is_enabled=True,
    )


def set_ingest_source_enabled(
    repo: IngestSourceRepository,
    source_id_pk: int,
    *,
    is_enabled: bool,
) -> IngestSource:
    """Toggle is_enabled for an existing row (D-01/D-18). Missing → NotFound."""
    try:
        return repo.set_enabled(source_id_pk, is_enabled=is_enabled)
    except KeyError as exc:
        raise IngestSourceNotFoundError(source_id_pk) from exc


def delete_ingest_source(repo: IngestSourceRepository, source_id_pk: int) -> None:
    """Hard-delete the row (D-10). Missing → NotFound."""
    try:
        repo.delete(source_id_pk)
    except KeyError as exc:
        raise IngestSourceNotFoundError(source_id_pk) from exc


def _normalize_label(label: str | None) -> str | None:
    if label is None:
        return None
    trimmed = label.strip()
    return trimmed or None


def _validate_add(
    *,
    kind: str,
    source_id: str,
    label: str | None,
    existing: list[IngestSource],
) -> list[PipelineConfigError]:
    errors: list[PipelineConfigError] = []
    raw_id = (source_id or "").strip()
    kind_value = (kind or "").strip()

    if kind_value not in ("channel", "playlist"):
        errors.append(PipelineConfigError(path="kind", message="Допустимы channel или playlist."))
        return errors

    if kind_value == "channel":
        if not _CHANNEL_ID_RE.fullmatch(raw_id):
            if raw_id.startswith("PL") or (
                raw_id.startswith("UC") and len(raw_id) != 24
            ):
                # Prefix hints at playlist / wrong length — still source_id path;
                # kind/prefix mismatch when PL… under channel.
                if raw_id.startswith("PL"):
                    errors.append(PipelineConfigError(path="source_id", message=_KIND_MISMATCH))
                else:
                    errors.append(PipelineConfigError(path="source_id", message=_INVALID_SOURCE_ID))
            else:
                errors.append(PipelineConfigError(path="source_id", message=_INVALID_SOURCE_ID))
    else:  # playlist
        if not _PLAYLIST_ID_RE.fullmatch(raw_id):
            if raw_id.startswith("UC"):
                errors.append(PipelineConfigError(path="source_id", message=_KIND_MISMATCH))
            else:
                errors.append(PipelineConfigError(path="source_id", message=_INVALID_SOURCE_ID))

    if label is not None and len(label.strip()) > _LABEL_MAX:
        errors.append(PipelineConfigError(path="label", message=_LABEL_TOO_LONG))

    if not errors:
        for row in existing:
            if row.kind == kind_value and row.source_id == raw_id:
                errors.append(PipelineConfigError(path="source_id", message=_DUPLICATE))
                break

    return errors
