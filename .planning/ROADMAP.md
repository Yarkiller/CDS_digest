# Roadmap: Digest CDS

## Milestones

- ✅ **[v1 MVP](milestones/v1-ROADMAP.md)** — Phases 1-5 (shipped 2026-09-22)
- ✅ **[v1.1 YouTube → LLM → Supabase ingestion](milestones/v1.1-ROADMAP.md)** — Phases 6-11 (shipped 2026-10-02)
- ✅ **[v1.2 Admin UX + diagnostics + PIPE-01 MVP](milestones/v1.2-ROADMAP.md)** — Phases 12-16 (shipped 2026-10-05)
- 🚧 **v1.3 Live mail, scheduled ingestion & backlog debt** — Phases 17-24 (in progress)

## Phases

<details>
<summary>✅ v1 MVP (Phases 1-5) — SHIPPED 2026-09-22</summary>

- [x] Phase 1: Platform Foundation & Auth (8/8 plans) — completed 2026-09-19
- [x] Phase 2: Issue, Materials & Archive (6/6 plans) — completed 2026-09-20
- [x] Phase 3: Voting Cycle (6/6 plans) — completed 2026-09-20
- [x] Phase 4: Knowledge & Razbory (10/10 plans) — completed 2026-09-21
- [x] Phase 5: Admin Digest Publish (9/9 plans) — completed 2026-09-22

Full phase detail: [milestones/v1-ROADMAP.md](milestones/v1-ROADMAP.md)

</details>

<details>
<summary>✅ v1.1 YouTube → LLM → Supabase ingestion (Phases 6-11) — SHIPPED 2026-10-02</summary>

- [x] Phase 6: Ports & DTOs (3/3 plans) — completed 2026-09-26
- [x] Phase 7: Captions Adapter (3/3 plans) — completed 2026-09-26
- [x] Phase 8: DeepSeek Article & Templates (4/4 plans) — completed 2026-09-27
- [x] Phase 9: Draft Persist & Shortlist Enqueue (4/4 plans) — completed 2026-09-27
- [x] Phase 10: CLI Composition & UAT (5/5 plans) — completed 2026-10-01
- [x] Phase 11: Captions diagnostics & persist error classification (4/4 plans) — completed 2026-10-02

Full phase detail: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

<details>
<summary>✅ v1.2 Admin UX + diagnostics + PIPE-01 MVP (Phases 12-16) — SHIPPED 2026-10-05</summary>

- [x] Phase 12: Admin shortlist empty-batch contract (3/3 plans) — completed 2026-10-02
- [x] Phase 13: Admin material & email preview honesty (8/8 plans) — completed 2026-10-03
- [x] Phase 14: Draft→ready & justification honesty (8/8 plans) — completed 2026-10-04
- [x] Phase 15: CLI --debug diagnostics (3/3 plans) — completed 2026-10-04
- [x] Phase 16: PIPE-01 MVP config UI (4/4 plans) — completed 2026-10-05

Full phase detail: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)

</details>

### 🚧 v1.3 Live mail, scheduled ingestion & backlog debt (In Progress)

**Milestone Goal:** The admin sends the weekly digest through real mail (not a log line), new videos are collected on a schedule without a human running the CLI, and the accumulated backlog debt is closed before any new feature work.

Backlog tech debt comes first (lowest blast radius first), then mail, then ingest sources, then the scheduler. Continuous numbering — v1.3 starts at Phase 17 (v1.2 ended at Phase 16).

