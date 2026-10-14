---
gsd_state_version: "1.0"
milestone: v1.3
milestone_name: Live mail, scheduled ingestion & backlog debt
status: planning
last_updated: "2026-10-14T08:59:51.362Z"
last_activity: 2026-10-14
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-14 — after v1.3 milestone start)

**Core value:** Trusted weekly prepared-article issue + one honest vote toward the next разбор
**Current focus:** v1.3 — Live mail, scheduled ingestion & backlog debt (defining requirements)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-10-14 — Milestone v1.3 started

## Performance Metrics

**Velocity:**

- Total plans completed: 26 (40 v1 + 23 v1.1)
- v1.2 plans completed: 19
- Prior milestone velocity: see MILESTONES.md / archived STATE

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1–5 (v1 shipped) | 40/40 | complete | see MILESTONES |
| 6–11 (v1.1 shipped) | 23/23 | complete | see MILESTONES |
| 12. Empty-batch contract | 3/3 | complete | see per-plan |
| 13. Preview honesty | 0/? | not started | - |
| 14. Draft→ready & justification | 0/? | not started | - |
| 15. CLI --debug | 3/3 | complete | see per-plan |
| 16. PIPE-01 MVP UI | 0/? | not started | - |
| 13 | 8 | - | - |
| 12 | 3 | - | - |
| 14 | 8 | - | - |
| 15 | 3 | - | - |
| 16 | 4 | - | - |
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 12 P01 | 2min | 2 tasks | 1 files |
| Phase 12 P02 | 5min | 2 tasks | 4 files |
| Phase 12-03 P03 | 6min | 2 tasks | 2 files |
| Phase 13 P01 | 7min | 2 tasks | 7 files |
| Phase 13 P02 | 8min | 3 tasks | 8 files |
| Phase 13 P03 | 5min | 2 tasks | 3 files |
| Phase 13 P06 | 12min | 2 tasks | 6 files |
| Phase 13 P04 | 7min | 2 tasks | 3 files |
| Phase 13 P05 | 45min | 3 tasks | 6 files |
| Phase 13 P07 | 11min | 2 tasks | 5 files |
| Phase 13 P08 | 9min | 2 tasks | 3 files |
| Phase 14 P01 | 5min | 2 tasks | 8 files |
| Phase 14 P02 | 4min | 2 tasks | 6 files |
| Phase 14 P03 | 16min | 3 tasks | 7 files |
| Phase 14 P06 | 6min | 1 tasks | 2 files |
| Phase 14 P07 | 5min | 1 tasks | 3 files |
| Phase 14 P08 | 5min | 1 tasks | 2 files |
| Phase 15 P01 | 10min | 3 tasks | 10 files |
| Phase 15 P02 | 8 min | 3 tasks | 5 files |
| Phase 15 P03 | 8min | 3 tasks | 3 files |
| Phase 16 P01 | 5 min | 2 tasks | 10 files |
| Phase 16 P02 | 6min | 2 tasks | 12 files |
| Phase 16 P04 | 20min | 2 tasks | 6 files |
| Phase 16 P03 | 30min | 3 tasks | 9 files |

## Accumulated Context

### Decisions

Full decision log: `.planning/PROJECT.md` (Key Decisions and `<decisions>`).

v1.2 roadmap locks:

