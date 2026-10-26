# Digest CDS

## What This Is

Digest CDS is an editorial knowledge service for СВА (Служба внутреннего аудита) Сбербанка. It turns external video/text into agent-prepared articles, then delivers weekly digests, topic voting → разборы, and semantic knowledge search for рядовой сотрудник СВА, Data Analyst, Data Scientist, and Админ (CDS/делегат).

## Core Value

Authorized СВА staff can read a trustworthy weekly issue of prepared articles and influence the next разбор through one honest vote — without treating raw video/transcript as published material.

## Current Milestone: v1.5 Two-pass article enrichment

**Goal:** Ingest даёт сотруднику СВА полезную статью, а не сухое трёхблочное резюме: структура по содержанию, сохранённые факты и вывод для аудита; практические темы дополнительно получают гайд, код, проверенные ссылки и одну или несколько markdown-заметок в стиле личной базы знаний (по файлу на ключевую технологию).

**Target features:**
- Проход 1 всегда: новый шаблон (секции по ходу источника + слой фактов + «зачем СВА» и риски), без выдуманных ссылок
- Классификатор `practical | conceptual`; код / гайд / Tavily / cheat sheet — только у practical
- Проход 2: Tavily search/extract по коротким запросам; в статью попадают URL из ролика плюс только открывшиеся страницы; код можно сгенерировать
- Cheat sheet — одна или несколько markdown-заметок в стиле личной базы знаний (по файлу на ключевую технологию); гайд — секции статьи
- Глобальный лимит Tavily **1000** запросов: `try_consume`, потолок на ролик (~5), на исчерпании лог `tavily_quota_exhausted`, статья прохода 1 всё равно сохраняется
- Порты в `data-collection`, wiring в `ingestion-service/composition`; backend/SPA только показывают источники и скачивание файла

## Current State

v1.5 Two-pass article enrichment is in planning on branch `dev` (requirements → roadmap). Phase numbering continues at 29. Tavily is a second public API after DeepSeek (ADR-0002 bend). Carry from v1.4 (`INVALID_ROLE` toast) stays out of this milestone.

v1.4 UI polish & honest navigation shipped 2026-10-22 (Phases 25–28, 19 plans). Scope: close the five user-reported UI defects found in live use — honest admin naming and readable form surfaces, theme-independent button labels, section context that survives navigation plus anchor scrolling that clears the sticky header, and a header search that runs on the first Enter — and land one live proof that the streamed DeepSeek ingest completes end-to-end.

v1.4 status: **shipped 2026-10-22 — all four phases complete and verified (10/10 requirements), tag `v1.4`.** Before closeout the owner asked for three measured residuals to be settled, and all three landed under TDD (`eedd76d`): the radio-circle border moved to `border-field-border` (WR-11), the send-failure banner gained a tone so it paints `text-danger-ink` (WR-12), and the 640–959.98px header band got `--header-height: 112px` (NAV-01 residual). The full suite grew 215 → 218 Playwright cases.

Phase 26 shipped 2026-10-22: «Содержание» anchors land clear of the sticky header via one `scroll-padding-top: calc(var(--header-height) + 1rem)` declaration plus a measured 200px mobile token (`NAV-01`), and the header keeps «Архив»/«База» lit from a single closed `history.state.usr.section` marker that degrades honestly on a direct visit (`NAV-02`). UAT 3/3, threats_open 0; two review items carried (desktop gap ~7px in the 640–999px band).

Phase 27 shipped 2026-10-22: one Enter in the header runs the search immediately — the pill only produces a URL plus an opaque `submitId`, the page effect issues exactly one request per submission and zero for an empty query, and Back restores the settled rows at Δ=0 from a memory-only cache (`KNOW-05`). Closed after security (`27-SECURITY.md`, 0 open threats; T-27-16 accepted below threshold as AR-27-03) and a retroactive UI audit; four review findings were fixed under TDD — overlong submit on a mounted surface now clears the rows (WR-03), in-flight CTA chrome is single-sourced and role chips stay live, placeholder contrast clears 4.5:1 in both themes, and `searchGenerationRef` discards a slower older response (WR-01). UAT closed 2 pass + 1 deferred: C-12 paging resume is now automated (21 `pagingFixtures` + a resume case), and the `INVALID_ROLE` toast is deferred to the Phase 28 live stand because the mock adapter cannot produce that code.

Phase 28 shipped 2026-10-22: the streaming fix `0dddc75` is proven live rather than asserted — one run on a 24.14-minute video exited 0 in 21.91 s (`stage=llm elapsed_ms=16578`, zero `APIConnectionError`) and landed material 25 as `draft` with a `pending` shortlist row (`batch 7 / rank 2`). The phase was proof-only: `data-collection/` and `ingestion-service/` received zero edits. Two measured facts are now recorded preconditions: direct TLS to YouTube is blocked from the operator host (so `YOUTUBE_PROXY_URL` is required for captions, while DeepSeek is reached directly with `trust_env=False`), and `--template` is mandatory (the ROADMAP command line omits it and exits 2). The rider `FU-27-01` was closed under TDD — the empty header submit now replaces history — which closes `T-27-16` and leaves `27-SECURITY.md` at 19/19 with 0 open. The `INVALID_ROLE` toast was **not** closed: it needs an authenticated live SPA session, which the CLI proof never opened.

Phase 25 (v1.4 phase 1) shipped 2026-10-22: the pipeline section is named «Настройка» on all three surfaces with the URL unchanged, the semantic token family (`paper` / `paper-2` / `ink` / `ink-2` / `muted` / `rule` plus the theme-independent `-solid` / `on-solid` / `voting-ink` / `scrim` roles) is declared and gated by 22 automated checks (`G-0`…`G-21`), the «Админ» eyebrow is gone and the ingest block is «Источники». UAT closed 12/12 (320px geometry, partially filled forms, long ids, zero-one-many rows); security re-check found 37 threats, 0 open. The two findings that needed a semantic decision rather than a patch were settled at closeout under TDD: **WR-11** the radio circle now paints `border-field-border` (G-17 sanctions the one non-`<input>` control boundary by exact literal), and **WR-12** the send banner carries a tone so a failure paints `text-danger-ink`.

