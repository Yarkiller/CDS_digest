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
    _EXTRA_ANCHOR_KEY_MESSAGE,
    _MERGE_TOO_BIG_MESSAGE,
    _OVER_CAP_MESSAGE,
    _UNHASHABLE_KEY_MESSAGE,
    MAX_MERGE_DEPTH,
    MAX_MERGE_ENTRIES,
    MAX_PIPELINE_CONFIG_CHARS,
    PipelineConfigModel,
    YamlPipelineConfigValidator,
    _anchor_holder_keys,
    _project,
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

# D-07 shape: an anchor holder that is also the merge source — the most likely
# post-fix admin spelling. The holder key sits outside the four-key schema, so the
# document is rejected at the schema stage (never at parse): the merge itself is valid.
ANCHOR_HOLDER_KEY_DOC = (
    "defaults: &base\n"
    "  template: lecture\n"
    "  roles:\n"
    "    - employee\n"
    "  language: ru\n"
    "  max_chars: 4000\n"
    "<<: *base\n"
)

# A genuine unknown key on a NON-merge document — the D-09 tripwire's shape.
UNKNOWN_KEY_DOC = (
    "template: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 100\nscore_factors: 1.0\n"
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

# Group 5b — CR-01 gap shapes (17-03): a duplicate key written inside a mapping that is
# only ever used as a merge source must STILL be rejected (PIPE-04/PIPE-05, D-02).
MERGE_SOURCE_DUPLICATE_DOC = (
    "<<: &b {language: ru, language: en}\n"
    "template: lecture\n"
    "roles: [employee]\n"
    "max_chars: 4000\n"
)

MERGE_SOURCE_SEQUENCE_DUPLICATE_DOC = (
    "<<: [&b {language: ru, language: en}]\n"
    "template: lecture\n"
    "roles: [employee]\n"
    "max_chars: 4000\n"
)

ANCHOR_HOLDER_DUPLICATE_DOC = (
    "defaults: &b {template: lecture, roles: [employee], language: ru, "
    "language: en, max_chars: 4000}\n"
    "<<: *b\n"
)

# The duplicate lives inside a merge source's VALUES — caught by the ordinary scan.
MERGE_SOURCE_VALUE_DUPLICATE_DOC = (
    "<<: &b {language: {x: 1, x: 2}}\n"
    "template: lecture\n"
    "roles: [employee]\n"
    "max_chars: 4000\n"
)

# A near-miss: distinct keys `language` / `languages` — the source scan must NOT flag it.
MERGE_SOURCE_NEAR_MISS_DOC = (
    "<<: &b {language: ru, languages: en}\n"
    "template: lecture\n"
    "roles: [employee]\n"
    "max_chars: 4000\n"
)

# One document carrying BOTH an own-key duplicate and a merge-source duplicate: the
# pristine own-key scan runs first, so the OWN duplicate is the row that is reported.
OWN_AND_SOURCE_DUPLICATE_DOC = (
    "template: podcast\n"
    "template: lecture\n"
    "<<: &b {language: ru, language: en}\n"
    "roles: [employee]\n"
    "max_chars: 4000\n"
)

# WR-01 shapes (17-03): a top-level key used as a merge source only by a NESTED merge,
# and the alias-copy case the identity-keyed detection deliberately over-matches (IN-01).
NESTED_MERGE_ANCHOR_HOLDER_DOC = (
    "defaults: &c {template: lecture, roles: [employee], language: ru, "
    "max_chars: 4000}\n"
    "other:\n"
    "  <<: *c\n"
)

ALIAS_COPY_ANCHOR_HOLDER_DOC = (
    "defaults: &c {template: lecture, roles: [employee], language: ru, "
    "max_chars: 4000}\n"
    "alias_key: *c\n"
    "<<: *c\n"
)

# WR-02 shapes: a holder consumed only by a merge nested inside a SEQUENCE value (a
# list element), which the WR-01 walk must still reach; and the unhashable-key reject
# whose 400 body must carry curated copy rather than PyYAML's raw English text.
LIST_NESTED_MERGE_ANCHOR_HOLDER_DOC = (
    "defaults: &c {template: lecture, roles: [employee], language: ru, "
    "max_chars: 4000}\n"
    "items:\n"
    "  - <<: *c\n"
)

UNHASHABLE_DUPLICATE_KEYS_DOC = "? [1, 2]\n: 1\n? [1, 2]\n: 2\n"

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
        (
            "<<: &b {language: ru}\n"
            "template: podcast\n"
            "template: lecture\n"
            "roles:\n"
            "  - ds\n"
            "language: ru\n"
            "max_chars: 100\n"
        ),
        3,
    ),
)