- Phases 12–16 only; continuous numbering after v1.1 Phase 11
- PIPE-01 MVP = config + validation + UI; execution → v1.3
- Live SMTP (MAIL-01) and signup confirmation mail (MAIL-02) deferred to v1.3
- ADUX preview cluster (13) before draft→ready / score_factors (14)
- [Phase 12]: D-03: no production edits — empty-unsent already returned D-04 #2 via get_admin_shortlist
- [Phase 12]: Both empty proofs use required-key asserts (D-08); AdminShortlistResponse keeps extra=forbid (D-09)
- [Phase 12]: D-10 lock tables mirror D-04 #1/#2; digest_rest called out as third non-empty shape (G-05-2)
- [Phase 12]: REQUIREMENTS FIX-01 rephrased per RESEARCH Q2: no-batch + empty-unsent under required-key asserts
- [Phase 12]: D-13: no AdminDigestPage chrome — empty-unsent reuses D-80 empty UI
- [Phase 12]: Playwright RED authorized emptyUnsentDto GREEN (RED_EVIDENCE_OK)
- [Phase 13]: Counts computed in get_admin_shortlist from body_markdown; reading_minutes from stored join
- [Phase 13]: Enrich shortlist via get_current_batch join only — no /admin/materials/:id (D-01)
- [Phase 13]: render_email_html blocks as kind maps; site_url defaults until Plan 06; ban assert-only
- [Phase 13]: AdminItemPreview uses MaterialPage markdown stack; no fetch-on-open (D-01/D-04)
- [Phase 13]: Counts always shown (incl. zeros); provenance omitted when empty (D-05/D-06)
- [Phase 13]: Reuse preview _html_content_blocks in send_digest; no second HTML builder
- [Phase 13]: Optional Mailer body_html + StubMailer.last_body_html additive (A4)
- [Phase 13]: Email honesty is sandboxed iframe srcDoc only; no FE HTML assembly or dangerouslySetInnerHTML
- [Phase 13]: Interstitial paragraph hint under both intro and connecting-text (UI-SPEC E3)
- [Phase 13]: D-20 apply-after-sql: ship 010 + runbook section 4g, operator applies via Studio SQL (postgres); do not defer live scrub
- [Phase 13]: D-20 apply-after-sql completed: 010 applied 2026-10-03 Studio SQL (postgres); PostgREST title probe empty; criterion 4 live honesty claimable
- [Phase 13]: Runbook scrub section is §4g (plan text said §4f; §4f already used for admin shortlist/send E2E)
- [Phase 13]: Preview close stays visible because the header row is outside overflow-y-auto, with cursor-pointer on Закрыть
- [Phase 13]: Long-body mock repeats one sentence forty times only inside fetchShortlist useMocks
- [Phase 13]: Email success branch renders subject and email-preview-frame only; the preview.items ul is not mounted
- [Phase 13]: Close-scroll viewport is 1280x400 so overflow comes from the subject plus the iframe after the items list is gone
- [Phase 14]: Triage ready uses with_ready_status — never publish_material/as_ready/index (D-06)
- [Phase 14]: Single ready route is body-less; MarkReadyResponse extra=forbid (D-07/D-10)
- [Phase 14]: In-memory shortlist overlays material_status for send-bridge fidelity
- [Phase 14]: Batch ready uses HTTP 200 partial success results[] (D-08); never 207/FE-loop
- [Phase 14]: D-02 Approve≠ready locked via asserts + AST import guard
- [Phase 14]: Mock DEFAULT_ITEMS seed owned by getMockDefaultItems (material 104 empty factor_labels)
- [Phase 14]: Batch mock call counter on harness for D-08 Playwright proof
- [Phase 14]: Empty Обоснование is exact D-15 sentence; populated join unchanged
- [Phase 15]: Sink stays typer-free: cli.py injects typer.echo(err=True) as emitter; adapter falls back to sys.stderr
- [Phase 15]: Redaction order: SecretRegistry.mask -> DENY_PATTERNS -> control-char strip -> length cap; Bearer before assignment pattern
- [Phase 15]: Captions stage emits domain token 'captions' for 1:1 correlation with IngestError.stage
- [Phase 15]: Metadata debug line emits only video_id; failed-stage lines emit reason/exit_code/elapsed_ms and never IngestError.message or context — D-06/D-08/T-15-04: minimize disclosure while the JSON envelope keeps the allowlisted context
- [Phase 15]: Each mapping except-block emits stage_failed from the mapped IngestError's stage/reason/exit_code so debug lines correlate 1:1 with the JSON envelope; url/consistency failures report elapsed_ms=0 — D-10/D-11/RESEARCH Pattern 4/T-15-05: attribute failures without altering the envelope or exit code
- [Phase 15]: RecordingDiagnostics call-spy added to tests_support/fakes.py and used for pipeline event-order plus CLI failure assertions — RED-first TDD: the use-case test double records ordered stage events without coupling to the stderr sink
- [Phase 15]: Gap closure (15-03): assignment denylist now uses a non-word left boundary `(?<![A-Za-z0-9_])` with compound alternatives (access_token/refresh_token/client_secret/secret_key/private_key/auth) before the bare secret/token and NO trailing `\b`, so underscore-compound credentials mask to [redacted]; the control-character strip runs once before the token patterns — T-15-07/T-15-08 close the verifier's single blocker without touching the allowlist, SecretRegistry, sink, use-case, CLI flags, or stdout contract
- [Phase 16]: 16-01 attaches pipeline_config fakes post-build; AppContainer field declaration + build_in_memory_container wiring are 16-02's slice
- [Phase 16]: 16-01 defers the PUT PipelineConfigValidationError reject branch (structured 400 {errors:[...]}) to 16-02 behind the same validator port; tracer proves the happy path only
- [Phase 16]: 16-01 mock config persists to sessionStorage so a page reload re-reads the saved YAML (PIPE-03 round-trip proof without a reload control)
- [Phase 16]: 16-01 names the service mock cutover helper mocksEnabled (not useMocks) to avoid new react-hooks lint false positives
- [Phase 16]: Locked pipeline config schema keys {template, roles, language, max_chars}; template/role Literals defined locally in backend (no data-collection import) (16-02)
- [Phase 16]: PUT /admin/pipeline/config reject returns top-level JSONResponse(400, {errors:[...]}) with zero writes; never HTTPException detail nesting (16-02, D-05)
- [Phase 16]: MAX_PIPELINE_CONFIG_CHARS=20000 cap checked before parse; strict _StrictSafeLoader rejects duplicate keys (16-02, T-16-07/T-16-09)
- [Phase 16]: Rule 2 deviation: added PUT to CORS allow_methods so the live browser preflight reaches the reject path (16-02, RESEARCH Pitfall 1)
- [Phase 16]: AppContainer.pipeline_config/pipeline_config_validator declared with None defaults; build_in_memory_container wires the real YamlPipelineConfigValidator + InMemoryPipelineConfigRepository (16-02)
- [Phase 16]: 16-04 harness arms live in sessionStorage so armFailNextLoad survives page.reload(); save arms consume once so retry can succeed
- [Phase 16]: 16-04 page performs no client YAML validation: only a server INVALID_CONFIG reject opens the panel and keeps the document dirty (D-03/D-07)
- [Phase 16]: 16-04 aria-invalid is driven by the rejected flag so a reject with no structured errors still marks the editor
- [Phase 16]: 16-04 exposed window.__DIGEST_PIPELINE_CONFIG_HARNESS__ in Task 1 (plan scheduled it for Task 2) so Task 1 Playwright verify could pass
- [Phase 16]: 16-03: singleton pipeline_config (id=1) with RLS enabled and no permissive policy; only the service_role composition adapter reaches it (D-08, T-16-10)
- [Phase 16]: 16-03: migration 011 applied on shared knowledge-db VM 2026-10-04; read-only PostgREST probe returned [] (0 rows under RLS deny-by-default) — PIPE-03 live DoD satisfied
- [Phase 16]: UAT complete 4/4 (live round-trip operator-confirmed; 7 visual backstops auto-verified at 1280/480; unsaved-guard accepted; deep-nesting fixed). WR-02 fixed in commit 758ddac — yaml.load RecursionError mapped to a structured 400 {errors:[...]} instead of a 500; verifier re-run passed 49/49.
- [Phase 16]: Deferred to ROADMAP backlog — 999.5 admin nav grouping (option C tab-bar; top-level «Пайплайн» removed) and 999.6 unsaved-changes guard (WR-04/WR-05). Optional UX, not SC; DB safe (no save → no write).

