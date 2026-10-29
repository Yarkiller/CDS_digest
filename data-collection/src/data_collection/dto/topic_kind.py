"""Closed topic-kind set for ingestion drafts (KIND-01, KIND-02). Not a public export."""

from __future__ import annotations

from typing import Literal

TopicKind = Literal["practical", "conceptual"]
VALID_TOPIC_KINDS: frozenset[str] = frozenset({"practical", "conceptual"})


def normalize_topic_kind(value: object) -> TopicKind:
    """Keep only practical|conceptual after strip+casefold; everything else is conceptual."""
    if isinstance(value, str):
        token = value.strip().casefold()
        if token in VALID_TOPIC_KINDS:
            return token  # type: ignore[return-value]
    return "conceptual"
