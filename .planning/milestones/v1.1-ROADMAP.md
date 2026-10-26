# Roadmap: Digest CDS

## Milestones

- ✅ **[v1 MVP](milestones/v1-ROADMAP.md)** — Phases 1-5 (shipped 2026-09-22)
- 🚧 **v1.1 YouTube → LLM → Supabase ingestion** — Phases 6-10 (in progress)

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

### 🚧 v1.1 YouTube → LLM → Supabase ingestion (In Progress)

**Milestone Goal:** Operator can run a CLI one-shot that turns a YouTube URL into a `materials` draft and a shortlist row — without touching backend/SPA read paths.

- [x] **Phase 6: Ports & DTOs** - Typed Transcript / MaterialDraft boundaries and in-memory port fakes
- [x] **Phase 7: Captions Adapter** - YouTube URL → captions with fail-closed, zero-row exits
- [x] **Phase 8: DeepSeek Article & Templates** - Validated MaterialDraft via lecture/podcast templates, honesty and fail-closed LLM errors (2026-09-27)
- [x] **Phase 9: Draft Persist & Shortlist Enqueue** - materials draft + provenance + overflow-safe shortlist enqueue (completed 2026-09-27)
- [x] **Phase 10: CLI Composition & UAT** - Typer one-shot, idempotency, staged progress, separate env, 3–5 video UAT (completed 2026-10-01)

## Phase Details

### Phase 6: Ports & DTOs

**Goal**: `data-collection` exposes typed ingestion contracts so adapters and the CLI never mix transcript with prepared article
**Depends on**: Nothing (v1.1 first phase; builds on shipped v1 schema/admin readers)
**Requirements**: DTO-01, DTO-02
**Success Criteria** (what must be TRUE):
  1. Types `Transcript`, `VideoMetadata`, `MaterialDraft`, and `TemplateKind` exist in `data-collection` and pass unit tests
  2. Ports `TranscriptProvider` and `ArticleGenerator` have in-memory fakes that unit tests can inject without network or DB
  3. A `Transcript` cannot be passed where a `MaterialDraft` is required (type boundary holds in tests)

**Plans**: `06-01-PLAN.md` · `06-02-PLAN.md` · `06-03-PLAN.md`

**Wave 1**
- [x] `06-01-PLAN.md` — Tracer: DTOs + ArticleGenerator fake + assembler + type boundary ✓ 2026-09-26

**Wave 2** *(blocked on Wave 1 completion)*
- [x] `06-02-PLAN.md` — TranscriptProvider fake + DTO validation edges ✓ 2026-09-26

**Wave 3** *(blocked on Wave 2 completion)*
- [x] `06-03-PLAN.md` — Public `__all__` rewrite + brownfield DTO delete ✓ 2026-09-26

### Phase 7: Captions Adapter

**Goal**: Operator can resolve a YouTube URL to captions, or get a loud captions-stage failure with no database side effects
**Depends on**: Phase 6
**Requirements**: CAP-01, CAP-02
**Success Criteria** (what must be TRUE):
  1. Given a YouTube URL, the captions path resolves `video_id` and returns a `Transcript` preferring `ru` then `en`
  2. Missing, disabled, or blocked captions exit non-zero with `stage=captions`
  3. A captions failure writes zero database rows (no partial materials or shortlist items) — Phase 7 proves at adapter/unit level (D-14); live persist spy in Phase 9/10

**Plans**: `07-01-PLAN.md` · `07-02-PLAN.md` · `07-03-PLAN.md`

**Wave 1**
- [x] `07-01-PLAN.md` — Tracer: ingestion-service scaffold + extract_video_id + IngestError + mocked captions happy path (CAP-01) — 2026-09-26

**Wave 2** *(blocked on Wave 1 completion)*
- [x] `07-02-PLAN.md` — Fail-closed CaptionsError + locked reasons + language edges (CAP-02 unit) + D-14 Phase 9/10 spy note — 2026-09-26

**Wave 3** *(blocked on Wave 2 completion)*
- [x] `07-03-PLAN.md` — oEmbed/VideoMetadataProvider + FakeVideoMetadataProvider + Settings/proxy + public `__all__` + runbook/integration gate — 2026-09-26

