---
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
plan: 03
subsystem: backend-adapter
tags: [yaml, pyyaml, pydantic, duplicate-keys, merge-keys, error-messages, fastapi, pytest]

# Dependency graph
requires:
  - phase: 17-01
    provides: "the merge-key parse-path fix (skip by tag + pristine own-key snapshot), the pre-flatten expansion bound, and the green D-09 reject-envelope tripwire this gap plan builds on"
  - phase: 17-02
    provides: "the D-07 anchor-holder teaching message and the guarded `_anchor_holder_keys` helper this plan's WR-01 fix repairs"
provides:
  - "_StrictSafeLoader._check_own_keys(key_pairs, node, deep) — the pristine own-key duplicate scan factored out verbatim and called from BOTH construct_mapping and flatten_mapping (CR-01)"
  - "the merge-source snapshot + scan loop inside flatten_mapping, running before super().flatten_mapping and before _project (CR-01)"
  - "_merge_source_ids(node) — an iterative, visited-guarded walk collecting merge-source node ids at ANY depth (WR-01)"
  - "a recursive _anchor_holder_keys that reaches anchor holders referenced only by a nested merge (WR-01)"
affects: [17-verify-work, 18, 19, 22]

# Actuals (#2632) — pairs with the plan's `estimate` (tokens 18000 / raw 36000 / tasks 3).
# `tokens` is chars/4 over the realized diff of the plan range, on the SAME scale the
# estimate used. `commits` is MEASURED: git rev-list --count plan_head_before..HEAD.
actuals:
  tokens: 5106
  tasks: 3
  commits: 3

plan_head_before: e5251246c3e3c31e748e9b0c050c6b4ce4171bb7
plan_head_after: 96046456e62240a1e48f603e72bec77798758594

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "The pristine-window rule generalised: EVERY mapping observed in flatten_mapping (the merge carrier AND each of its sources) is snapshotted and scanned before super() mutates the graph"
    - "Precedence by construction, not by convention: the source scan runs inside the same pre-mutation window, so the four duplicate-vs-bound / own-key-vs-source orderings are pinned by tests rather than left incidental"
    - "Iterative + visited-guarded graph walks for anything reachable from untrusted text, so a self-referential merge terminates in O(#nodes)"

key-files:
  created: []
  modified:
    - backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
    - tests/unit/test_pipeline_config_merge.py
    - tests/unit/test_http_pipeline_config.py

key-decisions:
  - "The merge-source scan runs BEFORE _project inside the existing pre-mutation window, so a duplicate the projected node itself observes is reported first and an over-budget document still yields exactly one row — the precedence is measured and pinned in all four directions"
  - "_check_own_keys is a verbatim extraction of the existing loop (same ConstructorError context string, argument order, message text and both marks), so the D-09 tripwire and test_explicit_duplicate_still_rejected stay byte-identical"
  - "The source scan only ADDS rejection — the four-key extra=\"forbid\" schema, MAX_PIPELINE_CONFIG_CHARS, the Loader= argument and the yaml.SafeLoader subclass hierarchy are untouched (D-01)"
  - "WR-01 is fixed by an iterative _merge_source_ids walk rather than recursion, and _anchor_holder_keys keeps its except (yaml.YAMLError, RecursionError) -> set() guard and its reject-path-only invocation (D-05)"
  - "IN-01 (alias-copy over-match) is accepted and pinned by a characterisation test: precise disambiguation would need composer-event data PyYAML discards after composition, for a message nicety on a key whose teaching message is apt anyway"

patterns-established:
  - "Snapshot before mutate: any node whose keys are compared for duplicates must be snapshotted in the pre-mutation window, because PyYAML splices raw pairs and later copies lose the original key list"
  - "A graph walk over untrusted YAML text is iterative with a visited node-id set"

