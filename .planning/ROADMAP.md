# Roadmap: Digest CDS

## Milestones

- ✅ **[v1 MVP](milestones/v1-ROADMAP.md)** — Phases 1-5 (shipped 2026-09-22)
- ✅ **[v1.1 YouTube → LLM → Supabase ingestion](milestones/v1.1-ROADMAP.md)** — Phases 6-11 (shipped 2026-10-02)
- ✅ **[v1.2 Admin UX + diagnostics + PIPE-01 MVP](milestones/v1.2-ROADMAP.md)** — Phases 12-16 (shipped 2026-10-05)
- ✅ **[v1.3 Live mail, scheduled ingestion & backlog debt](milestones/v1.3-ROADMAP.md)** — Phases 17-24 (shipped 2026-10-18)

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

<details>
<summary>✅ v1.1 YouTube → LLM → Supabase ingestion (Phases 6-11) — SHIPPED 2026-10-02</summary>

- [x] Phase 6: Ports & DTOs (3/3 plans) — completed 2026-09-26
- [x] Phase 7: Captions Adapter (3/3 plans) — completed 2026-09-26
- [x] Phase 8: DeepSeek Article & Templates (4/4 plans) — completed 2026-09-27
- [x] Phase 9: Draft Persist & Shortlist Enqueue (4/4 plans) — completed 2026-09-27
- [x] Phase 10: CLI Composition & UAT (5/5 plans) — completed 2026-10-01
- [x] Phase 11: Captions diagnostics & persist error classification (4/4 plans) — completed 2026-10-02

Full phase detail: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)

</details>

<details>
<summary>✅ v1.2 Admin UX + diagnostics + PIPE-01 MVP (Phases 12-16) — SHIPPED 2026-10-05</summary>

- [x] Phase 12: Admin shortlist empty-batch contract (3/3 plans) — completed 2026-10-02
- [x] Phase 13: Admin material & email preview honesty (8/8 plans) — completed 2026-10-03
- [x] Phase 14: Draft→ready & justification honesty (8/8 plans) — completed 2026-10-04
- [x] Phase 15: CLI --debug diagnostics (3/3 plans) — completed 2026-10-04
- [x] Phase 16: PIPE-01 MVP config UI (4/4 plans) — completed 2026-10-05

Full phase detail: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)

</details>

<details>
<summary>✅ v1.3 Live mail, scheduled ingestion & backlog debt (Phases 17-24) — SHIPPED 2026-10-18</summary>

- [x] Phase 17: YAML merge-key acceptance in the strict validator (3/3 plans) — completed 2026-10-14
- [x] Phase 18: Reader-route honesty for draft materials (3/3 plans) — completed 2026-10-15
- [x] Phase 19: Unsaved-changes guard for the pipeline editor (2/2 plans) — completed 2026-10-16
- [x] Phase 20: MAIL-02 signup confirmation mail (2/2 plans) — completed 2026-10-16
- [x] Phase 21: MAIL-01 live SMTP digest delivery (3/3 plans) — completed 2026-10-18
- [x] Phase 22: Admin nav grouping (3/3 plans) — completed 2026-10-17
- [x] Phase 23: Admin-managed ingest sources (4/4 plans) — completed 2026-10-17
- [x] Phase 24: Scheduled ingestion (8/8 plans) — completed 2026-10-18

Full phase detail: [milestones/v1.3-ROADMAP.md](milestones/v1.3-ROADMAP.md)

</details>

## Backlog

> **Triaged 2026-10-13** (`/gsd-review-backlog`).
> - **Queued for v1.3** — Bucket A tech debt; promote with `/gsd-new-milestone` (next free phase numbers 17+).
> - **Deferred** — product preference, not debt.
> - **Removed 2026-10-13** — former 999.2 (merged into 999.1, identical root cause) and former 999.3 (stale: fixed by the global `@layer base button:not(:disabled) { cursor: pointer }` rule shipped in v1.2 Phase 15).
>
> **Moved into v1.3 (2026-10-14):** 999.7 → Phase 17 · 999.1 → Phase 18 · 999.6 → Phase 19 · 999.5 → Phase 22. **999.4 stays parked** (product preference, not debt).

### Backlog 999.1: Reader-route honesty for draft materials — `/materials/<slug>` error page (→ v1.3 Phase 18)

**Goal:** A reader link opened from the admin shortlist or the email preview must not land on an error page while the material is still a draft
**Source phase:** 13
**Tech-debt id:** `W-1` (`.planning/milestones/v1.2-MILESTONE-AUDIT.md`)
**Deferred at:** 2026-10-03 during /gsd-verify-work 13 session completion
**Merged:** former 999.2 folded in on 2026-10-13 — identical root cause (`GET /materials/{slug}` is ready-only → 404)
**Follow-ups:**
- [ ] Reader `/materials/<slug>` returns an error page. Check: slug validity, reader endpoint health, SPA route. (deferred 2026-10-03)
- [ ] «Открыть материал →» from the email/admin preview leads to an error page — reader route issue, not admin preview. (deferred 2026-10-03)

### Backlog 999.4: Follow-up — Phase 14 deferred UAT follow-up: Test 1 (Deferred — stays parked)

