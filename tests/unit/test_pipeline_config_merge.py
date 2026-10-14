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

import time

import pytest
import yaml

from backend.domain.errors import PipelineConfigValidationError
from backend.domain.pipeline_config import PipelineConfigError
from backend.infrastructure.yaml_pipeline_config_validator import (
    MAX_MERGE_DEPTH,
    MAX_MERGE_ENTRIES,
    MAX_PIPELINE_CONFIG_CHARS,
    PipelineConfigModel,
    YamlPipelineConfigValidator,
    _MERGE_TOO_BIG_MESSAGE,
    _OVER_CAP_MESSAGE,
    _StrictSafeLoader,
    _project,
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

VALID_KEY_LINES = (
    "template: lecture",
    "roles: [employee]",
    "language: ru",
    "max_chars: 4000",
)


def _merge_chain_lines(*, fanout: int, nesting: int) -> list[str]:
    """The side-key chain: a0 owns one key, every aN merges its child `fanout` times.

    The chain node therefore projects ``(fanout ** nesting, nesting + 1)`` — the shape
    that multiplies inside ``SafeConstructor.flatten_mapping``.
    """
    lines = ["a0: &a0 {k0: v0}"]
    for level in range(1, nesting + 1):
        sources = ", ".join([f"*a{level - 1}"] * fanout)
        lines.append(f"a{level}: &a{level} {{<<: [{sources}]}}")
    return lines


def _merge_bomb(*, fanout: int, nesting: int) -> str:
    """The side-key bomb: the chain plus the four required keys (no merge at the root)."""
    lines = _merge_chain_lines(fanout=fanout, nesting=nesting)
    lines.extend(VALID_KEY_LINES)
    return "\n".join(lines) + "\n"


def _root_anchored_bomb(*, fanout: int, nesting: int) -> str:
    """The same chain, but the document's own root mapping carries ``<<: *aN``."""
    lines = _merge_chain_lines(fanout=fanout, nesting=nesting)
    lines.append(f"<<: *a{nesting}")
    lines.extend(VALID_KEY_LINES)
    return "\n".join(lines) + "\n"


def _wide_merge_source(n: int) -> str:
    """A document whose root carries a single ``<<`` whose source owns exactly `n` keys."""
    keys = "\n".join(f"  k{i}: v{i}" for i in range(n))
    return f"<<: &w\n{keys}\n"


def _nested_merge_chain(fanout: int, levels: int) -> str:
    """Nested flow-mapping chain: four schema keys at the leaf, merge-only levels above.

    Every enclosing level merges its child exactly `fanout` times (one inline anchor plus
    `fanout - 1` aliases), so the chain projects ``(fanout ** levels * 4, levels + 1)``.
    `levels = 0` emits the bare four-key flow mapping.
    """
    expression = "{template: lecture, roles: [employee], language: ru, max_chars: 4000}"
    for level in range(levels):
        sources = [f"&chain{level} {expression}"] + [f"*chain{level}"] * (fanout - 1)
        expression = "{<<: [" + ", ".join(sources) + "]}"
    return expression + "\n"


# 2 ** 6 * 4 == 256 projected entries at depth 7 — the entries budget is INCLUSIVE.
EXACT_ENTRY_BUDGET = _nested_merge_chain(2, 6)
BOMB = _merge_bomb(fanout=3, nesting=13)
ROOT_ANCHORED_BOMB = _root_anchored_bomb(fanout=3, nesting=13)


def _errors(yaml_text: str) -> tuple[PipelineConfigError, ...]:
    validator = YamlPipelineConfigValidator()
    with pytest.raises(PipelineConfigValidationError) as exc_info:
        validator.validate(yaml_text)
    return exc_info.value.errors


def _projection(document: str) -> tuple[int, int]:
    return _project(yaml.compose(document, Loader=_StrictSafeLoader), {}, set())


MERGE_BOUND_ROW = (PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE),)


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


# --- Group 4: the merge-expansion bound (D-04/D-06) ----------------------------


@pytest.mark.parametrize("document", (BOMB, ROOT_ANCHORED_BOMB))
def test_merge_bomb_is_rejected_in_bounded_time(document: str) -> None:
    """PIPE-05: a tiny fan-out bomb is refused by the bound, loudly and fast."""
    # The reject can never be the size cap: the bomb is ~2.5% of MAX_PIPELINE_CONFIG_CHARS.
    assert len(document) < MAX_PIPELINE_CONFIG_CHARS

    start = time.perf_counter()
    errors = _errors(document)
    elapsed = time.perf_counter() - start

    assert errors == MERGE_BOUND_ROW
    assert errors[0].line is None
    assert _MERGE_TOO_BIG_MESSAGE != _OVER_CAP_MESSAGE
    # ~2 ms guarded; the unbounded cost at this size is ~1.5 s (minutes deeper).
    assert elapsed < 0.5


