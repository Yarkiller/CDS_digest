# Phase 4: Knowledge & Razbory - Context

**Gathered:** 2026-09-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Authenticated users find prepared materials via **semantic (hybrid) search** with **role filters** (KNOW-01…04), and consume **разборы** as a chronology list → published longread with sticky TOC, honest notebook download, and metrics vs «обзор» labeling (RAZB-01…04). Scope is live FastAPI + Supabase wiring for knowledge search and razbor read paths — not admin publish of разборы, not live-as-you-type search, not tag/format/topic filters beyond role, not quizzes or public leaderboard.

</domain>

<decisions>
## Implementation Decisions

### Search trigger & result cards (US-14, US-17)
- **D-57:** Search runs on **Submit / Enter** with a visible **«Найти»** control — not on every keystroke. — **Reversibility:** reversible — UX trigger only.
- **D-58:** Live-as-you-type / debounced search is **out of Phase 4**; note for Phase 5+ backlog.
- **D-59:** Each hit is a **ranked list row**: cover/title/tags as today plus a **chunk-matched snippet**; **do not** show numeric relevance scores. — **Reversibility:** reversible — presentation.
- **D-60:** Pre-search landing: **neutral empty** + **topic hint chips** that fill the query field (not role chips — roles stay in filters). No seeded “recommended” materials (would violate honesty). Aligns with `error_handling.md` §2.5.
- **D-61:** After a successful search: return **top N** from API with **«Показать ещё»** (page/cursor) — evolve mock `PAGE_SIZE` + load-more into a real pagination contract.

### Role filter UX (US-15…17)
- **D-62:** Role filter = **chips**: Analyst / DS / «Все» — replace the role `<select>`. — **Reversibility:** reversible.
- **D-63:** Phase 4 ships **role chips only** — drop tag / format / topic selects from the knowledge UI for v1 (defer to later). — **Reversibility:** reversible — can restore selects later.
- **D-64:** Changing a role chip **re-runs search immediately** when a non-empty query is already active (chip is not deferred until next Submit).
- **D-65:** Zero-hit empty: copy per KNOW-04 / error_handling («Ничего не нашли» + refine hint); CTA **«Сбросить фильтр»** clears **only the role chip** and **keeps query text**. Never substitute irrelevant ML tops.

### Razbor list & routing (US-18…19)
- **D-66:** Routes: **`/razbory`** (list) + **`/razbory/:id`** (detail); AppShell nav label **«Разборы»**. Plural for collections (like `/issues`, `/materials`); singular section routes stay `/archive`, `/voting`, `/knowledge`. — **Reversibility:** costly — URL + nav contract once linked from empty CTAs and seeds.
- **D-67:** List UI follows design-frontend **chronology-item** pattern (date/status overline, title, byline, «Читать»), not `MaterialListRow` covers.
- **D-68:** **Announcement** razbors appear in the list with **«Анонс»**; opening detail shows a **stub** (name/date/status) — **no fake empty longread**. Published multi-section razbor gets sticky TOC (RAZB-02; reuse material TOC patterns where fit).
- **D-69:** Empty list: **«Разборов пока нет»** + primary CTA **«К голосованию» → `/voting`** only (no secondary «К выпуску» in Phase 4).

### Notebook & metrics on longread (US-20…21)
- **D-70:** Primary notebook action is **download only** — «Скачать .ipynb» (no separate in-app notebook viewer in Phase 4). — **Reversibility:** reversible.
- **D-71:** Download control appears in a **top action strip** and is **repeated near the end** of the longread (design-frontend pattern).
- **D-72:** Missing notebook: keep the strip; control **disabled** + caption **«Notebook скоро будет»** (error_handling §2.6); download failure → toast «Не удалось скачать».
- **D-73:** **Honest split for metrics:** with metrics → dedicated **«Качество»** block + TOC entry; without → hero/type badge **«Обзор»** and **no empty metrics table/section** (same honesty as Phase 2: only render what exists).

### Claude's Discretion
- Exact top-N page size / cursor shape, hybrid search port evolution (SQL HNSW+FTS vs in-memory for live), embedding seed vs FoundryModels for demo index, razbor DTO field names, sticky TOC breakpoint shared with materials, notebook storage/serving path behind FastAPI — planner/researcher within Ports & Adapters + TDD + existing schema.
- Carry forward: same `VITE_USE_MOCKS` gate; page GET failures → ServiceUnavailable splash; search/mutation partial failures → banner/ErrorPanel + Retry; soft 404 for unknown razbor id → «К списку разборов».

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria, KNOW-*/RAZB-* mapping
- `.planning/REQUIREMENTS.md` — KNOW-01…04, RAZB-01…04 (REQ-US-14…21)
- `.planning/PROJECT.md` — core value, constraints, stack (pgvector, FoundryModels)
- `CONTEXT.md` — domain language (база знаний, разбор, материал, роль)