**Cross-cutting constraints:**
- CAP-01 and CAP-02 appear in every plan `requirements` field
- Adapters never read `os.environ`; composition injects clients (D-17)
- No Whisper / DeepSeek / persist / Typer / supabase migrations this phase
- CAP-02 live persist spy deferred to Phase 9/10 (D-14); unit proof only in Phase 7

### Phase 8: DeepSeek Article & Templates

**Goal**: Operator can turn a transcript into a validated prepared-article draft via lecture or podcast templates, with fail-closed LLM and context-budget behavior
**Depends on**: Phase 7
**Requirements**: LLM-01, LLM-02, LLM-03, LLM-04, LLM-05
**Success Criteria** (what must be TRUE):
  1. DeepSeek (OpenAI-compatible SDK) returns a validated `ArticleDraft` with `title`, `dek`, `body_markdown`; provenance label is caller-supplied in Phase 10
  2. Operator can choose `--template lecture|podcast` backed by repository markdown templates
  3. Network/5xx/invalid JSON/validation LLM failures exit non-zero with `stage=llm`, zero database rows, and no partial output
  4. System prompt requires honesty (transcript-only facts; output always Russian — `ru` format-only, `en` translated to Russian, terms/names/numbers/units preserved); oversized transcripts fail closed with `stage=llm_truncation` and no silent truncation. Supersedes "output language matches transcript".

**Plans**: `08-01-PLAN.md` · `08-02-PLAN.md` · `08-03-PLAN.md` · `08-04-PLAN.md`

**Wave 1**
- [x] `08-01-PLAN.md` — Tracer: stubbed DeepSeek JSON becomes an ArticleDraft for lecture and podcast

**Wave 2** *(blocked on Wave 1 completion)*
- [x] `08-02-PLAN.md` — Fail closed: SDK, JSON, and validation errors map to stage=llm

**Wave 3** *(blocked on Wave 2 completion)*
- [x] `08-03-PLAN.md` — Over-cap transcripts fail closed with stage=llm_truncation

**Wave 4** *(blocked on Wave 3 completion)*
- [x] `08-04-PLAN.md` — English suffix constant, fake LLM failures, and the public API boundary

### Phase 9: Draft Persist & Shortlist Enqueue

**Goal**: A successful draft write lands as `status=draft` with required provenance and appears on an unsent shortlist batch (creating a new batch when the current one is full)
**Depends on**: Phase 8
**Requirements**: PERS-01, PERS-02
**Success Criteria** (what must be TRUE):
  1. A successful persist inserts `materials` with `status=draft` only (never `ready`) and required provenance fields `source_url`, `youtube_video_id`, `source_author`, `source_published_at`, `provenance_label` (migration added if live schema lacks columns)
  2. The run enqueues `digest_shortlist_items` on the current unsent batch with `decision=pending`
  3. When the current unsent batch already has 5 items, the run creates a new unsent batch and enqueues there (does not fail-if-full)
  4. Persist/enqueue never attaches to a batch with `sent_at` set

**Deferred from Phase 7 (CAP-02 / D-14):** captions failure test — fake failing `TranscriptProvider` + spy `PersistPort` → `persist.calls == []` (Phase 7 proved CAP-02 at unit/adapter level; live zero-row assertion belongs to Phase 9/10).
**Plans**: `09-01-PLAN.md` · `09-02-PLAN.md` · `09-03-PLAN.md` · `09-04-PLAN.md`
- [x] 09-01-PLAN.md
- [x] 09-02-PLAN.md
- [x] 09-03-PLAN.md
- [x] 09-04-PLAN.md

**Wave 1**
- [x] `09-01-PLAN.md` — Tracer: RoleKind promotion — `roles: list[RoleKind]` on ArticleDraft/MaterialDraft, audience-role instructions in lecture/podcast templates, assembler copy, DeepSeek adapter normalization ✓ 2026-09-27

**Wave 2** *(blocked on Wave 1 completion)*
- [x] `09-02-PLAN.md` — PersistPort + persist_draft use-case with generate_slug/estimate_reading_minutes, DraftPersistError mapping, FakeDraftPersister ✓ 2026-09-27

**Wave 3** *(blocked on Wave 2 completion)*
- [x] `09-03-PLAN.md` — Migration 007 (provenance columns + unique youtube_video_id + atomic persist_draft_and_enqueue RPC) and SupabaseDraftPersister ✓ 2026-09-27

