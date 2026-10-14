---
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
verified: 2026-10-14T13:53:00Z
status: passed
score: 27/27 must-haves verified
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
covered_digest: "v2:sha256:db7f5bcf6e15320455cb5ffcd74c06c0f0b56edeae01c9c2b6ccc051c4f6dd93"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 25/25
  gaps_closed: []
  gaps_remaining: []
  regressions: []
coincidental_reliance_items: []
---

# Phase 17: YAML merge-key acceptance in the strict validator Verification Report

**Phase Goal:** The strict pipeline-config validator accepts a valid YAML merge-key (`<<`) document and persists it, without weakening duplicate-key rejection and without opening a CPU-exhaustion path.
**Verified:** 2026-10-14T13:53:00Z
**Status:** passed
**Re-verification:** Yes — **post-rework refresh**. This report supersedes the stale `passed` @ 25/25 verification (`verified: 2026-10-14T13:45:00Z`). It covers the two commits that landed **after** that verified state:
- `e3cb84c` — `fix(17-03)`: `_merge_source_ids` descends into `SequenceNode`s so a holder referenced only by a merge inside a LIST (`items: [- <<: *c]`) reaches its anchor holder (WR-02), and the `found unhashable key` reject now carries curated copy `_UNHASHABLE_KEY_MESSAGE` instead of PyYAML's raw English text.
- `5e68801` — `style(17-03)`: `ruff check --fix` on `tests/unit/test_http_pipeline_config.py` (I001, UP017).

Neither commit added, removed or amended a must-have; both are in-contract repairs of items the post-verification review raised (`17-REVIEW.md` WR-02, IN-04, IN-05 disposition). The `covered_digest` above is therefore **new** and does not match the previous report's `e4334987…`.

I did **not** trust the SUMMARYs. I re-ran the three phase suites and the full workspace suite, executed an independent throwaway probe against the real `YamlPipelineConfigValidator` (28 assertions, all green), confirmed the D-09 tripwire is byte-identical at the function level, and re-confirmed the untouched invariants. The probe file was deleted afterwards.

## Post-Rework Delta (what changed since the stale verification)

