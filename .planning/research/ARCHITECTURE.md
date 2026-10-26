# Architecture Research

**Domain:** editorial ingest enrichment (two-pass article + Tavily + cheat sheet)
**Project:** Digest CDS — milestone v1.5
**Researched:** 2026-10-26
**Confidence:** HIGH for integration points (read from live ingest pipeline, ports, `Stage`, reader DTO, razbor file pattern). MEDIUM for Tavily SDK internals (STACK.md).

> **Scope.** Subsequent milestone. The dual-hexagon (backend reader vs ingestion-service writer, shared Supabase) is **shipped and not re-litigated**. This document covers NEW components, data-flow changes, fail-soft vs fail-closed rules, and build order for two-pass enrichment.

---

## Standard Architecture (existing — preserve)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ web/  — UI only; API via web/src/services/*                                   │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ HTTPS (JWT)
┌───────────────────────────────▼──────────────────────────────────────────────┐
│ backend/  interface/http → application/use_cases → domain                     │
│           composition/ live.py wires supabase-integration adapters            │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ service_role / authenticated client
┌───────────────────────────────▼──────────────────────────────────────────────┐
│ self-hosted Supabase (Postgres + pgvector + Auth)                             │
└───────────────────────────────▲──────────────────────────────────────────────┘
                                │ persist_draft_and_enqueue (service_role)
┌───────────────────────────────┴──────────────────────────────────────────────┐
│ ingestion-service  CLI composition → run_ingest_pipeline                      │
│   captions / metadata / ArticleGenerator  ← data-collection ports             │
│   DeepSeek + YouTube adapters live in data-collection; wiring in composition  │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Invariant:** backend/SPA stay **readers**. CLI owns YouTube + LLM + persist. No Tavily/DeepSeek SDK in `backend/` domain or use-cases.

---

## System Overview (v1.5 additions)

```
URL → captions → metadata → consistency
        ↓
   ArticleGenerator.process   [pass 1, fail-closed, stage=llm]
        ↓
   TopicKindClassifier        [practical | conceptual; fail-closed → conceptual]
        ↓
   persist_draft              [ALWAYS — pass-1 floor lands as materials draft]
        ↓ (already_saved? stop. conceptual? stop.)
   TavilyQuota.try_consume    [atomic RPC; miss → log, return persist result]
        ↓
   WebSearch + PageExtract    [Tavily; trust_env=False; https-only]
        ↓
   URL liveness allowlist     [transcript/description ∪ extract successes]
        ↓
   ArticleEnricher.process    [pass 2, fail-SOFT; second json_object stream]
        ↓
   update draft + cheat sheet file
        ↓
   backend reader: body + sources[] + cheat_sheet download
```

Pass 2 **never** raises `IngestError`. A Tavily/quota/enricher miss leaves the pass-1 row. That is the architectural fix for grafting search onto today's fail-closed `stage=llm` path.

---

## Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `TopicKindClassifier` | Closed `practical \| conceptual` from transcript + pass-1 draft | Protocol in `data-collection/ports/`; DeepSeek JSON adapter or a cheap second call; invalid/empty → `conceptual` |
| `WebSearchPort` / `PageExtractPort` | Tavily search + extract; map SDK errors at the adapter | `AsyncTavilyClient` + injected `httpx.AsyncClient(trust_env=False)` |
| `UrlLivenessPort` | HEAD then GET; https-only; reject private/link-local | existing `httpx==0.28.1` |
| `TavilyQuota` | Atomic `try_consume(n)` against global 1000 | Postgres single-row + RPC; in-memory fake in unit tests |
| `ArticleEnricher` | Pass-2 JSON: guide sections, generated code, cheat-sheet md, **only allowlisted URLs** | Reuse `AsyncOpenAI` stream + `json_object`; not tool-calling |
| `CheatSheetStorage` | Write/read markdown under `CHEAT_SHEET_ROOT` | Copy `LocalNotebookStorage` containment |
| `run_ingest_pipeline` | Orchestrate classify → persist → optional enrich/update | `ingestion-service` use-case; new deps injected, not imported SDKs |
| Reader delivery | `sources[]` + cheat-sheet download | Additive fields on `MaterialReaderResponse`; FastAPI `FileResponse` |

