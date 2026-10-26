# Phase 2: Issue, Materials & Archive - Research

**Researched:** 2026-09-19
**Domain:** Editorial reader APIs + SPA (issue / material / archive) on existing FastAPI + Supabase + React/Vite stack
**Confidence:** HIGH (architecture & schema); MEDIUM (markdown package stack — Context7-verified APIs, classify-confidence MEDIUM)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-20:** Same `VITE_USE_MOCKS` controls issue + materials (and archive): `true` → offline mocks for Playwright; `false` → live FastAPI content APIs. — **Reversibility:** costly — second content flag later would split env and tests.
- **D-21:** Live API failure (network / 5xx): **ErrorPanel + Retry**; never silent fallback to mock content.
- **D-22:** Page-level load failures use friendly splash art `bad_gateway.png` (move into `web/public/` or equivalent static asset). Material **404** stays editorial **without** that art.
- **D-23:** UI shows **friendly copy only** under the art («Не удалось загрузить…»); never HTTP status codes or stacktraces on screen (details stay in logs).
- **D-24:** Current issue = latest `digest_issues` row with `published_at` set (`ORDER BY published_at DESC LIMIT 1`). No `is_current` flag in Phase 2.
- **D-25:** Idempotent **checked-in SQL seed** derived from today's `mock.js` content; apply via MCP/psql; document in runbook (shared VM — no reckless resets).
- **D-26:** **Typography-only** issue hero (number / period / title); no `cover_url` migration in Phase 2. Material card covers may remain from seed assets if present.
- **D-27:** Seed includes **current issue + one past published issue** so archive is demonstrable.
- **D-28:** New route **`/archive`** + AppShell nav «Архив»; archive page includes clear link **«К текущему выпуску»** → `/`.
- **D-29:** Opening a past issue uses the **same IssuePage layout** at `/issues/:id` (or equivalent id/number route).
- **D-30:** Empty current («выпуск готовится») CTA → `/archive` (and/or knowledge as secondary if already natural); empty archive CTA → `/`.
- **D-31:** Archive list = **past published only** (excludes current).
- **D-32:** **Honest stub until Phase 3** — no vote cast/change API in Phase 2.
- **D-33:** Open/closed + end date on **current-issue API DTO**, sourced from existing `voting_cycles` (seed one cycle). SPA only renders EditorialCallout.
- **D-34:** EditorialCallout **only on current `/`** — never on past `/issues/:id`.
- **D-35:** When open, CTA «Выбрать тему →» links to **`/voting`** (mock ballot OK until Phase 3). Closed → closed messaging, no topic-select CTA.
- **D-36:** Empty audit-dek → **hide dek block** entirely (no neutral stub sentence).
- **D-37:** Tags / related links: render **only what API returns**; omit empty sections; **never fabricate** related links (MAT-03).
- **D-38:** SPA renders `body_markdown` → prose HTML + **section TOC from headings** (MAT-01). Format remains «статья» only.
- **D-39:** Unknown/unpublished id → **soft editorial 404** («материал не найден») with calm back-nav to issue/archive — understandable, not harsh; no `bad_gateway.png`.

### Claude's Discretion
- Exact route param shape (`/issues/:id` vs number), markdown library choice, seed file layout under `supabase-integration/`, and ErrorPanel vs dedicated ServiceUnavailable component structure — planner/researcher within Ports & Adapters + TDD.
- Secondary empty-current CTA to knowledge if it fits existing nav without new scope.

### Deferred Ideas (OUT OF SCOPE)
- Vote cast / change / ballot honesty — Phase 3
- Admin shortlist → publish — Phase 5
- Issue `cover_url` / hero image migration — later polish
- Separate `VITE_USE_CONTENT_MOCKS` flag — not chosen
- Live voting cycle write APIs — Phase 3
- Logout UI button — Phase 1 gap, still non-blocking
- Knowledge empty-CTA as primary — optional secondary only
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ISSUE-01 | Authenticated user opens current published issue with cover, period/title, and IssueTOC; empty materials show «выпуск готовится» + CTA | D-24/D-26 override “cover” → typography hero; `GET /issues/current` + IssueToc; empty-state copy from 02-UI-SPEC |
| ISSUE-02 | Open voting cycle shows EditorialCallout with end date and CTA; closed cycle shows closed messaging without topic-select CTA | D-32–D-35: read-only `voting_cycle` on current-issue DTO; no vote write APIs |
| ISSUE-03 | Material with audit-dek shows 1–2 audit-language sentences under title; missing dek hides stub | D-36 wins over REQUIREMENTS “neutral fallback”: hide dek block when empty |
| ISSUE-04 | User can open a past issue from archive; empty archive shows CTA to current issue | `/archive` + `GET` archive list excluding current; `/issues/:number` same IssuePage |
| MAT-01 | Opening a material shows prepared article in prose column with section TOC; no raw media | `body_markdown` → `react-markdown` + heading TOC; format check `статья` only |
| MAT-02 | Article distinguishable as «статья»; unknown id → «материал не найден» + back nav | Soft 404 for missing/draft; badge always «Статья» |
| MAT-03 | Badge, provenance, tags when present, related links without fabricating | Optional DTO fields; omit empty sections; relations only if target ready |
</phase_requirements>

