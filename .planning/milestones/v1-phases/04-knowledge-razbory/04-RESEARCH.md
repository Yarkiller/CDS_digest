# Phase 4: Knowledge & Razbory - Research

**Researched:** 2026-09-20
**Domain:** Hybrid semantic knowledge search (pgvector + FTS) + razbor chronology/longread/notebook download (FastAPI + React)
**Confidence:** HIGH (brownfield schema/use-cases/UI patterns + locked D-57…73); MEDIUM (Context7 pgvector/FastAPI FileResponse — classify-confidence returned MEDIUM even with `--verified`); LOW (general search-UX web sources)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)
- Live-as-you-type / debounced knowledge search — Phase 5+ candidate
- Knowledge tag / format / topic filter selects — later phase
- In-app notebook viewer / nbconvert pipeline UI — not Phase 4 (download-only)
- Admin create/publish разборы — Phase 5 territory
- Quizzes after material/razbor (US-29) — post-v1
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KNOW-01 | Meaningful semantic query → relevant hits or honest empty; whitespace-only → inline «Введите запрос», no search | Client+HTTP validation; `search_knowledge` only after trim; empty list 200 not fake tops |
| KNOW-02 | Analyst role filter → only analyst-tagged materials; clear filter restores unrestricted keeping query | `role_filter="analyst"` on materials.roles; D-65 reset clears chip only |
| KNOW-03 | DS search/filter → ML/experiment materials open to material page | Seed `roles` include `ds`; hit → `/materials/{slug}` |
| KNOW-04 | Analyst zero-hit honest empty; no ML top substitution; reset/refine works | Server never backfills other roles; empty CTA «Сбросить фильтр» |
| RAZB-01 | List name/date/status; empty → CTA to voting | `GET /razbory`; chronology UI; D-69 |
| RAZB-02 | Published multi-section longread + sticky TOC | Reuse `extractMarkdownHeadings` + MaterialPage sticky `lg:` TOC |
| RAZB-03 | `.ipynb` download when attached; disabled + caption when missing | `notebook_path` + FastAPI `FileResponse`; D-70…72 |
| RAZB-04 | Metrics → «Качество»; without → «Обзор», no empty metrics section | D-73 + body/DTO honesty (no schema metrics column) |
</phase_requirements>

## Summary

Phase 4 wires the existing hybrid-search use-case and schema (`knowledge_chunks` HNSW + `content_tsv` GIN) to authenticated FastAPI + a Submit/Enter knowledge UI, and adds greenfield razbor list/detail routes that already exist in design-frontend but not in React. Today `KnowledgePage` still keyword-filters `mock.js` client-side; `live.py` still wires `InMemoryKnowledgeChunkRepository()`; there is **no** razbor HTTP port, route, or AppShell nav. Schema already defines `razbor_status` (`announcement` | `published`) and `notebook_path` but **no metrics column** — metrics honesty must come from body/DTO presence rules.

**Primary recommendation:** Evolve `KnowledgeChunkRepository` with a SQL-capable `search(...)` (keep Python hybrid only for in-memory fakes); add `QueryEmbedder` + seeded 1024-d vectors for demo (defer live Foundry HTTP); expose `GET /knowledge/search` with pagination and **score omitted from JSON**; add `RazborRepository` + `GET /razbory`, `GET /razbory/{id}`, `GET /razbory/{id}/notebook` via `FileResponse`; SPA `knowledgeApi` / `razboryApi` behind `isMocksEnabled()`. Install **no new packages**.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Hybrid ranking + role filter | API / Backend | Database / Storage | Architecture forbids ranking in React; SQL HNSW/FTS owns scale |
| Query embedding | API / Backend | — | Embed at edge of use-case via port; never in browser |
| Whitespace / overlong validation | Browser / Client | API / Backend | Inline UX first; server rejects blank as defense |
| Hit presentation (snippet, no scores) | Browser / Client | API / Backend | DTO omits score; UI shows cover/title/tags/snippet |
| Razbor list chronology + empty CTA | Browser / Client | API / Backend | DTO list; CTA link to `/voting` is presentation |
| Sticky TOC / markdown prose | Browser / Client | — | Reuse MaterialPage + `markdownToc.js` |
| Notebook binary download | API / Backend | CDN / Static (files on disk) | AuthZ + path sanitize in FastAPI; not public StaticFiles |
| Metrics vs «Обзор» labeling | API / Backend | Browser / Client | Use-case/DTO sets `content_kind`; UI only renders when present |
| Mock vs live cutover | Browser / Client | — | Carry `VITE_USE_MOCKS` / `isMocksEnabled()` |
| Persist chunks / razbors | Database / Storage | API / Backend | service_role adapters in composition only |

