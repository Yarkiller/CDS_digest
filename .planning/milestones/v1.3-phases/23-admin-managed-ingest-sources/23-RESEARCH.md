# Phase 23: Admin-managed ingest sources - Research

**Researched:** 2026-10-17
**Domain:** Admin CRUD for YouTube ingest subscriptions (Postgres/RLS + FastAPI ports/adapters + React admin SPA + unsaved-changes guard)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Every row action is **immediate** — add, enable/disable, and delete each issue their own request and the UI reflects the server's response. There is **no** «Сохранить источники» button and no buffered list diff. Rationale: the list is short (single-digit rows) and a second Save control on a page whose other half already has one is a UX trap. — **Reversibility:** costly — switching to a buffered model later requires a draft-state container, a dirty contract, and a new test surface for atomic list saves.
- **D-02:** The sources section renders **above** the YAML editor on `/admin/pipeline`, with its own heading «Источники ингеста». YAML remains below, unchanged. — **Reversibility:** reversible.
- **D-03:** The Phase 19 guard is reused **verbatim** — `useUnsavedChangesGuard` + `UnsavedChangesDialog` + `armBeforeUnload`, same copy «Есть несохранённые изменения. Уйти без сохранения?». The page keeps **one** dirty signal: `dirty = yamlDirty || sourceFormDirty`. One modal on the page; no second dialog and no per-surface copy. — **Reversibility:** costly — a second guard instance would double-prompt and force a precedence rule across two blockers.
- **D-04:** `sourceFormDirty = sourceId.trim() !== '' || label.trim() !== ''`. Changing the kind selector alone is **not** dirty (it carries a default; nothing typed is lost). — **Reversibility:** reversible.
- **D-05:** No optimistic updates. A row's control is disabled while its request is in flight; on failure the row shows an inline error and keeps the last known server state (a toggle that failed stays where it was). — **Reversibility:** reversible.
- **D-06:** The type is an **explicit selector** «Канал | Плейлист» next to the id field. The server rejects a kind/prefix mismatch (`kind=channel` with a `PL…` id and vice versa) through the same structured 400 — the client is never the authority. — **Reversibility:** reversible.
- **D-07:** An **optional** `label` («Название») is captured on the add form. Trimmed; empty → `null`; max 120 chars (a longer value is a 400 with `path: "label"`). Rationale: no automatic titles exist without the rejected Data API. — **Reversibility:** reversible.
- **D-08:** A row shows: `source_id` in mono, the kind, the status («включён»/«выключен»), an enable/disable control, «Удалить», and an external link «Открыть на YouTube» (`/channel/{id}` for a channel, `/playlist?list={id}` for a playlist, `target="_blank"` + `rel="noopener noreferrer"`). The link lets the admin verify the id before enabling it, at zero cost and with no API. — **Reversibility:** reversible.
- **D-09:** `label` is set **only at creation**; inline label editing is not shipped here (see Deferred Ideas). This keeps the surface at exactly three row actions plus one add form. — **Reversibility:** reversible.
- **D-10:** `is_enabled` is a boolean column; **delete is hard** (`DELETE` removes the row). No soft delete, no archive, no restore. This matches the roadmap's "enable/disable, and remove". — **Reversibility:** one-way — a hard delete destroys the row, so a later restore feature cannot recover data deleted under this contract without a new column and a backfill.
- **D-11:** Zero enabled sources is **allowed**, but the section states it honestly: «Нет включённых источников — новые видео собираться не будут». The copy deliberately avoids «Запуск», «Выполнить», «Планировщик», «Расписание» because the shipped Playwright tripwire bans those words on this page (see D-20). — **Reversibility:** reversible.
- **D-12:** Two distinct empty states: (a) **no rows at all** — «Пока нет источников» plus the add form and the id help; (b) **rows exist, none enabled** — the D-11 hint above the list. Neither state hides the add form. — **Reversibility:** reversible.
- **D-13:** The «где взять id» instruction (`SRC-02`) lives **inline next to the form**: one short line under the id field plus a collapsible «Где взять id?» disclosure containing both recipes — channel: YouTube Studio → «Настройки» → «Канал» → «Расширенные настройки» → «Идентификатор канала» (`UC…`); playlist: open the playlist and copy `list=` from the address bar (`PL…`). — **Reversibility:** reversible.
- **D-14:** Canonical id is strict: channel `^UC[A-Za-z0-9_-]{22}$` (24 chars total), playlist `^PL[A-Za-z0-9_-]{32}$` (34 chars total). Anything else — including a bare 11-char video id, a URL, or `@handle` — is a 400 with the top-level `{errors:[{path:"source_id", message:"…"}]}` envelope and **zero writes**. — **Reversibility:** reversible.
- **D-15:** A duplicate `(kind, source_id)` is a 400 with the **same** envelope and `path: "source_id"` (message «Этот источник уже добавлен»), so this surface keeps exactly one reject shape. The use case pre-checks the list so a unique-constraint violation can never surface as a `PersistenceError` 503; the DB unique index remains the backstop. — **Reversibility:** reversible.
- **D-16:** The new table is **`public.pipeline_ingest_sources`** in migration **`012_phase23_ingest_sources.sql`**. Do **not** reuse or alter `ingestion_sources` from `001_initial_schema.sql`: that existing table models *fetched content items* (`external_id`, `canonical_url`, `title`, `published_at`, `view_count`, `status`) and is the FK target of `materials.source_id`, `ingestion_jobs` and `source_texts`. Reusing it would conflate an admin subscription with a fetched item and break those relations. — **Reversibility:** one-way — renaming a shipped table means a migration plus updating the adapter, the service, and every test that names it.
- **D-17:** Migration shape mirrors `011`: `create table if not exists` (idempotent), `bigint generated always as identity` PK, `kind text not null check (kind in ('channel','playlist'))`, `source_id text not null`, `label text`, `is_enabled boolean not null default true`, `created_at`/`updated_at timestamptz not null default now()`, `unique (kind, source_id)`, **RLS enabled with zero policies** (deny-by-default; only the `service_role` client from `composition/live.py` reaches it), and no `truncate`/`delete from`. — **Reversibility:** one-way — the RLS/policy stance and the unique constraint are data-model commitments.
- **D-18:** REST surface under the existing admin router, all `require_admin`: `GET /admin/ingest-sources` → `{sources:[…]}`; `POST /admin/ingest-sources` → created row (201); `PATCH /admin/ingest-sources/{id}` with `{is_enabled}` → updated row; `DELETE /admin/ingest-sources/{id}` → 204. Unknown JSON fields stay `extra="forbid"` → 422, as on the pipeline config. Router module split is Claude's discretion (existing home: `interface/http/routes/admin.py`). — **Reversibility:** costly — the SPA service module and the Playwright mock both encode these paths.
- **D-19:** The reject row reuses the shipped `{path, message}` shape with **no** `line` key. Whether the helper is extracted from `PipelineConfigError.to_dict()` or duplicated is Claude's discretion; a second envelope shape is not. — **Reversibility:** reversible.
- **D-20:** RED split follows the Phase 18/Pitfall-24 precedent: **server-side validation, the 400 envelope and zero writes are pytest HTTP/contract tests** (`VITE_USE_MOCKS=true` cannot reproduce a real reject), while Playwright covers the admin journey (add → row appears → disable → delete, plus the dirty-guard prompts). Playwright is integration proof, not the RED for server behaviour. — **Reversibility:** reversible.
- **D-21:** Composition gains `ingest_sources: IngestSourceRepository | None = None` on `AppContainer` (defaulted so a bare container still constructs), wired in `composition/container.py` (in-memory fake) and `composition/live.py` (`SupabaseIngestSourceRepository` on the existing service-role client). A missing repo keeps the established `pipeline_config_not_configured` 503 style, with its own detail code. — **Reversibility:** reversible.
- **D-22:** `tests/admin.spec.js` → **`"pipeline config no execution controls render"`** (≈ line 1804) → **PRESERVE byte-identical.** It bans «Запустить», «Выполнить», «Запуск», «Планировщик», «Расписание» in the page text and as buttons. Every new string in the sources section must stay clear of those words — this is why D-11's copy is phrased the way it is. Do not "fix" the test.
- **D-23:** `tests/admin.spec.js` dirty-gating and admin-section-tab tests, `tests/unit/test_http_pipeline_config.py`, `tests/unit/test_phase16_migration_011.py`, `tests/unit/test_schema_migration_contract.py` → **PRESERVE** (no edit to the pipeline-config contract, no edit to migrations 001/011).
- **D-24:** `tests/unit/test_composition_container.py`, `tests/unit/test_live_container_wiring.py`, and any exact-`__all__` assertion on `supabase_integration` → **AMEND** (a new port and a new adapter export are additive wiring changes, not regressions).

