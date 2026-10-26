# Project Research Summary

**Project:** Digest CDS
**Domain:** editorial ingest enrichment (two-pass article + Tavily + cheat sheet) — subsequent milestone v1.5 on a shipped app (v1–v1.4 complete)
**Researched:** 2026-10-26
**Confidence:** HIGH (local contracts, existing stack, feature shape) / MEDIUM (Tavily SDK billing surface, extract-batch 400 behaviour)

## Executive Summary

Digest CDS is a shipped editorial knowledge service for СВА Сбербанка. v1.5 does **not** rebuild ingest or the reader: it replaces the dry three-block DeepSeek summary with a two-pass article. Pass 1 always writes a content-shaped, transcript-grounded СВА article (facts layer + «зачем СВА» + risks) and **always persists** a `materials` draft. Pass 2 runs only when the classifier says `practical`: bounded Tavily Search + Extract, then a second DeepSeek `json_object` stream that may add in-article guide sections, generated code, verified links, and a downloadable markdown cheat sheet. Experts in review-first newsletters and Diátaxis knowledge bases do this same split — retrieve-then-enrich after a grounded draft, never search-first writing, never auto-publish.

The recommended approach is one new runtime package (`tavily-python>=0.8.5,<0.9` `AsyncTavilyClient` with injected `httpx.AsyncClient(trust_env=False)`) plus reuse of locked `openai` 3.19.2, `httpx` 0.28.1, `supabase` 2.31.0, PostgreSQL, and the razbor local-file download pattern. Quota lives in Postgres (`tavily_quota` + atomic `try_consume` RPC, cap 1000 **requests we initiate**, ~5 per video). Cheat sheets copy `NOTEBOOK_ROOT` / `FileResponse`, not Supabase Storage. Backend/SPA stay readers. Do not add LangChain, DeepSeek tool-calling, Tavily Crawl/Map/Research, Redis, a quota file, or an admin «Обогатить» button.

The dominant risk is grafting optional Tavily onto today's **fail-closed** `stage=llm` path so a 429, quota miss, or bad pass-2 JSON deletes a finished pass-1 draft — or so re-runs burn the 1000-request budget on `already_saved` videos. Mitigate with persist-then-enrich (fail-soft pass 2), an exists-check **before** Tavily, atomic DB quota, Tavily on a DeepSeek-class client (`trust_env=False`, never the YouTube SOCKS5 proxy), a code-side URL allowlist (transcript ∪ extract successes), and locked `__all__` / `Stage` / stdout contracts. Phase numbering **continues at 29** (v1.4 ended at 28).

## Key Findings

### Recommended Stack

Summary of [STACK.md](STACK.md). Validated stack (Python 3.12/`uv`, FastAPI, React/Vite, Playwright, pytest, DeepSeek via `openai` 3.19.2 streaming `json_object`, YouTube captions + SOCKS5, DeepSeek `trust_env=False`, self-hosted Supabase) is **not** re-opened. v1.5 adds **one** runtime package.

**Core technologies:**
- **`tavily-python` `AsyncTavilyClient` 0.8.5** (`>=0.8.5,<0.9` on `data-collection`) — official Search + Extract; accepts injected `httpx.AsyncClient`. Sync `TavilyClient` uses `requests` and would inherit `HTTP_PROXY`.
- **`httpx.AsyncClient` 0.28.1** (already pinned) — Tavily transport (`trust_env=False`, timeout ~30–60s) and URL liveness (HEAD then GET, ~5s, https-only, `follow_redirects=True`). Liveness does **not** consume Tavily quota.
- **Postgres `tavily_quota` + RPC `try_consume_tavily_quota(p_n int)`** — shared 1000-request ledger for operator `ingest` and systemd `ingest-collect`. Count each SDK `search`/`extract` call as 1, **not** Tavily credits / `include_usage`.
- **`openai` `AsyncOpenAI` 3.19.2** (reuse) — pass-2 enrichment is a second `chat.completions.create` with `json_object`, `thinking.disabled`, `stream=True`. Not tool-calling.
- **Local cheat-sheet files + `materials.cheat_sheet_path`** — copy razbor `notebook_path` / `NOTEBOOK_ROOT` / `LocalNotebookStorage` / authenticated `FileResponse` (`text/markdown`). Do not use `storage3`.

