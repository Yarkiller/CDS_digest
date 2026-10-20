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

> **Reviewed 2026-10-20** (`/gsd-review-backlog`) — v1.3 shipped 2026-10-18.
> - **Closed and removed** — 999.7 → Phase 17 · 999.1 → Phase 18 · 999.6 → Phase 19 (ADUX-10 → Phase 23) · 999.5 → Phase 22 · 999.3 resolved 2026-10-18.
> - **Open** — 999.2: AdminLayout chrome polish; candidate for the next milestone.
> - **Parked** — 999.4: product preference, not debt.

### Backlog 999.2: Follow-up — Phase 23 deferred UAT follow-up: AdminLayout chrome

**Goal:** Resolve the UAT checkpoint deferred during Phase 23 verification
**Source phase:** 23
**Deferred at:** 2026-10-17 during /gsd-verify-work 23 session completion
**Status:** open — re-checked 2026-10-20 against `web/src/components/AdminLayout.jsx`: the «Админ» label, the `text-3xl` tab size and the `mt-2`/`gap-2` spacing are all still as described
**Follow-ups:**
- [ ] Test 1: AdminLayout chrome: убрать надпись «АДМИН» над вкладками Дайджест|Пайплайн; уменьшить пустоту сверху; уменьшить кегль вкладок до уровня остальных заголовков (как «Источники ингеста»); чуть увеличить расстояние между вкладками Дайджест и Пайплайн (deferred 2026-10-17)

### Backlog 999.4: Follow-up — Phase 14 deferred UAT follow-up: Test 1 (Deferred — stays parked)

**Goal:** Resolve the UAT checkpoint deferred during Phase 14 verification
**Source phase:** 14
**Triaged:** 2026-10-13 — product preference, not tech debt; stays parked
**Deferred at:** 2026-10-04 during /gsd-verify-work 14 session completion
**Follow-ups:**
- [ ] Test 1: UX (для Phase 15+): две операции на одно editorial-решение избыточны для single-operator workflow — объединить Approve (decision) + Mark ready (material_status) в одну кнопку «Одобрить и подготовить → ready»; переименовать «Сделать ready» → «Отобрать», ready → «Отобран». (deferred 2026-10-03)
