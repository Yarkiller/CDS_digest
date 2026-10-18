---
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
plan: 01
subsystem: backend-adapter
tags: [yaml, pyyaml, safe-loader, merge-keys, dos-bound, fastapi, pytest]

# Dependency graph
requires: []
provides:
  - "YAML merge-key (`<<`) acceptance in the strict validator: the merge key node is skipped by its tag and duplicate detection scans a pristine pre-merge own-key snapshot"
  - "_project + MAX_MERGE_DEPTH (8) / MAX_MERGE_ENTRIES (256), enforced at the head of _StrictSafeLoader.flatten_mapping — before SafeConstructor's k^depth node multiplication"
  - "_MERGE_TOO_BIG_MESSAGE + the `except _MergeExpansionTooLarge` clause inside validate()'s existing parse try (no new 500 path)"
  - "tests/unit/test_pipeline_config_merge.py — the yaml.SafeLoader oracle corpus, the schema-accept subset, the duplicate-reject pair, the bounded bomb / boundary pins, the cycle guard and the loader safety-profile guard"
affects: [17-02, 18, 19, 20, 21, 22, 23, 24]

# Actuals (#2632) — pairs with the plan's `estimate` (tokens 20000 / raw 40000 / tasks 2).
# `commits` is measured as `git rev-list --count plan_head_before..plan_head_after` at
# SUMMARY-write time, i.e. the four task commits; the docs(17-01) metadata commit is separate.
actuals:
  tokens: 6033
  tasks: 2
  commits: 4

plan_head_before: 4e0982e1be434f27920bc112bd49c60e16fcf39e
plan_head_after: 35b76817768bfde301628aa920f2d8a4cc6758df

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-flatten projection: a memoised, cycle-guarded (entries, depth) walk of the composed node graph, evaluated before the expansion it prevents"
    - "Pristine own-key snapshot: capture node.value at the head of flatten_mapping, the only window before PyYAML's in-place `node.value = merge + node.value`"
    - "yaml.SafeLoader-as-oracle parametrized corpus: the reference mapping is the merge-semantics contract, never hand-written per-shape asserts"

key-files:
  created:
    - tests/unit/test_pipeline_config_merge.py
  modified:
    - backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
    - tests/unit/test_http_pipeline_config.py

key-decisions:
  - "Merge-introduced collisions are override semantics, not errors (D-03): an explicit own key beats a merged one, the first merge source wins — pinned by oracle equality rather than by a hand-written case list"
  - "The merge key is skipped by tag `tag:yaml.org,2002:merge`, never by the literal '<<' — a quoted '<<' stays an ordinary string key (D-02)"
  - "Both bounds are enforced before the expensive flatten step and are independently load-bearing: fan-out 2 at 8 levels is admissible on entries alone (exactly 256) yet refused by the depth bound (D-04)"
  - "Entries budget inclusive at exactly MAX_MERGE_ENTRIES and depth inclusive at exactly MAX_MERGE_DEPTH: 256 projected entries / depth 8 validate, 257 / depth 9 are refused"
  - "The bound raises a plain Exception (not a ConstructorError/MarkedYAMLError) so the reject row stays `{path: '', message: …}` with no `line` (D-06/D-09)"
  - "RED was recorded in two stages: the corpus module failed with the PyYAML merge-tag constructor error against the unmodified adapter, then the bound tests were added (they cannot be collected until the bound constants exist)"

patterns-established:
  - "Bound a parser amplification by walking the composed node graph pre-construction, memoised by node identity"
  - "Snapshot mutable parser state at the earliest hook, then scan the snapshot so an in-place mutation cannot corrupt a strictness check"

