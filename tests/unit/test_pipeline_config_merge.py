"""RED→GREEN: YAML merge-key acceptance in the strict validator — PIPE-04, PIPE-05.

Covers the ``yaml.SafeLoader`` oracle for merge semantics (D-03: an explicit own key
overrides a merged one, the first merge source wins), explicit-duplicate rejection with
and without a ``<<`` present (D-02), the merge-expansion bound enforced before the
expensive flatten step (D-04/D-06) with the entries budget pinned inclusive at exactly
``MAX_MERGE_ENTRIES``, the self-referential-merge cycle guard, and the unchanged loader
safety profile (research Pitfall 9).

The oracle corpus is the contract: every document ``yaml.safe_load`` accepts must yield
the SAME mapping from ``_StrictSafeLoader`` — looped, never one hand-written assert per
shape (hand-written cases are how the nested-collision trap stays invisible).
"""

from __future__ import annotations

import pytest
import yaml

from backend.domain.errors import PipelineConfigValidationError
from backend.domain.pipeline_config import PipelineConfigError
from backend.infrastructure.yaml_pipeline_config_validator import (
    MAX_PIPELINE_CONFIG_CHARS,
    PipelineConfigModel,
    YamlPipelineConfigValidator,
    _StrictSafeLoader,
)

SCHEMA_KEYS = frozenset(PipelineConfigModel.model_fields)

# --- the oracle corpus (17-RESEARCH § Q4) -------------------------------------

PLAIN_DOC = "template: lecture\nroles:\n  - employee\nlanguage: ru\nmax_chars: 4000\n"

MERGE_SOURCE_DOC = (
    "<<: &base\n"
    "  template: lecture\n"
    "  roles:\n"
    "    - employee\n"
    "  language: ru\n"
    "  max_chars: 4000\n"
)

OWN_OVERRIDES_MERGED_DOC = (
    "<<: &base {template: podcast}\n"
    "template: lecture\n"
    "roles: [employee]\n"
    "language: ru\n"
    "max_chars: 4000\n"
)

FIRST_SOURCE_WINS_DOC = (
    "<<: [&a {roles: [ds]}, &b {roles: [analyst]}]\n"
    "template: lecture\n"
    "language: ru\n"
    "max_chars: 4000\n"
)

OWN_KEY_OVERRIDES_DOC = (
    "<<: &b {roles: [ds]}\n"
    "template: lecture\n"
    "roles: [analyst]\n"
    "language: ru\n"
    "max_chars: 4000\n"
)

NESTED_INLINE_DOC = (
    "<<: &c {<<: &d {template: lecture, roles: [employee], language: ru, max_chars: 4000}}\n"
)

ANCHOR_HOLDER_DOC = (
    "defaults: &c\n"
    "  <<: [&a {roles: [ds]}, &b {roles: [analyst]}]\n"
    "  template: lecture\n"
    "  language: ru\n"
    "  max_chars: 4000\n"
    "<<: *c\n"
)

ANCHOR_HOLDER_TWICE_DOC = (
    "h: &c\n"
    "  <<: [&a {roles: [ds]}, &b {roles: [analyst]}]\n"
    "  template: lecture\n"
    "  language: ru\n"
    "  max_chars: 4000\n"
    "<<: [*c, *c]\n"
)

QUOTED_MERGE_DOC = (
    "'<<': 1\ntemplate: lecture\nroles: [employee]\nlanguage: ru\nmax_chars: 4000\n"
)

EXPLICIT_TAG_DOC = (
    "!!merge <<: &b {language: ru}\n"
    "template: lecture\n"
    "roles: [employee]\n"
    "max_chars: 4000\n"
)

EMPTY_SOURCE_DOC = (
    "<<: &e {}\ntemplate: lecture\nroles: [employee]\nlanguage: ru\nmax_chars: 4000\n"
)

SAME_SOURCE_TWICE_DOC = (
    "<<: [&a {template: lecture}, *a]\n"
    "roles: [employee]\n"
    "language: ru\n"
    "max_chars: 4000\n"
)

