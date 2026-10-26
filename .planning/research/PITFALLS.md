# Pitfalls Research

**Domain:** Brownfield editorial ingest CLI (YouTube → DeepSeek → Supabase drafts) adding two-pass Tavily enrichment, quota accounting, cheat-sheet files, and richer templates
**Researched:** 2026-10-26
**Confidence:** HIGH for local contracts (measured on this checkout); MEDIUM for Tavily billing/extract behaviour (official docs via Context7, verified)

**Framing:** this is a **subsequent milestone (v1.5) on a live, working ingest+reader system**. The pipeline today is one LLM stage, fail-closed on `ArticleError` (`stage=llm`, zero DB rows), character-capped before DeepSeek (`ArticleBudgetError` → `stage=llm_truncation`), honesty-prompted (“do not invent facts/names/numbers not in the transcript”), and idempotent only at persist (`unique youtube_video_id` → `already_saved`). `ingest-collect` already runs unattended under systemd (`TimeoutStartSec=1800`, `flock`, drafts only). **The dominant failure mode is grafting pass-2 onto that single-stage fail-closed path so that a Tavily hiccup, a quota miss, or a re-run discards a good pass-1 article — or burns the 1000-request budget on videos that will never be updated.** Each pitfall names the existing contract that will break.

**Proposed phase numbering used below** (roadmap owns the final numbers; continues at 29 per PROJECT.md):

| Phase | Scope |
|-------|-------|
| 29 | Pass-1 richer templates: content-shaped sections, source-facts layer, СВА takeaway + risks. No Tavily. Honesty prompt stays transcript-only. |
| 30 | Classifier `practical \| conceptual`. Code / guide / Tavily / cheat sheet attach only when practical. |
| 31 | Tavily port + adapter, composition wiring, proxy/TLS (`trust_env=False`), `SecretRegistry`, locked `data_collection.__all__`. |
| 32 | Quota: atomic `try_consume`, global 1000, per-video ~5, log `tavily_quota_exhausted`, persist pass-1 anyway. |
| 33 | Pass-2 enrich: search/extract, URL allowlist (transcript ∪ live extract successes), prompt-injection isolation, JSON/streaming. |
| 34 | Cheat-sheet markdown file on the material (new persist path — not `razbors.notebook_path`). `already_saved` skips enrich. |
| 35 | Reader sources block + cheat-sheet download. Backend/SPA stay readers. |
| 36 | `ingest-collect` integration: timer bound, operator-vs-timer race, journal, exit codes, no false `OnFailure=`. |

---

## Critical Pitfalls

### Pitfall 1: Treating Tavily like DeepSeek — fail-closed `stage=llm` drops a finished pass-1 draft

**What goes wrong:**
Today `run_ingest_pipeline` has one `article.process(...)` inside `except ArticleError` → `map_article_error` → `IngestError(stage="llm")` and **never reaches persist**. If pass-2 (Tavily search/extract, second DeepSeek call, cheat-sheet assembly) lives inside that same `process()` / `ArticleError` taxonomy, a 429, a 400 on one bad URL, a timeout, or invalid pass-2 JSON raises the same way as a missing article. Result: **zero `materials` rows**, even though pass-1 already produced a publishable СВА draft. Collect counts it as `videos_failed` (exit 1) and the systemd `OnFailure=` alert fires for a video that should have been saved.

**Why it happens:**
The v1.1 contract is correct for “no article at all”. Pass-2 is optional enrichment. The cheapest wiring is “another call in `DeepSeekArticleGenerator.process`”. One exception type, one mapper, one fail-closed path.

**How to avoid:**
- Pass-1 stays fail-closed (no transcript-grounded article → no row). Pass-2 is **fail-soft**: on Tavily/quota/pass-2-JSON/second-LLM failure, persist the pass-1 draft and log a closed reason (`tavily_quota_exhausted`, `tavily_unavailable`, `enrich_invalid_json`, …) on stderr.
- Do not map Tavily errors through `LLM_REASONS` / `map_article_error`. New error type, new stage or a non-fatal diagnostic — not `stage=llm`.
- Keep pass-1 `ArticleDraft` in memory until persist; pass-2 mutates a copy. Pass-2 `ArticleInvalidJson` must not discard pass-1.
- Unit test: Tavily raises after a valid pass-1 → `PersistPort.persist` is still called with the pass-1 body; collect `videos_failed` does **not** increment; operator JSON `ok: true`.

**Warning signs:**
- `Tavily*` exceptions subclass `ArticleError`.
- `map_article_error` grows a Tavily branch that still returns `stage="llm"`.
- A test that expects exit 1 / zero rows when extract fails.
- `LLM_REASONS` edited to include `tavily_*`.

**Phase to address:** Phase 32 (quota exhaustion) and Phase 33 (enrich errors). The split of fail-closed vs fail-soft is a Phase 29/30 design invariant — lock it before the adapter exists.

---

### Pitfall 2: `already_saved` runs *after* captions + LLM (+ Tavily) — re-runs burn quota and keep the dry body

**What goes wrong:**
`persist_draft_and_enqueue` does `INSERT … ON CONFLICT (youtube_video_id) DO NOTHING` and, when `v_inserted = 0`, returns the **existing** material/shortlist ids. `run_ingest_pipeline` always does captions → metadata → LLM → persist. There is no cheap existence check. Consequences for v1.5:

1. Operator `ingest` of an already-saved video still pays DeepSeek **and** (if enrich is before persist) Tavily, then discards the new body.
2. `ingest-collect` uses a per-source cursor, but a video the **operator already ingested** can still sit in the collect window (cursor has not seen it). Collect runs the full pipeline, then `already_saved: true`, `videos_already += 1`. Quota gone, article unchanged.
3. Existing v1.1/v1.4 dry drafts can **never** gain a cheat sheet or sources block via re-ingest: the unique key blocks updates. The product looks “enriched” in code and stays dry in `/admin/digest`.

