# Phase 2: Issue, Materials & Archive - Context

**Gathered:** 2026-09-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Readers open the **current published issue** (cover/period/title as typography hero + IssueTOC), read **prepared articles** as markdown prose with section TOC («Статья» badge, provenance, tags/related only when present), and open **past issues from `/archive`**. Empty current → «выпуск готовится»; empty archive → CTA to current. Voting callout on current issue reflects open vs closed from a **read-only** cycle DTO (no cast/change vote — Phase 3). Live content behind the same `VITE_USE_MOCKS` flag as Phase 1 auth.

</domain>

<decisions>
## Implementation Decisions

### Live cutover for issue/materials
- **D-20:** Same `VITE_USE_MOCKS` controls issue + materials (and archive): `true` → offline mocks for Playwright; `false` → live FastAPI content APIs. — **Reversibility:** costly — second content flag later would split env and tests.
- **D-21:** Live API failure (network / 5xx): **ErrorPanel + Retry**; never silent fallback to mock content.
- **D-22:** Page-level load failures use friendly splash art `bad_gateway.png` (move into `web/public/` or equivalent static asset). Material **404** stays editorial **without** that art.
- **D-23:** UI shows **friendly copy only** under the art («Не удалось загрузить…»); never HTTP status codes or stacktraces on screen (details stay in logs).

### Current issue + seed
- **D-24:** Current issue = latest `digest_issues` row with `published_at` set (`ORDER BY published_at DESC LIMIT 1`). No `is_current` flag in Phase 2.
- **D-25:** Idempotent **checked-in SQL seed** derived from today's `mock.js` content; apply via MCP/psql; document in runbook (shared VM — no reckless resets).
- **D-26:** **Typography-only** issue hero (number / period / title); no `cover_url` migration in Phase 2. Material card covers may remain from seed assets if present.
- **D-27:** Seed includes **current issue + one past published issue** so archive is demonstrable.

### Archive & empty CTAs
- **D-28:** New route **`/archive`** + AppShell nav «Архив»; archive page includes clear link **«К текущему выпуску»** → `/`.
- **D-29:** Opening a past issue uses the **same IssuePage layout** at `/issues/:id` (or equivalent id/number route).
- **D-30:** Empty current («выпуск готовится») CTA → `/archive` (and/or knowledge as secondary if already natural); empty archive CTA → `/`.
- **D-31:** Archive list = **past published only** (excludes current).

### Voting callout (ISSUE-02)
- **D-32:** **Honest stub until Phase 3** — no vote cast/change API in Phase 2.
- **D-33:** Open/closed + end date on **current-issue API DTO**, sourced from existing `voting_cycles` (seed one cycle). SPA only renders EditorialCallout.
- **D-34:** EditorialCallout **only on current `/`** — never on past `/issues/:id`.
- **D-35:** When open, CTA «Выбрать тему →» links to **`/voting`** (mock ballot OK until Phase 3). Closed → closed messaging, no topic-select CTA.

### Material honesty
- **D-36:** Empty audit-dek → **hide dek block** entirely (no neutral stub sentence).
- **D-37:** Tags / related links: render **only what API returns**; omit empty sections; **never fabricate** related links (MAT-03).
- **D-38:** SPA renders `body_markdown` → prose HTML + **section TOC from headings** (MAT-01). Format remains «статья» only.
- **D-39:** Unknown/unpublished id → **soft editorial 404** («материал не найден») with calm back-nav to issue/archive — understandable, not harsh; no `bad_gateway.png`.

### Claude's Discretion
- Exact route param shape (`/issues/:id` vs number), markdown library choice, seed file layout under `supabase-integration/`, and ErrorPanel vs dedicated ServiceUnavailable component structure — planner/researcher within Ports & Adapters + TDD.
- Secondary empty-current CTA to knowledge if it fits existing nav without new scope.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria, ISSUE-*/MAT-* mapping
- `.planning/REQUIREMENTS.md` — ISSUE-01…04, MAT-01…03
- `.planning/PROJECT.md` — core value, constraints
- `CONTEXT.md` — domain language (выпуск, материал = подготовленная статья, etc.)

### Prior phase decisions
- `.planning/phases/01-platform-foundation-auth/01-CONTEXT.md` — D-09 mocks, D-12 post-login → issue, JWT/API patterns
- `.planning/phases/01-platform-foundation-auth/01-VERIFICATION.md` — Phase 1 PASS_WITH_GAPS

### Specs & UX
- `docs/digest-cds/acceptance_criteria.md` — US-03…05, US-07…09, US-28
- `docs/digest-cds/error_handling.md` — banners, Retry, 404 editorial tone
- `docs/digest-cds/user_stories.md` — ISSUE/MAT stories
- `docs/digest-cds/technical_specification.md` — stack/NFR overview

### Schema & architecture
- `supabase-integration/migrations/001_initial_schema.sql` — `digest_issues`, `digest_issue_items`, `materials`, `material_tags`, `material_relations`, `voting_cycles`
- `.cursor/rules/architecture.mdc` — Ports & Adapters; composition root only
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `.planning/codebase/STRUCTURE.md`, `ARCHITECTURE.md`, `CONVENTIONS.md`

### Assets
- `bad_gateway.png` (repo root today) — relocate under `web/public/` (or agreed static path) for Vite; friendly load-failure splash

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `web/src/pages/IssuePage.jsx`, `MaterialPage.jsx`, `IssueToc`, `EditorialCallout` — wire to services instead of `mock.js` when live
- `web/src/data/mock.js` — source narrative for SQL seed + offline mocks
- `web/src/services/` + `VITE_USE_MOCKS` / `authEnv.js` patterns from Phase 1
- `backend/.../composition/` live vs memory container — extend with issue/material ports
- Domain already has `Material` entity / publish use-cases — align or extend carefully

### Established Patterns
- TDD: pytest for API/ports; Playwright for reader flows
- UI consumes DTOs only; no business rules in React components
- JWT `Authorization: Bearer` for authenticated reads

### Integration Points
- Routes: `/`, new `/archive`, `/issues/:id`, `/materials/:id`; AppShell nav
- New ports: issue repository / material reader; adapters in `supabase-integration/`
- Seed SQL + runbook update (apply on shared VM once)

</code_context>

<specifics>
## Specific Ideas

- Error splash: cartoon kitten («Упс. / Ошибочка вышла.») from `bad_gateway.png` — warm, non-technical; user explicitly rejected raw 502/stacktraces.
- Soft material-not-found: clear and gentle, not alarming (no red panic UI).
- Archive must offer return path to current issue when user is on `/archive`.

</specifics>

<deferred>
## Deferred Ideas

- Vote cast / change / ballot honesty — Phase 3
- Admin shortlist → publish — Phase 5
- Issue `cover_url` / hero image migration — later polish
- Separate `VITE_USE_CONTENT_MOCKS` flag — not chosen
- Live voting cycle write APIs — Phase 3
- Logout UI button — Phase 1 gap, still non-blocking
- Knowledge empty-CTA as primary — optional secondary only

</deferred>

---

*Phase: 2-Issue, Materials & Archive*
*Context gathered: 2026-09-19*
