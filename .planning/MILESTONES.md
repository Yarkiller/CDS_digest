# Milestones

## v1.3 v1.3 (Shipped: 2026-10-18)

**Phases completed:** 8 phases, 28 plans, 68 tasks

**Key accomplishments:**
- The strict YAML validator now accepts `<<` merge documents with SafeLoader-identical mappings and refuses a 489-char fan-out merge bomb in ~2 ms with one structured 400 row, without weakening duplicate-key rejection
- An extra top-level anchor-holder key now gets a key-naming Russian message that teaches the `<<` form, while a genuine unknown key keeps Pydantic's English `extra_forbidden` message and the 400 envelope stays byte-identical
- A duplicate key written inside a mapping that is only ever used as a merge source is now rejected with the same single structured row as anywhere else, and anchor holders referenced only by a nested merge finally get the D-07 teaching message
- A new `GET /admin/materials/{slug}` route behind `require_admin` serves a `draft` with the reader DTO verbatim (empty `tags`/`related`, no `status`, `Cache-Control: no-store`), while the reader route and `get_material_for_reader` stay byte-identical.
- A new `admin/materials/:id` SPA route renders the REUSED `MaterialPage` (additive `preview` prop) with the persistent «Черновик — предпросмотр, не опубликовано» banner, maps the preview endpoint's 404 to a client-side `Navigate` back to `/materials/{slug}` and its 403 to `ForbiddenPage` — while the reader route, its loader and `tests/web-app.spec.js` stay byte-identical.
- The email-preview «Читать →» CTA now opens a real top-level browsing context — `target="_blank" rel="noopener noreferrer"` on both the backend renderer and its SPA mock mirror inside a `allow-popups allow-popups-to-escape-sandbox` iframe that still withholds script and same-origin powers — and the admin shortlist's «Открыть материал →» reaches `/admin/materials/{slug}` for draft and ready rows alike, while the shared email href stays reader-facing for preview and the real send.
- Migrated `web/src/App.jsx` to a single module-scope `createBrowserRouter` + `<RouterProvider>`, preserving every route and the RequireAuth layout; full Playwright `web` suite stayed at the measured Wave-0 baseline of 110.
- Shipped the ADUX-09 leave guard as a reusable util/hook/dialog trio: boolean `useBlocker(dirty)` drives an in-app modal with the locked Russian copy, and a two-statement `armBeforeUnload` arms the browser prompt only while dirty — full Playwright `web` suite 113 passed (110 Wave-0 + 3 new).
- Null-session register path shows locked honest copy «Регистрация завершена. Аккаунт активен — войдите.» via `armSignUpWithoutSession` harness; letter-claim language forbidden by Playwright regression.
- Digest audience resolved from all usable `profiles` emails with planned-M/delivered-N honesty, a domain `MailDeliveryError` contained after publish, and D-09/D-12 two-sentence copy — all sealed with `StubMailer` before live SMTP lands in Plan 02
- Live Supabase digest recipients (service_role, usable-email filtered) + planned `p_recipient_count` forwarding, an additive HTTP `delivered_count` that stays 200 through contained mail failure, the SPA contract, and the runbook digest SMTP smoke/rollback
- One admin-gated AppShell «Админ» entry plus a shared in-page «Дайджест | Пайплайн» underline switch, with both admin URLs unchanged and page H1s retired
- Dirty pipeline → in-page «Дайджест» (and the below-sm select) proven to raise the unchanged Phase 19 leave dialog with zero production edits, while 16-UI-SPEC A-2's second-shell «Пайплайн» mandate is retired
- Admin can list and add a YouTube channel ingest source end-to-end through domain → port → HTTP → SPA service → section above YAML, with ADUX-10 dirty OR wired.
- Server is the authority for canonical ingest-source ids: rejects never write, PATCH toggles enablement, hard DELETE returns 204, and CORS advertises DELETE for the live SPA.
- Idempotent `pipeline_ingest_sources` (012) with RLS deny-by-default, `SupabaseIngestSourceRepository` on the live admin client, and shared-VM apply stamped in runbook §4i.
- IngestSourcesSection ships full UI-SPEC chrome (toggle/delete/YouTube/empties/id-help/errors) with Playwright proving ADUX-10 against the existing Phase 19 leave guard.
- `ingest-collect` vertical slice: Atom feed → VideoRef → `run_ingest_pipeline` (bare id, `on_stage=None`) → monotonic cursor → two-line stdout summary, with deterministic FeedError/FeedSkip taxonomy.
- `select_window` + monotonic successful-only cursor + zero-LLM rescan at feed head; video/source isolation with graded exit codes 0/1/2 and fixed two-line stdout.
- «Пора/не пора» считается в Europe/Moscow по БД; пустой прогон штампует last_run_at; миграция 013 применена на общей VM без seed-строки.
- Checked-in ingest timer (15 min, Persistent=false), flock oneshot with RuntimeMaxSec/exit-75 success, journald alert distinguishing exit 1 vs 2, and dual-level ING-07 proof that collect_cli cannot reach publish/send.
- Admin GET/PATCH `/admin/ingestion-schedule` с доменной валидацией (русские сообщения), портом и Supabase-адаптером на `ingestion_schedule(id=1)`.
- Админ на `/admin/pipeline` настраивает автоматический сбор (переключатель, время МСК, дни) с немедленным PATCH и честным откатом — без кнопки запуска и без влияния на YAML-dirty.
- Replaced the inert `RuntimeMaxSec=1800` with `TimeoutStartSec=1800`, inverted the text contract so the broken token cannot return, corrected every record that asserted it, and proved on a live systemd 255 host that a killed run does not stamp `last_run_at`.
- The `OnFailure=` alert now reads `MONITOR_EXIT_STATUS` instead of the `exited`/`killed` qualifier, so exit 1 and exit 2 produce distinct journald lines — proven on the same host where the pre-fix exit-2 run had printed «unexpected failure (exit exited)».

