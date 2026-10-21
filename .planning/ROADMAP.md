# Roadmap: Digest CDS

## Milestones

- ✅ **[v1 MVP](milestones/v1-ROADMAP.md)** — Phases 1-5 (shipped 2026-09-22)
- ✅ **[v1.1 YouTube → LLM → Supabase ingestion](milestones/v1.1-ROADMAP.md)** — Phases 6-11 (shipped 2026-10-02)
- ✅ **[v1.2 Admin UX + diagnostics + PIPE-01 MVP](milestones/v1.2-ROADMAP.md)** — Phases 12-16 (shipped 2026-10-05)
- ✅ **[v1.3 Live mail, scheduled ingestion & backlog debt](milestones/v1.3-ROADMAP.md)** — Phases 17-24 (shipped 2026-10-18)
- 🚧 **v1.4 UI polish & honest navigation** — Phases 25-28 (4 phases, 0 plans; roadmap created 2026-10-21)

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

<details>
<summary>✅ v1.3 Live mail, scheduled ingestion & backlog debt (Phases 17-24) — SHIPPED 2026-10-18</summary>

- [x] Phase 17: YAML merge-key acceptance in the strict validator (3/3 plans) — completed 2026-10-14
- [x] Phase 18: Reader-route honesty for draft materials (3/3 plans) — completed 2026-10-15
- [x] Phase 19: Unsaved-changes guard for the pipeline editor (2/2 plans) — completed 2026-10-16
- [x] Phase 20: MAIL-02 signup confirmation mail (2/2 plans) — completed 2026-10-16
- [x] Phase 21: MAIL-01 live SMTP digest delivery (3/3 plans) — completed 2026-10-18
- [x] Phase 22: Admin nav grouping (3/3 plans) — completed 2026-10-17
- [x] Phase 23: Admin-managed ingest sources (4/4 plans) — completed 2026-10-17
- [x] Phase 24: Scheduled ingestion (8/8 plans) — completed 2026-10-18

Full phase detail: [milestones/v1.3-ROADMAP.md](milestones/v1.3-ROADMAP.md)

</details>

## 🚧 v1.4 UI polish & honest navigation (Phases 25-28)

**Started:** 2026-10-21 · **Requirements:** 10 (`PIPEUI-01…04`, `THEME-01/02`, `NAV-01/02`, `KNOW-05`, `ING-09`) · **Source:** five UI defects reported from live use + the live proof owed for commit `0dddc75`.
**Phase count:** 4 (Phases 25-28) · **Plans:** 7 · **Status:** Phase 25 gap closure planned (7 plans, 7 waves — absolute: 25-01…25-04 = waves 1-4, 25-05…25-07 = waves 5-7); Phases 26-28 awaiting planning.

### Phase 25: Admin «Настройка» — naming, readable surfaces, token repair

**Goal:** An admin opening the pipeline section sees it named «Настройка», every field and label legible in both themes, and chrome that matches the rest of the product.
**Requirements:** PIPEUI-01, PIPEUI-02, PIPEUI-03, PIPEUI-04, THEME-01, THEME-02

**Locked scope facts (do not re-litigate):**

