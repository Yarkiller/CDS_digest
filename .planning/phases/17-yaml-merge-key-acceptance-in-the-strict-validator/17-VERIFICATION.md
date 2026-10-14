---
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
verified: 2026-10-14T12:25:00Z
status: gaps_found
score: 13/14 must-haves verified
covered_files:
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-01-PLAN.md
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-01-SUMMARY.md
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-02-PLAN.md
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-02-SUMMARY.md
  - backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
  - tests/unit/test_http_pipeline_config.py
  - tests/unit/test_pipeline_config_merge.py
covered_digest: "v2:sha256:2b7721da9c39241d17114101cfbaf52e29646f0c81c7aadf55993cddd5e55d4e"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "A document with a duplicated explicit key is still rejected with the same top-level structured 400 {errors:[…]} and zero writes, with and without a `<<` present (PIPE-04/PIPE-05; ROADMAP criterion 2; plan 17-01 must_haves truth 8; plan prohibition 'MUST NOT weaken duplicate-key rejection')."
    status: partial
    reason: "Duplicate-key rejection IS weakened for documents whose duplicate lives in a merge source's own mapping. `<<: &b {language: ru, language: en}` (and the sequence-source form `<<: [&b {language: ru, language: en}]`) is accepted with last-wins instead of producing the structured 400. The duplicate scan in `construct_mapping` iterates `self._own_keys.get(id(node), node.value)` for the node that CARRIES the merge; a mapping node used only as a merge source is never passed to `construct_mapping` (PyYAML splices its raw pairs into the parent via `merge.extend(value_node.value)`), so its own duplicate keys are never scanned. Before this phase such documents were rejected (cryptically, via the merge-tag constructor error), so this is a genuine behavioural weakening introduced by the phase, and it contradicts both the phase goal ('without weakening duplicate-key rejection'), PIPE-05 ('provably not weakened') and the module docstring ('rejects duplicate mapping keys instead of silently last-wins'). Independently reproduced against the real validator, not taken from the review."
    artifacts:
      - path: backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
        issue: "lines 124-144 — `construct_mapping` scans only the pristine own-key snapshot of the node that carries the merge, so duplicates inside a merge source's own mapping are never checked; the source's `MappingNode` is never scanned when it is observed in `flatten_mapping` (lines 118-122)."
    missing:
      - "Snapshot every merge-source `MappingNode`'s own keys at the same pre-mutation window used for the parent (in `flatten_mapping` / a `_merge_source_ids` walk) and run the duplicate scan over each source's pristine keys before `super().flatten_mapping(node)`."
      - "A RED test pinning `<<: &b {language: ru, language: en}` and `<<: [&b {language: ru, language: en}]` → exactly one `found duplicate key ('language')` row (path \"\", line present), added to `DUPLICATE_REJECTED` in tests/unit/test_pipeline_config_merge.py."
      - "Adjust the module docstring claim only if the behaviour is deliberately not adopted; otherwise the docstring already states the intended contract."
---

# Phase 17: YAML merge-key acceptance in the strict validator Verification Report