---

## v1.2 Admin UX + diagnostics + PIPE-01 MVP (Shipped: 2026-10-05)

**Phases completed:** 5 phases, 26 plans, 56 tasks

**Key accomplishments:**
- Locked both empty GET /admin/shortlist shapes via in-memory HTTP units (no-batch null batch_id vs empty-unsent batch_id) with required-key asserts; production untouched.
- Authoritative `12-FIX-01-LOCK.md` empty-shape tables plus REQUIREMENTS/ROADMAP/PROJECT proof strings citing both 12-01 D-05 HTTP unit names.
- Wired `emptyUnsentDto` + `__DIGEST_ADMIN_EMPTY_UNSENT__` sticky harness and locked Playwright empty-unsent to D-80 empty UI (not digest_rest).
- GET /admin/shortlist items now carry full material preview fields (body, provenance, slug, reading minutes, char/word counts) proven by `test_admin_shortlist_returns_full_items`.
- Backend-owned `render_email_html` ships with interstitial `<p>`/`<br>` matrix, additive preview `html`, SITE_URL settings, and assert-only ban helpers — send parity deferred to 13-06.
- AdminItemPreview renders enriched shortlist markdown with provenance, counts, honest empty body, and reader link — Playwright green for ADUX-01 / D-04…D-06.
- Admin email preview displays backend/mock HTML in a fully sandboxed iframe; Playwright honesty moved to frameLocator; intro/connecting-text show paragraph-break hint.
- Synced Python↔JS ban helpers, idempotent migration 010 + runbook §4g, Playwright admin ban asserts, and shared-VM Studio SQL apply evidenced for ADUX-04 / D-20 live honesty.
- Send path reuses Plan 02 `render_email_html` with trusted `Settings.site_url`, optional StubMailer `body_html`, and green D-12 preview≡send parity proof.
- Material and email preview dialogs keep «Закрыть» in view with cursor-pointer while their bodies scroll
- Email preview success view is the subject plus a sandboxed iframe; the numbered preview.items list is gone
- Admin JWT can promote one draft to triage-ready without publishing; shortlist and D-85 send gate follow materials.status.
- Collection `POST /admin/materials/ready` returns order-preserving partial-success `results[]`; Approve still never flips `material_status` (D-02).
- Admin can promote draft→ready in the SPA (per-row + approved-drafts batch) against Plan 01/02 APIs, and empty shortlist «Обоснование» shows the exact D-15 honesty sentence.
- Per-row and batch «Сделать ready» now treat the POST response as authoritative — a still-draft shortlist refetch is reconciled by a pure `preservePromotedReady` helper and can no longer silently revert a promoted row.
- Approved drafts no longer read as a contradiction — the material_status pill is localised («черновик»/«готов») and the triage caption is qualified («одобрен (в шортлист)»), and the sticky footer drops its duplicate title list for a count-only hint plus a quantified batch CTA.
- The admin promote 503 is fixed at its shared root cause — `_fetch_one` now emits the FK-hinted `material_relations!material_relations_from_material_id_fkey(to_material_id)` embed, so live `get()`/`get_by_slug()` return a Material instead of raising PGRST201 → PersistenceError, with an offline PGRST201-rejecting fake locking the shape.
- The admin footer no longer advertises or performs a batch promote — the «Сделать ready все одобренные черновики (N)» CTA, its `promoteApprovedDrafts` handler/import, and the «Уберите черновики из одобренных или дождитесь ready.» copy are gone; the per-row «Сделать ready» and the D-85 send gate stay intact, and `sendHint` now reads a neutral «Отправка недоступна.» while an approved draft blocks send.
- A single global `@layer base` rule `button:not(:disabled) { cursor: pointer }` restores the pointer affordance across the admin surface — the shortlist «Превью материала» button, the per-row «Сделать ready», and the toolbar «Выбрать все» now compute `cursor: pointer`, while the disabled Send button stays non-pointer; the behavior is locked by a computed-cursor Playwright assertion.
- Opt-in `--debug` prints a secret-safe `[HH:MM:SS] debug stage=captions …` line on stderr through a Clock-injected sink and hybrid allowlist/denylist redaction, while the default stdout contract stays byte-identical.
- Full per-stage `--debug` lines across captions/metadata/llm/persist plus completed-stage + failed `reason`/`exit_code`/`elapsed_ms` failure lines and a `stage=config` line for pre-video errors — the default stdout/JSON/exit-code contracts stay byte-identical.
- The assignment denylist now masks underscore-compound credentials (`secret_key`/`access_token`/`client_secret`/`refresh_token`/`private_key`/`auth` → `[redacted]`) and strips control characters before the token patterns, closing the verifier's single blocker with committed regressions plus the review's W-2/W-3 coverage.
- Admin-only GET/PUT pipeline-config route with a raw-YAML editor, validate-then-persist use-case behind a repository port, and the SPA reaching storage only through `pipelineConfigApi.js` — no execution control ships
- Server-authoritative strict YAML + Pydantic `extra="forbid"` validator whose rejects return a top-level `{"errors":[{path,line?,message}]}` 400 with zero repository writes, wired into the default container as PyYAML 6.0.3

