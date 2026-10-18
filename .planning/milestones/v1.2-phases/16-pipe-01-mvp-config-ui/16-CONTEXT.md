# Phase 16: PIPE-01 MVP config UI - Context

**Gathered:** 2026-10-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 16 delivers the PIPE-01 MVP admin surface: an admin can **view, edit, validate,
and persist** the pipeline config as YAML **without any pipeline execution**. The
surface is a new admin page (`/admin/pipeline`) backed by a `PUT`/`GET` config
endpoint whose validation is server-authoritative and whose storage sits behind a
port (`PipelineConfigRepository`) wired in `composition/`. The SPA talks only through
`web/src/services/pipelineConfigApi.js` — no Supabase/SQL/storage coupling in
components (PIPE-03).

In scope:
- **View/edit** (PIPE-01): raw YAML `<textarea>` editor; load the saved config on
  mount; edit marks the document dirty.
- **Validate-before-save** (PIPE-02): server parses + schema-validates the YAML;
  invalid config is rejected **before persist** with structured errors
  `{path, line?, message}`; the UI renders every error and keeps the document dirty.
  No silent accept, no client-only pass.
- **Persist + reload** (PIPE-03): a valid save persists behind a port and is readable
  on the next admin session; the UI consumes one DTO `{ yaml, updated_at }`.
- A new admin route + nav item, reusing the locked Phase 5/13/14 admin chrome and the
  approved `16-UI-SPEC.md` design contract.

Out of scope (other phases / not this phase):
- **Any execution UI** — no run / trigger / scheduler / «Запустить» control
  (PIPE-EXEC-* → v1.3). Hard boundary.
- `score_factors` weights in the config and any score population writer
  (PIPE-EXEC-02 → v1.3+); ADUX-06 stays on its honest-empty path.
- Config history / version list / diff / rollback UI.
- Structured field builder (non-raw-YAML representation).
- Full pipeline execution, live SMTP, ingestion HTTP/scheduler.

</domain>

<decisions>
## Implementation Decisions

### Config content scope (Area 2)
- **D-01:** The YAML holds **pipeline parameters only** — the ingest pipeline's template
  kind (lecture/podcast), roles/audiences, and generation limits (e.g. `max_chars`,
  language). **No `score_factors` weights** in the MVP config; ADUX-06 remains on the
  honest-empty path. — **Reversibility:** reversible — adding factor weights later is
  additive keys + a schema bump; nothing already-shipped depends on their absence.
- **D-02:** The config uses a **fixed, documented key set** (a validatable schema), not
  free-form YAML and not fixed-required-plus-free-nested. Unknown keys are rejected
  (see D-06). — **Reversibility:** costly — the key set + rejection behavior become the
  persisted contract clients save against; loosening it later is additive, tightening it
  would reject previously-saved documents.
- **D-03:** The **backend is authoritative** for the schema (Pydantic model). The SPA
  does **not** carry a parallel schema; it renders server-returned errors only. —
  **Reversibility:** reversible — a shared schema could be introduced later, but two
  schema sources would today risk drift (UI-SPEC forbids a client-only "looks fine" pass).

### Validation depth (Area 3 — PIPE-02)
- **D-04:** Validation depth is **syntax + schema** (YAML well-formedness plus
  keys/types/required against the fixed model). No semantic range/interdependency
  validation in MVP. — **Reversibility:** reversible — semantic checks are additive
  rules layered on the same reject envelope.
- **D-05:** The error payload is **`{ errors: [{ path, line?, message }] }`** — matches
  the approved UI-SPEC error contract; `line` is omitted when the parser cannot supply
  it. Server `message` text is rendered **verbatim**. — **Reversibility:** reversible —
  additive fields are tolerated by the existing consumer.
- **D-06:** **Unknown keys are rejected** (strict, `extra="forbid"`), consistent with the
  admin DTO convention from Phases 12–14 (D-09 `extra=forbid`). No ignore, no warn-and-accept.
  — **Reversibility:** costly — strict rejection becomes the save contract; relaxing it
  later is safe, but clients built against rejection expect it.
- **D-07:** **No client-side pre-check** — the server is the only validator on save
  (no client YAML parse that could "pass" locally while the server rejects). —
  **Reversibility:** reversible — a client parse could be added later as a hint, but the
  server must always remain authoritative (UI-SPEC interaction rule 3).