**Why it happens:**
PROJECT.md calls the CLI “idempotent”. That is true for **rows**, not for **work**. Phase 24 already learned this for LLM cost (high-water mark at listing). Tavily quota is the new scarce resource sitting on the same side of the persist gate.

**How to avoid:**
- Short-circuit **before** pass-2 (and, cheaply, before LLM if the video is already a material): a `PersistPort.exists(youtube_video_id)` / `SELECT id FROM materials WHERE youtube_video_id = $1`. On hit: return `already_saved` with **zero** Tavily `try_consume`.
- Do not add a silent `UPDATE` on conflict in this milestone unless product explicitly wants “re-enrich old drafts” — that is a different feature (overwrite a possibly-edited draft, cheat-sheet replace, knowledge-chunk rebuild). Default: skip.
- Lock with tests: (a) second `ingest` of the same id → 0 Tavily calls, 0 second LLM calls; (b) collect window containing an operator-saved id → `videos_already`, 0 Tavily; (c) existing dry row is unchanged after a skip.
- Collect cursor may still advance (today it advances on `already_saved`); keep that, so the skip stays cheap forever.

**Warning signs:**
- Tavily/DeepSeek calls in logs for `already_saved: true`.
- `ON CONFLICT DO UPDATE` slipped into migration 007’s RPC “to refresh the body”.
- A plan that “re-runs ingest to backfill cheat sheets” with no exists-check.
- Quota counter dropping on a collect tick that ingested 0 new videos.

**Phase to address:** Phase 34 (cheat-sheet persist) with the exists-check designed in Phase 32 so quota tests can use it. Phase 36 proves it on the collect path.

---

### Pitfall 3: Mixing Tavily extracts into the honesty «факты из источника» layer

**What goes wrong:**
Articles are dry **because** the system prompt says “Use only the transcript below. Do not invent facts, names, or numbers.” Pass-1’s new template adds a source-facts layer that СВА will treat as “this was in the video”. If pass-2 concatenates extract markdown into the same prompt, or the template has one undifferentiated “facts” section, the model will:

- copy numbers/names from web pages into the source-facts layer;
- “correct” the speaker with Wikipedia;
- keep the honesty line in the system prompt while the user message now contains web text — the model cannot tell which is the source.

Published material then lies about provenance. That is a content-contract break (D-CONTENT-01: prepared article; provenance must stay honest), not a style issue.

**Why it happens:**
One `ARTICLE_SYSTEM_PROMPT`, one `article.process`, one `body_markdown`. Pass-2 looks like “give the model more context so the article is richer”.

**How to avoid:**
- Pass-1 prompt stays transcript-only. Source-facts / «зачем СВА» / risks are generated here and **never rewritten from the web**.
- Pass-2 is a separate call (or a strictly section-scoped edit) whose prompt says: web text is untrusted *data*; you may write guide / verified-links / code; you may **not** add or alter names, numbers, or claims in the source-facts layer.
- Fence extracts (random delimiter, not a reusable `DATA_START`) and treat them as untrusted input — pages will contain “ignore previous instructions”.
- Post-check: pass-2 body’s source-facts heading text equals pass-1’s (byte or normalized). Test with an extract that plants a fake number.

**Warning signs:**
- A single system prompt that both forbids invention and includes Tavily `raw_content`.
- Template with one «Факты» section fed from both transcript and extracts.
- Pass-2 described as “refine the article” without a frozen facts region.

**Phase to address:** Phase 29 (section contract) and Phase 33 (pass-2 prompt + frozen-facts test).

---

### Pitfall 4: Quota `try_consume` that is not atomic — and that counts the wrong unit

**What goes wrong:**
Agreed cap is **1000 Tavily requests**, per-video ~5, on exhaustion log `tavily_quota_exhausted` and persist pass-1. Three independent ways this overshoots:

1. **Check-then-act race.** `ingest` (operator, **no flock**) and `ingest-collect` (timer, flock only on `/run/digest-ingest/lock`) can overlap. Two processes read “999 remaining”, both call Tavily, both increment. A file/env counter without `UPDATE … WHERE used < 1000 RETURNING` will exceed 1000.
2. **Requests ≠ Tavily credits.** Official billing (Context7 / docs.tavily.com, MEDIUM): basic **search = 1 credit/request**; basic **extract = 1 credit per 5 successful URLs** (failed URLs are free); `include_usage` may report **0** until that threshold. A local “1 extract call = 1 request” cap of 5/video can still be 1 search + 1 extract of 20 URLs. Conversely, counting Tavily credits while the product promised “1000 requests” under-counts HTTP calls. Auto `search_depth=advanced` (2 credits) or Crawl/Research (map+extract, Research 4–250 credits) blows the budget in one call.
3. **Unattended collect.** Default `INGEST_MAX_VIDEOS_PER_SOURCE = 5`. If the classifier marks everything practical, one source × 5 videos × ~5 requests = 25/tick. A 15-minute timer can empty 1000 in days with no human at the keyboard. Pay-as-you-go on the Tavily key continues charging after the local cap if the local counter is skipped or drifts.

**Why it happens:**
“1000” matches Tavily’s free monthly credits, so it feels like “just stop at 1000”. Collect already has a video cap, so it feels like Tavily is naturally bounded. `flock` feels like it serializes everything — it does not serialize operator `ingest`.

**How to avoid:**
- Persist the counter in Postgres (service-role), `try_consume(n)` as a single `UPDATE … WHERE remaining >= n RETURNING`. In-memory/file counters are tests-only.
- Define the unit in code as **HTTP calls we dispatch** (search = 1, each extract POST = 1), matching the product sentence “1000 Tavily requests”. Pin `search_depth="basic"`; never call crawl/map/research. Cap URLs per extract so one POST cannot become a 20-URL surprise; per-video cap counts those POSTs.
- Do not use `include_usage` / `GET /usage` as the gate (usage can be 0; `/usage` is a different number than local requests).
- Disable Tavily pay-as-you-go on the key, or treat Tavily 402/429 as exhaustion: log `tavily_quota_exhausted`, persist pass-1, stop dispatching.
- Collect: if remaining quota is 0, skip pass-2 for the rest of the tick (still persist pass-1). Do not fail the batch.
- Test: two overlapping `try_consume` fakes cannot exceed 1000; a 5-video collect with remaining=3 enriches at most one video (or none if per-video needs 5 — pick the rule and lock it).