**Delivered:** Admin preview/email honesty (body, provenance, counts, reader link; sandboxed HTML preview; interstitial whitespace; `test-header` purge), admin draft→ready promote that clears the D-85 send gate without SQL, honest «Обоснование» (populated or explicit D-15 empty), secret-safe opt-in CLI `--debug` diagnostics with byte-identical default contracts, and PIPE-01 MVP — YAML pipeline config view/edit/validate/persist behind a `PipelineConfigRepository` port (no execution). Plus the Phase 10 carry: admin shortlist empty-batch HTTP contract.

**Git range:** `c2ca098` → `d29e318` (258 commits, 2026-10-02 → 2026-10-05). 237 files, +32475 / −1467.

**Closeout type:** override_closeout

**Known verification overrides:** 10 newly acknowledged, 5 carried forward from a prior close (see STATE.md Deferred Items)

**Known Gaps / Deferred:**
- Backlog 999.1–999.4: Phase 13/14 deferred UAT outcomes (reader route errors, preview cursor, Appr+ready unification)
- Backlog 999.5 admin nav grouping (option C tab-bar) and 999.6 unsaved-changes guard WR-04/WR-05
- Backlog 999.7: Phase 16 code-review advisory WR-01 — YAML merge-key (`<<`) rejected with a cryptic message (fails closed, structured 400)
- Advisory review INF-01/IN-02/IN-03 on the pipeline-config validator (non-blocking)
- Known debt carried from v1.1: Nyquist VALIDATION.md for phases 6–8; signup confirmation mail (MAIL-02) still open

Archives: [roadmap](milestones/v1.2-ROADMAP.md) · [requirements](milestones/v1.2-REQUIREMENTS.md) · [audit](milestones/v1.2-MILESTONE-AUDIT.md) · [phases](milestones/v1.2-phases/)

---

## v1.1 YouTube → LLM → Supabase ingestion (Shipped: 2026-10-02)

**Phases completed:** 6 phases (6–11), 23 plans, 60 tasks