- [x] **Phase 17: YAML merge-key acceptance in the strict validator** - The strict pipeline-config validator accepts valid `<<` merge-key documents, bounded so they cannot exhaust CPU, without weakening duplicate-key rejection (completed 2026-10-14)
- [x] **Phase 18: Reader-route honesty for draft materials** - An admin reads any draft at an admin-gated preview surface while the public reader route stays ready-only and draft ≡ missing (opaque 404) (completed 2026-10-15)
- [x] **Phase 19: Unsaved-changes guard for the pipeline editor** - The admin pipeline editor warns before losing unsaved changes on in-app SPA navigation and on reload/close (completed 2026-10-16)
- [x] **Phase 20: MAIL-02 signup confirmation mail** - The root cause is diagnosed and the delivered end state is honest (working relay mail, or explicitly autoconfirmed copy) (completed 2026-10-16)
- [ ] **Phase 21: MAIL-01 live SMTP digest delivery** - The weekly digest is delivered by a real SMTP mailer to the `profiles` audience, with honest counts and contained failures
- [ ] **Phase 22: Admin nav grouping** - The pipeline config is reached from a single «Админ» entry with an in-page tab-bar, not a second top-level nav item
- [ ] **Phase 23: Admin-managed ingest sources** - An admin manages the DB-stored YouTube channel/playlist source list on the pipeline page, validated server-side
- [ ] **Phase 24: Scheduled ingestion** - A systemd timer drives the existing `ingest` CLI against enabled sources, writing drafts + shortlist rows only

## Phase Details

### Phase 17: YAML merge-key acceptance in the strict validator

**Goal**: The strict pipeline-config validator accepts a valid YAML merge-key (`<<`) document and persists it, without weakening duplicate-key rejection and without opening a CPU-exhaustion path.
**Depends on**: Nothing (first phase of v1.3; standalone debt item)
**Requirements**: PIPE-04, PIPE-05
**Success Criteria** (what must be TRUE):
  1. An admin can save a pipeline config that uses valid `<<` merge keys; it validates, persists, and reads back in a later session.
  2. A document with a duplicated **explicit** key is still rejected with the same top-level structured 400 `{errors:[…]}` and zero writes — duplicate-key rejection is provably not weakened.
  3. A merge document crafted for high fan-out is refused by the expansion bound with the structured 400 and zero writes; the research-measured 480-char bomb (~1.5 s unguarded on this checkout, vs ~2 ms guarded) and deeper chains measured in the tens of seconds complete in bounded time instead of exhausting CPU.
  4. The merge fix and the bound ship together — there is no intermediate state where merges validate but expansion is unbounded; the strict 4-key `extra="forbid"` schema still governs the result and the structured-body contract is unchanged.

**Plans:** 3/3 plans complete

**Wave 1** (no dependencies)
- [x] 17-01-PLAN.md — Tracer: valid merge document accepted end-to-end, merge bomb refused (PIPE-04, PIPE-05)
- [x] 17-03-PLAN.md — Gap closure: a duplicate inside a merge source is rejected; nested-merge anchor holders taught (PIPE-04, PIPE-05)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 17-02-PLAN.md — Teach the anchor-holder mistake with a key-naming Russian message (PIPE-04, PIPE-05)

**Cross-cutting constraints**:
- Structured-body contract: every new reject keeps the existing top-level `{errors:[…]}` 400 envelope with zero writes and no new response shape — the duplicate row, the merge-bound row and the anchor-holder row each carry `path` and omit `line`.
- Single production file: both plans edit only `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`; the four-key `extra="forbid"` schema is never widened and `MAX_PIPELINE_CONFIG_CHARS` is untouched.
- Parse path only: no `web/` change (D-08); `_StrictSafeLoader` keeps subclassing `yaml.SafeLoader` and `validate()` keeps passing `Loader=_StrictSafeLoader`.
- PIPE-02 tripwire: `test_put_invalid_error_rows_are_verbatim_and_top_level` stays byte-identical.

**Tripwires**: `test_put_invalid_error_rows_are_verbatim_and_top_level` → **PRESERVE** (PIPE-02 duplicate-key rejection must survive verbatim). RED tests are pytest validator/HTTP tests (a `yaml.load` merge-fit oracle); Playwright is only integration proof.

### Phase 18: Reader-route honesty for draft materials

