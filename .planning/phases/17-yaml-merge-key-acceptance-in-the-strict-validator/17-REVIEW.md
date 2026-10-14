---
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
reviewed: 2026-10-14T12:30:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
  - tests/unit/test_http_pipeline_config.py
  - tests/unit/test_pipeline_config_merge.py
findings:
  critical: 1
  warning: 1
  info: 3
  total: 5
status: issues_found
---

# Phase 17: Code Review Report

Adversarial review at `standard` depth of the YAML merge-key work (PIPE-04/PIPE-05, tasks 17-01/17-02). The suite is green locally (48 passed) and I probed the six failure hypotheses from the brief by executing the validator against purpose-built documents (evidence below each finding). Conclusions on the specific probes:

- **`_project` bypass via pre-flattened merge sources (Q1): disproven.** `flatten_mapping` snapshots and calls `_project` *before* `super().flatten_mapping` mutates `node.value` (lines 118–122), and `super`'s recursive source-flattening goes through the same override (`self.flatten_mapping`), so every node whose `node.value` is mutated is projected first; nodes without a merge tag are never mutated. No ordering path lets `_project` read a flattened node.
- **`stack.discard` skipped on exception (Q2): not exploitable.** `_project` raises only for a cycle or an over-budget node, both of which abort the whole `yaml.load`; `yaml.load` constructs a fresh `_StrictSafeLoader` per call, so a partially-populated `_memo`/`stack` never survives into another validation.
- **Depth/entries accounting for non-`MappingNode` sources (Q3): no bypass.** A scalar/sequence-element source is not counted, but PyYAML's own `flatten_mapping` then raises `ConstructorError` ("expected a mapping or list of mappings for merging"), so such documents are rejected regardless; every accepted shape matched `yaml.safe_load`.
- **`except` ordering (Q5): correct.** `_MergeExpansionTooLarge(Exception)` is not a subclass of `MarkedYAMLError`/`RecursionError`/`YAMLError`, so the last `except` (lines 243–248) is the only one that can catch it; a merge bomb returns the intended `{"path": "", "message": _MERGE_TOO_BIG_MESSAGE}` row.
- **Nested-mapping duplicates (Q6): handled.** `note: {a: 1, a: 2}` is rejected (`line 5`); duplicates introduced by merging still resolve last-wins/override and are not rejected.
- **Duplicate keys inside a merge *source* (Q6, uncovered variant): NOT handled — see CR-01.**

## Critical Issues

### CR-01: Duplicate keys inside a merge source are silently accepted

**File:** `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py:118-142`
**Issue:** Duplicate-key rejection only ever sees a node's *own* pristine keys — `flatten_mapping` snapshots `_own_keys` for the node carrying the merge (lines 118–122) and `construct_mapping` scans `self._own_keys.get(id(node), node.value)` for that same node (line 127). A mapping node that is used **only** as a merge source is never passed to `construct_mapping` — PyYAML copies its raw pairs into the parent via `merge.extend(value_node.value)` after flattening — so the duplicate scan never runs on it. The result is that an explicitly duplicated key inside a merge source is accepted with last-wins, while the identical duplicate written anywhere else (or inside an anchor-holder that is also a top-level value) is rejected. This contradicts the module docstring ("SafeLoader that rejects duplicate mapping keys instead of silently last-wins") and the phase's own MUST-NOT ("an explicit duplicate key keeps producing the same structured 400 … with or without a merge key present"). Reproduced against the real validator:

```text
# ACCEPTED (WRONG) — duplicate 'language' lives in the anonymous merge source
<<: &b {language: ru, language: en}
template: lecture
roles: [employee]
max_chars: 4000
# -> YamlPipelineConfigValidator().validate(...) returns None (no error)

# REJECTED (correct) — same duplicate inside a source that is also a top-level value
defaults: &b {template: lecture, roles: [employee], language: ru, language: en, max_chars: 4000}
<<: *b
# -> CR-01 guard fires: [{'path': '', 'message': "found duplicate key ('language')", 'line': 1}]

# sequence-element sources leak the same way
<<: [&b {language: ru, language: en}]
# -> ACCEPTED
```

The leak is confined to a source mapping's own key set; nested duplicates *inside a source's values* are still caught (`<<: &b {language: {x: 1, x: 2}}` → rejected).
**Fix:** Snapshot and duplicate-check every merge-source `MappingNode`'s own keys at the same pre-mutation window used for the parent. Factor the scan out of `construct_mapping` and invoke it when the source is observed in `flatten_mapping`, before `super()` mutates it:

```python
def _check_own_keys(self, key_pairs, node: MappingNode, deep: bool = False) -> None:
    seen: set[Any] = set()
    for key_node, _value_node in key_pairs:
        if key_node.tag == _MERGE_TAG:
            continue
        key = self.construct_object(key_node, deep=deep)
        try:
            hash(key)
        except TypeError:
            continue
        if key in seen:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"found duplicate key ({key!r})", key_node.start_mark,
            )
        seen.add(key)

def flatten_mapping(self, node: MappingNode) -> None:
    if isinstance(node, MappingNode) and id(node) not in self._checked:
        self._checked.add(id(node))
        has_merge = any(k.tag == _MERGE_TAG for k, _ in node.value)
        if has_merge:
            self._own_keys[id(node)] = list(node.value)
            for key_node, value_node in node.value:
                if key_node.tag != _MERGE_TAG:
                    continue
                sources = value_node.value if isinstance(value_node, SequenceNode) else [value_node]
                for source in sources:
                    if isinstance(source, MappingNode) and id(source) not in self._own_keys:
                        self._own_keys[id(source)] = list(source.value)  # pristine, pre-mutation
                        self._check_own_keys(self._own_keys[id(source)], source)
            _project(node, self._memo, set())
    return super().flatten_mapping(node)
```

Rejecting a duplicate *within one mapping* preserves override semantics for keys supplied by a source vs. own keys (D-03); it does not affect `SAME_SOURCE_TWICE_DOC` or the override/first-source corpus rows.

## Warnings

### WR-01: `_anchor_holder_keys` misses anchor holders referenced only by a nested merge

**File:** `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py:190-204`
**Issue:** The helper collects merge-source node ids by iterating only `root.value` (lines 191–196). A top-level key that is used as a merge source solely by a *nested* merge is therefore not recognised, so its `extra_forbidden` row keeps Pydantic's English `"Extra inputs are not permitted"` instead of the D-07 teaching message. The element design (17-02-PLAN) describes the helper as collecting "the ids of every node used as a merge source", and the module docstring says "whose value node is used as a merge source" without a top-level restriction, so this is an implementation/doc mismatch, not an intentional bound. Reproduced:

```text
defaults: &c {template: lecture, roles: [employee], language: ru, max_chars: 4000}
other:
  <<: *c
# _anchor_holder_keys(...) -> set()
# errors: defaults -> "Extra inputs are not permitted"  (expected the Russian teaching message)
```

**Fix:** Walk the composed graph recursively (rather than only `root.value`) to collect ids of every node used as a merge value at any depth, then keep matching top-level non-schema keys against that set:

```python
def _merge_source_ids(node) -> set[int]:
    ids: set[int] = set()
    if not isinstance(node, MappingNode):
        return ids
    for key_node, value_node in node.value:
        if key_node.tag != _MERGE_TAG:
            continue
        sources = value_node.value if isinstance(value_node, SequenceNode) else [value_node]
        for source in sources:
            ids.add(id(source))
            ids |= _merge_source_ids(source)  # descend into nested merges too
    return ids
```

## Info

### IN-01: `_anchor_holder_keys` over-matches alias copies of the merge-source node

**File:** `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py:197-204`
**Issue:** The return set is keyed on node identity of the *value*, so any top-level key that aliases the same mapping as the merge source is flagged as an anchor holder — even though it did not declare an anchor. `defaults: &c {…}` + `alias_key: *c` + `<<: *c` yields `{'defaults', 'alias_key'}`, and `alias_key` receives the teaching message. The message is still roughly apt (the key exists only via the anchor), so impact is low, but the detection is broader than "the anchor declaration site".
**Fix:** If exactness is wanted, distinguish the anchor-definition occurrence from alias occurrences (e.g. via composer events or the `&`-marked source span) rather than by bare value-node identity; otherwise document the alias-copy case as accepted behaviour.

### IN-02: New test file fails `ruff check` (I001, ISC004)

**File:** `tests/unit/test_pipeline_config_merge.py:15,174`
**Issue:** `.\.venv\Scripts\python.exe -m ruff check tests/unit/test_pipeline_config_merge.py` reports `I001 Import block is un-sorted or un-formatted` (line 15) and `ISC004 Unparenthesized implicit string concatenation in collection` (line 174). Both are introduced by this phase. (`tests/unit/test_http_pipeline_config.py` already failed `I001`/`UP017` at the phase base `c9606c0`, so those are pre-existing, not phase regressions.)
**Fix:** Run `ruff check --fix` on the new file (parenthesise the implicitly concatenated string in `DUPLICATE_REJECTED[1][0]`).

### IN-03: Wall-clock timing assertions make two tests load-sensitive

**File:** `tests/unit/test_pipeline_config_merge.py:341,406`
**Issue:** `test_merge_bomb_is_rejected_in_bounded_time` asserts `elapsed < 0.5` and `test_self_referential_merge_is_refused_not_hung` asserts `elapsed < 0.5`. The measured cost is ~2 ms, so the margin is large, but a hard wall-clock threshold is still a load-sensitive assertion that can flake on a saturated CI runner. The behavioural guarantee (a structured reject row) is already asserted independently, so the timing assertion is the only flake surface.
**Fix:** Keep the reject assertions and either drop the timing checks or raise the threshold substantially (the regression they guard against is ~1.5 s+, so e.g. `< 5.0` still catches it without CI flakiness).

---

_Reviewed: 2026-10-14T12:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
