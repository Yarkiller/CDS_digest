---
gsd_state_version: "1.0"
milestone: v1.3
milestone_name: Live mail, scheduled ingestion & backlog debt
current_phase: 21
current_phase_name: MAIL-01 live SMTP digest delivery
current_plan: Not started
status: planning
stopped_at: Phase 21 context gathered
last_updated: "2026-10-16T12:04:24.144Z"
last_activity: 2026-10-16
last_activity_desc: Phase 18 complete, transitioned to Phase 21
state_head: 989407b9f12b680935afcbfa071b5f4aab59d322
progress:
  total_phases: 8
  completed_phases: 4
  total_plans: 10
  completed_plans: 10
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-16 — after Phase 20)

**Core value:** Trusted weekly prepared-article issue + one honest vote toward the next разбор
**Current focus:** Phase 18 — Reader-route honesty for draft materials

## Current Position

Phase: 21 — MAIL-01 live SMTP digest delivery
Current Plan: Not started
Total Plans in Phase: 3
Status: Ready to plan
Last activity: 2026-10-16 — Phase 18 complete, transitioned to Phase 21

Progress: [█████░░░░░] 50%

## Performance Metrics

**Velocity:**
- Total plans completed: 10 (40 v1 + 23 v1.1 + 26 v1.2)
- Prior milestones shipped: v1 (5 phases), v1.1 (6 phases), v1.2 (5 phases)
- v1.3 plans completed: 3

**By Phase (v1.3):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 17. YAML merge-key | 3/3 | Complete (verified 27/27) | - |
| 18. Reader-route honesty | 3/3 | Complete (verified 20/20, UAT 3/3, threats_open 0) | - |
| 19. Unsaved-changes guard | 0/? | not started | - |
| 20. Signup mail (MAIL-02) | 0/? | context gathered | - |
| 21. Live SMTP digest (MAIL-01) | 0/? | not started | - |
| 22. Admin nav grouping | 0/? | not started | - |
| 23. Ingest sources | 0/? | not started | - |
| 24. Scheduled ingestion | 0/? | not started | - |
| 17 | 3 | - | - |
| 18 | 3 | - | - |
| 19 | 2 | - | - |
| 20 | 2 | - | - |
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 17 P01 | 9min | 2 tasks | 3 files |
| Phase 17 P02 | 7min | 2 tasks | 3 files |
| Phase 17 P03 | 8min | 3 tasks | 3 files |
| Phase 18 P01 | 9min | 3 tasks | 5 files |
| Phase 18 P02 | 21 min | 3 tasks | 4 files |
| Phase 18 P03 | 57min | 2 tasks | 5 files |
| Phase 19 P01 | 16min | 2 tasks | 1 files |
| Phase 19 P02 | 22min | 3 tasks | 6 files |
| Phase 20 P01 | 4min | 2 tasks | 4 files |
| Phase 20 P02 | 5min | 2 tasks | 2 files |

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
- [Phase 17]: [Phase 17-03]: A merge source's pristine own keys are snapshotted and duplicate-scanned in the same pre-mutation window as the carrier, before super().flatten_mapping mutates the graph (CR-01)
- [Phase 17]: [Phase 17-03]: The source scan runs before _project, so the duplicate-vs-bound and own-key-vs-source precedence is specified and pinned in all four measured directions, one row in every case
- [Phase 17]: [Phase 17-03]: _check_own_keys is a verbatim extraction of the existing duplicate loop, so the D-09 tripwire and the explicit-duplicate line pins stay byte-identical
- [Phase 17]: [Phase 17-03]: _merge_source_ids is an iterative visited-guarded walk, so _anchor_holder_keys reaches nested-merge holders and terminates on a self-referential merge (WR-01)
- [Phase 17]: [Phase 17-03]: IN-01 alias-copy over-match is accepted and pinned by a characterisation test; precise disambiguation needs composer-event data PyYAML discards
- [Phase 18]: Phase 18 P01: the preview endpoint reuses MaterialReaderResponse verbatim with tags=[] and related=[] (D-02/D-08) — no preview DTO, no status key
- [Phase 18]: Phase 18 P01: 403 comes only from require_admin and every non-draft slug is 404 material_not_found, so no slug-existence oracle is created (D-03/D-04/D-12)
- [Phase 18]: Phase 18 P01: no-store is set on the preview route only via the declared Response param; the reader route and get_material_for_reader stay byte-identical (D-07)
- [Phase 18]: Phase 18 P01: the reader route's lack of a role branch is frozen by an admin-token characterisation pin landed with zero production edits
- [Phase 18]: 18-02: единственный SPA-маршрут admin/materials/:id с флагом preview — структурное переиспользование MaterialPage (D-02), без отдельной страницы предпросмотра
- [Phase 18]: 18-02: полномочия остаются за сервером (D-03) — клиент не делает запрос /me на preview-маршруте, а маппит FORBIDDEN на ForbiddenPage, NOT_FOUND — на Navigate к /materials/:slug (D-12)
- [Phase 18]: 18-02: баннер предпросмотра зависит только от route-scoped prop preview (D-06), т.к. ответ читательского DTO не содержит status; tags/related приходят пустыми по D-08
- [Phase 18]: 18-03: anchor attributes plus a widened sandbox replace any repoint of the shared email href (D-11), so preview-send parity stays provable and no admin URL reaches recipient mail — render_email_html is shared by preview_digest_email and send_digest; test_preview_email_html_matches_send_html and the /materials/ href assertions all stayed byte-identical and green
- [Phase 18]: 18-03: the email-preview iframe grants allow-popups allow-popups-to-escape-sandbox while withholding script and same-origin powers (T-18-05) - the CTA escapes, the frame does not gain script or origin powers — The frame body is backend-rendered with stdlib html.escape only; the new spec asserts the exact sandbox value plus two not.toContain checks, so a future token addition fails the suite
- [Phase 18]: 18-03: only the shortlist modal link is repointed to /admin/materials/{slug} (D-10) - the draft-404 never lived in the email, whose pool is approved-and-ready — Repointing the shared email builder would put admin URLs into the real digest mail ordinary readers receive (T-18-06); preview_digest_email.py received zero edits
- [Phase 18]: CR-01 (post-execution code review, reproduced in the browser and fixed): MaterialPage now resets `redirectToReader` and `forbidden` on every load — The instance is reused across the /admin/materials/:id -> /materials/:id handoff the flag itself triggers (both routes are children of one layout route in App.jsx), so a stale `true` re-rendered `<Navigate>` to the URL already current and the reader route rendered nothing; the pre-existing D-12 test could not see it because `gotoAsRole` ends in `page.reload()` after the redirect has already moved the document (WR-02)
- [Phase 18]: The RED that catches CR-01 drives the real user journey (shortlist «Превью материала» -> «Открыть материал →») and asserts the rendered reader surface, not just the URL — URL equality is necessary but not sufficient, since it also holds while the page renders nothing
- [Phase 18]: IN-01…IN-05 (code-review info findings) are recorded `deferred` with reasons in `18-REVIEW-DISPOSITION.md` and the verifier concurred — inert unused prop, `no-store` absent on error paths (no leak), private `_SLUG_PATTERN` crossing route modules + a duplicated guard, a duplicated mock role resolver, and 401 mapped to a retryable NETWORK error on the preview surface
- [Phase 19]: D-09: router migration alone, proven at Wave-0 baseline 110 before any useBlocker wiring
- [Phase 19]: No errorElement on createBrowserRouter migration (behaviour-preserving)
- [Phase 19]: D-01/D-04: boolean useBlocker + custom modal for SPA leave (ADUX-09 c1)
- [Phase 19]: D-05/D-06: armBeforeUnload two-statement contract; browser-owned unload text
- [Phase 19]: D-07: reusable util/hook/dialog trio for Phase 23 ADUX-10 reuse
- [Phase 20]: D-02: Ship path (B) honest autoconfirm copy this session; relay-proof deferred to Phase 21 via Plan 20-02
- [Phase 20]: D-07/D-08: CONFIRM_MESSAGE lives only in RegisterPage; authApi error-mapping strings untouched
- [Phase 20]: D-10: DOM harness armSignUpWithoutSession forces null session under VITE_USE_MOCKS
- [Phase 20]: D-12: Close g-01-3b in place with Resolution citing 20-01 honest copy
- [Phase 20]: D-03/D-13: Runbook records GOTRUE_SMTP_*/SMTP_* shape only; no new ADR (D-04)
- [Phase 20]: D-05/D-06: Rollback GOTRUE_MAILER_AUTOCONFIRM=true; criterion-4 proof → Phase 21