**Goal**: An admin can open any draft (or ready) material at an admin-gated preview and read it in the normal reader rendering, while ordinary readers still get an opaque 404 and no unpublished content is exposed.
**Depends on**: Nothing (independent debt item; the debt-track order is a sequencing choice, not a dependency)
**Requirements**: ADUX-07, ADUX-08
**Success Criteria** (what must be TRUE):
  1. An admin can open a draft material from the admin shortlist / email preview and read it in the normal reader rendering.
  2. `GET /materials/{slug}` and `get_material_for_reader` remain ready-only and untouched; an unknown **or draft** slug returns an opaque 404 (never 403) to any authenticated reader.
  3. A draft preview response is served `no-store`, carries a visible preview marker, and exposes no `related`/`tags` of unpublished material.
  4. The admin shortlist and email-preview links target the admin preview surface, and the email-preview CTA navigates the top-level app rather than being trapped inside the `sandbox=""` iframe.

**Plans:** 3/3 plans complete
- [x] 18-01-PLAN.md
- [x] 18-02-PLAN.md
- [x] 18-03-PLAN.md

**Wave 1** — backend preview surface (ADUX-07, ADUX-08):
- [ ] `18-01-PLAN.md` — Tracer slice + gate/non-draft outcomes + `no-store`/empty-relations/read-only edge contract

**Wave 2** — SPA preview rendering (ADUX-07, ADUX-08), depends on 18-01:
- [ ] `18-02-PLAN.md` — Tracer slice for the reader rendering with draft banner + client-side `NOT_FOUND` redirect + `ForbiddenPage` mapping

**Wave 3** — link honesty and sandbox escape (ADUX-08), depends on 18-02:
- [ ] `18-03-PLAN.md` — Email-preview CTA escapes the sandbox + admin shortlist link repointed at the preview surface

**Tripwires**: `test_materials_draft_slug_returns_404_not_403` → **PRESERVE** (the current ready-only contract must stay). RED test must be a pytest HTTP test — `VITE_USE_MOCKS=true` makes draft-404 structurally unreproducible in the browser suite (mock materials have no `status`).

### Phase 19: Unsaved-changes guard for the pipeline editor

**Goal**: The admin pipeline editor warns before losing unsaved changes on in-app SPA navigation and on reload/close.
**Depends on**: Phase 17 (same pipeline-editor surface); otherwise an independent debt item
**Requirements**: ADUX-09
**Success Criteria** (what must be TRUE):
  1. With unsaved edits, in-app SPA navigation away from the editor prompts with the existing Russian copy («Есть несохранённые изменения. Уйти без сохранения?»), and Cancel keeps the draft.
  2. A dirty editor prompts on reload/close via a correct `beforeunload` handler (`preventDefault()` + truthy `returnValue`); a clean editor prompts on neither path.
  3. The dirty flag clears after a successful save and stays armed after a server reject.
  4. `App.jsx` is migrated from declarative `<BrowserRouter>` to a data router (`createBrowserRouter` + `RouterProvider`) as its own behaviour-preserving plan gated by the full Playwright suite — the migration and the guard are never combined in one plan, and no double-prompt occurs.

**Plans:** 2/2 plans complete
- [x] 19-01-PLAN.md
- [x] 19-02-PLAN.md

**Wave 1** — the data-router migration, behaviour-preserving (ADUX-09 criterion 4 / D-09):
- [ ] `19-01-PLAN.md` — Tracer: `web/src/App.jsx` on a module-scope `createBrowserRouter` + `RouterProvider`, gated by the full Playwright `web` suite at the Wave-0 recorded count (the stated TDD exception for a refactor)

**Wave 2** — the unsaved-changes guard, RED-first (ADUX-09 criteria 1-3), depends on 19-01:
- [ ] `19-02-PLAN.md` — Tracer: the in-app SPA blocker + `UnsavedChangesDialog`; then the two-statement `armBeforeUnload` backstop with the amended tripwire; then the save/reject dirty-contract pins

