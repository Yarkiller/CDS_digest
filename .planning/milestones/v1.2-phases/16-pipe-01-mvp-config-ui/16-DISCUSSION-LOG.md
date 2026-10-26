# Phase 16: PIPE-01 MVP config UI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-04
**Phase:** 16-pipe-01-mvp-config-ui
**Areas discussed:** Config content scope, Validation depth, Storage & versioning, Placement

---

## Config content scope

| Option | Description | Selected |
|--------|-------------|----------|
| Pipeline params only | Ingest template/roles/generation limits; no score_factors weights | ✓ |
| Pipeline + score_factors weights | Adds scoring weights (ADUX-06 populated path) | |
| Free-form YAML | No fixed schema | |

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed documented keys | Validatable key set | ✓ |
| Free-form (syntax-only) | Validate well-formedness only | |
| Fixed required top-level + free nested | Hybrid | |

| Option | Description | Selected |
|--------|-------------|----------|
| Backend authoritative | Pydantic model owns the schema; UI renders errors | ✓ |
| Shared schema file | One schema for backend + UI | |

**User's choice:** 2.1a / 2.2a / 2.3a — pipeline-only params, fixed documented keys, backend-authoritative schema.
**Notes:** score_factors weights were explicitly left out → ADUX-06 stays on honest-empty; recorded as deferred (PIPE-EXEC-02).

---

## Validation depth

| Option | Description | Selected |
|--------|-------------|----------|
| Syntax only | YAML well-formedness | |
| Syntax + schema | Keys/types/required | ✓ |
| + Semantic | Ranges, interdependencies | |

| Option | Description | Selected |
|--------|-------------|----------|
| `{path, line, message}` | UI-SPEC error contract | ✓ |
| `{path, message}` | No line | |

| Option | Description | Selected |
|--------|-------------|----------|
| Reject unknown keys | Strict `extra="forbid"` (Phase 12–14 convention) | ✓ |
| Ignore unknown keys | | |
| Warn but accept | | |

| Option | Description | Selected |
|--------|-------------|----------|
| No client pre-check | Server authoritative on save | ✓ |
| Client YAML parse for UX | Hint only | |

**User's choice:** 3.1b / 3.2a / 3.3a / 3.4a — syntax+schema, `{path,line,message}`, strict reject, no client pre-check.
**Notes:** Server is the only validator; no client-only pass (UI-SPEC rule 3).

---

## Storage & versioning

| Option | Description | Selected |
|--------|-------------|----------|
| Singleton row | New `pipeline_config` table: one yaml text + updated_at | ✓ |
| Version rows + pointer | History with a current pointer | |
| JSONB document | Single JSONB blob | |

| Option | Description | Selected |
|--------|-------------|----------|
| No history in MVP | One current version | ✓ |
| Store history, no UI | Rows kept, no surface | |

| Option | Description | Selected |
|--------|-------------|----------|
| Admin-only | Read + write require `profiles.role=admin`; service-role write | ✓ |
| Read any auth, write admin | | |

| Option | Description | Selected |
|--------|-------------|----------|
| `{yaml, updated_at}` | Missing config → empty state | ✓ |
| `{yaml, updated_at, version}` | | |

**User's choice:** 4.1a / 4.2a / 4.3a / 4.4a — singleton row, no history, admin-only, `{yaml, updated_at}`.
**Notes:** Next migration is `011` (after `010`); storage adapter lives in `supabase-integration`, wired in `composition/`.

---

## Placement

| Option | Description | Selected |
|--------|-------------|----------|
| New page + nav | `/admin/pipeline` + «Пайплайн» nav item | ✓ |
| Embed in `/admin/digest` | Inside the digest page | |
| Page, no nav | Reachable by URL only | |

| Option | Description | Selected |
|--------|-------------|----------|
| «Пайплайн» | Nav label | ✓ |
| «Конфиг пайплайна» | Nav label | |

**User's choice:** 5.1a / 5.2a — new page `/admin/pipeline` + nav «Пайплайн».
**Notes:** `/admin/digest` send flow stays untouched.

---

## Claude's Discretion

- Exact key names/defaults within the fixed schema (D-02).
- Precise `/admin/` route path and nav label treatment.
- YAML parser choice and port method names (storage stays behind the port; validation server-side).
- Reject plumbing details (HTTP status, error mapping) consistent with admin route conventions.

## Deferred Ideas

- `score_factors` weights / population — PIPE-EXEC-02, v1.3+.
- Config history / diff / rollback UI — v1.3+.
- Structured field builder — later.
- Client-side YAML pre-parse — not MVP.
- Any execution/run/scheduler control — PIPE-EXEC-01, v1.3.
