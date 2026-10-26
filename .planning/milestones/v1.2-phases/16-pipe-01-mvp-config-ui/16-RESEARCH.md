<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** The YAML holds **pipeline parameters only** — the ingest pipeline's template kind (lecture/podcast), roles/audiences, and generation limits (e.g. `max_chars`, language). **No `score_factors` weights** in the MVP config; ADUX-06 remains on the honest-empty path. — **Reversibility:** reversible — adding factor weights later is additive keys + a schema bump; nothing already-shipped depends on their absence.
- **D-02:** The config uses a **fixed, documented key set** (a validatable schema), not free-form YAML and not fixed-required-plus-free-nested. Unknown keys are rejected (see D-06). — **Reversibility:** costly — the key set + rejection behavior become the persisted contract clients save against; loosening it later is additive, tightening it would reject previously-saved documents.
- **D-03:** The **backend is authoritative** for the schema (Pydantic model). The SPA does **not** carry a parallel schema; it renders server-returned errors only. — **Reversibility:** reversible — a shared schema could be introduced later, but two schema sources would today risk drift (UI-SPEC forbids a client-only "looks fine" pass).
- **D-04:** Validation depth is **syntax + schema** (YAML well-formedness plus keys/types/required against the fixed model). No semantic range/interdependency validation in MVP. — **Reversibility:** reversible — semantic checks are additive rules layered on the same reject envelope.
- **D-05:** The error payload is **`{ errors: [{ path, line?, message }] }`** — matches the approved UI-SPEC error contract; `line` is omitted when the parser cannot supply it. Server `message` text is rendered **verbatim**. — **Reversibility:** reversible — additive fields are tolerated by the existing consumer.
- **D-06:** **Unknown keys are rejected** (strict, `extra="forbid"`), consistent with the admin DTO convention from Phases 12–14 (D-09 `extra=forbid`). No ignore, no warn-and-accept. — **Reversibility:** costly — strict rejection becomes the save contract; relaxing it later is safe, but clients built against rejection expect it.
- **D-07:** **No client-side pre-check** — the server is the only validator on save (no client YAML parse that could "pass" locally while the server rejects). — **Reversibility:** reversible — a client parse could be added later as a hint, but the server must always remain authoritative (UI-SPEC interaction rule 3).
- **D-08:** Storage is a **single global row** in a new table (`pipeline_config`: singleton holding `yaml` text + `updated_at`). Not version rows, not a JSONB blob. — **Reversibility:** costly — the singleton shape is the storage contract; introducing versioning later means a schema migration and a read-path change.
- **D-09:** **No history in MVP** — one current version only. The UI-SPEC ships no diff/rollback surface, so nothing else is needed. — **Reversibility:** reversible — history can be added later without changing the current-version read.
- **D-10:** **Admin-only** access — read **and** write require `profiles.role=admin`; the backend persists via the service-role adapter (composition wiring), never the SPA. — **Reversibility:** costly — relaxing read to any authenticated user later is a policy change across route + RLS, not a local edit.
- **D-11:** The read DTO is **`{ yaml, updated_at }`**; an absent config returns the empty state (UI-SPEC empty-state copy). No version number in the DTO. — **Reversibility:** reversible — additive fields are safe for existing consumers.
- **D-12:** New page **`/admin/pipeline`** (`AdminPipelineConfigPage.jsx`, per UI-SPEC assumption A-2) plus one `Админ`-gated nav item in `AppShell.jsx`. `/admin/digest` stays untouched (its send flow is isolated from config). — **Reversibility:** reversible — route + nav entry are local chrome.
- **D-13:** Representation stays **raw YAML in a monospace `<textarea>`** per the approved UI-SPEC (A-1). The YAML document is the source of truth; no structured field builder in MVP. Locked by the UI-SPEC decision; not re-opened in this discussion.

### Claude's Discretion
- Exact pipeline-config key names and defaults within the fixed schema (D-02), provided the document round-trips and validates.
- Precise route path under `/admin/` (UI-SPEC proposes `/admin/pipeline`) and the nav label treatment as long as PIPE-01…03 hold.
- Which YAML parser/adapter to use, and the port method names, provided the storage stays behind `PipelineConfigRepository` and validation stays server-side.
- Exact reject plumbing (HTTP status, FastAPI error mapping) consistent with the existing admin route conventions.

### Deferred Ideas (OUT OF SCOPE)
- `score_factors` weights in the config / any score population writer — PIPE-EXEC-02, v1.3+ (ADUX-06 stays honest-empty).
- Config history / version list / diff / rollback UI — v1.3+.
- Structured field builder (non-raw-YAML editing) — later.
- Client-side YAML pre-parse as a UX hint — not MVP (server stays authoritative).
- Any run / trigger / scheduler / «Запустить» control — PIPE-EXEC-01, v1.3.
- Live SMTP, ingestion HTTP/scheduler — v1.3+.
</user_constraints>

# Phase 16: PIPE-01 MVP config UI - Research