### Storage & versioning (Area 4 — PIPE-03)
- **D-08:** Storage is a **single global row** in a new table (`pipeline_config`:
  singleton holding `yaml` text + `updated_at`). Not version rows, not a JSONB blob. —
  **Reversibility:** costly — the singleton shape is the storage contract; introducing
  versioning later means a schema migration and a read-path change.
- **D-09:** **No history in MVP** — one current version only. The UI-SPEC ships no
  diff/rollback surface, so nothing else is needed. — **Reversibility:** reversible —
  history can be added later without changing the current-version read.
- **D-10:** **Admin-only** access — read **and** write require `profiles.role=admin`;
  the backend persists via the service-role adapter (composition wiring), never the SPA.
  — **Reversibility:** costly — relaxing read to any authenticated user later is a policy
  change across route + RLS, not a local edit.
- **D-11:** The read DTO is **`{ yaml, updated_at }`**; an absent config returns the
  empty state (UI-SPEC empty-state copy). No version number in the DTO. — **Reversibility:**
  reversible — additive fields are safe for existing consumers.

### Placement (Area 5 — A-2)
- **D-12:** New page **`/admin/pipeline`** (`AdminPipelineConfigPage.jsx`, per UI-SPEC
  assumption A-2) plus one `Админ`-gated nav item in `AppShell.jsx`. `/admin/digest`
  stays untouched (its send flow is isolated from config). — **Reversibility:** reversible
  — route + nav entry are local chrome.

### Representation (Area 1 — A-1, not re-discussed)
- **D-13:** Representation stays **raw YAML in a monospace `<textarea>`** per the approved
  UI-SPEC (A-1). The YAML document is the source of truth; no structured field builder in
  MVP. Locked by the UI-SPEC decision; not re-opened in this discussion.

### Claude's Discretion
- Exact pipeline-config key names and defaults within the fixed schema (D-02), provided
  the document round-trips and validates.
- Precise route path under `/admin/` (UI-SPEC proposes `/admin/pipeline`) and the nav
  label treatment as long as PIPE-01…03 hold.
- Which YAML parser/adapter to use, and the port method names, provided the storage stays
  behind `PipelineConfigRepository` and validation stays server-side.
- Exact reject plumbing (HTTP status, FastAPI error mapping) consistent with the existing
  admin route conventions.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §Phase 16 — goal, success criteria 1–4 (view/edit, validate-before-save, persist+readable, no execution).
- `.planning/REQUIREMENTS.md` — PIPE-01 (view/edit YAML config), PIPE-02 (validate before save, structured errors), PIPE-03 (persist behind a port; no deep Supabase coupling in UI); PIPE-EXEC-01/02 (deferred v1.3+).
- `.planning/phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` — approved UI design contract: raw-YAML editor, toolbar, validation-error panel, error payload `{path,line,message}`, copy strings, forbidden no-execution controls, `pipelineConfigApi.js` boundary (PIPE-03).

