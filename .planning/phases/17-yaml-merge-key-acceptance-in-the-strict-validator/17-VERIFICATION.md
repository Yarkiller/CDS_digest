---
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
verified: 2026-10-14T13:45:00Z
status: passed
score: 25/25 must-haves verified
covered_files:
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-01-PLAN.md
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-01-SUMMARY.md
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-02-PLAN.md
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-02-SUMMARY.md
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-03-PLAN.md
  - .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-03-SUMMARY.md
  - backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
  - tests/unit/test_http_pipeline_config.py
  - tests/unit/test_pipeline_config_merge.py
covered_digest: "v2:sha256:e4334987e18830d004dc3f79562c7a91d6d898ce03d8e7e1c9213252dda1b06a"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 13/14
  gaps_closed:
    - "A document with a duplicated explicit key is still rejected with the same top-level structured 400 and zero writes, with and without a `<<` present (prior truth 5 / CR-01) — the duplicate is now also caught when it lives inside a merge source's own mapping."
  gaps_remaining: []
  regressions: []
coincidental_reliance_items: []
---

# Phase 17: YAML merge-key acceptance in the strict validator Verification Report

**Phase Goal:** The strict pipeline-config validator accepts a valid YAML merge-key (`<<`) document and persists it, without weakening duplicate-key rejection and without opening a CPU-exhaustion path.
**Verified:** 2026-10-14T13:45:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (plan 17-03, commits `04ac410`, `c7afe1b`, `9604645`, `fe0b59f`)

## Re-verification Summary

