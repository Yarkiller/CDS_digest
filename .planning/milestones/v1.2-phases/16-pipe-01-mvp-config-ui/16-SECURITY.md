---
phase: "16"
slug: "pipe-01-mvp-config-ui"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-04"
---

# Phase 16 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser SPA → FastAPI | Untrusted admin YAML text crosses here | Admin-authored YAML config (untrusted input) |
| FastAPI → PipelineConfigRepository | Persistence boundary through the port | Validated pipeline config document |
| Component → service module | SPA must reach storage only through `pipelineConfigApi.js` (PIPE-03) | `{yaml, updated_at}` DTO |
| PyYAML → parsed Python object | Arbitrary tag/object construction risk if the wrong loader is used | Parsed YAML object graph |
| Validator → repository | Must not write when validation fails | Validated config (write) / none on reject |
| FastAPI (service_role) → Postgres | Backend writes the singleton config row bypassing RLS | `public.pipeline_config` row (`id=1`) |
| anon/authenticated → pipeline_config | Must not read the config directly; RLS is deny-by-default | Table access denied |
| Supabase SDK → adapter | SDK errors must not leak to domain or UI | `PersistenceError` (mapped) |
| Server error payload → DOM | Server-supplied error text is rendered to the admin | Structured validation `errors` rows |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-16-01 | Elevation of Privilege | GET/PUT /admin/pipeline/config | high | mitigate | Both routes use `Depends(require_admin)` reading `profiles.role`; unauth → 401, non-admin → 403; never trusts a JWT role claim (D-10) | closed |
| T-16-02 | Tampering | PipelineConfigSaveRequest / save path | high | mitigate | Request DTO is `extra="forbid"` and accepts only `{yaml: str}`; strict document validation behind the same port | closed |
| T-16-03 | Information Disclosure | SPA ↔ storage boundary | medium | mitigate | SPA reaches config only via `web/src/services/pipelineConfigApi.js`; no Supabase/SQL import in pages or components (PIPE-03) | closed |
| T-16-04 | Denial of Service | YAML document size | medium | mitigate | Editor bounded (`min-h-[20rem]/max-h-[60vh]`); server-side `MAX_PIPELINE_CONFIG_CHARS` cap | closed |
| T-16-05 | Tampering | YAML parser (yaml.load) | high | mitigate | Strict `_StrictSafeLoader(yaml.SafeLoader)` subclass only; never `yaml.load` unsafe loader, `FullLoader` or `UnsafeLoader`; arbitrary tag construction impossible | closed |
| T-16-06 | Tampering | PUT reject path | high | mitigate | `PipelineConfigValidationError` → `JSONResponse(400, {"errors":[...]})` with zero repository writes; server-authoritative, no client schema (D-03/D-07) | closed |
| T-16-07 | Denial of Service | YAML alias / oversized document | high | mitigate | `MAX_PIPELINE_CONFIG_CHARS = 20000` rejected before parse; `safe_load` semantics; multi-document stream rejected | closed |
| T-16-08 | Information Disclosure | validation error messages | low | mitigate | Only parser `problem` text and Pydantic `msg` are surfaced; no stack traces, file paths or secrets returned | closed |
| T-16-09 | Tampering | duplicate keys silently last-wins | medium | mitigate | `construct_mapping` override raises `ConstructorError`; covered by a RED→GREEN duplicate-key test | closed |
| T-16-10 | Elevation of Privilege | public.pipeline_config | high | mitigate | RLS enabled with no permissive policy; only the service_role client (composition) reaches the table; read/write gated by `require_admin` at the routes (D-10) | closed |
| T-16-11 | Tampering | adapter upsert | medium | mitigate | PostgREST/SDK parameterized upsert — no raw SQL; SDK failures mapped to `PersistenceError` at the boundary | closed |
| T-16-12 | Information Disclosure | live DTO / storage leak into UI | medium | mitigate | SPA imports no supabase module (PIPE-03); boundary guard asserts `pipelineConfigApi.js` is the only transport; DTO carries `yaml` + `updated_at` only (D-11) | closed |
| T-16-13 | Repudiation | migration apply | medium | mitigate | `[BLOCKING]` operator gate with runbook §4h verify SQL + dated `Applied (2026-10-04)` line; never reset the shared DB | closed |
| T-16-14 | Information Disclosure | response DTO keys | medium | mitigate | `PipelineConfigResponse` declares only `{yaml, updated_at}`; every GET/PUT success body exposes exactly those keys (no secret/credential field) | closed |
| T-16-15 | Information Disclosure | pipeline-config page / error panel | medium | mitigate | Page renders only the server `errors` rows and the `{yaml, updated_at}` DTO; no secret/credential field read or rendered; boundary guard asserts no supabase import | closed |
| T-16-16 | Tampering | client-side acceptance of invalid config | medium | mitigate | The SPA performs no YAML/schema validation; only a server 400 sets the error panel; a reject keeps the document dirty and never auto-accepts (D-03/D-07) | closed |
| T-16-17 | Spoofing | admin nav / page gate | medium | mitigate | The «Пайплайн» nav item and page render only when the resolved profile role is admin (`appRole === 'admin'`); server-side `require_admin` remains authoritative (D-10) | closed |
| T-16-SC | Tampering | pip installs | high | mitigate | `pyyaml==6.0.3` install gated by a blocking-human package-legitimacy checkpoint; already resolved in `uv.lock` | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

**Summary:** 18 threats registered · 18 closed · 0 open.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-16-01 | threat_flag: cors-method-widening | `PUT` added to the CORS allow-list (`backend/src/backend/interface/http/app.py`) improves preflight for the already-shipped admin-gated PUT route (`require_admin` + RLS deny-by-default). Not a new trust boundary; no new endpoint, auth path, or table exposure. | gsd-secure-phase (orchestrator) | 2026-10-04 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-04 | 18 | 18 | 0 | gsd-secure-phase (L1 grep-depth) |
| 2026-10-04 | 18 | 18 | 0 | gsd-secure-phase re-audit (L1 grep-depth, short-circuit: threats_open 0) |
| 2026-10-05 | 18 | 18 | 0 | gsd-secure-phase re-run, stale re-verification (L1 grep-depth, short-circuit: threats_open 0, register_authored_at_plan_time true, ASVS L1). Re-verified validator mitigations T-16-05/06/07/08/09 against the only changed sources — `yaml_pipeline_config_validator.py`, `tests/unit/test_http_pipeline_config.py`, `tests/unit/test_pipeline_config_validator.py`; hardening only (CR-01/WR-02/IN-01/IN-02), no new trust boundary |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-04
