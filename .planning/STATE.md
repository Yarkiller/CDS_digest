---
gsd_state_version: "1.0"
milestone: v1.3
milestone_name: Live mail, scheduled ingestion & backlog debt
current_phase: 17
current_phase_name: YAML merge-key acceptance in the strict validator
status: ready_to_plan
stopped_at: Phase 17 context gathered
last_updated: "2026-10-14T09:51:39.486Z"
last_activity: 2026-10-14
last_activity_desc: v1.3 roadmap created (Phases 17–24, 19/19 requirements mapped)
state_head: 3d58d392596cf01f756b5ea651f963ec88b71bcf
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-14 — after v1.3 milestone start)

**Core value:** Trusted weekly prepared-article issue + one honest vote toward the next разбор
**Current focus:** v1.3 Phase 17 — YAML merge-key acceptance in the strict pipeline-config validator

## Current Position

Phase: 17 (1 of 8) — YAML merge-key acceptance in the strict validator
Plan: — (ready to plan)
Status: Roadmap complete — ready to plan Phase 17
Last activity: 2026-10-14 — v1.3 roadmap created (Phases 17–24, 19/19 requirements mapped)

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 26 (40 v1 + 23 v1.1 + 26 v1.2)
- Prior milestones shipped: v1 (5 phases), v1.1 (6 phases), v1.2 (5 phases)
- v1.3 plans completed: 0

**By Phase (v1.3):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 17. YAML merge-key | 0/? | not started | - |
| 18. Reader-route honesty | 0/? | not started | - |
| 19. Unsaved-changes guard | 0/? | not started | - |
| 20. Signup mail (MAIL-02) | 0/? | not started | - |
| 21. Live SMTP digest (MAIL-01) | 0/? | not started | - |
| 22. Admin nav grouping | 0/? | not started | - |
| 23. Ingest sources | 0/? | not started | - |
| 24. Scheduled ingestion | 0/? | not started | - |

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

### Pending Todos

None.

### Blockers/Concerns

- **SMTP relay choice (pre-phase gate)** — Phase 20/21 cannot pass until the corporate relay is chosen (one relay serves GoTrue + MAIL-01; TLS mode/port, CA bundle, ADR-0002 contour isolation). TDD: contract first.
- Signup confirmation mail (`g-01-3b-signup-mailer`) carried from v1 — root cause still unknown; Phase 20 opens with diagnosis.
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

Last session: 2026-10-14T09:51:39.459Z
Stopped at: Phase 17 context gathered
Resume file: .planning/phases/17-yaml-merge-key-acceptance-in-the-strict-validator/17-CONTEXT.md
Next: `/gsd-plan-phase 17`

## Operator Next Steps

- Start Phase 17 with `/gsd-plan-phase 17`
- Resolve the SMTP relay choice before Phase 20 is planned (`/gsd-discuss-phase 20`)
