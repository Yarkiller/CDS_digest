---
gsd_state_version: "1.0"
milestone: v1.3
milestone_name: Live mail, scheduled ingestion & backlog debt
current_phase: 17
current_phase_name: YAML merge-key acceptance in the strict validator
status: executing
stopped_at: Phase 20 context gathered
last_updated: "2026-10-14T13:19:00.359Z"
last_activity: 2026-10-14
last_activity_desc: Phase 17 execution started
state_head: 43f76a75e78b58f423399715ab5a8633ae8caf9a
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 3
  completed_plans: 2
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-14 — after v1.3 milestone start)

**Core value:** Trusted weekly prepared-article issue + one honest vote toward the next разбор
**Current focus:** Phase 17 — YAML merge-key acceptance in the strict validator

## Current Position

Phase: 17 (YAML merge-key acceptance in the strict validator) — GAP CLOSURE PENDING
Plan: 2 of 3 (17-01, 17-02 done; 17-03 gap plan ready)
Status: Verification found a gap (13/14) — CR-01 duplicate keys inside a merge source; execute `17-03`
Last activity: 2026-10-14 — Phase 20 context gathered

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 26 (40 v1 + 23 v1.1 + 26 v1.2)
- Prior milestones shipped: v1 (5 phases), v1.1 (6 phases), v1.2 (5 phases)
- v1.3 plans completed: 0

**By Phase (v1.3):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 17. YAML merge-key | 2/3 | gap closure pending (17-03) | - |
| 18. Reader-route honesty | 0/? | context gathered | - |
| 19. Unsaved-changes guard | 0/? | not started | - |
| 20. Signup mail (MAIL-02) | 0/? | context gathered | - |
| 21. Live SMTP digest (MAIL-01) | 0/? | not started | - |
| 22. Admin nav grouping | 0/? | not started | - |
| 23. Ingest sources | 0/? | not started | - |
| 24. Scheduled ingestion | 0/? | not started | - |
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 17 P01 | 9min | 2 tasks | 3 files |
| Phase 17 P02 | 7min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Full decision log: `.planning/PROJECT.md` (Key Decisions and `<decisions>`).

v1.3 roadmap locks:

- Order: backlog debt first (999.7 → 999.1 → 999.6), then MAIL-02 → MAIL-01, then 999.5 (own phase), then ingest sources, then scheduler
- Scheduled ingestion split from the sources work into two phases (sources = migration + API + UI; scheduler = adapter + CLI + timer)
- Phase 17 (999.7): merge fix and the merge-expansion CPU bound ship in the SAME phase; duplicate-key rejection must not weaken
- Phase 18 (999.1): `GET /materials/{slug}` + `get_material_for_reader` stay ready-only; draft ≡ missing ≡ opaque 404 (never 403); `no-store`; no unpublished `related`/`tags`
- Phase 19 (999.6): data-router migration of `App.jsx` is its own behaviour-preserving plan (full Playwright green) — never combined with the guard; ADUX-10 is NOT here
- Phase 20 (MAIL-02): GoTrue/Supabase Auth owns signup mail — routing it through the backend `Mailer` port is an anti-feature
- Phase 21 (MAIL-01): honesty (recipients from `profiles` + honest count) lands and is testable WITH THE STUB before the real SMTP adapter; mailer errors caught alongside `PersistenceError` so a published digest is never 500-ed (D-88)
- Phase 22 (999.5): one «Админ» top-level entry + in-page tab-bar «Дайджест | Пайплайн»; `/admin/pipeline` unchanged, no new route; 16-UI-SPEC A-2 must be updated
- Phase 23 (SRC): `IngestSourceRepository` port wired only in composition; server-side canonical-id validation → structured 400 with zero writes; ADUX-10 owned here
- Phase 24 (ING): key-free YouTube Atom feed chosen → **ADR-0002 gate removed**, no Data API spike; `google-api-python-client` and `yt-dlp` rejected; zero new runtime Python packages
- [Phase 17]: Merge-key fix and the expansion bound ship in the same diff (D-04): _project bounds (entries, depth) memoised at the head of flatten_mapping, before the k^depth node multiplication
- [Phase 17]: Merge-introduced collisions are override semantics, not errors (D-03): an explicit own key beats a merged one and the first merge source wins; pinned by yaml.SafeLoader oracle equality rather than hand-written cases
- [Phase 17]: Skip the merge key by tag tag:yaml.org,2002:merge, never by the literal << — a quoted << is an ordinary string key (D-02); the duplicate scan reads the pristine pre-merge own-key snapshot
- [Phase 17]: The merge bound raises a plain Exception (not a ConstructorError) so the reject row keeps the sibling {path: "", message: ...} shape with no line, never reusing _OVER_CAP_MESSAGE (D-06/D-09)
- [Phase 17]: The D-07 row keeps the loc-derived path (defaults) and only the message changes, so its field identity matches every other extra_forbidden row (A2)
- [Phase 17]: The anchor-holder translation is gated on composed-graph anchor identity, so a genuine unknown key keeps Pydantic's English extra_forbidden message and the D-09 tripwire stays byte-identical (Pitfall 9)
- [Phase 17]: _anchor_holder_keys is guarded (yaml.YAMLError/RecursionError -> empty set), runs only on the reject path when an extra_forbidden row exists, and reads the allow-list from PipelineConfigModel.model_fields (D-05, A5)