## Project Constraints (from .cursor/rules/)

| Rule | Directive for Phase 4 |
|------|------------------------|
| Ports & Adapters (`architecture.mdc`) | Domain/use-cases depend only on ports; Supabase adapters in `supabase-integration/`; wire only in `composition/` (`live.py` / `container.py`) |
| No SDK in use-cases | No `supabase` / `httpx` / FastAPI imports in `search_knowledge` or razbor use-cases |
| Frontend services boundary | Knowledge/razbor HTTP only via `web/src/services/`; pages consume DTOs |
| TDD (`tdd.mdc` / `AGENTS.md`) | `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST` — pytest for ports/HTTP, Playwright for KNOW/RAZB honesty |
| Python deps | Add packages only via `uv` / `python-uv.mdc` if needed — Phase 4 should need **none** |
| Context7 for library docs | Prefer Context7 for FastAPI/pgvector when changing download/search SQL patterns |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.141.1 [VERIFIED: local `uv run` import] | HTTP search + razbor + FileResponse | Already in composition / routes |
| PostgreSQL + pgvector | schema `vector(1024)` + HNSW [VERIFIED: `001_initial_schema.sql:160-181`] | Hybrid vector+FTS index | ADR-0004 + existing migration |
| React | ^19.2.8 [VERIFIED: `web/package.json`] | Knowledge + razbor pages | Existing SPA |
| react-router-dom | ^7.18.3 (registry latest 7.18.4) [VERIFIED: `web/package.json`] | `/razbory`, `/razbory/:id` | Existing router |
| react-markdown + remark-gfm + rehype-slug + rehype-sanitize | existing [VERIFIED: `web/package.json`] | Razbor longread + TOC ids | MaterialPage pattern |
| Playwright | ^1.62.1 [VERIFIED: root `package.json`] | E2E KNOW/RAZB honesty | Existing suite |
| pytest via `uv run pytest` | existing | Unit/HTTP contract | `test:unit` script |

### Supporting

| Library / asset | Version | Purpose | When to Use |
|-----------------|---------|---------|-------------|
| FastAPI `FileResponse` | same FastAPI | Authenticated `.ipynb` download | RAZB-03 — [CITED: fastapi.tiangolo.com FileResponse] |
| `design-frontend/assets/notebooks/hybrid-retrieval.ipynb` | in-repo [VERIFIED: path exists] | Seed notebook binary for download demo | Copy under backend-served root |
| Deterministic embed stub (in-repo) | n/a | Query + chunk vectors without Foundry | Demo/live until Foundry client exists |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQL hybrid in adapter | Keep `list_all` + Python cosine forever | Works for tiny seed; fails NFR-P3 and ignores HNSW/GIN — reject for live |
| FoundryModels live embed | Deterministic seed embeddings | Live Foundry needs `data-collection` HTTP client (still DTO-only) — defer |
| Supabase Storage for notebooks | Local path + FileResponse | Storage adds RLS/bucket ops; `notebook_path` is plain `text` today — path+FileResponse fits schema |
| Offset pagination | Keyset cursor on (score, id) | Cursor better at scale; offset enough for Phase 4 page sizes |

**Installation:** none — reuse existing stack.

**Version verification:** FastAPI 0.141.1 (local); React 19.2.8 / Vite 8.2.2 / react-router-dom ^7.18.3 from `web/package.json`; Playwright ^1.62.1 from root `package.json`.

## Package Legitimacy Audit

> No new external packages recommended for this phase.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | N/A |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none  

*If planner later proposes a Foundry/httpx client package, run `gsd_run query package-legitimacy check` before install.*

## Architecture Patterns

### System Architecture Diagram