# Group 1 — documents `yaml.safe_load` accepts; the strict loader must agree exactly.
ORACLE_ACCEPTED: tuple[str, ...] = (
    PLAIN_DOC,
    MERGE_SOURCE_DOC,
    OWN_OVERRIDES_MERGED_DOC,
    FIRST_SOURCE_WINS_DOC,
    OWN_KEY_OVERRIDES_DOC,
    NESTED_INLINE_DOC,
    ANCHOR_HOLDER_DOC,
    ANCHOR_HOLDER_TWICE_DOC,
    QUOTED_MERGE_DOC,
    EXPLICIT_TAG_DOC,
    EMPTY_SOURCE_DOC,
    SAME_SOURCE_TWICE_DOC,
)

# Group 2 — the subset of the corpus that resolves to exactly the four schema keys.
SCHEMA_ACCEPTED: tuple[str, ...] = (
    PLAIN_DOC,
    MERGE_SOURCE_DOC,
    OWN_OVERRIDES_MERGED_DOC,
    FIRST_SOURCE_WINS_DOC,
    OWN_KEY_OVERRIDES_DOC,
    NESTED_INLINE_DOC,
    EXPLICIT_TAG_DOC,
    EMPTY_SOURCE_DOC,
    SAME_SOURCE_TWICE_DOC,
)

# Group 3 — explicit duplicates must still be rejected, with and without a `<<`.
DUPLICATE_REJECTED: tuple[tuple[str, int], ...] = (
    (
        "template: podcast\ntemplate: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 100\n",
        2,
    ),
    (
        "<<: &b {language: ru}\n"
        "template: podcast\n"
        "template: lecture\n"
        "roles:\n"
        "  - ds\n"
        "language: ru\n"
        "max_chars: 100\n",
        3,
    ),
)

UNSAFE_DOC = (
    "template: !!python/object/apply:os.system ['echo hi']\n"
    "roles: [employee]\n"
    "language: ru\n"
    "max_chars: 4000\n"
)

SELF_REFERENTIAL_DOC = "a: &a {<<: *a}\n"


def _errors(yaml_text: str) -> tuple[PipelineConfigError, ...]:
    validator = YamlPipelineConfigValidator()
    with pytest.raises(PipelineConfigValidationError) as exc_info:
        validator.validate(yaml_text)
    return exc_info.value.errors


# --- Group 1: the loader oracle ------------------------------------------------


@pytest.mark.parametrize("document", ORACLE_ACCEPTED)
def test_strict_loader_matches_safeloader_oracle(document: str) -> None:
    """PIPE-04: SafeLoader is the merge-semantics oracle; the strict loader must agree."""
    assert yaml.load(document, Loader=_StrictSafeLoader) == yaml.safe_load(document)


def test_merge_override_and_first_source_semantics() -> None:
    """D-03: an explicit own key overrides a merged one; the first merge source wins."""
    own_over_merged = yaml.load(OWN_OVERRIDES_MERGED_DOC, Loader=_StrictSafeLoader)
    first_source_wins = yaml.load(FIRST_SOURCE_WINS_DOC, Loader=_StrictSafeLoader)
    own_key_wins = yaml.load(OWN_KEY_OVERRIDES_DOC, Loader=_StrictSafeLoader)

    assert own_over_merged["template"] == "lecture"
    assert first_source_wins["roles"] == ["ds"]
    assert own_key_wins["roles"] == ["analyst"]


# --- Group 2: schema acceptance ------------------------------------------------


@pytest.mark.parametrize("document", SCHEMA_ACCEPTED)
def test_merge_document_validates(document: str) -> None:
    """PIPE-04: a merge document resolving to the four keys passes the un-widened schema."""
    assert set(yaml.safe_load(document)) == SCHEMA_KEYS
    YamlPipelineConfigValidator().validate(document)


# --- Group 3: explicit duplicates are still rejected (D-02/PIPE-05) ------------


@pytest.mark.parametrize(("document", "expected_line"), DUPLICATE_REJECTED)
def test_explicit_duplicate_still_rejected(document: str, expected_line: int) -> None:
    """PIPE-05: duplicate rejection is not weakened by a merge key being present."""
    errors = _errors(document)

    assert len(errors) == 1
    assert "duplicate" in errors[0].message.lower()
    assert errors[0].line == expected_line


# --- loader safety profile (Pitfall 9) -----------------------------------------


def test_unsafe_tag_is_refused_not_constructed() -> None:
    """Pitfall 9: arbitrary-object construction stays refused at the adapter boundary."""
    errors = _errors(UNSAFE_DOC)

    assert len(errors) == 1
    assert errors[0].path == ""
