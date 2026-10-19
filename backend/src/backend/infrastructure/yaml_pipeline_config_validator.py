"""Strict YAML + schema validator adapter — PIPE-02 (D-01..D-07, T-16-05/06/09).

This is the ONLY module that parses YAML. It implements the
``PipelineConfigValidator`` port with a strict ``SafeLoader`` subclass (syntax +
duplicate keys + non-string top-level keys + empty/multi-document) plus a fixed
Pydantic ``extra="forbid"`` schema (keys/types/required). Parse and schema
failures are mapped at this adapter boundary into a
``PipelineConfigValidationError`` carrying ``PipelineConfigError(path, line?, message)``
entries — never a silent accept, never an execution path.

``yaml`` and ``pydantic`` must not be imported from ``domain/`` or
``application/use_cases/`` (architecture.mdc); this file lives in infrastructure.
"""

from __future__ import annotations

from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode, SequenceNode

from backend.domain.errors import PipelineConfigValidationError
from backend.domain.pipeline_config import PipelineConfigError

# Server-side cap rejected before parse (T-16-07: YAML alias / oversized document DoS).
MAX_PIPELINE_CONFIG_CHARS = 20000

_OVER_CAP_MESSAGE = "Документ конфига превышает допустимый размер"
_NOT_A_TEXT_OBJECT_MESSAGE = "Ожидается объект с текстовыми ключами"
_TOO_DEEP_MESSAGE = "Документ YAML имеет слишком глубокую вложенность"
_UNREADABLE_MESSAGE = "Документ содержит недопустимые символы"

# PyYAML exposes no named constant for the merge tag (it uses the bare literal in
# ``SafeConstructor.flatten_mapping``), so it is a local module constant (D-02).
_MERGE_TAG = "tag:yaml.org,2002:merge"
# Merge-expansion bound (D-04): merge nesting and the flattened-entry budget. Both are
# checked BEFORE ``SafeConstructor.flatten_mapping`` materialises anything, because
# ``merge.extend(...)`` multiplies the node list (k^depth) inside a 20 000-char document.
MAX_MERGE_DEPTH = 8
MAX_MERGE_ENTRIES = 256
# D-06: a dedicated message — a merge bomb is ~500 characters, so claiming it exceeds
# the size cap would be false.
_MERGE_TOO_BIG_MESSAGE = "Документ содержит слияние (merge), превышающее допустимый размер"
# D-07: an extra top-level key used purely as an anchor holder gets a message that names
# the key and teaches the merge form — the most likely admin mistake after the merge fix.
# ``{key}`` is interpolated with the offending top-level key name.
_EXTRA_ANCHOR_KEY_MESSAGE = "Лишний ключ «{key}»: якоря нужно объявлять в самом `<<`"
# Info #2 (17-03 rework): a key node that is a collection cannot be hashed, so PyYAML
# refuses the document itself; the reject row must carry our copy, not PyYAML's raw
# English ``found unhashable key`` text (the phase's transparency prohibition).
_UNHASHABLE_KEY_MESSAGE = "Ключом объекта не может быть список или объект"


class _MergeExpansionTooLarge(Exception):
    """A merge would expand past the bound (D-04).

    Deliberately NOT a ``ConstructorError``: that is a ``MarkedYAMLError`` and the
    ``MarkedYAMLError`` branch of ``validate()`` would attach a ``line``, breaking the
    sibling ``{"path": "", "message": …}`` envelope.
    """


def _project(
    node: MappingNode,
    memo: dict[int, tuple[int, int]],
    stack: set[int],
) -> tuple[int, int]:
    """Return ``(flattened entries, merge depth)`` for a mapping node, over budget raising.

    Memoised by ``id(node)`` so it is O(#nodes), and ``stack`` guards a self-referential
    merge. Called at the head of ``flatten_mapping``, i.e. while the node graph is still
    pristine — the only point where the cost of the expansion it prevents has not been
    paid (D-04).
    """
    node_id = id(node)
    if node_id in memo:
        return memo[node_id]
    if node_id in stack:
        raise _MergeExpansionTooLarge

    stack.add(node_id)
    entries = 0
    depth = 0
    for key_node, value_node in node.value:
        if key_node.tag == _MERGE_TAG:
            sources = value_node.value if isinstance(value_node, SequenceNode) else [value_node]
            for source in sources:
                if isinstance(source, MappingNode):
                    source_entries, source_depth = _project(source, memo, stack)
                    entries += source_entries
                    depth = max(depth, source_depth)
        else:
            entries += 1
    stack.discard(node_id)

    result = (entries, 1 + depth)
    if result[0] > MAX_MERGE_ENTRIES or result[1] > MAX_MERGE_DEPTH:
        raise _MergeExpansionTooLarge
    memo[node_id] = result
    return result


