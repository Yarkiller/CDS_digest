# Requirements: Digest CDS

**Defined:** 2026-10-14
**Core Value:** Authorized СВА staff can read a trustworthy weekly issue of prepared articles and influence the next разбор through one honest vote — without treating raw video/transcript as published material.

**Milestone:** v1.3 Live mail, scheduled ingestion & backlog debt

## v1.3 Requirements

Requirements for this milestone. Each maps to roadmap phases.

Ordering rule: **backlog tech debt first** (999.7 → 999.1 → 999.6), then mail, then ingest sources and scheduling.

### Reader honesty for draft materials (backlog 999.1)

- [x] **ADUX-07**: Admin can open any material (draft or ready) at an admin-gated preview and read it in the normal reader rendering; the public `GET /materials/{slug}` stays ready-only and an unknown **or draft** slug returns an opaque 404 (never 403)
- [x] **ADUX-08**: The admin shortlist and email-preview links target the admin preview surface; a draft preview is served non-cacheable (`no-store`) and carries a visible preview marker, exposing no `related`/`tags` of unpublished material

### Unsaved-changes guard for the pipeline editor (backlog 999.6)

- [x] **ADUX-09**: The admin pipeline editor warns before losing unsaved changes on in-app SPA navigation **and** on reload/close, using the existing Russian copy; no warning when clean; the dirty flag clears after a successful save and stays armed after a server reject
- [x] **ADUX-10**: The guard covers every editable surface on `/admin/pipeline`, including the ingest-sources editor shipped in the sources phase

### Pipeline config validator (backlog 999.7)

- [x] **PIPE-04**: The strict pipeline-config validator accepts a valid YAML merge-key (`<<`) document and persists it, while still rejecting duplicate **explicit** keys with the same top-level structured 400 `{errors:[…]}` and zero writes
- [x] **PIPE-05**: Merge expansion is bounded so a small document cannot exhaust CPU (breach returns the structured 400), and duplicate-key rejection is provably not weakened

### Mail

- [x] **MAIL-02**: The signup-confirmation root cause is diagnosed and documented, and the delivered end state is honest — either a working confirmation email through the corporate relay, or an explicitly autoconfirmed flow whose copy never claims that mail was sent
- [x] **MAIL-01**: The weekly digest is delivered by a real SMTP mailer in place of `StubMailer`, to the audience derived from `profiles`; mail stays best-effort **after** publish — a mail failure never converts an already-published digest into a failed send (CR-02/D-88)
- [x] **MAIL-03**: `recipient_count` is honest — both the planned `profiles` audience size and the actually delivered count are recorded, and the response reports them (e.g. «доставлено N из M»); the copy never claims the whole organisation
- [x] **MAIL-04**: Mailer failures are contained — SMTP exceptions (`SMTPException`/`OSError`/timeout) map to a domain error caught alongside `PersistenceError`, with bounded timeouts, so a published digest is not 500-ed
- [x] **MAIL-05**: SMTP configuration (`SMTP_*`) is read only from the VM environment through `settings`/composition; no `os.environ` in adapters and no secret in app code

### Ingest sources (admin-managed)

- [x] **SRC-01**: An admin can list, add, enable/disable, and remove ingest sources (YouTube channel or playlist) on the pipeline page, and the list is stored in the database
- [x] **SRC-02**: The source API validates the canonical source id server-side and rejects anything else with a top-level structured 400 `{errors:[…]}` and zero writes; the UI states where to obtain the id
- [x] **SRC-03**: Sources are read/written through an `IngestSourceRepository` port wired in composition; the SPA reaches them only through a service module (no deep Supabase coupling)

### Admin nav grouping (backlog 999.5)

- [x] **ADUX-12**: The pipeline config surface is reached from the admin area rather than a second top-level nav item — one «Админ» entry (→ `/admin/digest`) plus an in-page tab-bar «Дайджест | Пайплайн»; the `/admin/pipeline` route is unchanged and no new route is added

### Scheduled ingestion

- [ ] **ING-02**: A scheduled run enumerates new videos for each **enabled** source and ingests them through the existing pipeline, writing **drafts + pending shortlist rows only** — never publishing or sending
- [ ] **ING-05**: A per-source high-water mark prevents re-processing already-ingested videos, so a re-run is safe and does not re-pay caption/LLM cost
- [ ] **ING-06**: The schedule runs unattended from a systemd timer with the environment it needs; each run's outcome is visible, and one bad video does not abort the batch
- [ ] **ING-07**: The scheduled path is provably unable to reach publish/send, and the existing `ingest <url>` CLI stdout contract stays byte-identical