**Warning signs:**
- Counter in a JSON file next to the CLI, or in `os.environ`.
- `tavily.research` / `crawl` / `search_depth` omitted (SDK default may upgrade).
- Quota tests that only cover a single process.
- Collect exit 1 when remaining hits 0 mid-batch.

**Phase to address:** Phase 32. Phase 36 verifies collect does not alert on exhaustion.

---

### Pitfall 5: Tavily inherits the YouTube SOCKS5 proxy (or `HTTP_PROXY`) — DeepSeek’s `trust_env=False` lesson, round two

**What goes wrong:**
Measured Phase 28: direct TLS to YouTube times out; captions **must** use `YOUTUBE_PROXY_URL` (SOCKS5); DeepSeek **must not** (`DefaultAsyncHttpxClient(trust_env=False)`). `build_httpx_client(settings)` injects that proxy for oEmbed/Atom. The Tavily Python SDK talks to `https://api.tavily.com` and, like any `requests`/httpx client with default `trust_env`, will honour `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`. Two failure modes:

- Reuse `build_httpx_client` → Tavily goes through AdGuard SOCKS5. TLS to `api.tavily.com` may fail, hang past extract’s 10–60 s timeout, or leak `TAVILY_API_KEY` to the proxy log (same T-08-PROXY class as DeepSeek).
- Construct `TavilyClient(api_key=…)` with no client and a systemd env that also exported `HTTP_PROXY` “for YouTube”. Same leak/hang, and it will not show up in unit tests.

ADR-0002 is already bent for DeepSeek; Tavily is a **second** public foreign API. Routing it through a consumer VPN does not make it “in contour”.

**Why it happens:**
“We already have an httpx client in composition.” YouTube and Tavily are both “the internet”, so they look like the same adapter.

**How to avoid:**
- New factory `build_tavily_client` next to `build_async_deepseek_client`: **direct TLS**, `trust_env=False` (or a `requests.Session` with `trust_env=False` / empty proxies). Never pass `settings.youtube_proxy_url`.
- Adapters still take a ready client (D-17); no `os.environ` inside `data-collection`.
- Pin with a test mirroring `test_ingestion_settings.py`: constructed Tavily HTTP client `_trust_env is False` and `proxy is None`.
- Measure once on the operator host (like Phase 28): TCP/TLS to `api.tavily.com` without the proxy. Record it as a precondition. If it fails, that is a spike — do not silently fall back to the YouTube proxy.

**Warning signs:**
- `build_httpx_client(settings)` in the Tavily factory.
- `TavilyClient()` with no injected session.
- SOCKS5 credentials appearing in Tavily error strings (also Pitfall 12).
- Plan that “shares the YouTube client for all egress”.

**Phase to address:** Phase 31.

---

### Pitfall 6: Hallucinated, search-only, or failed-extract URLs published as «проверенные ссылки»

**What goes wrong:**
Agreed rule: links in the article = URLs **already in the transcript** plus URLs of pages that **actually opened** via Tavily extract. The model will invent GitHub/docs links; Tavily **search** returns URLs that were not extracted; extract returns `failed_results` for pages that did not open. If pass-2 copies search hits or model-proposed hrefs into `body_markdown`, the sources block lies. СВА clicks a 404 or a hallucinated domain. Reader trust dies the first time.

**Why it happens:**
Search snippets look like “sources”. `response_format=json_object` does not validate hrefs. There is no URL field on `ArticleDraft` today — everything is markdown.

**How to avoid:**
- Build an allowlist in code, not in the prompt: (1) http(s) URLs regex-extracted from the **transcript**; (2) `results[].url` from extract where `raw_content` is non-empty. **Not** `failed_results`, **not** search hits unless subsequently extracted, **not** model-invented strings.
- Strip any markdown link whose href is outside that set (or drop the href, keep the phrase). Do this after the LLM, always.
- Test: plant `https://evil.example/totally-real` in the model JSON and a search hit that was not extracted; neither survives. A transcript URL and an extract-success URL both survive.

**Warning signs:**
- “The prompt says only use provided URLs” as the only control.
- Sources block rendered from the search API response directly.
- No post-filter in the diff.

**Phase to address:** Phase 33; Phase 35 must not grow a second, unfiltered sources list in the SPA.

---

### Pitfall 7: One bad extract URL 400s the whole batch — and we fetch URLs ourselves (SSRF)