### Prior phase decisions
- `.planning/phases/01-platform-foundation-auth/01-CONTEXT.md` — D-09 mocks, JWT/API patterns
- `.planning/phases/02-issue-materials-archive/02-CONTEXT.md` — D-20…23 errors/splash; D-36…39 material honesty / TOC
- `.planning/phases/03-voting-cycle/03-CONTEXT.md` — D-56 mocks; voting empty CTA target for razbor empty state

### Specs & UX
- `docs/digest-cds/acceptance_criteria.md` — US-14…US-21
- `docs/digest-cds/error_handling.md` — §2.5 knowledge, §2.6 разборы / notebook
- `docs/digest-cds/technical_specification.md` — search / knowledge NFR overview
- `docs/digest-cds/user_stories.md` — knowledge & razbor stories if present
- `design-frontend/pages/razbory.html` — chronology list visual canon
- `design-frontend/pages/razbor.html` — longread, TOC, notebook strip, metrics section

### Schema & architecture
- `supabase-integration/migrations/001_initial_schema.sql` — `knowledge_chunks`, `materials.roles`, `razbors`, `notebook_path`, HNSW/GIN indexes
- `.cursor/rules/architecture.mdc` — Ports & Adapters; composition root only; no business rules in React
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `.planning/codebase/CONCERNS.md` — knowledge UI ≠ search use-case; missing razbor routes; hybrid search `list_all` debt
- `.planning/codebase/ARCHITECTURE.md`, `STRUCTURE.md`, `CONVENTIONS.md`

### Brownfield code to evolve
- `web/src/pages/KnowledgePage.jsx`, `web/src/utils/filters.js`, `web/src/components/MaterialListRow.jsx`
- `backend/src/backend/application/use_cases/search_knowledge.py`, `index_material_chunks.py`
- `backend/src/backend/application/ports/knowledge_chunk_repository.py`, `backend/src/backend/domain/knowledge.py`
- `web/src/App.jsx`, `web/src/components/AppShell.jsx` — add `/razbory` routes + nav

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `KnowledgePage` + `MaterialListRow` + `filterMaterials` — evolve to Submit/Enter + API hits with snippets; replace role select with chips; remove extra selects
- Domain `search_knowledge` / `KnowledgeHit` / `KnowledgeChunkRepository` + in-memory fakes — extend with live SQL hybrid search adapter
- Material page sticky TOC / markdown prose patterns — reuse for published razbor longread
- Phase 2–3 `ServiceUnavailable`, `ErrorPanel`, toast, `VITE_USE_MOCKS` service boundary

### Established Patterns
- UI consumes DTOs only; ranking/filter rules live in application use-cases, not React
- Authenticated FastAPI reads via JWT; Supabase adapters in `supabase-integration/`, wired only in composition
- TDD: pytest for ports/HTTP; Playwright for search honesty, role empty, razbor list/longread/notebook

### Integration Points
- New/extend knowledge search HTTP + `web/src/services/` knowledge API
- New razbor list/detail HTTP + pages; AppShell nav «Разборы»
- Seed: searchable chunks with embeddings + ≥1 published multi-section razbor (± notebook) + announcement stub + empty-path coverage
- RLS / service_role: follow Phase 2–3 pattern — browser never gets service role

</code_context>

<specifics>
## Specific Ideas

- Hint chips are **topics** that fill the query, not roles — user explicitly separated “point of entry” from filter semantics.
- Routing convention stated by user: **plural for collections**, singular for section hubs (`/archive`, `/voting`, `/knowledge`).
- Metrics honesty mirrors Phase 2 material rules: never show empty stub sections («метрики не публиковались» rejected as a fake section).

</specifics>

<deferred>
## Deferred Ideas

- Live-as-you-type / debounced knowledge search — Phase 5+ candidate
- Knowledge tag / format / topic filter selects — later phase
- In-app notebook viewer / nbconvert pipeline UI — not Phase 4 (download-only)
- Admin create/publish разборы — Phase 5 territory
- Quizzes after material/razbor (US-29) — post-v1

</deferred>

---

*Phase: 4-Knowledge & Razbory*
*Context gathered: 2026-09-20*