```text
[Browser KnowledgePage]
   | Submit/Enter + role chip
   v
[knowledgeApi] --VITE_USE_MOCKS--> mock hits
   | live Bearer JWT
   v
[GET /knowledge/search?q&role&limit&offset]
   -> validate trim(q)
   -> QueryEmbedder.embed(q)
   -> search_knowledge / chunks.search(...)
        |                          |
        v                          v
 [InMemory hybrid]         [Supabase SQL: <=> + ts_rank]
        |
        v
 [KnowledgeSearchResponse { items[], has_more } ]  // no score field
        |
        v
 [MaterialListRow] --> /materials/:slug

[Browser RazboryListPage / RazborPage]
   -> razboryApi GET /razbory | /razbory/:id
   -> announcement stub OR markdown+TOC
   -> download GET /razbory/:id/notebook -> FileResponse(.ipynb)
```

### Recommended Project Structure

```text
backend/src/backend/
  domain/razbor.py                    # Razbor entity + status enum
  application/ports/
    knowledge_chunk_repository.py     # + search(...); keep list_all for index/tests
    query_embedder.py                 # Protocol
    razbor_repository.py              # list / get / resolve_notebook_path
    notebook_storage.py               # optional: resolve safe Path
  application/use_cases/
    search_knowledge.py               # evolve: pagination, blank guard
    list_razbors.py / get_razbor.py
    download_razbor_notebook.py
  interface/http/routes/
    knowledge.py
    razbory.py
  composition/live.py                 # wire SupabaseKnowledgeChunkRepository + RazborRepo

supabase-integration/src/.../
  knowledge_chunk_repository.py       # SQL hybrid
  razbor_repository.py

web/src/
  services/knowledgeApi.js
  services/razboryApi.js
  pages/KnowledgePage.jsx             # evolve
  pages/RazboryListPage.jsx           # new
  pages/RazborPage.jsx                # new
  components/ChronologyItem.jsx       # optional extract
```

### Pattern 1: Port-shaped hybrid search (replace list_all debt)

**What:** Live adapter runs vector + FTS in SQL; in-memory fake keeps current Python scoring for unit tests.  
**When to use:** Always for Phase 4 live path.  
**Evidence:** Current port is list-only [VERIFIED: `knowledge_chunk_repository.py:8-11`]:

```python
class KnowledgeChunkRepository(Protocol):
    def replace_for_material(self, material_id: int, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]: ...
    def list_all(self) -> list[KnowledgeChunk]: ...
```

**Recommended port addition (planner-facing):**

```python
def search(
    self,
    *,
    query_embedding: list[float],
    query_text: str,
    role_filter: str | None,
    limit: int,
    offset: int,
) -> list[KnowledgeHit]: ...
```

SQL shape (live) — cosine NN [CITED: Context7 /pgvector/pgvector]:

```sql
ORDER BY embedding <=> $query_vec
LIMIT $candidate_k
```

Combine with `content_tsv @@ plainto_tsquery('simple', $q)` / `ts_rank_cd` (same language as generated column `to_tsvector('simple', ...)` [VERIFIED: `001_initial_schema.sql:167-169`]). Keep fusion weights aligned with use-case (0.7 vector + 0.3 FTS) [VERIFIED: `search_knowledge.py:46`] or RRF in SQL — pick one and unit-test honesty of empty.

### Pattern 2: Score stays server-side (D-59)

**What:** HTTP response lists material fields + `snippet` only; never expose `score`.  
**When to use:** Always.  
**Domain today includes score** [VERIFIED: `knowledge.py:21-26`]:

```python
class KnowledgeHit:
    material_id: int
    material_slug: str
    chunk_index: int
    snippet: str
    score: float
```

Map to HTTP DTO without `score`. Deduplicate by `material_id` (best chunk wins) before pagination so «Показать ещё» pages materials, not raw chunks.

### Pattern 3: Role vocabulary

**What:** Filter chips send `analyst` | `ds` | omit for «Все».  
**Verified values in domain tests/mocks:** `("ds", "sva")`, `analyst` [VERIFIED: `test_search_knowledge.py:26`; `mock.js` roles arrays].  
**Do not** send UI label strings; do not use DB `app_role.employee` for material filters (materials.roles is `text[]`, not `app_role`).

### Pattern 4: Razbor status + notebook

Schema [VERIFIED: `001_initial_schema.sql:33-35`, `216-224`]:

```sql
create type razbor_status as enum ('announcement', 'published');
...
create table if not exists razbors (
  id bigint generated always as identity primary key,
  topic_id bigint not null references topics (id) on delete restrict,
  title text not null,
  body_markdown text not null default '',
  meeting_at timestamptz,
  status razbor_status not null default 'announcement',
  notebook_path text,
  created_at timestamptz not null default now()
);
```