### Claude's Discretion
- **D-14…D-21** (validation regexes, duplicate handling, table/migration name, REST shape, reject-row helper extraction, RED split, composition field) were set in discuss-phase as discretion locks — treat them as decided for planning; do not reopen alternatives.
- Router module split (keep routes in `admin.py` vs new module) — recommend **keep in `admin.py`** next to pipeline-config routes to reuse `_require_*` / `require_admin` patterns; split only if the planner judges file size a maintenance risk.
- Whether to extract a shared `{path, message}` helper from `PipelineConfigError.to_dict()` or duplicate a one-liner on a new error type — recommend **reuse `PipelineConfigError` rows** (or a tiny shared dataclass with identical `to_dict`) so the HTTP mapper stays one shape (D-19).
- Whether the SPA section is inline in `AdminPipelineConfigPage.jsx` or a child component — recommend a **child section component** owned by the page, with dirty/list state lifted to the page so the single `dirty` OR stays obvious.

### Deferred Ideas (OUT OF SCOPE)
- **One-off ingest of a single video from the admin UI** (paste a video URL/id, run it once, without adding a source to the list). Raised during this discussion. It is a new capability, not an editor detail: it needs an HTTP trigger surface, and `ING-01` ("Ingestion HTTP API") is explicitly out of scope for v1.3, while Phase 24 is specified as scheduler → existing `ingest` CLI only. Candidate for `/gsd-review-backlog` as its own future phase (admin-triggered single-video ingest, drafts only).
- **Inline label editing** for a saved source (D-09 keeps label creation-only). Natural follow-up if admins start with placeholder names.
- **Soft delete / restore** of a source (D-10 ships hard delete). Revisit only if an accidental deletion actually happens in use.
- **Automatic source titles / channel metadata** — needs the YouTube Data API v3, which is rejected in REQUIREMENTS (contra ADR-0002); would require its own ADR decision.
- **Per-source statistics** (last ingested, video count, last error) — belongs with the scheduler's run history in Phase 24 or later, not with the source list.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SRC-01 | An admin can list, add, enable/disable, and remove ingest sources (YouTube channel or playlist) on the pipeline page, and the list is stored in the database | Migration `012` + `pipeline_ingest_sources`; REST CRUD under `/admin/ingest-sources`; SPA section above YAML via `ingestSourcesApi.js` |
| SRC-02 | The source API validates the canonical source id server-side and rejects anything else with a top-level structured 400 `{errors:[…]}` and zero writes; the UI states where to obtain the id | Domain/use-case regex + kind match (D-14/D-06); `JSONResponse` 400 envelope copied from pipeline config; inline id-help disclosure (D-13) |
| SRC-03 | Sources are read/written through an `IngestSourceRepository` port wired in composition; the SPA reaches them only through a service module (no deep Supabase coupling) | Port in `application/ports/`; Supabase adapter in `supabase-integration/`; wiring only in `container.py` / `live.py`; SPA only via `web/src/services/ingestSourcesApi.js` |
| ADUX-10 | The guard covers every editable surface on `/admin/pipeline`, including the ingest-sources editor shipped in the sources phase | Widen page dirty to `yamlDirty \|\| sourceFormDirty` (D-03/D-04); reuse Phase 19 guard trio unchanged; Playwright dirty prompts for typed add-form fields |
</phase_requirements>