**Phase Goal:** The strict pipeline-config validator accepts a valid YAML merge-key (`<<`) document and persists it, without weakening duplicate-key rejection and without opening a CPU-exhaustion path.
**Verified:** 2026-10-14T12:25:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | A valid `<<` merge document loads to a mapping identical to `yaml.safe_load` (12-row oracle corpus) and passes the un-widened four-key schema | ✓ VERIFIED | `test_strict_loader_matches_safeloader_oracle` (12 rows) + `test_merge_document_validates` (9 rows) pass; 64-test phase run green |
| 2 | A key supplied by a merge source AND explicitly by the document resolves to the explicit value (override, not collision); in a merge sequence the FIRST source wins | ✓ VERIFIED | `test_merge_override_and_first_source_semantics` passes; `OWN_OVERRIDES_MERGED_DOC`/`FIRST_SOURCE_WINS_DOC`/`OWN_KEY_OVERRIDES_DOC` in the oracle corpus |
| 3 | A merge source contributing zero keys (`<<: *empty`) is accepted; missing required keys are reported by the schema, not the loader | ✓ VERIFIED | `EMPTY_SOURCE_DOC` in `ORACLE_ACCEPTED` + `SCHEMA_ACCEPTED`; both parametrized cases pass |
| 4 | An admin can PUT a merge-key config → 200 → persist once → later GET returns the identical yaml | ✓ VERIFIED | `test_put_merge_document_round_trips` passes: PUT 200, `save_count == 1`, GET returns identical text |
| 5 | A document with a duplicated explicit key is still rejected with the same structured 400 and zero writes, **with and without a `<<` present** | ✗ FAILED | Own-key duplicates (with and without `<<`) and duplicates inside a top-level anchor holder ARE rejected; a duplicate inside a merge source's own mapping is ACCEPTED with last-wins — see CR-01 gap. `<<: &b {language: ru, language: en}` → `validate()` returns `None` |
| 6 | A high-fan-out merge document is refused by the expansion bound with the structured 400, in bounded time, with zero writes, never a 500 | ✓ VERIFIED | `test_merge_bomb_is_rejected_in_bounded_time` (side-key + root-anchored) + `test_put_merge_bomb_returns_400_and_writes_nothing` pass; row `{path:"", message:_MERGE_TOO_BIG_MESSAGE}`, `save_count == 0`, well under the 0.5 s ceiling |
| 7 | Both bounds are inclusive at their limit and exclusive one beyond (256 entries / depth 8 accepted; 257 / depth 9 refused), yielding exactly one structured row | ✓ VERIFIED | `test_merge_bound_boundaries` passes: `_project(EXACT_ENTRY_BUDGET) == (256, 7)`, `_wide_merge_source(256)` loads to a 256-key mapping, the +1 successors are each refused |
| 8 | A document exceeding BOTH bounds still yields exactly ONE error row | ✓ VERIFIED | `BOMB` (fan-out 3, nesting 13) exceeds both bounds; `errors == MERGE_BOUND_ROW` (a 1-tuple) in `test_merge_bomb_is_rejected_in_bounded_time` |
| 9 | A document containing no merge key is never charged against the merge budget | ✓ VERIFIED | The projection runs only when a merge key is present (`flatten_mapping` guard); plain four-key doc accepted (probe run) |
| 10 | A document asking the parser to construct an arbitrary Python object is still refused; `_StrictSafeLoader` stays a `yaml.SafeLoader` subclass and `Loader=` is unchanged | ✓ VERIFIED | `test_unsafe_tag_is_refused_not_constructed` passes; `issubclass(_StrictSafeLoader, yaml.SafeLoader) == True` (probe); no `safe_load`/`FullLoader`/`UnsafeLoader` in the adapter |
| 11 | The merge fix and the bound ship together; the four-key `extra="forbid"` schema still governs; the structured-body contract is unchanged | ✓ VERIFIED | One `plan_head_before..after` diff carries both; `PipelineConfigModel`/`MAX_PIPELINE_CONFIG_CHARS`/route unchanged; `git diff -G test_put_invalid_error_rows_are_verbatim_and_top_level c9606c0..HEAD` is empty (tripwire byte-identical); `web/` untouched |
| 12 | A top-level anchor-holder key (`defaults: &base` + `<<: *base`) is rejected with the Russian teaching message naming the offending key | ✓ VERIFIED | `test_anchor_holder_key_gets_teaching_message` + `test_put_anchor_holder_key_returns_400_with_teaching_message` pass; `path == "defaults"`, `line is None` |
| 13 | A genuine unknown key keeps Pydantic's English `extra_forbidden` message with its own key as path and no `line` | ✓ VERIFIED | `test_genuine_unknown_key_keeps_english_message` + `test_unknown_key_is_rejected_by_extra_forbid` pass unchanged |
| 14 | The anchor-holder row rides the unchanged `{errors:[…]}` envelope with zero writes; the detection never fires on a document without a merge key and never turns a genuine typo into an anchor lecture | ✓ VERIFIED | `test_inline_merge_shape_has_no_anchor_holder_keys` (`_anchor_holder_keys(MERGE_SOURCE_DOC) == set()`), HTTP test asserts `save_count == 0`, no `"detail"` key; detection is gated on composed-graph anchor identity |