- List: order by `meeting_at DESC NULLS LAST`, then `created_at DESC`.
- `announcement`: return stub DTO (`body_markdown` empty or ignored); UI shows «Анонс» — no prose/TOC/metrics.
- `published`: render markdown; TOC from headings; notebook strip always present.

### Pattern 5: Sticky TOC reuse

Material TOC [VERIFIED: `MaterialPage.jsx:45-48`]:

```jsx
className="sticky top-24 hidden max-h-[70vh] w-56 shrink-0 overflow-auto lg:block"
```

Reuse same breakpoint (`lg:`) and `extractMarkdownHeadings` + `rehypeSlug` for razbor.

### Pattern 6: Notebook FileResponse

[CITED: Context7 FastAPI FileResponse] — stream path with `filename=...ipynb`, `content_disposition_type="attachment"`, JWT via `get_principal`. Resolve `notebook_path` under a configured root (`NOTEBOOK_ROOT`); reject `..` / absolute escapes. Missing file → HTTP 404; UI already disabled when DTO `notebook_available=false`.

### Pattern 7: Metrics honesty without schema column

No metrics column exists [VERIFIED: razbors DDL above]. **Recommendation:** DTO field `content_kind: "quality" | "overview"` (or `has_metrics: bool`) computed in use-case:

- If published body contains a real quality heading (e.g. `## Оценка качества` / `## Качество`) **and** a markdown table with numeric cells → `content_kind="quality"`, ensure TOC includes that heading.
- Else → `content_kind="overview"`, hero badge «Обзор», **do not** render empty metrics table.

Seed one published razbor with metrics table and one overview without.

### Anti-Patterns to Avoid

- **Client-side keyword filter as “semantic search”:** current `filterMaterials` — replace with API.
- **Returning ML tops when analyst filter yields zero:** violates KNOW-04 / D-65.
- **Showing relevance scores in UI:** violates D-59.
- **Live `list_all` hybrid:** documented debt in CONCERNS — do not ship as production search.
- **Public StaticFiles for notebooks:** bypasses auth; use authenticated FileResponse.
- **Fake empty longread for announcement:** violates D-68.
- **Empty metrics stub section:** violates D-73 / Phase 2 honesty.
- **Business ranking in React:** architecture.mdc anti-pattern.
- **Deep-import supabase from use-cases.**

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector similarity | Custom ANN in Python for live | pgvector `<=>` + HNSW | Index already exists; NFR-P3 |
| FTS ranking | Ad-hoc substring only for live | `tsvector` / `ts_rank_cd` | GIN on `content_tsv` exists |
| File download headers | Manual Content-Disposition | FastAPI `FileResponse` | Correct encoding / ranges |
| Markdown TOC / slugs | New slugger | `markdownToc.js` + rehype-slug | Already matched to MaterialPage |
| Auth gate | New middleware | Existing `get_principal` | Phase 1 pattern |
| Mock cutover | Second env flag | `isMocksEnabled()` | D-20/D-56 carry-forward |
| Soft 404 UX | Raw HTTP error page | ContentApiError `NOT_FOUND` pattern | Phase 2 materials |

**Key insight:** Schema and domain use-case already encode hybrid search; Phase 4 is mostly **adapter + HTTP + honesty UX**, not inventing a new search algorithm.

## Common Pitfalls

### Pitfall 1: Role chip resets wipe the query
**What goes wrong:** Empty CTA «Сбросить» clears everything → user retypes.  
**Why:** Current KnowledgePage `reset()` clears all filters including query.  
**How to avoid:** D-65 — clear **only** role chip; keep query; re-run search.  
**Warning signs:** Playwright KNOW-04 fails on preserved `q`.

### Pitfall 2: Pagination returns duplicate materials
**What goes wrong:** Multiple chunks from same material flood pages.  
**Why:** Chunk-level scoring without material collapse.  
**How to avoid:** Dedupe by `material_id` (max score) before offset/limit.  
**Warning signs:** Same title appears twice in first page.

### Pitfall 3: Embedding dim mismatch
**What goes wrong:** Insert/query fails or silent zero scores.  
**Why:** Schema `vector(1024)` and Foundry DTO `EMBEDDING_DIM = 1024` [VERIFIED: `foundry.py:5-6`]; stub must match.  
**How to avoid:** Seed and QueryEmbedder both emit length-1024 lists; unit-test length.  
**Warning signs:** Adapter errors on upsert; empty search always.