**Explicitly rejected:** LangChain/CrewAI, DeepSeek tool-calling wrapping Tavily, sync `TavilyClient`, Tavily Crawl/Map/Research, Redis or a quota JSON file, Supabase Storage for cheat sheets, `nbformat`/Jupyter, counting Tavily `usage.credits` as the 1000.

**Tavily call shape:** `search(..., search_depth="basic", max_results=5, include_answer=False, include_raw_content=False, auto_parameters=False, include_usage=True)` → httpx liveness → `extract(urls, extract_depth="basic", format="markdown")` batched so one extract = one quota unit.

**Env (composition only):** `TAVILY_API_KEY`, `TAVILY_MAX_REQUESTS_PER_VIDEO` default 5, `CHEAT_SHEET_ROOT`. Adapters do not read `os.environ`.

### Expected Features

Summary of [FEATURES.md](FEATURES.md). Auth, issue/archive, voting, knowledge search, разборы, admin shortlist→send, and YouTube→DeepSeek ingest are **shipped consumers**, not rebuild targets. Pass 1 *is* the product; pass 2 is a gated enhancement.

**Must have (table stakes):**
- Content-shaped article sections (rewrite `lecture.md` / `podcast.md`) — not the three-block scaffold; TOC already follows `##`.
- Dedicated source-facts layer from the transcript only (names, numbers, tools, caveats).
- Explicit «зачем СВА» + risks in the body (editorial inference allowed; keep `dek` as the hook).
- Classifier `practical | conceptual` on every ingest; invalid/empty → `conceptual`; extras only on practical.
- Pass 1 always persists a complete draft + shortlist row; Tavily skip does not delete it.
- In-article guide as extra `##` sections (not a second file); generated code allowed and marked generated.
- Links = transcript/description URLs ∪ Tavily pages that actually opened; drop `failed_results`; post-filter allowlist in code.
- Cheat sheet = downloadable `.md` on practical materials that produced one; hide CTA when absent.
- Reader sources block + admin preview parity (same DTO).
- Global Tavily 1000 + per-video ~5 via `try_consume`; log `tavily_quota_exhausted`; unattended on existing CLI/timer.
- Honest absence: no empty «Гайд», no greyed download, no “ссылки скоро появятся”.
- Operator `--debug`/journal: classifier, remaining quota, opened vs failed URL **counts** — no secrets, no extract bodies.

**Should have (competitive):**
- Audit takeaway beyond what the talk said (labeled editorial).
- Classifier-gated Tavily (do not search conceptual talks — saves the 1000).
- Live-URL allowlist from extract successes (liveness, not NLI).
- Pass-1 article remains useful when pass 2 is skipped.

**Defer (v1.x / v2+):**
- Re-ingest that *updates* enrichment on an existing `youtube_video_id` (P2 — needed if pass 2 died after persist; default v1.5 is skip).
- Quiet admin-preview “обогащение не выполнялось” note (only if UAT surprise).
- Index cheat-sheet text in knowledge search (P3).
- FoundryModels, CiteGuard/NLI, admin Enrich button, HTTP ingest API, auto-publish, material `.ipynb`, v1.4 `INVALID_ROLE` toast.

**Anti-features (do not build):** admin «Обогатить», tool-calling one-shot, Tavily-first inverted writing, invented URLs, second “гайд” file, code/Tavily/cheat sheet on conceptual talks, multi-provider search fallback, reader-facing quota/classifier badges, executing generated code.

### Architecture Approach

Summary of [ARCHITECTURE.md](ARCHITECTURE.md). Dual-hexagon (backend reader vs ingestion-service writer, shared Supabase) is **shipped and not re-litigated**. Pass 2 **never** raises `IngestError`. `IngestError.stage` stays the locked seven values.

