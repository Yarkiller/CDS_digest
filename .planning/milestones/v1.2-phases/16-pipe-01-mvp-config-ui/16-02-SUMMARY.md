---
phase: 16-pipe-01-mvp-config-ui
plan: 02
subsystem: api
tags: [fastapi, pydantic, pyyaml, validation, ports-and-adapters, pipeline-config, pytest]

# Dependency graph
requires:
  - phase: 16-pipe-01-mvp-config-ui
    plan: 01
    provides: PipelineConfig domain model + merged repository/validator ports + validate-then-save use-case + GET/PUT admin routes + tracer route tests
provides:
  - YamlPipelineConfigValidator (strict SafeLoader + Pydantic extra=forbid) as the sole yaml import site
  - PipelineConfigError(path, message, line?) with to_dict() omitting line when None
  - PipelineConfigValidationError carrying tuple[PipelineConfigError, ...]
  - PUT /admin/pipeline/config top-level JSONResponse 400 {"errors":[...]} reject branch with zero writes
  - AppContainer.pipeline_config / pipeline_config_validator fields + build_in_memory_container wiring
  - InMemoryPipelineConfigRepository save recording (save_count)
  - pyyaml==6.0.3 as an explicit backend dependency
affects: [16-03 live persistence, 16-04 full page surface]

actuals:
  tokens: 4727    # chars/4 over the realized diff (18,908 changed chars)
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: [pyyaml 6.0.3]
  patterns:
    - "Strict SafeLoader subclass rejecting duplicate keys via construct_mapping override"
    - "Pydantic ConfigDict(extra='forbid') fixed schema mapped to dotted-path errors"
    - "Adapter-boundary error mapping: parser/pkg failures -> domain PipelineConfigValidationError"
    - "Top-level JSONResponse(400, {errors:[...]}) reject payload (never HTTPException detail nesting)"
    - "Optional container fields (None defaults) so bare AppContainer(...) keeps constructing"

key-files:
  created:
    - backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
    - tests/unit/test_pipeline_config_validator.py
  modified:
    - backend/src/backend/domain/pipeline_config.py
    - backend/src/backend/domain/errors.py
    - backend/src/backend/interface/http/routes/admin.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/interface/http/app.py
    - backend/src/backend/pyproject.toml
    - uv.lock
    - tests/unit/test_http_pipeline_config.py
    - tests/unit/test_cors.py

key-decisions:
  - "Locked schema key set to {template, roles, language, max_chars}: template Literal[lecture|podcast], roles list[Literal[employee|analyst|ds]] min_length=1, language str min_length=1, max_chars int gt=0 (backend defines the role Literal locally — no data-collection import)"
  - "Reject payload is a top-level JSONResponse(400, {errors:[...]}); HTTPException(detail=...) nesting explicitly avoided (RESEARCH Pitfall 2)"
  - "MAX_PIPELINE_CONFIG_CHARS=20000 cap is checked before parse (DoS guard, T-16-07)"
  - "CORS allow_methods now advertises PUT (Rule 2 deviation) so the live browser preflight reaches the reject path"

patterns-established:
  - "Strict YAML validation: SafeLoader subclass + Pydantic extra=forbid, both mapped to PipelineConfigError(path, line?, message)"
  - "Zero-write reject: validator runs before repo.save; route tests assert save_count == 0"

requirements-completed: [PIPE-02]

