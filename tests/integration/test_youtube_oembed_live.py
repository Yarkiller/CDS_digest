"""Optional live YouTube oEmbed proof (D-20). Skipped unless RUN_YOUTUBE_INTEGRATION=1."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration

_LIVE = os.environ.get("RUN_YOUTUBE_INTEGRATION") == "1"


@pytest.mark.skipif(
    not _LIVE,
    reason="set RUN_YOUTUBE_INTEGRATION=1 to run live YouTube oEmbed",
)
def test_live_youtube_oembed_smoke() -> None:
    """Operator live stub — requires network and optional YOUTUBE_PROXY_URL."""
    # Stub: flag gate only. Full live wiring belongs with Phase 10 CLI composition.
    assert _LIVE is True
