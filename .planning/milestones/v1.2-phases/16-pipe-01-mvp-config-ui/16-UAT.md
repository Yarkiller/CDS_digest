---
status: complete
phase: 16-pipe-01-mvp-config-ui
source: [16-VERIFICATION.md]
started: 2026-10-04T12:15:00.000Z
updated: 2026-10-04T18:15:00.000Z
---

## Current Test

[testing complete]

## Tests

### 1. Live persistence round-trip (PIPE-03 DoD)
expected: In live mode (VITE_USE_MOCKS=false against the shared VM), open /admin/pipeline as admin, save a valid YAML document, reload, and confirm the saved YAML is returned; the row persists to public.pipeline_config (id=1) with count 1.
result: pass

### 2. Visual overflow/backstop checks on /admin/pipeline (7 items)
expected: Editor scrolls internally on a long config; the Save toolbar stays reachable and never overlaps; the error panel wraps long text; the nav item stays usable at narrow widths.
result: pass
source: automated
evidence: Playwright/chromium @1280 and @480 — editor wrap=off + overflow-auto + min-h-[20rem]/max-h-[60vh], vertical scroll 6576>318 and horizontal scroll 3654>1118 on a 250-line/400-char config; Save toolbar visible inside the viewport at 1280 and 480; 30-error reject panel: every row wraps (scrollWidth<=clientWidth) and the page has no horizontal overflow; empty state fits at 480; «Пайплайн» nav visible at 480. Screenshots: .planning/tmp/uat16/01..05.

### 3. Unsaved-changes guard in a real browser (WR-04/WR-05)
expected: After editing the YAML, (a) closing/reloading the tab and (b) clicking an in-app NavLink (e.g. «Архив») presents a leave-confirm; Cancel keeps the edit. NOTE: the code uses window.confirm inside beforeunload (unreliable in real browsers) and registers no router-level guard, so in-app SPA navigation currently discards the draft without a prompt.
result: pass
note: Scoped as optional UX, not a Phase 16 acceptance requirement. The must-have (exact copy «Есть несохранённые изменения. Уйти без сохранения?» + reset guard) is delivered and asserted. The residual WR-04/WR-05 behavior gap is accepted as a known limitation (DB is safe: unsaved = nothing written; only the textarea draft is lost) and recorded under Deferred Follow-Ups.

### 4. Deep-nesting robustness (WR-02)
expected: PUT a config of ~3000 nested flow brackets (under the 20k cap) returns a structured 400 {errors:[...]}.
result: pass
note: Fixed in-session via TDD (commit 758ddac). Observed defect was an unhandled RecursionError → HTTP 500, violating PIPE-02's strict-validation contract. Fix wraps yaml.load at the adapter boundary and maps RecursionError to a PipelineConfigValidationError with one {path:"", message:"YAML nesting too deep (exceeds parser limit)"} row. Evidence: tests/unit/test_pipeline_config_validator.py#test_deeply_nested_flow_document_is_rejected_not_recursion_error and tests/unit/test_http_pipeline_config.py#test_put_deeply_nested_yaml_returns_400_not_500 (asserts 400 + top-level errors + save_count 0). Full backend suite 759 passed.

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Deferred Follow-Ups

- test: 3
  idea: "WR-04/WR-05 — unsaved-changes guard accepted as a known limitation: window.confirm inside beforeunload is unreliable in real browsers, and no router-level guard is registered, so in-app SPA navigation discards the draft silently. DB stays safe (unsaved = nothing written); only the textarea draft is lost."
  deferred_at: 2026-10-04
- test: 0
  idea: "Admin nav grouping (option C, UX preference not SPEC): remove top-level «Пайплайн»; expose pipeline config via an admin tab-bar «Дайджест | Пайплайн», with top-level «Админ» → /admin/digest. Route /admin/pipeline unchanged; no new route. Amend 16-UI-SPEC A-2 when implemented (TDD: failing Playwright test first)."
  deferred_at: 2026-10-04

## Gaps

- gap_id: G-16-4
  truth: "A config of ~3000 nested flow brackets (under the 20k cap) is rejected with a structured 400 {errors:[...]}, never an unhandled 500"
  status: resolved
  reason: "User reported: RecursionError → HTTP 500 instead of a structured reject; strict-validation contract (PIPE-02) violated"
  severity: major
  test: 4
  resolved_by: "in-session TDD fix (commit 758ddac: catch RecursionError in yaml_pipeline_config_validator → PipelineConfigValidationError)"
  resolved_at: 2026-10-04
  artifacts:
    - path: "backend/src/backend/infrastructure/yaml_pipeline_config_validator.py"
      issue: "yaml.load RecursionError was not caught at the adapter boundary"
  missing:
    - "Catch RecursionError around yaml.load and map to a single structured error row"
  debug_session: ""