v1.3 Live mail, scheduled ingestion & backlog debt started 2026-10-14 (Phases 17+). Scope: backlog tech debt first — 999.1 reader-route honesty, 999.6 unsaved-changes guard, 999.7 YAML merge-key — then MAIL-02 investigation + signup mail, MAIL-01 live SMTP digest delivered to `profiles`, and a cron/systemd scheduled ingestion over the existing `ingest` CLI (YouTube channel/playlist source; drafts only, never auto-send).

v1.3 progress: **all 8 phases complete (Phases 17–24, 28 plans); milestone closed 2026-10-18 (tag `v1.3`).** Phase 18 shipped admin-gated draft preview + CR-01 fix. Phase 19 shipped the pipeline-editor unsaved-changes guard. Phase 20 (MAIL-02) shipped path (B): honest autoconfirm post-register copy (no letter claim), GoTrue owns confirmation. Phase 21 shipped live SMTP digest delivery with the `profiles` audience and honest counts. Phase 22 shipped the single «Админ» entry with in-page tabs. Phase 23 shipped DB-stored admin-managed ingest sources. Phase 24 shipped scheduled ingestion: a systemd timer drives `ingest-collect` against enabled sources, writing drafts + shortlist rows only.

Phase 24 closed with two UAT-found blockers fixed by gap-closure plans (`24-07`, `24-08`): the run bound moved from the inert `RuntimeMaxSec=1800` to `TimeoutStartSec=1800` on the `Type=oneshot` unit, and the `OnFailure=` alert now reads the numeric `MONITOR_EXIT_STATUS` instead of the `exited`/`killed` qualifier — both proven on a live systemd 255 host. One live-run checkpoint (a real enabled YouTube source) is deferred: `pipeline_ingest_sources` has no rows.

v1.2 Admin UX + diagnostics + PIPE-01 MVP shipped 2026-10-05 (Phases 12–16, 26 plans). Admin preview/email honesty, draft→ready promote without SQL, CLI `--debug` secret-safe diagnostics, and PIPE-01 MVP (YAML config view/edit/validate/persist behind a `PipelineConfigRepository` port; no execution). Phase 16 verified 49/49 after a stale re-verification (covered-digest restamp + code-review advisory only).

v1.1 YouTube → LLM → Supabase ingestion shipped 2026-10-02 (Phases 6–11). Operator CLI turns a YouTube URL into a `materials` draft + shortlist row via captions → DeepSeek → `persist_draft_and_enqueue` (migrations 007–009). Backend/SPA remain readers; four-video UAT confirmed drafts in `/admin/digest`. Mail still StubMailer; signup confirmation mail unresolved.

v1 MVP (Phases 1–5) remains the editorial read/vote/admin publish surface (shipped 2026-09-22).

Stack: FastAPI, React/Vite, self-hosted Supabase + pgvector, `data-collection` + `ingestion-service`, Playwright, pytest.

## Shipped Milestone: v1.4 UI polish & honest navigation (SHIPPED 2026-10-22)

**Status:** shipped 2026-10-22 — all four phases (25–28, 19 plans) complete and verified; 10/10 requirements; tag `v1.4`.

**Goal:** Every surface tells the reader the truth about where they are and what they are looking at — the admin section is named honestly, both themes stay legible, section context survives navigation, anchors land below the sticky header, and the header search runs on the first Enter.

**Target features (all shipped, 25–28):**
- Admin «Настройка» (PIPEUI-01…04): the section tab, the hidden heading and the mobile select say «Настройка»; the ingest-source «Тип» select is legible in both themes; the block heading is «Источники»; backlog 999.2 chrome polish lands in the same phase
- Theme contrast (THEME-01/02): filled buttons and the active nav pill carry a white label in both themes, backed by the missing semantic token family (`paper`, `ink`, `rule`, `accent-ink`) declared in `@theme`
- Section context (NAV-01/02): «Содержание» anchors stop hiding their heading under the sticky header, and the header keeps «Архив» / «База» lit when the reader opens an issue or a material from that section
- Header search (KNOW-05): submitting from the header navigates to «База знаний» and runs the search immediately — one API call, no second click
- Ingestion proof (ING-09): a live run of the streamed DeepSeek path on a long video produces a draft + pending shortlist row with no `APIConnectionError`

**Key context (risks to resolve in-phase):**
- The admin components already speak the `paper/ink/rule` vocabulary, but `web/src/index.css` never declares it — so every such utility silently no-ops. Declaring the family is the root fix for both the unreadable «Канал | Плейлист» select and the invisible `accent-ink` labels; expect a wide but intended visual change on admin pages.
- White labels are correct on purple (`primary`) and cyan (`accent`) fills, but the yellow `voting` button must keep its dark label — white on `#EAB308` fails contrast.
- «Архив» / «База» cannot be derived from the URL alone: the same `/materials/:id` URL is reachable from three sections, so the origin must ride navigation state and degrade honestly on a direct visit.
- The DeepSeek streaming fix is already committed (`0dddc75`); ING-09 is a live-proof requirement, not new adapter work.
- Bug 3 was confirmed as anchor scrolling, not a breadcrumb component: headings from «Содержание» scroll under the 64px sticky header and the section title disappears off-screen.

## Shipped Milestone: v1.3 Live mail, scheduled ingestion & backlog debt (SHIPPED 2026-10-18)

**Status:** shipped 2026-10-18 — all eight phases (17–24, 28 plans) complete; tag `v1.3`.

**Goal:** The admin sends the weekly digest through real mail (not a log line), new videos are collected on a schedule without a human running the CLI, and the accumulated backlog debt is closed before any new feature work.