coverage:
  - id: D1
    description: "Strict YAML parse (syntax/duplicate/non-string-key/empty/multi-document) rejected with structured PipelineConfigError(path, line?)"
    requirement: PIPE-02
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_validator.py#test_duplicate_top_level_key_is_rejected_not_last_wins"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fixed-key Pydantic extra=forbid schema rejects unknown keys/type/required/min-length with dotted paths and no line"
    requirement: PIPE-02
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_validator.py#test_unknown_key_is_rejected_by_extra_forbid"
        status: pass
    human_judgment: false
  - id: D3
    description: "PUT invalid YAML returns 400 with top-level {errors:[...]} (no detail nesting) and zero repository writes"
    requirement: PIPE-02
    verification:
      - kind: unit
        ref: "tests/unit/test_http_pipeline_config.py#test_put_invalid_yaml_returns_400_top_level_errors_and_writes_nothing"
        status: pass
    human_judgment: false
  - id: D4
    description: "Schema exposes exactly {template, roles, language, max_chars} — no secret/credential or score_factors key"
    requirement: PIPE-03
    verification:
      - kind: unit
        ref: "tests/unit/test_pipeline_config_validator.py#test_schema_exposes_only_documented_non_secret_keys"
        status: pass
    human_judgment: false
  - id: D5
    description: "Container wiring: build_in_memory_container yields InMemoryPipelineConfigRepository + YamlPipelineConfigValidator; AppContainer None defaults"
    verification:
      - kind: unit
        ref: "tests/unit/test_http_pipeline_config.py#test_build_in_memory_container_wires_real_validator_and_repo"
        status: pass
    human_judgment: false
  - id: D6
    description: "pyyaml 6.0.3 is an explicit backend dependency and imports in the uv env"
    verification:
      - kind: unit
        ref: "command: uv run python -c \"import yaml; print(yaml.__version__)\" -> 6.0.3"
        status: pass
    human_judgment: false
  - id: D7
    description: "CORS allow-list advertises PUT so the live browser preflight reaches PUT /admin/pipeline/config"
    verification:
      - kind: unit
        ref: "tests/unit/test_cors.py#test_put_method_is_advertised_in_cors_preflight"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-10-04
status: complete
commits: 3
plan_head_before: ca1a5867a9c8298d96b5ff032f53ed3e8a50ffc0
plan_head_after: 94b786fd83ec7b90346f4c3d4db35b538310266f
---

# Phase 16 Plan 02: Strict validate-before-save with structured errors Summary

**Server-authoritative strict YAML + Pydantic `extra="forbid"` validator whose rejects return a top-level `{"errors":[{path,line?,message}]}` 400 with zero repository writes, wired into the default container as PyYAML 6.0.3**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-04T10:53:00Z
- **Completed:** 2026-10-04T10:59:35Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- `YamlPipelineConfigValidator` — the only `yaml` import site in the backend — parses with a strict `_StrictSafeLoader` (duplicate keys rejected, no silent last-wins) and validates the fixed 4-key `PipelineConfigModel` (`extra="forbid"`), mapping both failure sources to `PipelineConfigError(path, line?, message)`
- `PipelineConfigValidationError` carried to the PUT route, which returns a **top-level** `JSONResponse(400, {"errors":[...]})` — never nested under `detail` — and calls the repository **zero** times on reject
- `AppContainer.pipeline_config` / `pipeline_config_validator` declared with `None` defaults; `build_in_memory_container` wires `InMemoryPipelineConfigRepository()` + `YamlPipelineConfigValidator()`; a bare `AppContainer(...)` still constructs
- Schema key set locked and asserted to exactly `{template, roles, language, max_chars}` — no secret/credential or `score_factors` key (PIPE-03)
- `pyyaml==6.0.3` promoted from a transitive lock entry to an explicit `backend` dependency
- Full backend suite green: **745 passed** (up from 726)

## Task Commits

Each task was committed atomically; Task 2 ran the RED→GREEN cycle:

1. **Task 1** — `09c5ab7` (chore): add pyyaml 6.0.3 as an explicit backend dependency
2. **Task 2 RED** — `397ac41` (test): add failing tests for strict validator and 400 reject plumbing
3. **Task 2 GREEN** — `94b786f` (feat): implement strict YAML validator and 400 reject plumbing

**Plan metadata:** final `docs(16-02)` metadata commit (SUMMARY + STATE + ROADMAP + REQUIREMENTS).

_Note: no REFACTOR commit was needed — the GREEN implementation was already minimal._

## Files Created/Modified
- `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` — strict SafeLoader + Pydantic schema + error mapping (sole `import yaml`)
- `backend/src/backend/domain/pipeline_config.py` — `PipelineConfigError` frozen dataclass with `to_dict()`
- `backend/src/backend/domain/errors.py` — `PipelineConfigValidationError(errors: tuple[PipelineConfigError, ...])`
- `backend/src/backend/interface/http/routes/admin.py` — PUT reject branch returning top-level `JSONResponse(400, {"errors":[...]})`
- `backend/src/backend/composition/container.py` — new optional fields + in-memory wiring
- `backend/src/backend/tests_support/in_memory.py` — `InMemoryPipelineConfigRepository.saves` / `save_count`
- `backend/src/backend/interface/http/app.py` — CORS `allow_methods` now includes `PUT`
- `backend/pyproject.toml`, `uv.lock` — `pyyaml==6.0.3`
- `tests/unit/test_pipeline_config_validator.py` — 13 validator cases (syntax/duplicate/non-string/empty/multi-doc/unknown/type/required/valid/cap/schema keys/to_dict)
- `tests/unit/test_http_pipeline_config.py` — 4 new route/wiring cases + real-validator harness
- `tests/unit/test_cors.py` — PUT preflight assertion

