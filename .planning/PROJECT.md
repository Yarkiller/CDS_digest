# Digest CDS

## What This Is

Digest CDS is an editorial knowledge service for СВА (Служба внутреннего аудита) Сбербанка. It turns external video/text into agent-prepared articles, then delivers weekly digests, topic voting → разборы, and semantic knowledge search for рядовой сотрудник СВА, Data Analyst, Data Scientist, and Админ (CDS/делегат).

## Core Value

Authorized СВА staff can read a trustworthy weekly issue of prepared articles and influence the next разбор through one honest vote — without treating raw video/transcript as published material.

## Current State

v1.3 Live mail, scheduled ingestion & backlog debt started 2026-10-14 (Phases 17+). Scope: backlog tech debt first — 999.1 reader-route honesty, 999.6 unsaved-changes guard, 999.7 YAML merge-key — then MAIL-02 investigation + signup mail, MAIL-01 live SMTP digest delivered to `profiles`, and a cron/systemd scheduled ingestion over the existing `ingest` CLI (YouTube channel/playlist source; drafts only, never auto-send).

v1.2 Admin UX + diagnostics + PIPE-01 MVP shipped 2026-10-05 (Phases 12–16, 26 plans). Admin preview/email honesty, draft→ready promote without SQL, CLI `--debug` secret-safe diagnostics, and PIPE-01 MVP (YAML config view/edit/validate/persist behind a `PipelineConfigRepository` port; no execution). Phase 16 verified 49/49 after a stale re-verification (covered-digest restamp + code-review advisory only).

v1.1 YouTube → LLM → Supabase ingestion shipped 2026-10-02 (Phases 6–11). Operator CLI turns a YouTube URL into a `materials` draft + shortlist row via captions → DeepSeek → `persist_draft_and_enqueue` (migrations 007–009). Backend/SPA remain readers; four-video UAT confirmed drafts in `/admin/digest`. Mail still StubMailer; signup confirmation mail unresolved.

v1 MVP (Phases 1–5) remains the editorial read/vote/admin publish surface (shipped 2026-09-22).

Stack: FastAPI, React/Vite, self-hosted Supabase + pgvector, `data-collection` + `ingestion-service`, Playwright, pytest.

## Current Milestone: v1.3 Live mail, scheduled ingestion & backlog debt

**Goal:** The admin sends the weekly digest through real mail (not a log line), new videos are collected on a schedule without a human running the CLI, and the accumulated backlog debt is closed before any new feature work.

**Target features:**
- Backlog 999.1 — reader-route honesty: a draft material opened at `/materials/<slug>` must not land on an error page (today `GET /materials/{slug}` is ready-only → 404)
- Backlog 999.6 — unsaved-changes guard (WR-04/WR-05): correct `beforeunload` plus a router guard, so in-app SPA navigation cannot silently drop the typed pipeline config
- Backlog 999.7 — restore valid YAML merge-key (`<<`) acceptance in the strict pipeline-config validator without weakening duplicate-key rejection
- MAIL-02 — investigate why no signup confirmation mail is sent, then ship the fix
- MAIL-01 — live SMTP digest delivery behind the existing `Mailer` port, with recipients taken from `profiles` and an honest `recipient_count`
- Scheduled ingestion — cron/systemd timer on the VM driving the existing `ingest` CLI against a YouTube channel/playlist; drafts + shortlist rows only, never auto-publish or auto-send

**Key context (risks to resolve in-phase):**
- **SMTP relay is not chosen yet.** Ship the port + config (`SMTP_*`), the operator plugs in the relay; ADR-0002 contour isolation applies.
- **No recipient list exists today** — `recipient_count` is hardcoded `0` by migrations 005/006 (`p_recipient_count int default 0`). `profiles` becomes the source of truth.
- **Listing a channel/playlist needs YouTube Data API v3 + an API key** — a new external public dependency that must be settled in a spike/ADR (against ADR-0002) before the scheduler phase can pass.
- **MAIL-02's root cause is unknown** since v1 («signup mailer is still unknown») — the phase opens with investigation, not implementation.
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

### Active

v1.3 scope (REQ-IDs are defined in `.planning/REQUIREMENTS.md`):

- [ ] Backlog 999.1 — a draft material reachable from the admin shortlist or email preview does not land on an error page
- [ ] Backlog 999.6 — unsaved pipeline-config edits survive in-app SPA navigation or are guarded before leaving
- [ ] Backlog 999.7 — the strict pipeline-config validator accepts valid YAML merge keys (`<<`) while still rejecting duplicate keys
- [ ] MAIL-02 — signup confirmation mail root cause identified and the send path shipped
- [ ] MAIL-01 — weekly digest delivered by a real mailer to the `profiles` audience with an honest `recipient_count`
- [ ] Scheduled ingestion — unattended collection against a YouTube channel/playlist writes drafts + shortlist rows only

### Out of Scope

- XP, streaks, anonymous average comparison — rejected for v1 and still rejected as the participation driver
- Storing or publishing video/audio/raw transcript as material — content contract
- Whisper / FoundryModels transcription — captions-only until FoundryModels revisit
- Ingestion HTTP API and auto-publish/auto-send — deferred beyond v1.3 (ING-*); v1.3 ships scheduled CLI collection only, never a send trigger
- PIPE-01 full pipeline execution — deferred past v1.3 (v1.2 shipped config + validation + UI only)
- Backlog 999.4 (unify Approve + Mark ready) and 999.5 (admin nav grouping) — product preference, not debt; stays parked
- Public leaderboard, quiz cards — still deferred
- Managed Supabase Cloud / managed PostgreSQL Cloud.ru as primary DB — ADR-0004
- Dynamic admin-managed email domain list — ADR-0003 (fixed two domains only)

## Context

- **Shipped v1:** Auth, issue/materials/archive, voting, knowledge search, разборы, and admin digest publish. Live adapters through migration 005. Mail is StubMailer.
- **Shipped v1.1:** Ingestion path (`data-collection` + `ingestion-service`) writes drafts into the same Supabase DB; backend/SPA unchanged as readers. DeepSeek MVP bends ADR-0002 temporarily. Migrations 007–009 live (`persist_draft_and_enqueue`, provenance, unique `youtube_video_id`, decision gate, sent-batch `already_saved`).
- **v1.2 focus:** Admin UX honesty, CLI `--debug`, PIPE-01 MVP (config/validation/UI), admin shortlist unit fix. Live SMTP and PIPE execution deferred.
- **v1.3 focus:** Backlog tech debt first (999.1 reader-route honesty, 999.6 unsaved-changes guard, 999.7 YAML merge-key), then MAIL-02 investigation + signup mail, MAIL-01 live SMTP digest to `profiles`, and a cron/systemd scheduled ingestion over the existing `ingest` CLI. No auto-send, no pipeline execution.
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
| Unsaved-changes guard (WR-04/WR-05) and admin nav grouping deferred to ROADMAP backlog 999.5/999.6 | Optional UX, not v1.2 success criteria; DB is safe (no save → no write) | — Deferred → backlog |

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
*Last updated: 2026-10-14 after starting the v1.3 milestone*
