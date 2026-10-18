---
phase: "16"
slug: "pipe-01-mvp-config-ui"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-04"
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest `>=8.3.0` (Python) + Playwright `^1.62.1` (UI) |
| **Config file** | root `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths=["tests/unit"]`); `playwright.config.js` (web project, port 5174, `VITE_USE_MOCKS=true`) |
| **Quick run command** | `uv run pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -x` |
| **Full suite command** | `uv run pytest` then `npx playwright test tests/admin.spec.js --project=web --reporter=line` |
| **Estimated runtime** | ~60–120 seconds (unit) + ~90 seconds (Playwright, mock mode) |

---

## Sampling Rate

- **After every task commit:** Run the task's own focused `pytest`/Playwright command (RED first, then GREEN).
- **After every plan wave:** Run `uv run pytest`.
- **Before `/gsd-verify-work`:** Full `uv run pytest` green **plus** `npx playwright test tests/admin.spec.js --project=web` green.
- **Max feedback latency:** ~120 seconds (unit) / ~90 seconds (Playwright mock).

---

## Per-Task Verification Map

> Task IDs are assigned by the planner; rows below are seeded at requirement granularity. The planner's tasks must map onto these rows without gaps.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-01-T1 | 16-01 | 1 | PIPE-01 | V4 | Admin-only GET returns `{yaml,updated_at}`; non-admin 403 / unauth 401 | unit (route + fake repo) | `uv run pytest tests/unit/test_http_pipeline_config.py -k get_returns -x` | ✅ | ✅ green |
| 16-01-T1 (dirty gating: 16-04-T2) | 16-04 | 3 | PIPE-01 | — | Page renders editor, loads saved YAML, Save disabled while clean | e2e (Playwright) | `npx playwright test tests/admin.spec.js --project=web -g "pipeline config"` | ✅ | ✅ green |
| 16-02-T2 | 16-02 | 2 | PIPE-02 | V5 | Invalid YAML (syntax) rejected with `{errors:[{path,line,message}]}`, no write | unit (validator) | `uv run pytest tests/unit/test_pipeline_config_validator.py -k syntax -x` | ✅ | ✅ green |
| 16-02-T2 | 16-02 | 2 | PIPE-02 | V5 | Unknown key rejected (`extra_forbidden`), no write | unit (validator + route) | `uv run pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -k unknown -x` | ✅ | ✅ green |
| 16-02-T2 | 16-02 | 2 | PIPE-02 | V5 | Duplicate key rejected (strict loader) | unit (validator) | `uv run pytest tests/unit/test_pipeline_config_validator.py -k duplicate -x` | ✅ | ✅ green |
| 16-02-T2 | 16-02 | 2 | PIPE-02 | V5 | Reject payload is top-level `{"errors":[...]}`, not nested under `detail` | unit (route) | `uv run pytest tests/unit/test_http_pipeline_config.py -k "top_level or verbatim" -x` | ✅ | ✅ green |
| 16-02-T2 (WR-02) | 16-02 | 2 | PIPE-02 | T-16-07 | Deeply nested flow YAML (under the cap) → structured reject, never an unhandled 500 | unit (validator + route) | `uv run pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -k nested -x` | ✅ | ✅ green |
| 16-02-T2 (CR-01) | 16-02 | 2 | PIPE-02 | T-16-08 | Unmarked YAML error (control char / `ReaderError`) → structured reject, never an unhandled 500 | unit (validator + route) | `uv run pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -k control_char -x` | ✅ | ✅ green |
| 16-04-T1 | 16-04 | 3 | PIPE-02 | — | UI renders every error row + fallback copy, document stays dirty | e2e (Playwright) | `npx playwright test tests/admin.spec.js --project=web -g "validation"` | ✅ | ✅ green |
| 16-01-T1 | 16-01 | 1 | PIPE-03 | V4 | Valid save round-trips (GET after PUT returns saved text) | unit (route + fake repo) | `uv run pytest tests/unit/test_http_pipeline_config.py -k round_trip -x` | ✅ | ✅ green |
| 16-01-T1 (UI empty block: 16-04-T2) | 16-04 | 3 | PIPE-03 | — | Empty state: no row → 200 empty DTO / UI empty block | unit + e2e | `uv run pytest tests/unit/test_http_pipeline_config.py -k empty -x` | ✅ | ✅ green |
| 16-01-T1 | 16-01 | 1 | PIPE-03 | V4 | Non-admin GET/PUT → 403; unauthenticated → 401 | unit (route) | `uv run pytest tests/unit/test_http_pipeline_config.py -k admin -x` | ✅ | ✅ green |
| 16-04-T1 | 16-04 | 3 | PIPE-03 | V5 | SPA reaches config only via `pipelineConfigApi.js` (no Supabase import in page) | unit (static/AST guard) | `uv run pytest tests/unit/test_http_pipeline_config.py -k no_supabase` | ✅ | ✅ green |
| 16-04-T2 | 16-04 | 3 | PIPE-EXEC guard | — | No run/trigger/scheduler control renders | e2e (Playwright) | `npx playwright test tests/admin.spec.js --project=web -g "no execution"` | ✅ | ✅ green |
| 16-03-T1 | 16-03 | 3 | — (migration) | V4 | Migration `011` contract: singleton + RLS enabled + no permissive policy + no wipe | unit (migration contract) | `uv run pytest tests/unit/test_phase16_migration_011.py -x` | ✅ | ✅ green |
| 16-03-T2 | 16-03 | 3 | — (CORS) | — | CORS advertises `PUT` for the live browser preflight | unit (CORS) | `uv run pytest tests/unit/test_cors.py -k put -x` | ✅ | ✅ green |
| 16-03-T2 | 16-03 | 3 | — (wiring) | V4 | Live container wires `SupabasePipelineConfigRepository` | unit (wiring) | `uv run pytest tests/unit/test_live_container_wiring.py -k pipeline -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_pipeline_config_validator.py` — PyYAML syntax/duplicate/non-string/empty + Pydantic extra/type/required, covering PIPE-02.
- [x] `tests/unit/test_http_pipeline_config.py` — GET/PUT route, auth gate, top-level error payload, round-trip, empty, 503 guard, PIPE-03 boundary guard.
- [x] `tests/unit/test_phase16_migration_011.py` — mirrors `test_phase5_migration_005.py` (singleton, `enable row level security`, no `create policy`, no wipe).
- [x] `backend/src/backend/tests_support/in_memory.py` — `InMemoryPipelineConfigRepository` (+ validator fake, with `save_count`).
- [x] `tests/admin.spec.js` — pipeline-config describe blocks + harness reset in `gotoAsRole`.
- [x] Extend `tests/unit/test_cors.py` (PUT preflight) and `tests/unit/test_live_container_wiring.py` (new adapter).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Supabase migration `011` apply | PIPE-03 | No `POSTGRES_URL` in default env; operator applies via Studio SQL (established 005–010 path) | Apply `011_phase16_pipeline_config.sql` in Supabase Studio; verify `select count(*) from public.pipeline_config` returns 0 or 1; confirm RLS enabled with no permissive policy |
| Live browser CORS preflight (`PUT` cross-origin) | PIPE-01/03 | Mock-mode Playwright cannot exercise cross-origin preflight | Run the SPA against a live backend origin and confirm the `PUT /admin/pipeline/config` preflight succeeds |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-05 (audit found 0 gaps)

---

## Validation Audit 2026-10-05

Re-run of `/gsd-validate-phase 16` (State A — audit existing `16-VALIDATION.md`). Source delta since the prior verification: `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` (CR-01 `yaml.YAMLError` branch, IN-01 localized `_TOO_DEEP_MESSAGE`, IN-02 test refactor) plus `tests/unit/test_http_pipeline_config.py` and `tests/unit/test_pipeline_config_validator.py`. Every branch of the changed validator was cross-referenced to a named, passing test.

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Evidence (all green):
- `uv run pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -q` → 29 passed
- `uv run pytest tests/unit/test_phase16_migration_011.py tests/unit/test_supabase_pipeline_config_repository_contract.py tests/unit/test_live_container_wiring.py tests/unit/test_cors.py -q` → 22 passed
- `npm run test:web -- tests/admin.spec.js` → 50 passed (includes all pipeline-config cases)

No gaps → no `gsd-nyquist-auditor` spawn, no tests generated. The two seeded "reject payload" robustness behaviors (WR-02 deep nesting, CR-01 unreadable characters) were promoted to first-class rows above.