### Pending Todos

None. Phase 13 plans 01–08 are complete and ready for verification.

### Blockers/Concerns

Signup confirmation mail (`g-01-3b-signup-mailer`) carried from v1 into v1.3 as MAIL-02 — root cause still unknown, the phase opens with investigation.
Nyquist VALIDATION.md drafts for phases 6–8 remain historical debt (not a v1.2 product requirement).
[Phase 16] Backlog 999.5 (admin nav grouping) and 999.6 (WR-04/WR-05 unsaved-changes guard) — 999.6 is scheduled for v1.3; 999.5 stays deferred optional UX.
[Phase 16] Open advisory review warnings (16-REVIEW.md, post stale re-verification): WR-01 (valid YAML merge-key `<<` rejected with a cryptic internal-tag message in `_StrictSafeLoader.construct_mapping` — fails closed, still a structured 400) scheduled for v1.3 as 999.7; plus IN-01/IN-02/IN-03 — non-blocking, no must-have impact; verifier passed 49/49.

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| deferred_items | 10/deferred-items.md: pre-existing test_admin_shortlist_empty_batch failure → FIX-01 / Phase 12 | in_roadmap | 2026-10-02 | v1.1→v1.2 |
| debug_sessions | (4 items from v1 close — see MILESTONES.md) | acknowledged | 2026-09-22 | v1 |
| debug_sessions | admin-batch-cta-removal | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| debug_sessions | draft-approved-contradiction | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| debug_sessions | email-plain-body-rendered | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| debug_sessions | footer-duplicates-cta-label | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| debug_sessions | interstitial-not-paragraph | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| debug_sessions | mark-ready-503 | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| debug_sessions | modal-close-not-sticky | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| debug_sessions | per-row-ready-click-noop | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| debug_sessions | preview-cursor | resolved 2026-10-13 | 2026-10-05 | v1.2 |
| deferred_items | 13/deferred-items.md: admin.spec.js `/me network failure shows ServiceUnavailable not Forbidden` flake (pre-existing, not G-13-*) | acknowledged | 2026-10-05 | v1.2 |

Carried product deferrals beyond v1.3: leaderboard, quiz, Whisper/Foundry ASR, ingest HTTP API, auto-publish/send, PIPE execution.

## Session Continuity

Last session: 2026-10-14T08:59:51.362Z
Stopped at: Milestone v1.3 started — backlog debt first (999.1, 999.6, 999.7), then mail and scheduled ingestion
Resume file: None
Next: define v1.3 requirements and create the roadmap (backlog debt → MAIL-02 → MAIL-01 → scheduled ingestion)

## Operator Next Steps

- Finish scoping v1.3 (requirements + roadmap), then start Phase 17 with /gsd-discuss-phase 17