**Researched:** 2026-10-04
**Domain:** Python/FastAPI + React/Vite admin surface; YAML parse + strict schema validation + singleton persistence behind a port
**Confidence:** HIGH (codebase conventions + verified library behavior); MEDIUM on the exact config key set (Claude's discretion)

## Summary

Phase 16 adds an admin-only `/admin/pipeline` surface (GET/PUT `/admin/pipeline/config`) that reads, validates, and persists a raw-YAML pipeline config as a single Supabase row, with **no pipeline execution**. All 13 implementation decisions are locked in CONTEXT.md; this research resolves the open implementation unknowns: the YAML parser, the structured-error mapping, the migration + RLS convention, the admin HTTP route shape, the frontend service/route/nav insertion points, and the RED-test list.

The single most important finding is that the approved UI-SPEC error contract `{ "errors": [ { path, line?, message } ] }` is **not** what FastAPI produces by default. `HTTPException(detail={"errors": [...]})` nests the payload under `detail` (verified: `{'detail': {'errors': [...]}}`), and request-DTO validation (`extra="forbid"`) produces `{'detail': [...]}` with a different element shape. To honor D-05 verbatim, the reject path **must return `JSONResponse(status_code=400, content={"errors": [...]})`** (verified: `{'errors': [...]}` top-level).

Two secondary findings materially affect the plan. First, **PyYAML `safe_load` silently accepts duplicate keys, last-wins** (verified: `safe_load("a: 1\na: 2\n") == {'a': 2}`) — for a "no silent accept" contract (PIPE-02) the parser must use a strict `SafeLoader` subclass that rejects duplicates. Second, the CORS allow-list in `app.py` is **`["GET", "POST", "PATCH", "OPTIONS"]` — it does not include `PUT`**; shipping a `PUT` endpoint without adding `PUT` breaks the live browser preflight while all mock-mode Playwright tests still pass. There is also **no existing admin-only RLS policy convention** in the migrations (contrary to the research-scope assumption) — the repo gates admin via backend `require_admin` + a `service_role` client, with RLS-enabled tables carrying no permissive policy.

**Primary recommendation:** Pin **PyYAML 6.0.3** (already resolved in `uv.lock` transitively via `uvicorn[standard]`; add it explicitly to `backend`) with a strict `SafeLoader` subclass, validate the parsed mapping with a Pydantic v2 `extra="forbid"` model (`pydantic 2.13.5` already installed), map both error sources into a frozen `PipelineConfigError(path, line, message)` tuple carried by a `PipelineConfigValidationError` domain error, persist through a new `PipelineConfigRepository` port (Supabase adapter + in-memory fake), and return rejects via `JSONResponse(400, {"errors": [...]})`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| YAML parse + schema validation | API / Backend | — | D-03 server-authoritative; PyYAML/Pydantic must not leak into the SPA (D-07 bans client pre-check) |
| Config persistence (singleton row) | Database / Storage | API / Backend | D-08 storage shape; access mediated by `PipelineConfigRepository` port, live adapter in `supabase-integration` |
| Admin authorization | API / Backend | Database / Storage | Existing convention: `require_admin` reads `profiles.role` via service_role; RLS is deny-by-default, not policy-based (D-10) |
| Config read/write transport | Frontend Server (SPA service) | API / Backend | PIPE-03 hard boundary — the SPA reaches the API only through `web/src/services/pipelineConfigApi.js` |
| Raw-YAML editing surface | Browser / Client | — | D-13/UI-SPEC A-1: controlled `<textarea>`, no structured builder |
| Structured error rendering | Browser / Client | — | UI-SPEC: render server `{errors:[...]}` verbatim; no client schema (D-03) |
| No-execution honesty | Browser / Client | — | UI-SPEC hard boundary: no run/trigger/scheduler control ships |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPE-01 | Admin can view and edit YAML (or equivalent structured) pipeline config through an admin UI | Raw-YAML `<textarea>` page + `GET /admin/pipeline/config`; frontend route/nav insertion points identified (`App.jsx:38`, `AppShell.jsx:86-90`); admin gate reuse (`AdminDigestPage.jsx:137-159`) |
| PIPE-02 | Config is validated before save; invalid config rejected with field-level/structured errors (no silent accept) | PyYAML strict parse (syntax+duplicate keys) + Pydantic `extra="forbid"`; verified `MarkedYAMLError.problem_mark`, `ValidationError.errors()` shape; `JSONResponse(400, {"errors":[...]})` to match D-05 |
| PIPE-03 | Validated config persists and is readable on subsequent sessions (storage behind a port; no deep Supabase coupling in UI) | `PipelineConfigRepository` Protocol + in-memory fake + `SupabasePipelineConfigRepository`; migration `011` singleton table; `pipelineConfigApi.js` as sole SPA transport boundary |
</phase_requirements>

## Project Constraints (from AGENTS.md / .cursor/rules)

`CLAUDE.md` does not exist. The actionable directives come from `AGENTS.md`, `.cursor/rules/tdd.mdc`, and `.cursor/rules/architecture.mdc` (always applied). The planner **must** honor these:

- **TDD mandatory (Red–Green–Refactor).** No production code before a failing test exists. Every behavior below (invalid YAML rejected, unknown key rejected, valid save round-trips, empty state, admin-only, no-execution control absent) ships as a `type: tdd` task with a RED run recorded first.
- **Ports & Adapters.** New persistence → `Protocol` in `backend/.../application/ports/`; fake in `tests_support/`; live adapter in `supabase-integration/`; wiring **only** in `composition/container.py` (memory) and `composition/live.py`.
- **Dependencies point inward.** `domain/` and `use_cases/` must not import `supabase`, `httpx`, `fastapi`, `yaml`, or React. SDK/parse failures are mapped to domain errors **at the adapter boundary**.
- **UI boundary.** The SPA calls the API only through `web/src/services/*Api.js`; components never import Supabase/SQL/storage.
- **Conventions.** Pydantic v2 `ConfigDict(extra="forbid")` at the HTTP boundary; `{verb}_{noun}.py` use-case modules; `{noun}_repository.py` ports; `Supabase{Port}` adapter classes; HTTP maps domain errors **per-route** (no global `DomainError` handler); new DB work → numbered migration.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | `6.0.3` | Parse admin YAML server-side | Canonical Python YAML parser; already in `uv.lock`; `safe_load` + `MarkedYAMLError` give structured line/column. `[VERIFIED: uv.lock:1231-1232]` |
| Pydantic | `2.13.5` | Strict config schema (`extra="forbid"`) + `ValidationError.errors()` | Already installed and already used at the HTTP boundary in `routes/admin.py`. `[VERIFIED: uv.lock:1063-1064]`, `[VERIFIED: uv run python -c import pydantic → 2.13.5]` |
| FastAPI | `0.141.1` | `GET`/`PUT` admin routes | Existing HTTP edge; `JSONResponse` for the D-05 payload. `[VERIFIED: backend/pyproject.toml:8]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `yaml.constructor.ConstructorError` | (PyYAML) | Duplicate-key rejection from the strict loader | Strict `SafeLoader` subclass `construct_mapping` override |
| `fastapi.responses.JSONResponse` | (FastAPI) | Emit top-level `{"errors":[...]}` with status 400 | Reject path only |
| React / `react-router-dom` | `19.2.8` / `7.18.3` | Page, route, nav | Reuse existing shell |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML | `ruamel.yaml` | Rejects duplicate keys by default (`DuplicateKeyError`) and gives better marks, but is **not** in `uv.lock`, adds a heavy dependency, and its round-trip feature (comments/formatting) is unused because the raw YAML text is stored verbatim, not re-emitted. PyYAML + a ~10-line strict loader is the smaller, already-resolved choice. |
| Top-level `{"errors":[...]}` via `JSONResponse` | `HTTPException(detail={"errors":[...]})` | Rejected: produces `{"detail": {...}}`, contradicting the locked UI-SPEC/D-05 contract (verified by probe). |
| PyYAML `safe_load` | `yaml.load(..., Loader=yaml.FullLoader/UnsafeLoader)` | Rejected: unsafe tag resolution / arbitrary object construction. Use `safe_load` semantics (or a subclass of `SafeLoader`). |

**Installation (uv workspace member):**
```bash
uv add --package backend "pyyaml==6.0.3"
# Optional hygiene: declare pydantic explicitly (currently transitive-only, yet already imported)
uv add --package backend "pydantic>=2.13,<3"
```
No frontend dependency is added (D-07: no client-side YAML parse).

**Version verification:**
```bash
uv run python -c "import yaml, pydantic; print(yaml.__version__, pydantic.VERSION)"
# expected: 6.0.3 2.13.5
```

## Package Legitimacy Audit

> Run via `gsd_tools query package-legitimacy check --ecosystem pypi pyyaml ruamel.yaml pydantic`.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `pyyaml` | PyPI | `6.0.3` published 2025-09-25 | unknown (seam) | `https://pyyaml.org/` → `yaml/pyyaml` | `[SUS]` | Flagged — **already in `uv.lock` transitively**; add one `checkpoint:human-verify` before `uv add` |
| `pydantic` | PyPI | `2.13.5` present in lock | unknown (seam) | `github.com/pydantic/pydantic` | `[SUS]` | Flagged — **already installed and imported**; no new risk |
| `ruamel.yaml` | PyPI | 2026-01-02 | unknown (seam) | `sourceforge.net/p/ruamel-yaml` | `[SUS]` | **Not recommended / not installed** — rejected in favor of PyYAML |

**Packages removed due to `[SLOP]` verdict:** none.

**Packages flagged as suspicious `[SUS]`:** `pyyaml`, `pydantic`. Both verdicts are driven solely by the seam's `unknown-downloads` signal — PyPI does not expose a weekly-downloads metric to the legitimacy check (`signals.weeklyDownloads: null`, `reasons: ["unknown-downloads"]`). Neither is a hallucination vector: both are resolved in the checked-in `uv.lock`, and PyYAML is corroborated by Context7 `/yaml/pyyaml` (Source Reputation: High) and Pydantic by Context7 `/pydantic/pydantic` (High). Per protocol the planner should still insert a lightweight `checkpoint:human-verify` before the `uv add` — it is a formality here, not a real risk gate.

## Architecture Patterns

### System Architecture Diagram

```
Admin browser (React SPA)
  AdminPipelineConfigPage.jsx
        │  fetchPipelineConfig() / savePipelineConfig(yaml)
        ▼
  web/src/services/pipelineConfigApi.js     ← ONLY transport boundary (PIPE-03)
        │  GET  /admin/pipeline/config
        │  PUT  /admin/pipeline/config  { yaml }
        ▼
  FastAPI router  routes/admin.py  (thin)
        │  Depends(require_admin)  → profiles.role == "admin"   (D-10)
        ▼
  use-case  save_pipeline_config / get_pipeline_config
        ├── PipelineConfigValidator port ──► infrastructure/yaml_pipeline_config_validator.py
        │        ├─ PyYAML StrictSafeLoader (syntax + duplicate keys)  → MarkedYAMLError
        │        └─ Pydantic extra="forbid" schema                     → ValidationError
        │                 │  both mapped to PipelineConfigError(path, line?, message)
        │                 └─ invalid ⇒ raise PipelineConfigValidationError(errors)
        │                        │
        │                        └─► 400 JSONResponse {"errors":[{path,line?,message}]}   ← D-05, no write
        └── PipelineConfigRepository port ──► SupabasePipelineConfigRepository (service_role)
                 migration 011: singleton row pipeline_config(id=1, yaml, updated_at)
                 valid ⇒ upsert ⇒ 200 { yaml, updated_at }

  No path below the SPA reaches Supabase directly. No execution path exists at all.
```

### Recommended Project Structure (new/changed files)

```
backend/src/backend/
├── domain/
│   ├── pipeline_config.py            # PipelineConfig, PipelineConfigError dataclasses
│   └── errors.py                     # += PipelineConfigValidationError
├── application/
│   ├── ports/
│   │   ├── pipeline_config_repository.py   # get() / save() Protocol
│   │   └── pipeline_config_validator.py    # validate(yaml_text) -> None Protocol
│   └── use_cases/
│       ├── get_pipeline_config.py          # repo.get()
│       └── save_pipeline_config.py         # validate() then repo.save()
├── infrastructure/
│   └── yaml_pipeline_config_validator.py   # PyYAML StrictSafeLoader + Pydantic model + mapping
├── composition/
│   ├── container.py                  # += pipeline_config, pipeline_config_validator (memory fakes)
│   └── live.py                       # += SupabasePipelineConfigRepository(admin_client)
├── interface/http/routes/admin.py    # += GET/PUT /admin/pipeline/config
└── tests_support/in_memory.py        # += InMemoryPipelineConfigRepository, InMemoryPipelineConfigValidator

supabase-integration/
├── migrations/011_phase16_pipeline_config.sql   # singleton table + RLS enabled (no policy)
└── src/supabase_integration/pipeline_config_repository.py   # SupabasePipelineConfigRepository
    (re-exported from __init__.py)

web/src/
├── pages/AdminPipelineConfigPage.jsx        # new page (UI-SPEC)
├── services/pipelineConfigApi.js            # new sole transport boundary
├── components/AppShell.jsx                  # += «Пайплайн» admin nav item
└── App.jsx                                  # += admin/pipeline route

tests/
├── unit/test_pipeline_config_validator.py   # PyYAML + Pydantic RED behaviors
├── unit/test_http_pipeline_config.py        # route + fake repo + admin gate
├── unit/test_phase16_migration_011.py       # migration contract (mirrors test_phase5_migration_005.py)
└── admin.spec.js                            # += Playwright pipeline-config cases
```

### Pattern 1: Strict YAML parse → structured error tuple
**What:** Parse with a `SafeLoader` subclass that rejects duplicate keys, catch `MarkedYAMLError` and turn it into one `PipelineConfigError`.
**When to use:** Every save. `[VERIFIED: probe — problem_mark is 0-based; duplicate keys silently last-wins under `safe_load`]`
```python
# infrastructure/yaml_pipeline_config_validator.py
import yaml
from yaml.constructor import ConstructorError

class _StrictSafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _value in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError:
                continue
            if key in seen:
                raise ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    f"found duplicate key ({key!r})", key_node.start_mark,
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)

# mark.line / mark.column are 0-based → +1 for the 1-based UI row
try:
    data = yaml.load(yaml_text, Loader=_StrictSafeLoader)
except yaml.MarkedYAMLError as exc:
    mark = exc.problem_mark
    raise PipelineConfigValidationError((
        PipelineConfigError(path="", line=(mark.line + 1) if mark else None, message=str(exc.problem or exc)),
    ))
```
Source: Context7 `/yaml/pyyaml` (error-types: `MarkedYAMLError.context/problem/problem_mark`); behavior confirmed by local probe against PyYAML 6.0.3.

### Pattern 2: Pydantic `extra="forbid"` schema → dotted-path errors
**What:** Validate the parsed mapping against a frozen key set; map each `ValidationError` entry to `path = dotted loc`, no `line` (YAML scalars carry no line info once parsed).
**When to use:** After a successful strict parse. `[VERIFIED: probe — `extra_forbidden`, nested `loc=('source','bogus')`]`
```python
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing import Literal

class PipelineConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")          # D-06
    template: Literal["lecture", "podcast"]            # D-01 / TemplateKind values
    roles: list[str] = Field(min_length=1)             # D-01 (audience roles)
    language: str = Field(min_length=1)
    max_chars: int = Field(gt=0)

def _loc_to_dot_sep(loc: tuple[str | int, ...]) -> str:
    path = ""
    for i, x in enumerate(loc):
        if isinstance(x, str):
            path += ("." if i > 0 else "") + x
        else:
            path += f"[{x}]"
    return path

try:
    PipelineConfigModel.model_validate(data)
except ValidationError as exc:
    raise PipelineConfigValidationError(tuple(
        PipelineConfigError(path=_loc_to_dot_sep(e["loc"]), line=None, message=e["msg"])
        for e in exc.errors()
    ))
```
Source: Context7 `/pydantic/pydantic` (errors: `errors()` dict fields `type/loc/msg/input/url`; `loc_to_dot_sep` example). Model keys are **Claude's discretion** (D-02) — see Assumptions Log A2.

### Pattern 3: Storage port (mirrors `ShortlistRepository`)
**What:** `Protocol` with `get() -> PipelineConfig | None` and `save(*, yaml, updated_at) -> PipelineConfig`; fake in `tests_support`, live adapter in `supabase-integration`, wired only in composition.
**When to use:** Always — D-08/D-10.
```python
# application/ports/pipeline_config_repository.py
from typing import Protocol
from datetime import datetime
from backend.domain.pipeline_config import PipelineConfig

class PipelineConfigRepository(Protocol):
    def get(self) -> PipelineConfig | None: ...
    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig: ...
```
Source: `backend/src/backend/application/ports/shortlist_repository.py:10-41` (existing convention).

### Pattern 4: Thin admin route + admin gate + top-level error payload
**What:** Route resolves the repo/validator from `app.state.container`, returns `JSONResponse(400, {"errors": [...]})` on `PipelineConfigValidationError`, 503 on missing config, 401/403 via `require_admin`.
**When to use:** Both GET and PUT.
```python
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

@router.put("/pipeline/config")
def put_pipeline_config(body: PipelineConfigSaveRequest, request: Request,
                        _admin: CurrentUser = Depends(require_admin)):
    repo = _require_pipeline_config(request)     # 503 pipeline_config_not_configured
    try:
        cfg = save_pipeline_config(repo, request.app.state.pipeline_config_validator,
                                   yaml_text=body.yaml)
    except PipelineConfigValidationError as exc:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"errors": [e.to_dict() for e in exc.errors]})
    return PipelineConfigResponse(yaml=cfg.yaml, updated_at=cfg.updated_at)
```
Source: `backend/src/backend/interface/http/routes/admin.py:167-195` (guard pattern) and `:436-491` (per-route domain→HTTP mapping). **Verified**: `HTTPException(detail=...)` nests under `detail`; `JSONResponse` does not.

### Anti-Patterns to Avoid
- **`yaml.safe_load` alone:** silently accepts duplicate keys (last-wins) → violates "no silent accept" (PIPE-02).
- **`yaml.load` / `FullLoader` / `UnsafeLoader`:** arbitrary tag/object construction.
- **Importing `yaml` in `use_cases/` or `domain/`:** violates inward dependency direction; keep it in the `infrastructure/` adapter behind the validator port.
- **Returning `HTTPException(detail={"errors": ...})`:** breaks the locked D-05 payload shape (nested under `detail`).
- **Client-side YAML parse / schema:** banned by D-03/D-07.
- **Any run/trigger/scheduler control:** banned by CONTEXT + UI-SPEC (PIPE-EXEC-01 → v1.3).
- **Inventing an `admin` RLS policy:** there is no such precedent; RLS is deny-by-default and admin is enforced in the backend.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Regex/line scanner | PyYAML `safe_load` + strict `SafeLoader` subclass | Anchors, block/flow scalars, quoting, multi-line, encodings |
| Duplicate-key detection | Post-parse `dict` inspection | `construct_mapping` override raising `ConstructorError` | The `dict` has already dropped the duplicate by then |
| Schema/required/type checks | Manual `if key not in data` | Pydantic `extra="forbid"` model | Nested `loc`, chained/union errors, consistent messages |
| Error `loc` rendering | Ad-hoc string joins | `loc_to_dot_sep` (Context7 example) | Numeric list indices → `items[1].value` |
| Timestamps | Manual ISO slicing | `datetime` + adapter `_iso`/`_parse_dt` | Existing adapters already centralize this |

**Key insight:** The parser and the schema are the two places where "no silent accept" lives; both already exist as hardened libraries. Re-implementing either is exactly where a field-format bug lands at the executor's typecheck/parse step.

## Common Pitfalls

### Pitfall 1: `PUT` blocked by CORS preflight (live browser only)
**What goes wrong:** The browser sends an `OPTIONS` preflight for `PUT /admin/pipeline/config`; `CORSMiddleware` advertises `Access-Control-Allow-Methods: GET, POST, PATCH, OPTIONS`, so the live cross-origin call fails while all mock Playwright tests pass.
**Why it happens:** `allow_methods=["GET", "POST", "PATCH", "OPTIONS"]` in `app.py` predates any `PUT` route. `[VERIFIED: backend/src/backend/interface/http/app.py:48]`
**How to avoid:** Add `"PUT"` to `allow_methods`, and extend `tests/unit/test_cors.py` with a `PUT` preflight assertion. (Alternative: use `POST` to match existing convention — but CONTEXT/UI-SPEC say `PUT`.)
**Warning signs:** Live FE↔BE proof fails with a CORS error on save; mock-mode green.

### Pitfall 2: Reject payload nests under `detail`
**What goes wrong:** `HTTPException(status_code=400, detail={"errors":[...]})` yields `{'detail': {'errors':[...]}}`; the SPA's `body.errors` is `undefined` and the validation panel falls back to the generic string.
**Why it happens:** FastAPI wraps `detail`. `[VERIFIED: local TestClient probe]`
**How to avoid:** Return `JSONResponse(status_code=400, content={"errors":[...]})`; unit-test the top-level key.
**Warning signs:** Playwright sees «Конфиг не прошёл проверку» instead of per-field rows.

### Pitfall 3: Duplicate keys silently accepted
**What goes wrong:** `template: podcast` then `template: lecture` parses to `lecture` with no error.
**Why it happens:** `SafeLoader.construct_mapping` overwrites duplicate keys. `[VERIFIED: probe → {'a': 2}]`
**How to avoid:** Strict loader subclass (Pattern 1); add a RED test asserting a duplicate-key reject.
**Warning signs:** A "last value wins" survives save.

### Pitfall 4: Non-string top-level keys
**What goes wrong:** `1: x` / `true: y` parse to `{1: ..., True: ...}`; Pydantic mapping against string fields produces confusing `extra_forbidden`/coercion errors rather than a clean schema message.
**Why it happens:** YAML 1.1 scalar resolution. `[VERIFIED: probe → {1: True}]`
**How to avoid:** Before validation, assert `isinstance(data, dict)` and all keys are `str`; raise a structured `{path:"", message}` error otherwise.
**Warning signs:** Error `path` prints `1` or `True`.

### Pitfall 5: Empty / multi-document streams
**What goes wrong:** `safe_load("")` returns `None`; `safe_load("a: 1\n---\nb: 2\n")` raises `ComposerError: expected a single document in the stream`. `[VERIFIED: probe]`
**Why it happens:** `safe_load` reads exactly one document; empty input is `None`.
**How to avoid:** Treat `None` as "empty document" (reject on save unless the schema has all-optional fields), and catch `ComposerError` as a structured syntax error with a line.
**Warning signs:** `AttributeError: 'NoneType'` in the validator.

### Pitfall 6: `AppContainer` constructor breakage
**What goes wrong:** Adding required fields to the `AppContainer` dataclass breaks the direct constructor in `tests/unit/test_http_knowledge_search.py:100-113`. `[VERIFIED: file read]`
**How to avoid:** Give the new fields defaults (`pipeline_config=None`, `pipeline_config_validator=None`) and keep the `_require_pipeline_config` 503 guard; or update the test. Existing routes already tolerate missing attributes via `getattr(container, "...", None)`.
**Warning signs:** `TypeError: missing required keyword argument` in an unrelated knowledge test.

### Pitfall 7: Assuming an admin RLS policy exists
**What goes wrong:** Writing `create policy ... using (exists (select 1 from profiles where role='admin'))` invents a convention and may grant `authenticated` more than intended.
**Why it happens:** The research brief assumed such a policy exists; it does not.
**How to avoid:** Match the repo: `alter table public.pipeline_config enable row level security;` with **no** permissive policy. `service_role` (composition's `create_service_role_client`) bypasses RLS. `[VERIFIED: 001_initial_schema.sql:241-258 enables RLS; lines 260-296 define only ready/own select policies, no admin policy]`, `[CITED: backend/src/backend/composition/live.py:35-38 "service_role: RLS bypass ..."]`
**Warning signs:** A migration reviewer flags a novel admin policy; anon can read the config.

### Pitfall 8: `extra="forbid"` request DTO vs config errors
**What goes wrong:** A malformed request body (extra JSON field) yields FastAPI 422 `{'detail':[{'type':'extra_forbidden','loc':['body','bogus'],...}]}` — a different shape from the config reject payload. `[VERIFIED: probe]`
**How to avoid:** In `pipelineConfigApi.js`, treat 422 as a non-retryable `PIPELINE_CONFIG_FAILED` with generic copy; only 400 carries `body.errors`.
**Warning signs:** The UI tries to read `.errors` off a 422 and renders nothing.

### Pitfall 9: Leaking `score_factors` or an execution control
**What goes wrong:** A reviewer adds "helpful" weight keys or a «Запустить» button.
**Why it happens:** Phase 16 is adjacent to the deferred execution phase.
**How to avoid:** Schema has no `score_factors`; Playwright asserts none of the banned strings render.
**Warning signs:** Any of «Запустить», «Выполнить», «Запуск», «Планировщик», «Расписание» as a control.

## Code Examples

### Strict validator: parse + schema in one place
```python
# Source: Context7 /yaml/pyyaml (MarkedYAMLError) + /pydantic/pydantic (errors()),
#         behavior confirmed by local probe against PyYAML 6.0.3 / pydantic 2.13.5.
def validate(self, yaml_text: str) -> None:
    try:
        data = yaml.load(yaml_text, Loader=_StrictSafeLoader)
    except yaml.MarkedYAMLError as exc:
        mark = exc.problem_mark
        raise PipelineConfigValidationError((
            PipelineConfigError(
                path="",
                line=(mark.line + 1) if mark is not None else None,
                message=str(exc.problem or exc),
            ),
        ))
    if not isinstance(data, dict) or not all(isinstance(k, str) for k in data):
        raise PipelineConfigValidationError((
            PipelineConfigError(path="", line=None, message="Ожидается объект с текстовыми ключами"),
        ))
    try:
        PipelineConfigModel.model_validate(data)
    except ValidationError as exc:
        raise PipelineConfigValidationError(tuple(
            PipelineConfigError(path=_loc_to_dot_sep(e["loc"]), line=None, message=e["msg"])
            for e in exc.errors()
        ))
```

### Domain error carrying structured entries
```python
# mirrors DraftInSendPoolError(draft_material_ids=...) in domain/errors.py:145-150
@dataclass(frozen=True)
class PipelineConfigError:
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict:
        out = {"path": self.path, "message": self.message}
        if self.line is not None:
            out["line"] = self.line
        return out

class PipelineConfigValidationError(DomainError):
    def __init__(self, errors: tuple[PipelineConfigError, ...]) -> None:
        super().__init__("pipeline config validation failed")
        self.errors = errors
```

### Migration `011` (mirrors 001/005/010 conventions)
```sql
-- Phase 16: PIPE-01 MVP pipeline config singleton (PIPE-01..03, D-08).
-- Idempotent: create-if-not-exists; single row enforced by PK + CHECK. No wipe, no reset.
-- Shared VM: apply once via Studio SQL / psql / supabase db push.
create table if not exists public.pipeline_config (
  id integer primary key default 1 check (id = 1),
  yaml text not null default '',
  updated_at timestamptz not null default now()
);

-- Deny-by-default: RLS enabled, NO permissive policy. Only service_role (backend
-- composition adapter) reaches this table; admin gating is backend require_admin (D-10).
alter table public.pipeline_config enable row level security;

-- Verify after apply:
-- select count(*) from public.pipeline_config;  -- expect 0 or 1
```

### Supabase adapter (mirrors `SupabaseProfileRepository` error mapping)
```python
class SupabasePipelineConfigRepository:
    def __init__(self, client) -> None:
        self._client = client

    def get(self) -> PipelineConfig | None:
        try:
            result = (self._client.table("pipeline_config")
                      .select("yaml,updated_at").eq("id", 1).execute())
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"pipeline_config get failed: {exc}") from exc
        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        return PipelineConfig(yaml=str(rows[0].get("yaml") or ""),
                              updated_at=_parse_dt(rows[0].get("updated_at")))

    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig:
        try:
            result = (self._client.table("pipeline_config")
                      .upsert({"id": 1, "yaml": yaml, "updated_at": _iso(updated_at)})
                      .execute())
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"pipeline_config save failed: {exc}") from exc
        return PipelineConfig(yaml=yaml, updated_at=updated_at)
```
Source: `supabase-integration/src/supabase_integration/profile_repository.py:33-80`, `shortlist_repository.py:76-98`.

### Frontend service boundary (`pipelineConfigApi.js`)
```js
// Mirrors adminApi.js AdminApiError shape + isMocksEnabled cutover.
export class PipelineConfigError extends Error {
  constructor(message, { code = 'PIPELINE_CONFIG_FAILED', retryable = true, errors = null } = {}) {
    super(message); this.name = 'PipelineConfigError'
    this.code = code; this.retryable = retryable; this.errors = errors
  }
}
export async function fetchPipelineConfig(accessToken) { /* GET; empty → { yaml: '', updated_at: null } */ }
export async function savePipelineConfig(yaml, accessToken) {
  // 400 → read body.errors → throw PipelineConfigError('Конфиг не прошёл проверку',
  //          { code:'INVALID_CONFIG', retryable:false, errors })
  // 422 → generic non-retryable; 5xx/network → retryable
}
```
Source: `web/src/services/adminApi.js:23-31` (error class), `:59` (`useMocks`), `:281-301` (fetch+map).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pydantic` v1 `.dict()` errors | v2 `ValidationError.errors()` list of dicts with `loc`/`type`/`msg`/`input`/`url` | Pydantic v2 | Map `loc` tuples; don't rely on v1 `.error_dict()` |
| `yaml.load(..., Loader=yaml.Loader)` | `yaml.safe_load` / `SafeLoader` subclass | Since 5.1 | No arbitrary object construction |
| Parse-time "looks fine" UI validation | Server-authoritative validate-before-save | Phase 16 (D-03/D-07) | One schema source |

**Deprecated/outdated:**
- PyYAML is in maintenance mode but stable at 6.0.3; no migration pressure for this scope.
- `ruamel.yaml` round-trip is unnecessary because the raw text is persisted verbatim and never re-dumped.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The config key set is `template` / `roles` / `language` / `max_chars` (D-02 says fixed documented set; names are Claude's discretion) | Standard Stack (Pattern 2), Code Examples | Low — renaming keys is additive before ship; the schema must round-trip and validate (D-02) |
| A2 | `updated_at` in the DTO is an ISO-8601 string (DB `timestamptz`); empty GET returns `{ yaml: "", updated_at: null }` | Summary, Code Examples | Low — UI-SPEC typedef allows `updated_at: string | null`; `yaml: string` |
| A3 | Reject HTTP status is **400** (matching `invalid_decision` / `empty_send_pool` precedent) rather than 422 | Pattern 4, Pitfall 8 | Medium — UI must switch on the status; recommend locking 400 in the plan |
| A4 | Duplicate-key rejection is in-scope strictness (not explicitly in CONTEXT) | Pattern 1, Pitfall 3 | Low — extends "no silent accept"; if excluded, remove Pattern 1's override and the RED test |
| A5 | Malformed request-body 422 may surface as `{detail:[...]}`; the SPA maps it to generic copy | Pitfall 8 | Low — request DTO is `{yaml: string}` only |

**If this table were empty:** No — A1–A5 needed confirmation at research time; A1 and A3 are now resolved in `## Open Questions (RESOLVED)` above (16-02 locks the 4-key set and the 400 reject).

## Open Questions (RESOLVED)

1. **Exact config key names and defaults (A1)**
   - What we know: D-01 enumerates template kind, roles/audiences, generation limits; D-02 requires fixed keys; template/role closed sets exist elsewhere (`TemplateKind` = lecture|podcast; `VALID_ROLES` = employee|analyst|ds, but `backend` does **not** depend on `data-collection`). `[VERIFIED: data-collection/src/data_collection/dto/template_kind.py:6-8]`, `[VERIFIED: data-collection/src/data_collection/dto/role_kind.py:7-8]`, `[VERIFIED: backend/pyproject.toml:6-12 — no data-collection dep]`
   - What's unclear: whether `roles` uses the material audience set (`employee|analyst|ds`) and whether more limit keys are wanted.
   - Recommendation: lock the 4-key set in the plan; define the role Literal **in backend** (cannot import `data-collection`).
   - **RESOLVED:** 16-02 locks the schema to the 4-key set `{template, roles, language, max_chars}` with `template: Literal["lecture","podcast"]`, `roles: list[Literal["employee","analyst","ds"]]` (`min_length=1`), `language: str` (`min_length=1`), `max_chars: int` (`gt=0`), defined locally in backend (no `data-collection` import), and asserts `PipelineConfigModel.model_fields` equals exactly those four keys.

2. **HTTP status for a rejected save (A3)**
   - What we know: admin routes use 400 for `invalid_*`, 422 is FastAPI's body-shape default.
   - What's unclear: 400 vs 422 for semantic config rejection.
   - Recommendation: 400 with `JSONResponse({"errors":[...]})`; document in the route docstring.
   - **RESOLVED:** reject status is locked to **400** returned as a top-level `JSONResponse(status_code=400, content={"errors":[...]})` (never `HTTPException(detail=...)`, which nests under `detail`); implemented in 16-02's `put_pipeline_config` reject branch.

3. **Live migration apply path**
   - What we know: migrations 005–010 were applied by the operator via Supabase Studio SQL (some via MCP PostgREST); `raw_sql`/`transaction` need an extra `POSTGRES_URL`. `[CITED: docs/agents/local-platform-runbook.md §4c, §4g]`
   - Recommendation: author `011`, add a runbook section, plan an `apply-after-sql` checkpoint like 010 — no destructive reset.
   - **RESOLVED:** 16-03 authors `011_phase16_pipeline_config.sql`, adds runbook **§4h** with the apply + verify SQL (count 0/1, RLS enabled, zero policies, dated Applied line), and gates the live DoD behind the `[BLOCKING]` apply checkpoint — no destructive reset.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (uv env) | Backend + tests | ✓ | 3.12.13 | — |
| `uv` | Dependency management / `uv add` | ✓ | 0.10.9 | — |
| Node / npm | Vite + Playwright | ✓ | 22.13.0 / 11.18.0 | — |
| PyYAML | YAML parse | ✓ (transitive) | 6.0.3 | Add explicit direct dep |
| Pydantic | Schema | ✓ | 2.13.5 | — |
| pytest | Unit tests | ✓ (`uv run pytest`) | `>=8.3.0` | — |
| Playwright | UI E2E | ✓ | `^1.62.1` | Mock mode `VITE_USE_MOCKS=true` |
| Supabase live + `POSTGRES_URL` | Live migration apply | ✗ by default | — | Operator applies `011` via Studio SQL |

**Missing dependencies with no fallback:** none for local unit/Playwright development.
**Missing dependencies with fallback:** live Supabase migration apply falls back to the operator Studio SQL path (established pattern for 005–010).

## Validation Architecture

> `workflow.nyquist_validation` is absent in `.planning/config.json` → treated as **enabled**.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `>=8.3.0` (Python) + Playwright `^1.62.1` (UI) |
| Config file | root `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths=["tests/unit"]`) + `playwright.config.js` (web project, port 5174, `VITE_USE_MOCKS=true`) |
| Quick run command | `uv run pytest tests/unit/test_pipeline_config_validator.py -x` |
| Full suite command | `uv run pytest` then `npx playwright test tests/admin.spec.js --project=web --reporter=line` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | GET returns saved config DTO `{yaml, updated_at}` | unit (route + fake repo) | `uv run pytest tests/unit/test_http_pipeline_config.py -k get_returns -x` | ❌ Wave 0 |
| PIPE-01 | Page renders editor + loads saved YAML; Save disabled while clean | e2e (Playwright) | `npx playwright test tests/admin.spec.js --project=web -g "pipeline config"` | ❌ Wave 0 |
| PIPE-02 | Invalid YAML (syntax) rejected with `{errors:[{path,line,message}]}`, no write | unit (validator) | `uv run pytest tests/unit/test_pipeline_config_validator.py -k syntax -x` | ❌ Wave 0 |
| PIPE-02 | Unknown key rejected (`extra_forbidden`), no write | unit (validator + route) | `uv run pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -k unknown -x` | ❌ Wave 0 |
| PIPE-02 | Duplicate key rejected | unit (validator) | `uv run pytest tests/unit/test_pipeline_config_validator.py -k duplicate -x` | ❌ Wave 0 |
| PIPE-02 | Reject payload is top-level `{"errors":[...]}` (not nested `detail`) | unit (route) | `uv run pytest tests/unit/test_http_pipeline_config.py -k nested -x` | ❌ Wave 0 |
| PIPE-02 | UI renders every error row + fallback copy | e2e (Playwright) | `npx playwright test tests/admin.spec.js --project=web -g "validation"` | ❌ Wave 0 |
| PIPE-03 | Valid save round-trips (GET after PUT returns saved text) | unit (route + fake repo) | `uv run pytest tests/unit/test_http_pipeline_config.py -k round_trip -x` | ❌ Wave 0 |
| PIPE-03 | Empty state: no row → 200 empty DTO / UI empty block | unit + e2e | `uv run pytest tests/unit/test_http_pipeline_config.py -k empty -x` | ❌ Wave 0 |
| PIPE-03 | Non-admin GET/PUT → 403; unauthenticated → 401 | unit (route) | `uv run pytest tests/unit/test_http_pipeline_config.py -k admin -x` | ❌ Wave 0 |
| PIPE-03 | SPA reaches config only via `pipelineConfigApi.js` (no Supabase import in page) | unit (Node/static assert) or AST/text guard | `uv run pytest tests/unit/test_http_pipeline_config.py -k no_supabase` | ❌ Wave 0 |
| PIPE-EXEC guard | No run/trigger/scheduler control renders | e2e (Playwright) | `npx playwright test tests/admin.spec.js --project=web -g "no execution"` | ❌ Wave 0 |
| — | Migration `011` contract (singleton + RLS + no policy) | unit (migration contract) | `uv run pytest tests/unit/test_phase16_migration_011.py -x` | ❌ Wave 0 |
| — | CORS advertises `PUT` | unit (CORS) | `uv run pytest tests/unit/test_cors.py -k put -x` | ⚠️ extend existing |
| — | Live container wires `SupabasePipelineConfigRepository` | unit (wiring) | `uv run pytest tests/unit/test_live_container_wiring.py -k pipeline -x` | ⚠️ extend existing |

### Sampling Rate
- **Per task commit:** the task's own focused `pytest`/Playwright command (RED first, then GREEN).
- **Per wave merge:** `uv run pytest`.
- **Phase gate:** full `uv run pytest` green **plus** `npx playwright test tests/admin.spec.js --project=web` green before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/unit/test_pipeline_config_validator.py` — PyYAML syntax/duplicate/non-string/empty + Pydantic extra/type/required, covering PIPE-02.
- [ ] `tests/unit/test_http_pipeline_config.py` — GET/PUT route, auth gate, top-level error payload, round-trip, empty, 503 guard, PIPE-03 boundary guard.
- [ ] `tests/unit/test_phase16_migration_011.py` — mirrors `test_phase5_migration_005.py` (singleton, `enable row level security`, no `create policy`, no wipe).
- [ ] `backend/src/backend/tests_support/in_memory.py` — add `InMemoryPipelineConfigRepository` (+ validator fake).
- [ ] `tests/admin.spec.js` — extend with pipeline-config describe block + harness reset in `gotoAsRole`.
- [ ] Extend `tests/unit/test_cors.py` (PUT preflight) and `tests/unit/test_live_container_wiring.py` (new adapter).

## Security Domain

> `security_enforcement` absent in config → enabled.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Reuse Supabase JWT verify via `deps.get_principal` (no new auth) |
| V3 Session Management | no | Unchanged; Supabase-managed |
| V4 Access Control | yes | `require_admin` (`profiles.role='admin'`) on **both** GET and PUT; RLS deny-by-default on `pipeline_config` |
| V5 Input Validation | yes | PyYAML `safe_load` semantics + strict `SafeLoader`; Pydantic `extra="forbid"`; input size cap |
| V6 Cryptography | no | No new crypto |

### Known Threat Patterns for FastAPI + PyYAML + Supabase
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection through config | Tampering | No raw SQL — PostgREST/SDK parameterized; adapter only |
| Stored XSS via YAML/message rendered in UI | Tampering | React escapes text; error `message` is server-generated; **never** `dangerouslySetInnerHTML` for config/errors (UI-SPEC bans FE HTML assembly) |
| YAML alias/"billion laughs" resource exhaustion | Denial of Service | `safe_load` blocks arbitrary tags, but cap request body size / YAML length and reject oversized docs before parse `[ASSUMED — verify alias behavior if hardening]` |
| Unauthorized config read/write | Elevation of Privilege | `require_admin` + RLS enabled with no permissive policy + service_role only in composition |
| Arbitrary object construction via unsafe YAML | Tampering / RCE | `SafeLoader` subclass only; never `yaml.load` default loader or `UnsafeLoader` |
| Secrets shown in UI | Information Disclosure | Config holds pipeline parameters only (D-01); if a sensitive value is ever added, the backend redacts it in the DTO (UI-SPEC out-of-scope rule) |

## Sources

### Primary (HIGH confidence)
- Context7 `/yaml/pyyaml` — `safe_load`, `MarkedYAMLError.context/problem/problem_mark` (line/column 0-based), error handlers.
- Context7 `/pydantic/pydantic` — `ValidationError.errors()` fields (`type/loc/msg/input/url`), `loc_to_dot_sep` example, `extra="forbid"`.
- Context7 `/pycontribs/ruamel-yaml` — `DuplicateKeyError` default behavior (used to evaluate the alternative).
- Local probe against PyYAML 6.0.3 / Pydantic 2.13.5 — duplicate-key last-wins, `problem_mark` indices, multi-doc `ComposerError`, non-string keys, empty→`None`, `extra_forbidden` loc, and FastAPI 400/422 body shapes.

### Secondary (MEDIUM confidence)
- `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONVENTIONS.md` — layers, naming, error handling.
- `supabase-integration/migrations/001…010`, `docs/agents/local-platform-runbook.md` — migration/RLS/service_role conventions.

### Tertiary (LOW confidence)
- None material. `[ASSUMED]` items are listed in the Assumptions Log.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PyYAML/Pydantic versions verified in `uv.lock` and env; APIs verified via Context7 + local probe.
- Architecture: HIGH — mirrors existing ports/composition/routes/adapters verbatim; verified against current source.
- Pitfalls: HIGH — CORS `PUT` gap, nested `detail`, and duplicate-key behavior all verified in-repo/by probe.
- Config key set: MEDIUM — Claude's discretion (A1).

**Research date:** 2026-10-04
**Valid until:** ~2026-11-03 (30 days; stable libraries, slow-moving repo conventions).
