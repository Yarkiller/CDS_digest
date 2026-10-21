---
gsd_state_version: "1.0"
milestone: v1.4
milestone_name: UI polish & honest navigation
current_phase: 25
current_phase_name: Admin «Настройка» — naming, readable surfaces, token repair
status: executing
stopped_at: Completed 25-08-PLAN.md
last_updated: "2026-10-21T19:20:07.946Z"
last_activity: 2026-10-21
last_activity_desc: Phase 25 execution started
state_head: bc9653a42029c184ab0f68f42714ff157bf0e00f
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 10
  completed_plans: 8
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-21 — v1.4 milestone started)

**Core value:** Trusted weekly prepared-article issue + one honest vote toward the next разбор
**Current focus:** Phase 25 — Admin «Настройка» — naming, readable surfaces, token repair

## Current Position

Phase: 25 (Admin «Настройка» — naming, readable surfaces, token repair) — READY TO EXECUTE
Plan: 7 of 7
Status: Ready to execute
Last activity: 2026-10-21 — Phase 25 plan 05 executed (status label roles + field boundary)

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
| Phase 25 P01 | 11min | 2 tasks | 4 files |
| Phase 25 P02 | 13min | 2 tasks | 4 files |
| Phase 25 P03 | 15min | 2 tasks | 7 files |
| Phase 25 P04 | 17min | 3 tasks | 10 files |
| Phase 25 P05 | 8 min | 2 tasks | 3 files |
| Phase 25 P06 | 21min | 3 tasks | 9 files |
| Phase 25 P07 | 19 | 2 tasks | 12 files |
| Phase 25 P08 | 12m | 3 tasks | 22 files |

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
- [Phase 25]: 25-01: three admin section labels read «Настройка» — sr-only h1, tab and mobile option renamed as literals; PIPELINE_PATH/DIGEST_PATH, handleSectionTabClick, every data-testid and both aria-labels stayed byte-identical
- [Phase 25]: 25-01: the web project's testMatch widened to /(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/ — admin-chrome.spec.js is the single home for criteria 1/2/4/5, so a new file never silently drops out of the runner
- [Phase 25]: 25-01: the tracer gate ran as a TDD pair (RED commit then GREEN commit) instead of a blocking human-verify stop — the tracer's own verify demands a failing result, so there is nothing sane for a human to approve until the component edit lands
- [Phase 25]: 25-02: eyebrow «Админ» удалён из DOM — getByText('Админ', { exact: true }) теперь 1 узел и это shell-ссылка; sr-only h1 (IN-01) сохранён и остаётся единственным
- [Phase 25]: 25-02: кегль вкладки сравнивается с контентным h2 двусторонне (tab === ingest-sources-heading И оба === 24px), зазор 16px, margin-top 0, nav.top − main.top < 48 — относительный порог вместо литерала 40px
- [Phase 25]: 25-02: пять замеров критерия 5 оформлены expect.soft — иначе RED показывает только первое падение, а acceptance требует все пять причин в одном выводе; soft-падение всё равно валит тест
- [Phase 25]: 25-03: семейство paper/paper-2/ink/ink-2/muted/rule объявлено в существующих блоках @theme static и [data-theme=light] (6 light-override'ов); семь тема-независимых ролей (-solid, on-solid, voting-ink, scrim) — только в @theme static, отсутствие override пинится G-3
- [Phase 25]: 25-03: tests/helpers/contrast.js дополнительно бросает исключение при alpha < 1 и на var()/% в каналах — прозрачные/полупрозрачные фоны устраняются конструктивно, а не проверкой
- [Phase 25]: 25-03: канонический контраст ui-select — --color-paper / #eef1f8 (light, 15.0:1) и канал/плейлист — --color-paper-2 / #f7f8fb (dark, 6.04:1)
- [Phase 25]: 25-04: G-9/G-10 живут в одном node-гейте и ищут токены, а не подстроки — класс-строка извлекается сканером строковых литералов, поэтому bg-primary-solid никогда не читается как bg-primary
- [Phase 25]: 25-04: пять пилюльных ассертов admin.spec.js переведены на token-exact пару (split по пробелам) — подстрочный toHaveClass(/bg-primary/) зеленел на bg-primary-solid и не ловил блудный базовый класс
- [Phase 25]: 25-04: voting пинится ПОЛОЖИТЕЛЬНО (rgb(15,23,42) на rgb(234,179,8), 9.31) в обеих темах — белая подпись на жёлтом даёт 1.92 и обязана провалить тест, поэтому исключение ROADMAP не является пропуском
- [Phase 25 code review]: 12 находок (1 critical / 6 warning / 5 info) → `25-REVIEW.md`; закрыты CR-01, WR-01 и IN-02, остальные девять отложены с причинами в `25-REVIEW-DISPOSITION.md`
- [Phase 25 CR-01]: `text-[oklch(45%_0.14_25)]` = rgb(147,43,42) давал 1.98:1 на тёмной `paper-2` (2.20:1 на `paper`) и проходил зелёным, потому что G-9 читал только именованные токены и по одному литералу за раз — закрыто токеном `--color-danger-ink` (#F87171 dark / #B91C1C light; 6.36/5.75 и 6.47/5.91 на paper/paper-2), плюс G-11 (численный пол для arbitrary-цветов), G-12 (arbitrary-цветовые утилиты запрещены целиком) и G-13 (замер danger-ink), каждый со своим proof-тестом, чтобы детектор не мог пройти вхолостую
- [Phase 25 CR-01]: `parseColor()` в `tests/helpers/contrast.js` выучил CSS Color 4 `oklch()` именно потому, что парсер, бросающий на плохом значении, даёт падающему коэффициенту спрятаться за «unsupported colour» — ровно failure-mode CR-01; поведение для hex/rgb не изменилось
- [Phase 25 CR-01]: проверено, что Tailwind v4 реально генерирует новые утилиты — `.text-danger-ink`, `.border-danger-ink`, `.bg-danger\/10` и оба значения токена присутствуют в собранном CSS, иначе фикс был бы тем же дефектом «токен, который не генерируется»
- [Phase 25]: 25-05: `blendOver(colour, base, alpha)` — единственная реализация композита тинта: alpha самого цвета не переносится (иначе `rgba(...)` из `getComputedStyle` дошёл бы до `contrastRatio` и тот бросил бы), полупрозрачная база бросает, alpha 1 нормализуется в `rgb(...)`
- [Phase 25]: 25-05: `--color-field-border` — плоский `#64748B` без light-override; заявленная в постановке пара `#4B5563`/`#64748B` провалила бы собственный 3:1-гейт в тёмной теме (2.328), поэтому отклонение записано измеряемо, а не вкусово
- [Phase 25]: 25-05: `success-ink` / `voting-ink-on-tint` / `accent-text` намеренно НЕ добавлены в `THEMED` — иначе G-4 anti-vacuum потребовал бы потребителей, которых до 25-06/25-07 нет; их темо-зависимость пинится внутри G-14 (наличие в блоке + отличающийся light-override)
- [Phase 25]: 25-05: имя `accent-text` выбрано именно потому, что G-5 запрещает подстроку `accent-ink`; базовый `--color-accent` не изменён, тёмное значение новой роли байт-идентично ему, поэтому тёмная тема визуально не двигается
- [Phase 25]: Status fills stay as brand colours; only labels moved to the -ink roles (G-18 enforces the split).
- [Phase 25]: admin-toast uses the alias family (bg-paper-2 + border-rule + text-ink), not a one-off colour.
- [Phase 25]: G-16 asserts only status literals the harness can render; the send-failure banner literal is registered but not demanded.
- [Phase 25]: 25-07: gotoAdmin awaits data-theme only where the theme toggle is mounted, so WR-04 is closed without making the auth shell hang.
- [Phase 25]: 25-07: ActionButton keeps stateFill.loading empty and dims via an additive stateChrome map, preserving the variant fill mid-flight (must_have #13).
- [Phase 25]: 25-07: G-17 pins 16 controls plus four decorative literals; G-19 forbids text-accent as a label, keeping boundary and divider roles from re-merging.
- [Phase 25]: The base --color-primary stays byte-identical (#8B5CF6) as fill/border/ring/tint (D-05); only the label role moves to the theme-dependent --color-primary-text (#A78BFA dark / #6D28D9 light).
- [Phase 25]: G-20 scans className string literals token-exact, never substrings: text-primary-text, text-text-primary, bg-primary, border-primary and outline-primary are all non-offenders, so the gate cannot self-trigger on its own fix.
- [Phase 25]: The save-retry background is assembled from tokens via blendOver(--color-danger, --color-bg-app, 0.1) because getComputedStyle serializes bg-danger/10 to oklab(…/0.1), which parseColor refuses.

### Pending Todos

None.

### Blockers/Concerns

- **Vite dev-server flakiness in this workspace (operational, recurring).** Across Phases 18-02, 18-03, the Phase 18 gates and the Phase 24 UAT/validation runs, the Playwright `web` project produced mass failures on `127.0.0.1:5174` — a reuse fight between a stale long-lived Vite server and a new run, or the server dying mid-run. **Phase 24 closing added a second signature:** a stale server left running with `VITE_USE_MOCKS=false` from `web/.env.local` makes every admin spec land on the login screen (17 failures, all on `getByTestId("admin-pipeline-page")`). Always check for a listener on 5174 (`Get-NetTCPConnection -LocalPort 5174 -State Listen`) and kill stale servers before a full-suite run; a clean re-run has produced green every time (17/17 for the Phase 24 slice).

- **Scheduled ingestion has no live-run proof yet (deferred UAT checkpoint).** `pipeline_ingest_sources` is empty, so `24-UAT.md` test 6 — a real YouTube Atom feed producing `materials.status='draft'` + `pending` shortlist rows, with the cursor not advancing on a re-run — is recorded as a deferred follow-up rather than a pass. Everything else in Phase 24 (timer ticks, flock exit 75, bounded run, numeric alert codes, `0600` env file, migration 013, admin UI block) is proven on the live WSL2/systemd 255 host. Add one enabled source and re-run the tick to close it.
- **SMTP relay (Phase 20/21)** — the corporate relay **choice and configuration shape** are recorded (Phase 20 CONTEXT: `GOTRUE_SMTP_*` for the GoTrue lane, `SMTP_*` for MAIL-01; one-command rollback = `GOTRUE_MAILER_AUTOCONFIRM=true` + container config reload). Relay **values** are still operator-supplied, so criterion 4's smoke-test *proof* remains an acknowledged ops gap.
- Signup confirmation mail (`g-01-3b-signup-mailer`) — **root cause diagnosed** (GoTrue fails while sending the confirmation email; `{code:500, error_code:"unexpected_failure"}`), autoconfirm on since 2026-09-20, delivery path (B) shipped in Phase 20; the SPA error-mapping honesty in `authApi.js` stays deferred.
- **Phase 25 code review left 9 findings deferred (readability debt, deferred by operator decision on 2026-10-21).** CR-01 and WR-01 are closed, but the *rest of the «readable surfaces» goal is not met yet*: status tokens used as **text on tints** still fail 4.5:1 in the light theme (success pill **1.92:1**, voting pill **1.62:1**, error panel **3.17:1**, Login/Register field errors **3.76:1** — WR-02); the admin toast is `bg-text-primary` on `text-text-primary`, i.e. **1.00:1** and explicitly carved out of `G-10` (WR-05); the light field edge is **1.48:1** against WCAG 1.4.11's 3:1 (WR-06). WR-03 (ActionButton appends variant *and* state fills; the state fill is dead today only because of stylesheet order) and WR-04 (the light-theme spec races `data-theme`, never awaiting the attribute) are test/robustness concerns. Full reasons and per-item rationale: `.planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-REVIEW-DISPOSITION.md`. **WR-02 and WR-05 are the strongest candidates for the next phase** — they are the same defect class CR-01 was, just one family over.
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

Last session: 2026-10-21T19:20:07.892Z
Stopped at: Completed 25-08-PLAN.md
Resume file: None
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