## Decisions Made
- Locked the fixed schema to `{template, roles, language, max_chars}` with `template: Literal["lecture","podcast"]`, `roles: list[Literal["employee","analyst","ds"]]` (`min_length=1`), `language: str` (`min_length=1`), `max_chars: int` (`gt=0`); the role `Literal` is defined locally in backend because backend cannot import `data-collection`.
- Reject status locked to 400 via `JSONResponse` (top-level `errors`), never `HTTPException(detail=...)`.
- `MAX_PIPELINE_CONFIG_CHARS = 20000` checked before parse to reject oversized documents.
- `_require_pipeline_config` 503 guard retained; `attach_repo=False` tests now explicitly set `container.pipeline_config = None`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Advertised PUT in the CORS allow-list**
- **Found during:** Task 2 (route/reject plumbing)
- **Issue:** `app.py` `allow_methods` was `["GET", "POST", "PATCH", "OPTIONS"]` — it did not include `PUT`. The browser sends an `OPTIONS` preflight for `PUT /admin/pipeline/config`, so the live save/reject path would fail cross-origin while mock-mode Playwright stayed green (RESEARCH Pitfall 1, T-16-06). The plan did not list `app.py` in its `<files>`.
- **Fix:** Added `"PUT"` to `allow_methods` and a `PUT` preflight assertion in `tests/unit/test_cors.py`.
- **Files modified:** `backend/src/backend/interface/http/app.py`, `tests/unit/test_cors.py`
- **Verification:** `test_put_method_is_advertised_in_cors_preflight` passes; full suite 745 green.
- **Committed in:** `94b786f` (part of Task 2 GREEN).

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** The CORS fix is required for the reject path to function in a live browser; it adds no new scope beyond the already-planned PUT route.

## Issues Encountered
- The RED run surfaced as a pytest collection error (`ImportError: cannot import name 'PipelineConfigValidationError'`) because the production modules did not exist yet — the expected RED cause (mirrors 16-01). Resolved by the GREEN implementation.
- One first-pass test assertion was wrong (`template: 5\nroles: []` also omitted `max_chars`, so the validator correctly reported four errors). Fixed within the GREEN step; the production behavior was already correct.

## Known Stubs

None. All previously-deferred items from 16-01 are now implemented: the PUT reject branch and the container field declaration/wiring.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: cors-method-widening | backend/src/backend/interface/http/app.py | Added `PUT` to the CORS allow-list. Not a new trust boundary — it improves preflight for the already-shipped admin-gated PUT route (require_admin + RLS deny-by-default). |

(All other surface is covered by the plan's `<threat_model>`: T-16-05 strict SafeLoader, T-16-06 zero-write reject, T-16-07 length cap, T-16-08 verbatim parser/`msg` text only, T-16-09 duplicate-key rejection.)

## User Setup Required

None - no external service configuration required (live migration `011` is 16-03's `user_setup`).

## Next Phase Readiness
- PIPE-02 is delivered: the server is the single authoritative validator and rejects with the locked structured payload without writing.
- `build_in_memory_container` now wires the real validator, so 16-04's Playwright reject case can exercise the true validation path.
- 16-03 can add the `SupabasePipelineConfigRepository` + migration `011` behind the same `PipelineConfigRepository` port and wire it in `composition/live.py`.
- REQUIREMENTS.md PIPE-02 is marked complete only if the shared-ID gate releases it (no sibling plan declares PIPE-02).

---
*Phase: 16-pipe-01-mvp-config-ui*
*Completed: 2026-10-04*

## Self-Check: PASSED

All declared created files exist on disk and all 3 plan commits (`09c5ab7`, `397ac41`, `94b786f`) are present in `git log`.