**Public `data_collection.__all__` stays the current 10 names.** New ports live as modules under `data-collection/ports/` and are imported by `ingestion-service` the same way `article_generator` is — do not widen `__all__` unless a second package must construct them. Adapters stay module-private.

---

## Recommended Project Structure

```
data-collection/src/data_collection/
  ports/
    article_generator.py          # existing pass 1
    topic_kind.py                 # NEW
    web_search.py                 # NEW
    page_extract.py               # NEW
    tavily_quota.py               # NEW (or ingestion-service/application/ports if quota is persist-adjacent)
    article_enricher.py           # NEW
  adapters/
    deepseek_article.py           # existing; templates rewritten
    deepseek_classifier.py        # NEW
    tavily_search.py              # NEW
    httpx_url_liveness.py         # NEW
    deepseek_enricher.py          # NEW
  templates/lecture.md, podcast.md
  dto/material_draft.py           # additive optional fields

ingestion-service/src/ingestion_service/
  application/use_cases/ingest_pipeline.py   # persist-then-enrich
  composition/clients.py                     # Tavily httpx trust_env=False
  composition/settings.py                    # TAVILY_API_KEY, caps, CHEAT_SHEET_ROOT
  domain/errors.py                           # Stage set UNCHANGED for fail-closed path

backend/
  domain/material.py                         # sources + cheat_sheet_path
  infrastructure/local_cheat_sheet_storage.py
  interface/http/routes/materials.py         # additive DTO + download route

supabase-integration/migrations/
  0xx_tavily_quota.sql
  0xx_materials_cheat_sheet.sql
```

### Structure Rationale

- **Ports in `data-collection`:** matches `ArticleGenerator`; the CLI already depends on that package.
- **Quota RPC in supabase-integration:** same home as `persist_draft_and_enqueue`; both CLI and a future second writer share one ledger.
- **Cheat sheet local FS, not Storage:** STACK.md — CLI and API already share the app VM; razbor `NOTEBOOK_ROOT` is the proven pattern.
- **Do not put Tavily in `backend/`:** reader never searches.

---

## Architectural Patterns

### Pattern 1: Persist-then-enrich (fail-soft floor)

**What:** Pass 1 is fail-closed (`stage=llm` / `llm_truncation`, zero rows). After a valid `ArticleDraft`, persist immediately. Classify/enrich run on the saved row. Enricher exceptions are caught, logged, and the original persist result is returned (exit 0).

**When to use:** Any optional external read (Tavily) after a required LLM write.

**Trade-offs:** One extra UPDATE vs today's single persist. `already_saved` must skip the whole chain (including enrich) so a timer re-scan cannot burn quota. First-run enrich happens *before* the CLI returns, so the админ rarely sees a race of “thin then thick”.

### Pattern 2: Allowlist-bound generation

**What:** Enricher prompt receives `{pass_1_article, extract_texts, allowed_urls}`. Output URLs are intersected with the allowlist before persist. Code fences are allowed; they are not claimed as transcript quotes.

**When to use:** Generated code + retrieved links in one JSON object.

**Trade-offs:** Stricter than “model cites whatever”. Drops hallucinated docs. Does not NLI-verify claims (out of scope).

### Pattern 3: Diagnostic stages without `IngestError.Stage`

**What:** `--debug` / `StageDiagnostics` may emit `classify` and `enrich` lines. `IngestError.stage` stays the locked seven values (`url|captions|metadata|consistency|llm|llm_truncation|persist`). Quota exhaustion is **not** an error envelope.

**When to use:** Fail-soft steps that must not change CLI exit-code contracts (`EXPECTED_SUCCESS_LINES`, collect `videos_failed`).

**Trade-offs:** Tests that pin `Stage` stay green. Operators still see enrich skip reasons in `--debug`.