**What goes wrong:**
Tavily `POST /extract` accepts up to 20 URLs. Community + Tavily error surface (MEDIUM/LOW: official 400 on malformed requests; hermes-agent #54339 reports one non-http(s)/private URL **fails the entire POST**, not just that item). If pass-2 forwards model-proposed or transcript-garbled strings:

- the whole extract fails;
- a naive mapper fail-closes the video (Pitfall 1);
- retries hammer Tavily (quota).

Separately: implementing “extract” with **our** `httpx` against attacker/transcript URLs is SSRF against `supabase`, `169.254.169.254`, `192.168.1.68` (the AdGuard box), and the app VM. Tavily’s servers fetching public URLs is the point of the vendor; we must not duplicate fetch on-box.

**Why it happens:**
Transcripts contain bare domains, `ftp:`, internal hosts, and truncated URLs. The model will add more. `build_httpx_client` already exists.

**How to avoid:**
- Pre-validate each URL: absolute `http`/`https`, public host, no link-local/RFC1918/loopback, not our `SUPABASE_URL` host, not `youtube.com` (waste). Drop bad entries **locally**; extract only the remainder. One bad URL must not 400 siblings.
- Never `httpx.get` candidate pages from ingestion-service. Extract = Tavily only.
- Treat extract `failed_results` as skip, not as ingest failure.
- Test: batch `[good, "not a url", "http://127.0.0.1/"]` → one Tavily POST with only `good`; persist still happens.

**Warning signs:**
- `httpx.get` / `requests.get` of enrich URLs in `data-collection`.
- Whole-video failure when `failed_results` is non-empty.
- No scheme/host filter before `client.extract`.

**Phase to address:** Phase 31 (no local fetch) and Phase 33 (pre-filter + fail-soft).

---

### Pitfall 8: Unattended collect + `TimeoutStartSec=1800` kill mid-pass-2 — pass-1 never persisted

**What goes wrong:**
`digest-ingest.service` is `Type=oneshot`, bounded by `TimeoutStartSec=1800` (not `RuntimeMaxSec` — that knob is inert; measured Phase 24-07). Collect loops `await run_ingest_pipeline` per video with `diagnostics=None`. If enrich is in-process *before* persist:

- extract default timeout is 10 s basic / 30 s advanced, max 60 s; a second DeepSeek stream was 16.6 s on a 24 min video (Phase 28);
- a 5-video source at the per-source cap can grow from ~2 min to many minutes;
- SIGTERM mid-extract → no persist, no `stamp_last_run` (if kill is before the tail), next tick retries the same video, pays again.

Classifier bias toward `practical` (models “helpfully” pick the branch that unlocks tools) turns every new video into a Tavily spender. Collect has no `--debug`; `tavily_quota_exhausted` sent only through `StageDiagnostics` is **silent** in the journal (`run_collect_batch(..., diagnostics=None)`).

If Tavily failure is counted as `videos_failed`, collect exits 1 and `OnFailure=` pages the operator for a saved-or-should-have-been-saved draft.

**Why it happens:**
The timer was sized for captions + one LLM. Pass-2 was not in the budget. Collect’s success metric is “pipeline didn’t throw”.

**How to avoid:**
- Persist pass-1 **before** starting Tavily, or accept that a kill loses the video and ensure the next tick’s exists-check (Pitfall 2) is cheap. Prefer persist-then-enrich-in-memory-then-update **only** if an explicit enrich-update RPC exists; otherwise persist-once at the end but **skip pass-2 when wall-clock remaining < bound**.
- Per-video Tavily time budget; on expiry persist pass-1.
- `tavily_quota_exhausted` and enrich-skipped reasons go through collect’s `emit_diagnostic` (stderr → journal), not only `--debug`.
- Exhaustion and enrich-skip are **not** `videos_failed`. Exit 0 if pass-1 persisted.
- Pin classifier: default `conceptual` on unknown/empty; test a “please be helpful / include links” transcript still can classify conceptual.
- Do not raise `INGEST_MAX_VIDEOS_PER_SOURCE` in the same milestone.

**Warning signs:**
- Collect tests that treat Tavily 429 as `videos_failed`.
- No journal line on exhaustion.
- Enrich started before any persist call.
- Classifier test set with only practical gold labels.

**Phase to address:** Phase 30 (classifier default), Phase 32 (exhaustion logging), Phase 36 (timer/exit/journal).

---

### Pitfall 9: Cheat sheet stuffed into `body_markdown` or reused as `razbors.notebook_path`

**What goes wrong:**
`materials` has `body_markdown` and no attachment column. `razbors` has `notebook_path` and an authenticated `GET /razbory/{id}/notebook`. Agreed: cheat sheet is a **downloadable markdown file on the material**; the guide stays in article sections. Cheap mistakes:

- Append the cheat sheet to `body_markdown` → reader article becomes a dump; no download; knowledge-chunk embeddings ingest the cheatsheet twice.
- Reuse `notebook_path` / razbor download API → wrong resource, announcement-status rules, `.ipynb` filename logic, and a foreign-key story that does not exist.
- Write a file under `/opt/digest-cds/…` from collect → path is VM-local; SPA on another host cannot serve it; operator laptop ingest writes a different path.
- Store in `knowledge_chunks` → violates “material = article”; search starts hitting cheat-sheet fragments.

**Why it happens:**
No material-attachment table exists. Razbor notebooks look like “we already download files”.

**How to avoid:**
- New persist path: e.g. `materials.cheat_sheet_markdown` (or a `material_files` row) written in the same transaction as the draft, nullable, only for `practical` that actually produced a sheet. Empty/null for conceptual and for quota-skipped pass-2.
- Reader download mirrors razbor **pattern** (auth, blob, honest 404) on a **new** materials route; do not call `downloadRazborNotebook`.
- Guide headings live in `body_markdown`; the file is the cheat sheet only.
- `already_saved` skip must not insert a second file (Pitfall 2).
- Test: conceptual material → no file, no download link; practical + quota skip → article saved, download absent (honest), not a 500.

**Warning signs:**
- `notebook_path` on `materials`.
- Cheat-sheet text in the article-only Playwright snapshot.
- Local filesystem paths in `MaterialDraft`.

**Phase to address:** Phase 34 (storage) and Phase 35 (download). Do not invent the file in Phase 29 templates.

---

### Pitfall 10: Breaking locked public contracts — `__all__`, `Stage`, `ALLOWED_KEYS`, stdout

**What goes wrong:**
`tests/unit/test_data_collection_public_api.py` pins `data_collection.__all__` to **exactly ten** names and negative-roots adapters/errors (`DeepSeekArticleGenerator`, `ArticleError`, …). `test_stage_set_is_unchanged` pins `Stage` to `{url, captions, metadata, consistency, llm, llm_truncation, persist}`. Diagnostics `ALLOWED_KEYS` is a closed frozenset; values over 256 chars are sliced; `SecretRegistry` is seeded from DeepSeek key, Supabase secret, and `YOUTUBE_PROXY_URL` only — **`tvly-` keys are not in the denylist** (`sk-`, `bearer`, `eyJ` JWT). `test_cli_ingest_contract.py` locks `EXPECTED_SUCCESS_LINES` (three checkmarks, no enrich line) and default `stderr == ""`.

Exporting `TavilyClient` / `EnrichmentPort` from the package root, adding `stage=tavily` without amending the Stage test, printing `✓ tavily` on stdout, or logging extract bodies / the API key on `--debug` will red the suite **or** leak secrets into journald (collect has no redaction path today beyond whatever the adapter throws).

**Why it happens:**
PROJECT.md says “ports in `data-collection`”. The v1.1 rule was: ports that are the **ingestion contract** go on `__all__`; adapters and errors stay private. Tavily is an adapter, like DeepSeek.

**How to avoid:**
- Keep Tavily adapter, errors, and DTOs **off** `data_collection.__all__` unless the roadmap explicitly extends the public contract and **amends** `PUBLIC_NAMES` under TDD (amend, do not delete negatives). Wiring stays in `ingestion-service/composition`.
- If a new stage is required, amend `Stage` + `test_stage_set_is_unchanged` + `ALLOWED_KEYS` in the same plan. Prefer logging enrich via collect `emit_diagnostic` / allowlisted debug keys (`tavily_requests`, `quota_remaining`) without a new fatal stage.
- Seed `SecretRegistry` with `TAVILY_API_KEY`; add a `tvly-` denylist pattern. Never put `raw_content`, transcript, or URLs-with-query into operator JSON `context` (existing `_CONTEXT_ALLOWLIST` is `video_id` / `exception_class` / `status_code`).
- Do not add a fourth stdout checkmark. Enrichment is stderr/debug only. Preserve `EXPECTED_SUCCESS_LINES`.

**Warning signs:**
- `from data_collection import Tavily…` in production code.
- `EXPECTED_SUCCESS_LINES` edited to add `✓ enrich`.
- Debug line containing `raw_content` or a `tvly-` prefix.
- `ALLOWED_KEYS` unchanged while new debug dict keys are emitted (they will be dropped — silent, not leaked, but operators see nothing).

**Phase to address:** Phase 31 (exports, secrets, client) with stdout preservation checked in every CLI-touching phase (32–36).

---

### Pitfall 11: Pass-2 JSON / character budget / second idle stream — invalid output kills pass-1

**What goes wrong:**
Pass-1 already streams because a non-streaming DeepSeek call idled 8–12 s and middleboxes reset (`APIConnectionError`; fix `0dddc75`). Pass-2 adds extract markdown + generated code inside `response_format=json_object`. Failure modes:

- Code fences and unescaped newlines → `json.loads` fails → `ArticleInvalidJson` → fail-closed (Pitfall 1).
- Concatenating extracts onto the transcript and reusing `MAX_TRANSCRIPT_CHARS` (80000) → `ArticleBudgetError` / `stage=llm_truncation` for a video that **already had** a valid pass-1 article.
- Second non-streamed completion → same idle reset, now on the enrich call, counted as `stage=llm` network_error.
- Larger `body_markdown` → `response_chars` debug OK, but persist/RPC payload and later knowledge-chunking grow without a cap.

**Why it happens:**
One generator class, one budget check at the top of `process()`, one `_stream_content`. Pass-2 looks like “call it again with more text”.

**How to avoid:**
- Budget check stays on the **transcript** only (pass-1). Pass-2 has its own, smaller extract-context cap; overflow **skips enrich**, does not raise `llm_truncation`.
- Stream pass-2 the same way as pass-1. `max_retries=0` stays.
- Generated code belongs in the cheat-sheet file and fenced article sections, not as a reason to drop JSON mode without a parser test.
- Test: pass-2 returns broken JSON → persist pass-1, no `llm_truncation`; pass-2 payload over extract cap → skip enrich, persist pass-1.

**Warning signs:**
- `len(transcript.text) + len(extracts)` compared to `max_transcript_chars`.
- Pass-2 using `stream=False`.
- `ArticleBudgetError` raised from the enrich path.

**Phase to address:** Phase 29 (pass-1 still streams) and Phase 33 (pass-2 budget/JSON fail-soft).

---

### Pitfall 12: Operator JSON / journal leak of extracts, queries, and `tvly-` keys

**What goes wrong:**
Phase 8/11/15 locked: operator JSON must not contain transcript or keys; `--debug` is stderr, allowlisted, `SecretRegistry` + denylist, mask-not-fail. Pass-2 introduces: Tavily query strings (often copied from the talk), extract `raw_content` (arbitrary web HTML/markdown), `TAVILY_API_KEY` (`tvly-…`, **not** matched by `sk-`), and URL query strings that can carry tokens. Collect writes exceptions via `f"{type(err).__name__}: {err}"` with **no** `SecretRegistry` — a Tavily SDK error that echoes the key or the proxy URL lands in journald.

**Why it happens:**
Debug “richer enrich diagnostics” copies the search response into context. Collect’s `except Exception` path predates Tavily.

**How to avoid:**
- Enrich debug keys: counts and ids only (`tavily_requests`, `extract_ok`, `extract_failed`, `quota_remaining`, `classified`). No query text, no `raw_content`, no URL list in default debug (video_id-only metadata stays the D-06 rule unless an allowlisted `extract_ok` integer).
- Register `TAVILY_API_KEY` in `_settings_secrets`. Denylist `tvly-[A-Za-z0-9_-]+`.
- Run collect’s `emit_diagnostic` through the same `sanitize()` used by `--debug`, or never interpolate `str(err)` from SDK exceptions (log `type` + closed reason only).
- Test: plant a `tvly-` key and a transcript sentence in a Tavily exception; neither appears in CLI JSON, `--debug` lines, or collect stderr.

**Warning signs:**
- `context["query"]` or `context["raw_content"]` in `IngestError`.
- Collect diagnostic still `f"{err}"` for adapter errors after Tavily lands.
- `.env.example` gaining the Tavily **value**.

**Phase to address:** Phase 31 (registry/denylist) and Phase 36 (collect sanitize).

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Tavily errors subclass `ArticleError` / share `process()` fail-closed | One mapper | Pass-1 drafts vanish on any enrich hiccup; collect exit 1 | Never |
| Skip exists-check; rely on `already_saved` after persist | No new port method | Re-runs burn Tavily; dry body stuck forever | Never |
| One prompt for honesty + web | One DeepSeek call | Source-facts absorb Wikipedia; provenance lies | Never |
| File/env quota counter | No migration | Races with operator `ingest`; 1000 exceeded | Never in production (in-memory fake OK in unit tests) |
| Reuse `build_httpx_client` / default `TavilyClient()` | One less factory | Proxy leak + TLS hang; ADR-0002 pretend-fix | Never |
| Prompt-only URL honesty | No post-filter | Hallucinated sources in the reader | Never |
| `httpx.get` “extract” ourselves | No Tavily extract credits | SSRF to contour hosts | Never |
| Cheat sheet in `body_markdown` | No schema | No download; embeddings polluted | Never |
| Reuse `razbors.notebook_path` | Existing download | Wrong bounded context; `.ipynb` rules | Never |
| Export Tavily types on `data_collection.__all__` without amending the pin | “ports are public” | Locked 10-name contract goes red; adapters leak | Only with an explicit `__all__` amendment + negatives kept |
| `search_depth` unset / crawl / research | “better results” | 2–250 credits per call; 1000 gone | Never |
| Classifier default `practical` | More “useful” articles | Unattended collect empties quota | Never — default conceptual on unknown |
| `ON CONFLICT DO UPDATE` to “refresh” enrich | Backfill old drafts | Overwrites editor-touched drafts; duplicate cheat sheets | Not in v1.5 unless a dedicated re-enrich command is specified |
| Fourth stdout checkmark `✓ tavily` | Visible progress | `EXPECTED_SUCCESS_LINES` red | Never — stderr/debug only |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `run_ingest_pipeline` | Fold pass-2 into `article.process` so `ArticleError` fail-closes | Pass-1 fail-closed; pass-2 fail-soft; persist pass-1 on enrich errors |
| `persist_draft_and_enqueue` | Assume re-ingest updates `body_markdown` | `ON CONFLICT DO NOTHING` returns old row; exists-check **before** Tavily |
| `ingest-collect` | Count enrich skip as `videos_failed` (exit 1 → `OnFailure=`) | Exhaustion/skip → diagnostic + persist pass-1 + exit 0 if drafts saved |
| `ingest` vs timer | `flock` on collect only; operator ingest races quota | Atomic DB `try_consume`; exists-check is the other guard |
| Collect `diagnostics=None` | `tavily_quota_exhausted` only on `--debug` | `emit_diagnostic` always (stderr → journal) |
| `TimeoutStartSec=1800` | Start extract before persist; kill loses the article | Persist pass-1 first, or skip pass-2 when remaining wall-clock is tight |
| YouTube proxy | Tavily via `build_httpx_client` / `trust_env` | Direct TLS factory, `trust_env=False`, measured like DeepSeek |
| Tavily Search | Omit `search_depth` (may auto-upgrade to advanced = 2 credits) | Pin `basic`; never crawl/map/research |
| Tavily Extract | POST model URLs unfiltered; one bad URL 400s the batch | Pre-validate; extract successes only in allowlist; `failed_results` = skip |
| Tavily `include_usage` | Use as remaining-quota oracle (can be 0 under 5 successful extracts) | Local request counter is source of truth |
| `SecretRegistry` | Forget `TAVILY_API_KEY` / `tvly-` | Seed + denylist; sanitize collect `str(err)` |
| `data_collection.__all__` | Add Tavily symbols next to `ArticleGenerator` | Adapter stays private; composition wires it; amend PUBLIC_NAMES only on purpose |
| `Stage` Literal | Add `tavily` without the pin test | Amend `test_stage_set_is_unchanged` + `ALLOWED_KEYS` together, or don’t add a stage |
| Reader SPA | Deep-import Tavily / render extract HTML | Sources + download via `web/src/services/` only; markdown as download, not unsanitized HTML |
| ADR-0002 | Treat Tavily as “just HTTP” with no recorded bend | Record the second public-API bend next to DeepSeek; FoundryModels still not this milestone |
| Knowledge chunks | Re-embed on every skipped re-run | `already_saved` skip means no new chunks; enrich-update (if ever) must rebuild explicitly |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Pass-2 before persist + timer kill | Video retried every 15 min; quota bleeds | Persist pass-1 first; exists-check | First collect tick that overruns 1800 s |
| Per-URL extract POSTs instead of one batched POST | 5 URLs = 5 requests against the per-video cap of ~5 (no search left) | One extract POST per video with pre-filtered URLs (≤ cap−1) | Every practical video |
| `advanced` extract (30 s default, 2 credits / 5 URLs) | Collect approaches `TimeoutStartSec`; credits vanish | Pin `extract_depth="basic"` (10 s default) | 5 practical videos/tick |
| Second DeepSeek call without streaming | `APIConnectionError` on enrich; fail-closed if mapped as llm | Stream pass-2; fail-soft | Same middlebox as Phase 28 |
| Classifier always practical | 25 Tavily requests/source/tick | Default conceptual; cap already ~5/video | Days of unattended timer vs 1000 |
| Re-pipeline of operator-saved ids in the collect window | `already_saved` after paid work | Exists-check before LLM/Tavily | Every mixed operator+timer workflow |
| Huge `raw_content` into pass-2 context | `provider_context_length` or idle timeout | Extract-context cap; skip enrich on overflow | Long documentation pages |
| Cheat sheet in `body_markdown` | Knowledge search hits dumps; reader scroll death | Separate file column | First practical video published |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Local `httpx.get` of transcript/model URLs | SSRF to Supabase, metadata IP, AdGuard `192.168.1.68` | Tavily extract only; pre-validate public https |
| One unfiltered URL in extract POST | Whole-batch 400; retry loops; quota burn | Filter before dispatch; no retry on 400-from-bad-URL |
| Prompt injection via `raw_content` | Model follows page instructions; leaks prompt; invents facts | Fence extracts as data; freeze source-facts; post-filter URLs |
| Tavily through YouTube SOCKS5 / `HTTP_PROXY` | API key in proxy logs; unexpected egress | `trust_env=False`; never reuse YouTube client |
| `tvly-` key in JSON/journal/`str(err)` | Secret outside Cloud.ru | `SecretRegistry` + `tvly-` denylist; collect sanitize |
| Extract bodies in `--debug` | Web PII + prompt leak on operator stderr | Allowlist counts only |
| Unauthenticated cheat-sheet URL | Unpublished draft file readable by anyone who guesses | Auth-gated download, same idea as razbor notebook; draft still admin-only |
| Rendering cheat sheet / extract HTML in SPA | XSS from markdown/HTML | Download as file; article markdown through existing sanitizing path |
| Publishing search URLs as “verified” | Reader sent to attacker-controlled lookalikes | Allowlist = transcript ∪ extract **successes** |
| Enabling Tavily pay-as-you-go “just in case” | Unattended spend after local 1000 | Local gate first; treat vendor 402/429 as exhaustion |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Enrich failure → «материал не создан» | Admin thinks ingest is broken; video skipped until tomorrow | Save pass-1; show a draft; optional quiet “без гайда — квота/сеть” in admin provenance later (not required in v1.5 CLI) |
| Dry v1.1 article never gains a cheat sheet on re-run | Feature looks shipped, old shortlist stays three-block | Exists-skip is correct; backfill is a later command, not silent UPDATE |
| Sources list with dead/hallucinated links | СВА loses trust in the edition | Post-filter allowlist; omit the block if empty |
| Cheat sheet button on conceptual / quota-skipped | 404 after a visible CTA | Hide download when null; don’t show a disabled mystery button |
| Guide duplicated as the whole article | Unreadable longread | Guide = sections; cheat sheet = file |
| Collect pager at 03:00 because Tavily 429 | Operator ignores real failures | Exhaustion is exit 0 + journal line `tavily_quota_exhausted` |
| `✓ tavily` on stdout | Breaks anyone parsing ingest success lines | Keep three checkmarks; enrich on stderr |

## "Looks Done But Isn't" Checklist

- [ ] **Fail-soft enrich:** Tavily 429 / 400 / timeout / invalid pass-2 JSON still inserts a `draft` with the pass-1 body — verify persist spy called; collect `videos_failed` unchanged.
- [ ] **Fail-closed pass-1:** DeepSeek `ArticleNetworkError` still `stage=llm`, zero rows — verify existing `test_article_error_mapping` + pipeline tests still green.
- [ ] **Exists-check:** second ingest of the same `youtube_video_id` performs **zero** Tavily HTTP calls and does not change `body_markdown`.
- [ ] **Collect + operator mix:** video saved by `ingest`, then in the collect window → `videos_already`, zero Tavily, cursor may advance.
- [ ] **Quota atomic:** two concurrent `try_consume` cannot pass 1000; remaining=0 logs `tavily_quota_exhausted` and still persists pass-1.
- [ ] **Quota unit:** `search_depth="basic"` pinned; no crawl/map/research; per-video HTTP cap ~5; extract URLs pre-filtered so one POST cannot smuggle 20.
- [ ] **Proxy:** Tavily client `trust_env is False` and does not receive `youtube_proxy_url`; DeepSeek test still asserts the same.
- [ ] **URL allowlist:** hallucinated href, search-only hit, and `failed_results` URL are stripped; transcript URL + extract-success URL remain.
- [ ] **Extract pre-filter:** malformed + loopback URLs never reach Tavily; sibling good URL is extracted.
- [ ] **No local fetch:** grep `data-collection` / `ingestion-service` for extract-URL `httpx.get`/`requests.get` is empty (Tavily adapter POSTs to `api.tavily.com` only).
- [ ] **Honesty freeze:** source-facts section bytes (or normalized text) match pass-1 after pass-2; planted extract number does not appear there.
- [ ] **Classifier:** unknown/empty → `conceptual`; no Tavily/cheat sheet; practical-only artifacts gated.
- [ ] **Cheat sheet:** conceptual / quota-skip → null file, no download CTA; practical success → file **not** in `body_markdown` and **not** `notebook_path`.
- [ ] **Locked `__all__`:** `len(data_collection.__all__) == 10` unless an explicit amendment landed with negatives still red for adapter names.
- [ ] **Stage pin:** `test_stage_set_is_unchanged` green (amended deliberately if a new stage exists).
- [ ] **Stdout:** `EXPECTED_SUCCESS_LINES` byte-identical; no `✓ tavily`.
- [ ] **Secrets:** `tvly-` key + proxy URL absent from CLI JSON, `--debug`, and collect stderr in a planted-secret test.
- [ ] **Collect journal:** exhaustion visible without `--debug`; exit 0 when pass-1 saved; `OnFailure=` does not fire.
- [ ] **Streaming:** pass-2 uses `stream=True`; transcript cap not applied to extracts.
- [ ] **ADR-0002:** second public-API bend recorded; FoundryModels not silently reintroduced.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Pass-1 dropped by fail-closed enrich | HIGH | Stop collect; revert mapper; re-ingest affected ids **after** exists-check exists or they will no-op; quota already spent is gone |
| Quota exceeded (race / credits mismatch) | MEDIUM | Freeze collect; set remaining=0 in DB; persist will stay pass-1-only; rotate Tavily key if paygo charged; fix `try_consume` before re-enabling |
| Tavily via YouTube proxy (key in proxy logs) | HIGH | Rotate `TAVILY_API_KEY`; force `trust_env=False`; do not “fix” by routing DeepSeek through the proxy |
| Hallucinated URLs in published drafts | MEDIUM | Do not auto-send (still out of scope); strip sources in a one-off editor pass or leave drafts unpublished; ship post-filter before next collect |
| SSRF via local fetch | HIGH | Remove the fetch; audit egress logs; treat as incident if contour hosts were hit |
| Dry articles stuck (already_saved) | LOW | Correct behaviour for v1.5; schedule a later re-enrich command if product wants backfill |
| Cheat sheet in body | LOW | Migration to split column; re-render reader; rebuild chunks if already embedded |
| `__all__` / stdout / Stage tests red | LOW | Revert exports/checkmark/stage; keep adapter private |
| Collect paging on Tavily skip | LOW | Recode skip as non-failure; `SuccessExitStatus` unchanged (0 and 75 only) |
| Prompt-injected nonsense in one draft | LOW | Reject that shortlist row; fence extracts; do not republish |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 — fail-closed enrich drops pass-1 | 32, 33 (invariant from 29) | Persist spy on Tavily error; collect `videos_failed` not incremented; `LLM_REASONS` unchanged |
| 2 — `already_saved` after paid enrich | 32 (exists-check), 34, 36 | Zero Tavily on second ingest; collect mix-path; body unchanged |
| 3 — web mixed into source facts | 29, 33 | Frozen source-facts test; planted extract number absent |
| 4 — quota race / wrong unit / paygo | 32, 36 | Concurrent `try_consume`; remaining=0 persist; no crawl/research; collect exit 0 |
| 5 — Tavily through YouTube proxy | 31 | Client `trust_env is False`; DeepSeek assertion still green; no `build_httpx_client` |
| 6 — hallucinated / search-only URLs | 33, 35 | Post-filter unit test; SPA sources use the same DTO list |
| 7 — extract 400 / local SSRF | 31, 33 | Pre-filter test; grep no local GET of page URLs |
| 8 — collect timer / classifier / silent quota | 30, 32, 36 | Default conceptual; journal line without `--debug`; kill/skip still persist pass-1 |
| 9 — cheat sheet on wrong storage | 34, 35 | Null file for conceptual; download route ≠ razbor; body without sheet dump |
| 10 — locked `__all__` / Stage / stdout / keys | 31 (every CLI phase) | `PUBLIC_NAMES` length; `EXPECTED_SUCCESS_LINES`; `tvly-` redaction test |
| 11 — JSON / budget / second stream | 29, 33 | Pass-2 broken JSON persists pass-1; extract cap skips enrich; `stream=True` |
| 12 — JSON/journal leak | 31, 36 | Planted key/transcript absent from JSON, debug, collect stderr |

## Sources

**Measured on this checkout (HIGH — code and Phase 24/28 evidence, 2026-10-26):**
- `run_ingest_pipeline`: single `article.process` inside `except ArticleError`; persist only after LLM (`ingestion-service/.../ingest_pipeline.py`).
- `persist_draft_and_enqueue`: `ON CONFLICT (youtube_video_id) DO NOTHING`; `already_saved` when `v_inserted = 0` (migration 007). No body update.
- Collect: `await run_ingest_pipeline(...)` per window video; `diagnostics=None`; `already_saved` counted after the call; `INGEST_MAX_VIDEOS_PER_SOURCE` default 5; exit 1 iff `videos_failed > 0` (`collect_batch.py`, `settings.py`).
- `flock` only on `ingest-collect` (`deploy/systemd/digest-ingest.service`); operator `ingest` is unlocked.
- `TimeoutStartSec=1800` on `Type=oneshot`; `RuntimeMaxSec` inert (Phase 24-07).
- DeepSeek `DefaultAsyncHttpxClient(trust_env=False)`; YouTube proxy only in `build_youtube_transcript_api` / `build_httpx_client` (`clients.py`). Phase 28 measured YouTube TLS timeout vs DeepSeek TLSv1.3.
- Honesty prompt and three-block templates (`deepseek_article.py`, `lecture.md`).
- `data_collection.__all__` exactly 10 names; Stage 7 values; `ALLOWED_KEYS` closed; `_settings_secrets` is DeepSeek + Supabase + YouTube proxy (`test_data_collection_public_api.py`, `redaction.py`, `cli.py`).
- `EXPECTED_SUCCESS_LINES` three checkmarks (`test_cli_ingest_contract.py`).
- `materials` has `body_markdown`, no file column; `razbors.notebook_path` + `/razbory/{id}/notebook` only (`001_initial_schema.sql`, `razboryApi.js`).

**Tavily official docs (Context7 `/websites/tavily` + `/tavily-ai/tavily-python`, classify-confidence **MEDIUM**, verified 2026-10-26):**
- Credits: free plan 1000/month; basic search = 1 credit/request; basic extract = 1 credit per 5 **successful** URLs; failed URLs not charged; advanced extract = 2 per 5; Crawl = map + extract; Research 4–250 credits/request.
- Extract: up to 20 URLs/POST; `failed_results` separate; default timeout 10 s basic / 30 s advanced, max 60 s; `include_usage` may be 0 below threshold.
- Search `search_depth` basic vs advanced (2 credits); changelog notes auto-upgrade risk if depth omitted.
- `GET /usage` is account/key usage, not a substitute for a local request gate.
- https://docs.tavily.com/documentation/api-credits
- https://docs.tavily.com/documentation/api-reference/endpoint/extract
- https://docs.tavily.com/sdk/python/reference

**Community corroboration (classify-confidence **LOW** for webfetch — not authoritative; use only as a warning sign):**
- NousResearch/hermes-agent#54339 (2026-06-28): agent-supplied malformed/private URLs → Tavily `POST /extract` **400 for the whole request**; local pre-filter + per-URL salvage is the fix they shipped.

**Repository sources:**
- `.planning/PROJECT.md` — v1.5 goal, two-pass rules, 1000/`try_consume`/~5, ADR-0002 DeepSeek bend, collect ING-05/06/07.
- `.planning/STATE.md` — proxy/DeepSeek asymmetry; collect live-run still deferred (empty `pipeline_ingest_sources`).
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — no public foreign LLM/API as the contour rule (already bent once).

---
*Pitfalls research for: Digest CDS v1.5 — two-pass Tavily enrichment on the existing ingest+reader system*
*Researched: 2026-10-26*