requirements-completed: [PIPE-04, PIPE-05]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "A duplicate key written inside a merge source's own mapping — mapping source or merge-sequence element — is rejected with exactly one row {path: \"\", message: \"found duplicate key ('language')\", line: 1}"
    requirement: PIPE-04
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_duplicate_inside_merge_source_is_rejected"
        status: pass
    human_judgment: false
  - id: D2
    description: "A duplicate nested inside a merge source's VALUES is still caught (found duplicate key ('x'))"
    requirement: PIPE-04
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_duplicate_inside_merge_source_is_rejected[MERGE_SOURCE_VALUE_DUPLICATE_DOC]"
        status: pass
    human_judgment: false
  - id: D3
    description: "A near-miss source with distinct keys (language / languages) is NOT flagged as a duplicate; the strict loader still equals the yaml.safe_load oracle"
    requirement: PIPE-04
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_merge_source_near_miss_is_not_flagged_as_duplicate"
        status: pass
    human_judgment: false
  - id: D4
    description: "Precedence (a): a duplicate source the projected node's own window observes wins over the merge bound (duplicate row, real line, never _MERGE_TOO_BIG_MESSAGE)"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_duplicate_source_observed_before_the_projection_wins_over_the_bound"
        status: pass
    human_judgment: false
  - id: D5
    description: "Precedence (b): an over-budget document whose duplicate source the projection never reaches yields exactly ONE merge-bound row, never two"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_nested_duplicate_source_over_the_bound_is_refused_by_the_bound"
        status: pass
    human_judgment: false
  - id: D6
    description: "Precedence (c): the same nested shape inside both bounds is rejected as a duplicate (found duplicate key ('language'), line 1) — the scan reaches NESTED sources"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_nested_duplicate_source_under_the_bound_is_rejected_as_a_duplicate"
        status: pass
    human_judgment: false
  - id: D7
    description: "Precedence (d): a document carrying BOTH an own-key duplicate and a merge-source duplicate reports the OWN-key duplicate (template, line 2)"
    requirement: PIPE-04
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_own_key_duplicate_wins_over_a_merge_source_duplicate"
        status: pass
    human_judgment: false
  - id: D8
    description: "The merge-source duplicate crosses the unchanged top-level 400 {errors:[…]} envelope through the real validator with save_count == 0 and the real line present"
    requirement: PIPE-05
    verification:
      - kind: integration
        ref: "tests/unit/test_http_pipeline_config.py#test_put_merge_source_duplicate_returns_400_and_writes_nothing"
        status: pass
    human_judgment: false
  - id: D9
    description: "A top-level key used as a merge source only by a NESTED merge gets the D-07 teaching message on its own path, while the key that merely CARRIES the nested merge keeps Pydantic's English message"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_nested_merge_anchor_holder_gets_teaching_message"
        status: pass
    human_judgment: false
  - id: D10
    description: "The anchor-holder walk terminates on a self-referential merge (a: &a {<<: *a} -> {\"a\"}) and still returns the empty set for the inline <<: &base shape"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_anchor_holder_keys_terminates_on_self_referential_merge + #test_inline_merge_shape_has_no_anchor_holder_keys"
        status: pass
    human_judgment: false
  - id: D11
    description: "IN-01 (accepted): the identity-keyed anchor set also reports a top-level key that merely aliases the merge source; both rows carry their own interpolated teaching message — a tested, documented acceptance"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_anchor_holder_keys_matches_alias_copies_by_identity_design"
        status: pass
    human_judgment: false
  - id: D12
    description: "The D-09 reject-envelope tripwire is preserved byte-identically and green; the four-key extra=forbid schema, MAX_PIPELINE_CONFIG_CHARS, the Loader= argument and the loader class hierarchy are untouched"
    requirement: PIPE-04
    verification:
      - kind: integration
        ref: "tests/unit/test_http_pipeline_config.py#test_put_invalid_error_rows_are_verbatim_and_top_level (source unchanged; the module diff is additions only)"
        status: pass
    human_judgment: false

# Metrics
duration: 8min
completed: 2026-10-14
status: complete
---

# Phase 17 Plan 03: Close the merge-source duplicate-key gap Summary