requirements-completed: [PIPE-04, PIPE-05]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "A valid `<<` merge document loads to the same mapping as yaml.safe_load and passes the un-widened four-key schema"
    requirement: PIPE-04
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_strict_loader_matches_safeloader_oracle (12 rows) + #test_merge_document_validates (9 rows) + #test_merge_override_and_first_source_semantics"
        status: pass
    human_judgment: false
  - id: D2
    description: "An admin PUT of a merge-key config returns 200, persists once, and a later GET returns the identical yaml text"
    requirement: PIPE-04
    verification:
      - kind: integration
        ref: "tests/unit/test_http_pipeline_config.py#test_put_merge_document_round_trips"
        status: pass
    human_judgment: false
  - id: D3
    description: "A tiny fan-out merge bomb is refused with exactly one {path: '', message: _MERGE_TOO_BIG_MESSAGE} row, no `line`, in under 0.5 s (measured ~2 ms) and with zero writes"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_merge_bomb_is_rejected_in_bounded_time (side-key + root-anchored) + #test_merge_bound_boundaries + #test_self_referential_merge_is_refused_not_hung"
        status: pass
      - kind: integration
        ref: "tests/unit/test_http_pipeline_config.py#test_put_merge_bomb_returns_400_and_writes_nothing"
        status: pass
    human_judgment: false
  - id: D4
    description: "Duplicate-key rejection (with and without a `<<`), the verbatim reject envelope, and the loader's arbitrary-object refusal are provably unchanged"
    requirement: PIPE-05
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_merge.py#test_explicit_duplicate_still_rejected + #test_unsafe_tag_is_refused_not_constructed; tests/unit/test_pipeline_config_validator.py (16 passed); tests/unit/test_http_pipeline_config.py#test_put_invalid_error_rows_are_verbatim_and_top_level"
        status: pass
    human_judgment: false

# Metrics
duration: 9min
completed: 2026-10-14
status: complete
---

# Phase 17 Plan 01: Tracer — merge-key acceptance + pre-flatten expansion bound Summary

**The strict YAML validator now accepts `<<` merge documents with SafeLoader-identical mappings and refuses a 489-char fan-out merge bomb in ~2 ms with one structured 400 row, without weakening duplicate-key rejection**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-14T11:53:00Z
- **Completed:** 2026-10-14T12:01:53Z
- **Tasks:** 2
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments

- The pre-fix failure is reproduced and fixed: `_StrictSafeLoader.construct_mapping` used to construct the merge-tagged key node before `SafeConstructor.flatten_mapping` could run, so every valid `<<` document died with `could not determine a constructor for the tag 'tag:yaml.org,2002:merge'`. The scan now skips the merge node **by tag** and iterates a pristine `_own_keys` snapshot taken at the head of a new `flatten_mapping` override — the only window before PyYAML mutates `node.value` in place.
- The merge fix and the DoS bound ship in the same diff (ROADMAP criterion 4): `_project` returns `(entries, depth)` over the composed node graph, memoised by node identity and cycle-guarded, and is evaluated **before** `super().flatten_mapping(node)` — so the `k^depth` node multiplication never materialises. `MAX_MERGE_ENTRIES = 256` / `MAX_MERGE_DEPTH = 8`, both inclusive at the limit.
- The reject rides the existing envelope with zero wiring changes: `_MergeExpansionTooLarge` (deliberately not a `ConstructorError`, so no `line` is attached) is mapped inside the existing parse `try` to `_MERGE_TOO_BIG_MESSAGE`, and the route returns `{"errors": [{"path": "", "message": …}]}` with zero writes.
- The `yaml.SafeLoader`-as-oracle corpus replaced hand-written cases: 12 documents (including the nested-collision anchor-holder trap that only a loop catches) assert mapping equality, 9 of them also validate against the un-widened four-key schema.
- Both bounds are pinned as load-bearing, with the entries budget proven inclusive from two independent axes: `_nested_merge_chain(2, 6)` projects `(256, 7)` and validates, its `(2, 7)` successor (512 entries) is refused; `_wide_merge_source(256)` loads to a 256-key mapping, 257 is refused.

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "accept a valid merge document, refuse a merge bomb"** — RED/GREEN, three commits:
   - `137863d` (test) — failing oracle/schema corpus: 20 failed / 5 passed, every merge document dying with the PyYAML merge-tag constructor error
   - `e3c001f` (test) — failing bound + boundary corpus (not collectable until the bound constants exist)
   - `58e469c` (feat) — the parse-gate fix, `_project`, the constants, and the `validate()` clause