**Cross-cutting constraints**:
- The migration and the guard are **never combined in one plan** (PITFALLS Technical Debt Patterns row = Never); the guard is wired only after the migration is green.
- The migration has **no RED test** by design — it is gated by the existing suite with the passed count measured on the untouched tree before the edit (never assume STATE.md's 110).
- The leave copy «Есть несохранённые изменения. Уйти без сохранения?» has **one home** (`web/src/utils/unsavedChangesGuard.js`), rendered only by the dialog; the reset `window.confirm` copy is unchanged (D-08).
- Correct `beforeunload` = exactly `preventDefault()` + truthy `returnValue`, attached only while dirty, removed on unmount and after a successful save, with no `window.confirm`/`alert` (D-05); no app copy on the reload/close path (D-06).
- The dirty signal is the existing `dirty === yaml !== savedYaml` — never a second "touched" flag (D-12); the guard blocks **every** dirty in-app navigation, including the `RequireAuth` 401 → `/login` redirect, with no pathname carve-out (D-04).
- The guard must stay extractable for Phase 23 (`ADUX-10`), which owns the ingest-sources editor.

**Tripwires**: `tests/admin.spec.js` dirty-gating → **AMEND** (the existing synthetic-`beforeunload` test green-lights the broken handler; amend it to assert the correct handler contract, never delete). **ADUX-10 is deliberately NOT owned here** — the ingest-sources editor guard ships in Phase 23 (sources); the gap is intentional, not forgotten.

### Phase 20: MAIL-02 signup confirmation mail

**Goal**: The signup-confirmation mail root cause is diagnosed and documented, and the delivered end state is honest — either a working confirmation email through the corporate relay, or an explicitly autoconfirmed flow whose copy never claims mail was sent.
**Depends on**: Nothing (opens the mail track); the shared relay decision must land here and is reused by the later digest-delivery phase
**Requirements**: MAIL-02
**Decision gate**: the **corporate SMTP relay choice** must be settled before this phase can pass — one relay serves GoTrue and MAIL-01 (ADR-0002 contour isolation applies).
**Success Criteria** (what must be TRUE):
  1. The current state is recorded and the root cause documented (GoTrue/Supabase Auth container config: `mailer_autoconfirm`, presence of `GOTRUE_SMTP_*`, relay reachability); the debug session `.planning/debug/g-01-3b-signup-mailer.md` is closed with the fix.
  2. Exactly one honest end state ships: (A) a working confirmation email through the corporate relay, or (B) an explicitly autoconfirmed flow whose Russian copy never claims that mail was sent.
  3. The signup confirmation is provably sent by the GoTrue/Supabase Auth container — routing it through the backend `Mailer` port would be an anti-feature.
  4. The corporate SMTP relay is chosen and proven by a smoke test with a one-command rollback, serving both GoTrue and MAIL-01.
  5. If autoconfirm is flipped off, the shipped `tests/auth.spec.js` post-register assertion is deliberately **amended** (never deleted) alongside a regression for the re-introduced signup path.

**Plans:** 2/2 plans complete

**Wave 1** (no dependencies)
- [x] 20-01-PLAN.md — Tracer: honest (B) post-register copy + harness + Playwright D-09/D-10 (MAIL-02)

**Wave 2** *(blocked on Wave 1)*
- [x] 20-02-PLAN.md — Close g-01-3b diagnosis; runbook relay shape/smoke/rollback; criterion-4 gap → Phase 21 (MAIL-02)

**Tripwires**: `tests/auth.spec.js` post-register assertion → **AMEND** (deliberate, with a relay smoke and one-command rollback); `test_auth_email_domain.py` → **PRESERVE** (the fixed two-domain gate is unchanged).

### Phase 21: MAIL-01 live SMTP digest delivery

**Goal**: The weekly digest is delivered by a real SMTP mailer to the `profiles`-derived audience, with an honest `recipient_count`, and a mail failure never turns an already-published digest into a 500.
**Depends on**: Phase 20 (the shared relay chosen and proven on the GoTrue lane)
**Requirements**: MAIL-01, MAIL-03, MAIL-04, MAIL-05
**Decision gate**: relay/TLS mode and port pairing, bounded timeouts, and partial-failure semantics are settled here; Phase 20's relay choice is the precondition.
**Success Criteria** (what must be TRUE):
  1. Recipients are resolved server-side from `profiles` through a repository port and the planned audience size is computed — this half lands and is testable **with the stub** before the real adapter exists.
  2. The digest is delivered over real SMTP (stdlib `smtplib`/`email`) behind the extended `Mailer` port, and both the planned audience size and the actually delivered count are recorded and reported (e.g. «доставлено N из M»); copy never claims the whole organisation.
  3. A mail failure (`SMTPException`/`OSError`/timeout) is contained — mapped to a domain error caught alongside `PersistenceError` with bounded timeouts — so an already-published digest returns success, never a 500 (D-88).
  4. `delivery_status`/`recipient_count` are written from the mailer's post-send result (idempotently), so a live send can no longer report `stubbed`/`0`.
  5. `SMTP_*` configuration is read only from the VM environment through `settings`/composition; no `os.environ` in adapters and no secret in app code.

**Plans**: TBD
**Tripwires**: `test_send_digest.py` `"stubbed"` asserts → **AMEND** (stub is no longer the delivered status); `test_send_audit_failure_after_publish_still_returns_success` → **PRESERVE** (D-88); `test_stub_mailer.py` → **PRESERVE** (the stub remains a test double); `test_composition_container.py` and `test_live_container_wiring.py` → **AMEND** (new recipients/mailer wiring).

### Phase 22: Admin nav grouping

**Goal**: The pipeline config surface is reached from the admin area rather than a second top-level nav item.
**Depends on**: Phase 17 (the pipeline-config surface being grouped); placed immediately before the ingest-sources phase
**Requirements**: ADUX-12
**Success Criteria** (what must be TRUE):
  1. There is exactly one top-level «Админ» nav entry pointing to `/admin/digest`; the second top-level «Пайплайн» item is gone.
  2. An in-page tab-bar «Дайджест | Пайплайн» lets an admin reach the pipeline config from the admin area; `/admin/pipeline` still resolves and no new route is added.
  3. 16-UI-SPEC A-2 is updated so it no longer mandates the second top-level «Пайплайн» item, and its "no second navigation bar" rule is honoured because the tab-bar is in-page.
  4. A failing Playwright test was written first per the backlog TDD note before the nav change.

**Plans**: TBD
**Tripwires**: `tests/admin.spec.js` nav assertions → **AMEND** if they assert the removed top-level «Пайплайн» item (the nav contract intentionally changed; disposition confirmed in-phase).
**UI hint**: yes

### Phase 23: Admin-managed ingest sources

**Goal**: An admin manages the list of ingest sources (YouTube channel or playlist) on the pipeline page, stored in the database, with server-side canonical-id validation.
**Depends on**: Phase 22 (the «Пайплайн» tab-bar host) and Phase 19 (the guard extended to the new editor)
**Requirements**: SRC-01, SRC-02, SRC-03, ADUX-10
**Success Criteria** (what must be TRUE):
  1. An admin can list, add, enable/disable, and remove ingest sources on the pipeline page, and the list survives a reload because it is stored in a new DB table via an idempotent migration.
  2. The source API validates the canonical source id (`UC…`/`PL…`) server-side and rejects anything else with the same top-level structured 400 `{errors:[…]}` and zero writes; the UI states where to obtain the id.
  3. Sources are read/written through an `IngestSourceRepository` port whose Supabase adapter is wired only in composition; the SPA reaches them only through a service module (no deep Supabase coupling).
  4. The Phase 19 unsaved-changes guard stays green and now covers the ingest-sources editor on `/admin/pipeline` (ADUX-10 — owned by this phase, not Phase 19).

**Plans**: TBD
**UI hint**: yes

### Phase 24: Scheduled ingestion

**Goal**: New videos are collected on a schedule without a human running the CLI — drafts and pending shortlist rows only, never publishing or sending.
**Depends on**: Phase 23 (the enabled source list)
**Requirements**: ING-02, ING-05, ING-06, ING-07
**Success Criteria** (what must be TRUE):
  1. A scheduled run enumerates new videos for each **enabled** source via the key-free public YouTube Atom feed (`feeds/videos.xml`, canonical `UC…`/`PL…` ids only) and ingests them through the existing pipeline, writing drafts + pending shortlist rows only.
  2. A per-source high-water mark prevents re-processing already-ingested videos, so a re-run is safe and does not re-pay caption/LLM cost.
  3. The systemd `Type=oneshot` service + timer runs unattended with `EnvironmentFile=` (0600), a pinned timezone, `flock`, `OnFailure=`, `RuntimeMaxSec=`, and journald logging; each run's outcome is visible and one bad video does not abort the batch.
  4. An import/reference guard test proves the scheduled path cannot reach publish/send, and the existing `ingest <url>` CLI stdout contract stays byte-identical.
  5. Zero new runtime Python packages are introduced (Atom feed + stdlib only).

**Plans**: TBD
**Notes**: YouTube Data API v3 / `google-api-python-client` / `yt-dlp` are rejected; the Atom-feed choice **removes the ADR-0002 gate** (do not plan a Data API spike). `@handle` resolution is out of scope.
**Tripwires**: `test_cli_ingest_contract.py` `EXPECTED_SUCCESS_LINES` → **PRESERVE** (byte-identical stdout contract).

## Progress

**Execution Order:**
Phases execute in numeric order: 17 → 18 → 19 → 20 → 21 → 22 → 23 → 24

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 17. YAML merge-key acceptance | 3/3 | Complete    | 2026-10-14 |
| 18. Reader-route honesty | 3/3 | Complete    | 2026-10-15 |
| 19. Unsaved-changes guard | 2/2 | Complete    | 2026-10-16 |
| 20. MAIL-02 signup mail | 2/2 | Complete    | 2026-10-16 |
| 21. MAIL-01 live SMTP digest | 0/TBD | Not started | - |
| 22. Admin nav grouping | 0/TBD | Not started | - |
| 23. Admin-managed ingest sources | 0/TBD | Not started | - |
| 24. Scheduled ingestion | 0/TBD | Not started | - |

## Backlog

> **Triaged 2026-10-13** (`/gsd-review-backlog`).
> - **Queued for v1.3** — Bucket A tech debt; promote with `/gsd-new-milestone` (next free phase numbers 17+).
> - **Deferred** — product preference, not debt.
> - **Removed 2026-10-13** — former 999.2 (merged into 999.1, identical root cause) and former 999.3 (stale: fixed by the global `@layer base button:not(:disabled) { cursor: pointer }` rule shipped in v1.2 Phase 15).
>
> **Moved into v1.3 (2026-10-14):** 999.7 → Phase 17 · 999.1 → Phase 18 · 999.6 → Phase 19 · 999.5 → Phase 22. **999.4 stays parked** (product preference, not debt).

### Backlog 999.1: Reader-route honesty for draft materials — `/materials/<slug>` error page (→ v1.3 Phase 18)

**Goal:** A reader link opened from the admin shortlist or the email preview must not land on an error page while the material is still a draft
**Source phase:** 13
**Tech-debt id:** `W-1` (`.planning/milestones/v1.2-MILESTONE-AUDIT.md`)
**Deferred at:** 2026-10-03 during /gsd-verify-work 13 session completion
**Merged:** former 999.2 folded in on 2026-10-13 — identical root cause (`GET /materials/{slug}` is ready-only → 404)
**Follow-ups:**
- [ ] Reader `/materials/<slug>` returns an error page. Check: slug validity, reader endpoint health, SPA route. (deferred 2026-10-03)
- [ ] «Открыть материал →» from the email/admin preview leads to an error page — reader route issue, not admin preview. (deferred 2026-10-03)

### Backlog 999.4: Follow-up — Phase 14 deferred UAT follow-up: Test 1 (Deferred — stays parked)

**Goal:** Resolve the UAT checkpoint deferred during Phase 14 verification
**Source phase:** 14
**Triaged:** 2026-10-13 — product preference, not tech debt; stays parked
**Deferred at:** 2026-10-04 during /gsd-verify-work 14 session completion
**Follow-ups:**
- [ ] Test 1: UX (для Phase 15+): две операции на одно editorial-решение избыточны для single-operator workflow — объединить Approve (decision) + Mark ready (material_status) в одну кнопку «Одобрить и подготовить → ready»; переименовать «Сделать ready» → «Отобрать», ready → «Отобран». (deferred 2026-10-03)

### Backlog 999.5: Follow-up — Phase 16 deferred UAT follow-up: admin nav grouping (→ v1.3 Phase 22)

**Goal:** Resolve the UAT checkpoint deferred during Phase 16 verification
**Source phase:** 16
**Triaged:** 2026-10-13 — product preference, not debt; promoted into v1.3 as Phase 22 (own separate phase, immediately before the sources phase)
**Deferred at:** 2026-10-04 during /gsd-verify-work 16 session completion
**Follow-ups:**
- [ ] Test 0: UX (предпочтение, не SPEC): убрать top-level nav-пункт «Пайплайн»; открывать конфиг только из админ-раздела. Вариант C — tab-bar «Дайджест | Пайплайн» на админ-страницах, top-level «Админ» → /admin/digest. Route /admin/pipeline не меняется, новый route не нужен. При реализации обновить 16-UI-SPEC A-2 и писать TDD (failing Playwright test first). (deferred 2026-10-04)

### Backlog 999.6: Follow-up — Phase 16 deferred UAT follow-up: unsaved-changes guard WR-04/WR-05 (→ v1.3 Phase 19)

**Goal:** Resolve the UAT checkpoint deferred during Phase 16 verification
**Source phase:** 16
**Tech-debt ids:** `WR-04`, `WR-05` (`16-REVIEW-DISPOSITION.md` — both an accepted known limitation)
**Deferred at:** 2026-10-04 during /gsd-verify-work 16 session completion
**Follow-ups:**
- [ ] Test 3: WR-04/WR-05 — unsaved-changes guard принят как known limitation: window.confirm внутри beforeunload ненадёжен в реальных браузерах, router-level guard не зарегистрирован, поэтому in-app SPA-навигация молча теряет черновик. БД безопасна (не сохранил → не записано); теряется только набранный текст. Fix: корректный beforeunload (event.preventDefault/returnValue) + router guard (useBlocker) с той же копией «Есть несохранённые изменения. Уйти без сохранения?». (deferred 2026-10-04)
- [ ] ADUX-10 — extend the guard to the ingest-sources editor; owned by v1.3 Phase 23 (sources), not Phase 19.

### Backlog 999.7: Follow-up — Phase 16 code-review advisory WR-01: YAML merge-key regression (→ v1.3 Phase 17)

**Goal:** Restore valid YAML merge-key (`<<`) acceptance in the strict pipeline-config validator without weakening duplicate-key rejection
**Source phase:** 16
**Tech-debt id:** `999.7` (`v1.2-MILESTONE-AUDIT.md` — `WR-01`, fails closed)
**Deferred at:** 2026-10-05 at v1.2 milestone close
**Follow-ups:**
- [ ] WR-01: `_StrictSafeLoader.construct_mapping` pre-constructs key nodes before `flatten_mapping`, so a valid YAML merge-key document (`<<`) is rejected with a cryptic internal-tag error instead of merging. Fails closed (still a structured 400 `{errors:[...]}`, zero writes) and the fixed 4-key `extra="forbid"` schema cannot yield a valid config from such a document, so it is not a v1.2 must-have. Fix: run `flatten_mapping` (or pre-resolve merge keys) BEFORE duplicate-key detection so `<<` documents behave like `SafeLoader` while duplicate-key rejection stays intact. Advisory only — fails closed. (deferred 2026-10-05)