**Delivered:** Operator CLI one-shot: YouTube URL → captions → DeepSeek article → Supabase `materials` draft + shortlist enqueue, with idempotent re-runs and four-video UAT on `/admin/digest`. Phase 11 hardened captions diagnostics and persist error classification (migrations 007–009).

**Git range:** `45db99f` → `fff73a3` (218 commits, 2026-09-26 → 2026-10-02). 225 files, +30507 / −549.

**Closeout type:** override_closeout

**Known verification overrides:** 1 newly acknowledged, 4 carried forward from a prior close (see STATE.md Deferred Items)

**Known Gaps / Deferred to v1.2:**
- Admin UX UAT polish (preview/email/draft→ready/score_factors)
- Phase 10 deferred-items.md (admin shortlist empty-batch unit flake)
- Nyquist VALIDATION.md drafts for phases 6–8; advisory WR notes in v1.1-MILESTONE-AUDIT
- PIPE-01 admin YAML pipeline UI; CLI `--debug`

**Key accomplishments:**
- Typed ingestion contracts (`Transcript` ≠ `MaterialDraft`) + port fakes in `data-collection`
- YouTube captions + oEmbed adapters with fail-closed `stage=captions` / metadata errors
- DeepSeek lecture/podcast templates with honesty, budget fail-closed, redacted diagnostics
- Atomic `persist_draft_and_enqueue` + overflow-safe shortlist (migrations 007–009 live)
- Typer `ingest` CLI: staged progress, separate `.env`, idempotent `already_saved`, four-video UAT
- Phase 11: secret-safe captions stderr; `23514`/int HTTP persist classify; sent-batch `already_saved`

Archives: [roadmap](milestones/v1.1-ROADMAP.md) · [requirements](milestones/v1.1-REQUIREMENTS.md) · [audit](milestones/v1.1-MILESTONE-AUDIT.md) · [phases](milestones/v1.1-phases/)

---

## v1 MVP (Shipped: 2026-09-22)

**Phases completed:** 5 phases, 40 plans, 94 tasks

**Delivered:** Corporate auth, the weekly prepared-article issue and archive, one honest vote, knowledge search and разборы, and admin shortlist → preview → send.

**Git range:** `cabd7eb` → `ba8be89` (330 commits, 2026-08-23 → 2026-09-22). 600 files, +77115 / −149 from the initial commit.

**Known verification overrides:** 4 newly acknowledged, 0 carried forward from a prior close (see STATE.md Deferred Items)

**Key accomplishments:**