### Prior-phase locks & context
- `.planning/phases/14-draft-ready-justification-honesty/14-CONTEXT.md` — D-11/D-12: config UI + `score_factors` writers were deferred here; D-13 silent-fake ban; D-15 exact empty copy.
- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` — admin DTO `extra="forbid"` convention carried into D-06.
- `.planning/phases/13-admin-material-email-preview-honesty/13-CONTEXT.md` — admin preview honesty patterns; `AdminDigestPage` chrome reused by the new page.
- `.planning/PROJECT.md` — v1.2 focus; PIPE-01 MVP = config + validation + UI; execution deferred.
- `.planning/STATE.md` — current position Phase 16; accumulated decisions.

### Architecture & process
- `.cursor/rules/architecture.mdc` — Ports & Adapters; storage behind a port; wiring only in `composition/`; FE via `web/src/services/`; no Supabase in components.
- `.cursor/rules/tdd.mdc` + `AGENTS.md` — no production code without a failing test first.
- `.planning/codebase/ARCHITECTURE.md` — layers, adapter modules, composition roots, anti-patterns.
- `.planning/codebase/CONVENTIONS.md` — naming (`_repository.py`, `{verb}_{noun}.py`, `*Api.js`), Pydantic `extra="forbid"`, error-class conventions, `__all__` surfaces.

### Code under change (candidate surfaces)
- `backend/src/backend/interface/http/routes/admin.py` — admin route family; add the pipeline-config read/write routes here (thin: HTTP ↔ use-case).
- `backend/src/backend/application/ports/` — add `PipelineConfigRepository` Protocol.
- `backend/src/backend/application/use_cases/` — new `get_pipeline_config` / `save_pipeline_config` use-cases (parse + schema-validate + persist).
- `backend/src/backend/composition/container.py` / `live.py` — wire the in-memory + Supabase adapters.
- `backend/src/backend/domain/` — new domain model/errors for the config (schema validation errors mapped at the boundary).
- `supabase-integration/migrations/` — new `011_phase16_pipeline_config.sql` (singleton table; next after `010`); `supabase-integration/src/supabase_integration/` adapter.
- `web/src/pages/AdminPipelineConfigPage.jsx` (new), `web/src/services/pipelineConfigApi.js` (new), `web/src/components/AppShell.jsx` (nav item), `web/src/App.jsx` (route).
- `tests/unit/test_http_admin.py` + new `tests/unit/test_pipeline_config*.py`; `tests/admin.spec.js` (Playwright).

### External libs (research/planning must decide — not currently in deps)
- No YAML library is present in the backend workspace or `web/package.json` today. Research must pick the backend parser (server-authoritative validation) and confirm whether the SPA needs one (D-07 says no client validation, so likely backend-only).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AdminDigestPage.jsx` — the admin eyebrow/H1 pattern, `ErrorPanel`, `ServiceUnavailable`, `ForbiddenPage`, and the admin `<textarea>` chrome the new page mirrors (UI-SPEC).
- `adminApi.js` — the `AdminApiError`-style error shape (`code`/`retryable`), `isMocksEnabled()` cutover, and "never silent mock fallback after live failure" — the template for `pipelineConfigApi.js`.
- `AppShell.jsx` — existing `Админ`-gated nav (`appRole === 'admin'`, `linkClass` pill) to extend with one «Пайплайн» item.
- Admin HTTP conventions — thin routers over `app.state.container`, Pydantic `extra="forbid"` request/response DTOs, per-route domain-error → HTTP mapping.
- In-memory port fakes in `backend/src/backend/tests_support/in_memory.py` — add a `PipelineConfigRepository` fake for unit tests.

### Established Patterns
- Ports & Adapters: new persistence capability → `Protocol` in `application/ports/`, fake in `tests_support/`, live adapter in `supabase-integration/`, wired only in `composition/`.
- Boundaries: domain/use-cases import no `fastapi`/`supabase`/`httpx`; the SPA calls only through `web/src/services/`; adapters map SDK/parse failures into domain errors at the boundary.
- TDD mandatory: RED first for each behavior — including "invalid YAML rejected with structured errors", "unknown key rejected", "valid save round-trips", and "no execution control exists".
- Admin DTO `extra="forbid"` + explicit models + unit tests (Phase 12–14 precedent).

### Integration Points
- `GET /admin/pipeline/config` (admin) → use-case reads the singleton via `PipelineConfigRepository` → DTO `{yaml, updated_at}` (or the empty state).
- `PUT /admin/pipeline/config` (admin) → use-case parses + schema-validates → on success persists + returns the saved DTO; on reject returns `{errors:[{path,line?,message}]}` with no write.
- FE: `AdminPipelineConfigPage` mounts → `fetchPipelineConfig()`; Save → `savePipelineConfig(yaml)`; renders validation errors above the editor; both controls honour the UI-SPEC disabled/`dirty` rules.
- `supabase-integration` adapter implements the port against the new `pipeline_config` singleton row; migration `011` follows `010`.

</code_context>

<specifics>
## Specific Ideas

- Error payload mirrors the approved UI-SPEC verbatim: `{ errors: [ { path, line, message } ] }`; server `message` rendered as-is; `line` omitted when unknown.
- Admin-only for both read and write; the SPA never touches Supabase for this surface (PIPE-03 hard boundary).
- No-execution honesty: the page subhead «Просмотр и правка без запуска пайплайна» and the banned-controls list from the UI-SPEC are contract, not decoration.
- Strict `extra="forbid"` on the config document keys, matching the admin DTO convention.

</specifics>

<deferred>
## Deferred Ideas

- `score_factors` weights in the config / any score population writer — PIPE-EXEC-02, v1.3+ (ADUX-06 stays honest-empty).
- Config history / version list / diff / rollback UI — v1.3+.
- Structured field builder (non-raw-YAML editing) — later.
- Client-side YAML pre-parse as a UX hint — not MVP (server stays authoritative).
- Any run / trigger / scheduler / «Запустить» control — PIPE-EXEC-01, v1.3.
- Live SMTP, ingestion HTTP/scheduler — v1.3+.

</deferred>

---

*Phase: 16-pipe-01-mvp-config-ui*
*Context gathered: 2026-10-04*