## Summary

Phase 2 wires the existing mock Issue/Material UI to **JWT-protected FastAPI content reads** backed by the already-applied Supabase schema (`digest_issues`, `digest_issue_items`, `materials`, tags/relations, `voting_cycles`). Live cutover reuses the Phase 1 `VITE_USE_MOCKS` gate (D-20): mocks stay default for Playwright; `false` hits live APIs with **ErrorPanel + Retry + `bad_gateway.png`** on network/5xx (never silent mock fallback). Current issue is computed as latest published row (D-24); archive lists past published only; EditorialCallout is a **read-only cycle stub** on `/` only.

Brownfield gaps the planner must close: (1) `live.py` still wires **in-memory** materials — need real Supabase adapters; (2) SPA routes lack `/archive` and `/issues/:…`; (3) MaterialPage still renders mock `body[]` paragraphs, not markdown; (4) RLS enables `voting_cycles` / `material_tags` / `material_relations` **without SELECT policies** — content reads must go through FastAPI + `service_role`, not the browser Supabase client; (5) checked-in SQL seed from `mock.js` for shared VM (idempotent, documented).

**Primary recommendation:** Add `IssueRepository` + reader use-cases + thin FastAPI routes (`/issues/current`, `/issues/{number}`, `/archive`, `/materials/{slug}`); extend SPA services with the same mock/live pattern as `meApi.js`; render markdown with `react-markdown` + `remark-gfm` + `rehype-slug` (+ `rehype-sanitize`); seed two published issues + one voting cycle.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Current / past issue assembly (published filter, TOC order) | API / Backend | Database / Storage | Business rule D-24/D-31 lives in use-case; Postgres stores rows |
| Voting open/closed stub DTO | API / Backend | Database / Storage | D-33: cycle fields on issue DTO; SPA only renders |
| Material readiness gate (draft → soft 404) | API / Backend | Database / Storage | Never leak draft; map to 404 at HTTP edge |
| Markdown → prose HTML + section TOC | Browser / Client | — | D-38: SPA renders `body_markdown`; TOC from headings |
| Empty / error / soft-404 UX | Browser / Client | — | Copy + splash per 02-UI-SPEC; no status codes on screen |
| Auth gate for content routes | API / Backend | Browser / Client | Reuse `get_principal`; RequireAuth already wraps shell |
| Seed content for demo | Database / Storage | — | Idempotent SQL; apply via MCP/psql once on shared VM |
| Mock offline Playwright path | Browser / Client | — | `VITE_USE_MOCKS` default true (D-20 / D-09) |

## Project Constraints (from .cursor/rules/)

| Rule | Directive for planner |
|------|----------------------|
| `architecture.mdc` | Ports & Adapters; no Supabase/httpx in use-cases; adapters in `supabase-integration/`; wiring only in `composition/`; FE via `web/src/services/` only |
| `tdd.mdc` / `AGENTS.md` | **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**; pytest unit + Playwright e2e |
| `python-uv.mdc` | Python deps only via `uv add` / `uv sync` (no new PyPI packages expected this phase unless JWT/stack already covered) |

Project skills to respect: `.agents/skills/supabase/SKILL.md` (service_role never in Vite; RLS traps; shared VM no reckless resets); hallmark if present for editorial tone — reuse locked 02-UI-SPEC copy.

## Standard Stack