- Offline FastAPI skeleton: Settings, GET /health, CORS allowlist, request_id middleware, and committed `.env.example`.
- ES256 JWKS verification, corporate email allowlist, and authenticated GET /me with ProfileRepository upsert — offline unit suite green.
- PingRecorder port + in-memory fake and JWT-gated POST /me/ping complete the D-13 Phase 1 API surface offline (PLAT-04 / D-10).
- Supabase profile + ping adapters and env-selected live composition are green offline; Auth dashboard seed is deferred for Plan 01-06 live proof.
- Login via supabase-js services, RequireAuth gated by VITE_USE_MOCKS, and meApi proof banner close AUTH-01/02/03 SPA contracts offline-green.
- PLAT-08 runbooks shipped; live FE↔BE proof human-approved (login → /me → /me/ping → activity_events).
- Self-service `/register` with Логин nickname, slim email+password login, and Playwright contracts closing UAT gap G-01-3.
- Planning and ops docs now match Plan 01-07 self-service registration: signUp INTEGRATE, amended D-08, runbook `/register` + «Логин».
- JWT-protected `GET /issues/current` through ports → in-memory → contentApi → typography IssuePage (hero+TOC or «Выпуск готовится»), with Wave 0 archive/material scaffolds
- Idempotent mock.js→SQL seed on shared VM plus service_role Issue/Material adapters replacing live in-memory content
- JWT-gated archive API + `/archive` reader UX with past IssuePage (no voting callout) and calm «Выпуск не найден» soft empty.
- Ready-only GET /materials/{slug} plus sanitized markdown MaterialPage with TOC and honesty rules (MAT-01/02/03, ISSUE-03).
- Read-only `voting_cycle` on current-issue DTO drives EditorialCallout open/closed/absent on `/` only — no vote write APIs.
- ServiceUnavailable splash (`/bad_gateway.png` + «Ошибочка вышла» + Повторить) with sticky content fail harness and green Phase 2 full Playwright+pytest gate under mocks
- JWT-protected GET/POST `/voting` returns BallotSnapshot via VoteRepository → in-memory, with PersistenceError→503 and InvalidVoteError→400 (D-40, D-52).
- Option-a open-cycle vote trigger + idempotent topic seed (LLM/RAG/AutoML) and live SupabaseVoteRepository wiring via service_role
- Unit-locked get_ballot leaders[] (single/tie/hide-when-zero) and D-48…50 empty/closed BallotSnapshot shapes — production logic already from 03-01; SPA copy deferred to 03-06.
- VOTE-03 complete: A→B upsert, closed/CAS 409+ballot with SPA adopt, mutation ErrorPanel vs GET splash, save toasts — phase voting gate green under mocks.
- SPA votingApi + VotingPage under mocks: honest never-voted UX, confirm-one-vote with D-52 snapshot apply, D-47 pointless-POST guard, no row «Лидирует» (D-40, D-44…47, D-52, D-56).
- Muted server-driven leader strip, shared RU plurals with honest «0 материалов», and D-48…50 closed/empty `/voting` states under Playwright mocks.
- JWT-gated `GET /knowledge/search` via QueryEmbedder → chunk.search → search_knowledge, omitting scores (KNOW-01 / D-59 / D-61).
- KnowledgePage Submit/Enter «Найти» wired to `knowledgeApi.searchKnowledge` under mocks, with blank/overlong inline guards and slug-linked hit rows (KNOW-01 / D-57…D-61).
- Analyst/DS/Все chips filter knowledge search on the server, and an empty analyst result resets only the role without substituting other materials
- JWT-gated `GET /razbory` chronology via RazborRepository → list_razbors, with empty 200 and 503 unavailable (RAZB-01 / D-66 / D-69).
- Razbory chronology SPA at `/razbory` with AppShell «Разборы», ChronologyItem rows (Анонс + editorial byline), and empty CTA to `/voting` only (RAZB-01 / D-66…D-69).
- GET /razbory/{id} + RazborPage ship sticky TOC longread, announcement stub honesty (D-68), and content_kind quality vs Обзор (D-73) without notebook download.
- Authenticated `GET /razbory/{id}/notebook` streams `.ipynb` under NOTEBOOK_ROOT with path containment, and published RazborPage shows honest dual download strips (D-70…72) without regressing announcement stubs.
- Idempotent migration 004 seeds 1024-d knowledge chunks and razbors with hybrid RPC; live composition wires Supabase adapters + StubQueryEmbedder; operator confirmed apply on knowledge-db.ru with NOTEBOOK_ROOT ready.
- Playwright knowledge + razbory honesty suites green under mocks; VALIDATION.md marked wave_0_complete / nyquist_compliant with explicit UI-SPEC backstops.
- Announcement chronology rows no longer expose «Читать разбор →»; they show the honest «готовится» placeholder while published rows keep the read link (G-04-2).
- Ports & Adapters admin shortlist GET behind `require_admin` (profiles.role) plus `/me` app_role alignment to employee/admin
- Approve/Reject via `set_shortlist_decision` + `POST /admin/shortlist/items/{id}/decision` with draft approve allowed and non-admin 403
- Mandatory email preview + StubMailer send that publishes a digest issue once, blocks drafts/empty/already-sent, and embeds `/issues/{n}` for ADMIN-08
- Role-gated Admin Digest triage SPA under mocks: 403 for employees, shortlist chrome with factor honesty, batch Approve/Reject, select-all/top-3, mandatory preview fingerprint gate, and confirm send.
- Idempotent migration 005 (delivery columns + demo shortlist seed) plus SupabaseShortlistRepository and StubMailer live wiring; operator confirmed schema applied on shared VM.
- Phase 5 honesty gate: Playwright covers 403/empty/top-N/preview/send/draft + ADMIN-08 returnUrl; VALIDATION Wave 0 marked complete; stub send surfaces «К выпуску →».
- Intro and ordered blocks reach `preview.body` end-to-end — «Вводный текст» is visible in «Превью письма» (G-05-1).
- Reorderable topic blocks and optional interstitials drive preview composition; `material_ids` permutation becomes publication order while locked send copy stays intact.
- G-05-2 closed: after stub send (or cold `digest_rest`), triage rows/checkboxes hide behind «дайджест успешно выпущен» + «через 7 дней», while locked «Отправка записана» / «Уже отправлено» stay

---