## Summary

Phase 23 is a **ports-and-adapters CRUD slice** that stores admin-managed YouTube channel/playlist *subscriptions* separately from the existing `ingestion_sources` *fetched-item* table. The locked design copies the Phase 16 pipeline-config stack almost verbatim: idempotent migration with deny-by-default RLS, Protocol port + in-memory fake + Supabase adapter wired only in composition, thin `require_admin` FastAPI routes, and a mock/live SPA service module. Server-side canonical-id validation (`UC…` / `PL…` + kind match) returns the same top-level `{errors:[{path, message}]}` 400 envelope already used by `PUT /admin/pipeline/config`, with zero repository writes on reject.

The UI is an immediate-persist list (no second Save button) placed above the YAML editor on `/admin/pipeline`. Dirty-guard ownership for ADUX-10 is a one-line OR into the existing Phase 19 blocker — not a second modal. Playwright proves the journey and guard; pytest owns the validation/400/zero-write RED.

**Primary recommendation:** Mirror the pipeline-config vertical slice end-to-end (`011` → `012`, port/fake/adapter/composition, HTTP mapper, `pipelineConfigApi.js` → `ingestSourcesApi.js`), keep validation in the use case before any write, and widen only the page-level `dirty` expression for ADUX-10.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Canonical id + kind validation | API / Backend (use case / domain) | — | Server is authority (D-06/D-14); client UX only |
| Persist / list / enable / delete | Database / Storage | API / Backend adapter | Table + unique index; adapter maps SDK → `PersistenceError` |
| Admin authz (`require_admin`) | API / Backend | — | Same gate as all `/admin/*` routes |
| Deny-by-default RLS | Database / Storage | — | No policies; only service_role from composition |
| SPA list + add form + row actions | Browser / Client | API via service module | Immediate per-row requests (D-01); no Supabase in UI |
| Unsaved-changes guard (ADUX-10) | Browser / Client | — | Existing guard trio; dirty OR on page |
| Id-help teaching copy | Browser / Client | — | SRC-02 UI obligation; no network |