2. **Task 2: HTTP round-trip and zero-write proofs** - `35b7681` (test)

**Plan metadata:** see the `docs(17-01): complete tracer-merge-key-acceptance plan` commit

_Note: Task 1 was `tdd="true"`, hence the multiple RED → GREEN commits._

## Files Created/Modified

- `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` — the only production file: `_MERGE_TAG`, `MAX_MERGE_DEPTH`, `MAX_MERGE_ENTRIES`, `_MERGE_TOO_BIG_MESSAGE`, `_MergeExpansionTooLarge`, `_project`, `_StrictSafeLoader.__init__`/`flatten_mapping`, the tag-skip + pristine-snapshot `construct_mapping`, and the new `except` clause. The four-key schema, `MAX_PIPELINE_CONFIG_CHARS`, the `Loader=` argument and the class hierarchy are untouched.
- `tests/unit/test_pipeline_config_merge.py` (new) — 29 tests: the 12-row oracle corpus, the 9-row schema-accept subset, the override/first-source semantics, the duplicate-reject pair (with and without `<<`), the bounded bomb (side-key + root-anchored), the boundary table, the cycle guard, and the loader safety-profile guard.
- `tests/unit/test_http_pipeline_config.py` — +2 tests on the existing `_real_validator_admin_env()` harness; the D-09 tripwire `test_put_invalid_error_rows_are_verbatim_and_top_level` is byte-identical (the module diff is additions only).

## Decisions Made

- **The oracle is the contract (D-03).** Merge-introduced collisions are override semantics, not errors. Rather than hand-writing one assert per shape, every accepted document is compared against `yaml.safe_load` — this is what surfaced the nested-collision anchor-holder rows (`defaults: &c` / `h: &c`), which a skip-only fix would have rejected with `found duplicate key ('roles')`.
- **Skip by tag, scan the snapshot (D-02).** A quoted `'<<'` resolves to `tag:yaml.org,2002:str` and stays an ordinary key (pinned by corpus row 9), and the duplicate scan reads the pre-merge snapshot so an already-flattened merge source cannot look like a duplicate.
- **Both bounds, before the work (D-04/D-05).** The projection runs at the head of `flatten_mapping`, and `_MergeExpansionTooLarge` is caught inside the existing parse `try` so it cannot become a new 500 path. Fan-out 2 at 8 levels stays the proof that the two bounds are independently load-bearing (entries exactly at budget, refused on depth).
- **Inclusivity is pinned from both axes.** `_nested_merge_chain(2, 6)` projects exactly `(256, 7)` and validates; `_wide_merge_source(256)` projects `(256, 2)` and loads; the +1 successor of each is refused. A `>=` off-by-one in the bound now fails the suite.
- **A plain `Exception` for the bound (D-06).** `_MergeExpansionTooLarge` is not a `MarkedYAMLError`, so the reject row keeps the sibling `{path: '', message: …}` shape (no `line`) and never reuses `_OVER_CAP_MESSAGE` — asserted explicitly, since the bomb is 2.5 % of the size cap.

## Deviations from Plan

None - plan executed exactly as written. Two additive, test-side refinements are noted under Issues Encountered; neither changes production behaviour or the shipped contract.

## Issues Encountered

