# Stack Research

**Domain:** editorial ingest enrichment (two-pass article + Tavily + cheat sheet)
**Project:** Digest CDS (СВА editorial knowledge service)
**Milestone:** v1.5 — subsequent milestone on a shipped app (v1–v1.4 complete)
**Researched:** 2026-10-26
**Confidence:** HIGH (existing stack from `uv.lock`) / MEDIUM (Tavily SDK surface — Context7+PyPI; GSD `classify-confidence` returns MEDIUM even with `--verified`)
**Scope:** NEW capabilities only. Do **not** re-research the validated stack: Python 3.12 via `uv`, FastAPI, React/Vite, Playwright, pytest, `data-collection` + `ingestion-service` (Typer), DeepSeek via official OpenAI-compatible SDK (`openai>=3.0,<4`, locked **3.19.2**, async, `stream=True`, `json_object`, thinking disabled), YouTube captions (`youtube-transcript-api`) + SOCKS5 for YouTube only, DeepSeek `trust_env=False`, self-hosted Supabase (`supabase` locked **2.31.0**) + pgvector + Storage, article templates, `ArticleDraft` JSON, `persist_draft_and_enqueue`, TDD, Ports & Adapters, wiring only in `composition/`.

---

## Decision Summary (what v1.5 needs)

| # | Feature | Mechanism to add | New dependency? |
|---|---------|------------------|-----------------|
| Tavily Search + Extract | Official `AsyncTavilyClient` behind a `data-collection` port; injected `httpx.AsyncClient(trust_env=False)` | **Yes:** `tavily-python>=0.8.5,<0.9` on `data-collection` |
| Global 1000-request quota | PostgreSQL single-row table + `try_consume` RPC via existing `supabase-py` | **No** (SQL + existing client) |
| Per-video cap ~5 | Application counter on the port, env `TAVILY_MAX_REQUESTS_PER_VIDEO` default 5 | **No** |
| URL liveness | Existing `httpx==0.28.1`: HEAD then GET fallback, `trust_env=False`, https-only | **No** |
| Second DeepSeek pass | Reuse locked `openai` 3.19.2 / same `AsyncOpenAI` client; second `json_object` call, **not** tool-calling | **No** |
| Generated code | Markdown fenced blocks inside pass-2 JSON + cheat sheet. No Jupyter/nbformat | **No** |
| Cheat sheet file | Copy razbor `notebook_path`: `materials.cheat_sheet_path text` + `CHEAT_SHEET_ROOT` + FastAPI `FileResponse` | **No** (column + local FS) |

