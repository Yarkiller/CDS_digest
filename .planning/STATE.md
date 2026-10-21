---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: UI polish & honest navigation
current_phase: 25
current_phase_name: Admin «Настройка» — naming, readable surfaces, token repair
status: planning
stopped_at: Phase 25 UI-SPEC approved
last_updated: "2026-10-21T12:18:20.047Z"
last_activity: 2026-10-21
last_activity_desc: Milestone v1.4 roadmap created (UI polish & honest navigation)
state_head: 229d07be034ca72fe13064668cf93587754bdc35
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 4
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-21 — v1.4 milestone started)

**Core value:** Trusted weekly prepared-article issue + one honest vote toward the next разбор
**Current focus:** v1.4 UI polish & honest navigation (roadmap ready — Phase 25 next)

## Current Position

Phase: 25 (Admin «Настройка» — naming, readable surfaces, token repair) — READY TO EXECUTE
Plan: —
Status: Roadmap ready; 10 requirements mapped, 0 unmapped
Last activity: 2026-10-21 — Milestone v1.4 roadmap created (UI polish & honest navigation)

## Performance Metrics

**Velocity:**

- Total plans completed: 28 (40 v1 + 23 v1.1 + 26 v1.2)
- Prior milestones shipped: v1 (5 phases), v1.1 (6 phases), v1.2 (5 phases)
- v1.3 plans completed: 3

