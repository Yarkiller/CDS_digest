# Phase 23: Admin-managed ingest sources - Context

**Gathered:** 2026-10-17
**Status:** Ready for planning

<domain>
## Phase Boundary

An admin manages the list of **ingest sources** (a YouTube channel or playlist) on `/admin/pipeline`. The list is stored in the database behind an `IngestSourceRepository` port, validated server-side, and reached by the SPA only through a service module. The list is what Phase 24's scheduler will read.

This phase ships **stored + editable data only**. It does not list channels, does not fetch videos, does not run the pipeline, and does not schedule anything.

**In scope:**
- A new table for admin-managed subscriptions via an idempotent migration.
- `IngestSourceRepository` port + in-memory fake + Supabase adapter wired only in `composition/`.
- Thin admin HTTP surface: list / add / enable-disable / delete, `require_admin`-gated.
- Server-side canonical-id validation (`UC…`/`PL…` + kind match) with the existing top-level `{errors:[…]}` 400 envelope and zero writes.
- SPA section «Источники ингеста» **above** the YAML editor on `/admin/pipeline`, backed by a new `web/src/services/ingestSourcesApi.js` (mock + live).
- Per-row immediate persistence; **no** separate «Сохранить источники» button.
- Phase 19 guard extended to the sources form (`ADUX-10`): one dirty signal, one dialog, unchanged copy.

**Out of scope:**
- Scheduled enumeration, Atom-feed listing, high-water marks, systemd units — Phase 24 (`ING-02`/`ING-05`/`ING-06`/`ING-07`).
- Any way to run ingestion from the UI (HTTP trigger). `ING-01` is out of scope for v1.3.
- Resolving `@handle` / free-form URLs to a canonical id — rejected in REQUIREMENTS (would re-open the ADR-0002 gate).
- YouTube Data API v3, `google-api-python-client`, `yt-dlp` — rejected; canonical ids only.
- Inline editing of a saved source's label; soft delete / restore; per-source statistics.
- Changes to the pipeline-config validator, the pipeline-config API, or the YAML editor beyond the section placement.

</domain>

<decisions>
## Implementation Decisions

### Saving model and guard (ADUX-10)
- **D-01:** Every row action is **immediate** — add, enable/disable, and delete each issue their own request and the UI reflects the server's response. There is **no** «Сохранить источники» button and no buffered list diff. Rationale: the list is short (single-digit rows) and a second Save control on a page whose other half already has one is a UX trap. — **Reversibility:** costly — switching to a buffered model later requires a draft-state container, a dirty contract, and a new test surface for atomic list saves.
- **D-02:** The sources section renders **above** the YAML editor on `/admin/pipeline`, with its own heading «Источники ингеста». YAML remains below, unchanged. — **Reversibility:** reversible.
- **D-03:** The Phase 19 guard is reused **verbatim** — `useUnsavedChangesGuard` + `UnsavedChangesDialog` + `armBeforeUnload`, same copy «Есть несохранённые изменения. Уйти без сохранения?». The page keeps **one** dirty signal: `dirty = yamlDirty || sourceFormDirty`. One modal on the page; no second dialog and no per-surface copy. — **Reversibility:** costly — a second guard instance would double-prompt and force a precedence rule across two blockers.
- **D-04:** `sourceFormDirty = sourceId.trim() !== '' || label.trim() !== ''`. Changing the kind selector alone is **not** dirty (it carries a default; nothing typed is lost). — **Reversibility:** reversible.
- **D-05:** No optimistic updates. A row's control is disabled while its request is in flight; on failure the row shows an inline error and keeps the last known server state (a toggle that failed stays where it was). — **Reversibility:** reversible.

