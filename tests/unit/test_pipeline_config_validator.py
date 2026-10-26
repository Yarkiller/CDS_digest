"""RED→GREEN: strict YAML + schema validator adapter — PIPE-02, D-01..D-07.

Covers syntax errors, duplicate keys (no silent last-wins), non-string top-level
keys, empty / multi-document streams, unknown keys (extra=forbid), wrong
type / missing required / empty roles, a valid document, the length cap, the
fixed schema key set (PIPE-03 secret-key guard), and the structured error shape.
"""

from __future__ import annotations

import sys

import pytest

from backend.domain.errors import PipelineConfigValidationError
from backend.domain.pipeline_config import PipelineConfigError
from backend.infrastructure.yaml_pipeline_config_validator import (
    MAX_PIPELINE_CONFIG_CHARS,
    PipelineConfigModel,
    YamlPipelineConfigValidator,
    _TOO_DEEP_MESSAGE,
    _UNREADABLE_MESSAGE,
)

VALID_DOC = "template: lecture\nroles:\n  - employee\nlanguage: ru\nmax_chars: 4000\n"


def _errors(yaml_text: str) -> tuple[PipelineConfigError, ...]:
    validator = YamlPipelineConfigValidator()
    with pytest.raises(PipelineConfigValidationError) as exc_info:
        validator.validate(yaml_text)
    return exc_info.value.errors


# --- 1. syntax -----------------------------------------------------------------


def test_syntax_error_maps_to_one_error_with_one_based_line() -> None:
    """RED→GREEN: a scanner error on line 1 → one error with path '' and line 1."""
    errors = _errors("@invalid\n")

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line == 1
    assert errors[0].message


def test_syntax_error_line_equals_problem_mark_plus_one() -> None:
    """RED→GREEN: the reported line is the 1-based parser problem mark."""
    errors = _errors("template: lecture\nroles: [employee\nlanguage: ru\n")

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is not None
    assert errors[0].line >= 2


# --- 2. duplicate keys ---------------------------------------------------------


def test_duplicate_top_level_key_is_rejected_not_last_wins() -> None:
    """RED→GREEN: SafeLoader last-wins is replaced by a strict duplicate reject."""
    errors = _errors(
        "template: podcast\ntemplate: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 100\n"
    )

    assert len(errors) == 1
    assert "duplicate" in errors[0].message.lower()
    assert errors[0].line == 2


# --- 3. non-string top-level keys ---------------------------------------------


def test_non_string_top_level_key_is_rejected() -> None:
    """RED→GREEN: `1: value` → path '' with the Russian object-with-text-keys message."""
    errors = _errors("1: value\n")

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is None
    assert errors[0].message == "Ожидается объект с текстовыми ключами"


# --- 4. empty / multi-document -------------------------------------------------


def test_empty_document_is_rejected_without_attribute_error() -> None:
    """RED→GREEN: an empty document (None) → structured error, never AttributeError."""
    errors = _errors("")

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is None
    assert errors[0].message == "Ожидается объект с текстовыми ключами"


def test_multi_document_stream_is_rejected_with_a_line() -> None:
    """RED→GREEN: a multi-document stream → one structured syntax error with a line."""
    errors = _errors("template: lecture\n---\ntemplate: podcast\n")

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is not None
    assert errors[0].message


# --- 5. unknown key ------------------------------------------------------------


def test_unknown_key_is_rejected_by_extra_forbid() -> None:
    """RED→GREEN: `score_factors` is unknown → path 'score_factors', line None (D-06)."""
    errors = _errors(
        "template: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 100\nscore_factors: 1.0\n"
    )

    assert len(errors) == 1
    assert errors[0].path == "score_factors"
    assert errors[0].line is None


# --- 6. type / required / min-length -------------------------------------------


