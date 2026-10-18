# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1 — MVP

**Shipped:** 2026-09-22
**Phases:** 5 | **Plans:** 40 | **Tasks:** 94

### What Was Built

- Corporate login and self-service `/register` on live Supabase, with FastAPI health, JWT, and FE↔BE proof
- Current issue, prepared-article reader, and archive
- One honest vote: confirm, change while open, closed-cycle rejection, audit-language ballot
- Semantic knowledge search with role filters, plus разборы longread, TOC, and notebook download
- Admin shortlist triage, letter preview with intro and ordered blocks, publish-on-send, and post-send rest

### What Worked

- Ports & Adapters plus Red–Green–Refactor kept domain code free of Supabase and FastAPI
- Gap-closure plans (01-07/01-08, 04-10, 05-07…05-09) closed UAT findings without reopening finished phases
- Mock-first Playwright gates made honesty checks repeatable before live adapters landed

### What Was Inefficient

- Debug sessions stayed `diagnosed` after the fixing plans shipped, so close had to acknowledge them
- Phases 1–3 left Nyquist `VALIDATION.md` in draft, and several live FE↔BE smokes stayed human-gated
- Rank rewrite before `claim_and_publish_digest` is still non-atomic (CR-01)

### Patterns Established

- Admin authorization reads `profiles.role` through `require_admin`, never a JWT role claim
- Successful send publishes an issue and claims `sent_at` before stub mail
- Announcement разборы and the post-send shortlist hide actions that would look available

### Key Lessons

1. When a gap-closure plan ships, mark the debug session resolved in the same change.
2. Treat SMTP (signup confirmation and digest delivery) as an ops milestone, separate from the editorial product path.
3. Keep REQUIREMENTS wording aligned with locked UI decisions (ISSUE-01 still said «cover» after the typography-only hero).

### Cost Observations

- Model mix: not recorded for this milestone
- Commits: 330 from `cabd7eb` (2026-08-23) through `ba8be89` (2026-09-22)
- Notable: timed plans clustered around 7 minutes; a few live-schema plans ran about 45 minutes

---

## Milestone: v1.1 — YouTube → LLM → Supabase ingestion

**Shipped:** 2026-10-02
**Phases:** 6 (6–11) | **Plans:** 23 | **Tasks:** 60

### What Was Built

- Typed `data-collection` ingestion contracts and in-memory port fakes
- YouTube captions + oEmbed adapters with fail-closed stage envelopes
- DeepSeek lecture/podcast article generation (honesty, budget, redacted errors)
- Atomic draft persist + shortlist enqueue (migrations 007–009)
- Typer CLI one-shot with idempotency, staged progress, four-video UAT
- Phase 11 hardening: secret-safe captions diagnostics, persist classify, sent-batch `already_saved`

### What Worked

- Hexagonal boundary: CLI/adapters never mixed `Transcript` with `MaterialDraft`
- Live Studio SQL apply ritual for migrations stayed explicit and blocking
- Phase 11 inserted after audit tech_debt without reopening finished phase DoD

### What Was Inefficient

- Phases 9–10 verification went stale after Phase 11; close used override_closeout
- Nyquist VALIDATION.md for phases 6–8 left draft through milestone close
- Admin UX UAT findings accumulated as follow-ups instead of a planned polish phase

### Patterns Established

- Ingestion writes Supabase only; backend/SPA stay readers
- `IngestError.to_dict()` on stderr; no SDK/proxy secrets in operator JSON
- Conflict-safe persist via RPC `already_saved` + unique `youtube_video_id`

### Key Lessons

1. After a tech-debt insert phase, re-verify prior phases or accept override_closeout explicitly.
2. Park UAT polish (admin preview/email/draft→ready) as the next milestone, not silent debt.
3. Keep Nyquist reconcile (`/gsd-validate-phase`) on the critical path before audit, not after.

### Cost Observations

- Model mix: not recorded for this milestone
- Commits: 218 from `45db99f` (2026-09-26) through `fff73a3` (2026-10-02)
- Notable: Phase 10 live UAT plan spanned ~48h wall clock; Phase 11-04 migration apply ~140min

---

## Milestone: v1.2 — Admin UX + diagnostics + PIPE-01 MVP

**Shipped:** 2026-10-05
**Phases:** 5 (12–16) | **Plans:** 26 | **Tasks:** 56

### What Was Built

