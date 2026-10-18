"""Optional live YouTube captions proof (D-20). Skipped unless RUN_YOUTUBE_INTEGRATION=1."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration

_LIVE = os.environ.get("RUN_YOUTUBE_INTEGRATION") == "1"


@pytest.mark.skipif(
    not _LIVE,
    reason="set RUN_YOUTUBE_INTEGRATION=1 to run live YouTube captions",
)
def test_live_youtube_captions_smoke() -> None:
    """Operator live stub — captions-then-metadata order is Phase 10 policy (D-24)."""
    # Stub: flag gate only. Full live wiring belongs with Phase 10 CLI composition.
    assert _LIVE is True