- **Naming (PIPEUI-01).** `web/src/components/AdminLayout.jsx` says «Пайплайн» in three places: the sr-only `h1` (line 49), the nav tab (line 70) and the mobile `<option>` (line 82). All three become «Настройка». The route `/admin/pipeline`, `PIPELINE_PATH`, `data-testid="admin-tab-pipeline"` and the guard/leave-blocker wiring stay byte-identical — the label changes, not the URL. No `/admin/settings` route.
- **Block heading (PIPEUI-03).** `web/src/components/IngestSourcesSection.jsx:171` «Источники ингеста» becomes «Источники».
- **Root cause of the unreadable «Канал | Плейлист» select (PIPEUI-02 / THEME-02).** The admin components already use the semantic tokens `paper`, `paper-2`, `ink`, `ink-2`, `muted`, `rule`, `accent-ink`, but `web/src/index.css` `@theme` declares none of them. Tailwind v4 silently emits no utility for an unknown token, so the `<select>` falls back to the native white field while inheriting white text in dark theme. **Declaring the token family** (dark values inside `@theme static`, light overrides under `[data-theme="light"]`) is the fix — it also repairs the currently inert `accent-ink` labels. No per-component colour hardcoding, no `!important`, no inline styles.
- **Theme-independent labels (THEME-01).** Filled buttons and the active nav pill label with `text-text-primary` (`AppShell.jsx:14` `linkClass`, plus the primary/accent buttons), which flips to `#0F172A` in light theme. They must carry a theme-independent white label. **Exception:** the `voting` fill `#EAB308` keeps a dark label — white on yellow fails contrast.
- **Chrome 999.2 (PIPEUI-04).** Drop the «Админ» eyebrow (`AdminLayout.jsx:42`), tab type down to the content-heading scale, wider tab gap, less empty space above the tab row.
- **Range note.** Declaring the family is a wide but *intended* visual change on admin pages only; the reader surface keeps `bg-app/text-primary`.

**Success criteria:**

1. On `/admin/pipeline` the tab row, the sr-only heading and the mobile section select all read «Настройка», while `page.url()` is still `/admin/pipeline` and the sibling tab still reads «Дайджест». *Proof:* Playwright assertions on all three surfaces plus the unchanged URL and `data-testid`.
2. The ingest-source «Тип» select is legible in **both** themes: its computed `background-color` is opaque (not the transparent/UA fallback) and the colour/background pair reaches a 4.5:1 ratio, with «Канал» / «Плейлист» present as options. *Proof:* Playwright computed-style assertion run once in dark and once under `[data-theme="light"]` — it fails on the pre-fix tree because the `bg-paper` / `text-ink` utilities never reach the DOM, so the field keeps the browser-default surface while the inherited text stays white in dark theme.
3. **Token-coverage gate (the RED for the root cause):** an automated test asserts that every `paper`, `paper-2`, `ink`, `ink-2`, `muted`, `rule`, `accent-ink` utility used under `web/src` resolves to a `--color-*` declaration in `web/src/index.css`, and that tokens whose value differs per theme also have a `[data-theme="light"]` override. This test fails before the `@theme` declaration lands and is the reason the phase cannot be closed as "works in dark".
4. In the light theme the labels on the purple `primary` and cyan `accent` fills and on the active nav pill are white, and the yellow `voting` fill keeps its dark label; both combinations hold ≥ 4.5:1. *Proof:* computed-colour assertions in both themes, with the `voting` exception pinned as a positive assertion (not an omission).
5. The ingest-sources heading reads exactly «Источники», the «Админ» eyebrow is absent from the DOM, the tab font-size equals the content `h2` scale, the tab gap is wider than the pre-fix `gap-2`, and the space above the tab row is smaller than pre-fix. *Proof:* Playwright text-absence plus computed-style assertions on the shared admin chrome.

**Plans:** 6/7 plans executed — 25-01…25-05 green; 25-06…25-07 are gap closure for GAP-25-1…GAP-25-4 (+WR-03, WR-04)
- [x] 25-05-PLAN.md
- [x] 25-06-PLAN.md
- [ ] 25-07-PLAN.md

**Wave 1**