**Wave 4** *(blocked on Wave 3 completion)*
- [x] `09-04-PLAN.md` — Composition (Settings, Supabase client/persister factories, .env.example) plus idempotency/overflow/batch_sent and CAP-02 zero-persist tests ✓ 2026-09-27

### Phase 10: CLI Composition & UAT

**Goal**: Operator runs one Typer command end-to-end with staged progress, idempotent re-runs, separate env, and 3–5 real videos visible as drafts in `/admin/digest`
**Depends on**: Phase 9
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05
**Success Criteria** (what must be TRUE):
  1. `ingestion-service` Typer one-shot prints `material_id`, `slug`, `batch_id`, and `rank` on success
  2. Re-running the same `video_id` does not create duplicate materials or shortlist rows
  3. CLI prints staged progress (`✓ transcript` / `✓ LLM` / `✓ saved`) and loads secrets from `ingestion-service/.env` (not the backend env file)
  4. UAT: 3–5 real captioned videos appear as drafts in `/admin/digest` with no backend/SPA code changes required, including at least one English source video (draft in Russian)

**Plans**: 5/5 plans complete

Plans:
**Wave 1**
- [x] 10-01-PLAN.md — Tracer: Typer `ingest` happy path + PersistResult.already_saved on fakes (CLI-01, CLI-04)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 10-02-PLAN.md — Pipeline edges, D-08 errors, ingestion `.env.example` (CLI-04, CLI-05)
- [x] 10-03-PLAN.md — Migration 008 decision gate + SQL authoring (CLI-02)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 10-05-PLAN.md — Adapter already_saved parse + blocking schema push (CLI-02)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 10-04-PLAN.md — Live composition + four-video manual UAT (CLI-03)

**Cross-cutting constraints:**
- Edge CLI-02 concurrency: guarantees are Postgres `ON CONFLICT DO NOTHING` atomicity; no Python pre-check; parallel CLI processes may race but only one material row exists.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Platform Foundation & Auth | v1 | 8/8 | Complete | 2026-09-19 |
| 2. Issue, Materials & Archive | v1 | 6/6 | Complete | 2026-09-20 |
| 3. Voting Cycle | v1 | 6/6 | Complete | 2026-09-20 |
| 4. Knowledge & Razbory | v1 | 10/10 | Complete | 2026-09-21 |
| 5. Admin Digest Publish | v1 | 9/9 | Complete | 2026-09-22 |
| 6. Ports & DTOs | v1.1 | 3/3 | Complete | 2026-09-26 |
| 7. Captions Adapter | v1.1 | 3/3 | Complete | 2026-09-26 |
| 8. DeepSeek Article & Templates | v1.1 | 4/4 | Complete | 2026-09-27 |
| 9. Draft Persist & Shortlist Enqueue | v1.1 | 4/4 | Complete    | 2026-09-27 |
| 10. CLI Composition & UAT | v1.1 | 5/5 | Complete    | 2026-10-01 |

### Phase 11: Address tech debt: captions diagnostics and persist error classification

**Goal:** Operator CLI diagnostics stay secret-safe and classified correctly: captions/URL envelopes never leak SDK text; out-of-catalog SDK maps to `unknown_captions_error`; persist recognizes `23514` and numeric HTTP statuses without changing `PERSIST_REASONS`; sent-batch re-run returns `already_saved: true` via RPC
**Requirements**: CAP-02, PERS-02, CLI-02, CLI-04 (hardening; already satisfied at milestone level)
**Depends on:** Phase 10
**Plans:** 4/4 plans executed
- [x] 11-01-PLAN.md
- [x] 11-02-PLAN.md
- [x] 11-03-PLAN.md
- [x] 11-04-PLAN.md

**Wave 1**
- [x] `11-01-PLAN.md` — Tracer: captions CookieInvalid → JSON stderr + mapper/adapter locks (CAP-02)
- [x] `11-02-PLAN.md` — Persist classification: `23514` + int HTTP → existing reasons (PERS-02)
- [x] `11-03-PLAN.md` — Decision gate + migration 009 + fake/overflow invert (CLI-02)

**Wave 2**
- [x] `11-04-PLAN.md` — CLI sent-batch checkmarks + `[BLOCKING]` Studio/psql apply 009 (CLI-02, CLI-04)