### Pitfall 4: Path traversal on notebook_path
**What goes wrong:** `../../etc/passwd` served.  
**Why:** `notebook_path` is free text.  
**How to avoid:** Resolve under `NOTEBOOK_ROOT` with `Path.resolve()` containment check.  
**Warning signs:** Integration test with `../` returns 400/404 not file bytes.

### Pitfall 5: Existing Playwright tests assume tag selects
**What goes wrong:** Suite red after removing tag/format/topic selects (D-63).  
**Why:** `tests/web-app.spec.js` “filters knowledge materials by tag facet”.  
**How to avoid:** Rewrite those tests in Wave 0 to Submit/Enter + role chips; keep empty-state + load-more coverage under new contract.  
**Warning signs:** Immediate Playwright failures on `/knowledge`.

### Pitfall 6: MaterialListRow id vs slug
**What goes wrong:** Live hits use numeric id; MaterialPage expects slug.  
**Why:** Mock ids are slug strings; row links `to={/materials/${material.id}}` [VERIFIED: `MaterialListRow.jsx:6`].  
**How to avoid:** Pass `slug` into row / link `/materials/${slug}`.  
**Warning signs:** Click search hit → soft 404.

### Pitfall 7: RLS gap on razbors
**What goes wrong:** Assuming browser PostgREST can read razbors.  
**Why:** RLS enabled; no SELECT policy for razbors [VERIFIED: policies end without razbors SELECT — `001_initial_schema.sql:260-297`].  
**How to avoid:** service_role adapter via FastAPI (same as issues/materials), never expose secret to Vite.  
**Warning signs:** Direct supabase-js read returns empty.

## Code Examples

### Blank query guard (use-case / HTTP)

```python
# Align with KNOW-01 / error_handling §2.5
q = (query_text or "").strip()
if not q:
    raise KnowledgeQueryValidationError("empty_query")  # -> 400; SPA shows «Введите запрос»
```

### pgvector cosine query (live adapter)

```sql
-- Source: Context7 /pgvector/pgvector (HNSW cosine)
SELECT kc.*, m.slug, m.title, m.roles
FROM knowledge_chunks kc
JOIN materials m ON m.id = kc.material_id AND m.status = 'ready'
WHERE ($role::text IS NULL OR $role = ANY (m.roles))
ORDER BY kc.embedding <=> $1::vector
LIMIT $2;
```

Fuse with FTS candidates / scores in the same adapter method; return domain `KnowledgeHit` list.

### Notebook download route sketch

```python
# Source: Context7 FastAPI FileResponse
from fastapi.responses import FileResponse

@router.get("/{razbor_id}/notebook")
def download_notebook(razbor_id: int, principal=Depends(get_principal)):
    path = resolve_notebook(razbor_id)  # raises NotFound / MissingNotebook
    return FileResponse(
        path,
        filename=path.name,
        media_type="application/x-ipynb+json",
        content_disposition_type="attachment",
    )
```

### Knowledge search HTTP shape (recommended)

```json
{
  "items": [
    {
      "slug": "pgvector",
      "title": "pgvector for Enterprise Search",
      "snippet": "Use HNSW indexes for semantic search.",
      "tags": ["pgvector", "RAG"],
      "cover_url": null,
      "roles": ["ds", "sva"]
    }
  ],
  "has_more": false,
  "limit": 10,
  "offset": 0
}
```

No `score` field.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Client keyword filter | Server hybrid vector+FTS | Phase 4 | True semantic search |
| `list_all` + Python cosine (live) | SQL HNSW + GIN in adapter | Phase 4 | Uses existing indexes |
| No razbor routes | `/razbory` + `/razbory/:id` | Phase 4 | Closes CONCERNS gap |
| Live chunks = InMemory | SupabaseKnowledgeChunkRepository | Phase 4 | live.py must change |

**Deprecated/outdated:**