- **RED had to be recorded in two stages.** The plan's RED gate requires the module to fail with the PyYAML merge-tag constructor error "not with an import or collection error" — but the bound tests import `_project`, `MAX_MERGE_DEPTH`, `MAX_MERGE_ENTRIES` and `_MERGE_TOO_BIG_MESSAGE`, which do not exist before the production edit. The corpus half was therefore written and run first (RED, recorded: 20 failed / 5 passed with the constructor error), and the bound half was appended afterwards as a second `test(...)` commit. Both stages are in the git history; neither bypassed the failable-test-first rule.
- **The duplicate-reject pair carries a per-document expected line.** The plan quotes `line == 2` for the explicit duplicate; the second document carries `<<: &b {language: ru}` on line 1, so its duplicate lands on line 3. `DUPLICATE_REJECTED` is parametrized over `(document, expected_line)` — the mark-sensitive assertion is preserved, not weakened. (`test_pipeline_config_validator.py::test_duplicate_top_level_key_is_rejected_not_last_wins` still reports `line == 2`, unchanged.)
- **Fixture lengths differ from the plan's parenthetical numbers.** The plan quotes "166 characters" for `EXACT_ENTRY_BUDGET` and "~480" for the bomb; the committed constructions are 220 and 489 characters (whitespace/inline-vs-block choices in the four-key leaf). The load-bearing facts are unchanged and asserted: the projection is exactly `(256, 7)`, the bomb is well under `MAX_PIPELINE_CONFIG_CHARS` (asserted in-test, so the reject can never be the size cap), and the bounded-time ceiling holds with a >100× margin.

## TDD Gate Compliance

| Gate | Commit | Evidence |
|------|--------|----------|
| RED (corpus) | `137863d` | `pytest tests/unit/test_pipeline_config_merge.py -q` → 20 failed / 5 passed; every merge document failed with `could not determine a constructor for the tag 'tag:yaml.org,2002:merge'` |
| RED (bound) | `e3c001f` | Same command → `ImportError: cannot import name 'MAX_MERGE_DEPTH'` (expected: the constants are part of the production change) |
| GREEN | `58e469c` | Same command → 29 passed |
| REFACTOR | — | Not needed: no cleanup was identified after green |

## Verification

- `.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_merge.py -q` → **29 passed** (tracer gate re-run after the task commit)
- `.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_pipeline_config_merge.py tests/unit/test_http_pipeline_config.py -q` → **60 passed** (16 + 29 + 15)
- `.venv\Scripts\python.exe -m pytest -q` → **798 passed** (pre-change baseline of 796 + 2 HTTP tests; the 29 merge tests are new)
- `_StrictSafeLoader` still subclasses `yaml.SafeLoader`; `validate()` still calls `yaml.load(yaml_text, Loader=_StrictSafeLoader)`; no `safe_load`/`FullLoader`/`UnsafeLoader` and no dropped `Loader=` argument anywhere in the adapter.

## Known Stubs

None.

## Threat Flags

None — no new network endpoint, auth path, file access pattern or schema change is introduced. The change tightens an existing DoS surface (T-17-01/02/03) inside the already-published 400 envelope; the loader class hierarchy and the `Loader=` argument are unchanged (T-17-06).

## Next Phase Readiness

- Ready for `17-02` (the anchor-holder teaching message): `_EXTRA_ANCHOR_KEY_MESSAGE` and `_anchor_holder_keys` slot into the same adapter beside the new constants, and the D-09 tripwire is confirmed green and untouched, which is the precondition for gating that translation on anchor identity.
- No blockers. The four-key schema, `MAX_PIPELINE_CONFIG_CHARS`, the HTTP layer and `composition/` are untouched, so the phase's single-production-file constraint holds for plan 02 as well.

## Self-Check: PASSED

- Files: `tests/unit/test_pipeline_config_merge.py` FOUND, `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` FOUND, `tests/unit/test_http_pipeline_config.py` FOUND
- Commits: `137863d` FOUND, `e3c001f` FOUND, `58e469c` FOUND, `35b7681` FOUND

---
*Phase: 17-yaml-merge-key-acceptance-in-the-strict-validator*
*Completed: 2026-10-14*
