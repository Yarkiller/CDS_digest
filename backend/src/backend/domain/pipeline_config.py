"""Pipeline config domain model — PIPE-01/PIPE-03 (D-08, D-11, D-12, D-13).

The PIPE-01 MVP config is a raw YAML document persisted as a single global row
behind the PipelineConfigRepository port (D-08). The YAML text is the source of
truth (D-13); the backend owns schema validation and the SPA renders the
``{yaml, updated_at}`` DTO verbatim (D-11). This module carries no yaml/pydantic
imports — parsing stays in the infrastructure validator adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PipelineConfig:
    """A saved pipeline config document plus its last-saved timestamp (D-08/D-11)."""

    yaml: str
    updated_at: datetime | None


@dataclass(frozen=True)
class PipelineConfigError:
    """One structured validation failure (PIPE-02, D-05).

    ``path`` is a dotted field path (empty for document-level parse errors) and
    ``line`` is the 1-based YAML line when the parser can supply one. ``to_dict()``
    omits ``line`` when it is None so the reject payload matches the UI-SPEC contract
    verbatim.
    """

    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"path": self.path, "message": self.message}
        if self.line is not None:
            payload["line"] = self.line
        return payload