**Target features:**
- ✓ Backlog 999.1 — reader-route honesty (Phase 18): an admin previews any draft **or ready** material at the admin-gated surface while the public reader route stays ready-only and draft ≡ missing (opaque 404)
- Backlog 999.6 — unsaved-changes guard (WR-04/WR-05): correct `beforeunload` plus a router guard, so in-app SPA navigation cannot silently drop the typed pipeline config
- Backlog 999.7 — restore valid YAML merge-key (`<<`) acceptance in the strict pipeline-config validator without weakening duplicate-key rejection
- ✓ MAIL-02 — root cause diagnosed; path (B) honest autoconfirm copy shipped; live confirmation relay deferred to Phase 21 (criterion 4) — Phase 20
- MAIL-01 — live SMTP digest delivery behind the existing `Mailer` port, with recipients taken from `profiles` and an honest `recipient_count`
- Scheduled ingestion — cron/systemd timer on the VM driving the existing `ingest` CLI against a YouTube channel/playlist; drafts + shortlist rows only, never auto-publish or auto-send

**Key context (risks to resolve in-phase):**
- **SMTP relay is not chosen yet.** Ship the port + config (`SMTP_*`), the operator plugs in the relay; ADR-0002 contour isolation applies.
- **No recipient list exists today** — `recipient_count` is hardcoded `0` by migrations 005/006 (`p_recipient_count int default 0`). `profiles` becomes the source of truth.
- **Listing a channel/playlist needs YouTube Data API v3 + an API key** — a new external public dependency that must be settled in a spike/ADR (against ADR-0002) before the scheduler phase can pass.
- **MAIL-02 closed as path (B)** — GoTrue autoconfirm + honest UI copy; confirmation-letter relay remains a Phase 21 ops criterion, not a backend `Mailer` feature.
- **The `ingest` CLI is already idempotent** (`already_saved`, unique `youtube_video_id`), so re-scanning a playlist must stay safe — lock it with a test.

## Shipped Milestone: v1.2 Admin UX + diagnostics + PIPE-01 MVP (SHIPPED 2026-10-05)

**Goal:** Admin can honestly review and promote ingested drafts, operators get secret-safe `--debug` diagnostics, and PIPE-01 ships as config + validation + UI only (no full pipeline execution).

**Status:** shipped 2026-10-05 — all five phases (12–16) complete and verified; Phase 16 re-verified 49/49 after a stale re-verification. Requirements 12/12 validated. Closeout: override (10 artifact items acknowledged/deferred; see STATE.md Deferred Items).

**Target features:**
- Admin material preview shows body, provenance, counts, reader link (not title+dek only)
- Email preview honesty (HTML / intro / summaries) + interstitial whitespace + purge leaked `test-header`
- Admin draft → ready control (remove SQL workaround for D-85 send gate)
- `score_factors` / justification honesty (fill via config MVP or honest empty)
- CLI `--debug` richer secret-safe operator diagnostics
- PIPE-01 MVP: YAML pipeline config + validation + admin UI (execution deferred past v1.3)
- Fix admin shortlist empty-batch HTTP contract (Phase 10 carry): `test_admin_shortlist_no_batches_returns_null_batch_id` + `test_admin_shortlist_empty_unsent_batch_returns_batch_id`

**Deferred at v1.2 close:** Live SMTP (MAIL-01) and signup confirmation mail (MAIL-02) → v1.3; scheduled ingestion → v1.3; PIPE full pipeline execution → beyond v1.3; ingestion HTTP API → later still.

## Prior Milestone: v1.1 YouTube → LLM → Supabase ingestion (SHIPPED)

**Goal achieved:** Operator can run a CLI one-shot that turns a YouTube URL into a `materials` draft and a shortlist row — without touching backend/SPA read paths.

<details>
<summary>v1.1 target features (shipped)</summary>

- `data-collection/` ports/DTOs: Transcript, VideoMetadata, MaterialDraft, TemplateKind
- Thin `ingestion-service/` Typer CLI (no HTTP API, no scheduler)
- YouTube captions via `youtube-transcript-api` (no Whisper)
- DeepSeek via OpenAI-compatible SDK — MVP LLM; FoundryModels revisit later
- Templates `lecture.md`, `podcast.md`
- Pipeline: URL → transcript → LLM → markdown → Supabase draft + shortlist enqueue
- UAT: 3–5 real videos as drafts in `/admin/digest`
- Phase 11: captions diagnostics hardening + persist error classification + sent-batch `already_saved`

</details>

## Success Criteria (v1 — developer-facing)

v1 is done only when **all** of the following hold:

1. **Backend operability** — DB deployed and working; API endpoints correct; no critical errors.
2. **Frontend–Backend integration** — Frontend connects to Backend; data loads from server; data posts to server; app works end-to-end.
3. **Security** — authentication configured; access policies (RLS or middleware); secrets not in code; CORS correct.
4. **Error handling** — network errors handled; validation errors handled; errors logged.
5. **Delivery quality** — code structured and readable; documentation complete and clear; deployment instructions work; process documented.

**Target runtime:** Cursor (solo developer + Claude workflow).

## Requirements

### Validated