**Score:** 13/14 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` | `_MERGE_TAG`, `MAX_MERGE_DEPTH`, `MAX_MERGE_ENTRIES`, `_MERGE_TOO_BIG_MESSAGE`, `_MergeExpansionTooLarge`, `_project`, loader `__init__`/`flatten_mapping`/`construct_mapping`, `except` clause, `_EXTRA_ANCHOR_KEY_MESSAGE`, `_anchor_holder_keys` | ✓ VERIFIED | All present and substantive (lines 33-99, 102-144, 173-204, 210-281); wired into `validate()` and the route; no stub/debt markers |
| `tests/unit/test_pipeline_config_merge.py` | Oracle corpus, schema-accept corpus, duplicate-reject corpus, bomb + boundary pins, cycle guard, safety-profile guard, D-07 tests | ✓ VERIFIED | 32 tests, all pass; new file |
| `tests/unit/test_http_pipeline_config.py` | +3 tests on the real-validator HTTP harness; D-09 tripwire preserved | ✓ VERIFIED | 16 tests pass; round-trip, bomb zero-write, anchor-holder envelope; tripwire source byte-identical |
| `web/src/` | No change attributable to this phase (D-08) | ✓ VERIFIED | `git diff --name-only c9606c0..HEAD -- web/` empty |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `tests/unit/test_pipeline_config_merge.py` | adapter | imports `_StrictSafeLoader`, `_project`, `_MERGE_TOO_BIG_MESSAGE`, `_OVER_CAP_MESSAGE`, `_anchor_holder_keys`, `_EXTRA_ANCHOR_KEY_MESSAGE` | ✓ WIRED | Import block lines 24-36; all resolved |
| `_StrictSafeLoader.flatten_mapping` | `yaml.SafeConstructor.flatten_mapping` | `return super().flatten_mapping(node)` after snapshot+bound | ✓ WIRED | line 122; bookkeeping precedes the in-place `node.value` mutation |
| adapter | `backend/domain/pipeline_config.py` | bound raises `PipelineConfigValidationError` carrying `PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE)` | ✓ WIRED | lines 245-248; `line` omitted as designed |
| `tests/unit/test_http_pipeline_config.py` | `backend/.../routes/admin.py` | `_real_validator_admin_env()` drives the real validator through PUT/GET `/admin/pipeline/config` | ✓ WIRED | tests at lines 197, 387, 401 pass with `save_count`/envelope assertions |
| `_anchor_holder_keys` | `PipelineConfigModel.model_fields` | allow-list read from the schema (A5) | ✓ WIRED | line 203; no second copy of the four keys |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `test_put_merge_document_round_trips` | `get.json()["yaml"]` | `InMemoryPipelineConfigRepository` written by the real validator | Yes | ✓ FLOWING |

_No UI/rendered-data artifacts in this phase; Level 4 is limited to the persist→read-back path._

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase 17 suites | `.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_merge.py tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -q` | `64 passed` | ✓ PASS |
| Full workspace suite (run once) | `.venv\Scripts\python.exe -m pytest -q` | `802 passed, 1 warning` | ✓ PASS |
| Merge-source duplicate (CR-01) | `.venv\Scripts\python.exe tmp_verify17_cr01.py` | `<<: &b {language: ru, language: en}` → `ACCEPTED`; `yaml.safe_load` → `language: 'en'` (last-wins); the sequence-source form also `ACCEPTED` | ✗ FAIL |
| Loader hierarchy / unsafe tag | same probe | `issubclass(_StrictSafeLoader, SafeLoader) == True`; `!!python/object/apply` refused with one row, `path == ""` | ✓ PASS |
| Lint on the new test file | `.venv\Scripts\python.exe -m ruff check tests/unit/test_pipeline_config_merge.py` | 2 errors (I001, ISC004) — no CI workflow in repo, advisory only | ✗ FAIL (non-blocking) |

### Probe Execution

Step 7c: SKIPPED — no `scripts/*/tests/probe-*.sh` exist and this is not a migration/tooling phase; no probe is declared in either PLAN or SUMMARY.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| PIPE-04 | 17-01, 17-02 | Accept a valid YAML merge-key document and persist it, **while still rejecting duplicate explicit keys** with the same structured 400 and zero writes | ⚠️ PARTIAL | Acceptance + persist + read-back verified (truths 1-4); duplicate rejection verified for own-key/holder duplicates but **FAILS for a duplicate inside a merge source** (truth 5 / CR-01) |
| PIPE-05 | 17-01, 17-02 | Merge expansion is bounded (breach → structured 400) and **duplicate-key rejection is provably not weakened** | ⚠️ PARTIAL | Bound fully verified (truths 6-9, 11); "not weakened" is contradicted by CR-01 |

No orphaned requirements: `REQUIREMENTS.md` maps exactly `PIPE-04` and `PIPE-05` to Phase 17, and both appear in both plans' `requirements:` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| adapter, both test files | — | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` | none | No debt markers in any phase-modified file |
| `tests/unit/test_pipeline_config_merge.py` | 15, 174 | `ruff` I001 (import order) + ISC004 (implicit concat) | ℹ️ Info | New lint debt; no `.github/workflows` and no pre-commit hook in the repo, so not build-blocking |
| `tests/unit/test_pipeline_config_merge.py` | 341, 406 | wall-clock `elapsed < 0.5` assertions | ℹ️ Info | ~2 ms measured vs 0.5 s threshold (>100× margin); only flake surface on a saturated runner |

### Human Verification Required

None beyond the blocking gap. Every truth that is behaviour-dependent (the expansion bound, the cycle guard, the duplicate scan) is exercised by a passing named test, so `behavior_unverified` is 0.

### Gaps Summary

One blocking gap. The phase's headline promise — "without weakening duplicate-key rejection" (ROADMAP goal, PIPE-05, and the test-tier prohibition in `17-01-PLAN.md`) — does not hold for a reachable document shape.

**CR-01 (BLOCKER, confirmed independently).** A duplicate key inside a merge source's own mapping is silently accepted with last-wins:

```text
<<: &b {language: ru, language: en}          -> ACCEPTED (yaml.safe_load -> language: 'en')
<<: [&b {language: ru, language: en}]        -> ACCEPTED
template: podcast / template: lecture        -> REJECTED "found duplicate key ('template')" line 2
duplicate inside a top-level anchor holder   -> REJECTED "found duplicate key ('language')" line 1
```

Root cause: `construct_mapping` scans `self._own_keys.get(id(node), node.value)` only for the node that carries the merge; a `MappingNode` used purely as a merge source is never passed to `construct_mapping` (its raw pairs are spliced into the parent by `SafeConstructor.flatten_mapping`'s `merge.extend(value_node.value)`), so its own duplicate keys are never examined. The phase introduced this weakening: before the fix, any `<<` document was rejected outright (merge-tag constructor error).

**Judgement:** this is a must-have gap, not an out-of-scope edge case. The plans' own must-have truth 8 says a duplicated explicit key is still rejected "with and without a `<<` present", and the prohibition "MUST NOT weaken duplicate-key rejection" is test-tier, i.e. hold open — the invariant is violated for a reachable input. It also contradicts the adapter's own docstring ("rejects duplicate mapping keys instead of silently last-wins"). Fix is small and confined to the same pre-mutation window already used for the parent (snapshot + scan each merge source's pristine keys).

**Non-blocking findings (from 17-REVIEW.md, not phase-goal failures):**
- WR-01 — `_anchor_holder_keys` walks only `root.value`, so an anchor holder referenced solely by a *nested* merge (`defaults: &c {…}` + `other: {<<: *c}`) keeps the English message. Reproduced: `_anchor_holder_keys(...) == set()`. The must-have truth 12 covers only the top-level `defaults: &base` + `<<: *base` shape, which passes, so this does not fail a must-have; it is a UX inconsistency in the D-07 nicety.
- IN-01/IN-02/IN-03 — alias over-match, the two `ruff` errors, and the wall-clock assertions (see Anti-Patterns). All non-blocking.

---

_Verified: 2026-10-14T12:25:00Z_
_Verifier: Claude (gsd-verifier)_
