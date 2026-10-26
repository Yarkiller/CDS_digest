"""Operator-facing ingest diagnostic errors (D-11, D-13)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Stage = Literal[
    "url",
    "captions",
    "metadata",
    "consistency",
    "llm",
    "llm_truncation",
    "persist",
]


@dataclass
class IngestError(Exception):
    stage: Stage
    reason: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 1

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": False,
            "stage": self.stage,
            "reason": self.reason,
            "message": self.message,
            "exit_code": self.exit_code,
        }
        if self.context:
            payload["context"] = self.context
        return payload