| Change | File | Verified effect |
| --- | --- | --- |
| `_merge_source_ids` now descends through a popped `SequenceNode` (`visited`-guarded, `stack.extend(current.value)`) | adapter | `_anchor_holder_keys(LIST_NESTED_MERGE_ANCHOR_HOLDER_DOC) == {"defaults"}`; the `defaults` row carries `_EXTRA_ANCHOR_KEY_MESSAGE` (new truth 26) |
| `_UNHASHABLE_KEY_MESSAGE` constant + `exc.problem == "found unhashable key"` mapping in the `MarkedYAMLError` branch | adapter | unhashable-key document → one row `{path: "", message: "Ключом объекта не может быть список или объект", line: 1}`, no `unhashable` substring (new truth 27) |
| Import block re-sorted; `datetime(…, tzinfo=timezone.utc)` → `datetime.UTC` | `tests/unit/test_http_pipeline_config.py` | `ruff check` clean; the D-09 tripwire body is byte-identical (verified against both `c9606c0` and `1313c6f`) — no behavioural change |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | A valid `<<` merge document loads to a mapping identical to `yaml.safe_load` (12-row oracle corpus) and passes the un-widened four-key schema | ✓ VERIFIED | `test_strict_loader_matches_safeloader_oracle` (12 rows) + `test_merge_document_validates` (9 rows) pass; independent probe: all 12 accepted rows `loader == safe_load` (0 mismatches) |
| 2 | A key supplied by a merge source AND explicitly by the document resolves to the explicit value; in a merge sequence the FIRST source wins | ✓ VERIFIED | `test_merge_override_and_first_source_semantics` passes; probe: override → `lecture`, first-source-wins → `["ds"]` |
| 3 | A merge source contributing zero keys (`<<: *empty`) is accepted; missing required keys are reported by the schema, not the loader | ✓ VERIFIED | `EMPTY_SOURCE_DOC` in `ORACLE_ACCEPTED` + `SCHEMA_ACCEPTED`; probe row accepted |
| 4 | An admin can PUT a merge-key config → 200 → persist once → later GET returns the identical yaml | ✓ VERIFIED | `test_put_merge_document_round_trips` passes: PUT 200, `save_count == 1`, GET returns identical text |
| 5 | A document with a duplicated explicit key is still rejected with the same structured 400 and zero writes, with and without a `<<` present | ✓ VERIFIED | Probe: `<<: &b {language: ru, language: en}` → one row `{path:"", message:"found duplicate key ('language')", line:1}`; `<<: [&b {language: ru, language: en}]` → same; controls reject identically; HTTP test asserts `save_count == 0` |
| 6 | A high-fan-out merge document is refused by the expansion bound with the structured 400, in bounded time, with zero writes, never a 500 | ✓ VERIFIED | Probe: fan-out-3/nesting-13 (498 chars) REJECTED one exact row in 0.0029 s; root-anchored shape in 0.0019 s; `test_put_merge_bomb_returns_400_and_writes_nothing` passes |
| 7 | Both bounds are inclusive at their limit and exclusive one beyond (256 entries / depth 8 accepted; 257 / depth 9 refused), exactly one structured row | ✓ VERIFIED | `test_merge_bound_boundaries` passes; probe-adjacent pins `_project(EXACT_ENTRY_BUDGET) == (256, 7)`, `_nested_merge_chain(2,7)` refused, `_wide_merge_source(256)` loads 256 keys, `(257)` refused |
| 8 | A document exceeding BOTH bounds still yields exactly ONE error row | ✓ VERIFIED | `(fanout=3, nesting=13)` bomb over-budget on both axes → `errors == MERGE_BOUND_ROW` (1-tuple) |
| 9 | A document containing no merge key is never charged against the merge budget | ✓ VERIFIED | Projection runs only when a merge key is present (`flatten_mapping` guard); plain four-key doc accepted |
| 10 | An arbitrary-object request is still refused; `_StrictSafeLoader` stays a `yaml.SafeLoader` subclass and `Loader=` is unchanged | ✓ VERIFIED | `test_unsafe_tag_is_refused_not_constructed` passes; probe: `issubclass(_StrictSafeLoader, yaml.SafeLoader) == True`; `yaml.load(yaml_text, Loader=_StrictSafeLoader)` present |
| 11 | The merge fix and the bound ship together; the four-key `extra="forbid"` schema still governs; the structured-body contract is unchanged | ✓ VERIFIED | Probe: schema keys `== {language, max_chars, roles, template}`, `extra == "forbid"`; `MAX_PIPELINE_CONFIG_CHARS == 20000`; `git diff c9606c0..HEAD -- web/` empty; tripwire byte-identical |
| 12 | A top-level anchor-holder key (`defaults: &base` + `<<: *base`) is rejected with the Russian teaching message naming the offending key | ✓ VERIFIED | `test_anchor_holder_key_gets_teaching_message` + HTTP sibling pass; `path == "defaults"`, `line is None` |
| 13 | A genuine unknown key keeps Pydantic's English `extra_forbidden` message with its own key as path and no `line` | ✓ VERIFIED | `test_genuine_unknown_key_keeps_english_message` + `test_unknown_key_is_rejected_by_extra_forbid` pass unchanged |
| 14 | The anchor-holder row rides the unchanged `{errors:[…]}` envelope with zero writes; detection never fires without a merge key and never turns a typo into an anchor lecture | ✓ VERIFIED | `test_inline_merge_shape_has_no_anchor_holder_keys` (`== set()`), HTTP test asserts `save_count == 0`, no `"detail"` key; probe confirms |
| 15 | Mapping-source duplicate `<<: &b {language: ru, language: en}` → exactly one row `{path:"", message:"found duplicate key ('language')", line:1}` | ✓ VERIFIED | Probe + `test_duplicate_inside_merge_source_is_rejected[MERGE_SOURCE_DUPLICATE_DOC]` (whole-row equality) |
| 16 | Sequence-source duplicate `<<: [&b {language: ru, language: en}]` → same single row | ✓ VERIFIED | Probe + `test_duplicate_inside_merge_source_is_rejected[MERGE_SOURCE_SEQUENCE_DUPLICATE_DOC]` |
| 17 | Must-not-regress controls reject identically: top-level duplicate ± `<<`, duplicate in a top-level anchor holder, duplicate nested in a merge source's VALUES | ✓ VERIFIED | Probe: all four REJECTED with one row (`template` l2 / l3; `language` l1; `x` l1); `DUPLICATE_IN_MERGE_SOURCE` table green |
| 18 | D-09 tripwire byte-identical + merge-source duplicate crosses the unchanged 400 envelope with `save_count == 0` | ✓ VERIFIED | Function-level comparison: `test_put_invalid_error_rows_are_verbatim_and_top_level` identical to `c9606c0` **and** `1313c6f`; `test_put_merge_source_duplicate_returns_400_and_writes_nothing` asserts exact body + zero writes |
| 19 | No previously-accepted merge document became rejected; near-miss (`language`/`languages`) is not flagged as a duplicate | ✓ VERIFIED | Probe: oracle loop all equal; near-miss row is `Extra inputs are not permitted` on `path == "languages"` (schema, not duplicate) |
| 20 | The merge-expansion bound still refuses the bomb shapes in bounded time with exactly one `{path:"", message:_MERGE_TOO_BIG_MESSAGE}` row (no regression from the source scan) | ✓ VERIFIED | Probe (two shapes, ~2–3 ms, exact row); `test_merge_bomb_is_rejected_in_bounded_time` green |
| 21 | Reject precedence pinned both directions: (a) an observed duplicate-bearing source wins over the bound; (b) a source the projection never reaches leaves the bound to win — one row either way | ✓ VERIFIED | Probe: `_root_anchored_bomb_with_duplicate_source(3,13)` → duplicate row line 15, not the bound message; `_nested_duplicate_source_bomb(3,13)` → exactly `MERGE_BOUND_ROW` |
| 22 | The source scan reaches NESTED sources whenever the projection does not raise first | ✓ VERIFIED | Probe: `_nested_duplicate_source_bomb(3,4)` → `found duplicate key ('language')`, line 1 |
| 23 | Reject precedence INSIDE one node: the own-key duplicate is reported over a same-node merge-source duplicate | ✓ VERIFIED | Probe: `OWN_AND_SOURCE_DUPLICATE_DOC` → `found duplicate key ('template')`, line 2 |
| 24 | A top-level key used as a merge source only by a NESTED merge (mapping value) gets the D-07 teaching message on its own path; the key that merely CARRIES the nested merge keeps the English message | ✓ VERIFIED | `test_nested_merge_anchor_holder_gets_teaching_message` green; `_anchor_holder_keys(NESTED_MERGE_ANCHOR_HOLDER_DOC) == {"defaults"}` |
| 25 | The `_anchor_holder_keys` walk terminates on a self-referential merge (`a: &a {<<: *a}` → `{"a"}`) and still yields the empty set for the inline `<<: &base` shape | ✓ VERIFIED | `test_anchor_holder_keys_terminates_on_self_referential_merge` + `test_inline_merge_shape_has_no_anchor_holder_keys` green; probe: self-ref refused in bounded time |
| **26 (NEW — post-rework WR-02)** | A merge nested under a **SEQUENCE** (list element) reaches its anchor holder: `_anchor_holder_keys(LIST_NESTED_MERGE_ANCHOR_HOLDER_DOC) == {"defaults"}`, exactly one row carries the teaching message, and `items` (which only CARRIES the merge) keeps the English message | ✓ VERIFIED | Whole-row probe reproduced: holders `== {"defaults"}`; the 6-row document has exactly one `Лишний ключ` row on `path == "defaults"` with `line is None`; the `items` row is `Extra inputs are not permitted`; `test_anchor_holder_keys_reaches_a_merge_nested_under_a_sequence` green |
| **27 (NEW — post-rework Info #2)** | The unhashable-key reject returns curated copy (`_UNHASHABLE_KEY_MESSAGE`), with exactly one row, `path == ""`, `line == 1`, and no `unhashable` substring | ✓ VERIFIED | Probe: `? [1, 2]\n: 1\n? [1, 2]\n: 2\n` → `(PipelineConfigError(path='', message='Ключом объекта не может быть список или объект', line=1),)`, `"unhashable" not in message`; `test_unhashable_duplicate_keys_are_rejected_with_curated_copy` green |

**Score:** 27/27 truths verified (0 present, behavior-unverified)

Every behaviour-dependent truth (duplicate state detection, the expansion bound, the cycle guard, the four precedence orderings, the WR-01/WR-02 walk termination, the sequence descent, the curated-copy mapping) is exercised by a passing named test **and** independently reproduced in this run, so none is left `PRESENT_BEHAVIOR_UNVERIFIED` and none is flagged `coincidental-reliance`.

### Deferred Items

None — no gap remains open; nothing is deferred to a later phase. (`IN-05`, duplicate *collection* keys not reported as duplicates, is a **deliberate, recorded** disposition — not a deferral of phase scope: such documents are already refused with curated copy and no new CPU path is opened. Pinned by `test_unhashable_duplicate_keys_are_rejected_with_curated_copy`.)

### Advisory (New Scope, Unevidenced)

None. Re-verification ran; the Step 7 scan surfaced no new-scope unevidenced finding — the only findings (`WR-02`, `IN-04`, `IN-05`) are the review items already dispositioned in `17-REVIEW-DISPOSITION.md`, and the two repairs are evidenced by the probe above.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` | `_check_own_keys` (factored from `construct_mapping`), the merge-source snapshot+scan loop in `flatten_mapping`, `_merge_source_ids` (now descending into `SequenceNode`s), `_UNHASHABLE_KEY_MESSAGE` + its `validate()` mapping, recursive `_anchor_holder_keys`, plus the pre-existing `_MERGE_TAG`, `MAX_MERGE_DEPTH`, `MAX_MERGE_ENTRIES`, `_MERGE_TOO_BIG_MESSAGE`, `_MergeExpansionTooLarge`, `_project`, `_EXTRA_ANCHOR_KEY_MESSAGE` | ✓ VERIFIED | All present and substantive (lines 33–170, 205–249, 250–281, 285–365); no debt markers; `ruff` clean |
| `tests/unit/test_pipeline_config_merge.py` | Oracle corpus, schema-accept corpus, duplicate-reject + duplicate-in-merge-source corpora, bomb + boundary pins, precedence pins, WR-01/WR-02/IN-01 tests, cycle + safety guards | ✓ VERIFIED | **46 tests** collected (all pass); `ruff check` → All checks passed |
| `tests/unit/test_http_pipeline_config.py` | +4 tests on the real-validator HTTP harness; D-09 tripwire preserved | ✓ VERIFIED | **17 tests** pass; round-trip, bomb zero-write, merge-source-duplicate zero-write, anchor-holder zero-write; tripwire body byte-identical |
| `web/src/` | No change attributable to this phase (D-08) | ✓ VERIFIED | `git diff --name-only c9606c0..HEAD -- web/` → empty |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `tests/unit/test_pipeline_config_merge.py` | adapter | imports `_StrictSafeLoader`, `_project`, `_MERGE_TOO_BIG_MESSAGE`, `_OVER_CAP_MESSAGE`, `_UNHASHABLE_KEY_MESSAGE`, `_anchor_holder_keys`, `_EXTRA_ANCHOR_KEY_MESSAGE`, `MAX_MERGE_DEPTH`, `MAX_MERGE_ENTRIES` | ✓ WIRED | Import block lines 22–36; all resolved (suite collects and passes) |
| `_StrictSafeLoader.flatten_mapping` | `yaml.SafeConstructor.flatten_mapping` | `return super().flatten_mapping(node)` after snapshot + source scan + bound | ✓ WIRED | bookkeeping precedes the in-place `node.value` mutation |
| `_StrictSafeLoader.flatten_mapping` | `_check_own_keys` | the source scan calls it on each pristine source `MappingNode` | ✓ WIRED | source loop calls the shared helper |
| `_StrictSafeLoader.construct_mapping` | `_check_own_keys` | delegated with `self._own_keys.get(id(node), node.value)` | ✓ WIRED | present |
| `_anchor_holder_keys` | `_merge_source_ids` | consumes the nested-walk helper (now sequence-aware) | ✓ WIRED | probe: `{"defaults"}` for the list-nested shape |
| `_anchor_holder_keys` | `PipelineConfigModel.model_fields` | allow-list read from the schema (A5) | ✓ WIRED | no second copy of the four keys |
| adapter | `backend/domain/pipeline_config.py` | bound raises `PipelineConfigValidationError` carrying `PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE)` | ✓ WIRED | raised through the port; `line` omitted as designed |
| `validate()` | `_UNHASHABLE_KEY_MESSAGE` | `MarkedYAMLError` branch maps `exc.problem == "found unhashable key"` to the curated constant | ✓ WIRED | probe: exact curated row |
| `tests/unit/test_http_pipeline_config.py` | `backend/.../interface/http/routes/admin.py` | `_real_validator_admin_env()` drives the real validator through PUT/GET `/admin/pipeline/config` | ✓ WIRED | 17 tests pass with `save_count`/envelope assertions; route diff empty |

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
| Phase 17 suites | `-m pytest tests/unit/test_pipeline_config_merge.py tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -q` | `79 passed, 1 warning in 4.65s` (46 + 16 + 17) | ✓ PASS |
| Full workspace suite (run once) | `-m pytest -q` | `817 passed, 1 warning in 11.23s` | ✓ PASS |
| CR-01 reproduction (mapping + sequence source) | independent probe against `YamlPipelineConfigValidator.validate()` | both REJECTED, exactly one row `{'path':'','message':"found duplicate key ('language')",'line':1}` | ✓ PASS |
| Controls (top-level dup ± `<<`, anchor-holder dup, source-value dup) | same probe | all REJECTED one row (`template` l2 / l3, `language` l1, `x` l1) | ✓ PASS |
| Previously-accepted merge docs (oracle + override + first-source-wins + empty source + near-miss) | same probe | 12/12 oracle rows `loader == safe_load`; override/first-source ok; near-miss not flagged as duplicate | ✓ PASS |
| Merge bound (fan-out 3 & 1, nesting 13) | same probe with `time.perf_counter()` | one exact `MERGE_BOUND_ROW` each, 0.0029 s / 0.0019 s | ✓ PASS |
| Precedence (a)–(d) | same probe | (a) duplicate row line 15 not bound; (b) bound row; (c) nested dup line 1; (d) own-key `template` line 2 | ✓ PASS |
| WR-01 / WR-02 / IN-05 | same probe | `_anchor_holder_keys(NESTED)=={'defaults'}`; sequence-nested `=={'defaults'}` with one teaching row; unhashable → curated copy, `line 1` | ✓ PASS |
| No-new-500 paths | same probe | unsafe tag, self-referential merge, deep nesting each → structured `PipelineConfigError` rows, no exception escaping | ✓ PASS |
| Lint | `-m ruff check` on adapter + both test files | `All checks passed!` | ✓ PASS |
| D-09 tripwire byte-identity | function-level extract from `c9606c0`, `1313c6f`, `HEAD` | identical in all three | ✓ PASS |
| Diff shape | `git diff --name-only c9606c0..HEAD -- web/ backend/.../interface backend/.../composition backend/.../domain backend/.../application` | empty | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED — no `scripts/*/tests/probe-*.sh` exist and this is not a migration/tooling phase; no probe is declared in any PLAN or SUMMARY.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| PIPE-04 | 17-01, 17-02, 17-03 | Accept a valid YAML merge-key document and persist it, **while still rejecting duplicate explicit keys** with the same structured 400 and zero writes | ✓ SATISFIED | Acceptance + persist + read-back verified (truths 1–4); duplicate rejection verified for own-key, anchor-holder, source-value, and **merge-source** duplicates (truths 5, 15–19, 23) |
| PIPE-05 | 17-01, 17-02, 17-03 | Merge expansion is bounded (breach → structured 400) and **duplicate-key rejection is provably not weakened** | ✓ SATISFIED | Bound fully verified (truths 6–9, 11, 20); "not weakened" holds for every enumerated reachable shape (truths 5, 15–27), and the post-rework sequence/copy changes add rejection or copy honesty only — no accepted document became rejected |

No orphaned requirements: `REQUIREMENTS.md` maps exactly `PIPE-04` and `PIPE-05` to Phase 17, and both appear in all three plans' `requirements:` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| adapter, both test files | — | `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` | none | No debt markers in any phase-modified file |
| adapter, both test files | — | `ruff` findings (I001/UP017/ISC004) | none | All resolved — the post-rework `5e68801` cleared the last file; `ruff check` on all three is clean |
| `tests/unit/test_pipeline_config_merge.py` | bomb / cycle tests | wall-clock `elapsed < 5.0` assertions | ℹ️ Info | Ceilings raised from 0.5 s in 17-03; the `errors == MERGE_BOUND_ROW` row equality is the primary regression guard; measured ~2 ms vs 5 s (>1000× margin) |

No blockers, no unresolved debt markers.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `tests/unit/test_pipeline_config_merge.py` | PIPE-04, PIPE-05 | 46 | 0 | none | Value / Behavioural (whole-row equality, oracle comparison) | ✓ PASS |
| `tests/unit/test_http_pipeline_config.py` | PIPE-04, PIPE-05 | 17 | 0 | none | Behavioural (end-to-end PUT/GET, envelope + zero-write) | ✓ PASS |

**Disabled tests on requirements:** 0. **Circular patterns detected:** 0 (the oracle compares against `yaml.safe_load`, an independent parser path, not the system under test). **Insufficient assertions:** 0.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts. (`gsd-tools check.decision-coverage-verify` → `honored 9 / total 9`, `not_honored: []`, non-blocking.) D-01 (four-key schema not widened), D-02 (tag-based skip + pristine snapshot), D-03 (override / first-source-wins), D-04 (pre-flatten bounds), D-05 (guarded new pre-pass), D-06 (dedicated merge-bound copy), D-07 (anchor-holder teaching message), D-08 (no UI change), D-09 (tripwire preserved) all verified in code and tests.

### Prohibitions Checked

All ten test-tier prohibitions across `17-01`/`17-02`/`17-03` have wired enforcement and are green — duplicate-key rejection not weakened (`test_explicit_duplicate_still_rejected` + the CR-01 corpus), loader hierarchy / `Loader=` unchanged (probe `issubclass` + `test_unsafe_tag_is_refused_not_constructed`), parser-internal copy never leaks (exact curated row equality, including the new unhashable copy), pre-gap baseline not regressed (817-test suite green + byte-identical tripwire), four-key `extra="forbid"` surface un-widened (probe `SCHEMA_KEYS`). No flag is raised.

### Human Verification Required

N/A — infrastructure/parse-path phase with no user-facing elements. Every acceptance criterion is verifiable programmatically: all 27 truths are exercised by passing named tests and independently reproduced in this run; the user-facing copy is a locked decision (D-06/D-07) pinned exactly by test. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED or abstained non-inferable truth exists, so the infrastructure auto-pass-UAT shortcut is not masking an evidence gap.

### Gaps Summary

**No gaps.** This is a post-rework refresh of an already-`passed` phase. The two post-verification commits (`e3cb84c`, `5e68801`) are repairs, not regressions: the sequence-nested anchor-holder gap (WR-02) is closed and pinned (`_anchor_holder_keys(LIST_NESTED_MERGE_ANCHOR_HOLDER_DOC) == {"defaults"}`, one teaching row on `defaults`, `items` unchanged), and the unhashable-key reject now carries curated Russian copy with one row, `path == ""`, `line == 1` and no `unhashable` substring. Commit `5e68801` is lint-only — the D-09 tripwire body is byte-identical to the phase baseline. Every carried-forward must-have still holds: the CR-01 reproduction is still rejected with exactly one row and zero writes, the controls still reject identically, no previously-accepted merge document became rejected (12/12 oracle rows equal `yaml.safe_load`), the expansion bound still refuses both bomb shapes with one `_MERGE_TOO_BIG_MESSAGE` row in ~2–3 ms, the duplicate-vs-bound precedence is pinned in all four measured directions, the four-key `extra="forbid"` schema / `MAX_PIPELINE_CONFIG_CHARS == 20000` / `Loader=_StrictSafeLoader` / `yaml.SafeLoader` hierarchy / route / `composition/` / `web/` are untouched, and no new 500 path was introduced. The phase goal holds.

---

_Verified: 2026-10-14T13:53:00Z_
_Verifier: Claude (gsd-verifier)_
