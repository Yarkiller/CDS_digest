"""RED→GREEN: redaction denylist + exact-value safety net (D-07, D-08, D-09)."""

from __future__ import annotations

import pytest

from ingestion_service.diagnostics.redaction import (
    MAX_VALUE_LENGTH,
    REDACTED,
    SecretRegistry,
    sanitize,
)

SECRET = "sk-secret-key-1234567890"


def test_secret_registry_masks_exact_value() -> None:
    registry = SecretRegistry([SECRET])
    masked = registry.mask(f"key={SECRET} done")
    assert SECRET not in masked
    assert REDACTED in masked


def test_secret_registry_ignores_empty_and_short_values() -> None:
    registry = SecretRegistry(["", "abc"])
    assert registry.mask("abc") == "abc"


def test_sanitize_masks_plain_assignment_forms() -> None:
    """W-3: behavioral denylist coverage — the plain assignment shapes mask."""
    assert sanitize("api_key=abcdef123456") == REDACTED
    assert sanitize("token=abcdef123456") == REDACTED


@pytest.mark.parametrize(
    "raw",
    [
        "Cookie: sessionid=abc123secret",
        "Bearer abc123-token-value",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "https://user:p4ssw0rd@proxy.example.com:8080",
    ],
)
def test_sanitize_masks_denylist_credentials(raw: str) -> None:
    masked = sanitize(raw)
    assert raw not in masked
    assert REDACTED in masked


def test_sanitize_strips_control_chars_and_caps_length() -> None:
    stripped = sanitize("a\nb\x1bc\x7fd")
    assert "\n" not in stripped
    assert "\x1b" not in stripped
    assert "\x7f" not in stripped
    assert stripped == "abcd"

    overlong = "x" * (MAX_VALUE_LENGTH + 500)
    assert len(sanitize(overlong)) == MAX_VALUE_LENGTH


def test_sanitize_never_raises_and_masks_on_violation() -> None:
    """D-09: a denylist violation is masked, never raised or aborted."""
    result = sanitize("authorization: Bearer leaky-token")
    assert isinstance(result, str)
    assert "leaky-token" not in result
    assert REDACTED in result


@pytest.mark.parametrize(
    "raw",
    [
        "secret_key=abcdef123456",
        "access_token=abcdef123456",
        "client_secret=abcdef123456",
        "refresh_token=abcdef123456",
        "private_key=abcdef123456",
        "auth=abcdef123456",
    ],
)
def test_sanitize_masks_underscore_compound_credentials(raw: str) -> None:
    """SC2 / D-07 / D-08: underscore-compound names mask to exactly [redacted]."""
    assert sanitize(raw) == REDACTED


def test_sanitize_underscore_compound_positive_control() -> None:
    """The plain assignment shapes still mask (no regression from the fix)."""
    assert sanitize("api_key=abcdef123456") == REDACTED
    assert sanitize("token=abcdef123456") == REDACTED
    assert sanitize("secret=abcdef123456") == REDACTED


def test_sanitize_masks_control_char_split_bearer() -> None:
    """T-15-08: a control-char-split token masks fully — no tail fragment survives."""
    masked = sanitize("Bearer abc\ndef_secondhalf")
    assert "def_secondhalf" not in masked
    assert REDACTED in masked