**By Phase (v1.3):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 17. YAML merge-key | 3/3 | Complete (verified 27/27) | - |
| 18. Reader-route honesty | 3/3 | Complete (verified 20/20, UAT 3/3, threats_open 0) | - |
| 19. Unsaved-changes guard | 2/2 | Complete | - |
| 20. Signup mail (MAIL-02) | 2/2 | Complete | - |
| 21. Live SMTP digest (MAIL-01) | 3/3 | Complete | - |
| 22. Admin nav grouping | 2/2 | Complete | - |
| 23. Ingest sources | 4/4 | Complete | - |
| 24. Scheduled ingestion | 8/8 | Complete (UAT 7 pass + 1 deferred, threats_open 0) | - |
| 17 | 3 | - | - |
| 18 | 3 | - | - |
| 19 | 2 | - | - |
| 20 | 2 | - | - |
| 23 | 4 | - | - |
| 22 | 3 | - | - |
| 21 | 3 | - | - |
| 24 | 8 | - | - |
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
| Phase 21 P01 | 11min | 2 tasks | 12 files |
| Phase 21 P02 | 12 | 2 tasks | 11 files |
| Phase 21 P03 | 9min | 3 tasks | 10 files |
| Phase 22 P01 | 22min | 2 tasks | 6 files |
| Phase 22 P02 | 10min | 2 tasks | 2 files |
| Phase 23 P01 | 9min | 2 tasks | 14 files |
| Phase 23 P02 | 18min | 3 tasks | 7 files |
| Phase 23 P03 | 22min | 3 tasks | 8 files |
| Phase 23 P04 | 12min | 2 tasks | 4 files |
| Phase 24 P01 | 10 min | 2 tasks | 24 files |
| Phase 24 P02 | 7min | 2 tasks | 6 files |
| Phase 24 P03 | 40min | 3 tasks | 14 files |
| Phase 24 P04 | 25min | 2 tasks | 7 files |
| Phase 24 P05 | 25min | 3 tasks | 13 files |
| Phase 24 P06 | 11min | 2 tasks | 5 files |
| Phase 24 P07 | 35min | 3 tasks | 10 files |
| Phase 24 P08 | 20min | 3 tasks | 6 files |

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
- [Phase 21]: 21-01: delivery_status is read from the mailer result, not the batch row — the batch keeps planned M only; live N/status ride SendDigestResult + the digest_send ping payload (D-06 option i)
- [Phase 21]: 21-01: empty/malformed-only audience (M=0) still publishes; the live path honestly reports delivery_status=sent with delivered_count=0 and non-alarming copy (D-04 / RESEARCH Q3)
- [Phase 21]: resolve_mailer moved to composition/mailer_factory.py: adapter selection is wiring, so infrastructure must not import composition (architecture.mdc); stub_mailer.py keeps StubMailer + SmtpMailer re-export only
- [Phase 21]: Settings.smtp_port is int|None (None = unset) so D-16 can require SMTP_PORT explicitly instead of silently defaulting to 587; non-numeric SMTP_PORT raises ConfigurationError in from_env
- [Phase 21]: 21-03: SupabaseDigestPublisher forwards the planned audience M via p_recipient_count and leaves p_delivery_status at the RPC default (option i: no update_delivery, no migration, D-06)
- [Phase 21]: 21-03: list_digest_recipients runs on the service_role client wired in live.py — a user-scoped client would return M=0 under the profiles_select_own RLS policy (RESEARCH Pitfall 7); no RLS widened
- [Phase 21]: 21-03: SendDigestResponse.delivered_count is additive (default 0) and a contained mail partial/failure after a successful publish stays HTTP 200 with honest N/M (D-11)
- [Phase 21]: 21-03: runbook 4e records digest SMTP smoke/rollback + the MAIL-05 config boundary; Phase 20 criterion-4 relay proof stays an open ops gap (D-15), not claimed done
- [Phase 22]: 22-01: pathless AdminLayout parent keeps /admin/digest and /admin/pipeline byte-identical and adds no /admin index (D-01…D-04)
- [Phase 22]: 22-01: shell «Админ» active state comes from the useLocation pathname prefix — NavLink prefix matching on /admin/digest never lights /admin/pipeline or the materials preview (D-09)
- [Phase 22]: 22-01: the section switch is nav + NavLink (underline, no pill fill, no ARIA tab roles); the narrow select uses a hard-coded two-path whitelist and navigate() so the Phase 19 guard still fires (T-22-02, D-12, D-19)
- [Phase 22]: 22-01: both child pages drop the page H1 and duplicate eyebrow on every branch; the active tab carries the text-3xl font-semibold hierarchy (D-06, D-08)
- [Phase 22]: 22-02: the dirty->tab and dirty->select journeys passed immediately on the post-22-01 tree, so the plan is a characterization pin (D-13/D-14/D-15/D-19 already hold) with zero production edits; no guard carve-out exists
- [Phase 22]: 22-02: 16-UI-SPEC A-2 is marked SUPERSEDED (top banner, A-2 row, Route/nav heading) with a 22-UI-SPEC pointer; route retained, single shell Админ, in-page underline tabs, and 'no second navigation bar' kept true via D-05
- [Phase 23]: Tracer ships full happy-path spine before 23-02 reject matrix
- [Phase 23]: YAML Save/Reset use yamlDirty; combined dirty is leave-guard only (ADUX-10)
- [Phase 23]: D-10 confirmed hard-delete for ingest sources (user selected hard-delete)
- [Phase 23]: Missing ingest-source PATCH/DELETE id maps to 404 ingest_source_not_found
- [Phase 23]: D-16/D-17 schema door: new-table-012 — ship public.pipeline_ingest_sources via migration 012 with RLS enabled and zero policies (do not reuse ingestion_sources)
- [Phase 23]: Operator applied migration 012 on shared VM (2026-10-17); count(*)=0; §4i Applied stamped; RLS/policy checklist accepted via resume-signal
- [Phase 23]: ADUX-10 closed by Playwright only — dirty OR from 23-01 already matched D-04
- [Phase 23]: Toggle/delete errors share UI-SPEC copy «Не удалось обновить источник. Повторите действие.»
- [Phase 24]: Threat mitigations T-24-01/T-24-02 landed in tracer GREEN; Task 2 test-only pin
- [Phase 24]: Blank INGEST_TEMPLATE defaults to lecture; invalid non-blank raises ConfigurationError
- [Phase 24]: Older-than-cursor filtered by select_window; video try/except in Task 1 for D-09
- [Phase 24]: CollectOutcome.exit_code is single source for typer.Exit in collect_cli
- [Phase 24]: schema-013-now: cursor columns + singleton ingestion_schedule in one migration (D-06/D-14)
- [Phase 24]: Operator applied migration 013 on shared VM 2026-10-18; PostgREST ingestion_schedule empty (D-14)
- [Phase 24]: §4k prose avoids non-env KEY= so env cross-check only hits Settings.from_env keys
- [Phase 24]: Unit secret/publish scans require non-empty deploy/systemd (anti-vacuum)
- [Phase 24]: Port method is update(...); PLAN wins over PATTERNS save(schedule) sketch
- [Phase 24]: ingestion_schedule_not_configured detail string appears once in _require_* (OpenAPI text omits code)
- [Phase 24]: dirty stays yamlDirty || sourceFormDirty — schedule never arms leave dialog (D-16)
- [Phase 24]: Empty-week validation message is shown alone in status (not prefixed with Включён/Выключен)
- [Phase 24]: Harness exposes readIngestionScheduleMock for patchCount assertions (Task 2 blur contract)
- [Phase 24-07]: the oneshot's only bound is its start phase — `TimeoutStartSec=1800` replaces the inert `RuntimeMaxSec=1800`, because systemd 255 logs «has no effect … Ignoring.» and never applies the runtime knob to a `Type=oneshot`
- [Phase 24-07]: the binding property is the **stamp**, not the unit's `Result` — a kill landing in the shutdown tail can still write `last_run_at`, so the live probe asserts on `last_run_at` and uses 500 ms (2 s stamped; 500 ms did not)
- [Phase 24-08]: the `OnFailure=` monitor passes `MONITOR_EXIT_CODE` as a qualifier (`exited`/`killed`) and the number in `MONITOR_EXIT_STATUS`; the legacy `EXIT_CODE`/`EXIT_STATUS` are unset on systemd 255
- [Phase 24-08]: text contracts invert rather than extend — the positive assertion pins the whole nested substitution and a negative gate forbids the old token, because a bare `EXIT_STATUS:-` is a substring of `MONITOR_EXIT_STATUS:-` and would pass vacuously
- [Phase 24-08]: no `killed)` arm is added (D-12 scope) — a SIGTERM from the run limit correctly falls to `*)` with the numeric code, e.g. `unexpected failure (exit 15)`
- [Phase 24 verification]: record-drift gates run inside pytest, never as a shell `!` negation, because the execution host is PowerShell where a leading `!` is a parse error