- ✓ Ports & Adapters layout (`backend/`, `supabase-integration/`, `data-collection/`, `web/`) — brownfield
- ✓ Initial Supabase schema + RLS SQL (`supabase-integration/migrations/001_initial_schema.sql`) — brownfield
- ✓ React/Vite Editorial UI shell with mock data (`web/`) + design canon (`design-frontend/`) — brownfield
- ✓ Domain entities/ports for Material & Knowledge (in-memory composition) — brownfield
- ✓ Playwright E2E harness + pytest unit layout — brownfield
- ✓ Platform: live DB, FastAPI, FE↔BE, security, errors, docs (PLAT-*) — v1
- ✓ Corporate auth + session redirect (AUTH-*) — v1
- ✓ Current issue, materials (prepared article only), archive (ISSUE-*, MAT-*) — v1
- ✓ Voting cycle: one vote, change while open, audit-language ballot (VOTE-*) — v1
- ✓ Knowledge semantic search + role filters; разборы list/longread/notebook (KNOW-*, RAZB-*) — v1
- ✓ Admin shortlist → approve/reject → preview → send → archive (ADMIN-*) — v1
- ✓ `data-collection` ports/DTOs: Transcript, VideoMetadata, MaterialDraft, TemplateKind + TranscriptProvider/ArticleGenerator fakes (DTO-01, DTO-02) — Phase 6
- ✓ YouTube URL → `video_id` + captions (`ru`/`en`) via injected `youtube-transcript-api`; fail-closed `stage=captions` at unit/adapter level (CAP-01, CAP-02) — Phase 7
- ✓ `VideoMetadataProvider` + oEmbed + `ingestion-service` Settings/proxy composition (no Typer yet) — Phase 7
- ✓ DeepSeek article generation via lecture/podcast templates with fail-closed LLM errors, budget check, and redacted diagnostics (LLM-01…LLM-05) — Phase 8
- ✓ Persist `materials` as `status=draft` with provenance + overflow-safe shortlist enqueue via `persist_draft_and_enqueue` (PERS-01, PERS-02); RoleKind on drafts; CAP-02 persist spy empty — Phase 9
- ✓ `ingestion-service` Typer one-shot: staged progress, idempotent re-runs, separate `.env`, material_id/slug/batch_id/rank on success (CLI-01…CLI-05) — Phase 10
- ✓ Four-video live UAT: drafts visible in `/admin/digest` including English→Russian (CLI-03) — Phase 10
- ✓ Captions/persist diagnostics hardening: secret-safe envelopes, `23514`/int HTTP classification, sent-batch `already_saved` (migration 009) — Phase 11
- ✓ Admin shortlist empty-batch HTTP contract — `test_admin_shortlist_no_batches_returns_null_batch_id` + `test_admin_shortlist_empty_unsent_batch_returns_batch_id` (FIX-01) — Phase 12
- ✓ Admin material preview honesty (body, provenance, counts, reader link, pinned close) — Phase 13
- ✓ Email preview honesty + interstitial whitespace + `test-header` cleanup; email dialog is subject plus sandboxed HTML only — Phase 13
- ✓ Admin per-row draft → ready control clears the D-85 send gate without SQL; status-only promote leaves `published_at` untouched (ADUX-05) — Phase 14
- ✓ Honest shortlist «Обоснование»: populated `score_factors` or the explicit D-15 empty state, never a silent fake (ADUX-06) — Phase 14
- ✓ CLI `--debug` secret-safe operator diagnostics: opt-in stderr-only per-stage lines (timings/sizes/params/reasons/identifiers), byte-identical default stdout/JSON/exit-code path, allowlist + `SecretRegistry` + denylist redaction (DBG-01, DBG-02) — Phase 15
- ✓ PIPE-01 MVP: YAML pipeline config + validation + admin UI (no execution) — Phase 16
- ✓ PIPE-02: strict validate-before-save; invalid config rejected with a structured top-level 400 `{errors:[...]}` and zero writes (no silent accept) — Phase 16
- ✓ PIPE-03: validated config persists behind a `PipelineConfigRepository` port and reads back on later sessions; SPA has no deep Supabase coupling — Phase 16
- ✓ Backlog 999.1 — reader-route honesty: an admin opens any draft **or ready** material at an admin-gated preview surface (`GET /admin/materials/{slug}`) in the normal reader rendering with a visible «Черновик — предпросмотр, не опубликовано» marker, while `GET /materials/{slug}` and `get_material_for_reader` stay ready-only and draft ≡ missing (opaque 404, never 403) (ADUX-07, ADUX-08) — Phase 18
- ✓ MAIL-02 — path (B) honest autoconfirm post-register copy; no signup→`Mailer.send_digest`; criterion-4 relay → Phase 21 — Phase 20
- ✓ Backlog 999.7 — strict pipeline-config validator accepts YAML merge keys (`<<`) while still rejecting duplicate keys — Phase 17
- ✓ Backlog 999.6 — unsaved pipeline-config edits guarded on in-app SPA navigation and reload/close (ADUX-09) — Phase 19
- ✓ Backlog 999.5 / ADUX-12 — one «Админ» shell entry → `/admin/digest` plus in-page «Дайджест | Пайплайн»; `/admin/pipeline` unchanged, no new route — Phase 22
- ✓ SRC-01 — an admin manages the DB-stored YouTube channel/playlist source list on `/admin/pipeline`, with server-side canonical-id validation and structured 400s (`pipeline_ingest_sources`, migration 012, RLS on with zero policies) — Phase 23
- ✓ MAIL-01 — weekly digest delivered by a real SMTP mailer to the `profiles` audience with an honest `recipient_count`/`delivered_count` and contained failures — Phase 21
- ✓ ING-05/06/07 — scheduled ingestion: a systemd timer drives `ingest-collect` against enabled sources with a due gate in `Europe/Moscow`, a monotonic cursor, `flock` single-flight, a bounded run (`TimeoutStartSec=1800`), a numeric-code `OnFailure=` alert, and drafts + shortlist rows only (migration 013) — Phase 24
- ✓ PIPEUI-01…04 + THEME-01/02 — admin «Настройка» naming on all three surfaces with `/admin/pipeline` byte-identical, the semantic token family (`paper`/`paper-2`/`ink`/`ink-2`/`muted`/`rule` + theme-independent `-solid`/`on-solid`/`voting-ink`/`scrim`/`field-border`/`primary-text`/`accent-text`/`danger-ink`) declared and gated by `G-0`…`G-21`, eyebrow removed, ingest block «Источники», theme-independent labels on every fill — Phase 25
- ✓ NAV-01 — «Содержание» links land with the heading fully visible below the sticky header: one `scroll-padding-top: calc(var(--header-height) + 1rem)` in the base layer, plus a measured 200px mobile token, proven on short and long sections and with a zero-heading page — Phase 26
- ✓ NAV-02 — the header keeps «Архив»/«База» lit for an issue or material opened from that section via a single closed `history.state.usr.section` marker; a direct URL visit lights no false section — Phase 26
- ✓ KNOW-05 — a header submit runs the search immediately: one request per submission (the pill only produces a URL + opaque `submitId`), zero for an empty query, no double-fire on re-render, and Back restores the settled rows at Δ=0 from a memory-only cache; `knowledgeApi.js` byte-identical — Phase 27
- ✓ ING-09 — a live `ingest` on a 24.14 min video completes through the streamed DeepSeek path (`0dddc75`, `stream=True`): exit 0, material 25 `draft` (`youtube_video_id=HR7hD8TO4Z8`) plus `digest_shortlist_items` batch 7 / rank 2 / `pending`, no `APIConnectionError`, LLM stage 16.58 s recorded, with the operator preconditions (SOCKS5 proxy for captions only, `--template lecture`) written down — Phase 28

