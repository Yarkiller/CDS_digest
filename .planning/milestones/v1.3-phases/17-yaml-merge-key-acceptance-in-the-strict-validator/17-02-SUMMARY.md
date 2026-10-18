---
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
plan: 02
subsystem: backend-adapter
tags: [yaml, pyyaml, pydantic, extra-forbidden, fastapi, pytest, error-messages]

# Dependency graph
requires:
  - phase: 17-01
    provides: "merge-key parse-path fix (skip by tag + pristine own-key snapshot), the pre-flatten expansion bound, and the green D-09 reject-envelope tripwire this plan builds on"
provides:
  - "_EXTRA_ANCHOR_KEY_MESSAGE — the `{key}`-interpolated Russian teaching message for an extra top-level anchor holder (D-07)"
  - "_anchor_holder_keys(yaml_text) — a guarded yaml.compose() helper reading the allow-list from PipelineConfigModel.model_fields (D-05, A5)"
  - "the anchor-gated message translation inside validate()'s existing ValidationError comprehension — message-only, loc-derived path preserved"
affects: [17-verify-work, 18, 19, 22]

# Actuals (#2632) — pairs with the plan's `estimate` (tokens 12000 / raw 24000 / tasks 2).
# `commits` is MEASURED as `git rev-list --count plan_head_before..plan_head_after` at
# SUMMARY-write time (the four task commits); the docs(17-02) metadata commit is separate.
actuals:
  tokens: 2323
  tasks: 2
  commits: 4

plan_head_before: a8294886e489f52602bb467d2b73bf0846bbf837
plan_head_after: f89b22157deec3c6551802e1e775acf7b7aad70f

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Anchor identity is recovered from the composed node graph — never from the constructed dict, where merges are copies and aliases are shared node objects"
    - "Reject-path-only enrichment: the extra graph re-read runs only when an extra_forbidden row exists, so the happy path pays nothing"
    - "Schema-derived allow-list: the four keys are read from PipelineConfigModel.model_fields so the D-07 detection can never drift from the schema (A5)"

key-files:
  created: []
  modified:
    - backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
    - tests/unit/test_pipeline_config_merge.py
    - tests/unit/test_http_pipeline_config.py

key-decisions:
  - "The D-07 row keeps the loc-derived path (`defaults`) and only the message changes — the row's field identity stays identical to every other extra_forbidden row (A2, Open Question 1 resolved)"
  - "The translation is gated on anchor identity (`error['loc'][0] in anchor_holders`), so a genuine typo keeps Pydantic's English extra_forbidden message and the D-09 tripwire stays byte-identical (Pitfall 9)"
  - "`_anchor_holder_keys` is wrapped in `except (yaml.YAMLError, RecursionError) -> set()` and reads the allow-list from `PipelineConfigModel.model_fields` so neither a 500 path nor a second copy of the four keys is introduced (D-05, A5)"
  - "RED was recorded in two stages (behavioural message mismatch, then the not-yet-existing production symbols), mirroring 17-01 — neither stage bypassed the failable-test-first rule"

patterns-established:
  - "Re-read the composed node graph on the reject path when a construction-time identity is needed for error copy"
  - "Gate an error-message translation on a positive identity check, never on the error `type` alone, so an unrelated error keeps its upstream message"

requirements-completed: [PIPE-04, PIPE-05]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "A top-level anchor-holder key gets the Russian teaching message naming the offending key: «Лишний ключ «defaults»: якоря нужно объявлять в самом `<<`» on path == \"defaults\" with no line"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_anchor_holder_key_gets_teaching_message"
        status: pass
    human_judgment: false
  - id: D2
    description: "A genuine unknown key keeps Pydantic's English extra_forbidden message with its own key as the path — the translation never fires for a non-anchor extra key"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_genuine_unknown_key_keeps_english_message + tests/unit/test_pipeline_config_validator.py#test_unknown_key_is_rejected_by_extra_forbid"
        status: pass
    human_judgment: false
  - id: D3
    description: "The inline merge shape (`<<: &base` + four keys) is untouched: `_anchor_holder_keys` returns the empty set and the document validates cleanly"
    requirement: PIPE-04
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_inline_merge_shape_has_no_anchor_holder_keys"
        status: pass
    human_judgment: false
  - id: D4
    description: "The anchor-holder teaching message reaches the top-level {errors:[…]} 400 body verbatim through the unchanged route, with zero writes"
    requirement: PIPE-05
    verification:
      - kind: integration
        ref: "tests/unit/test_http_pipeline_config.py#test_put_anchor_holder_key_returns_400_with_teaching_message"
        status: pass
    human_judgment: false
  - id: D5
    description: "The D-09 reject-envelope tripwire is preserved byte-identically and green — the four-key extra=forbid surface and the HTTP layer are untouched"
    requirement: PIPE-04
    verification:
      - kind: integration
        ref: "tests/unit/test_http_pipeline_config.py#test_put_invalid_error_rows_are_verbatim_and_top_level (source unchanged: `git diff -G` over the range is empty)"
        status: pass
    human_judgment: false