def test_merge_bound_boundaries() -> None:
    """PIPE-05: both bounds are inclusive at their limit and exclusive one step beyond."""
    assert MAX_MERGE_ENTRIES == 256
    assert MAX_MERGE_DEPTH == 8

    # Fan-out 3: 5 merge levels project (243, 6) — accepted; 6 levels project 729
    # entries — refused by the ENTRIES budget.
    shallow_wide = _merge_bomb(fanout=3, nesting=5)
    deep_wide = _merge_bomb(fanout=3, nesting=6)
    assert len(shallow_wide) < MAX_PIPELINE_CONFIG_CHARS
    assert len(deep_wide) < MAX_PIPELINE_CONFIG_CHARS
    yaml.load(shallow_wide, Loader=_StrictSafeLoader)
    assert _errors(deep_wide) == MERGE_BOUND_ROW

    # Fan-out 1: a pure merge chain stays at 1 projected entry per level, so only the
    # DEPTH bound can refuse it — 7 levels (depth 8) accepted, 8 levels (depth 9) refused.
    shallow_narrow = _merge_bomb(fanout=1, nesting=7)
    deep_narrow = _merge_bomb(fanout=1, nesting=8)
    assert len(shallow_narrow) < MAX_PIPELINE_CONFIG_CHARS
    assert len(deep_narrow) < MAX_PIPELINE_CONFIG_CHARS
    yaml.load(shallow_narrow, Loader=_StrictSafeLoader)
    assert _errors(deep_narrow) == MERGE_BOUND_ROW

    # Fan-out 2 at 8 levels is admissible on entries alone (exactly 256) but refused by
    # the depth bound (9) — proof that both bounds are load-bearing.
    assert _errors(_merge_bomb(fanout=2, nesting=8)) == MERGE_BOUND_ROW

    # Entries budget INCLUSIVE at exactly MAX_MERGE_ENTRIES: the four schema keys at the
    # leaf under six merge-only levels project (2 ** 6 * 4, 7) == (256, 7) and validate.
    assert len(EXACT_ENTRY_BUDGET) < MAX_PIPELINE_CONFIG_CHARS
    assert _projection(EXACT_ENTRY_BUDGET) == (MAX_MERGE_ENTRIES, 7)
    assert set(yaml.load(EXACT_ENTRY_BUDGET, Loader=_StrictSafeLoader)) == SCHEMA_KEYS
    YamlPipelineConfigValidator().validate(EXACT_ENTRY_BUDGET)

    # The next level computes 2 ** 7 * 4 == 512 entries at depth 8: refused before
    # `_project` can return them.
    over_budget = _nested_merge_chain(2, 7)
    assert len(over_budget) < MAX_PIPELINE_CONFIG_CHARS
    assert _errors(over_budget) == MERGE_BOUND_ROW

    # The same inclusivity on the flat axis: 256 own keys in one merge source load to a
    # 256-key mapping, 257 are refused.
    wide = _wide_merge_source(MAX_MERGE_ENTRIES)
    assert len(wide) < MAX_PIPELINE_CONFIG_CHARS
    assert _projection(wide) == (MAX_MERGE_ENTRIES, 2)
    assert len(yaml.load(wide, Loader=_StrictSafeLoader)) == MAX_MERGE_ENTRIES

    overflowing = _wide_merge_source(MAX_MERGE_ENTRIES + 1)
    assert len(overflowing) < MAX_PIPELINE_CONFIG_CHARS
    assert _errors(overflowing) == MERGE_BOUND_ROW


# --- cycle guard ---------------------------------------------------------------


def test_self_referential_merge_is_refused_not_hung() -> None:
    """The `stack` branch of `_project` fires before any expansion — never a hang/500."""
    start = time.perf_counter()
    errors = _errors(SELF_REFERENTIAL_DOC)
    elapsed = time.perf_counter() - start

    assert errors == MERGE_BOUND_ROW
    assert elapsed < 0.5
    # The divergence from the oracle is deliberate and pinned: SafeLoader silently
    # collapses this document to {"a": {}}, which is why it is NOT in ORACLE_ACCEPTED.
    assert yaml.safe_load(SELF_REFERENTIAL_DOC) == {"a": {}}