### Active

- [ ] Richer lecture/podcast templates: content-shaped sections, a source-facts layer, and explicit СВА takeaway + risks — not the three-block dry summary
- [ ] Ingest classifies `practical | conceptual`; generated code, in-article guide, Tavily reads, and a cheat sheet attach only when practical
- [ ] Two-pass pipeline: pass 1 is transcript-grounded; pass 2 enriches from Tavily search/extract with only live URLs plus links already in the video
- [ ] Practical materials attach one or more personal-KB markdown notes (one file per key technology); the guide stays in article sections
- [ ] Shared Tavily quota of 1000 requests (`try_consume`, ~5 per video); on exhaustion log `tavily_quota_exhausted` and still persist the pass-1 draft
- [ ] Reader surfaces a sources block and a cheat-sheet download; DeepSeek/Tavily stay behind ports, wired only in `ingestion-service/composition`

### Out of Scope

- XP, streaks, anonymous average comparison — rejected for v1 and still rejected as the participation driver
- Storing or publishing video/audio/raw transcript as material — content contract
- Whisper / FoundryModels transcription — captions-only until FoundryModels revisit
- Ingestion HTTP API and auto-publish/auto-send — deferred beyond v1.3 (ING-*); v1.3 ships scheduled CLI collection only, never a send trigger
- PIPE-01 full pipeline execution — deferred past v1.3 (v1.2 shipped config + validation + UI only)
- Backlog 999.4 (unify Approve + Mark ready) — product preference, not debt; stays parked
- Public leaderboard, quiz cards — still deferred
- Managed Supabase Cloud / managed PostgreSQL Cloud.ru as primary DB — ADR-0004
- Dynamic admin-managed email domain list — ADR-0003 (fixed two domains only)

## Context

- **Shipped v1:** Auth, issue/materials/archive, voting, knowledge search, разборы, and admin digest publish. Live adapters through migration 005. Mail is StubMailer.
- **Shipped v1.1:** Ingestion path (`data-collection` + `ingestion-service`) writes drafts into the same Supabase DB; backend/SPA unchanged as readers. DeepSeek MVP bends ADR-0002 temporarily. Migrations 007–009 live (`persist_draft_and_enqueue`, provenance, unique `youtube_video_id`, decision gate, sent-batch `already_saved`).
- **v1.2 focus:** Admin UX honesty, CLI `--debug`, PIPE-01 MVP (config/validation/UI), admin shortlist unit fix. Live SMTP and PIPE execution deferred.
- **v1.3 focus:** Backlog tech debt (999.1/999.6/999.7), MAIL-02 path (B) shipped in Phase 20, next MAIL-01 live SMTP digest to `profiles`, then cron/systemd scheduled ingestion over the existing `ingest` CLI. No auto-send, no pipeline execution.
- **v1.4 focus:** UI honesty, not new capability. Five live-use defects (admin naming/readable surfaces, light-theme button labels, anchor scroll under the sticky header, section context in the header, header search that needs a second click) plus backlog 999.2. The DeepSeek streaming fix already landed as `0dddc75`; ING-09 only proves it live.
- **v1.4 focus (complete):** UI honesty found in live use — admin section naming + readable surfaces (999.2 folded in), theme-independent button labels via a declared token family, anchor scroll offset plus section-aware header state, and header search that executes on submit. The streamed DeepSeek ingest fix (`0dddc75`) got its live proof here (ING-09, material 25). Remaining carry: the `INVALID_ROLE` filter toast needs a signed-in live SPA session.
- **v1.5 focus:** Replace the three-block DeepSeek summary with a two-pass editorial ingest. Pass 1 always writes a structured, fact-preserving СВА article. Pass 2 runs only for `practical` topics: Tavily search/extract (global 1000-request cap), generated code, in-article guide, verified links, and one or more personal-KB markdown notes (one file per key technology). Reader delivery is sources + file downloads; FoundryModels, admin “enrich” button, and the v1.4 `INVALID_ROLE` toast stay out.
- **Product framing:** Concept 3 Editorial UI («Digest CDS: издание»); personas and journeys J1–J6 in ingest context.
- **Known debt at v1.1 close:** Nyquist drafts for phases 6–8; Phase 10 deferred admin unit flake; UAT polish items; advisory WR notes in milestone audit; four v1 debug sessions still suppressed (see STATE.md Deferred Items).
- **Domain language:** `CONTEXT.md` + `docs/adr/` are canonical for agents.
- **Intel source:** `.planning/intel/` (ingest MODE=new, READY, 0 blockers).
- **Preserve:** `.planning/codebase/` brownfield map — do not delete.

## Constraints