### Core (already in repo — do not replace)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | in-repo (Phase 1) | Content GET routes + JWT deps | Existing `create_app` / `get_principal` |
| React + Vite | react `^19.2.8`, vite `^8.2.2` [VERIFIED: web/package.json] | SPA | Phase 1 FE |
| react-router-dom | `^7.18.3` [VERIFIED: web/package.json] | `/`, `/archive`, `/issues/:number`, `/materials/:slug` | Existing router |
| @supabase/supabase-js | `^2.116.0` [VERIFIED: web/package.json] | Auth session only (not content reads) | D-11 pattern |
| Playwright | `^1.62.1` [VERIFIED: package.json] | Reader e2e | Existing `tests/web-app.spec.js` |
| pytest + uv | uv `0.10.9` [VERIFIED: env probe] | Unit/API tests | `npm run test:unit` |

### Supporting (new npm — Phase 2 markdown)

| Library | Version (npm view 2026-09-19) | Purpose | When to Use |
|---------|-------------------------------|---------|-------------|
| `react-markdown` | **10.1.0** [VERIFIED: npm registry + legitimacy OK] | Render `body_markdown` to React | Material page prose |
| `remark-gfm` | **4.0.1** [VERIFIED: npm registry + legitimacy OK] | GFM tables/strikethrough if present in seed | `remarkPlugins={[remarkGfm]}` |
| `rehype-slug` | **6.0.0** [VERIFIED: npm registry + legitimacy OK] | Stable heading `id`s for TOC anchors | Section TOC (MAT-01) |
| `rehype-sanitize` | **6.0.0** [VERIFIED: npm registry + legitimacy OK] | Defense-in-depth after plugins | Recommended even for trusted editorial markdown [CITED: remarkjs/react-markdown readme Security] |

**Install (web workspace):**
```bash
npm install react-markdown remark-gfm rehype-slug rehype-sanitize --prefix web
```

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `react-markdown` | `marked` + `dangerouslySetInnerHTML` | Faster but XSS footgun; violates “don’t hand-roll sanitize” |
| `rehype-slug` | Hand-rolled slugify in `components.h2` | Duplicate edge cases (unicode, collisions); rehype-slug is standard |
| FastAPI content APIs | Direct Supabase Data API from SPA | Blocked by missing RLS SELECT on tags/relations/cycles; leaks service concerns into UI |

**No new PyPI packages required** for Phase 2 content reads — extend existing backend modules.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| react-markdown | npm | published 2025-03-07 | ~24.8M/wk | github.com/remarkjs/react-markdown | OK | Approved |
| remark-gfm | npm | published 2025-02-10 | ~28.8M/wk | github.com/remarkjs/remark-gfm | OK | Approved |
| rehype-slug | npm | published 2023-08-31 | ~2.7M/wk | github.com/rehypejs/rehype-slug | OK | Approved |
| rehype-sanitize | npm | published 2023-08-26 | ~7.7M/wk | github.com/rehypejs/rehype-sanitize | OK | Approved |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none  
**postinstall scripts:** none on audited packages [VERIFIED: npm view / legitimacy seam]

## Architecture Patterns

### System Architecture Diagram

```text
                    ┌─────────────────────────────────────────┐
                    │ SPA (RequireAuth + AppShell)            │
                    │  /  /archive  /issues/:number           │
                    │  /materials/:slug                       │
                    └───────────────┬─────────────────────────┘
                                    │ Bearer JWT
                         VITE_USE_MOCKS?
                      ┌─────────────┴─────────────┐
                      │ true                      │ false
                      ▼                           ▼
               mock.js DTOs              contentApi.js → FastAPI
                                                    │
                                    ┌───────────────▼───────────────┐
                                    │ interface/http (thin)         │
                                    │ get_principal → use_cases     │
                                    └───────────────┬───────────────┘
                                                    │ ports
                                    ┌───────────────▼───────────────┐
                                    │ IssueRepository               │
                                    │ MaterialRepository (extended) │
                                    │ VotingCycleReader (read-only) │
                                    └───────────────┬───────────────┘
                                                    │ composition/live.py
                                    ┌───────────────▼───────────────┐
                                    │ supabase-integration adapters │
                                    │ service_role client           │
                                    │ digest_issues / materials /   │
                                    │ voting_cycles (+ joins)       │
                                    └───────────────────────────────┘
```

### Recommended Project Structure