## Project Constraints (from AGENTS.md / architecture / TDD)

- **TDD:** `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST` (AGENTS.md, `.cursor/rules/tdd.mdc`). RED split per D-20: pytest for server rejects; Playwright for journey/guard.
- **Ports & Adapters:** Domain/use cases import no `supabase`/`httpx`/`fastapi`; adapters in `supabase-integration/`; wiring only in `composition/` (`.cursor/rules/architecture.mdc`).
- **SPA boundary:** Admin data only through `web/src/services/*`; no deep Supabase coupling (SRC-03, architecture rule).
- **ADR-0002:** Canonical ids only — no YouTube Data API, no `@handle`/URL resolution, no scraping in this phase.
- **Git origin via WSL:** operational constraint for push/pull; not required for planning this phase.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.141.1 (installed) | Admin HTTP surface + `JSONResponse` 400 | Already owns `/admin/*` [VERIFIED: `uv pip show`] |
| Pydantic | 2.13.5 (installed) | Request/response DTOs with `extra="forbid"` | Existing admin DTO pattern [VERIFIED: `uv pip show`] |
| pytest | ≥8.3.0 (pyproject) | HTTP/contract/migration RED | Project unit harness [VERIFIED: `pyproject.toml:28`] |
| React | ^19.2.8 (`web/`) | Admin page section | Existing SPA [VERIFIED: `web/package.json`] |
| @playwright/test | ^1.62.1 (root) | Admin journey + dirty guard | Existing `tests/admin.spec.js` [VERIFIED: `package.json:18`] |
| Supabase Python client (existing) | project-pinned | `SupabaseIngestSourceRepository` | Same client as `SupabasePipelineConfigRepository` — **no new package** |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI `TestClient` + ES256 JWT harness | in-repo | HTTP contract tests | Copy from `tests/unit/test_http_pipeline_config.py` |
| sessionStorage mock store | browser | Playwright offline mocks | Copy `pipelineConfigApi.js` arm/reset pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New table `pipeline_ingest_sources` | Reuse `ingestion_sources` | **Forbidden by D-16** — wrong domain (fetched items + FKs) |
| YouTube Data API title lookup | Manual optional `label` | Rejected by REQUIREMENTS / ADR-0002 |
| Buffered list + Save | Immediate per-row | Rejected by D-01 |

**Installation:** None — **no new npm/PyPI packages** for this phase.

**Version verification:** FastAPI `0.141.1`, Pydantic `2.13.5` via `uv pip show` (2026-10-17). Playwright `@playwright/test` `^1.62.1` in root `package.json`.

## Package Legitimacy Audit

> No external packages are installed in this phase.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | N/A — reuse existing stack |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
Admin browser (/admin/pipeline)
  │
  ├─ Ingest sources section (above YAML)
  │     │  list / add / toggle / delete (immediate)
  │     ▼
  │  web/src/services/ingestSourcesApi.js  (mock | live)
  │     │  Authorization: Bearer <access_token>
  │     ▼
  │  FastAPI admin router  require_admin
  │     GET|POST|PATCH|DELETE /admin/ingest-sources[/{id}]
  │     │  validate (regex + kind + label + duplicate)
  │     │  on reject → JSONResponse 400 {"errors":[{path,message}]}  (zero writes)
  │     ▼
  │  use_cases (list/add/set_enabled/delete)
  │     ▼
  │  IngestSourceRepository  (Protocol)
  │     ├─ InMemory… (container.py / tests)
  │     └─ SupabaseIngestSourceRepository (live.py → service_role client)
  │           ▼
  │        public.pipeline_ingest_sources  (RLS on, 0 policies)
  │
  └─ YAML editor (unchanged) ──► pipelineConfigApi / PipelineConfigRepository
        dirty = yamlDirty || sourceFormDirty ──► useUnsavedChangesGuard + one dialog
```

### Recommended Project Structure
```text
supabase-integration/migrations/
  012_phase23_ingest_sources.sql          # new table + RLS
supabase-integration/src/supabase_integration/
  ingest_source_repository.py             # Supabase adapter
  __init__.py                             # export + __all__ AMEND
backend/src/backend/
  domain/ingest_source.py                 # entity + optional validation error rows
  application/ports/ingest_sources.py     # IngestSourceRepository Protocol
  application/use_cases/ingest_sources.py # validate-then-persist
  tests_support/in_memory.py              # InMemoryIngestSourceRepository (+ writes log)
  composition/container.py | live.py      # wire field ingest_sources
  interface/http/routes/admin.py          # routes + DTOs (recommended home)
web/src/
  services/ingestSourcesApi.js            # mock + live + harness
  pages/AdminPipelineConfigPage.jsx       # section above YAML; dirty OR
  components/IngestSourcesSection.jsx     # optional child (discretion)