**A duplicate key written inside a mapping that is only ever used as a merge source is now rejected with the same single structured row as anywhere else, and anchor holders referenced only by a nested merge finally get the D-07 teaching message**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-14T13:22:00Z
- **Completed:** 2026-10-14T13:30:00Z
- **Tasks:** 3
- **Files modified:** 3 (1 production, 2 test)

## Accomplishments

- **CR-01 closed.** `<<: &b {language: ru, language: en}` and `<<: [&b {language: ru, language: en}]` — both accepted with last-wins before this plan — now yield exactly one `{path: "", message: "found duplicate key ('language')", line: 1}` row, at both the unit and the HTTP level, with `save_count == 0`. The root cause (PyYAML splices a merge source's raw pairs into the parent via `merge.extend(value_node.value)`, so a source-only `MappingNode` never reaches `construct_mapping`) is fixed by snapshotting and scanning every source in the same pre-mutation window already used for the carrier.
- **The scan is a verbatim extraction, not a re-implementation.** `_check_own_keys` is called from both `construct_mapping` and `flatten_mapping`; the `ConstructorError` context string, argument order, `f"found duplicate key ({key!r})"` text and both marks are unchanged, so `test_explicit_duplicate_still_rejected` and the byte-identical D-09 tripwire stay green.
- **Precedence is specified and pinned in all four measured directions.** A source the projected node's own window observes reports its duplicate first; a source the projection never reaches leaves the over-budget refusal to win (exactly one row either way); a nested source inside both bounds is still reached; and inside one node the pristine own-key scan wins over the source scan. Each direction has its own asserting test, and every over-budget document still yields exactly one row.
- **WR-01 fixed.** `_merge_source_ids` is an iterative, `visited`-guarded walk collecting merge-source ids at any depth, so `defaults: &c {…}` + `other: {<<: *c}` now yields `_anchor_holder_keys(...) == {"defaults"}` and exactly one row carrying the Russian teaching message — while `other` keeps Pydantic's English message (the translation stays anchor-gated). The walk also terminates on `a: &a {<<: *a}`.
- **No previously-accepted document became rejected.** The `ORACLE_ACCEPTED` loop, the override / first-source-wins semantics (D-03), the unchanged near-miss case, the boundary corpus and the full 815-test suite are green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Reject a duplicate key written inside a merge source's own mapping (CR-01 closure)** — `04ac410` (fix)
2. **Task 2: Prove the merge-source duplicate rides the unchanged 400 envelope with zero writes** — `c7afe1b` (test)
3. **Task 3: Nested-merge anchor holders get the D-07 teaching message (WR-01) — carrying the advisory IN-01 / IN-02 / IN-03 items** — `9604645` (fix)

**Plan metadata:** see the `docs(17-03): complete merge-source duplicate-key gap-closure plan` commit

_Note: Task 1 and Task 3 are `tdd="true"`; the recorded RED state precedes the production edit in each and is captured below under TDD Gate Compliance._

## Files Created/Modified

- `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` — the ONLY production file: `_check_own_keys` (NEW method, factored verbatim out of `construct_mapping`), the merge-source snapshot + scan loop inside `flatten_mapping` (NEW, runs before `super().flatten_mapping` and before `_project`), a delegating `construct_mapping`, and `_merge_source_ids` (NEW module helper) consumed by a rewritten `_anchor_holder_keys`. `PipelineConfigModel`, its four-key set, `MAX_PIPELINE_CONFIG_CHARS`, `_MERGE_TAG`, `MAX_MERGE_DEPTH`/`MAX_MERGE_ENTRIES`, `_MERGE_TOO_BIG_MESSAGE`, `_project`, `_EXTRA_ANCHOR_KEY_MESSAGE`, the `Loader=` argument and the `yaml.SafeLoader` subclass hierarchy are all untouched.
- `tests/unit/test_pipeline_config_merge.py` — +9 tests (4 parametrized CR-01 rows over `DUPLICATE_IN_MERGE_SOURCE`, the near-miss guard, four precedence pins, and three WR-01/IN-01 tests) plus the corresponding document constants and the `_root_anchored_bomb_with_duplicate_source` / `_nested_duplicate_source_bomb` helpers. Now `ruff`-clean.
- `tests/unit/test_http_pipeline_config.py` — +1 test on the existing `_real_validator_admin_env()` harness (plus the `PipelineConfigError` import). The D-09 tripwire is byte-identical; the module diff is additions plus the one import line.

## Decisions Made

- **Source scan before `_project`.** The duplicate scan runs inside the existing pre-mutation window and ahead of the expansion projection. This is what makes the precedence deterministic in all four directions instead of incidental — an observed duplicate is reported, an unobserved one leaves the bound to win, and there is exactly one row either way.
- **`_check_own_keys` is a verbatim extraction.** Reusing the identical `ConstructorError` keeps the D-09 reject envelope, the two `DUPLICATE_REJECTED` line pins and the message text byte-identical, so closing CR-01 adds rejection without perturbing the existing contract (`T-17-12`).
- **Only ADD rejection.** The four-key `extra="forbid"` schema, the char cap, the `Loader=` argument and the loader hierarchy are untouched (D-01), so a merged or alias-referenced non-schema key still cannot reach the schema (`T-17-15`).
- **Iterative graph walk for WR-01.** `_merge_source_ids` is iterative with a `visited` node-id guard, so a self-referential merge terminates in O(#nodes) (`T-17-14`); `_anchor_holder_keys` keeps its `except (yaml.YAMLError, RecursionError) -> set()` guard and stays reject-path-only (D-05).
- **IN-01 accepted and pinned.** The composed graph is keyed on value-node identity, so a top-level key that merely aliases a merge source is reported too. Precise disambiguation would need composer-event or `&`-span data PyYAML does not retain after composition — a second parser surface for a low-impact message nicety. The behaviour is pinned by `test_anchor_holder_keys_matches_alias_copies_by_identity_design`, so it is a tested acceptance rather than a silent over-match.

## Deviations from Plan

None - plan executed exactly as written.

The only judgement call was ordering **within** Task 1's documented action: the plan said to extend the existing bookkeeping "INSIDE the `if any(...)` branch and BEFORE `_project(node, self._memo, set())`", and that is exactly what was implemented — the source loop sits between the `_own_keys[id(node)] = list(node.value)` snapshot and the `_project` call.

## Issues Encountered

- **The two "control" rows in `DUPLICATE_IN_MERGE_SOURCE` were already green pre-fix, as the plan predicted.** `ANCHOR_HOLDER_DUPLICATE_DOC` and `MERGE_SOURCE_VALUE_DUPLICATE_DOC` are reached by the ordinary scan today (the anchor holder is also a top-level value, and a source's inner values are constructed), so the recorded RED is precisely the two source-shape rows failing with `DID NOT RAISE` — not an import or collection error.
- **Precedence (c) also passed pre-fix.** For `_nested_duplicate_source_bomb(fanout=3, nesting=4)` the `a0` value is itself a top-level value, so the pristine own-key scan already reports the duplicate. The test pins the intended row regardless of which mechanism reaches it; the plan describes it as a precedence pin, not a RED gate.
- **IN-02's two `ruff` findings were landed as planned.** `I001` was fixed with `ruff check --fix` on the merge test file only; `ISC004` (not auto-fixable) was fixed by parenthesising the `DUPLICATE_REJECTED[1][0]` concatenation. `tests/unit/test_http_pipeline_config.py`'s pre-existing `I001`/`UP017` debt was deliberately NOT touched (out of scope).
- **IN-03 landed as planned.** Both wall-clock ceilings were raised to `assert elapsed < 5.0` with comments naming the row-equality assertion as the primary regression guard; the behavioural assertions are unchanged.
- No advisory item was dropped or silently skipped.

## TDD Gate Compliance

| Gate | Task | Evidence |
|------|------|----------|
| RED (CR-01) | Task 1 | `pytest tests/unit/test_pipeline_config_merge.py -q` → 3 failed / 38 passed; `test_duplicate_inside_merge_source_is_rejected[MERGE_SOURCE_DUPLICATE_DOC]` and `[…SEQUENCE_DUPLICATE_DOC]` failed with `Failed: DID NOT RAISE PipelineConfigValidationError`, and `test_duplicate_source_observed_before_the_projection_wins_over_the_bound` failed with the merge-bound message instead of the duplicate row |
| GREEN (CR-01) | Task 1 | `pytest tests/unit/test_pipeline_config_merge.py tests/unit/test_pipeline_config_validator.py -q` → **57 passed** |
| RED (WR-01) | Task 3 | `pytest tests/unit/test_pipeline_config_merge.py -q` → 2 failed / 42 passed; `assert set() == {'defaults'}` and `assert set() == {'a'}` — the recorded pre-fix state |
| GREEN (WR-01) | Task 3 | `pytest tests/unit/test_pipeline_config_merge.py tests/unit/test_pipeline_config_validator.py -q` → **60 passed** |
| REFACTOR | — | Not needed: no cleanup was identified after green |

_Note: the IN-01 characterisation test is deliberately NOT a RED gate — it asserts behaviour that is unchanged by this plan and passes pre-fix (see the test docstring)._

## Verification

- `.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_merge.py tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -q` → **77 passed**, exit 0
- `.venv\Scripts\python.exe -m pytest -q` → **815 passed, 1 warning** (pre-plan baseline 802 + 13 new tests), exit 0
- `.venv\Scripts\python.exe -m pytest tests/unit/test_http_pipeline_config.py::test_put_invalid_error_rows_are_verbatim_and_top_level -q` → **1 passed**; the tripwire source is unchanged (`git diff` over the range shows only the import line and the new test)
- `.venv\Scripts\python.exe -m ruff check tests/unit/test_pipeline_config_merge.py` → **All checks passed!**; `.venv\Scripts\python.exe -m ruff check backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` → **All checks passed!**
- `_StrictSafeLoader` still subclasses `yaml.SafeLoader`; `validate()` still passes `Loader=_StrictSafeLoader`; `MAX_PIPELINE_CONFIG_CHARS == 20000` — all asserted by unchanged tests.
- `git diff --name-only e525124..HEAD` → exactly the one adapter and the two test files; `web/src/`, `composition/`, the route and `PipelineConfigModel` untouched (D-01/D-08).

## Known Stubs

None.

## Threat Flags

None — no new network endpoint, auth path, file access pattern or schema change is introduced. T-17-11 (the added scan rides the existing parse-error mapping and is O(own keys) per source), T-17-12 (row identity preserved by the verbatim extraction), T-17-13 (one row in every precedence direction), T-17-14 (iterative, visited-guarded walk) and T-17-15/T-17-16 (schema un-widened; only the offending key name is echoed) are all mitigated as planned.

## Next Phase Readiness

- The blocking CR-01 gap from `17-VERIFICATION.md` is closed and WR-01 is repaired; all five `17-REVIEW.md` findings now have a landed disposition (CR-01 and WR-01 as graded behaviour changes with RED tests first; IN-01 accepted and pinned; IN-02 and IN-03 landed). Phase 17 is ready for re-verification (`/gsd-verify-work 17`).
- No blockers. `17-VALIDATION.md` still predates this gap plan and remains a record-accuracy task for `/gsd-validate-phase 17`.
- Reconciling the milestone-level "duplicate-key rejection not weakened" claim is now honest again: the invariant holds for every reachable input shape the phase's own tests enumerate.

## Self-Check: PASSED

- Files: `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` FOUND, `tests/unit/test_pipeline_config_merge.py` FOUND, `tests/unit/test_http_pipeline_config.py` FOUND
- Commits: `04ac410` FOUND, `c7afe1b` FOUND, `9604645` FOUND

---
*Phase: 17-yaml-merge-key-acceptance-in-the-strict-validator*
*Completed: 2026-10-14*