```text
backend/src/backend/
  application/ports/
    issue_repository.py          # NEW Protocol
    voting_cycle_reader.py       # NEW Protocol (or method on issue port)
  application/use_cases/
    get_current_issue.py         # NEW
    get_issue_by_number.py       # NEW
    list_archive_issues.py       # NEW
    get_material_for_reader.py   # NEW (ready-only by slug)
  interface/http/routes/
    issues.py                    # NEW
    materials.py                 # NEW
  tests_support/in_memory.py     # extend fakes
supabase-integration/
  src/supabase_integration/
    issue_repository.py          # NEW adapter
    material_repository.py       # NEW/extend (live materials)
  migrations/
    002_phase2_issue_seed.sql    # NEW idempotent seed (with schema migrations)
web/src/
  services/contentApi.js         # NEW (mock/live like meApi)
  pages/ArchivePage.jsx          # NEW
  pages/IssuePage.jsx            # wire services; current vs past
  pages/MaterialPage.jsx         # markdown + TOC + soft-404
  components/ServiceUnavailable.jsx  # OR extend ErrorPanel (discretion)
  utils/markdownToc.js           # heading extract for TOC
web/public/bad_gateway.png       # relocate from repo root
```

### Pattern 1: Content service cutover (mirror meApi)

**What:** Single `isMocksEnabled()` / `VITE_USE_MOCKS !== 'false'` gate; live path `fetch` + `Authorization: Bearer`; map failures to typed errors with `retryable` — never catch and return mock data.

**When to use:** All issue/material/archive reads (D-20, D-21).

**Example (shape):**
```javascript
// Mirror web/src/services/meApi.js — useMocks() then fetch(`${apiBase()}/issues/current`, { headers: { Authorization: `Bearer ${token}` } })
// On !response.ok / network → throw ContentApiError({ retryable: true }); on 404 material → soft-404 code, not splash
```

### Pattern 2: Ports & use-cases for read models

**What:** Use-cases return explicit DTOs / domain objects; HTTP maps `MaterialNotFoundError` → 404; adapters map SDK errors → `PersistenceError`.

**When to use:** Every DB-backed read.

### Pattern 3: Soft 404 vs load failure

**What:** HTTP 404 / domain not-found → editorial empty (D-39). Network/5xx → splash + Retry (D-21–23). Never conflate.

### Anti-Patterns to Avoid

- **Silent mock fallback on live failure** — violates D-21.
- **Supabase client content reads from SPA** — RLS gaps on tags/relations/cycles; architecture forbids UI knowing DB.
- **Business rules in React** (current = max published_at, archive exclude current) — compute on backend.
- **Showing draft materials as 403** — use soft 404 (error_handling §2.3 / D-39).
- **Fabricating related links or dek stubs** — D-36/D-37.
- **`rehype-raw` without sanitize** — XSS vector [CITED: react-markdown Security / remark-rehype].
- **Schema migration for `cover_url` / `is_current`** — explicitly deferred (D-24, D-26).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown → React | Custom regex HTML | `react-markdown` | Plugin ecosystem, default XSS resistance |
| Heading ids / TOC slugs | Ad-hoc slugify | `rehype-slug` | Collision handling, unicode |
| JWT verification | New auth path | Existing `get_principal` | Phase 1 already hardened |
| Content mock flag | Second env var | `VITE_USE_MOCKS` | D-20 locked |
| Vote APIs | Partial ballot backend | Stub DTO only | D-32 / Phase 3 |

**Key insight:** Phase 2 is a **read-model cutover**, not a new product surface — reuse Phase 1 auth/composition/testing patterns and only add ports + routes + SPA services.

## Common Pitfalls

### Pitfall 1: Treating REQUIREMENTS “cover” / dek fallback as binding
**What goes wrong:** Planner adds cover image or stub dek sentence.
**Why it happens:** ISSUE-01/ISSUE-03 wording vs CONTEXT overrides.
**How to avoid:** Honor D-26 / D-36; 02-UI-SPEC is the visual contract.
**Warning signs:** `cover_url` migration PR; “Нет описания” placeholder under title.

### Pitfall 2: SPA → Supabase for issues/materials
**What goes wrong:** Empty tags/relations/cycles or silent RLS denials.
**Why it happens:** RLS enabled on `voting_cycles`, `material_tags`, `material_relations` with **no SELECT policies** [VERIFIED: supabase-integration/migrations/001_initial_schema.sql:245-293 — policies listed for materials/issues/items/votes/profiles only].
**How to avoid:** FastAPI + `service_role` adapters only (same as Phase 1 profiles/pings).
**Warning signs:** Browser network tab hitting `/rest/v1/voting_cycles`.