---

## Data Flow

### Happy path (practical, quota remaining)

```
extract_video_id → captions → metadata → consistency
    → ArticleGenerator.process (pass 1)
    → TopicKindClassifier → practical
    → persist_draft_and_enqueue          # draft + shortlist
    → TavilyQuota.try_consume(n≤5)
    → search queries → extract → liveness
    → ArticleEnricher.process
    → write cheat sheet file
    → UPDATE materials body_markdown, source_links, cheat_sheet_path
    → return PersistResult (already_saved=false)
```

### Conceptual / quota miss / Tavily down

```
… pass 1 → persist → classify conceptual OR try_consume false OR adapter error
    → log (tavily_quota_exhausted | enrich_skipped)
    → return PersistResult unchanged
```

### `already_saved`

```
persist returns already_saved=true
    → zero classifier/Tavily/enricher calls
    → return immediately
```

### Key Data Flows

1. **Pass-1 article:** transcript-only; facts layer + СВА takeaway live in `body_markdown` so TOC/search/email preview keep working without a new renderer.
2. **Sources:** structured list (url, title, origin=`transcript|tavily`) stored on `materials`, mapped into `MaterialReaderResponse.sources`.
3. **Cheat sheet:** bytes on disk under `CHEAT_SHEET_ROOT / {material_id}.md`; column holds relative path; download copies razbor auth + containment.
4. **Quota:** `try_consume(n)` increments **our initiated requests** (each search or extract call), not Tavily billing credits.

### State Management

No new SPA client state. Reader is request/response. Operator state is DB quota row + material columns.

---

## Fail-closed vs fail-soft

| Step | Policy | Exit / rows |
|------|--------|-------------|
| URL / captions / metadata / consistency | fail-closed | existing `IngestError` |
| Pass-1 LLM / truncation | fail-closed | `stage=llm` / `llm_truncation`, zero rows |
| Persist pass-1 | fail-closed | `stage=persist` |
| Classifier invalid | fail-soft to `conceptual` | persist already done (or persist with conceptual) |
| Quota miss | fail-soft | log `tavily_quota_exhausted`, exit 0 |
| Tavily 4xx/5xx / timeout | fail-soft | log, keep pass-1 |
| Enricher invalid JSON | fail-soft | log, keep pass-1; do not persist partial guide |
| Cheat-sheet write fail after enrich | fail-soft on file; keep updated body if body UPDATE succeeded — prefer transactional: write file then UPDATE; if UPDATE fails, orphan file is OK, missing file hides CTA | |
| Collect timer | unchanged: `videos_failed` only on fail-closed stages | enrich skip ≠ failure |

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (weekly ingest-collect, ≤5 videos/source) | In-process two-pass is enough; per-video cap 5 keeps one talk off the 1000 |
| Many channels / 1000 cap hit mid-week | Pass-1 still ships; no multi-provider fallback (anti-feature) |
| Second writer (future HTTP ingest) | Quota RPC is the shared lock; do not use a local file |

### Scaling Priorities

1. **First bottleneck:** Tavily latency on extract (10–60s) inside `TimeoutStartSec=1800` — keep queries short, one extract batch, skip conceptual.
2. **Second bottleneck:** DeepSeek context on pass 2 (article + extracts) — cap extract chars; fail-soft on context_length rather than truncating silently.

---

## Anti-Patterns

### Anti-Pattern 1: Enrich inside the fail-closed `llm` stage

**What people do:** One `process()` that searches then writes; any Tavily error maps to `stage=llm` and **deletes** the chance of a draft.

**Why it's wrong:** Today's contract is “LLM fail ⇒ zero rows”. Search is optional. Operator loses the useful article.

**Do this instead:** Persist-then-enrich. `stage=llm` remains pass-1 only.

### Anti-Pattern 2: Widen `data_collection.__all__` for every new port

**What people do:** Export classifier, Tavily, enricher as public API.

**Why it's wrong:** `test_data_collection_public_api.py` pins ten names; extra exports become accidental contracts.

