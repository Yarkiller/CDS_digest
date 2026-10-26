"""Pipeline config read/save use-cases — PIPE-01/PIPE-03 (D-08, D-11, D-13).

Read is a straight repository pass-through. Save validates through the
PipelineConfigValidator port *before* persisting — no silent accept (D-03/D-07).
Both functions import only ports + domain; PyYAML/Pydantic live in the
infrastructure adapter behind the validator port.
"""

from __future__ import annotations

from datetime import datetime, timezone

from backend.application.ports.pipeline_config import (
    PipelineConfigRepository,
    PipelineConfigValidator,
)
from backend.domain.pipeline_config import PipelineConfig


def get_pipeline_config(repo: PipelineConfigRepository) -> PipelineConfig | None:
    """Return the current config, or None for the empty state (D-11)."""
    return repo.get()


def save_pipeline_config(
    repo: PipelineConfigRepository,
    validator: PipelineConfigValidator,
    *,
    yaml_text: str,
    now: datetime | None = None,
) -> PipelineConfig:
    """Validate then persist the document, returning the stored config (D-08/D-11)."""
    validator.validate(yaml_text)
    return repo.save(yaml=yaml_text, updated_at=now or datetime.now(timezone.utc))