This run re-verifies the milestone-gating phase after the single blocking gap from the prior report (`status: gaps_found`, 13/14 — CR-01: a duplicate key inside a merge source's own mapping was silently accepted with last-wins) was closed by plan 17-03. I did **not** trust the SUMMARY: I reproduced every claimed behaviour directly against the real `YamlPipelineConfigValidator` in a throwaway probe, ran the three phase suites and the full workspace suite, and confirmed the diff shape (one production file, two test files, `web/` untouched, the D-09 tripwire byte-identical).

- **CR-01 is closed.** `<<: &b {language: ru, language: en}` and `<<: [&b {language: ru, language: en}]` are now both REJECTED with exactly one row `PipelineConfigError(path="", message="found duplicate key ('language')", line=1)`.
- **No rejection control weakened** — top-level duplicate (with and without `<<`), anchor-holder duplicate, and a duplicate nested inside a merge source's values all reject identically.
- **No previously-accepted merge document became rejected** — the `yaml.safe_load` oracle, override and first-source-wins semantics still hold; a near-miss source (`language`/`languages`) is not flagged as a duplicate (it is rejected only by the unchanged schema, for the unknown key).
- **The CPU bound is intact** — both bomb shapes are refused with exactly one `{path: "", message: _MERGE_TOO_BIG_MESSAGE}` row in ~2–3 ms.
- **WR-01 repaired** — a top-level key used as a merge source only by a *nested* merge now gets the D-07 teaching message, and the anchor-holder walk terminates on a self-referential merge.

**Score composition:** 14 phase truths (carried forward from the prior report; truth 5 was the failing item and is now VERIFIED) + 11 gap-closure truths from `17-03-PLAN.md` = 25/25.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | A valid `<<` merge document loads to a mapping identical to `yaml.safe_load` (12-row oracle corpus) and passes the un-widened four-key schema | ✓ VERIFIED | `test_strict_loader_matches_safeloader_oracle` (12 rows) + `test_merge_document_validates` (9 rows) pass; independent probe: all accepted docs `loader == safe_load` |
| 2 | A key supplied by a merge source AND explicitly by the document resolves to the explicit value; in a merge sequence the FIRST source wins | ✓ VERIFIED | `test_merge_override_and_first_source_semantics` passes; probe: `ok_override`, `ok_first_source_wins`, `ok_own_key_overrides` all ACCEPTED and equal to `safe_load` |
| 3 | A merge source contributing zero keys (`<<: *empty`) is accepted; missing required keys are reported by the schema, not the loader | ✓ VERIFIED | `EMPTY_SOURCE_DOC` in `ORACLE_ACCEPTED` + `SCHEMA_ACCEPTED`; probe `ok_empty_source` ACCEPTED |
| 4 | An admin can PUT a merge-key config → 200 → persist once → later GET returns the identical yaml | ✓ VERIFIED | `test_put_merge_document_round_trips` passes: PUT 200, `save_count == 1`, GET returns identical text |
| 5 | A document with a duplicated explicit key is still rejected with the same structured 400 and zero writes, **with and without a `<<` present** | ✓ VERIFIED (was ✗ FAILED) | Probe: `<<: &b {language: ru, language: en}` → REJECTED one row `{path:"", message:"found duplicate key ('language')", line:1}`; `<<: [&b {language: ru, language: en}]` → same; controls reject identically; HTTP test asserts `save_count == 0` |
| 6 | A high-fan-out merge document is refused by the expansion bound with the structured 400, in bounded time, with zero writes, never a 500 | ✓ VERIFIED | Probe: fan-out-3/nesting-13 (498 chars) REJECTED one exact row in 0.0032 s; fan-out-1/nesting-13 in 0.0020 s; `test_put_merge_bomb_returns_400_and_writes_nothing` passes |
| 7 | Both bounds are inclusive at their limit and exclusive one beyond (256 entries / depth 8 accepted; 257 / depth 9 refused), exactly one structured row | ✓ VERIFIED | Probe: `_project(EXACT_ENTRY_BUDGET) == (256, 7)`, `validate` clean; `_nested_merge_chain(2,7)` refused with one bound row; `_wide_merge_source(256)` loads 256 keys, `(257)` refused |
| 8 | A document exceeding BOTH bounds still yields exactly ONE error row | ✓ VERIFIED | `(fanout=3, nesting=13)` bomb over-budget on both axes → `errors == MERGE_BOUND_ROW` (1-tuple) |
| 9 | A document containing no merge key is never charged against the merge budget | ✓ VERIFIED | Projection runs only when a merge key is present (`flatten_mapping` guard); plain four-key doc accepted |
| 10 | An arbitrary-object request is still refused; `_StrictSafeLoader` stays a `yaml.SafeLoader` subclass and `Loader=` is unchanged | ✓ VERIFIED | `test_unsafe_tag_is_refused_not_constructed` passes; probe: `issubclass(_StrictSafeLoader, yaml.SafeLoader) == True`; `Loader=_StrictSafeLoader` present in `validate()` |
| 11 | The merge fix and the bound ship together; the four-key `extra="forbid"` schema still governs; the structured-body contract is unchanged | ✓ VERIFIED | One phase diff carries both; probe `schema keys == ['language','max_chars','roles','template']`; `git diff c9606c0..HEAD -- web/` empty; tripwire byte-identical |
| 12 | A top-level anchor-holder key (`defaults: &base` + `<<: *base`) is rejected with the Russian teaching message naming the offending key | ✓ VERIFIED | `test_anchor_holder_key_gets_teaching_message` + HTTP sibling pass; `path == "defaults"`, `line is None` |
| 13 | A genuine unknown key keeps Pydantic's English `extra_forbidden` message with its own key as path and no `line` | ✓ VERIFIED | `test_genuine_unknown_key_keeps_english_message` + `test_unknown_key_is_rejected_by_extra_forbid` pass unchanged |
| 14 | The anchor-holder row rides the unchanged `{errors:[…]}` envelope with zero writes; detection never fires without a merge key and never turns a typo into an anchor lecture | ✓ VERIFIED | `test_inline_merge_shape_has_no_anchor_holder_keys` (`== set()`), HTTP test asserts `save_count == 0`, no `"detail"` key; probe confirms |
| 15 | Mapping-source duplicate `<<: &b {language: ru, language: en}` → exactly one row `{path:"", message:"found duplicate key ('language')", line=<real 1-based>}` | ✓ VERIFIED | Probe + `test_duplicate_inside_merge_source_is_rejected[MERGE_SOURCE_DUPLICATE_DOC]` (whole-row equality) |
| 16 | Sequence-source duplicate `<<: [&b {language: ru, language: en}]` → same single row | ✓ VERIFIED | Probe + `test_duplicate_inside_merge_source_is_rejected[MERGE_SOURCE_SEQUENCE_DUPLICATE_DOC]` |
| 17 | Must-not-regress controls reject identically: top-level duplicate ± `<<`, duplicate in a top-level anchor holder, duplicate nested in a merge source's VALUES | ✓ VERIFIED | Probe: all four REJECTED with one row (`template` line 2 / line 3; `language` line 1; `x` line 1); `DUPLICATE_IN_MERGE_SOURCE` table green |
| 18 | D-09 tripwire byte-identical + merge-source duplicate crosses the unchanged 400 envelope with `save_count == 0` | ✓ VERIFIED | `git diff c9606c0..HEAD -- tests/unit/test_http_pipeline_config.py` shows only the import line changed (no test body); `test_put_merge_source_duplicate_returns_400_and_writes_nothing` asserts exact body + zero writes |
| 19 | No previously-accepted merge document became rejected; near-miss (`language`/`languages`) is not flagged as a duplicate | ✓ VERIFIED | Probe: oracle loop all equal; near-miss row is `Extra inputs are not permitted` (schema, not duplicate) |
| 20 | The merge-expansion bound still refuses the bomb shapes in bounded time with exactly one `{path:"", message:_MERGE_TOO_BIG_MESSAGE}` row (no regression from the source scan) | ✓ VERIFIED | Probe (two shapes, ~2–3 ms, exact row); `test_merge_bomb_is_rejected_in_bounded_time` green |
| 21 | Reject precedence pinned both directions: (a) an observed duplicate-bearing source wins over the bound; (b) a source the projection never reaches leaves the bound to win — one row either way | ✓ VERIFIED | Probe: `_root_anchored_bomb_with_duplicate_source(3,13)` → duplicate row line 15, not the bound message; `_nested_duplicate_source_bomb(3,13)` → exactly `MERGE_BOUND_ROW` |
| 22 | The source scan reaches NESTED sources whenever the projection does not raise first | ✓ VERIFIED | Probe: `_nested_duplicate_source_bomb(3,4)` → `found duplicate key ('language')`, line 1 |
| 23 | Reject precedence INSIDE one node: the own-key duplicate is reported over a same-node merge-source duplicate | ✓ VERIFIED | Probe: `OWN_AND_SOURCE_DUPLICATE_DOC` → `found duplicate key ('template')`, line 2 |
| 24 | A top-level key used as a merge source only by a NESTED merge gets the D-07 teaching message on its own path; the key that merely CARRIES the nested merge keeps the English message | ✓ VERIFIED | Probe: `_anchor_holder_keys(NESTED) == {"defaults"}`; teaching row on `defaults`, `other` row English; `test_nested_merge_anchor_holder_gets_teaching_message` green |
| 25 | The `_anchor_holder_keys` walk terminates on a self-referential merge (`a: &a {<<: *a}` → `{"a"}`) and still yields the empty set for the inline `<<: &base` shape | ✓ VERIFIED | Probe: `{"a"}` in bounded time; `_anchor_holder_keys(MERGE_SOURCE_DOC) == set()`; both tests green |

**Score:** 25/25 truths verified (0 present, behavior-unverified)

Every behaviour-dependent truth (duplicate state detection, the expansion bound, the cycle guard, the precedence orderings, the WR-01 walk termination) is exercised by a passing named test **and** independently reproduced in this run, so none is left `PRESENT_BEHAVIOR_UNVERIFIED` and none is flagged `coincidental-reliance`.

### Deferred Items

None — no gap remains open; nothing is deferred to a later phase.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` | `_check_own_keys` (NEW, factored from `construct_mapping`), the merge-source snapshot+scan loop in `flatten_mapping`, `_merge_source_ids` (NEW), recursive `_anchor_holder_keys`, plus the pre-existing `_MERGE_TAG`, `MAX_MERGE_DEPTH`, `MAX_MERGE_ENTRIES`, `_MERGE_TOO_BIG_MESSAGE`, `_MergeExpansionTooLarge`, `_project`, `_EXTRA_ANCHOR_KEY_MESSAGE` | ✓ VERIFIED | All present and substantive (lines 33–170, 205–268); no stub/debt markers; `ruff` clean |
| `tests/unit/test_pipeline_config_merge.py` | Oracle corpus, schema-accept corpus, duplicate-reject + duplicate-in-merge-source corpora, bomb + boundary pins, precedence pins, WR-01/IN-01 tests, cycle + safety guards | ✓ VERIFIED | 44 tests collected (all pass); new file; `ruff check` → All checks passed |
| `tests/unit/test_http_pipeline_config.py` | +3 tests on the real-validator HTTP harness; D-09 tripwire preserved | ✓ VERIFIED | 17 tests pass; round-trip, bomb zero-write, merge-source-duplicate zero-write; tripwire body byte-identical |
| `web/src/` | No change attributable to this phase (D-08) | ✓ VERIFIED | `git diff --name-only c9606c0..HEAD -- web/` → empty |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `tests/unit/test_pipeline_config_merge.py` | adapter | imports `_StrictSafeLoader`, `_project`, `_MERGE_TOO_BIG_MESSAGE`, `_OVER_CAP_MESSAGE`, `_anchor_holder_keys`, `_EXTRA_ANCHOR_KEY_MESSAGE`, `MAX_MERGE_DEPTH`, `MAX_MERGE_ENTRIES` | ✓ WIRED | Import block lines 22–36; all resolved |
| `_StrictSafeLoader.flatten_mapping` | `yaml.SafeConstructor.flatten_mapping` | `return super().flatten_mapping(node)` after snapshot + source scan + bound | ✓ WIRED | line 141; bookkeeping precedes the in-place `node.value` mutation |
| `_StrictSafeLoader.flatten_mapping` | `_check_own_keys` | the source scan calls it on each pristine source `MappingNode` | ✓ WIRED | lines 124–139 |
| `_StrictSafeLoader.construct_mapping` | `_check_own_keys` | delegated with `self._own_keys.get(id(node), node.value)` | ✓ WIRED | lines 171–175 |
| `_anchor_holder_keys` | `_merge_source_ids` | consumes the nested-walk helper | ✓ WIRED | line 252 |
| `_anchor_holder_keys` | `PipelineConfigModel.model_fields` | allow-list read from the schema (A5) | ✓ WIRED | line 266; no second copy of the four keys |
| adapter | `backend/domain/pipeline_config.py` | bound raises `PipelineConfigValidationError` carrying `PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE)` | ✓ WIRED | lines 306–312; `line` omitted as designed |
| `tests/unit/test_http_pipeline_config.py` | `backend/.../interface/http/routes/admin.py` | `_real_validator_admin_env()` drives the real validator through PUT/GET `/admin/pipeline/config` | ✓ WIRED | tests at lines 197, 225, 411 pass with `save_count`/envelope assertions |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `test_put_merge_document_round_trips` | `get.json()["yaml"]` | `InMemoryPipelineConfigRepository` written by the real validator | Yes | ✓ FLOWING |
| `test_put_merge_source_duplicate_returns_400_and_writes_nothing` | `body["errors"]` / `container.pipeline_config.save_count` | real validator reject path → unchanged route serializer; repository never written | Yes | ✓ FLOWING (reject path, 0 writes) |

_No UI/rendered-data artifacts in this phase; Level 4 is limited to the persist→read-back and reject→envelope paths._

### Behavioral Spot-Checks

Commands run from the repo root with `.venv\Scripts\python.exe`.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase 17 suites | `-m pytest tests/unit/test_pipeline_config_merge.py tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -q` | `77 passed, 1 warning in 4.86s` | ✓ PASS |
| Full workspace suite (run once) | `-m pytest -q` | `815 passed, 1 warning in 14.25s` | ✓ PASS |
| CR-01 reproduction (mapping + sequence source) | independent probe against `YamlPipelineConfigValidator.validate()` | both REJECTED, exactly one row `{'path':'','message':"found duplicate key ('language')",'line':1}` | ✓ PASS |
| Controls (top-level dup ± `<<`, anchor-holder dup, source-value dup) | same probe | all REJECTED one row (`template` l2 / l3, `language` l1, `x` l1) | ✓ PASS |
| Previously-accepted merge docs (oracle + override + first-source-wins + empty source + near-miss) | same probe | all ACCEPTED and `loader == safe_load`; near-miss not flagged as duplicate | ✓ PASS |
| Merge bound (fan-out 3 & 1, nesting 13) | same probe with `time.perf_counter()` | one exact `MERGE_BOUND_ROW` each, 0.0032 s / 0.0020 s | ✓ PASS |
| Boundary inclusivity | same probe | `_project(EXACT)==(256,7)`; `chain(2,7)` refused; `wide(256)`→256 keys, `wide(257)` refused | ✓ PASS |
| Precedence (a)–(d) | same probe | (a) duplicate row line 15 not bound; (b) bound row; (c) nested dup line 1; (d) own-key `template` line 2 | ✓ PASS |
| WR-01 / IN-01 | same probe | `_anchor_holder_keys(NESTED)=={'defaults'}`, teaching row on `defaults`, `other` English; `{'defaults','alias_key'}` for alias doc; `{'a'}` for self-ref | ✓ PASS |
| Lint | `-m ruff check tests/unit/test_pipeline_config_merge.py backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` | `All checks passed!` | ✓ PASS |
| Diff shape | `git diff --name-only c9606c0..HEAD -- web/` | empty | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED — no `scripts/*/tests/probe-*.sh` exist and this is not a migration/tooling phase; no probe is declared in any PLAN or SUMMARY.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| PIPE-04 | 17-01, 17-02, 17-03 | Accept a valid YAML merge-key document and persist it, **while still rejecting duplicate explicit keys** with the same structured 400 and zero writes | ✓ SATISFIED | Acceptance + persist + read-back verified (truths 1–4); duplicate rejection verified for own-key, anchor-holder, source-value, and **merge-source** duplicates (truths 5, 15–19, 23) |
| PIPE-05 | 17-01, 17-02, 17-03 | Merge expansion is bounded (breach → structured 400) and **duplicate-key rejection is provably not weakened** | ✓ SATISFIED | Bound fully verified (truths 6–9, 11, 20); "not weakened" now holds for every enumerated reachable shape (truths 5, 15–25) |

No orphaned requirements: `REQUIREMENTS.md` maps exactly `PIPE-04` and `PIPE-05` to Phase 17, and both appear in all three plans' `requirements:` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| adapter, both test files | — | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` | none | No debt markers in any phase-modified file |
| `tests/unit/test_pipeline_config_merge.py` | 341 area, 500-area | wall-clock `elapsed < 5.0` assertions | ℹ️ Info | Ceilings raised from 0.5 s in 17-03; the `errors == MERGE_BOUND_ROW` row equality is the primary regression guard; measured ~2 ms vs 5 s (>1000× margin) |

No blockers, no unresolved debt markers. The two `ruff` findings (I001, ISC004) from the prior report are resolved.

### Prohibitions Checked

All ten test-tier prohibitions across `17-01`/`17-02`/`17-03` have wired enforcement and are green — duplicate-key rejection not weakened (`test_explicit_duplicate_still_rejected` + the CR-01 corpus), loader hierarchy / `Loader=` unchanged (probe `issubclass` + `test_unsafe_tag_is_refused_not_constructed`), parser-internal copy never leaks (exact curated row equality), pre-gap baseline not regressed (815-test suite green + byte-identical tripwire), four-key `extra="forbid"` surface un-widened (probe `SCHEMA_KEYS`). No flag is raised.

### Human Verification Required

None. Every must-have truth is behavioural and is exercised by a passing named test, independently reproduced in this run; the user-facing copy is a locked decision (D-07) pinned exactly by test, so no human judgment is required.

### Gaps Summary

**No gaps.** The single blocking gap from the prior report (CR-01) is closed: a duplicate key inside a merge source's own mapping — mapping-source or merge-sequence shape, at the root or nested under a within-budget chain — now yields exactly one `{path: "", message: "found duplicate key ('…')", line: <real 1-based>}` row at both the unit and the HTTP level, with zero writes. The must-not-regress controls still reject identically, no previously-accepted merge document became rejected, the expansion bound still refuses the bomb shapes in bounded time with exactly one row, and the reject precedence (duplicate-vs-bound and own-key-vs-source) is specified and pinned in all four measured directions. WR-01 is repaired. The phase goal holds.

---

_Verified: 2026-10-14T13:45:00Z_
_Verifier: Claude (gsd-verifier)_