- Admin shortlist empty-batch HTTP contract locked (FIX-01 carry from Phase 10)
- Admin material preview honesty: body, provenance, counts, reader link (Phase 13)
- Sandboxed email HTML preview + interstitial paragraph preservation + `test-header` purge (Phase 13)
- Per-row draft → ready promote that clears the D-85 send gate without SQL (Phase 14)
- Honest «Обоснование»: populated `score_factors` or the exact D-15 empty state (Phase 14)
- Secret-safe opt-in CLI `--debug` with byte-identical default contracts (Phase 15)
- PIPE-01 MVP: YAML config view/edit/validate/persist behind a repository port; no execution (Phase 16)

### What Worked

- Server-authoritative validation (strict YAML + Pydantic `extra="forbid"`) kept the SPA free of client YAML rules
- Port + composition-only wiring kept `PipelineConfigRepository` Supabase coupling out of the SPA
- Stale-verification route (#4682) resumed correctly at the tail gates without re-running any plan
- Gap-closure waves (13-07/08, 14-04…14-08, 15-03) absorbed UAT/review findings inside the milestone

### What Was Inefficient

- Phase 16 verification went stale twice: WR-02 fix, then CR-01/IN-01/IN-02 review fixes landed after the verifier ran
- Code review of 16 produced findings only after verification, forcing a re-verify + re-review loop
- `core.autocrlf=true` makes covered-file digests line-ending-sensitive; stat-dirty files add noise to staleness
- 10 artifact items (9 debug sessions + 1 deferred) carried to the close and needed acknowledgement

### Patterns Established

- Verifier covered-digest must be restamped after any post-verification source fix, or the phase reads `stale`
- `_StrictSafeLoader` rejects duplicate keys and unmarked YAML errors as structured 400s (fail-closed, zero writes)
- Advisory code-review findings are backlog items, not blockers — recorded as 999.7 (WR-01)
- `verify:post` capability hooks (nyquist/security/ui) short-circuit cleanly when artifacts already exist and sources are unchanged

### Key Lessons

1. Run code review **before** the phase verifier, or accept a re-verify loop — review fixes invalidate the digest.
2. Pin `eol=lf` in `.gitattributes` for covered source files to stop cross-platform digest churn on Windows checkouts.
3. Close or re-open debug sessions when their fix lands; a clean-named debug file resurfaces at the next close.
4. Advisory review warnings that fail closed belong in ROADMAP Backlog with a rationale, not in the phase DoD.

### Cost Observations

- Model mix: not recorded for this milestone
- Commits: 258 from `c2ca098` (2026-10-02) through `d29e318` (2026-10-05); 237 files, +32475 / −1467
- Notable: Phase 16 required two stale re-verifications; each tail-gate run re-ran nyquist/security/ui hooks

---

## Milestone: v1.3 — Live mail, scheduled ingestion & backlog debt

**Shipped:** 2026-10-18
**Phases:** 8 (17–24) | **Plans:** 28 | **Tasks:** 68

### What Was Built

- YAML merge-key (`<<`) acceptance in the strict validator, bounded against high-fan-out documents, duplicate-key rejection intact (Phase 17)
- Admin-gated draft preview surface (`GET /admin/materials/{slug}`, `no-store`) while the reader route stays ready-only with an opaque 404 (Phase 18)
- Reusable unsaved-changes guard (`useBlocker` + `armBeforeUnload` trio) on `/admin/pipeline`, reused by the ingest-sources editor (Phase 19)
- Signup-confirmation honesty path (B): explicitly autoconfirmed copy that never claims a letter was sent (Phase 20)
- Live SMTP weekly digest to the `profiles` audience with planned-M/delivered-N honesty and contained failures after publish (Phase 21)
- One «Админ» shell entry plus the in-page «Дайджест | Пайплайн» tab-bar; both admin URLs unchanged (Phase 22)
- DB-stored, admin-managed ingest sources validated server-side with zero writes on reject (Phase 23)
- systemd timer driving the `ingest-collect` CLI against enabled sources — drafts + pending shortlist only, never publish/send (Phase 24)

### What Worked

- Backlog-first ordering (999.7 → 999.1 → 999.6) closed accumulated debt before any new feature work
- Honesty framing everywhere (draft ≡ missing, planned/delivered counts, no mail-claim copy) kept every surface truthful
- Gap-closure plans (17-03, 24-07/24-08) absorbed UAT and review findings without reopening finished phases
- Contained-failure design kept publish honest even when mail delivery failed (HTTP 200 with honest N/M)
- Key-free YouTube Atom feed removed the Data API gate with zero new runtime Python packages

### What Was Inefficient

- The milestone close archived phases but left `ROADMAP.md` un-collapsed and `REQUIREMENTS.md` in place; the archival step had to be completed manually afterwards
- A concurrent `github/main` (Concept 2) merge landed at close time and forced conflict resolution in the SPA admin pages
- Phase 24 UAT test 6 (live run against a real enabled source) stayed deferred because `pipeline_ingest_sources` had no row — the timer is proven on a live systemd host but not end-to-end with a real feed
- `17-VALIDATION.md` was left stale and still needs a re-validate pass
- Phase 24 P01 touched 24 files; the plan set grew to 8 plans for one phase

### Patterns Established

- `TimeoutStartSec` (not `RuntimeMaxSec`) bounds a oneshot ingest run; a killed run must not stamp `last_run_at`
- systemd `OnFailure=` alerts read `MONITOR_EXIT_STATUS` so exit 1 and exit 2 stay distinguishable in journald
- The server is the authority for canonical ingest-source ids; the UI only states where to obtain them
- An admin preview surface serves a draft with the reader DTO verbatim (`no-store`, empty `related`/`tags`, no `status`)
- Mail stays best-effort **after** publish; mailer errors are caught alongside `PersistenceError`

### Key Lessons

1. Collapse `ROADMAP.md` and delete `REQUIREMENTS.md` in the same close pass — a later merge can silently restore them.
2. Land concurrent-branch merges before the close, not during it; planning files are the conflict-prone surface.
3. Prove a scheduler on a live host **and** with a real enabled source row; host-level proof alone leaves an end-to-end gap.
4. Invert text contracts (the `TimeoutStartSec` fix) so the broken token cannot silently return.
5. Re-validate a phase whose `VALIDATION.md` was written before gap-closure plans landed.

### Cost Observations

- Model mix: not recorded for this milestone
- Notable: 8 phases / 28 plans shipped 2026-10-14 → 2026-10-18; Phase 24 carried the largest plan set (8 plans)

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1 | not recorded | 5 | First close. Gap-closure plans and mock Playwright gates became the default. |
| v1.1 | not recorded | 6 | Separate ingestion CLI + RPC persist; audit tech_debt closed via inserted Phase 11. |
| v1.2 | not recorded | 5 | Capability hooks (nyquist/security/ui) on the execute tail; stale re-verification route; code review moved ahead of nothing → still after the verifier. |
| v1.3 | not recorded | 8 | Backlog-debt-first ordering; admin preview honesty surface; DB-backed ingest sources + systemd scheduled collection. Close must collapse ROADMAP.md and delete REQUIREMENTS.md in one pass. |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1 | pytest + Playwright per phase | not measured | Ports & Adapters layout kept |
| v1.1 | pytest unit + CliRunner + SQL contract tests; manual CLI-03 UAT | not measured | `ingestion-service` + DeepSeek adapter |
| v1.2 | 761 pytest unit + 50 Playwright admin + node source locks; 49/49 verifier truths | not measured | PIPE-01 config port; debug `StageDiagnostics`/`Clock` ports; strict YAML validator |
| v1.3 | 227 pytest unit + 17 Playwright (Phase 24 gate); `nyquist_compliant: true`, 0 gaps, 3 manual-only escalations | not measured | systemd ingest timer + `ingest-collect` CLI slice; admin draft preview surface; `IngestSourceRepository`/schedule ports; live SMTP mailer |

### Top Lessons (Verified Across Milestones)

1. Close the debug file when the fix lands, or the next milestone close will surface it again.
2. Live mail and signup SMTP are separate from the product requirements that shipped in v1.
3. Inserted tech-debt phases need explicit re-verify of prior VERIFICATION.md or documented override.
4. Order the tail gates review-before-verify: any source fix after the verifier stales the covered digest (#4682).
5. Pin line endings (`eol=lf`) on covered files so the fingerprint stays stable across Windows/Linux checkouts.
6. A milestone close will resurface every un-closed debug session; close them when their fix lands.
7. Collapse `ROADMAP.md` and delete `REQUIREMENTS.md` in the same close pass — a later merge can silently restore them.
8. Prove schedulers on a live host **and** with a real enabled source row; host-level proof alone leaves an end-to-end gap.