**Do this instead:** Private adapters + ports modules; composition imports them.

### Anti-Pattern 3: Route Tavily through the YouTube SOCKS5 proxy

**What people do:** Share one httpx client / `trust_env=True`.

**Why it's wrong:** Phase 28 measured YouTube TLS timeout vs DeepSeek direct TLSv1.3. Tavily is `api.tavily.com` — treat like DeepSeek (`trust_env=False`).

### Anti-Pattern 4: Reuse `razbors.notebook_path` for cheat sheets

**What people do:** Point material download at the razbor column/route.

**Why it's wrong:** Wrong aggregate; RLS/routes/UI all assume a разбор. Materials need `cheat_sheet_path` of their own.

### Anti-Pattern 5: Tool-calling DeepSeek that self-serves Tavily

**What people do:** One JSON session with function tools.

**Why it's wrong:** Quota becomes nondeterministic; pass-1 floor disappears; unit fakes explode.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| DeepSeek | existing `AsyncOpenAI` + stream json_object | Pass 1 + optional pass 2 + optional classifier call; all `trust_env=False` |
| Tavily | `AsyncTavilyClient` injected client | Search + Extract only. No Crawl/Map/Research. Composition passes `api_key`; adapter does not read `os.environ` |
| YouTube | unchanged captions/oEmbed | Description URLs feed the allowlist; still SOCKS5 for YouTube only |
| Postgres | RPC `try_consume_tavily_quota` + material UPDATE | Same service_role client as persist |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `data-collection` ↔ `ingestion-service` | Protocols + DTOs | New optional fields on `MaterialDraft`; pipeline injects new ports |
| `ingestion-service` ↔ Supabase | existing PersistPort + new QuotaPort | Quota adapter may live in supabase-integration |
| backend ↔ SPA | additive JSON | `extra="forbid"` on `MaterialReaderResponse` — must extend the model, not sneak keys |
| `ingest-collect` ↔ pipeline | same `run_ingest_pipeline` | `on_stage=None` in batch; enrich skip must not print `✓` extra lines that break the two-line stdout contract |

---

## Suggested build order

1. **Pass-1 templates only** — rewrite `lecture.md`/`podcast.md` + honesty prompt (facts layer + СВА/risks). No new ports. Existing `stage=llm` tests still apply.
2. **Classifier port + field on draft** — persist `topic_kind`; extras gated; default conceptual.
3. **Tavily ports + composition** — search/extract/liveness, `trust_env=False`, `SecretRegistry`, `__all__` unchanged.
4. **Quota RPC + `try_consume`** — global 1000, per-video cap, log on exhaust.
5. **Pass-2 enricher + allowlist** — fail-soft; persist-then-update body/sources.
6. **Cheat-sheet file + column** — write after enrich; containment copy of notebook storage.
7. **Reader + admin preview** — `sources[]`, download CTA only when file exists; Playwright.
8. **Collect/timer honesty** — enrich skip ≠ `videos_failed`; `already_saved` skips Tavily; timeout still 1800s.

Phases continue at **29**. Grouping into fewer roadmap phases is the roadmapper's job; do not invert this dependency order.

---

## Sources

- Live codebase: `ingest_pipeline.py`, `domain/errors.py` `Stage`, `data_collection/__init__.py` `__all__`, `MaterialReaderResponse`, `LocalNotebookStorage`, `persist_draft_and_enqueue`.
- `.planning/PROJECT.md` v1.5 locked two-pass behaviour.
- `.planning/research/STACK.md` (tavily-python 0.8.5, quota RPC, local cheat-sheet files).
- `.planning/research/FEATURES.md` (table stakes, anti-features, persist-then-enrich).
- `.planning/research/PITFALLS.md` (fail-closed graft, proxy, `__all__`, already_saved).
- Phase 28 measured proxy/TLS split.

---
*Architecture research for: Digest CDS v1.5 — two-pass article enrichment*
*Researched: 2026-10-26*