- Knowledge tag/format/topic `<select>`s in React for v1 (D-63)
- Design-frontend as product surface (reference only)
- Live-as-you-type search (D-58 deferred)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Default page size `limit=10` (evolve from mock `PAGE_SIZE=3`) is acceptable | Discretion / Standard Stack | UX denser/sparser — reversible |
| A2 | Offset+`has_more` sufficient vs keyset cursor for Phase 4 | Discretion | May revisit if seed ≫ hundreds |
| A3 | Deterministic 1024-d seed embeddings + matching QueryEmbedder enough without Foundry HTTP | Discretion | Live “semantic” quality limited until Foundry wired |
| A4 | Metrics detected via markdown heading/table convention, not new DB column | Pattern 7 | Fragile if authors omit heading — seed must follow convention |
| A5 | Notebook files live under local `NOTEBOOK_ROOT` (not Supabase Storage) | Don't Hand-Roll | Ops path differs if Storage preferred later |
| A6 | Cover URLs optional/null in search DTO until assets seeded | Code Examples | Rows may lack thumbnails |

**If empty:** N/A — assumptions listed for planner confirmation where needed.

## Open Questions (RESOLVED)

1. **FoundryModels for query embed in Phase 4?**
   - What we know: `data-collection` only has DTOs; no HTTP client.
   - What's unclear: whether Cloud.ru credentials are ready for live embed.
   - Recommendation: ship deterministic seed+embedder; optional env-gated Foundry later — do not block Phase 4.
   - **RESOLVED:** Use `StubQueryEmbedder` (deterministic length-1024) + seeded vectors this phase; Foundry HTTP client remains OPT-OUT (COVERAGE.md).

2. **Cover images for knowledge hits?**
   - What we know: MaterialListRow expects `material.cover`; materials schema has no cover column in initial migration excerpt.
   - Recommendation: allow `cover_url: null` and degrade row layout, or seed static paths — planner pick one.
   - **RESOLVED:** `cover_url` may be `null`; `MaterialListRow` degrades without thumbnail (no seeded static cover paths).

3. **Byline on chronology items?**
   - What we know: design shows author + DS badge; schema has no author column on razbors.
   - Recommendation: constant «Редакция Digest CDS» or omit byline until profile join exists.
   - **RESOLVED:** Constant byline «Редакция Digest CDS» on chronology items (no author join this phase).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Backend tests / uvicorn | ✓ | 3.14.0 | — |
| uv | pytest / deps | ✓ | 0.10.9 | — |
| Node / npm | Playwright / Vite | ✓ | 22.13.0 / 11.18.0 | — |
| FastAPI | HTTP | ✓ | 0.141.1 | — |
| Self-hosted Supabase | Live adapters / seed | ✓ (project pattern Phase 2–3) | knowledge-db.ru | In-memory for unit; mocks for Playwright |
| FoundryModels API | Live query embeddings | ✗ / unverified client | — | Deterministic embedder + seeded vectors |
| Notebook file on disk | RAZB-03 | ✓ design asset exists | hybrid-retrieval.ipynb | Copy into NOTEBOOK_ROOT |

**Missing dependencies with no fallback:** none for Phase 4 scope (Foundry has fallback).