- [x] 25-01-PLAN.md
- [ ] `25-01-PLAN.md` — Tracer: собрать `admin-chrome.spec.js` в проекте `web` (`testMatch`), naming-RED на трёх поверхностях, «Настройка» в `AdminLayout.jsx` (PIPEUI-01, wave 1)
- [ ] `25-02-PLAN.md` — Хром админки: убрать eyebrow, кегль вкладок = `h2`, `gap-4`, `mt-0`, заголовок блока «Источники» (PIPEUI-03, PIPEUI-04, wave 2)
- [ ] `25-03-PLAN.md` — WCAG-хелпер + гейт покрытия токенов G-0…G-8, 13 токенов в существующих блоках `index.css`, читаемый «Тип» (THEME-02, PIPEUI-02, wave 3)
- [ ] `25-04-PLAN.md` — Тема-независимые подписи на заливках и скраймах, гейты G-9/G-10 (THEME-01, wave 4)
- [ ] `25-05-PLAN.md` — gap closure: `blendOver`, роли `success-ink` / `voting-ink-on-tint` / `accent-text` / `field-border`, гейты G-14 (тинт-композит ≥ 4.5) и G-15 (граница поля ≥ 3:1) (THEME-02, wave 5)
- [ ] `25-06-PLAN.md` — gap closure: все 18 статусных подписей на `-ink`, тост на `bg-paper-2`/`border-rule`/`text-ink`, снятие carve-out G-10, G-18 (label-role scan) и G-16 (контракт e2e-ассертов), e2e на пилюли / ошибку поля / баннер отправки / тост в обеих темах (PIPEUI-02, THEME-02, wave 6)
- [ ] `25-07-PLAN.md` — gap closure: `text-accent-text` на трёх подписях акцента, `border-field-border` на всех 16 контролах, G-17 и G-19, единственная заливка `ActionButton` (без `bg-transparent`), ожидание `data-theme` в `gotoAdmin` (PIPEUI-01, PIPEUI-03, PIPEUI-04, THEME-01, wave 7)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 25-02-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 25-03-PLAN.md

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 25-04-PLAN.md

### Phase 26: Section context — anchor scrolling and header active state

**Goal:** A reader who jumps inside an article and a reader who opens a material from a section both keep their bearings.
**Requirements:** NAV-01, NAV-02

**Locked scope facts (do not re-litigate):**

- **Bug 3 is anchor scrolling, not breadcrumbs.** The user explicitly confirmed this. Do **not** plan a breadcrumb component, a route-hierarchy change or a new navigation surface.
- Today `<header>` is `sticky top-0` (`AppShell.jsx:67`) with `--header-height: 64px` declared in `web/src/index.css`, and «Содержание» links are plain `#heading` anchors into `[data-testid="material-prose"]`. Nothing in `web/src` sets `scroll-margin-top` or `scroll-padding-top` (verified: no matches), so the target heading lands *under* the header.
- The fix is a scroll offset — `scroll-margin-top` on prose headings (`[&_h1]:scroll-mt-…` on the `prose-column` rule, or an equivalent `scroll-padding-top` on the scroll container) — sized to the 64px header plus breathing room. One mechanism, applied once, so every TOC link inherits it. Proven on a **short** section and a **long** section.
- **NAV-02 root cause.** The «Архив» `NavLink to="/archive"` (`AppShell.jsx:80`) is active only on `/archive`, so it goes dark on `/issues/:number` and on `/materials/:id`. The same `/materials/:id` URL is reachable from the archive, from search («База») and from an issue, so the origin **must ride navigation state** (`navigate(..., { state })` read from `useLocation()`), and must degrade honestly on a direct URL visit: no origin state → neither section claimed.
- Reuse the prefix-active pattern that already exists for «Админ»: `adminActive = pathname.startsWith('/admin/')` (`AppShell.jsx:39`) with an explicit `aria-current` and `linkClass({ isActive })` (lines 99-100). Do not derive origin from the URL, and do not persist it in `localStorage` — a remembered section would make a later direct visit claim a section falsely.

**Success criteria:**

1. **Short section:** following a «Содержание» link to a short section leaves the target heading fully visible, with `heading.getBoundingClientRect().top >= header.getBoundingClientRect().height` (64px) plus visible breathing room, and the heading is inside the viewport. *Proof:* Playwright scroll assertion comparing the heading rect against the measured header height — not a hardcoded 64.
2. **Long section:** the same assertion holds for a TOC link deep in a long article (target initially below the fold), proving the offset is not an artifact of short pages. *Proof:* same spec, second fixture.
3. **Archive origin:** from `/archive`, opening an archived issue keeps «Архив» lit on `/issues/:number`, and opening a material from there keeps it lit on `/materials/:slug`. *Proof:* Playwright `aria-current` + active-class assertions on the header link.
4. **Search origin:** opening the same `/materials/:slug` from `/knowledge` lights «База» and not «Архив». *Proof:* Playwright, starting from the «База» journey, asserting both links.
5. **Honest degradation:** a **direct** visit to `/materials/:slug` in a fresh context lights neither «Архив» nor «База», `/issues/:number` typed directly lights «Архив», and `/` lights only «Выпуск». *Proof:* Playwright fresh-context `goto` for each URL — this is the criterion that forbids a URL-derived guess and forbids a breadcrumb-shaped "you are here" claim.

