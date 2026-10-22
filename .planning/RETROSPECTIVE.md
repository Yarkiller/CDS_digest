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

## Milestone: v1.4 — UI polish & honest navigation

**Shipped:** 2026-10-22
**Phases:** 4 (25–28) | **Plans:** 19 | **Tasks:** 35

### What Was Built

- Admin «Настройка» naming on the tab, the sr-only heading and the mobile select, `/admin/pipeline` unchanged; «Админ» eyebrow removed; ingest block «Источники»; backlog 999.2 chrome polish folded in (Phase 25)
- The semantic token family declared in `@theme` and enforced by 22 static gates (`G-0`…`G-21`), each with a mutation proof — the root fix for the invisible `paper/ink/rule` utilities (Phase 25)
- WCAG 1.4.11 field boundaries (`--color-field-border`) on every control, and theme-independent labels on every fill (Phase 25)
- Anchor landing clear of the sticky header via one `scroll-padding-top` plus a measured mobile token; section context carried in `history.state.usr.section` (Phase 26)
- Header search that executes on the first Enter — one request per submission, zero for an empty query, Back restored at Δ=0 from a memory-only cache (Phase 27)
- Live proof of the streamed DeepSeek ingest: 24.14-minute video → material 25 `draft` + shortlist `batch 7 / rank 2 / pending`, exit 0 in 21.91 s (Phase 28)
- Closeout debt closed under TDD: WR-11 radio boundary, WR-12 failure-banner tone, NAV-01 640–959.98px header band

### What Worked

- Turning each UI defect into a computed-style or request-count assertion made "looks fixed" checkable — every RED named the number that had to move
- Coding the readability rules as static gates with proof tests (G-14 tint alpha read from the class, G-16 reading behaviour not file text, G-17 with a text-pinned sanction) closed the class of defect rather than the instance
- The integration check caught a real cross-phase drift (Phase 25's loading-chrome pin vs Phase 27's single-source contract) that both phase reports had declared green
- The empty-submit rider (`FU-27-01`) was closed in Phase 28 under TDD, which closed its threat `T-27-16` as a side effect
- Reading the ingest proof back from the DB by `youtube_video_id` rather than trusting `✓ saved` made an idempotent re-run impossible to mistake for a success

### What Was Inefficient

- The audit's "215 passed" claim needed a full re-run to trust; the stale Phase 25 pin had been overriding a deliberate Phase 27 contract for two phases
- WR-11 needed a gate-contract decision (a `role="radio"` indicator is not an `<input>`), which the audit had recorded as "needs a semantic decision" and deferred twice — the fix itself was two lines
- The 640–959.98px header band was measured but never declared in a must-have, so it survived a full navigation phase as a WARNING
- Three `VALIDATION.md` drafts (25–27) are still unreconciled; phase 28 has none
- The live ingest proof stays operator-dependent (`YOUTUBE_PROXY_URL` + a connected VPN container), so the milestone's most "live" criterion is the least CI-reproducible

### Patterns Established

- A readability gate may sanction a non-`<input>` control boundary only by exact literal, with a proof that every other literal in the same file still offends
- Semantic colour for an outcome is a tone carried by state, never a substring match on the message text
- A responsive header's height belongs in `--header-height` per band; `scroll-padding-top` then needs no second source
- An ARIA control whose visual indicator is a span inherits the control-boundary role in the token vocabulary, not the decorative one

### Key Lessons

1. A green suite is only evidence if every pin points at a live contract — re-run the full suite before believing a phase report.
2. When a defect needs "a semantic decision", make the decision in the gate's vocabulary; otherwise it defers forever.
3. Declare the responsive band you measured; an undeclared band becomes nobody's requirement.
4. Fixing the README-level colour is not the same as fixing the outcome semantics — the banner needed a tone, not a different token.
5. Close debt before the archive commit, so the milestone's own record describes what actually shipped.

### Cost Observations

- Model mix: not recorded for this milestone
- Notable: 4 phases / 19 plans in 2 days (2026-10-21 → 2026-10-22); 146 commits, 115 files (+21 249 / −202); gates ended at 218 Playwright / 112 static / 1 156 pytest

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1 | not recorded | 5 | First close. Gap-closure plans and mock Playwright gates became the default. |
| v1.1 | not recorded | 6 | Separate ingestion CLI + RPC persist; audit tech_debt closed via inserted Phase 11. |
| v1.2 | not recorded | 5 | Capability hooks (nyquist/security/ui) on the execute tail; stale re-verification route; code review moved ahead of nothing → still after the verifier. |
| v1.3 | not recorded | 8 | Backlog-debt-first ordering; admin preview honesty surface; DB-backed ingest sources + systemd scheduled collection. Close must collapse ROADMAP.md and delete REQUIREMENTS.md in one pass. |
| v1.4 | not recorded | 4 | Static token gates with mutation proofs replaced one-off contrast fixes; closeout debt settled before the archive commit; integration check caught a two-phase contract drift. |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1 | pytest + Playwright per phase | not measured | Ports & Adapters layout kept |
| v1.1 | pytest unit + CliRunner + SQL contract tests; manual CLI-03 UAT | not measured | `ingestion-service` + DeepSeek adapter |
| v1.2 | 761 pytest unit + 50 Playwright admin + node source locks; 49/49 verifier truths | not measured | PIPE-01 config port; debug `StageDiagnostics`/`Clock` ports; strict YAML validator |
| v1.3 | 227 pytest unit + 17 Playwright (Phase 24 gate); `nyquist_compliant: true`, 0 gaps, 3 manual-only escalations | not measured | systemd ingest timer + `ingest-collect` CLI slice; admin draft preview surface; `IngestSourceRepository`/schedule ports; live SMTP mailer |
| v1.4 | 1 156 pytest + 218 Playwright web + 112 static gates (`G-0`…`G-21`); full suite re-run at close | not measured | semantic token family + 22 mutation-proven gates; `scroll-padding-top` band tokens; `history.state` section marker; live streamed-ingest proof |

### Top Lessons (Verified Across Milestones)

1. Close the debug file when the fix lands, or the next milestone close will surface it again.
2. Live mail and signup SMTP are separate from the product requirements that shipped in v1.
3. Inserted tech-debt phases need explicit re-verify of prior VERIFICATION.md or documented override.
4. Order the tail gates review-before-verify: any source fix after the verifier stales the covered digest (#4682).
5. Pin line endings (`eol=lf`) on covered files so the fingerprint stays stable across Windows/Linux checkouts.
6. A milestone close will resurface every un-closed debug session; close them when their fix lands.
7. Collapse `ROADMAP.md` and delete `REQUIREMENTS.md` in the same close pass — a later merge can silently restore them.
8. Prove schedulers on a live host **and** with a real enabled source row; host-level proof alone leaves an end-to-end gap.
9. Re-run the full suite before believing a phase report — a stale pin can hold a deliberate contract hostage for two phases.
10. A defect deferred as "needs a semantic decision" is a decision about the gate's vocabulary; make it there, or it defers forever.