# Metrics
duration: 7min
completed: 2026-10-14
status: complete
---

# Phase 17 Plan 02: Teach the anchor-holder mistake Summary

**An extra top-level anchor-holder key now gets a key-naming Russian message that teaches the `<<` form, while a genuine unknown key keeps Pydantic's English `extra_forbidden` message and the 400 envelope stays byte-identical**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-14T12:03:00Z
- **Completed:** 2026-10-14T12:10:09Z
- **Tasks:** 2
- **Files modified:** 3 (1 production, 2 test)

## Accomplishments

- The most likely post-fix admin mistake now reads honestly: `defaults: &base` + `<<: *base` is rejected with «Лишний ключ «defaults»: якоря нужно объявлять в самом `<<`» on `path == "defaults"` and no `line`, instead of Pydantic's cryptic English «Extra inputs are not permitted».
- The translation is **anchor-gated, not type-gated**: `_anchor_holder_keys` re-reads the composed node graph (anchor identity is gone after construction) and returns only top-level keys whose value node is used as a merge source — so `score_factors` still keeps the English `extra_forbidden` message and the D-09 tripwire never sees a changed row.
- The detection is **reject-path-only and schema-derived**: `yaml.compose` runs only when an `extra_forbidden` row exists, is wrapped in `except (yaml.YAMLError, RecursionError) -> set()` so it can never become a 500 path (D-05), and reads the allow-list from `PipelineConfigModel.model_fields` so the four keys are never copied (A5).
- The change is message-only: `PipelineConfigModel`, the `Loader=` argument, the route serializer, `web/src/` and `composition/` are all untouched — the diff is the one adapter plus two test files (verified by `git diff --name-only` over the range).
- The inline `<<: &base` form is provably unaffected: the guard returns ∅ for it and the document validates cleanly.

## Task Commits

Each task was committed atomically:

1. **Task 1: Anchor-holder key gets a key-naming teaching message, genuine unknown keys keep the English message** — RED/GREEN, three commits:
   - `905c1ba` (test) — failing anchor-holder corpus: the D-07 document yielded the English `Extra inputs are not permitted` message (1 failed / 30 passed)
   - `2ae86c2` (test) — the adapter private-symbol import (`_EXTRA_ANCHOR_KEY_MESSAGE`, `_anchor_holder_keys`) plus the inline-merge guard (1 collection error: `ImportError: cannot import name '_EXTRA_ANCHOR_KEY_MESSAGE'`)
   - `144eafd` (feat) — the constant, the guarded helper, and the anchor-gated translation
2. **Task 2: Prove the anchor-holder message rides the unchanged 400 envelope with zero writes** — `f89b221` (test)

**Plan metadata:** see the `docs(17-02): complete anchor-holder-teaching-message plan` commit

_Note: Task 1 was `tdd="true"`, hence the multiple RED → GREEN commits._

## Files Created/Modified

- `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` — the only production file: `_EXTRA_ANCHOR_KEY_MESSAGE`, `_anchor_holder_keys`, and the anchor-gated `message` translation inside the existing `ValidationError` comprehension. `PipelineConfigModel`, the loader hierarchy, the `Loader=` argument and the HTTP layer are untouched.
- `tests/unit/test_pipeline_config_merge.py` — +3 tests (anchor-holder teaching message, genuine-unknown-key English message preserved, inline-merge guard) plus the `ANCHOR_HOLDER_KEY_DOC` / `UNKNOWN_KEY_DOC` constants.
- `tests/unit/test_http_pipeline_config.py` — +1 test on the existing `_real_validator_admin_env()` harness; the D-09 tripwire `test_put_invalid_error_rows_are_verbatim_and_top_level` is byte-identical (the module diff is additions only).

## Decisions Made