tests/unit/
  test_phase23_migration_012.py
  test_http_ingest_sources.py
  test_supabase_ingest_source_repository_contract.py
tests/admin.spec.js                       # journey + dirty (AMEND carefully; D-22 PRESERVE)
```

### Pattern 1: Validate-then-persist use case (zero writes)
**What:** Validate in the use case; call repository only after accept. Mirror `save_pipeline_config`.
**When to use:** POST add and any field that can 400.
**Example:**
```python
# Pattern from backend/src/backend/application/use_cases/pipeline_config.py:25-34
# [VERIFIED: backend/src/backend/application/use_cases/pipeline_config.py:25-34]
def save_pipeline_config(repo, validator, *, yaml_text, now=None):
    validator.validate(yaml_text)  # raises before any write
    return repo.save(yaml=yaml_text, updated_at=now or datetime.now(timezone.utc))
```

### Pattern 2: Top-level `{errors:[…]}` 400 via JSONResponse
**What:** Return `JSONResponse(status_code=400, content={"errors": [...]})` — never nest under `detail`.
**When to use:** Canonical-id / kind / label / duplicate rejects (D-19).
**Example:**
```python
# [VERIFIED: backend/src/backend/interface/http/routes/admin.py:643-648]
# Source: in-repo + FastAPI JSONResponse docs (Context7 /websites/fastapi_tiangolo)
return JSONResponse(
    status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": [error.to_dict() for error in exc.errors]},
)
```

### Pattern 3: Deny-by-default RLS migration
**What:** `create table if not exists` + `enable row level security` + **no** `create policy`.
**When to use:** Migration `012` (D-17), mirror `011`.
**Example:**
```sql
-- [VERIFIED: supabase-integration/migrations/011_phase16_pipeline_config.sql:6-15]
create table if not exists public.pipeline_config (
  id integer primary key default 1 check (id = 1),
  yaml text not null default '',
  updated_at timestamptz not null default now()
);
alter table public.pipeline_config enable row level security;
```

### Pattern 4: Single dirty OR for ADUX-10
**What:** One `useUnsavedChangesGuard(dirty)` call; `dirty = yamlDirty || sourceFormDirty`.
**When to use:** `AdminPipelineConfigPage` only change to the guard stack.
**Example:**
```javascript
// Current [VERIFIED: web/src/pages/AdminPipelineConfigPage.jsx:106-107]
const dirty = yaml !== savedYaml
const blocker = useUnsavedChangesGuard(dirty)
// Target (D-03/D-04):
// const yamlDirty = yaml !== savedYaml
// const sourceFormDirty = sourceId.trim() !== '' || label.trim() !== ''
// const dirty = yamlDirty || sourceFormDirty
```

### Anti-Patterns to Avoid
- **Reuse `ingestion_sources`:** Wrong domain; FK target for materials/jobs/texts (D-16). [VERIFIED: `001_initial_schema.sql:48-86`]
- **Nest validation errors under `detail`:** Breaks SPA error rendering contract (pipeline Pitfall 2).
- **Optimistic toggle:** Forbidden by D-05 — keep last server state on failure.
- **Second unsaved dialog / second blocker:** Forbidden by D-03.
- **Banned copy** («Запустить», «Выполнить», «Запуск», «Планировщик», «Расписание»): D-22 tripwire PRESERVE.
- **Playwright as RED for 400/zero-writes:** Mocks cannot prove server reject (D-20).
- **SDK imports in use cases / deep Supabase in SPA:** Architecture / SRC-03.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured 400 envelope | New error JSON shape | `PipelineConfigError.to_dict()` shape `{path, message}` | UI-SPEC + existing SPA parsers expect it |
| Admin JWT test harness | New mint helpers | Copy `test_http_pipeline_config.py` ES256 helpers | Proven; D-23 PRESERVE that file |
| Mock SPA transport | Ad-hoc fetch in page | `pipelineConfigApi.js` mock/live + arm/reset | Playwright project uses `VITE_USE_MOCKS=true` |
| RLS “open for authenticated” | Permissive policies | RLS on + zero policies + service_role | Same as `pipeline_config` (T-16-10) |
| YouTube id “smart” parsing | URL/`@handle` resolvers | Strict regex only (D-14) | ADR-0002 / REQUIREMENTS out-of-scope |

**Key insight:** This phase is almost entirely **pattern reuse** from Phase 16/19/22 — inventing new envelopes, tables, or guard instances is the failure mode.

## Runtime State Inventory

> New-table migration (not a rename). Explicit answers:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Existing `public.ingestion_sources` holds **fetched content items**, not admin subscriptions [VERIFIED: `001_initial_schema.sql:48-62`]. New empty `pipeline_ingest_sources` after apply. | Author `012` only; **do not** ALTER/TRUNCATE `ingestion_sources`. No data backfill. |
| Live service config | Shared self-hosted Supabase/Postgres on VM (ADR-0004); migration apply via Studio SQL / `psql` / `supabase db push` (same ops note as `011`). | Ops apply `012` once on shared VM before live proof; not required for unit RED. |
| OS-registered state | None for this feature — Phase 24 owns systemd timer. | None |
| Secrets/env vars | Reuses existing service-role Supabase credentials in live composition; no new secret names. | None |
| Build artifacts | None specific; adapter export changes may require reinstall only if packaging caches `__all__` oddly (unlikely). | None expected |

**Nothing found in category:** OS-registered state — None (verified: Phase 24 owns timers; this phase is CRUD-only). Secrets — no new keys (verified via composition pattern for pipeline_config).

## Common Pitfalls

### Pitfall 1: Confusing `ingestion_sources` with subscriptions
**What goes wrong:** Adapter/tests write to the wrong table; materials FK semantics break.
**Why it happens:** Similar English name.
**How to avoid:** Table name `pipeline_ingest_sources` only (D-16); migration contract test asserts that string; never edit `001`.
**Warning signs:** FK errors, Playwright/mock talking to wrong resource name.

### Pitfall 2: Nesting 400 errors under `detail`
**What goes wrong:** SPA shows opaque error; contract tests fail.
**How to avoid:** Copy `JSONResponse` mapper from `put_pipeline_config` [VERIFIED: `admin.py:643-648`].
**Warning signs:** Response body `{"detail": ...}` on validation reject.

### Pitfall 3: Double unsaved-changes prompts
**What goes wrong:** Two blockers or two dialogs when typing in the add form *and* editing YAML.
**How to avoid:** Single `dirty` OR; single `useUnsavedChangesGuard` call (D-03).
**Warning signs:** Two modals; Playwright sees double confirm.

### Pitfall 4: Banned execution-control copy
**What goes wrong:** D-22 tripwire fails after adding section strings.
**How to avoid:** Use D-11 wording; grep section copy against the banned list before commit.
**Warning signs:** Failures in `"pipeline config no execution controls render"`.

### Pitfall 5: Treating unique-constraint as 503
**What goes wrong:** Duplicate add surfaces `PersistenceError` → 503 instead of teaching 400.
**How to avoid:** Use-case pre-check (D-15); keep unique index as backstop only.
**Warning signs:** 503 on duplicate; `save`/`insert` count > 0 after reject.

### Pitfall 6: Playwright-only RED for validation
**What goes wrong:** Mocks accept invalid ids; production rejects differently.
**How to avoid:** pytest HTTP tests own regex/kind/label/duplicate/zero-writes (D-20).
**Warning signs:** No `test_http_ingest_sources.py` asserting `save_count == 0`.

### Pitfall 7: Kind selector alone marks dirty
**What goes wrong:** Switching «Канал|Плейлист» prompts leave without typed text (violates D-04).
**How to avoid:** Dirty from trimmed `sourceId`/`label` only.
**Warning signs:** Guard fires after only changing the select.

### Pitfall 8: Old 18-char `PL…` playlists rejected
**What goes wrong:** Rare legacy playlists fail D-14's 34-char regex.
**Why it happens:** Archive Team documents both `PL[0-9A-F]{16}` and modern `PL[A-Za-z0-9_-]{32}` [CITED: wiki.archiveteam.org YouTube/Technical_details].
**How to avoid:** Accept as intentional (D-14); document in UI help that modern `list=` ids are required. Do not widen regex without a discuss-phase reopen.
**Warning signs:** Admin cannot add an old Favorites/`FL`/18-char playlist — expected.

## Code Examples

### Reject row shape (no `line`)
```python
# [VERIFIED: backend/src/backend/domain/pipeline_config.py:24-42]
@dataclass(frozen=True)
class PipelineConfigError:
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"path": self.path, "message": self.message}
        if self.line is not None:
            payload["line"] = self.line
        return payload