### Pending Todos

None.

### Blockers/Concerns

- **Vite dev-server flakiness in this workspace (operational, recurring).** Across Phases 18-02, 18-03, the Phase 18 gates and the Phase 24 UAT/validation runs, the Playwright `web` project produced mass failures on `127.0.0.1:5174` — a reuse fight between a stale long-lived Vite server and a new run, or the server dying mid-run. **Phase 24 closing added a second signature:** a stale server left running with `VITE_USE_MOCKS=false` from `web/.env.local` makes every admin spec land on the login screen (17 failures, all on `getByTestId("admin-pipeline-page")`). Always check for a listener on 5174 (`Get-NetTCPConnection -LocalPort 5174 -State Listen`) and kill stale servers before a full-suite run; a clean re-run has produced green every time (17/17 for the Phase 24 slice).

- **Scheduled ingestion has no live-run proof yet (deferred UAT checkpoint).** `pipeline_ingest_sources` is empty, so `24-UAT.md` test 6 — a real YouTube Atom feed producing `materials.status='draft'` + `pending` shortlist rows, with the cursor not advancing on a re-run — is recorded as a deferred follow-up rather than a pass. Everything else in Phase 24 (timer ticks, flock exit 75, bounded run, numeric alert codes, `0600` env file, migration 013, admin UI block) is proven on the live WSL2/systemd 255 host. Add one enabled source and re-run the tick to close it.
- **SMTP relay (Phase 20/21)** — the corporate relay **choice and configuration shape** are recorded (Phase 20 CONTEXT: `GOTRUE_SMTP_*` for the GoTrue lane, `SMTP_*` for MAIL-01; one-command rollback = `GOTRUE_MAILER_AUTOCONFIRM=true` + container config reload). Relay **values** are still operator-supplied, so criterion 4's smoke-test *proof* remains an acknowledged ops gap.
- Signup confirmation mail (`g-01-3b-signup-mailer`) — **root cause diagnosed** (GoTrue fails while sending the confirmation email; `{code:500, error_code:"unexpected_failure"}`), autoconfirm on since 2026-09-20, delivery path (B) shipped in Phase 20; the SPA error-mapping honesty in `authApi.js` stays deferred.
- Nyquist VALIDATION.md drafts for phases 6–8 remain historical audit debt (not a product requirement). Phase 24's `24-VALIDATION.md` is now `status: validated`, `nyquist_compliant: true` (0 gaps; 227 unit + 17 Playwright green).

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| backlog | 999.4 unify Approve + Mark ready (ADUX-11) | parked (product preference) | 2026-10-13 | v1.3 |
| deferred_items | 24-UAT.md test 6: live collection against a real enabled source (YouTube Atom → drafts + pending shortlist, cursor not advancing on re-run) | deferred — `pipeline_ingest_sources` empty | 2026-10-18 | v1.3 |
| backlog | 999.1 / 999.5 / 999.6 / 999.7 | moved into v1.3 (Phases 18 / 22 / 19 / 17) | 2026-10-14 | v1.3 |
| deferred_items | 13/deferred-items.md: admin.spec.js `/me network failure shows ServiceUnavailable not Forbidden` flake (pre-existing) | acknowledged | 2026-10-05 | v1.2 |
| deferred_items | 10/deferred-items.md: pre-existing test_admin_shortlist_empty_batch failure → FIX-01 / Phase 12 | resolved | 2026-10-02 | v1.1→v1.2 |
| debug_sessions | (4 items from v1 close — see MILESTONES.md) | acknowledged | 2026-09-22 | v1 |
| debug_sessions | admin-batch-cta-removal, draft-approved-contradiction, email-plain-body-rendered, footer-duplicates-cta-label, interstitial-not-paragraph, mark-ready-503, modal-close-not-sticky, per-row-ready-click-noop, preview-cursor | resolved 2026-10-13 | 2026-10-05 | v1.2 |

