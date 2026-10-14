---
phase: "17"
slug: "yaml-merge-key-acceptance-in-the-strict-validator"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-14"
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `17-RESEARCH.md` § Validation Architecture (1219-line research pass, measured against the repo `.venv` — PyYAML 6.0.3 / CPython 3.12.13 / pytest 9.1.1).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (repo `.venv`) |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]`, `testpaths = ["tests/unit"]`, `pythonpath = ["."]` |
| **Quick run command** | `.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_pipeline_config_merge.py tests/unit/test_http_pipeline_config.py -q` |
| **Full suite command** | `.venv\Scripts\python.exe -m pytest -q` |
| **Estimated runtime** | ~15 seconds full suite; ~11 s for the quick triplet (measured baseline 10.5 s for the two existing files) |

**Baseline before any change:** `29 passed` — 16 in `tests/unit/test_pipeline_config_validator.py` + 13 in `tests/unit/test_http_pipeline_config.py`.

---

## Sampling Rate

- **After every task commit:** Run the quick run command
- **After every plan wave:** Run the full suite command
- **Before `/gsd-verify-work`:** Full suite must be green, and the tripwire `test_put_invalid_error_rows_are_verbatim_and_top_level` must be explicitly green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

**Populated by the planner.** This file is seeded before `17-PLAN.md` exists, so task IDs are not yet assigned. The rows below are the requirement-level contracts the planner must bind each task to; the planner fills `Task ID / Plan / Wave` when writing the plans. Every row is automated — no row is manual-only.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 17-01-T1 | 17-01 | 1 | PIPE-04 | T-17-04 | Valid `<<` document accepted; strict loader mapping equals the `yaml.SafeLoader` oracle mapping | unit (oracle loop) | `.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_merge.py::test_strict_loader_matches_safeloader_oracle -q` | ❌ W0 | ⬜ pending |
| 17-01-T1 | 17-01 | 1 | PIPE-04 | T-17-05 | Valid `<<` document passes schema validation and resolves to exactly the 4 keys | unit | `…::test_merge_document_validates -q` | ❌ W0 | ⬜ pending |
| 17-01-T2 | 17-01 | 1 | PIPE-04 | T-17-04 | Merge document persists and reads back byte-identical (no store on reject) | integration (in-process HTTP) | `.venv\Scripts\python.exe -m pytest tests/unit/test_http_pipeline_config.py -q` | ✅ file, +1 test | ⬜ pending |
| 17-01-T1 | 17-01 | 1 | PIPE-04 | T-17-04 | Explicit duplicate still rejected with the same envelope, with and without a `<<` present | unit + HTTP | `…::test_explicit_duplicate_still_rejected -q` | ❌ W0 | ⬜ pending |
| 17-01-T2 | 17-01 | 1 | PIPE-04 | T-17-04 | Reject envelope rows verbatim + zero writes (tripwire — **PRESERVE**) | integration (in-process HTTP) | `.venv\Scripts\python.exe -m pytest tests/unit/test_http_pipeline_config.py::test_put_invalid_error_rows_are_verbatim_and_top_level -q` | ✅ PRESERVE | ⬜ pending |
| 17-01-T1 | 17-01 | 1 | PIPE-05 | T-17-01 | Merge bomb refused with `_MERGE_TOO_BIG_MESSAGE`, `path=""`, no `line`, bounded time, zero writes | unit | `…::test_merge_bomb_is_rejected_in_bounded_time -q` | ❌ W0 | ⬜ pending |
| 17-02-T1 | 17-02 | 2 | PIPE-05 | T-17-10 | Anchor-holder key (D-07) gets the Russian message naming the key | unit | `…::test_anchor_holder_key_gets_teaching_message -q` | ❌ W0 | ⬜ pending |
| 17-02-T1 | 17-02 | 2 | PIPE-05 | T-17-10 | Genuine unknown key keeps Pydantic's English `extra_forbidden` message with `path` preserved | unit | `.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_validator.py::test_unknown_key_is_rejected_by_extra_forbid -q` | ✅ PRESERVE | ⬜ pending |
| 17-01-T1 | 17-01 | 1 | PIPE-05 | T-17-01 | Depth/entry boundaries (5 accepted / 6 rejected at fan-out 3; 8 accepted / 9 rejected on depth) | unit | `…::test_merge_bound_boundaries -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_pipeline_config_merge.py` — the four fixture groups (oracle-accepted · schema-accepted · must-still-reject · adversarial bomb) plus the `yaml.safe_load` oracle loop. **Write the failing version first** (TDD gate): it must fail with `could not determine a constructor for the tag 'tag:yaml.org,2002:merge'` before any production edit.
- [ ] A merge round-trip test added to `tests/unit/test_http_pipeline_config.py` — reuse the existing `_real_validator_admin_env()` harness; no new harness.
- [ ] Private-symbol import decision — the new tests import `_MERGE_TOO_BIG_MESSAGE` and `_StrictSafeLoader` from the adapter. This is already the established pattern in `test_pipeline_config_validator.py` (it imports `_TOO_DEEP_MESSAGE`, `_UNREADABLE_MESSAGE`), so no new convention is introduced.
- [ ] No framework install needed; no `conftest.py` change needed — the oracle corpus is pure YAML strings, so no fixtures are shared.

---

## Manual-Only Verifications

All phase behaviors have automated verification. No browser test is used for this phase: Pitfall 24 names "a merge-key/config test written as a browser test" as a warning sign, and the SPA mock path has no validator at all (`VITE_USE_MOCKS=true`).

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