- **Protocol / TDD**: Red–Green–Refactor mandatory; no production code without a failing test first.
- **Architecture**: Ports & Adapters; domain/use-cases free of FastAPI/httpx/supabase; wiring only in `composition/`.
- **Content contract**: Material = agent-prepared article only; video/audio are transient pipeline input.
- **Stack**: App on Cloud.ru VM; FoundryModels for ML pipeline; self-hosted Supabase+pgvector on separate VM (Docker Compose); `web/` Vite+React+Tailwind; Playwright UI tests; Python via `uv`.
- **Security**: Email domains `@sberbank.ru` / `@omega.sbrf.ru` only; secrets in env/Cloud.ru only; NFR-S* and error-handling contracts apply.
- **NFR**: Issue/material/search/admin p95 targets; read-path availability; FoundryModels async and non-blocking for published content.
- **Error UX**: Inline field errors, editorial empty states, banners/toasts with Retry, 401→login?returnUrl=, Russian copy per CONTEXT.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Public leaderboard deferred past v1 (ADR-0001) | Collect activity in v1; show leaderboard later | ✓ Locked |
| Cloud.ru VM + FoundryModels pipeline (ADR-0002) | Contour isolation; no public foreign LLM/Whisper | — Pending (proposed) |
| Fixed email domains only (ADR-0003) | Corporate access without dynamic whitelist UI | — Pending (proposed) |
| Self-hosted Supabase on separate VM (ADR-0004) | Own Postgres+pgvector+Auth; reject managed Cloud | — Pending (proposed) |
| Material = prepared article only | Editorial trust; no media-as-material | ✓ Locked (SPEC/content) |
| Ports & Adapters + TDD | Architecture & AGENTS rules | ✓ Locked |
| Announcement разборы suppress read CTA (G-04-2) | Visual honesty: unpublished status must not look readable | ✓ Phase 4 |
| Admin send publishes an issue and claims sent_at before stub mail (D-88, D-87) | Archive and the email link must match a real issue; SMTP is not live yet | ✓ Phase 5 |
| Self-service `/register` with Логин; login is email+password (G-01-3) | UAT showed a dead registration CTA and a name field on login | ✓ Phase 1 |
| Typography-only issue hero (D-26) | Current issue shows number, period, and title | ✓ Phase 2 |
| StubMailer until SMTP is configured | Publish and the issue link must exist before live mail | ✓ Phase 5 |
| Four debug sessions acknowledged at v1 close | Diagnosis files stayed open after the gap-closure plans; signup mailer is still unknown | — Deferred |
| DeepSeek MVP for ingestion LLM (ADR-0002 bend) | Captions-only pipeline first; one external LLM; FoundryModels revisit later | ✓ v1.1 (revisit still open) |
| Ingestion writes Supabase only; no backend coupling | Backend/SPA stay readers; CLI owns YouTube + LLM + shortlist enqueue | ✓ v1.1 |
| Phase 11 secret-safe captions diagnostics + persist SQLSTATE/HTTP classify | Operator stderr must not leak SDK/proxy; PERSIST_REASONS closed set | ✓ Phase 11 |
| Sent-batch re-run returns already_saved via RPC (migration 009) | Idempotent CLI after shortlist send; no duplicate materials | ✓ Phase 11 |
| Phase 10 UAT admin polish deferred to v1.2 | Preview/email/draft→ready/score_factors out of CLI milestone DoD | — Deferred → v1.2 |
| Phase 6 six-name public `__all__`; brownfield YouTube/Foundry/text-import DTOs deleted (D-01…D-03) | Single ingestion contract; no parallel public DTO names | ✓ Phase 6 |
| Captions list-then-pick + CaptionsError→locked reasons; CAP-02 live persist spy deferred (D-14) | Adapter-boundary SDK mapping; zero-row proof at unit level until Phase 9/10 | ✓ Phase 7 |
| Phase 7 seven-name public `__all__` (+ VideoMetadataProvider); proxy only in composition | Adapters take ready clients; no `os.environ` in adapters (D-17) | ✓ Phase 7 |
| DeepSeek via OpenAI-compatible SDK with injected client, `response_format=json_object`, disabled thinking, and composition-only env | No `os.environ` in adapters; caller controls client and secrets (D-07, D-11, D-14) | ✓ Phase 8 |
| `ArticleDraft` validation + `ArticleError` taxonomy; redacted diagnostics and locked `LLM_REASONS` | Provenance label caller-supplied; no transcript/key in operator JSON (D-12, D-13) | ✓ Phase 8 |
| Character cap enforced before DeepSeek call; `ArticleBudgetError` maps to `stage=llm_truncation` | No silent truncation; context limited to `char_count`/`max_chars` (D-08, D-09, D-10) | ✓ Phase 8 |
| Public `data_collection.__all__` stays seven names; new symbols negative-rooted | Adapter/error/template loader are module-private; `Stage` set unchanged (D-04, D-06) | ✓ Phase 8 |
| RoleKind is first-class on ArticleDraft/MaterialDraft; unknown/empty → employee | Audience roles travel with the draft; templates instruct the model; assembler copies the list | ✓ Phase 9 |
| Single persist+enqueue RPC; migration 007 canonical; unique `youtube_video_id` (D-05, D-06, D-09) | Atomic draft + shortlist write; overflow creates a new unsent batch; never attach to `sent_at` set | ✓ Phase 9 |
| Composition owns service-role wiring; idempotency lives in the RPC (D-11) | Blank url/key raises ConfigurationError before `create_client`; no Python video_id pre-check | ✓ Phase 9 |
| RoleKind closed only in Python (D-14a / decision A); no RPC CHECK on `p_roles` | Ingest CLI is the only v1 writer; a direct service_role call can persist unknown roles | ✓ Phase 9 |
| Latest unsent batch locked `FOR UPDATE`; unique `(batch_id, rank)` (WR-05) | Concurrent persist cannot assign the same rank; sent-batch conflict fallback removed (WR-02) | ✓ Phase 9 |
| `--debug` as an opt-in stderr side-channel via `StageDiagnostics`/`Clock` ports + `NullDiagnostics` no-op | Default path must stay byte-identical; measurement behind a port keeps the use-case infra-free and testable (D-01…D-13) | ✓ Phase 15 |
| Sink stays `typer`-free; `cli.py` injects `typer.echo(..., err=True)` as the emitter | Preserves the repo invariant that only `cli.py` imports typer; debug never reaches stdout | ✓ Phase 15 |
| Redaction = allowlist emission + exact-value `SecretRegistry` + denylist safety net (non-word boundary, compound credential names, control-chars stripped before token patterns) | DBG-02: never leak secrets/proxy credentials/cookies/tokens/bodies; mask-not-fail | ✓ Phase 15 |
| Debug lines use the domain `Stage` vocabulary (`captions`/`metadata`/`llm`/`persist`) and metadata is `video_id`-only | 1:1 correlation with `IngestError.stage`; no URL/author leakage (D-04/D-06) | ✓ Phase 15 |
| Pipeline config persistence sits behind a `PipelineConfigRepository` port; the Supabase adapter is wired only in `composition/live.py` | PIPE-03: the SPA reaches storage only through `pipelineConfigApi.js`; no deep Supabase coupling in UI | ✓ Phase 16 |
| Strict validator maps parser `RecursionError` to a structured 400 (WR-02) | Deeply nested flow collections (< 20k cap) must not surface as an unhandled 500; strict validation stays honest | ✓ Phase 16 |
| Unsaved-changes guard (WR-04/WR-05) and admin nav grouping deferred to ROADMAP backlog 999.5/999.6 | Optional UX, not v1.2 success criteria; DB is safe (no save → no write) | ✓ Phase 19 + Phase 22 |
| Phase 22: pathless `AdminLayout` hosts digest + pipeline under one shell «Админ» entry; materials preview stays a sibling; Phase 19 leave dialog reused without carve-out (ADUX-12) | Second top-level «Пайплайн» pill retired; URLs `/admin/digest` and `/admin/pipeline` unchanged; no `/admin` index | ✓ Phase 22 |
| Phase 18 preview reuses `MaterialReaderResponse` verbatim with `tags=[]`/`related=[]`; no preview DTO and no `status` key (D-02/D-08) | A second DTO shape would be a second reader contract to keep in sync; empty collections are the honest answer since a draft's neighbours/taxonomy may themselves be unpublished | ✓ Phase 18 |
| Phase 18: 403 comes only from `require_admin`; every non-draft slug is 404 `material_not_found` (D-03/D-04/D-12) | Keeps draft ≡ missing ≡ opaque 404 — no slug-existence oracle for a non-admin | ✓ Phase 18 |
| Phase 18: `no-store` set on the preview route only via the declared `Response` param (D-07) | An unpublished body must not be cached, but the mitigation must not widen onto the reader route; both directions are pinned | ✓ Phase 18 |
| Phase 18: only the shortlist modal link is repointed to `/admin/materials/{slug}`; the shared email href builder is untouched (D-10/D-11) | Repointing the shared builder would put admin URLs into the real digest mail ordinary readers receive (T-18-06); `render_email_html` stays shared so preview≡send parity remains provable | ✓ Phase 18 |
| Phase 18: the email-preview iframe grants `allow-popups allow-popups-to-escape-sandbox` while withholding script and same-origin powers (T-18-05) | The CTA must escape the frame to reach the app, but the frame must not gain script or origin powers; the frame body is backend-rendered with stdlib `html.escape` only | ✓ Phase 18 |
| Phase 25: the base `--color-primary` stays byte-identical (#8B5CF6) as fill/border/ring/tint; only the *label* role moves to the theme-dependent `--color-primary-text` (#A78BFA dark / #6D28D9 light) | A single token cannot be both a 4.5:1 label in both themes and an unchanged brand fill (D-05 forbids darkening the base); splitting the role was the only honest fix for GAP-25-5 | ✓ Phase 25 |
| Phase 25: readability is enforced by static node gates (`G-0`…`G-21`) that read the tree, not the runtime, and each gate carries a proof test | A gate that cannot fail is worse than no gate: CR-01 passed a green suite because `G-9` read only named tokens. Every new gate is mutation-proven, and `G-12` forbids arbitrary-value colours outright | ✓ Phase 25 |
| Phase 25: backstops the verifier cannot prove automatically are human UAT, never a silent pass | 12 geometry/overflow/state backstops (320px, partially filled forms, long ids, zero-one-many) closed through `/gsd-verify-work` instead of being asserted away | ✓ Phase 25 (12/12)
| Phase 26: anchor offset is one base-layer `scroll-padding-top` declaration plus a measured 200px mobile token, not per-heading `scroll-margin` | `scroll-padding-top` on the scrolling root covers every heading the reader can reach, including ones added later; the mobile height is measured (196.6 @390 / 122.6 @639, rounded to 200) rather than guessed, and 640px keeps the locked 64px header | ✓ Phase 26
| Phase 26: section origin is one closed literal in `history.state.usr.section`, never the URL and never storage | The same `/materials/:id` URL is reachable from three sections, so the URL cannot name the origin; state degrades honestly to "no section lit" on a direct visit, and `NavLink` would erase an explicit `aria-current` on an inactive route | ✓ Phase 26
| Phase 27: the header pill stays navigation-only (URL + opaque `submitId`); the search itself runs in the page effect | Keeps exactly one `searchKnowledge` import and one call site; the effect already owns role reset, error state and the cache, so a second caller would be a second contract | ✓ Phase 27
| Phase 27: byte-identical adapter digest is pinned over LF-normalised text, and the single-call-site gate excludes the declaration by SHAPE | A CRLF checkout must not redden C-24 for the wrong reason while any real edit still fails; whitelisting a filename would let the gate pass on an empty scan | ✓ Phase 27
| Phase 27: response ordering is protected by a generation counter inside `runSearch`, not by disabling inputs | The user can legitimately fire a second query while the first is in flight; a slower older response must be discarded rather than allowed to overwrite the newer settled result (WR-01) | ✓ Phase 27
| Phase 27: `INVALID_ROLE` toast is deferred to the Phase 28 live stand instead of re-pinning the frozen adapter | The mock adapter cannot produce that code, and faking it would trade a real gate for a simulated pass; the owner chose live verification in Phase 28 | ⏭️ Still deferred after Phase 28 — needs an authenticated SPA session, which the CLI proof never opened |
| Phase 28: the live proof runs the captions stage through `YOUTUBE_PROXY_URL` while DeepSeek stays direct (`trust_env=False`) | Measured, not assumed: direct TLS to `www.youtube.com` / `www.youtube-nocookie.com` times out from this host even though TCP:443 connects, while `api.deepseek.com` negotiates TLSv1.3. Routing DeepSeek through the proxy would be a regression | ✓ Phase 28 |
| Phase 28: the recorded command carries `--template lecture`, and the ROADMAP line is treated as inaccurate | The literal command exits 2 (`Missing option '--template'`) before any network call — measured. Evidence must show the command that actually ran, not the aspirational one | ✓ Phase 28 |
| Phase 28: proof is read back from the database by `youtube_video_id`, not from the presence of `✓ saved` | `youtube_video_id` is unique, so a repeat run reports `already_saved: true` and creates nothing; the only non-vacuous proof is a previously absent id producing a `draft` row plus a `pending` shortlist row tied by `material_id` | ✓ Phase 28 |
| Phase 28: the empty header submit replaces history (`FU-27-01`), closing `T-27-16` | Pushing stacked a landing over the settled `?q` the reader came from, so Back re-entered an already-executed query; the fix is one navigation option, proven failing-first on `history.length` 2 → 3 | ✓ Phase 28 |
| v1.4 closeout: the ballot radio circle paints `border-field-border`, and G-17 sanctions that one literal as a state indicator (WR-11) | The `<button role="radio">` never reaches `controlTags` (input/select/textarea only), so the only 3:1 token had no legal consumer; pinning the exact literal keeps dividers out while letting the indicator clear WCAG 1.4.11 | ✓ v1.4 closeout |
| v1.4 closeout: the send banner carries a tone (`data-banner-tone`) instead of a fixed `text-success-ink` (WR-12) | Colour by outcome is a data question, not a message question — substring-matching «не отправлена» would break on any copy edit | ✓ v1.4 closeout |
| v1.4 closeout: the 640–959.98px band declares `--header-height: 112px` (NAV-01 residual) | The header grows past 64px only in that band, and the token is the one input `scroll-padding-top` reads; measured 31.5px of heading under the bar at 800px | ✓ v1.4 closeout |
| MaterialPage resets `redirectToReader`/`forbidden` on every load (CR-01/WR-01) | The instance is reused across the preview→reader handoff the flag itself triggers, so a stale `true` re-rendered `<Navigate>` to the current URL (a blank page) and wedged later navigation; the D-12 URL-only assertion could not see it (WR-02) | ✓ Phase 18 |

<decisions>
## Locked decisions (from ADRs / ingest)

### ADR-0001 — Public leaderboard (LOCKED)
- **D-ADR-0001:** Do not ship a public leaderboard or gamification UI in v1. Activity may be collected from digests, voting, and related events; the public leaderboard is deferred past v1. Rejected for long-term design: private-only stats and anonymous average comparison as the primary participation driver.
  — **Reversibility:** costly — shipping a public ranking UI later requires product/IA work and may re-open privacy expectations already set with СВА users.
  — **Source:** `docs/adr/0001-public-leaderboard-gamification.md`

### ADR-0002 — Cloud.ru + FoundryModels (proposed → project constraint)
- **D-ADR-0002:** Deploy Digest CDS on a Cloud.ru VM. Process YouTube/text via FoundryModels API (transcription/import, summarization, analysis, tagging, embeddings) — not public foreign APIs and not local Whisper on the app VM. Store prepared article + provenance metadata; do not store media as material.
  — **Reversibility:** costly — provider change requires ML-pipeline adapter swap and redeploy.
  — **Source:** `docs/adr/0002-cloud-ru-foundrymodels-deployment.md`

### ADR-0003 — Email domain restriction (proposed → project constraint)
- **D-ADR-0003:** Registration/login limited to fixed domains `@sberbank.ru` and `@omega.sbrf.ru` via config; no dynamic admin-managed domain list in v1.
  — **Reversibility:** reversible — domain list is config-driven; adding domains is cheap, changing the “no admin UI” policy is a product decision.
  — **Source:** `docs/adr/0003-email-domain-restriction.md`

### ADR-0004 — Self-hosted Supabase (proposed → project constraint)
- **D-ADR-0004:** Use self-hosted Supabase (PostgreSQL + pgvector, Auth/Storage/REST) on a separate VM via Docker Compose; reject managed Supabase Cloud and managed PostgreSQL Cloud.ru as primary. Access encapsulated in `supabase-integration`; initial schema/RLS in `001_initial_schema.sql`.
  — **Reversibility:** one-way — operational ownership of backups/HA and migration path away from self-hosted is a platform commitment.
  — **Source:** `docs/adr/0004-self-hosted-supabase-on-vm.md`

### Content & process (SPEC / AGENTS)
- **D-CONTENT-01:** Published material is only an agent-prepared article; raw transcript/video/audio are never material content.
- **D-PROC-01:** TDD Red–Green–Refactor is mandatory for behavior changes.
- **D-ARCH-01:** Hexagonal Ports & Adapters; adapters in `supabase-integration` / `data-collection`; composition root owns wiring.

### Claude's Discretion
- Exact FastAPI route layout and FE service module split within Ports & Adapters and `web/src/services/`.
- FoundryModels client internals inside `data-collection` as long as DTOs/ports stay clean.
</decisions>

## Evolution

After each phase transition: move validated/invalidated requirements; log decisions; keep “What This Is” accurate.
After milestone: full review of Core Value, Out of Scope, and Context against shipped reality.

---
*Last updated: 2026-10-26 after starting milestone v1.5 — Two-pass article enrichment*