### Pitfall 3: Leaving live container on InMemoryMaterialRepository
**What goes wrong:** Live FE proof shows empty/wrong content while DB has seed.
**Why it happens:** `build_live_container` currently keeps materials in-memory [VERIFIED: backend/src/backend/composition/live.py:39-44].
**How to avoid:** Wire Supabase material/issue adapters in `live.py` this phase.
**Warning signs:** `APP_CONTAINER=live` but materials still from empty InMemory.

### Pitfall 4: Slug vs bigint id mismatch
**What goes wrong:** Playwright `/materials/rag-systems` breaks after API switch.
**Why it happens:** Mock IDs are string slugs; DB `materials.id` is bigint identity, `slug` is unique text [VERIFIED: 001_initial_schema.sql:89-95].
**How to avoid:** Route param = **slug**; API `GET /materials/{slug}`; seed slugs from mock ids.
**Warning signs:** Numeric-only material URLs in e2e.

### Pitfall 5: Archive includes current issue
**What goes wrong:** Duplicate “current” card; D-31 violation.
**How to avoid:** Archive query `published_at IS NOT NULL` AND `id <> current.id` (or `number <> current.number`).
**Warning signs:** Archive card labeled «текущий» (design-frontend had this — do **not** copy for Phase 2 archive).

### Pitfall 6: Shared VM destructive seed
**What goes wrong:** Wipe other developers’ data.
**How to avoid:** Idempotent `INSERT … ON CONFLICT` / fixed slugs & issue numbers; runbook “apply once”; no `TRUNCATE`.
**Warning signs:** Seed script with `DELETE FROM materials`.

### Pitfall 7: EditorialCallout on past issues
**What goes wrong:** ISSUE-02 / D-34 failure.
**How to avoid:** Pass `showVotingCallout={isCurrent}` only on `/` route component.

## Code Examples

### react-markdown + GFM + slug + sanitize

```jsx
// Source: Context7 /remarkjs/react-markdown readme (remarkGfm, Security, rehypeSanitize order)
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeSlug from 'rehype-slug'
import rehypeSanitize from 'rehype-sanitize'

<Markdown
  remarkPlugins={[remarkGfm]}
  rehypePlugins={[rehypeSlug, rehypeSanitize]}
>
  {material.body_markdown}
</Markdown>
```

### FastAPI 404 for missing resource

```python
# Source: Context7 FastAPI docs — HTTPException 404 pattern
from fastapi import HTTPException

if material is None:
    raise HTTPException(status_code=404, detail="material_not_found")
```

Reuse Phase 1 bearer dependency:

```python
# Existing: backend/src/backend/interface/http/deps.py
# get_principal(...) → AccessTokenClaims; attach Depends(get_principal) on content routes
```

### Schema facts (verbatim) for planner DTOs

`digest_issues` columns [VERIFIED: 001_initial_schema.sql:124-131]:
> `id bigint …`, `number int not null unique`, `period_label text not null`, `title text not null`, `published_at timestamptz`, `created_at timestamptz`

`materials` format check [VERIFIED: 001_initial_schema.sql:95]:
> `format text not null default 'статья' check (format = 'статья')`

`material_status` enum [VERIFIED: 001_initial_schema.sql:14]:
> `create type material_status as enum ('draft', 'ready');`

`voting_cycle_status` enum [VERIFIED: 001_initial_schema.sql:29]:
> `create type voting_cycle_status as enum ('open', 'closed');`

`VITE_USE_MOCKS` helper [VERIFIED: web/src/services/authEnv.js:6-12]:
> `return value === undefined || value === '' || value === 'true'`

## State of the Art

| Old Approach (brownfield today) | Current Approach (Phase 2) | When Changed | Impact |
|---------------------------------|----------------------------|--------------|--------|
| Issue/Material from `mock.js` only | FastAPI read APIs + mock gate | Phase 2 | Live editorial reader |
| Material `body: string[]` | `body_markdown` prose | Phase 2 | MAT-01 TOC from headings |
| No `/archive` route | `/archive` + nav | Phase 2 | ISSUE-04 |
| Live container: in-memory materials | Supabase material/issue adapters | Phase 2 | Real seed visible |