### Phase 27: Header search runs on submit

**Goal:** One Enter from the header produces results.
**Requirements:** KNOW-05

**Locked scope facts (do not re-litigate):**

- Today `SearchPill.onSubmit` (`web/src/components/SearchPill.jsx:21-24`) navigates to `/knowledge?q=…`, and `KnowledgePage` only seeds `query` from `?q` (`KnowledgePage.jsx:49`) while `activeQuery` stays `null` (`:53`, documented as "pre-search landing"). The reader therefore lands on the pre-search screen and must click «Найти» a second time.
- Submitting must **run the search immediately**: exactly one API call per submission, no second click, no double-fire on re-render. An empty/whitespace query navigates to «База знаний» and **must not** call the API.
- Keep the existing query validation (blank/overlong guards) and the existing request shape (`q`, `role`, `limit`, `offset`). No new endpoint, no change to `knowledgeApi.searchKnowledge`, no change to the backend.

**Success criteria:**

1. Typing a query in the header and pressing Enter lands on «База знаний» with results already rendered — the pre-search landing is gone and «Найти» is never clicked. *Proof:* Playwright journey from the header input to a rendered hit row.
2. Exactly **one** `/knowledge/search` request is issued per submission. *Proof:* Playwright request interception counting calls to the search endpoint; pinned at `=== 1`, so a duplicate-fire (including a StrictMode double-invoke) fails the test.
3. A re-render after results are shown (role chip change, theme toggle, focus change) issues **no** additional request, and browser back/forward does not re-issue. *Proof:* the same counter asserted again after each interaction, plus a re-navigation assertion.
4. A whitespace-only submit navigates to «База знаний» and issues **zero** search requests, keeping the existing blank-query guard visible. *Proof:* Playwright counter at `=== 0` plus the inline guard assertion.

### Phase 28: Live proof — streamed DeepSeek ingest

**Goal:** Prove the committed streaming fix (`0dddc75`) on a real long video end to end.
**Requirements:** ING-09

**Locked scope facts (do not re-litigate):**

- **This phase is proof only.** The streaming fix is already committed as `0dddc75` ("fix(data-collection): stream DeepSeek responses to prevent TCP idle resets", `stream=True` + delta assembly). Do **not** plan adapter rewrites, new retry layers, timeout retuning or a new client.
- The run is `uv run --env-file ./ingestion-service/.env ingest <url>` against a video **longer than 10 minutes**, on the real DeepSeek path.
- A pass means: exit 0, material id/slug/batch id on stdout, `materials.status='draft'`, a `pending` shortlist row, and no `network_error` at stage `llm` / no `APIConnectionError`.
- If the run still fails, the phase records the observed failure and stops — the fix is re-opened as a *new* decision, not silently rewritten under a proof phase.

**Success criteria:**

1. `uv run --env-file ./ingestion-service/.env ingest <url>` on a video longer than 10 minutes exits 0 and prints material id, slug and batch id. *Proof:* captured command transcript attached to the phase summary.
2. A `status=draft` material **plus** a pending shortlist row exist in Supabase for that video, tied by `youtube_video_id`. *Proof:* a read-only query against `materials` + the shortlist row, recorded with the actual ids.
3. No `network_error` at stage `llm` and no `APIConnectionError` anywhere in the run; the streamed elapsed time is recorded so the improvement over the pre-fix TCP-idle failure is measurable. *Proof:* the run transcript plus the elapsed value in the summary.
4. The operator preconditions that made it pass (proxy disabled / env vars used / which `.env` file) are written into the phase summary, so a repeat run is reproducible by another operator. *Proof:* the recorded runbook-grade note, cross-checked against the actual command line used.

### Requirement coverage (v1.4)