def test_wrong_type_missing_required_and_empty_roles_map_to_dotted_paths() -> None:
    """RED→GREEN: one error per field with its dotted path and no line."""
    errors = _errors("template: 5\nroles: []\nmax_chars: 5\n")

    assert sorted(error.path for error in errors) == ["language", "roles", "template"]
    assert all(error.line is None for error in errors)
    assert all(error.message for error in errors)


def test_empty_language_is_rejected() -> None:
    """RED→GREEN: an empty `language` string fails min_length=1."""
    errors = _errors("template: lecture\nroles:\n  - ds\nlanguage: ''\nmax_chars: 100\n")

    assert len(errors) == 1
    assert errors[0].path == "language"


def test_non_positive_max_chars_is_rejected() -> None:
    """RED→GREEN: `max_chars: 0` fails gt=0."""
    errors = _errors("template: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 0\n")

    assert len(errors) == 1
    assert errors[0].path == "max_chars"


# --- 7. valid document ---------------------------------------------------------


def test_valid_document_validates_without_raising() -> None:
    """RED→GREEN: the documented 4-key document is accepted."""
    YamlPipelineConfigValidator().validate(VALID_DOC)


# --- 10. length cap ------------------------------------------------------------


def test_over_cap_document_is_rejected_before_parse() -> None:
    """RED→GREEN: an over-cap document is rejected by the cap, never silently accepted."""
    padding = "# " + ("x" * MAX_PIPELINE_CONFIG_CHARS) + "\n"
    document = VALID_DOC + padding
    assert len(document) > MAX_PIPELINE_CONFIG_CHARS

    errors = _errors(document)

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is None
    assert "размер" in errors[0].message.lower()


# --- 11. schema key set (PIPE-03) ---------------------------------------------


def test_schema_exposes_only_documented_non_secret_keys() -> None:
    """PIPE-03: the config document schema exposes exactly the four non-secret keys."""
    assert set(PipelineConfigModel.model_fields.keys()) == {
        "template",
        "roles",
        "language",
        "max_chars",
    }


# --- error payload shape -------------------------------------------------------


def test_error_to_dict_omits_line_when_none_and_includes_when_set() -> None:
    """D-05: `to_dict()` omits `line` when None and includes it when set."""
    assert PipelineConfigError(path="p", message="m").to_dict() == {
        "path": "p",
        "message": "m",
    }
    assert PipelineConfigError(path="p", message="m", line=3).to_dict() == {
        "path": "p",
        "message": "m",
        "line": 3,
    }


# --- 12. deep-nesting robustness (WR-02) --------------------------------------


def test_deeply_nested_flow_document_is_rejected_not_recursion_error() -> None:
    """RED→GREEN WR-02: nested flow brackets (under the cap) → structured error.

    Before the fix the parser raises an unhandled ``RecursionError`` (HTTP 500);
    strict validation must instead map it to a ``PipelineConfigValidationError``.
    The depth is derived from the live recursion limit (plus a margin) so the test
    keeps exercising the overflow branch even if the limit is raised.
    """
    depth = sys.getrecursionlimit() + 500
    document = ("[" * depth) + ("]" * depth)

    assert len(document) <= MAX_PIPELINE_CONFIG_CHARS

    errors = _errors(document)

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is None
    assert errors[0].message == _TOO_DEEP_MESSAGE


# --- 13. unreadable characters (CR-01) ----------------------------------------


def test_unreadable_control_char_document_is_rejected_not_unmarked_yaml_error() -> None:
    """RED→GREEN CR-01: a control char (< cap) raises a bare ``yaml.YAMLError``.

    ``yaml.reader.ReaderError`` is a ``yaml.YAMLError`` but not a
    ``MarkedYAMLError``; before the fix it escapes ``validate()`` entirely
    (unhandled HTTP 500). It must map to a structured reject instead.
    """
    document = "template: lecture\nroles:\n  - ds\nlanguage: \x00ru\nmax_chars: 100\n"
    assert len(document) <= MAX_PIPELINE_CONFIG_CHARS

    errors = _errors(document)

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is None
    assert errors[0].message == _UNREADABLE_MESSAGE

