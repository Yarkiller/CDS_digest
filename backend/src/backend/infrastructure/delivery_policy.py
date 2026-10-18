"""Delivery-stop policy shared by live ``Mailer`` adapters (D-07 / D-08).

The policy is transport-agnostic: SMTP and HTTP adapters both deliver one message per
recipient (D-05), derive an honest status from delivered-vs-planned counts (D-07), and
stop after the same number of *consecutive* failures (D-08). Keeping it here means a new
transport cannot quietly drift to a different stop/status contract.
"""

from __future__ import annotations

CONSECUTIVE_FAILURE_LIMIT = 3
"""D-08: stop the per-recipient loop after this many consecutive transport failures."""

STOP_REASON_CONSECUTIVE_FAILURES = "consecutive_failures"
"""D-08: ``stop_reason`` value reported once the consecutive-failure limit trips."""


def delivery_status(delivered: int, planned: int) -> str:
    """D-07: ``sent`` (N=M) / ``partial`` (0<N<M) / ``failed`` (N=0); M=0 is honestly sent."""
    if planned <= 0:
        return "sent"
    if delivered <= 0:
        return "failed"
    if delivered >= planned:
        return "sent"
    return "partial"