**Major components:**
1. **`TopicKindClassifier`** — closed `practical | conceptual`; fail-closed to conceptual; port in `data-collection/ports/`.
2. **`WebSearchPort` / `PageExtractPort` / `UrlLivenessPort`** — Tavily search+extract + httpx HEAD/GET; SDK errors mapped at the adapter; no local page fetch (SSRF).
3. **`TavilyQuota`** — atomic `try_consume(n)` against global 1000; in-memory fake in unit tests.
4. **`ArticleEnricher`** — pass-2 JSON (guide, code, cheat-sheet md) bound to `{pass_1_article, extract_texts, allowed_urls}`; URLs intersected in code after the LLM.
5. **`CheatSheetStorage`** — write/read markdown under `CHEAT_SHEET_ROOT`; clone `LocalNotebookStorage` containment.
6. **`run_ingest_pipeline`** — classify → persist pass-1 → optional enrich/update; `already_saved` short-circuits the whole chain.
7. **Reader delivery** — additive `sources[]` + `GET /materials/{slug}/cheat-sheet` `FileResponse`; `extra="forbid"` on `MaterialReaderResponse` must be extended.

**Key patterns:** persist-then-enrich (fail-soft floor); allowlist-bound generation; diagnostic stages (`classify`/`enrich`) without new `IngestError.Stage`. Public `data_collection.__all__` stays **exactly ten names**. Wiring only in `ingestion-service/composition/`. Conceptual / quota miss / Tavily down → log and return unchanged `PersistResult`. Collect `videos_failed` only on fail-closed stages.

### Critical Pitfalls

Top items from [PITFALLS.md](PITFALLS.md). Full set is 12; these five kill the milestone if missed.

1. **Fail-closed enrich drops a finished pass-1 draft** — do not fold Tavily/pass-2 into `article.process` / `ArticleError` → `stage=llm`. Pass-1 stay fail-closed; pass-2 fail-soft; persist spy must fire on Tavily 429; collect `videos_failed` must not increment.
2. **`already_saved` after paid work** — today's uniqueness check is at persist, after captions+LLM. Exists-check **before** Tavily (and cheaply before LLM). Default: skip, no silent `ON CONFLICT DO UPDATE`. Second ingest → 0 Tavily calls.
3. **Quota race + wrong unit** — operator `ingest` has no `flock`. Atomic `UPDATE … WHERE remaining >= n RETURNING`. Count HTTP calls we dispatch (search=1, extract POST=1). Pin `search_depth="basic"`; never crawl/map/research; do not gate on `include_usage`.
4. **Tavily inherits the YouTube SOCKS5 proxy** — Phase 28: YouTube needs proxy, DeepSeek must not. New `build_tavily_client` with `trust_env=False`, `proxy is None`. Never reuse `build_httpx_client(settings)`.
5. **Hallucinated / search-only / failed-extract URLs** — allowlist in code (transcript URLs ∪ extract `results[].url` with non-empty content). Strip markdown hrefs outside the set after the LLM. Prompt-only honesty is insufficient.

Also lock: source-facts frozen against web extracts (Pitfall 3); no local `httpx.get` of page URLs (Pitfall 7, SSRF); persist pass-1 before Tavily so `TimeoutStartSec=1800` kill does not lose the article (Pitfall 8); cheat sheet is **not** `razbors.notebook_path` and **not** stuffed into `body_markdown` (Pitfall 9); `__all__` / `Stage` / `EXPECTED_SUCCESS_LINES` / `tvly-` `SecretRegistry` (Pitfalls 10, 12); pass-2 streams and has its own extract cap — overflow skips enrich, does not raise `llm_truncation` (Pitfall 11). Classifier default is **conceptual**.

## Implications for Roadmap

Phase numbering **continues at 29**. Do not restart at 1. Eight sequential phases — do not invert this order. Templates + classifier + persist floor **before** Tavily; Tavily port + quota **before** enricher; enricher **before** reader/admin DTO. Do not wait on cheat-sheet UI to ship a better article body.

### Phase 29: Pass-1 richer templates
**Rationale:** Improves every article (conceptual and quota-skipped practical) with zero new ports or Tavily. Locks the section contract (facts vs СВА takeaway) before web text exists.
**Delivers:** Rewritten `lecture.md` / `podcast.md` + honesty prompt: content-shaped `##`, source-facts layer, «зачем СВА» + risks. Pass-1 still streams; `stage=llm` / `llm_truncation` unchanged.
**Addresses:** Content-shaped sections, facts layer, audit takeaway (table stakes).
**Avoids:** Pitfall 3 (facts stay transcript-only); Pitfall 11 (do not apply transcript cap to future extracts); Pitfall 1 invariant (pass-1 remains fail-closed). Do **not** invent the cheat-sheet file here.

