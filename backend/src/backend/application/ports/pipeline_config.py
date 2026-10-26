"""Pipeline config ports — repository + validator (PIPE-01/PIPE-03, D-08, D-10, D-11).

Both Protocols live in one merged module: the repository persists the singleton
YAML document (D-08), and the validator is the server-authoritative schema gate
(D-03/D-07) called before any write. Ports carry no yaml/pydantic imports — the
parsing adapter lives in infrastructure and is wired only in composition.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from backend.domain.pipeline_config import PipelineConfig


class PipelineConfigRepository(Protocol):
    def get(self) -> PipelineConfig | None:
        """Current saved config, or None when the singleton row is absent (D-11)."""
        ...

    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig:
        """Persist the YAML document and return the stored config (D-08)."""
        ...


class PipelineConfigValidator(Protocol):
    def validate(self, yaml_text: str) -> None:
        """Validate the document; raise PipelineConfigValidationError on reject (D-03/D-07)."""
        ...