**Missing dependencies with fallback:** FoundryModels → deterministic embeddings.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (`uv run pytest`) + Playwright `@playwright/test` ^1.62.1 |
| Config file | `playwright.config.js`; pytest via uv project |
| Quick run command | `uv run pytest tests/unit/test_search_knowledge.py -x` |
| Full suite command | `npm run test:unit && npm run test:web` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| KNOW-01 | Semantic hit / honest empty; whitespace no search | unit + e2e | `uv run pytest tests/unit/test_search_knowledge.py -x`; Playwright knowledge submit | ✅ unit partial / ❌ e2e Wave 0 |
| KNOW-02 | Analyst filter roles | unit + e2e | pytest role_filter; Playwright chip | ❌ Wave 0 |
| KNOW-03 | DS materials open | e2e | Playwright search → material | ❌ Wave 0 |
| KNOW-04 | No ML substitution; reset chip only | unit + e2e | pytest empty+filter; Playwright | ❌ Wave 0 (old empty exists) |
| RAZB-01 | List / empty CTA `/voting` | unit HTTP + e2e | pytest http razbory; Playwright | ❌ Wave 0 |
| RAZB-02 | Sticky TOC section jump | e2e | Playwright razbor TOC | ❌ Wave 0 |
| RAZB-03 | Download enable/disable | unit + e2e | pytest FileResponse; Playwright | ❌ Wave 0 |
| RAZB-04 | Metrics vs Обзор | unit + e2e | pytest DTO kind; Playwright | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** targeted pytest file(s) for touched use-case/route
- **Per wave merge:** `npm run test:unit` + affected Playwright project
- **Phase gate:** full `test:unit` + `test:web` green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_http_knowledge_search.py` — KNOW-01…04 HTTP contract (blank 400, role filter, no score field, pagination)
- [ ] Extend `tests/unit/test_search_knowledge.py` — role filter empty honesty; material dedupe; offset
- [ ] `tests/unit/test_http_razbory.py` — list/detail/announcement/404/notebook
- [ ] `tests/unit/test_razbor_use_cases.py` — content_kind metrics vs overview
- [ ] Rewrite `tests/web-app.spec.js` knowledge cases (remove tag facet; add Submit/Enter, chips, reset-filter-only)
- [ ] New Playwright razbory specs (list empty CTA, sticky TOC, notebook disabled/enabled, Обзор vs Качество)
- [ ] In-memory `RazborRepository` + `QueryEmbedder` fakes in `tests_support`
- [ ] Seed fixtures: chunks+embeddings, published multi-section razbor ± notebook, announcement, overview-without-metrics

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing JWT `get_principal`; Bearer on all knowledge/razbor routes |
| V3 Session Management | yes | Carry Phase 1 token handling; no new session store |
| V4 Access Control | yes | Authenticated reads only; service_role only in composition; soft-404 for unknown ids |
| V5 Input Validation | yes | Trim/length on `q`; role enum allowlist; path containment for notebooks; Pydantic response models `extra="forbid"` |
| V6 Cryptography | no new | No new crypto; reuse existing JWT verify |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via `notebook_path` | Elevation / Information disclosure | Resolve under NOTEBOOK_ROOT; reject escapes |
| Score leakage / ranking gaming UI | Information disclosure | Omit score from API |
| Unauthenticated notebook download | Information disclosure | JWT required; no public StaticFiles |
| SQL injection in hybrid search | Tampering | Parameterized PostgREST/SQL only |
| Exposing service_role to Vite | Elevation | Composition-only secrets (existing rule) |
| Draft materials in search | Information disclosure | Join `materials.status = 'ready'` only |
| RLS bypass assumptions | Elevation | Backend uses service_role; do not open browser RLS without policies |

## Sources

### Primary (HIGH / MEDIUM confidence)

- In-repo schema `supabase-integration/migrations/001_initial_schema.sql` — knowledge_chunks, razbors, enums, indexes, RLS
- In-repo `search_knowledge.py`, `knowledge.py`, `knowledge_chunk_repository.py`, `live.py`, `KnowledgePage.jsx`, `MaterialPage.jsx`, `App.jsx`, `AppShell.jsx`
- Context7 `/pgvector/pgvector` — `<=>`, HNSW `vector_cosine_ops`, hybrid FTS notes (classify-confidence MEDIUM with `--verified`)
- Context7 `/websites/fastapi_tiangolo` — `FileResponse` attachment download
- Locked `04-CONTEXT.md` D-57…D-73
- Specs: `docs/digest-cds/error_handling.md` §2.5–2.6; `acceptance_criteria.md` US-14…21; `technical_specification.md` NFR-P3

### Secondary (MEDIUM)

- design-frontend `razbory.html` / `razbor.html` visual canon
- `.planning/codebase/CONCERNS.md` — list_all debt, missing razbor routes
- Phase 2–3 CONTEXT carry-forward (mocks, ServiceUnavailable, soft 404)

### Tertiary (LOW)

- Tavily search UX articles (honest empty / no weak substitution) — aligns with KNOW-04 but non-authoritative

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — versions read from local imports / package.json; no new packages
- Architecture: HIGH — ports/adapters and brownfield seams verified by Read
- Pitfalls: HIGH — grounded in current tests/UI/schema gaps
- External docs (pgvector/FileResponse): MEDIUM — Context7 cited; classify-confidence MEDIUM
- Search UX web: LOW — supportive only

**Research date:** 2026-09-20  
**Valid until:** ~2026-10-20 (stable stack; re-check if Foundry client lands)

### Project skills accounted for

- `.agents/skills/supabase` — service_role only in composition; RLS on exposed tables; no browser secret
- `.agents/skills/supabase-postgres-best-practices` — parameterized SQL; use existing indexes
- `.agents/skills/hallmark` — not phase-blocking for this research