### Pending Todos

None.

### Blockers/Concerns

- **Vite dev-server flakiness in this workspace (operational, recurring).** Across Phases 18-02, 18-03 and the Phase 18 gates, the Playwright `web` project produced mass `ERR_CONNECTION_REFUSED` failures on `127.0.0.1:5174` — a reuse fight between a stale long-lived Vite server and a new run, or the server dying mid-run. The signature is indistinguishable from a real regression unless the error text is read. Always check for a listener on 5174 (`Get-NetTCPConnection -LocalPort 5174 -State Listen`) and kill stale servers before a full-suite run; a clean re-run has produced 110 passed every time.

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

Last session: 2026-10-16T12:04:24.012Z
Stopped at: Phase 21 context gathered
Resume file: .planning/phases/21-mail-01-live-smtp-digest-delivery/21-CONTEXT.md
Next: `/gsd-plan-phase 19`

## Operator Next Steps

- Plan the discussed phase: `/gsd-plan-phase 20` (MAIL-02, CONTEXT.md exists)
- Phase 19 (Unsaved-changes guard, 999.6) is not yet discussed — `/gsd-discuss-phase 19`
- Phase 17 and 18 are complete; stale `17-VALIDATION.md` is a record-accuracy task: `/gsd-validate-phase 17`
- Phase 18 deferred code-review info findings IN-01…IN-05 (see `18-REVIEW-DISPOSITION.md`) — none blocking
- Optional: `/gsd-ui-review 18` — Phase 18 modified frontend files