### Phase 30: Classifier `practical | conceptual`
**Rationale:** The gate for every extra. Must exist before Tavily so conceptual talks never spend quota.
**Delivers:** `TopicKindClassifier` port + field on `ArticleDraft`/`MaterialDraft`; invalid/empty → `conceptual`; extras stay off. Persist `topic_kind`.
**Addresses:** Classifier; extras only on practical; honest absence on conceptual.
**Avoids:** Pitfall 8 (default conceptual so unattended collect does not empty 1000); classifier bias toward “helpful” practical.

### Phase 31: Tavily port + composition (no enricher yet)
**Rationale:** Adapter, proxy/TLS, secrets, and locked public API must be green before any pipeline call that can burn quota or leak `tvly-`.
**Delivers:** `WebSearch` / `PageExtract` / `UrlLiveness` ports; `AsyncTavilyClient` + injected `httpx` `trust_env=False`; `SecretRegistry` + `tvly-` denylist; SSRF pre-validate (https, public host); `__all__` stays 10 names. No Crawl/Map/Research.
**Uses:** `tavily-python` 0.8.5, `httpx` 0.28.1, composition factories next to DeepSeek.
**Avoids:** Pitfalls 5, 7, 10, 12 (proxy, local fetch, exports, key leak). Measure TLS to `api.tavily.com` without the YouTube proxy (Phase 28-style precondition).

### Phase 32: Quota `try_consume` + persist-then-enrich floor
**Rationale:** Shared ledger and fail-soft persist must exist before the enricher can call Tavily. Exists-check designed here so quota tests can prove zero consume on `already_saved`.
**Delivers:** Migration `tavily_quota` + RPC; global 1000; per-video ~5; log `tavily_quota_exhausted`; persist pass-1 anyway; `PersistPort.exists(youtube_video_id)` short-circuit **before** Tavily. `Stage` set unchanged; no fourth stdout checkmark.
**Addresses:** Quota table stakes; persist pass-1 when pass 2 skipped.
**Avoids:** Pitfalls 1, 2, 4 (fail-closed graft, paid re-runs, race/wrong unit). Collect remaining=0 still persist pass-1, exit 0.

### Phase 33: Pass-2 enricher + allowlist
**Rationale:** Quota and Tavily ports are now deterministic; enricher can fail-soft onto the saved row.
**Delivers:** Search short queries → liveness → one extract batch → `ArticleEnricher` (streamed `json_object`); frozen source-facts post-check; URL post-filter; in-article guide + optional generated code; extract-context cap skips enrich (not `llm_truncation`); UPDATE same material row.
**Implements:** `ArticleEnricher`, allowlist-bound generation.
**Avoids:** Pitfalls 1, 3, 6, 7, 11 (JSON/budget, hallucinated URLs, extract 400, facts contamination). Fence extracts as untrusted data.

### Phase 34: Cheat-sheet file persist
**Rationale:** File is the practical extra; body/sources already update in 33. Storage must not reuse `razbors.notebook_path`. `already_saved` skip must not insert a second file.
**Delivers:** `materials.cheat_sheet_path`; `CHEAT_SHEET_ROOT`; write `{id}.md` then UPDATE; conceptual / quota-skip → null. Copy `LocalNotebookStorage` containment.
**Addresses:** Cheat-sheet markdown download (writer side).
**Avoids:** Pitfalls 2, 9 (exists-skip; wrong storage / body dump). No `ON CONFLICT DO UPDATE`.

### Phase 35: Reader sources block + cheat-sheet download
**Rationale:** Backend/SPA only display what ingest wrote. Preview parity is free if the reader DTO is extended once (`extra="forbid"`).
**Delivers:** `MaterialReaderResponse.sources`; `GET /materials/{slug}/cheat-sheet` auth `FileResponse`; CTA only when file exists; admin preview reuses the same DTO; Playwright. SPA does not call Tavily.
**Addresses:** Reader sources block, admin preview parity, honest absence.
**Avoids:** Pitfalls 6, 9 (second unfiltered sources list; razbor download reuse; XSS from extract HTML — download as file, article markdown through existing sanitizer).