**Deprecated/outdated:**
- MaterialPage cover `<img>` as primary content chrome — optional seed asset only; prose is source of truth (MAT-01).
- design-frontend archive card marking «текущий» inside archive grid — contradicts D-31.

## Discretion Recommendations (planner defaults)

| Topic | Recommendation | Confidence |
|-------|----------------|------------|
| Issue route | `/issues/:number` where `number` is `digest_issues.number` (human №) | HIGH — matches UI overline «Выпуск №» |
| Material route | Keep `/materials/:id` param name; value = **slug** | HIGH — existing Playwright URLs |
| Editor byline | Constant `"Редакция Digest CDS"` in DTO — **no DB column** | MEDIUM — [ASSUMED] schema has no editor field |
| Voting cycle selection | Prefer `status = 'open'` ordered by `closes_at DESC`; else latest by `opens_at` for closed messaging | MEDIUM — [ASSUMED] product rule not locked beyond “seed one cycle” |
| Error UI | Extend `ErrorPanel` or thin `ServiceUnavailable` wrapping splash + Retry + fixed copy | HIGH — either OK per CONTEXT discretion |
| Seed path | `supabase-integration/migrations/002_phase2_issue_seed.sql` | HIGH |
| Secondary empty CTA | Optional link to `/knowledge` only if zero new scope | HIGH — CONTEXT |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Issue byline editor is a constant string (no schema column) | Discretion / DTOs | Need tiny migration or omit byline |
| A2 | Active cycle = open-first else latest closed | ISSUE-02 | Wrong callout state until Phase 3 |
| A3 | `rehype-sanitize` included (not only remark-gfm) | Standard Stack | Slightly larger bundle; if omitted, rely on react-markdown defaults only |
| A4 | Archive cards omit thumbnail collage (typography/count only) | UI | Visual mismatch vs design-frontend archive.html thumbs — 02-UI-SPEC does not require thumbs |

**If wrong:** Discuss-phase already locked visual contract in 02-UI-SPEC — prefer UI-SPEC over design-frontend archive thumbs.

## Open Questions (RESOLVED)

1. **Should unpublished past issue numbers 404 or redirect to current?** — **RESOLVED**
   - What we know: error_handling §2.2 says empty «Выпуск не найден» + CTA to current for bad issue number.
   - What's unclear: not restated in CONTEXT decisions.
   - Recommendation: soft editorial empty (like material 404) + CTA «К текущему выпуску» — no splash art.
   - **RESOLVED (plan 02-03):** Adopt soft editorial empty / HTTP 404 for missing or unpublished issue numbers + CTA «К текущему выпуску»; no `bad_gateway` splash (matches material soft-404 tone).

2. **MaterialRelations target shape** — **RESOLVED**
   - What we know: domain `related_material_ids: tuple[str, ...]` [VERIFIED: domain/material.py:29]; DB uses bigint FKs.
   - Recommendation: API returns `{ slug, title }[]` for ready targets only; never invent.
   - **RESOLVED (plan 02-04):** Reader DTO related field is `{ slug, title }[]` for ready targets only; never invent missing links (D-37 / MAT-03).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | SPA + Playwright | ✓ | v22.13.0 | — |
| npm | web deps | ✓ | (with node) | — |
| Python | backend tests | ✓ | 3.14.0 | — |
| uv | pytest / uvicorn | ✓ | 0.10.9 | — |
| Playwright | e2e | ✓ | 1.62.1 | — |
| Remote Supabase VM | live seed + adapters | ✓ (Phase 1) | shared | Mocks for offline; live proof uses existing VM |
| Local Docker Supabase | — | N/A | — | Not required (D-05) |

