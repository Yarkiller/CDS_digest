"""Startup configuration errors — not an IngestError stage (D-17)."""

from __future__ import annotations


class ConfigurationError(Exception):
    """Settings or client factory misconfiguration before any video is processed."""