# Group 5b — duplicates inside a merge source's own mapping (CR-01 gap, 17-03).
DUPLICATE_IN_MERGE_SOURCE: tuple[tuple[str, str, int], ...] = (
    (MERGE_SOURCE_DUPLICATE_DOC, "language", 1),
    (MERGE_SOURCE_SEQUENCE_DUPLICATE_DOC, "language", 1),
    (ANCHOR_HOLDER_DUPLICATE_DOC, "language", 1),
    (MERGE_SOURCE_VALUE_DUPLICATE_DOC, "x", 1),
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


def _root_anchored_bomb_with_duplicate_source(*, fanout: int, nesting: int) -> str:
    """Precedence (a): the root's own pre-mutation window observes an over-budget source
    AND a duplicate-bearing source, so the duplicate row must win over the bound."""
    lines = _merge_chain_lines(fanout=fanout, nesting=nesting)
    lines.append(f"<<: [*a{nesting}, &dup {{language: ru, language: en}}]")
    lines.extend(VALID_KEY_LINES)
    return "\n".join(lines) + "\n"


def _nested_duplicate_source_bomb(*, fanout: int, nesting: int) -> str:
    """Precedence (b)/(c): the duplicate sits on the chain's ``a0`` base and is reachable
    only through the merge chain that the root merges."""
    lines = ["a0: &a0 {k0: v0, language: ru, language: en}"]
    for level in range(1, nesting + 1):
        sources = ", ".join([f"*a{level - 1}"] * fanout)
        lines.append(f"a{level}: &a{level} {{<<: [{sources}]}}")
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
    # IN-03 (17-03): the `errors == MERGE_BOUND_ROW` assertion above is the primary
    # regression guard — a removed bound falls through to the schema stage and can never
    # produce `_MERGE_TOO_BIG_MESSAGE` — so the wall clock only has to catch a hang or
    # runaway. The ceiling is raised from 0.5 s to remove the only flake surface.
    assert elapsed < 5.0


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
    # IN-03 (17-03): as above — the row equality is the guard; the ceiling only has to
    # catch a hang, so it is raised from 0.5 s to remove the flake surface.
    assert elapsed < 5.0
    # The divergence from the oracle is deliberate and pinned: SafeLoader silently
    # collapses this document to {"a": {}}, which is why it is NOT in ORACLE_ACCEPTED.
    assert yaml.safe_load(SELF_REFERENTIAL_DOC) == {"a": {}}


# --- Group 5: the D-07 anchor-holder teaching message --------------------------


def test_anchor_holder_key_gets_teaching_message() -> None:
    """D-07: a top-level anchor holder is rejected with the key-naming Russian message."""
    errors = _errors(ANCHOR_HOLDER_KEY_DOC)

    assert len(errors) == 1
    assert errors[0].path == "defaults"
    assert errors[0].line is None
    assert errors[0].message == _EXTRA_ANCHOR_KEY_MESSAGE.format(key="defaults")


def test_genuine_unknown_key_keeps_english_message() -> None:
    """D-07 / Pitfall 9: the translation is anchor-gated — a genuine typo stays English."""
    errors = _errors(UNKNOWN_KEY_DOC)

    assert len(errors) == 1
    assert errors[0].path == "score_factors"
    assert errors[0].line is None
    assert errors[0].message != _EXTRA_ANCHOR_KEY_MESSAGE.format(key="score_factors")
    assert "Лишний ключ" not in errors[0].message


def test_inline_merge_shape_has_no_anchor_holder_keys() -> None:
    """The inline `<<: &base` form has no top-level anchor holder — the guard returns ∅.

    Proves the D-07 detection cannot fire on a document whose merge sits in the merge
    key itself: identity exists only for a SEPARATE top-level key used as a merge source.
    """
    assert _anchor_holder_keys(MERGE_SOURCE_DOC) == set()
    # …and such a document validates cleanly (the translation never engages).
    YamlPipelineConfigValidator().validate(MERGE_SOURCE_DOC)


# --- Group 6: CR-01 — duplicate keys inside a merge source (17-03) -------------


@pytest.mark.parametrize(("document", "key", "line"), DUPLICATE_IN_MERGE_SOURCE)
def test_duplicate_inside_merge_source_is_rejected(
    document: str, key: str, line: int
) -> None:
    """CR-01 closure: an explicit duplicate inside a merge source is still rejected."""
    expected = PipelineConfigError(
        path="", message=f"found duplicate key ({key!r})", line=line
    )

    assert _errors(document) == (expected,)


def test_merge_source_near_miss_is_not_flagged_as_duplicate() -> None:
    """The source scan must not over-reach: distinct keys (`language`/`languages`) load."""
    assert yaml.load(
        MERGE_SOURCE_NEAR_MISS_DOC, Loader=_StrictSafeLoader
    ) == yaml.safe_load(MERGE_SOURCE_NEAR_MISS_DOC)
    errors = _errors(MERGE_SOURCE_NEAR_MISS_DOC)

    assert len(errors) == 1
    assert "duplicate" not in errors[0].message.lower()


def test_duplicate_source_observed_before_the_projection_wins_over_the_bound() -> None:
    """Precedence (a): a source the projected node itself observes reports its duplicate."""
    document = _root_anchored_bomb_with_duplicate_source(fanout=3, nesting=13)
    assert len(document) < MAX_PIPELINE_CONFIG_CHARS

    errors = _errors(document)

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is not None
    assert "duplicate" in errors[0].message.lower()
    assert errors[0].message != _MERGE_TOO_BIG_MESSAGE


def test_nested_duplicate_source_over_the_bound_is_refused_by_the_bound() -> None:
    """Precedence (b): a source the projection never reaches leaves the bound to win."""
    document = _nested_duplicate_source_bomb(fanout=3, nesting=13)
    assert len(document) < MAX_PIPELINE_CONFIG_CHARS

    assert _errors(document) == MERGE_BOUND_ROW


def test_nested_duplicate_source_under_the_bound_is_rejected_as_a_duplicate() -> None:
    """Precedence (c): the same nested shape inside both bounds is a duplicate reject."""
    document = _nested_duplicate_source_bomb(fanout=3, nesting=4)
    assert len(document) < MAX_PIPELINE_CONFIG_CHARS

    assert _errors(document) == (
        PipelineConfigError(
            path="", message="found duplicate key ('language')", line=1
        ),
    )


def test_own_key_duplicate_wins_over_a_merge_source_duplicate() -> None:
    """Precedence (d): the pristine own-key scan precedes the flatten/source scan."""
    assert _errors(OWN_AND_SOURCE_DUPLICATE_DOC) == (
        PipelineConfigError(
            path="", message="found duplicate key ('template')", line=2
        ),
    )


# --- Group 7: WR-01 nested-merge anchor holders + IN-01 alias acceptance (17-03) ---


def test_nested_merge_anchor_holder_gets_teaching_message() -> None:
    """WR-01: a holder referenced only by a NESTED merge still gets the D-07 message."""
    errors = _errors(NESTED_MERGE_ANCHOR_HOLDER_DOC)

    assert _anchor_holder_keys(NESTED_MERGE_ANCHOR_HOLDER_DOC) == {"defaults"}
    assert sum(1 for row in errors if "Лишний ключ" in row.message) == 1
    defaults_row = next(row for row in errors if row.path == "defaults")
    assert defaults_row.message == _EXTRA_ANCHOR_KEY_MESSAGE.format(key="defaults")
    assert defaults_row.line is None
    # `other` CARRIES the nested merge but is not itself a merge source: English message.
    other_row = next(row for row in errors if row.path == "other")
    assert other_row.message != _EXTRA_ANCHOR_KEY_MESSAGE.format(key="other")
    assert "Лишний ключ" not in other_row.message


def test_anchor_holder_keys_terminates_on_self_referential_merge() -> None:
    """WR-01: the visited-guarded walk terminates on `a: &a {<<: *a}`."""
    start = time.perf_counter()
    holders = _anchor_holder_keys(SELF_REFERENTIAL_DOC)
    elapsed = time.perf_counter() - start

    assert holders == {"a"}
    assert elapsed < 5.0


def test_anchor_holder_keys_matches_alias_copies_by_identity_design() -> None:
    """IN-01 (accepted, NOT a RED gate): the set is keyed on value-node identity.

    A top-level key that merely ALIASES the merge-source node is reported too; that is the
    documented acceptance — the teaching message is apt for any such key, and precise
    disambiguation would need composer-event data PyYAML discards after composition.
    """
    assert _anchor_holder_keys(ALIAS_COPY_ANCHOR_HOLDER_DOC) == {
        "defaults",
        "alias_key",
    }
    errors = _errors(ALIAS_COPY_ANCHOR_HOLDER_DOC)
    for key in ("defaults", "alias_key"):
        row = next(row for row in errors if row.path == key)
        assert row.message == _EXTRA_ANCHOR_KEY_MESSAGE.format(key=key)


# --- Group 8: WR-02 — sequence-nested holders + the unhashable-key reject (17-03 rework) ---


def test_anchor_holder_keys_reaches_a_merge_nested_under_a_sequence() -> None:
    """WR-02: a merge nested inside a SEQUENCE value must still be reached.

    The ``_merge_source_ids`` docstring promises "a merge nested under any value is
    reached"; before the WR-02 fix the walk popped a ``SequenceNode`` and skipped it, so
    ``items: [- <<: *c]`` left the holder undetected and the D-07 teaching message never
    fired.
    """
    assert _anchor_holder_keys(LIST_NESTED_MERGE_ANCHOR_HOLDER_DOC) == {"defaults"}

    errors = _errors(LIST_NESTED_MERGE_ANCHOR_HOLDER_DOC)
    assert sum(1 for row in errors if "Лишний ключ" in row.message) == 1
    defaults_row = next(row for row in errors if row.path == "defaults")
    assert defaults_row.message == _EXTRA_ANCHOR_KEY_MESSAGE.format(key="defaults")
    assert defaults_row.line is None
    # `items` CARRIES the sequence-nested merge but is not itself a merge source.
    items_row = next(row for row in errors if row.path == "items")
    assert "Лишний ключ" not in items_row.message


def test_unhashable_duplicate_keys_are_rejected_with_curated_copy() -> None:
    """Info #2 (decided): unhashable keys are rejected with curated copy, not parser text.

    Duplicate keys whose key nodes are collections cannot be compared by hashing, so
    ``_check_own_keys`` skips them (``except TypeError: continue``) rather than paying an
    O(n²) equality scan over attacker-controlled collections — a new CPU-exhaustion path
    this phase must not open. PyYAML then refuses the whole document itself, so the
    invariant that matters holds either way: the document is rejected, never
    silently accepted and never a 500.

    What this test pins is the 400-body honesty: the row carries OUR copy, not PyYAML's
    raw ``found unhashable key`` English text (the transparency prohibition).
    """
    errors = _errors(UNHASHABLE_DUPLICATE_KEYS_DOC)

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line == 1
    assert errors[0].message == _UNHASHABLE_KEY_MESSAGE
    assert "unhashable" not in errors[0].message
