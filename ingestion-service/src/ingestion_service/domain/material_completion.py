"""Slug and reading-minutes helpers for persist-ready MaterialDraft (D-12, D-13)."""

from __future__ import annotations

import math

from slugify import slugify


def generate_slug(title: str, video_id: str) -> str:
    return f"{slugify(title)[:50]}-{video_id}"


def estimate_reading_minutes(body_markdown: str) -> int:
    return max(1, math.ceil(len(body_markdown.split()) / 200))