**Goal:** Resolve the UAT checkpoint deferred during Phase 14 verification
**Source phase:** 14
**Triaged:** 2026-10-13 — product preference, not tech debt; stays parked
**Deferred at:** 2026-10-04 during /gsd-verify-work 14 session completion
**Follow-ups:**
- [ ] Test 1: UX (для Phase 15+): две операции на одно editorial-решение избыточны для single-operator workflow — объединить Approve (decision) + Mark ready (material_status) в одну кнопку «Одобрить и подготовить → ready»; переименовать «Сделать ready» → «Отобрать», ready → «Отобран». (deferred 2026-10-03)

### Backlog 999.5: Follow-up — Phase 16 deferred UAT follow-up: admin nav grouping (→ v1.3 Phase 22)

**Goal:** Resolve the UAT checkpoint deferred during Phase 16 verification
**Source phase:** 16
**Triaged:** 2026-10-13 — product preference, not debt; promoted into v1.3 as Phase 22 (own separate phase, immediately before the sources phase)
**Deferred at:** 2026-10-04 during /gsd-verify-work 16 session completion
**Follow-ups:**
- [ ] Test 0: UX (предпочтение, не SPEC): убрать top-level nav-пункт «Пайплайн»; открывать конфиг только из админ-раздела. Вариант C — tab-bar «Дайджест | Пайплайн» на админ-страницах, top-level «Админ» → /admin/digest. Route /admin/pipeline не меняется, новый route не нужен. При реализации обновить 16-UI-SPEC A-2 и писать TDD (failing Playwright test first). (deferred 2026-10-04)

### Backlog 999.6: Follow-up — Phase 16 deferred UAT follow-up: unsaved-changes guard WR-04/WR-05 (→ v1.3 Phase 19)

**Goal:** Resolve the UAT checkpoint deferred during Phase 16 verification
**Source phase:** 16
**Tech-debt ids:** `WR-04`, `WR-05` (`16-REVIEW-DISPOSITION.md` — both an accepted known limitation)
**Deferred at:** 2026-10-04 during /gsd-verify-work 16 session completion
**Follow-ups:**
- [ ] Test 3: WR-04/WR-05 — unsaved-changes guard принят как known limitation: window.confirm внутри beforeunload ненадёжен в реальных браузерах, router-level guard не зарегистрирован, поэтому in-app SPA-навигация молча теряет черновик. БД безопасна (не сохранил → не записано); теряется только набранный текст. Fix: корректный beforeunload (event.preventDefault/returnValue) + router guard (useBlocker) с той же копией «Есть несохранённые изменения. Уйти без сохранения?». (deferred 2026-10-04)
- [ ] ADUX-10 — extend the guard to the ingest-sources editor; owned by v1.3 Phase 23 (sources), not Phase 19.

### Backlog 999.7: Follow-up — Phase 16 code-review advisory WR-01: YAML merge-key regression (→ v1.3 Phase 17)

**Goal:** Restore valid YAML merge-key (`<<`) acceptance in the strict pipeline-config validator without weakening duplicate-key rejection
**Source phase:** 16
**Tech-debt id:** `999.7` (`v1.2-MILESTONE-AUDIT.md` — `WR-01`, fails closed)
**Deferred at:** 2026-10-05 at v1.2 milestone close
**Follow-ups:**
- [ ] WR-01: `_StrictSafeLoader.construct_mapping` pre-constructs key nodes before `flatten_mapping`, so a valid YAML merge-key document (`<<`) is rejected with a cryptic internal-tag error instead of merging. Fails closed (still a structured 400 `{errors:[...]}`, zero writes) and the fixed 4-key `extra="forbid"` schema cannot yield a valid config from such a document, so it is not a v1.2 must-have. Fix: run `flatten_mapping` (or pre-resolve merge keys) BEFORE duplicate-key detection so `<<` documents behave like `SafeLoader` while duplicate-key rejection stays intact. Advisory only — fails closed. (deferred 2026-10-05)

### Backlog 999.2: Follow-up — Phase 23 deferred UAT follow-up: Test 1 (BACKLOG)

**Goal:** Resolve the UAT checkpoint deferred during Phase 23 verification
**Source phase:** 23
**Deferred at:** 2026-10-17 during /gsd-verify-work 23 session completion
**Follow-ups:**
- [ ] Test 1: AdminLayout chrome: убрать надпись «АДМИН» над вкладками Дайджест|Пайплайн; уменьшить пустоту сверху; уменьшить кегль вкладок до уровня остальных заголовков (как «Источники ингеста»); чуть увеличить расстояние между вкладками Дайджест и Пайплайн (deferred 2026-10-17)

### Backlog 999.3: Follow-up — Phase 21 deferred UAT follow-up: Test 6 (DONE 2026-10-18)

**Goal:** Resolve the UAT checkpoint deferred during Phase 21 verification
**Source phase:** 21
**Deferred at:** 2026-10-18 during /gsd-verify-work 21 session completion
**Resolved at:** 2026-10-18 — MAILER confirmed account; live digest send works; UAT Test 6 pass
**Follow-ups:**
- [x] Test 6: Живой smoke Haskimail (ADR-0005): верифицировать учётную запись MAILER / HASKIMAIL_FROM и повторить реальную отправку дайджеста. (resolved 2026-10-18)