# Ingest rejects always omit line → {"path": "source_id", "message": "…"}
```

### Port style to copy
```python
# [VERIFIED: backend/src/backend/application/ports/pipeline_config.py:17-24]
class PipelineConfigRepository(Protocol):
    def get(self) -> PipelineConfig | None: ...
    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig: ...
# New: list / add / set_enabled / delete methods; no SDK types.
```

### Migration PK / unique style (from fetched-items table — shape only)
```sql
-- [VERIFIED: supabase-integration/migrations/001_initial_schema.sql:48-62]
create table if not exists ingestion_sources (
  id bigint generated always as identity primary key,
  ...
  unique (source_system, external_id)
);
-- 012 uses the same identity PK style + unique (kind, source_id) on pipeline_ingest_sources
```

### Canonical id regex (locked)
```python
# D-14 — locked; community validators agree on UC 24-char form [CITED: docs.tubearchivist.com/urls/]
CHANNEL_ID_RE = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
PLAYLIST_ID_RE = re.compile(r"^PL[A-Za-z0-9_-]{32}$")
# kind=channel ⇒ CHANNEL only; kind=playlist ⇒ PLAYLIST only
```

### Guard copy (unchanged)
```javascript
# [VERIFIED: web/src/utils/unsavedChangesGuard.js:7-8]
export const UNSAVED_LEAVE_CONFIRM =
  'Есть несохранённые изменения. Уйти без сохранения?'