class _StrictSafeLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys instead of silently last-wins."""

    def __init__(self, stream: Any) -> None:
        super().__init__(stream)
        self._own_keys: dict[int, list[Any]] = {}
        self._checked: set[int] = set()
        self._memo: dict[int, tuple[int, int]] = {}

    def flatten_mapping(self, node: MappingNode) -> None:
        """Snapshot the pristine own keys and enforce the bound before ``super()``.

        ``SafeConstructor.flatten_mapping`` mutates ``node.value`` in place
        (``node.value = merge + node.value``), so this is the only window in which the
        pre-merge own keys are observable — and the only point before the expansion.
        """
        if isinstance(node, MappingNode) and id(node) not in self._checked:
            self._checked.add(id(node))
            if any(key_node.tag == _MERGE_TAG for key_node, _ in node.value):
                self._own_keys[id(node)] = list(node.value)
                # CR-01: a mapping used ONLY as a merge source is never passed through
                # ``construct_mapping`` (PyYAML splices its raw pairs into the parent via
                # ``merge.extend(value_node.value)``), so its own duplicate keys must be
                # scanned here, still pristine (before ``super().flatten_mapping``).
                for key_node, value_node in node.value:
                    if key_node.tag != _MERGE_TAG:
                        continue
                    sources = (
                        value_node.value
                        if isinstance(value_node, SequenceNode)
                        else [value_node]
                    )
                    for source in sources:
                        if (
                            isinstance(source, MappingNode)
                            and id(source) not in self._own_keys
                        ):
                            self._own_keys[id(source)] = list(source.value)
                            self._check_own_keys(self._own_keys[id(source)], source)
                _project(node, self._memo, set())
        return super().flatten_mapping(node)

    def _check_own_keys(
        self, key_pairs: list[Any], node: MappingNode, deep: bool = False
    ) -> None:
        """Raise ``ConstructorError`` on the second occurrence of a key in ``key_pairs``.

        Factored out of ``construct_mapping`` (17-03) so the same verbatim scan runs for a
        node's own pristine keys AND for every mapping used as a merge source.
        """
        seen: set[Any] = set()
        for key_node, _value_node in key_pairs:
            if key_node.tag == _MERGE_TAG:
                # D-02: skip by tag — a quoted ``'<<'`` is an ordinary string key.
                continue
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError:
                continue
            if key in seen:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key ({key!r})",
                    key_node.start_mark,
                )
            seen.add(key)

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        if isinstance(node, MappingNode):
            self._check_own_keys(
                self._own_keys.get(id(node), node.value), node, deep=deep
            )
        return super().construct_mapping(node, deep=deep)


class PipelineConfigModel(BaseModel):
    """Fixed, documented pipeline-config schema — unknown keys forbidden (D-01/D-02/D-06).

    The four-key set deliberately excludes any secret/credential key (PIPE-03) and
    any ``score_factors`` weight (D-01; ADUX-06 stays on the honest-empty path).
    """

    model_config = ConfigDict(extra="forbid")

    template: Literal["lecture", "podcast"]
    roles: list[Literal["employee", "analyst", "ds"]] = Field(min_length=1)
    language: str = Field(min_length=1)
    max_chars: int = Field(gt=0)


def _loc_to_dot_sep(loc: tuple[Any, ...]) -> str:
    """Render a Pydantic ``loc`` tuple as a dotted/indexed path (e.g. ``roles[0]``)."""
    path = ""
    for index, part in enumerate(loc):
        if isinstance(part, str):
            path += ("." if index > 0 else "") + part
        else:
            path += f"[{part}]"
    return path


def _merge_source_ids(node: Any) -> set[int]:
    """Ids of every mapping node used as a merge source at any depth (WR-01/WR-02).

    Iterative with a ``visited`` node-id guard, so a self-referential merge
    (``a: &a {<<: *a}``) terminates in O(#nodes) rather than recursing. Values of
    non-merge pairs are pushed too, and a pushed ``SequenceNode`` is descended into, so a
    merge nested under any value — including inside a list element (``items: [- <<: *c]``)
    — is reached (WR-02).
    """
    ids: set[int] = set()
    if not isinstance(node, MappingNode):
        return ids

    stack: list[Any] = [node]
    visited: set[int] = set()
    while stack:
        current = stack.pop()
        if id(current) in visited:
            continue
        if isinstance(current, SequenceNode):
            # WR-02: a merge can sit inside a sequence value, so descend into it.
            visited.add(id(current))
            stack.extend(current.value)
            continue
        if not isinstance(current, MappingNode):
            continue
        visited.add(id(current))
        for key_node, value_node in current.value:
            if key_node.tag == _MERGE_TAG:
                sources = (
                    value_node.value
                    if isinstance(value_node, SequenceNode)
                    else [value_node]
                )
                for source in sources:
                    ids.add(id(source))
                    stack.append(source)
            else:
                stack.append(value_node)
    return ids


def _anchor_holder_keys(yaml_text: str) -> set[str]:
    """Top-level keys (outside the schema) whose value node is used as a merge source.

    Anchor identity survives only in the composed node graph (after construction the
    merged pairs are copies and the aliases are shared node objects), so the document is
    re-composed. The call is guarded (D-05): a malformed or too-deep document returns the
    empty set instead of becoming a new 500 path, and the helper runs only on the reject
    path when an ``extra_forbidden`` row exists. The allowed-key set is read from
    ``PipelineConfigModel.model_fields`` so the four keys are never copied here (A5).
    """
    try:
        root = yaml.compose(yaml_text, Loader=_StrictSafeLoader)
    except (yaml.YAMLError, RecursionError):
        return set()
    if not isinstance(root, MappingNode):
        return set()

    merge_source_ids = _merge_source_ids(root)

    # IN-01 (accepted): the set is keyed on value-node identity, so a top-level key that
    # merely ALIASES a merge source is reported too. The teaching message is apt for any
    # such key, and precise disambiguation would need composer-event data that PyYAML
    # does not retain after composition — pinned by
    # test_anchor_holder_keys_matches_alias_copies_by_identity_design.
    return {
        key_node.value
        for key_node, value_node in root.value
        if key_node.tag != _MERGE_TAG
        and id(value_node) in merge_source_ids
        and isinstance(key_node.value, str)
        and key_node.value not in PipelineConfigModel.model_fields
    }


class YamlPipelineConfigValidator:
    """Server-authoritative validator implementing the ``PipelineConfigValidator`` port."""

    def validate(self, yaml_text: str) -> None:
        if len(yaml_text) > MAX_PIPELINE_CONFIG_CHARS:
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_OVER_CAP_MESSAGE),)
            )

        try:
            data = yaml.load(yaml_text, Loader=_StrictSafeLoader)
        except yaml.MarkedYAMLError as exc:
            mark = exc.problem_mark
            raise PipelineConfigValidationError(
                (
                    PipelineConfigError(
                        path="",
                        line=(mark.line + 1) if mark is not None else None,
                        message=(
                            # Info #2: a collection key node cannot be hashed, so PyYAML
                            # refuses the document itself. Curate the copy here rather than
                            # echoing its raw English text; duplicate detection among
                            # unhashable keys is deliberately NOT attempted (it would need
                            # an O(n²) equality scan over attacker-controlled collections —
                            # a new CPU-exhaustion path this phase must not open).
                            _UNHASHABLE_KEY_MESSAGE
                            if exc.problem == "found unhashable key"
                            else str(exc.problem or exc)
                        ),
                    ),
                )
            ) from exc
        except RecursionError as exc:
            # WR-02: deeply nested flow collections (< cap) overflow the parser's
            # recursive scanner. Map it to a structured reject at this boundary so
            # the route returns a 400 {"errors":[...]} instead of an unhandled 500.
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_TOO_DEEP_MESSAGE),)
            ) from exc
        except yaml.YAMLError as exc:
            # CR-01: unmarked YAML errors (e.g. yaml.reader.ReaderError for
            # non-printable/control characters) are yaml.YAMLError but not
            # MarkedYAMLError. Map them to a structured reject too, so user-supplied
            # text never surfaces as an unhandled 500.
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_UNREADABLE_MESSAGE),)
            ) from exc
        except _MergeExpansionTooLarge as exc:
            # D-04/D-05: the bound rejects a merge bomb before the flatten step, and
            # rides the existing parse-error boundary so it cannot become a 500 path.
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE),)
            ) from exc

        if not isinstance(data, dict) or not all(isinstance(key, str) for key in data):
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_NOT_A_TEXT_OBJECT_MESSAGE),)
            )

        try:
            PipelineConfigModel.model_validate(data)
        except ValidationError as exc:
            schema_errors = exc.errors()
            # D-07: only pay for the composed-graph re-read when an extra key exists, and
            # only translate a row whose key is genuinely a top-level merge anchor holder.
            anchor_holders = (
                _anchor_holder_keys(yaml_text)
                if any(error["type"] == "extra_forbidden" for error in schema_errors)
                else set()
            )
            raise PipelineConfigValidationError(
                tuple(
                    PipelineConfigError(
                        path=_loc_to_dot_sep(error["loc"]),
                        message=(
                            _EXTRA_ANCHOR_KEY_MESSAGE.format(key=error["loc"][0])
                            if error["type"] == "extra_forbidden"
                            and error["loc"]
                            and error["loc"][0] in anchor_holders
                            else error["msg"]
                        ),
                    )
                    for error in schema_errors
                )
            ) from exc
