---
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
reviewed: 2026-10-14T16:45:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
  - tests/unit/test_pipeline_config_merge.py
  - tests/unit/test_http_pipeline_config.py
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
---

# Phase 17: Code Review Report (re-review of the 17-03 fixes)

**Reviewed:** 2026-10-14T16:45:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Fresh adversarial review of the post-17-03 code (diff `e5251246..HEAD`, commits `04ac410`, `c7afe1b`, `9604645`). The prior findings of the last review (CR-01 merge-source duplicate leak, WR-01 nested-merge anchor holder, IN-01 alias over-match, IN-02 ruff, IN-03 flaky ceiling) are disposed and landed; their IDs are **not** reused here. All findings below are narrative (AI reviewer) findings — no structural pre-pass was supplied for this run. Finding IDs continue the previous numbering (`WR-02`, `IN-04`, `IN-05`) so they cannot be confused with the closed `CR-01`/`WR-01`/`IN-0x`.

Test/lint state reproduced locally: `61 passed` for the two test modules; `ruff check` is clean on the validator and on `tests/unit/test_pipeline_config_merge.py`.

### Invariants verified as still holding (negative results)

Each was probed by executing the real validator against purpose-built documents:

- **CR-01 closure (duplicate inside a merge source): no leak found.** Rejected with the exact reject row in all shapes probed: inline/anonymous source, sequence-element source, source that is only an anchor holder, source nested under a plain value, source inside a list element (`items: - <<: *b`), doubly-nested inline merges (`<<: {<<: *b}`), `<<: [&a {..}, &b {dup}]`, a 3-deep chain, source also used as a direct value (`tpl: &s …` + `<<: *s`), source reused as a value and a merge source, and a source resident inside a sequence *of* a sequence. Message text, `path=""`, and the 1-based `<key line>` all matched `PipelineConfigError(path="", message=f"found duplicate key ({key!r})", line=…)`; `ConstructorError` keeps both marks (context = mapping start, problem = duplicate key), so the mapping to the 400 row is unchanged — e.g. `<<: &b {language: ru, language: en}` → `line=1`; `outer: / inner: / <<: &b {… dup}` → `line=3`; `a: 1\na: 2` → `line=2`.
- **Reject contract not weakened / no over-reach.** `'<<': 1` quoted keys and `!!merge` explicit tags behave as before; distinct keys (`language`/`languages`) and same-key-across-two-sources documents are not flagged. Oracle agreement (`_StrictSafeLoader` vs `yaml.safe_load`) holds on the accepted merge corpus.
- **No new 500 path.** `_MergeExpansionTooLarge`, `ConstructorError`/`MarkedYAMLError`, `yaml.YAMLError`, and `RecursionError` raised from the new scan all land in the pre-existing parse-error clauses. A merge source whose key is a collection surfaces as PyYAML's own `MarkedYAMLError`, again caught.
- **CPU bound intact.** Single `_MERGE_TOO_BIG_MESSAGE` row in bounded time: root-anchored chain bomb 4 ms; 4800-fold repeated merge list of one source 91 ms; 300 distinct sources 32 ms; 257-wide source 13 ms; self-referential `a: &a {<<: *a}` 0.3 ms. Repeated sources are skipped after the first via the `_own_keys` marker, so the new scan is O(#pairs).
- **Untouched surface.** `PipelineConfigModel` (four keys, `extra="forbid"`), `MAX_PIPELINE_CONFIG_CHARS = 20000`, `Loader=_StrictSafeLoader` at both call sites, and `class _StrictSafeLoader(yaml.SafeLoader)` are unchanged by the diff.
- **D-09 tripwire.** `test_put_invalid_error_rows_are_verbatim_and_top_level` is byte-identical between the base commit and HEAD (comparison over the function plus its surrounding 30 lines).

## Warnings

### WR-02: `_merge_source_ids` treats sequences as opaque, so a holder referenced only by a merge inside a list still misses the D-07 teaching message

**File:** `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py:219-233` (guard at `:219`, `else: stack.append(value_node)` at `:233`)
**Issue:** The rewrite of `_anchor_holder_keys` walks the composed graph, but the walk only descends through mapping pairs: at `:219` any `current` that is not a `MappingNode` is skipped, so a `SequenceNode` popped off the stack is discarded and its elements are never inspected. Consequently a top-level key whose anchor is consumed only by a merge **nested inside a list** is not recognised as a merge source, and its `extra_forbidden` row keeps Pydantic's English `Extra inputs are not permitted` instead of `_EXTRA_ANCHOR_KEY_MESSAGE`. This is the residual of the very gap WR-01 fixed for mapping-nested merges, and it contradicts the new docstring at `:209` — "Values of non-merge pairs are pushed too, so a merge nested under any value is reached" — which is false for sequence values. Reproduced against the real validator:

```text
defaults: &c {template: lecture, roles: [employee], language: ru, max_chars: 4000}
items:
  - <<: *c

# _anchor_holder_keys(doc) -> set()                       # expected {'defaults'}
# rows: defaults -> 'Extra inputs are not permitted'      # expected Лишний ключ «defaults»: …
# items  -> 'Extra inputs are not permitted'              # correct (carries the merge, not a source)
```

The document is still rejected (no accept/security leak) — the impact is a missing teaching message for a shape an administrator can plausibly write.
**Fix:** Descend into sequences in the walk and let the `visited` set guard them too:

```python
while stack:
    current = stack.pop()
    if id(current) in visited:
        continue
    visited.add(id(current))
    if isinstance(current, SequenceNode):
        stack.extend(current.value)
        continue
    if not isinstance(current, MappingNode):
        continue
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
```

Also correct the docstring line at `:209` (mapping values are reached directly; sequence values are now descended). Add the regression gate in the same commit — a parametrised row alongside `NESTED_MERGE_ANCHOR_HOLDER_DOC` asserting `_anchor_holder_keys(...) == {"defaults"}` and `_EXTRA_ANCHOR_KEY_MESSAGE.format(key="defaults")` for the `defaults` row of the sequence shape above.

## Info

### IN-04: `tests/unit/test_http_pipeline_config.py` still fails `ruff check` (I001, UP017)

**File:** `tests/unit/test_http_pipeline_config.py:8` (import block), `:163` (`timezone.utc`)
**Issue:** `ruff check` reports `I001 Import block is un-sorted or un-formatted` and `UP017 Use `datetime.UTC` alias`. This is **pre-existing, not a 17-03 regression**: the base-commit copy of the file fails identically when linted from the same directory (verified). However, 17-03's advisory was a "ruff cleanup", and it did touch this file (the `PipelineConfigError` import at line 27), so the touched file remains the only non-clean one in the reviewed set. Note the merge test file's `I001`/`ISC004` were fixed.
**Fix:** Fold this file into the same cleanup: re-sort the import block (constants before classes inside the `backend.*` block) and use `datetime.UTC`.

### IN-05: duplicate *collection* keys are still not reported as duplicates (pre-existing, retained by the refactor)

**File:** `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py:163-165` (`except TypeError: continue` inside `_check_own_keys`)
**Issue:** `_check_own_keys` skips any key it cannot hash, so an explicitly repeated complex key (`? &k {a: 1}` … `? *k` … `? *k`) is never reported as a duplicate; it falls through to PyYAML's own `found unhashable key` `MarkedYAMLError`, i.e. an English parser message instead of the duplicate-reject message. The code is a verbatim move of the pre-17-03 `construct_mapping` scan, so this is not a regression — but the new merge-source call path inherits the same asymmetry, and the guarantee "duplicate keys are rejected with the same message everywhere" is not uniform for collection keys. Impact is low: such documents are still rejected (400), just with a different message.
**Fix:** Out of the 17-03 scope, but if the "one duplicate contract" is to be exact, detect the repeat structurally — key the `seen` set on `id(key_node)` (or a composed-node fingerprint) in addition to the hashable-value path — and raise the same `ConstructorError` whenever that identity recurs within one mapping.

---

_Reviewed: 2026-10-14T16:45:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