## v2+ Requirements

Deferred. Not in this milestone's roadmap.

### Pipeline execution

- **PIPE-EXEC-01**: Full pipeline execution driven by the saved PIPE-01 config (run/trigger from admin or scheduler)
- **PIPE-EXEC-02**: Config-driven `score_factors` population during ingest

### Ingestion follow-ups

- **ING-01**: HTTP API to trigger ingestion (no CLI-only)
- **ING-03**: Transcription when captions are missing (FoundryModels revisit; not Whisper-on-VM)
- **ING-04**: Transcript chunking when content exceeds the context budget
- **ING-08**: Non-YouTube ingest sources / allowlist UI beyond channel and playlist

### Mail follow-ups

- **MAIL-06**: Unsubscribe / recipient preference management
- **MAIL-07**: Per-recipient personalization and a persisted per-recipient delivery summary

### Backlog product preferences (parked)

- **ADUX-11**: Unify `Approve` (decision) + `Mark ready` (`material_status`) into one editorial action (backlog 999.4)

### Deferred product

- **LEAD-01**: Public leaderboard (ADR-0001)
- **QUIZ-01**: Quiz cards

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-publish / auto-send of the digest | Editorial trust; the scheduler writes drafts only, sending stays an explicit admin action (D-85/D-88) |
| Ingestion HTTP API (ING-01) | The scheduler drives the existing CLI; no new HTTP surface in v1.3 |
| PIPE full pipeline execution | Deferred past v1.3 — v1.2 shipped config + validation + UI only |
| Whisper / local ASR on the app VM | ADR-0002; captions-only until a Foundry revisit |
| Resolving `@handle` / free-form channel URLs to a canonical id | Needs fragile scraping or an API key (re-opens the ADR-0002 gate); v1.3 requires the canonical id and rejects the rest |
| YouTube Data API v3 | A new public external dependency; the key-free Atom feed covers the weekly window, so no ADR-0002 exception is needed |
| Widening `GET /materials/{slug}` for drafts | Would publish unpublished content to every authenticated reader and collapse "draft ≡ missing" |
| Backlog 999.4 | Product preference, not debt — parked (ADUX-11) |
| Dynamic admin-managed email domain list | ADR-0003 — fixed two domains only |
| Nyquist reconcile of archived phases 6–8 | Historical audit debt; not a product requirement |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIPE-04 | Phase 17 | Complete |
| PIPE-05 | Phase 17 | Complete |
| ADUX-07 | Phase 18 | Complete |
| ADUX-08 | Phase 18 | Complete |
| ADUX-09 | Phase 19 | Complete |
| ADUX-10 | Phase 23 | Complete |
| ADUX-12 | Phase 22 | Complete |
| MAIL-02 | Phase 20 | Complete |
| MAIL-01 | Phase 21 | Complete |
| MAIL-03 | Phase 21 | Complete |
| MAIL-04 | Phase 21 | Complete |
| MAIL-05 | Phase 21 | Complete |
| SRC-01 | Phase 23 | Complete |
| SRC-02 | Phase 23 | Complete |
| SRC-03 | Phase 23 | Complete |
| ING-02 | Phase 24 | Pending |
| ING-05 | Phase 24 | Pending |
| ING-06 | Phase 24 | Pending |
| ING-07 | Phase 24 | Pending |

**Coverage:**
- v1.3 requirements: 19 total
- Mapped to phases: 19 — every v1.3 requirement maps to exactly one phase (Phase 17–24)
- Orphans: 0 — no v1.3 requirement is unmapped; deferred items are listed under v2+ / Out of Scope

**Notes:**
- ADUX-10 is owned by Phase 23 (ingest sources), not Phase 19 — recorded explicitly in both phases so the coverage gap is deliberate, not forgotten.
- Backlog 999.7 → Phase 17 · 999.1 → Phase 18 · 999.6 → Phase 19 · 999.5 → Phase 22; 999.4 stays parked.

---
*Requirements defined: 2026-10-14*
*Last updated: 2026-10-14 after v1.3 roadmap creation (Phases 17–24)*