- **Message-only, path preserved (A2).** The D-07 row keeps `path=_loc_to_dot_sep(error["loc"])` (`"defaults"`) and changes only `message` — the smallest change and the most informative row, with its field identity identical to every other `extra_forbidden` row. This resolves Open Question 1 as planned.
- **Gate on identity, not on `type` (Pitfall 9).** Only a row whose key is in the composed-graph anchor-holder set is translated; a genuine typo keeps Pydantic's English message. This is exactly what keeps the D-09 tripwire and `test_unknown_key_is_rejected_by_extra_forbid` green unchanged.
- **Two guards on the helper (D-05, A5).** The `yaml.compose` call is wrapped so a malformed/too-deep document returns `∅` instead of a new 500 path, and the allow-list is read from `PipelineConfigModel.model_fields` so the four keys are never duplicated — the D-07 detection follows any future schema change automatically.
- **Reject-path-only cost.** `_anchor_holder_keys` is invoked only when `exc.errors()` contains an `extra_forbidden` row, so the happy path never re-composes the document.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **RED was recorded in two stages, mirroring 17-01.** The plan's RED gate describes the failure as the English message, but Test A's final form binds `_EXTRA_ANCHOR_KEY_MESSAGE` — a symbol that does not exist before the production edit, which would make collection fail with an `ImportError` rather than reach the assertion. The first stage therefore used the literal expected wording (RED recorded: the D-07 document yielded `Extra inputs are not permitted`), and the second stage added the adapter import plus the inline-merge guard (RED recorded: `ImportError: cannot import name '_EXTRA_ANCHOR_KEY_MESSAGE'`). Both stages are in the git history; neither bypassed the failable-test-first rule, and the final test file asserts against the adapter constant as the plan requires.
- **Task 2 is a pure integration proof over Task 1's already-shipped production change.** It is not declared `tdd="true"` and adds no production code; the behavioural RED for the message itself was established by Task 1. The test would fail against the pre-17-02 message (English), which is the property it pins across the HTTP boundary.

## TDD Gate Compliance

| Gate | Commit | Evidence |
|------|--------|----------|
| RED (behavioural) | `905c1ba` | `pytest tests/unit/test_pipeline_config_merge.py -q` → 1 failed / 30 passed; `test_anchor_holder_key_gets_teaching_message` failed with actual `Extra inputs are not permitted` vs expected «Лишний ключ «defaults»…» |
| RED (symbols) | `2ae86c2` | Same command → `ImportError: cannot import name '_EXTRA_ANCHOR_KEY_MESSAGE'` (expected: the constant and helper are part of the production change) |
| GREEN | `144eafd` | `pytest tests/unit/test_pipeline_config_merge.py tests/unit/test_pipeline_config_validator.py -q` → 48 passed |
| REFACTOR | — | Not needed: no cleanup was identified after green |

## Verification

- `.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_merge.py tests/unit/test_pipeline_config_validator.py -q` → **48 passed** (32 + 16), exit 0
- `.venv\Scripts\python.exe -m pytest tests/unit/test_http_pipeline_config.py -q` → **16 passed** (13 pre-change + 2 from 17-01 + 1 new), exit 0
- `.venv\Scripts\python.exe -m pytest -q` → **802 passed** (pre-change baseline of 798 + 3 unit + 1 HTTP), exit 0
- `git diff --name-only a829488..HEAD` → exactly `yaml_pipeline_config_validator.py`, `test_pipeline_config_merge.py`, `test_http_pipeline_config.py`; `web/src/` untouched (D-08)
- `git diff -G test_put_invalid_error_rows_are_verbatim` over the range → empty: the D-09 tripwire source is byte-identical

## Known Stubs

None.

## Threat Flags

None — no new network endpoint, auth path, file access pattern or schema change is introduced. T-17-07 (schema stays un-widened), T-17-08 (`_anchor_holder_keys` guarded, reject-path-only), T-17-09 (only the offending top-level key name is echoed) and T-17-10 (translation gated on composed-graph anchor identity) are all mitigated as planned.

## Next Phase Readiness

- Plan 17-02 was the last plan declaring PIPE-04/PIPE-05, so both requirements are now checkable as complete and Phase 17 has 2/2 summaries on disk — ready for `/gsd-verify-work 17`.
- No blockers. The four-key schema, `MAX_PIPELINE_CONFIG_CHARS`, the HTTP layer and `composition/` are untouched; `web/src/` carries no change attributable to this phase (the editor hint stays deferred per D-08).

## Self-Check: PASSED

- Files: `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` FOUND, `tests/unit/test_pipeline_config_merge.py` FOUND, `tests/unit/test_http_pipeline_config.py` FOUND
- Commits: `905c1ba` FOUND, `2ae86c2` FOUND, `144eafd` FOUND, `f89b221` FOUND

---
*Phase: 17-yaml-merge-key-acceptance-in-the-strict-validator*
*Completed: 2026-10-14*