Carried product deferrals beyond v1.3: leaderboard, quiz, Whisper/Foundry ASR, ingest HTTP API, auto-publish/send, PIPE execution.

## Session Continuity

Last session: 2026-10-21T11:38:27.432Z
Stopped at: Phase 25 UI-SPEC approved
Resume file: .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-UI-SPEC.md
Next: `/gsd-discuss-phase 25` (or `/gsd-plan-phase 25`)

## Operator Next Steps

- Start Phase 25 with `/gsd-discuss-phase 25` (or `/gsd-plan-phase 25` to skip discussion)

## v1.4 roadmap (Phases 25-28)

| Phase | Name | Requirements |
|-------|------|--------------|
| 25 | Admin «Настройка» — naming, readable surfaces, token repair | PIPEUI-01…04, THEME-01/02 |
| 26 | Section context — anchor scrolling and header active state | NAV-01, NAV-02 |
| 27 | Header search runs on submit | KNOW-05 |
| 28 | Live proof — streamed DeepSeek ingest | ING-09 |

**v1.4 roadmap locks (for phase planners):**

- **Order:** 25 → 26 → 27 → 28. Phase 25 is the only phase that touches `web/src/index.css` (declaring the `paper` / `paper-2` / `ink` / `ink-2` / `muted` / `rule` / `accent-ink` token family plus its light overrides); 26 and 27 consume that tree, so they must not re-declare tokens.
- **Phase 25 (PIPEUI/THEME):** all three «Пайплайн» surfaces in `AdminLayout.jsx` (sr-only h1 line 49, tab line 70, mobile option line 82) become «Настройка»; `/admin/pipeline` and every `data-testid` stay unchanged. `IngestSourcesSection.jsx:171` becomes «Источники». Filled buttons and the active nav pill get a theme-independent white label, with the yellow `voting` fill (#EAB308) keeping a dark label. Backlog 999.2 chrome polish ships here (no «Админ» eyebrow, `h2`-scale tabs, wider gap, less top space).
- **Phase 26 (NAV-01/02):** Bug 3 is ANCHOR SCROLLING — no breadcrumb component, no route change. Use `scroll-margin-top` on prose headings (or `scroll-padding-top`), sized to the 64px sticky header, proven on a short and a long section. Section origin rides `location.state`, degrades honestly on a direct URL visit; reuse the `adminActive` prefix pattern — never derive origin from the URL, never persist it in `localStorage`.
- **Phase 27 (KNOW-05):** header submit must run the search immediately — exactly one API call per submission, zero calls for an empty query, no double-fire on re-render. `knowledgeApi.searchKnowledge` and the backend stay untouched.
- **Phase 28 (ING-09):** proof only — `0dddc75` (`stream=True` + delta assembly) is already committed. Live run on a >10 min video; no adapter rewrite. If it still fails, record the failure and stop.
- **Out of scope (do not plan):** breadcrumbs, `/admin/settings`, reader-surface re-theme, white label on the yellow `voting` fill, DeepSeek retry/backoff work, 999.4.