### Source fields and row content
- **D-06:** The type is an **explicit selector** «Канал | Плейлист» next to the id field. The server rejects a kind/prefix mismatch (`kind=channel` with a `PL…` id and vice versa) through the same structured 400 — the client is never the authority. — **Reversibility:** reversible.
- **D-07:** An **optional** `label` («Название») is captured on the add form. Trimmed; empty → `null`; max 120 chars (a longer value is a 400 with `path: "label"`). Rationale: no automatic titles exist without the rejected Data API. — **Reversibility:** reversible.
- **D-08:** A row shows: `source_id` in mono, the kind, the status («включён»/«выключен»), an enable/disable control, «Удалить», and an external link «Открыть на YouTube» (`/channel/{id}` for a channel, `/playlist?list={id}` for a playlist, `target="_blank"` + `rel="noopener noreferrer"`). The link lets the admin verify the id before enabling it, at zero cost and with no API. — **Reversibility:** reversible.
- **D-09:** `label` is set **only at creation**; inline label editing is not shipped here (see Deferred Ideas). This keeps the surface at exactly three row actions plus one add form. — **Reversibility:** reversible.

### Lifecycle and empty states
- **D-10:** `is_enabled` is a boolean column; **delete is hard** (`DELETE` removes the row). No soft delete, no archive, no restore. This matches the roadmap's "enable/disable, and remove". — **Reversibility:** one-way — a hard delete destroys the row, so a later restore feature cannot recover data deleted under this contract without a new column and a backfill.
- **D-11:** Zero enabled sources is **allowed**, but the section states it honestly: «Нет включённых источников — новые видео собираться не будут». The copy deliberately avoids «Запуск», «Выполнить», «Планировщик», «Расписание» because the shipped Playwright tripwire bans those words on this page (see D-20). — **Reversibility:** reversible.
- **D-12:** Two distinct empty states: (a) **no rows at all** — «Пока нет источников» plus the add form and the id help; (b) **rows exist, none enabled** — the D-11 hint above the list. Neither state hides the add form. — **Reversibility:** reversible.
- **D-13:** The «где взять id» instruction (`SRC-02`) lives **inline next to the form**: one short line under the id field plus a collapsible «Где взять id?» disclosure containing both recipes — channel: YouTube Studio → «Настройки» → «Канал» → «Расширенные настройки» → «Идентификатор канала» (`UC…`); playlist: open the playlist and copy `list=` from the address bar (`PL…`). — **Reversibility:** reversible.

### Claude's Discretion (validation, duplicates, persistence — not selected for discussion)
- **D-14:** Canonical id is strict: channel `^UC[A-Za-z0-9_-]{22}$` (24 chars total), playlist `^PL[A-Za-z0-9_-]{32}$` (34 chars total). Anything else — including a bare 11-char video id, a URL, or `@handle` — is a 400 with the top-level `{errors:[{path:"source_id", message:"…"}]}` envelope and **zero writes**. — **Reversibility:** reversible.
- **D-15:** A duplicate `(kind, source_id)` is a 400 with the **same** envelope and `path: "source_id"` (message «Этот источник уже добавлен»), so this surface keeps exactly one reject shape. The use case pre-checks the list so a unique-constraint violation can never surface as a `PersistenceError` 503; the DB unique index remains the backstop. — **Reversibility:** reversible.
- **D-16:** The new table is **`public.pipeline_ingest_sources`** in migration **`012_phase23_ingest_sources.sql`**. Do **not** reuse or alter `ingestion_sources` from `001_initial_schema.sql`: that existing table models *fetched content items* (`external_id`, `canonical_url`, `title`, `published_at`, `view_count`, `status`) and is the FK target of `materials.source_id`, `ingestion_jobs` and `source_texts`. Reusing it would conflate an admin subscription with a fetched item and break those relations. — **Reversibility:** one-way — renaming a shipped table means a migration plus updating the adapter, the service, and every test that names it.
- **D-17:** Migration shape mirrors `011`: `create table if not exists` (idempotent), `bigint generated always as identity` PK, `kind text not null check (kind in ('channel','playlist'))`, `source_id text not null`, `label text`, `is_enabled boolean not null default true`, `created_at`/`updated_at timestamptz not null default now()`, `unique (kind, source_id)`, **RLS enabled with zero policies** (deny-by-default; only the `service_role` client from `composition/live.py` reaches it), and no `truncate`/`delete from`. — **Reversibility:** one-way — the RLS/policy stance and the unique constraint are data-model commitments.
- **D-18:** REST surface under the existing admin router, all `require_admin`: `GET /admin/ingest-sources` → `{sources:[…]}`; `POST /admin/ingest-sources` → created row (201); `PATCH /admin/ingest-sources/{id}` with `{is_enabled}` → updated row; `DELETE /admin/ingest-sources/{id}` → 204. Unknown JSON fields stay `extra="forbid"` → 422, as on the pipeline config. Router module split is Claude's discretion (existing home: `interface/http/routes/admin.py`). — **Reversibility:** costly — the SPA service module and the Playwright mock both encode these paths.
- **D-19:** The reject row reuses the shipped `{path, message}` shape with **no** `line` key. Whether the helper is extracted from `PipelineConfigError.to_dict()` or duplicated is Claude's discretion; a second envelope shape is not. — **Reversibility:** reversible.
- **D-20:** RED split follows the Phase 18/Pitfall-24 precedent: **server-side validation, the 400 envelope and zero writes are pytest HTTP/contract tests** (`VITE_USE_MOCKS=true` cannot reproduce a real reject), while Playwright covers the admin journey (add → row appears → disable → delete, plus the dirty-guard prompts). Playwright is integration proof, not the RED for server behaviour. — **Reversibility:** reversible.
- **D-21:** Composition gains `ingest_sources: IngestSourceRepository | None = None` on `AppContainer` (defaulted so a bare container still constructs), wired in `composition/container.py` (in-memory fake) and `composition/live.py` (`SupabaseIngestSourceRepository` on the existing service-role client). A missing repo keeps the established `pipeline_config_not_configured` 503 style, with its own detail code. — **Reversibility:** reversible.

