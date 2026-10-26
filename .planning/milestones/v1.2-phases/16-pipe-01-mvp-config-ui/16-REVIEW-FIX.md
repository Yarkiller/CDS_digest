---
phase: 16-pipe-01-mvp-config-ui
fixed_at: 2026-10-04T19:21:00Z
review_path: C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/.planning/phases/16-pipe-01-mvp-config-ui/16-REVIEW.md
fix_scope: all
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 16: Code Review Fix Report

**Fixed at:** 2026-10-04T19:21:00Z
**Source review:** `C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/.planning/phases/16-pipe-01-mvp-config-ui/16-REVIEW.md`
**Iteration:** 1 (incremental re-review after the CR-01 fix)

**Summary:**
- Findings in scope: 2 (both Info: IN-01, IN-02)
- Fixed: 2
- Skipped: 0

The source review (`status: issues_found`) reported 0 critical, 0 warning, 2 info.
Both Info items are now fixed; the prior CR-01 remediation documented in the
previous revision of this file is untouched and still in place.

## Fixed Issues

### IN-01: `_TOO_DEEP_MESSAGE` is English while every other hand-authored document-level message is Russian

**Files modified:** `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`, `tests/unit/test_pipeline_config_validator.py`, `tests/unit/test_http_pipeline_config.py`
**Commit:** `722ee05` — `fix(16): IN-01 localize _TOO_DEEP_MESSAGE to Russian`

**Applied fix (TDD — RED → GREEN):**

1. **RED** — updated the deep-nesting expectations in both test files to assert the
   reviewer's suggested Russian literal `"Документ YAML имеет слишком глубокую вложенность"`.
   Ran the two-file suite and confirmed exactly the two deep-nesting tests failed for
   the expected cause:
   ```
   2 failed, 27 passed
   FAILED tests/unit/test_pipeline_config_validator.py::test_deeply_nested_flow_document_is_rejected_not_recursion_error
   FAILED tests/unit/test_http_pipeline_config.py::test_put_deeply_nested_yaml_returns_400_not_500
   AssertionError: {'path': '', 'message': 'YAML nesting too deep (exceeds parser limit)'}
                    != {'path': '', 'message': 'Документ YAML имеет слишком глубокую вложенность'}
   ```
2. **GREEN** — changed the single production constant to
   `_TOO_DEEP_MESSAGE = "Документ YAML имеет слишком глубокую вложенность"`. The
   adapter now emits Russian for the deep-nesting reject, matching
   `_OVER_CAP_MESSAGE` / `_NOT_A_TEXT_OBJECT_MESSAGE` / `_UNREADABLE_MESSAGE`, so the
   verbatim-rendering admin surface (D-05) shows consistent copy.
3. **Verification** — reran the two-file suite: **29 passed**.

### IN-02: Deep-nesting tests pin a depth coupled to the interpreter recursion limit and duplicate message literals

**Files modified:** `tests/unit/test_pipeline_config_validator.py`, `tests/unit/test_http_pipeline_config.py`
**Commit:** `c336865` — `fix(16): IN-02 derive deep-nesting depth and import message constants`

**Applied fix:**

1. **Derive the depth from the live limit** — both deep-nesting tests now use
   `depth = sys.getrecursionlimit() + 500` and build `"[" * depth + "]" * depth`
   (still well under `MAX_PIPELINE_CONFIG_CHARS`, which the unit test asserts). The
   margin keeps the parser on the overflow branch even if the interpreter recursion
   limit is raised above the old hard-coded 3000.
2. **Import the production message constants instead of re-typing literals** — both
   test modules now import `_TOO_DEEP_MESSAGE` and `_UNREADABLE_MESSAGE` from
   `backend.infrastructure.yaml_pipeline_config_validator` and assert against them,
   removing all four duplicated literal sites
   (`test_pipeline_config_validator.py` deep-nesting + unreadable assertions;
   `test_http_pipeline_config.py` deep-nesting + control-char assertions). No
   production change was required for this half: the two constants were already
   module-level names, so they are directly importable by the tests.
3. **Verification** — reran the two-file suite: **29 passed**.

## Verification

Exact command and result (final, after both fixes):

```
uv run pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -q
...
29 passed, 1 warning in 3.08s
```

- `pytest` exit code: `0`
- Result: **29 passed**, 0 failed (1 pre-existing Starlette `DeprecationWarning`).

## Skipped Issues

None — `fix_scope=all`, both in-scope findings fixed.

## Notes / Staleness (not rewritten — historical records)

The following committed planning artifacts still quote the pre-fix English literal
`"YAML nesting too deep (exceeds parser limit)"`. They are past-tense records of the
WR-02/CR-01 work and were intentionally **not** rewritten per scope guidance; the
orchestrator may annotate or reconcile them when re-running the review gate:

- `.planning/phases/16-pipe-01-mvp-config-ui/16-VERIFICATION.md:171,179` (WR-02 probe rows)
- `.planning/phases/16-pipe-01-mvp-config-ui/16-UAT.md:33` (WR-02 fix note)
- the previous revision of this `16-REVIEW-FIX.md` (CR-01 report)

---

_Fixed: 2026-10-04T19:21:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