### Pending Todos

None.

### Blockers/Concerns

- **SMTP relay (Phase 20/21)** — the corporate relay **choice and configuration shape** are now recorded (Phase 20 CONTEXT: `GOTRUE_SMTP_*` for the GoTrue lane, `SMTP_*` for MAIL-01; one-command rollback = `GOTRUE_MAILER_AUTOCONFIRM=true` + container config reload). Relay **values** are still operator-supplied, so criterion 4's smoke-test *proof* is an acknowledged gap: Phase 20 ships honest autoconfirm (path B) and hands "relay chosen and proven" forward as Phase 21's precondition.
- Signup confirmation mail (`g-01-3b-signup-mailer`) — **root cause is now diagnosed** (GoTrue fails while sending the confirmation email; `{code:500, error_code:"unexpected_failure"}`), and autoconfirm is on since 2026-09-20. Phase 20 now delivers the honest-copy fix (B) and closes the debug session; the SPA error-mapping honesty in `authApi.js` stays deferred.
- Nyquist VALIDATION.md drafts for phases 6–8 remain historical audit debt (not a product requirement).

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| backlog | 999.4 unify Approve + Mark ready (ADUX-11) | parked (product preference) | 2026-10-13 | v1.3 |
| backlog | 999.1 / 999.5 / 999.6 / 999.7 | moved into v1.3 (Phases 18 / 22 / 19 / 17) | 2026-10-14 | v1.3 |
| deferred_items | 13/deferred-items.md: admin.spec.js `/me network failure shows ServiceUnavailable not Forbidden` flake (pre-existing) | acknowledged | 2026-10-05 | v1.2 |
| deferred_items | 10/deferred-items.md: pre-existing test_admin_shortlist_empty_batch failure → FIX-01 / Phase 12 | resolved | 2026-10-02 | v1.1→v1.2 |
| debug_sessions | (4 items from v1 close — see MILESTONES.md) | acknowledged | 2026-09-22 | v1 |
| debug_sessions | admin-batch-cta-removal, draft-approved-contradiction, email-plain-body-rendered, footer-duplicates-cta-label, interstitial-not-paragraph, mark-ready-503, modal-close-not-sticky, per-row-ready-click-noop, preview-cursor | resolved 2026-10-13 | 2026-10-05 | v1.2 |

Carried product deferrals beyond v1.3: leaderboard, quiz, Whisper/Foundry ASR, ingest HTTP API, auto-publish/send, PIPE execution.

## Session Continuity

Last session: 2026-10-14T13:19:00.200Z
Stopped at: Phase 20 context gathered
Resume file: .planning/phases/20-mail-02-signup-confirmation-mail/20-CONTEXT.md
Next: `/gsd-execute-phase 17`

## Operator Next Steps

- Close Phase 17's verification gap: `/gsd-execute-phase 17 --gaps-only` (executes `17-03`)
- Plan the discussed phases: `/gsd-plan-phase 18` and `/gsd-plan-phase 20` (both have CONTEXT.md)
- Discuss or plan Phase 19 (Unsaved-changes guard) — not yet discussed