### Phase 36: `ingest-collect` honesty
**Rationale:** Unattended path is where quota, timer kill, and false `OnFailure=` actually fire. Last because it integrates 29–35 rather than adding product surface.
**Delivers:** Enrich skip ≠ `videos_failed`; `tavily_quota_exhausted` via collect `emit_diagnostic` (journal, not only `--debug`); exists-check on operator+timer mix; `TimeoutStartSec=1800` still holds (skip pass-2 if wall-clock tight); `EXPECTED_SUCCESS_LINES` byte-identical; collect `str(err)` sanitized.
**Avoids:** Pitfalls 2, 4, 8, 10, 12. Do not raise `INGEST_MAX_VIDEOS_PER_SOURCE`.

### Phase Ordering Rationale

- Pass-1 templates (29) have no Tavily dependency and raise the floor for every video — ship them first.
- Classifier (30) is the budget gate; Tavily (31) before quota (32) would let tests hit the network without a ledger.
- Enricher (33) after quota so `try_consume` is deterministic; cheat-sheet (34) after enricher so the file is produced only when pass 2 succeeded.
- Reader (35) after columns/files exist; collect (36) last so timer/exit/journal contracts are proven against the full chain.
- Grouping 31+32 or 34+35 is the roadmapper's option; **do not** put enrich before persist, cheat-sheet UI before the body, or collect before fail-soft.

### Research Flags

Phases likely needing `/gsd-plan-phase --research-phase <N>` during planning:
- **Phase 31:** Tavily SDK constructor/`search`/`extract` shapes and TLS to `api.tavily.com` from the operator host are MEDIUM / unmeasured. Confirm `AsyncTavilyClient(client=httpx)` still ignores env; record the second ADR-0002 public-API bend.
- **Phase 32:** Quota **unit** (our HTTP calls vs Tavily credits) and the remaining=3 vs per-video=5 rule must be locked in the plan. Concurrent `try_consume` RPC shape needs a migration spike.
- **Phase 33:** Extract whole-POST 400 on one bad URL is community-MEDIUM; prompt-injection fencing and frozen-facts comparison need a concrete delimiter/normalization rule.
- **Phase 36:** Persist-then-update vs “skip pass-2 when wall-clock remaining < bound” under `TimeoutStartSec=1800` needs a measured budget (extract 10–60s + second DeepSeek stream). Collect sanitize path is currently `f"{err}"`.

Phases with standard patterns (skip research-phase):
- **Phase 29:** Template + DeepSeek `json_object` stream — copy Phase 8/28 call shape.
- **Phase 30:** Second small JSON call or extra field on pass-1 draft — same client, same honesty mapper.
- **Phase 34:** Clone `LocalNotebookStorage` / `NOTEBOOK_ROOT` / relative basename.
- **Phase 35:** Clone razbor notebook download (auth, containment, honest 404) onto a **new** materials route; extend `MaterialReaderResponse` like Phase 18 preview reuse.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH (existing lock) / MEDIUM (Tavily) | `uv.lock` httpx 0.28.1, openai 3.19.2, supabase 2.31.0 is first-party HIGH. Tavily 0.8.5 PyPI + Context7 SDK classified MEDIUM even `--verified`. |
| Features | HIGH | Owner-locked two-pass shape + shipped ingest/reader. Analog products (Diátaxis, Tavily credits, newsletters) MEDIUM. |
| Architecture | HIGH | Integration points read from live `ingest_pipeline.py`, `Stage`, `__all__`, `MaterialReaderResponse`, razbor file pattern. Tavily internals inherit STACK MEDIUM. |
| Pitfalls | HIGH (local) / MEDIUM (vendor) | Fail-closed graft, `already_saved`, proxy split, `__all__`/stdout measured on this checkout. Tavily billing/extract-400 from Context7 + one community issue. |

**Overall confidence:** HIGH for “what to build and in what order”; MEDIUM for Tavily credit accounting and live TLS to `api.tavily.com`.

### Gaps to Address