### Tripwires (state the disposition in each plan)
- **D-22:** `tests/admin.spec.js` → **`"pipeline config no execution controls render"`** (≈ line 1804) → **PRESERVE byte-identical.** It bans «Запустить», «Выполнить», «Запуск», «Планировщик», «Расписание» in the page text and as buttons. Every new string in the sources section must stay clear of those words — this is why D-11's copy is phrased the way it is. Do not "fix" the test.
- **D-23:** `tests/admin.spec.js` dirty-gating and admin-section-tab tests, `tests/unit/test_http_pipeline_config.py`, `tests/unit/test_phase16_migration_011.py`, `tests/unit/test_schema_migration_contract.py` → **PRESERVE** (no edit to the pipeline-config contract, no edit to migrations 001/011).
- **D-24:** `tests/unit/test_composition_container.py`, `tests/unit/test_live_container_wiring.py`, and any exact-`__all__` assertion on `supabase_integration` → **AMEND** (a new port and a new adapter export are additive wiring changes, not regressions).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 23 — goal, `SRC-01`…`SRC-03` + `ADUX-10`, the four success criteria, dependencies (Phase 22 host, Phase 19 guard), UI hint.
- `.planning/ROADMAP.md` § Phase 24 — what the list feeds; confirms scheduling and Atom-feed enumeration are **not** here.
- `.planning/REQUIREMENTS.md` — `SRC-01`, `SRC-02`, `SRC-03`, `ADUX-10`; and the Out-of-Scope rows that forbid `@handle` resolution, the Data API, and the ingestion HTTP API.
- `.planning/PROJECT.md` — v1.3 framing; the ADR-0002 / Data-API risk row and the "ingest CLI is already idempotent" note.
- `.planning/STATE.md` — Vite `127.0.0.1:5174` flakiness blocker: kill a stale listener before any full Playwright run; mass `ERR_CONNECTION_REFUSED` mimics a real regression.

