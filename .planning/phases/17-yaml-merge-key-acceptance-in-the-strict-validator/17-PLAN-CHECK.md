---
status: passed
type: plan-check
phase: 17-yaml-merge-key-acceptance-in-the-strict-validator
checked: 2026-10-14
mode: standard
iteration: 3
verdict: VERIFICATION PASSED
blockers: 0
warnings: 0
info: 4
prior_iteration: 2
---

# Phase 17 Plan Check — YAML merge-key acceptance in the strict validator

**Phase goal:** The strict pipeline-config validator accepts a valid YAML merge-key (`<<`) document and persists it, without weakening duplicate-key rejection and without opening a CPU-exhaustion path.
**Plans verified:** `17-01-PLAN.md` · `17-02-PLAN.md`
**Requirements:** PIPE-04, PIPE-05
**Do not replan from this file** — this is a revision-gate report.
**Do not commit from plan-checker.**

## VERIFICATION PASSED

0 blockers, 0 warnings. Both prior blockers are genuinely cleared and were independently re-measured against the repo `.venv` (PyYAML 6.0.3 / CPython 3.12.13). The four remaining items are `info` advisories; three were folded into the plans at this gate and the fourth shipped as a new RED test.

## Prior revision (iteration 2 → 3)

| Prior finding | Severity | Status |
|---------------|----------|--------|
| `17-RESEARCH.md` carried a bare `## Open Questions` heading with no `(RESOLVED)` suffix and no inline RESOLVED lines (iteration 1) | blocker | **Fixed** — `## Open Questions (RESOLVED)` at `17-RESEARCH.md:1174`, all five questions carry inline `**RESOLVED:**` markers |
| Accepted-boundary fixture unproducible: `_nested_merge_chain(2, 5) == (256, 7)` was unreachable under the prescribed "four schema keys at every level" chain, which projects `4 · (2 ** (levels + 1) - 1)` = 124 / 252 / 508 | blocker | **Fixed** — the four schema keys moved to the **leaf** and the enclosing levels became **merge-only**, each merging its child exactly `fanout` times, projecting `(fanout ** levels * 4, levels + 1)`. Re-measured: `_nested_merge_chain(2, 6)` → `(256, 7)`, resolves to exactly the four schema keys and validates; `_nested_merge_chain(2, 7)` → refused; `_wide_merge_source(256)` → `(256, 2)`; `_wide_merge_source(257)` → refused. `17-RESEARCH.md` § Q6 corrected in the same commit (a pure merge chain adds no own keys, so the fan-out-1 chain's entry count stays at 1 and only the depth bound can refuse it) |

## Info advisories and their disposition

| # | Advisory | Disposition |
|---|----------|-------------|
| 1 | `17-02` artifacts/`must_haves` said “+2 tests” while `<behavior>`/`<action>` prescribed three | **Fixed** — both sites now say “+3 tests” and name the inline-merge guard |
| 2 | `17-01` Task 1's enumerated adapter import list omitted `_project` and `_OVER_CAP_MESSAGE`, both asserted by its own acceptance criteria | **Fixed** — the private-symbol import list was extended |
| 3 | “`_nested_merge_chain(2, 7)` projects `(512, 8)` and is refused” is unobservable, because `_project` raises before returning | **Fixed** — the refusal is now the assertion and `512`/depth 8 are stated as arithmetic rationale |
| 4 | The `_project` `stack` cycle guard (self-referential merge) had no covering test, while `17-RESEARCH.md` Assumption A3 said the divergence from `yaml.safe_load` must be pinned | **Fixed** — `test_self_referential_merge_is_refused_not_hung` added as a fourth RED test. Measured: `a: &a {<<: *a}` → `yaml.safe_load` returns `{'a': {}}` while the strict loader refuses with exactly one `{path: "", message: _MERGE_TOO_BIG_MESSAGE}` row. The document is deliberately excluded from `ORACLE_ACCEPTED` — the divergence is the point |

## Gate results

| Gate | Result |
|------|--------|
| Requirements coverage | PASS — 2/2 (PIPE-04, PIPE-05 in both plans) |
| Decision coverage D-01…D-09 | PASS — 17-01 cites D-01,02,03,04,05,06,09; 17-02 cites D-01,05,07,08,09 |
| TDD ordering (RED before production edit) | PASS — every code-touching task states RED FIRST and names its expected failure |
| T-17-01 (merge expansion DoS) threat coverage | PASS — bound enforced before `super().flatten_mapping`, side-key + root-anchored + cyclic bombs all asserted refused in bounded time |
| PIPE-02 tripwire preserved | PASS — `test_put_invalid_error_rows_are_verbatim_and_top_level` untouched; non-merge `score_factors` keeps the English `extra_forbidden` row with no `line` |
| Nyquist compliance (8) | PASS — 4/4 tasks carry an automated command and a stated failing direction |
| Numeric consistency PLAN ↔ RESEARCH ↔ VALIDATION | PASS — 8 / 256, 0.5 s ceiling, 29-test baseline, boundary 5/6, 7/8, 8-refused all agree and were live-reproduced |

Plans verified. Run `/gsd-execute-phase 17` to proceed.

---

*Gate type: Revision Gate (plan-phase Step 12 — recheck)*