- **Tavily TLS from the operator host** — Phase 28 measured YouTube (needs SOCKS5) vs DeepSeek (direct). `api.tavily.com` is unmeasured. Phase 31 must probe once; if it fails, that is a spike — do **not** silently fall back to the YouTube proxy.
- **Quota remaining vs per-video cap** — if remaining=3 and per-video needs 5, enrich 0 videos or consume 3? Lock in Phase 32. Recommendation: skip pass-2 unless `try_consume` can grant the planned `n` for that video (fail-soft, keep pass-1).
- **Classifier implementation** — extra DeepSeek JSON call vs extra field on pass-1 `ArticleDraft`. Architecture allows either; prefer a **separate** cheap call so pass-1 honesty prompt stays transcript-only (avoids Pitfall 3). Decide in Phase 30 planning.
- **Exists-check vs LLM cost** — Pitfall 2 wants skip before Tavily; also “cheaply before LLM”. v1.5 must skip Tavily; skipping DeepSeek on already-saved ids is in-scope if `PersistPort.exists` is cheap (Phase 24 high-water mark precedent). Silent body UPDATE is **out**.
- **Re-ingest / backfill** — dry v1.1 articles will not gain cheat sheets on re-run. That is correct for v1.5. Do not slip `ON CONFLICT DO UPDATE`. Schedule a later command if product wants backfill.
- **`tiktoken` transitive** — `tavily-python` pulls `tiktoken>=0.5.1`. Do not import; watch `uv lock` / pip-audit (existing constraints cover `multidict` and `pyjwt` only).
- **ADR-0002** — record the second public foreign-API bend next to DeepSeek. FoundryModels still not this milestone.
- **Cheat-sheet vs Storage** — local `CHEAT_SHEET_ROOT` is correct while CLI and API share the app VM (same as razbor). If hosts split later, use existing `storage3` 2.31.0 — do not pre-build.
- **Collect live-run** — `pipeline_ingest_sources` still has no rows (v1.3 residual). Phase 36 journal/exit proofs can be unit/integration against fakes; a live Tavily collect tick is optional and needs `TAVILY_API_KEY`.
- **v1.4 `INVALID_ROLE` toast** — parked; do not pull into 29–36.

## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` — v1.5 goal, locked two-pass behaviour, phase numbering continues at 29 (2026-10-26).
- First-party `uv.lock` — `httpx` 0.28.1, `openai` 3.19.2, `supabase`/`storage3` 2.31.0.
- Live ingest: `run_ingest_pipeline`, `Stage` seven values, `data_collection.__all__` ten names, `persist_draft_and_enqueue` `ON CONFLICT DO NOTHING`, `EXPECTED_SUCCESS_LINES`, `SecretRegistry` (DeepSeek + Supabase + YouTube proxy only).
- Razbor pattern: `razbors.notebook_path`, `NOTEBOOK_ROOT`, `LocalNotebookStorage`, `FileResponse`.
- Composition: `build_async_deepseek_client` + `DefaultAsyncHttpxClient(trust_env=False)`; YouTube SOCKS5 only on captions/oEmbed (Phase 28 measured).
- `CONTEXT.md` personas; US-05 / US-07 / US-09 / US-20.
- systemd: `TimeoutStartSec=1800`, `flock` on collect only, `INGEST_MAX_VIDEOS_PER_SOURCE` default 5.

### Secondary (MEDIUM confidence)
- Context7 `/tavily-ai/tavily-python` — `AsyncTavilyClient(client=httpx.AsyncClient)`, `search`/`extract`, `UsageLimitExceededError`.
- Context7 `/websites/tavily` + https://docs.tavily.com/documentation/api-credits — basic search 1 credit; basic extract 1 credit / 5 successful URLs; failed URLs free; free plan 1000 credits/month; `include_usage` may be 0; Crawl/Research out of scope.
- https://pypi.org/pypi/tavily-python/json — version **0.8.5**, uploaded 2026-10-06, not yanked.
- https://docs.tavily.com/sdk/python/reference — Search + Extract Python SDK (retrieved 2026-10-26).
- Context7 `/encode/httpx` — `trust_env=False`; `follow_redirects` defaults off.
- Diátaxis foundations — doing vs knowing; mixing types is the failure.
- Retrieve-then-generate: Tutor Kai arXiv 2405.06681; review-first newsletters (Vona, Impri, newsletter4link).
- Context7 `/supabase/supabase-py` — Storage upload/download (considered, not chosen for cheat sheets).

### Tertiary (LOW confidence)
- NousResearch/hermes-agent#54339 — one malformed/private URL 400s the whole Tavily extract POST. Use as a warning: pre-filter locally. Not authoritative.

---
*Research completed: 2026-10-26*
*Ready for roadmap: yes*