| Phase | Requirements | Count |
|-------|--------------|-------|
| 25 — Admin «Настройка» | PIPEUI-01, PIPEUI-02, PIPEUI-03, PIPEUI-04, THEME-01, THEME-02 | 6 |
| 26 — Section context | NAV-01, NAV-02 | 2 |
| 27 — Header search | KNOW-05 | 1 |
| 28 — Live proof | ING-09 | 1 |

**Coverage:** 10 total / 10 mapped / 0 unmapped. Every requirement maps to exactly one phase; no phase carries a requirement owned by another.

### Execution notes (v1.4)

- **Order is fixed** as listed: the theme/token repair (25) is the widest diff and the only phase touching `web/src/index.css`; the two navigation phases (26, 27) consume that tree; the live proof (28) is independent of the UI work and can run last without blocking anything.
- **TDD is mandatory** (repo rules `tdd.mdc` / `AGENTS.md`): each criterion above names the proof that must exist **and fail first**. No production edit lands before its RED. Criteria expressed as computed style, request count, URL presence or DB row are the intended REDs — "the file was edited" is never a criterion.
- **No research SUMMARY.md exists for this milestone** — the scope is five defects found in live use plus one live proof, so there is no domain research to reconcile. The locked scope facts above are the authority.
- **Do not widen:** no breadcrumb component, no `/admin/settings` route, no reader-surface re-theme, no white label on the yellow `voting` fill, no DeepSeek adapter rewrite.
- **Operational hazard:** before any Playwright run, check for a stale Vite listener on `5174` (`Get-NetTCPConnection -LocalPort 5174 -State Listen`) and a stale `VITE_USE_MOCKS=false` in `web/.env.local` — both have produced mass false failures in earlier milestones.

## Backlog

> **Reviewed 2026-10-20** (`/gsd-review-backlog`) — v1.3 shipped 2026-10-18.
> - **Closed and removed** — 999.7 → Phase 17 · 999.1 → Phase 18 · 999.6 → Phase 19 (ADUX-10 → Phase 23) · 999.5 → Phase 22 · 999.3 resolved 2026-10-18.
> - **Promoted 2026-10-21 (v1.4 roadmap)** — 999.2 → **Phase 25**, folded into PIPEUI-04.
> - **Parked** — 999.4: product preference, not debt. Not in v1.4.

### Backlog 999.2: Follow-up — Phase 23 deferred UAT follow-up: AdminLayout chrome (PROMOTED → Phase 25)

**Goal:** Resolve the UAT checkpoint deferred during Phase 23 verification
**Source phase:** 23
**Deferred at:** 2026-10-17 during /gsd-verify-work 23 session completion
**Status:** **PROMOTED → Phase 25 (v1.4) as requirement PIPEUI-04** (2026-10-21). Do not plan it here; the work is owned by Phase 25. Closed as a backlog item.
**Follow-ups:**

- [x] Test 1: AdminLayout chrome: убрать надпись «АДМИН» над вкладками Дайджест|Пайплайн; уменьшить пустоту сверху; уменьшить кегль вкладок до уровня остальных заголовков; чуть увеличить расстояние между вкладками (promoted → Phase 25 / PIPEUI-04)

### Backlog 999.4: Follow-up — Phase 14 deferred UAT follow-up: Test 1 (Deferred — stays parked)

**Goal:** Resolve the UAT checkpoint deferred during Phase 14 verification
**Source phase:** 14
**Triaged:** 2026-10-13 — product preference, not tech debt; stays parked
**Status:** parked — **not** in v1.4; do not pull into Phase 25 (it is a different editorial-workflow decision, not UI polish)
**Deferred at:** 2026-10-04 during /gsd-verify-work 14 session completion
**Follow-ups:**

- [ ] Test 1: UX (для Phase 15+): две операции на одно editorial-решение избыточны для single-operator workflow — объединить Approve (decision) + Mark ready (material_status) в одну кнопку «Одобрить и подготовить → ready»; переименовать «Сделать ready» → «Отобрать», ready → «Отобран». (deferred 2026-10-03)
