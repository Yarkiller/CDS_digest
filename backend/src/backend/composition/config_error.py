"""Startup configuration errors — raised while wiring, before the app serves traffic.

Mirrors ``ingestion_service.composition.config_error``: a plain ``Exception`` (deliberately
**not** a ``DomainError``) because misconfiguration is a deployment failure, not a business
rule. ``resolve_mailer`` raises it when ``MAILER=smtp`` lacks required ``SMTP_*`` (D-16).
"""

from __future__ import annotations


class ConfigurationError(Exception):
    """Settings or adapter-wiring misconfiguration detected at startup (D-16 / MAIL-05)."""