```

### Suggested DTO skeleton (planner/executor)
```python
# Aligns with D-18; values appear in CONTEXT decisions (not yet in codebase)
class IngestSourceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["channel", "playlist"]
    source_id: str
    label: str | None = None

class IngestSourcePatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_enabled: bool
```

### YouTube open links (D-08)
```text
channel  → https://www.youtube.com/channel/{source_id}
playlist → https://www.youtube.com/playlist?list={source_id}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| YouTube Data API v3 listing | Public Atom/RSS `feeds/videos.xml?channel_id=\|playlist_id=` | v1.3 research / Phase 24 lock | Phase 23 only stores canonical ids; no API client |
| Soft/buffered admin lists | Immediate per-row persist | Phase 23 D-01 | Simpler dirty model (add-form only) |
| Nested FastAPI `detail` errors | Top-level `{errors:[…]}` | Phase 16 PIPE-02 | Must copy envelope, not invent |

**Deprecated/outdated:**
- Data API / `google-api-python-client` / `yt-dlp` for this milestone — rejected.
- Reusing `ingestion_sources` as a subscription registry — incorrect domain model.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Older 18-char `PL…` playlists are intentionally out of D-14 scope and need no regex widen in this phase | Pitfalls / Open Questions | Rare admin cannot add legacy playlist; would need discuss reopen |
| A2 | Detail codes `ingest_sources_not_configured` / `ingest_sources_unavailable` are the preferred strings for 503 (mirroring pipeline_config) | Architecture / D-21 — RESOLVED in Open Questions | Naming pinned in 23-01 HTTP tests |
| A3 | Keeping routes in `admin.py` is preferable to a new router module | Discretion | File size / merge conflict risk only |

**If this table is empty:** N/A — three low-risk assumptions remain for planner naming/discretion.

## Open Questions (RESOLVED)

1. **503 detail code spelling** — RESOLVED
   - What we know: D-21 requires own detail codes in the `pipeline_config_*` style.
   - Resolution: Pin `ingest_sources_not_configured` (missing repo → 503) and `ingest_sources_unavailable` (PersistenceError → 503). Planned in `23-01-PLAN.md` tracer behavior/action and HTTP harness.
   - Not chosen: `ingest_source_repository_not_configured` (rejected for plural `ingest_sources_*` mirror of pipeline_config).

2. **Shared error type vs reuse `PipelineConfigError`** — RESOLVED
   - What we know: D-19 allows extract or duplicate; shape must match.
   - Resolution: `IngestSourceValidationError` in `backend/src/backend/domain/errors.py` carrying `tuple[PipelineConfigError, ...]` (same pattern as `PipelineConfigValidationError`). HTTP mapper emits top-level `{"errors":[e.to_dict() for e in exc.errors]}` with no `line` key. Planned in `23-01-PLAN.md` / expanded reject matrix in `23-02-PLAN.md`.

3. **UI-SPEC artifact** — RESOLVED
   - What we know: Phase has `UI hint: yes`; Phase 16 UI-SPEC covers YAML; copy table can be extended.
   - Resolution: Contract is `.planning/phases/23-admin-managed-ingest-sources/23-UI-SPEC.md` (already authored). Plans `23-01` / `23-04` cite it for copy, testids, and backstops; CONTEXT D-11…D-13 remain the locked copy source.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | pytest / backend | ✓ | 3.14.0 (`requires-python >=3.12`) | — |
| uv | deps | ✓ | 0.10.9 | — |
| Node.js | Playwright / Vite | ✓ | v24.21.0 | — |
| @playwright/test | admin journey | ✓ | ^1.62.1 | — |
| FastAPI / Pydantic | HTTP | ✓ | 0.141.1 / 2.13.5 | — |
| Live Supabase/Postgres | Live apply of `012` | ops VM | — | Unit tests use text-only migration + fake client; live apply is ops |

**Missing dependencies with no fallback:** none for unit/Playwright mock path.