### Established contracts this phase must copy
- `.planning/phases/19-unsaved-changes-guard-for-the-pipeline-editor/19-CONTEXT.md` — D-01…D-07 and D-12: the guard trio, the one dirty signal, the unchanged copy, "no carve-out". `ADUX-10` is owned here, not there.
- `.planning/phases/22-admin-nav-grouping/22-CONTEXT.md` — D-01…D-06 and D-12…D-15: `AdminLayout` is the host, `/admin/pipeline` unchanged, in-page tab navigation must keep firing the guard.
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` — copy table and the structured-error rendering contract the sources section reuses.
- `supabase-integration/migrations/011_phase16_pipeline_config.sql` — the idempotent-migration + deny-by-default RLS template for `012`.
- `supabase-integration/migrations/001_initial_schema.sql` § `ingestion_sources`, `ingestion_jobs`, `source_texts`, `materials.source_id` — proof that `ingestion_sources` is the fetched-content table and must not be reused (D-16).

### Code to change / reuse
- `backend/src/backend/domain/pipeline_config.py` — `PipelineConfigError.to_dict()` → the `{path, message}` row shape reused by D-19.
- `backend/src/backend/application/ports/pipeline_config.py` — the port style (`typing.Protocol`, no SDK imports) the new `ingest_sources.py` port copies.
- `backend/src/backend/application/use_cases/pipeline_config.py` — validate-then-persist use-case shape.
- `backend/src/backend/interface/http/routes/admin.py` (~lines 176–210 and 592–655) — the admin router, `_require_pipeline_config` 503 style, and the 400 `{errors:[…]}` mapping to mirror.
- `backend/src/backend/composition/container.py` (~lines 60–70, 130–136) and `composition/live.py` (~lines 55–65) — `AppContainer` fields and the two wiring sites.
- `backend/src/backend/tests_support/in_memory.py` (~lines 648–680) — the in-memory repository + recording-fake pattern.
- `supabase-integration/src/supabase_integration/pipeline_config_repository.py` — the adapter pattern (injected client, `PersistenceError` mapping at the boundary) for `SupabaseIngestSourceRepository`.
- `supabase-integration/src/supabase_integration/__init__.py` — the `__all__` export surface that gains the new adapter.
- `web/src/pages/AdminPipelineConfigPage.jsx` — the page that gains the section; holds `dirty`, `status`, the guard wiring and the modal.
- `web/src/services/pipelineConfigApi.js` — the mock/live service template (sessionStorage seed + arm/reset harness + typed error) for `ingestSourcesApi.js`.
- `web/src/hooks/useUnsavedChangesGuard.js`, `web/src/components/UnsavedChangesDialog.jsx`, `web/src/utils/unsavedChangesGuard.js` — the guard trio, reused unchanged.
- `web/src/components/AdminLayout.jsx` — the tab host that must keep firing the guard on section switches.
- `tests/unit/test_http_pipeline_config.py` — the ES256 JWT + container-attach harness the new HTTP tests reuse.
- `tests/unit/test_phase16_migration_011.py` — the text-only migration contract test pattern for `012`.
- `tests/admin.spec.js` (~1296–1814) — pipeline describes, the dirty-gating tests, and the no-execution-controls tripwire.

### Rules and decisions
- `.cursor/rules/tdd.mdc` and `AGENTS.md` — RED-first; `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`.
- `.cursor/rules/architecture.mdc` — port + composition-only wiring; SPA via `web/src/services/`; no domain/use-case SDK imports.
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — contour isolation: canonical ids only, no Data API / no scraping.
- `docs/adr/0004-self-hosted-supabase-on-vm.md` — self-hosted Postgres/Supabase owns the schema and RLS.
- `.planning/research/SUMMARY.md` § "YouTube public Atom/RSS feed" — the enumeration mechanism that makes canonical ids the only input Phase 24 needs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`PipelineConfigError.to_dict()`** already emits the `{path, message}` row (omitting `line` when absent) — the sources reject rows use the same shape.
- **`pipelineConfigApi.js`** is a complete template for a new service module: `isMocksEnabled()` branch, sessionStorage seed store, `armFail*`/`reset*` Playwright harness, `PipelineConfigError`-style typed error with `code`.
- **`InMemoryPipelineConfigRepository`** (with a `saves` list for zero-write assertions) is the fake pattern for `InMemoryIngestSourceRepository`.
- **`SupabasePipelineConfigRepository`** shows the injected-client + `PersistenceError` mapping contract verbatim.
- **Phase 19 guard trio** needs no change; only the `dirty` expression on the page widens.
- **`AdminLayout`** already provides the tab host and the narrow `<select>` that routes through `navigate()` so the blocker fires.

### Established Patterns
- Admin routes are `require_admin`-gated and live in one admin router; DTOs are Pydantic v2 with `ConfigDict(extra="forbid")`.
- Validation rejects are mapped **per route** to a top-level `{"errors": [...]}` 400 with **zero writes** — never nested under `detail`.
- Live adapters read through the `service_role` client wired in `composition/live.py`; RLS is enabled with no policies (deny-by-default) and is never widened for admin features.
- Migrations are idempotent text files with a text-only contract test; they carry no destructive statements.
- The SPA never touches Supabase for admin data — only `web/src/services/*.js`.
- The `web` Playwright project runs with `VITE_USE_MOCKS=true`, so any new UI must ship a mock branch and a harness to be testable.

### Integration Points
- `AdminPipelineConfigPage.jsx` → new section above the textarea → `ingestSourcesApi.js` (mock/live) → `GET/POST/PATCH/DELETE /admin/ingest-sources` → `IngestSourceRepository` → `pipeline_ingest_sources`.
- `AppContainer` gains the port field; `container.py` and `live.py` wire the fake and the Supabase adapter respectively.
- `supabase-integration/__init__.py` gains the adapter export.
- `tests/admin.spec.js` gains a sources journey; `tests/unit/` gains HTTP + migration + adapter-contract tests.

</code_context>

<specifics>
## Specific Ideas

- **Dirty is one signal.** `dirty = yamlDirty || sourceFormDirty`; the page must never arm two blockers or render two dialogs. A clean page prompts on neither path.
- **Per-row immediate means the server is always the truth.** After a successful row action, re-render from the response (or refetch); after a failure, keep the previous state and show an inline error.
- **The id help is a teaching surface, not decoration.** The admin must be able to answer "where do I get `UC…`/`PL…`?" without leaving the page, and the D-11 hint must be visible exactly when nothing is enabled.
- **Copy that must not appear anywhere in the section:** «Запустить», «Выполнить», «Запуск», «Планировщик», «Расписание» (D-22 bans them on this page).
- **Canonical id examples for tests:** valid channel `UC_x5XG1OV2P6uZZ5FSMdItQ`-shaped (24 chars, `UC` + 22), valid playlist `PL` + 32 chars; invalid: `dQw4w9WgXcQ` (video id), `@handle`, `https://youtube.com/...`, `UC` + 21, `PL` + 31.
- **Migration ordering matters** — `012` must not touch `001`; `test_schema_migration_contract.py` asserts the `001` text and stays green untouched.

</specifics>

<deferred>
## Deferred Ideas

- **One-off ingest of a single video from the admin UI** (paste a video URL/id, run it once, without adding a source to the list). Raised during this discussion. It is a new capability, not an editor detail: it needs an HTTP trigger surface, and `ING-01` ("Ingestion HTTP API") is explicitly out of scope for v1.3, while Phase 24 is specified as scheduler → existing `ingest` CLI only. Candidate for `/gsd-review-backlog` as its own future phase (admin-triggered single-video ingest, drafts only).
- **Inline label editing** for a saved source (D-09 keeps label creation-only). Natural follow-up if admins start with placeholder names.
- **Soft delete / restore** of a source (D-10 ships hard delete). Revisit only if an accidental deletion actually happens in use.
- **Automatic source titles / channel metadata** — needs the YouTube Data API v3, which is rejected in REQUIREMENTS (contra ADR-0002); would require its own ADR decision.
- **Per-source statistics** (last ingested, video count, last error) — belongs with the scheduler's run history in Phase 24 or later, not with the source list.

</deferred>

---

*Phase: 23-admin-managed-ingest-sources*
*Context gathered: 2026-10-17*