**Headline:** one new runtime package (`tavily-python` 0.8.x). Quota, liveness, second LLM pass, and cheat-sheet download all reuse `httpx`, `openai`, `supabase-py`, PostgreSQL, and the razbor local-file pattern. Do not add LangChain, CrewAI, DeepSeek tool-calling, Tavily Crawl/Map/Research, Redis, a quota file, or Supabase Storage for cheat sheets.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `tavily-python` (`AsyncTavilyClient`) | **0.8.5** current on PyPI (uploaded 2026-10-06, not yanked). Pin `>=0.8.5,<0.9` | Official Search + Extract client (ADR-0002 bend #2, same class as DeepSeek) | Official SDK owns auth headers, `search`/`extract` shapes, and typed errors (`UsageLimitExceededError`, `InvalidAPIKeyError`). `AsyncTavilyClient` accepts an injected `httpx.AsyncClient`, so composition can set `trust_env=False` the same way DeepSeek uses `DefaultAsyncHttpxClient(trust_env=False)`. Sync `TavilyClient` uses `requests.Session` and would leak `HTTP_PROXY`/`ALL_PROXY` (YouTube SOCKS5) unless carefully disabled — don't. |
| `httpx.AsyncClient` | **0.28.1** already pinned in `data-collection` | Tavily transport + URL liveness | Already the ingest HTTP standard (`youtube_oembed.py`, DeepSeek). Inject one client with `trust_env=False`, `timeout` ~30–60s for Tavily and a tighter timeout (~5s) for liveness. HEAD then GET on 405/501; `follow_redirects=True`; alive iff final status is 2xx. |
| PostgreSQL table `tavily_quota` + RPC `try_consume_tavily_quota(p_n int)` | self-hosted Postgres (existing Supabase VM) | Persistent 1000-request counter across CLI runs | Manual `ingest` and systemd `ingest-collect` must share one budget. A file next to the CLI races, dies on VM rebuild, and is invisible to the DB VM. A single-row table with `UPDATE … WHERE consumed + n <= 1000 RETURNING` is atomic, testable with an in-memory fake of the port, and matches `persist_draft_and_enqueue`. Cap is **requests we initiate** (each `search` or `extract` call = 1), not Tavily credits. |
| `openai` `AsyncOpenAI` (reuse) | locked **3.19.2** (`>=3.0,<4`) | Pass-2 enrichment JSON (guide, code, cheat-sheet markdown) | Pass 2 is a second `chat.completions.create` with `response_format={"type": "json_object"}`, `extra_body={"thinking": {"type": "disabled"}}`, `stream=True`. Same composition client, same `trust_env=False`. Tool-calling is not the path: Tavily is a separate port so quota/`try_consume` stays deterministic. |
| Local cheat-sheet files + `materials.cheat_sheet_path` | copy razbor `notebook_path` / `NOTEBOOK_ROOT` | Downloadable markdown attachment | Razbor already ships `LocalNotebookStorage` (`Path.resolve` containment, reject `..`/absolute) and `FileResponse`. Cheat sheets are the same shape with `text/markdown`. Ingest CLI and FastAPI already share the app VM, so a local root is reachable for write (CLI) and read (API). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `supabase` (existing) | locked **2.31.0** (`ingestion-service` `>=2.0,<3`; `supabase-integration` `>=2.31.0,<3`) | `try_consume` RPC + persist `cheat_sheet_path` / updated body | Service-role client already built in `ingestion-service/composition/clients.py`. No new driver. |
| `storage3` (transitive of supabase) | locked **2.31.0** | — | **Do not use** for cheat sheets. Available, not chosen. |
| `ipaddress` + `urllib.parse` | stdlib 3.12 | SSRF guard on Tavily/video URLs before httpx | Allow `https` only; reject loopback/link-local/private/metadata hosts after DNS/IP check. No extra package. |
| `tiktoken` | transitive of `tavily-python` (`>=0.5.1`) | SDK internal | Do **not** import in our code. Do **not** add it as a direct dep. |
| `requests` | already present (`youtube-transcript-api` / `tavily-python` sync client) | SDK transitive | Do **not** construct `TavilyClient` (sync) in adapters. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `uv add --package data-collection` | Add `tavily-python` | Workspace rule: never pip. Then `uv sync`. |
| pytest + in-memory fakes | Tavily port, quota port, liveness port, cheat-sheet storage | Unit tests never hit `api.tavily.com`. Map `UsageLimitExceededError` → fail-soft at the adapter boundary. |
| pytest `integration` marker (existing) | Optional live Tavily Search/Extract | Keep out of default `testpaths`. Needs `TAVILY_API_KEY`. |
| Playwright (existing) | Reader sources block + cheat-sheet download | No new FE library. Authenticated `FileResponse` like `/razbory/{id}/notebook`. |
| FastAPI `FileResponse` | Cheat-sheet download | `media_type="text/markdown"`, `content_disposition_type="attachment"`, JWT via `get_principal`. Path escapes → 400; missing → 404 (disabled download in UI). |

---

## Installation

```bash
# Only new runtime package — from repo root, uv workspace
uv add --package data-collection "tavily-python>=0.8.5,<0.9"
uv sync
```

Env (composition only — `ingestion-service/composition/settings.py` + `backend` `CHEAT_SHEET_ROOT`):

```bash
TAVILY_API_KEY=tvly-...
TAVILY_MAX_REQUESTS_PER_VIDEO=5
CHEAT_SHEET_ROOT=/var/lib/digest-cds/cheat-sheets
```

Do **not** set Tavily proxy env. Do **not** let adapters read `os.environ`. Pass `api_key` into `AsyncTavilyClient` explicitly so the SDK does not fall back to `TAVILY_API_KEY` inside the adapter.

---

## Integration points (wiring)

```
ingestion-service/composition/
  Settings.tavily_api_key, tavily_max_requests_per_video, cheat_sheet_root
  build_tavily_httpx_client() -> httpx.AsyncClient(trust_env=False, timeout=60)
  build_tavily_client()        -> AsyncTavilyClient(api_key=..., client=httpx)
  build_tavily_quota()         -> Supabase RPC adapter (service-role)
  build_url_liveness()         -> httpx HEAD/GET adapter (trust_env=False, timeout=5)
  reuse build_async_deepseek_client() for pass 2
  build_cheat_sheet_storage()  -> write under CHEAT_SHEET_ROOT

data-collection/
  ports: TavilySearch, UrlLiveness  (adapters wrap SDK; map SDK errors → domain)
  pass-1 ArticleGenerator unchanged except richer template JSON
  pass-2 ArticleEnricher: DeepSeek json_object, no tools

supabase-integration/migrations/
  tavily_quota (id=1, consumed, cap=1000)
  try_consume_tavily_quota(p_n int) → {ok, consumed, remaining}
  materials.cheat_sheet_path text null
  optional materials.source_urls text[]  (reader sources block)

backend/
  CHEAT_SHEET_ROOT + LocalCheatSheetStorage (clone LocalNotebookStorage)
  GET /materials/{slug}/cheat-sheet → FileResponse
```

**Quota semantics:** `try_consume(n)` **before** each Tavily call. If `ok=false`, log `tavily_quota_exhausted`, skip remaining Tavily work, persist pass-1 draft. Per-video: stop at 5 (default) even if global remaining is high. Count **our** HTTP calls to Tavily (`search` and `extract` each = 1), not Tavily's credit field (`include_usage` can be 0 until extract batches of 5).

**Tavily call shape (opinionated defaults):**
- `search(..., search_depth="basic", max_results=5, include_answer=False, include_raw_content=False, auto_parameters=False, include_usage=True)`
- Liveness-filter hits with httpx (does **not** consume Tavily quota)
- `extract(urls, extract_depth="basic", format="markdown")` for the live subset, batched so one extract = one quota unit
- Do not enable Crawl / Map / Research — they burn credits and are out of scope

**Cheat sheet write:** CLI writes `{youtube_video_id}.md` (or slug) under `CHEAT_SHEET_ROOT`, then stores the relative basename in `cheat_sheet_path`. Conceptual materials leave the column null. Reader shows download only when the path resolves to a file.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `tavily-python` `AsyncTavilyClient` | Raw `httpx` POST to `https://api.tavily.com/search` and `/extract` | Only if the SDK starts reading env inside adapters with no injection seam, or pins a breaking `httpx`. Today it accepts `client=httpx.AsyncClient` — no reason to hand-roll. |
| `AsyncTavilyClient` | Sync `TavilyClient` + `requests.Session(trust_env=False)` | Never for this pipeline. Ingest LLM is already async; mixing a blocking `requests` call inside the event loop is avoidable. |
| Postgres `tavily_quota` + RPC | JSON/SQLite file next to the CLI | Only a laptop spike with no systemd timer. Production has two entrypoints (`ingest` + `ingest-collect`) and a separate DB VM — the counter belongs in Postgres. |
| Postgres table | Redis / Tavily `/logs` | Redis is a new runtime. `/logs` needs a paid plan, is after-the-fact, and counts Tavily credits — not our 1000 requests. |
| `cheat_sheet_path` + `CHEAT_SHEET_ROOT` | Supabase Storage (`storage.from_(bucket).upload`) | Use Storage only if ingest and API later split hosts so the file is unreachable. Today razbor notebooks already chose local path + `FileResponse`; duplicating that is cheaper and keeps RLS/buckets out of v1.5. |
| Second DeepSeek `json_object` call | DeepSeek native tool-calling / OpenAI tools wrapping Tavily | Tool-calling makes `try_consume` and the per-video cap non-deterministic (the model decides how many calls). Two-pass is the product. |
| `search_depth="basic"` | `advanced` / `auto_parameters=True` | Advanced costs 2 Tavily credits and can be auto-selected by `auto_parameters`. Stay on basic until the 1000-request budget is proven too shallow. |
| httpx HEAD+GET liveness | Tavily `extract` as the liveness check | Extract consumes quota. Check first with httpx, extract only live URLs. |
| httpx liveness | Playwright / browser fetch | Absurd for ingest. No browser in the CLI. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| LangChain, `langchain-tavily`, CrewAI, LlamaIndex agents | New orchestration layer, hidden retries, tool loops that ignore `try_consume`. Quality gate forbids them as the primary path. | Ports in `data-collection` + use-cases in `ingestion-service` |
| DeepSeek / OpenAI native tool-calling for Tavily | Model-driven call count breaks the 1000-request and per-video caps | Explicit pass 2 after a bounded Tavily port |
| `TavilyClient()` keyless mode | Rate-limited public API, no production key, `TavilyKeylessLimitError` | `AsyncTavilyClient(api_key=settings.tavily_api_key, client=...)` |
| Tavily Crawl, Map, Research | Extra endpoints, extra credits, not required for “short queries + extract” | `search` + `extract` only |
| Constructing Tavily/DeepSeek clients inside adapters | Adapters would read `os.environ` / inherit YouTube proxy (violates D-17) | Wire in `ingestion-service/composition/clients.py` |
| Redis, memcached, or a quota JSON file | New infra or lost counter across systemd runs | `tavily_quota` row + RPC |
| `supabase.storage` for cheat sheets | Extra bucket/RLS; razbor already rejected this for `notebook_path` | `cheat_sheet_path` + `CHEAT_SHEET_ROOT` + `FileResponse` |
| `nbformat` / Jupyter / `markdown` pip package | Cheat sheet is a markdown file the reader downloads, not a notebook | Write UTF-8 `.md` with stdlib `Path.write_text` |
| Extra HTTP stacks (`aiohttp`, extra `requests` usage, `urllib3` directly) | `httpx` 0.28.1 is already pinned | Injected `httpx.AsyncClient` |
| Counting Tavily `usage.credits` as our 1000 | Credits ≠ requests; `include_usage` may be 0; extract batches of 5 share a credit | Count each SDK `search`/`extract` invocation |

---

## Stack Patterns by Variant

**If the topic is `conceptual`:**
- Use pass 1 only (richer template, no Tavily, no cheat sheet, no generated code)
- Because product: Tavily/code/guide/cheat sheet attach only when `practical`

**If `practical` and `try_consume` succeeds:**
- Use Tavily `search` (basic) → httpx liveness → Tavily `extract` (basic, markdown) → DeepSeek pass 2
- Because two-pass keeps quota on our side of the port

**If quota exhausted or Tavily 429/`UsageLimitExceededError` or missing live URLs:**
- Use pass-1 draft persist + log `tavily_quota_exhausted` (or mapped adapter reason)
- Because fail-soft is a v1.5 success criterion

**If ingest and API are later split across hosts:**
- Use Supabase Storage then (existing `storage3` 2.31.0, `text/markdown` content-type)
- Because local `CHEAT_SHEET_ROOT` would no longer be shared. Do not pre-build this.

**If YouTube SOCKS5 is set (`YOUTUBE_PROXY_URL`):**
- Keep Tavily and DeepSeek on `trust_env=False` with **no** proxy argument
- Because Phase 28 measured that YouTube needs the proxy and DeepSeek must stay direct; Tavily is a second public API in the DeepSeek class

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `tavily-python` 0.8.5 | `httpx==0.28.1` | SDK requires `httpx` unpinned; keep the existing pin. Inject `AsyncClient`; do not let the SDK build a default client that trusts env. |
| `tavily-python` 0.8.5 | `requests` (already in `data-collection`) | Sync extra; unused if we only import `AsyncTavilyClient`. |
| `tavily-python` 0.8.5 | `tiktoken>=0.5.1` (new transitive) | Do not import. Watch `uv lock` / pip-audit; existing constraints cover `multidict` and `pyjwt` only. |
| `openai` 3.19.2 | DeepSeek `json_object` + `thinking.disabled` + `stream=True` | Already proven live (ING-09). Pass 2 reuses this exact call shape. |
| `supabase` 2.31.0 | Postgres RPC `try_consume_tavily_quota` | Same `.rpc(name, params).execute()` pattern as `persist_draft_and_enqueue`. |
| `httpx` 0.28.1 | `trust_env=False`, `follow_redirects=True`, HEAD/GET | Official: env proxies are ignored only when `trust_env=False`. Default is **not** to follow redirects — set it explicitly for liveness. |
| Python | `>=3.12` | Unchanged. `tavily-python` requires `>=3.8`. |

---

## Sources

- `/tavily-ai/tavily-python` (Context7) — `AsyncTavilyClient` constructor (`client: Optional[httpx.AsyncClient]`), `search`/`extract` signatures, timeouts, `UsageLimitExceededError`. Confidence: MEDIUM (classifier).
- `/websites/tavily` (Context7) — Search basic=1 credit / advanced=2; Extract basic=1 credit per 5 successful URLs; `include_usage`; `/logs` paid-only. Confidence: MEDIUM.
- https://pypi.org/pypi/tavily-python/json — version **0.8.5**, requires `requests`, `tiktoken>=0.5.1`, `httpx`, upload **2026-10-06T15:11:33Z**, not yanked. Confidence: MEDIUM (classifier) / first-party registry.
- https://docs.tavily.com/sdk/python/reference — Search + Extract Python SDK reference (retrieved 2026-10-26).
- `/supabase/supabase-py` (Context7) — `storage.from_(bucket).upload` / `.download`; default mime `text/plain`. Confidence: MEDIUM.
- `/encode/httpx` (Context7) — `trust_env=False` disables `HTTP_PROXY`; `follow_redirects` defaults off. Confidence: MEDIUM.
- First-party `uv.lock` — `httpx` 0.28.1, `openai` 3.19.2, `supabase`/`storage3` 2.31.0. Confidence: HIGH.
- First-party razbor pattern — `razbors.notebook_path`, `NOTEBOOK_ROOT`, `LocalNotebookStorage`, `FileResponse` (`backend/src/backend/infrastructure/local_notebook_storage.py`). Confidence: HIGH.
- First-party ingest composition — `build_async_deepseek_client` + `DefaultAsyncHttpxClient(trust_env=False)` (`ingestion-service/src/ingestion_service/composition/clients.py`). Confidence: HIGH.

---

*Stack research for: editorial ingest enrichment (Digest CDS v1.5)*
*Researched: 2026-10-26*