**Missing dependencies with fallback:** Live DB apply — not needed for RED/GREEN in CI-style unit tests; document ops apply like `011`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (unit/contract) + Playwright `@playwright/test` ^1.62.1 (e2e) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| Quick run command | `uv run pytest tests/unit/test_http_ingest_sources.py tests/unit/test_phase23_migration_012.py -x` |
| Full suite command | `uv run pytest tests/unit -q` then `npm run test:web` (kill stale `:5174` first — STATE.md) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SRC-01 | CRUD round-trip + list survives reload (mock store / repo) | unit HTTP + Playwright | `uv run pytest tests/unit/test_http_ingest_sources.py -x` / Playwright journey | ❌ Wave 0 |
| SRC-02 | Invalid id/kind/label → 400 `{errors:[…]}`, zero writes; UI help visible | unit HTTP + Playwright | pytest reject cases; Playwright disclosure | ❌ Wave 0 |
| SRC-03 | Port wired; SPA only via service module | unit composition + adapter contract | `test_live_container_wiring` AMEND; adapter contract | ❌ Wave 0 (amend existing) |
| ADUX-10 | Typed add-form fields arm guard; kind-only does not; one dialog | Playwright | extend admin dirty describes | ❌ Wave 0 |
| D-17 | Migration 012 shape + RLS + no wipe | unit text contract | `test_phase23_migration_012.py` | ❌ Wave 0 |
| D-22 | Banned words absent | Playwright | existing test PRESERVE | ✅ |

### Sampling Rate
- **Per task commit:** focused pytest file(s) for the RED under edit
- **Per wave merge:** `uv run pytest tests/unit -q` + targeted Playwright admin describes
- **Phase gate:** Full unit suite green + `npm run test:web` green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_phase23_migration_012.py` — covers D-17 / SRC-01 storage
- [ ] `tests/unit/test_http_ingest_sources.py` — covers SRC-02/SRC-01 HTTP + zero writes + admin gate
- [ ] `tests/unit/test_supabase_ingest_source_repository_contract.py` — adapter boundary
- [ ] Amend `tests/unit/test_live_container_wiring.py` (+ composition if exact asserts) — SRC-03 / D-24
- [ ] Amend `tests/admin.spec.js` with sources journey + dirty cases — **without** editing D-22 tripwire body
- [ ] `web/src/services/ingestSourcesApi.js` mock harness (required for Playwright)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing Bearer JWT / GoTrue; same as other admin routes |
| V3 Session Management | no new | Reuse existing SPA session |
| V4 Access Control | yes | `require_admin` on all four endpoints; RLS deny-by-default |
| V5 Input Validation | yes | Server regex + kind match + label max 120 + Pydantic `extra="forbid"` |
| V6 Cryptography | no | No new crypto |

### Known Threat Patterns for admin ingest-sources CRUD

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Non-admin CRUD | Elevation of privilege | `require_admin` (403); pytest gate like pipeline config |
| Direct PostgREST access to table | Information disclosure / tampering | RLS enabled, zero policies; only service_role |
| Invalid / URL / `@handle` injection into scheduler later | Tampering | Strict UC/PL regex; reject before write |
| Massive label DoS | Denial of service | max 120 chars → 400 |
| Open-redirect via crafted id in «Открыть на YouTube» | Spoofing | Build URL only from validated `source_id` already stored; fixed path prefixes |

## Sources

### Primary (HIGH confidence)
- In-repo: `23-CONTEXT.md`, `REQUIREMENTS.md` SRC-01…03 / ADUX-10, `001_initial_schema.sql`, `011_phase16_pipeline_config.sql`, `pipeline_config` port/use-case/HTTP/SPA/guard files (cited with line ranges above)
- Context7 `/websites/fastapi_tiangolo` — `JSONResponse` custom status/body
- Context7 `/pydantic/pydantic` — `ConfigDict(extra='forbid')` / `extra_forbidden`

### Secondary (MEDIUM confidence)
- Tube Archivist URL docs — channel id length 24 [CITED: https://docs.tubearchivist.com/urls/]
- Archive Team YouTube technical details — `PL[A-Za-z0-9_-]{32}` modern playlist form [CITED: https://wiki.archiveteam.org/index.php/YouTube/Technical_details]
- `.planning/research/SUMMARY.md` — Atom feed enumeration consumes canonical ids in Phase 24

### Tertiary (LOW confidence)
- Community validators (rustypipe) for UC regex — consistent with D-14 but not Google vendor schema

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — reuse existing installed FastAPI/Pydantic/Playwright; no new packages
- Architecture: HIGH — locked CONTEXT + verified pipeline-config vertical slice
- Pitfalls: HIGH — tripwires and table-name collision verified in-repo; playlist legacy length MEDIUM/cited

**Research date:** 2026-10-17
**Valid until:** 2026-11-16 (30 days — stable in-repo patterns)
