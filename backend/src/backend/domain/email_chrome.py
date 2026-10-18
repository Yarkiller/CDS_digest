"""Assert-only email chrome ban list (ADUX-04, D-17/D-18).

Do not call from renderers to mutate output — tests and scrub tooling only.
"""

from __future__ import annotations

FORBIDDEN_LOWER = ["test-header", "test_header", "testheader"]


def contains_forbidden_chrome(text: str) -> bool:
    """Return True if any closed ban token appears (case-insensitive)."""
    lowered = (text or "").lower()
    return any(token in lowered for token in FORBIDDEN_LOWER)