**Missing dependencies with no fallback:** none for planning/execution of Phase 2.  
**Missing dependencies with fallback:** live VM unavailable → develop/test under mocks; document seed apply when VM reachable.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Playwright `^1.62.1` + pytest via `uv run pytest` |
| Config file | `playwright.config.js`; pytest via project `uv` |
| Quick run command | `npm run test:web` / `uv run pytest tests/unit/test_http_issues.py -x` (after Wave 0) |
| Full suite command | `npm test` && `npm run test:unit` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ISSUE-01 | Current issue hero + TOC or empty «Выпуск готовится» | e2e | `npx playwright test tests/web-app.spec.js -g "issue"` | ❌ Wave 0 (extend) |
| ISSUE-02 | Callout open vs closed (mock harness / fixture) | e2e + unit DTO | Playwright + pytest use-case | ❌ Wave 0 |
| ISSUE-03 | Dek visible when present; absent when empty | unit/e2e | Material page assertions | ❌ Wave 0 |
| ISSUE-04 | Archive list / empty CTA / open past issue | e2e | new describe archive | ❌ Wave 0 |
| MAT-01 | Prose from markdown + section TOC | e2e | material with headings | ❌ Wave 0 |
| MAT-02 | «Статья» + soft 404 | e2e | existing not-found test extend | ✅ partial `tests/web-app.spec.js` |
| MAT-03 | Tags/provenance/related only when present | unit (DTO) + e2e | pytest + Playwright | ❌ Wave 0 |
| PLAT-07 | Network failure → splash + Retry (no mock fallback) | e2e harness | armFailNext like meApi | ❌ Wave 0 |
| API | GET current/archive/material auth + 404 | unit http | `uv run pytest tests/unit/test_http_issues.py` | ❌ Wave 0 |

Existing coverage to preserve: `tests/web-app.spec.js` opens `/materials/rag-systems` and soft-404 for unknown id — must stay green after slug API.

### Sampling Rate

- **Per task commit:** targeted pytest file or single Playwright test
- **Per wave merge:** `npm run test:web` + `npm run test:unit`
- **Phase gate:** full `npm test` + `npm run test:unit` green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_get_current_issue.py` — D-24 selection + empty current
- [ ] `tests/unit/test_list_archive_issues.py` — excludes current
- [ ] `tests/unit/test_get_material_for_reader.py` — draft → not found; ready by slug
- [ ] `tests/unit/test_http_issues.py` / `test_http_materials.py` — JWT + 401/404 shapes
- [ ] Extend `tests/web-app.spec.js` — archive nav, empty states, closed callout, markdown TOC, load-failure splash
- [ ] In-memory fakes for `IssueRepository` / cycle reader in `tests_support/in_memory.py`
- [ ] Optional: unit test for `markdownToc` heading extraction

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | yes | Existing JWT `get_principal` on content GETs |
| V3 Session Management | yes | Supabase SPA session; API stateless Bearer |
| V4 Access Control | yes | Authenticated reads only; draft materials → 404 (no existence leak via 403) |
| V5 Input Validation | yes | Path params: issue `number` int; material `slug` constrained pattern; Pydantic response models |
| V6 Cryptography | no new | No new crypto; reuse Phase 1 JWT verify |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| IDOR draft material | Information disclosure | Use-case returns only `status=ready`; HTTP 404 otherwise |
| XSS via markdown | Tampering | `react-markdown` defaults + `rehype-sanitize`; **no** `rehype-raw` |
| service_role in browser | Elevation | Never `VITE_` secret; clients only in `composition/live.py` |
| Silent mock on failure | Spoofing trust | D-21: ErrorPanel only |
| RLS false sense of safety | Elevation | Do not rely on missing SELECT policies; server-side filter published/ready |

## Sources

### Primary (HIGH confidence — in-repo Read this session)
- `supabase-integration/migrations/001_initial_schema.sql` — tables/enums/RLS policies
- `backend/src/backend/composition/live.py`, `container.py`, `interface/http/deps.py`, `domain/material.py`
- `web/src/pages/IssuePage.jsx`, `MaterialPage.jsx`, `App.jsx`, `services/meApi.js`, `authEnv.js`
- `.planning/phases/02-issue-materials-archive/02-CONTEXT.md`, `02-UI-SPEC.md`
- `.planning/REQUIREMENTS.md`, `STATE.md`

### Secondary (MEDIUM — Context7)
- `/remarkjs/react-markdown` — remarkGfm, components, Security / rehype-sanitize
- `/websites/fastapi_tiangolo` — Depends, HTTPBearer, HTTPException 404

### Tertiary (LOW — Tavily)
- Heading TOC blog patterns; remark vs rehype-sanitize community guidance (cross-checked against official Security notes)

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — versions verified on npm + legitimacy OK; Context7 classify-confidence returned MEDIUM even with `--verified`
- Architecture: HIGH — Ports & Adapters + Phase 1 patterns + schema Read-verified
- Pitfalls: HIGH — RLS gap, live in-memory materials, slug mismatch confirmed in source

**Research date:** 2026-09-19  
**Valid until:** 2026-10-19 (stable editorial/API patterns; re-check npm majors if planning slips)
