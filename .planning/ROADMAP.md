# Roadmap: Digest CDS

## Milestones

- ✅ **[v1 MVP](milestones/v1-ROADMAP.md)** — Phases 1-5 (shipped 2026-09-22)
- ✅ **[v1.1 YouTube → LLM → Supabase ingestion](milestones/v1.1-ROADMAP.md)** — Phases 6-11 (shipped 2026-10-02)
- ✅ **[v1.2 Admin UX + diagnostics + PIPE-01 MVP](milestones/v1.2-ROADMAP.md)** — Phases 12-16 (shipped 2026-10-05)
- ✅ **[v1.3 Live mail, scheduled ingestion & backlog debt](milestones/v1.3-ROADMAP.md)** — Phases 17-24 (shipped 2026-10-18)
- ✅ **[v1.4 UI polish & honest navigation](milestones/v1.4-ROADMAP.md)** — Phases 25-28 (shipped 2026-10-22)
- 🚧 **[v1.5 Two-pass article enrichment](milestones/v1.5-ROADMAP.md)** — Phases 29-34 (in progress; roadmap created 2026-10-26)

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

<details>
<summary>✅ v1.4 UI polish & honest navigation (Phases 25-28) — SHIPPED 2026-10-22</summary>

- [x] Phase 25: Admin «Настройка» — naming, readable surfaces, token repair (10/10 plans) — completed 2026-10-22
- [x] Phase 26: Section context, anchor scrolling and header active state (3/3 plans) — completed 2026-10-22
- [x] Phase 27: Header search runs on submit (5/5 plans) — completed 2026-10-22
- [x] Phase 28: Live proof — streamed DeepSeek ingest (1/1 plan) — completed 2026-10-22

Full phase detail: [milestones/v1.4-ROADMAP.md](milestones/v1.4-ROADMAP.md)

</details>

- [x] **Phase 29: Pass-1 richer templates** - Every ingest is a content-shaped СВА longread with transcript-only facts and an explicit audit takeaway
- [ ] **Phase 30: Classifier practical | conceptual** - Every draft records `practical` or `conceptual`; extras stay off for conceptual/unknown
- [ ] **Phase 31: Tavily quota and persist-then-enrich floor** - Pass-1 always persists; Tavily is budgeted (1000) and `already_saved` never spends it
- [ ] **Phase 32: Pass-2 enricher and personal-KB cheat sheets** - Practical pass 2 may add guide, marked code, live URLs, and one markdown note per key technology without failing ingest
- [ ] **Phase 33: Reader sources and cheat-sheet downloads** - Reader and admin preview show the same sources and note downloads; absence is omission
- [ ] **Phase 34: Collect honesty and operator debug** - Collect treats enrich skip/quota/fail-soft as success; `--debug` reports kind/quota/URL counts without secrets

## Phase Details

### 🚧 v1.5 Two-pass article enrichment (Phases 29-34)

**Started:** 2026-10-26 · **Requirements:** 22 (`ART-01…04`, `KIND-01…03`, `TAV-01…03`, `ENR-01…03`, `SHEET-01…03`, `MAT-10`, `MAT-11`, `ADUX-13`, `DBG-03`, `ING-11`, `ING-12`) · **Source:** [milestones/v1.5-ROADMAP.md](milestones/v1.5-ROADMAP.md)
**Phase count:** 6 (Phases 29-34) · **Plans:** TBD · **Status:** in progress (Phase 29 complete)
**Granularity:** standard (research sketched 29–36; merged Tavily-port+quota and enricher+cheat-sheet-files as too-thin adjacent pairs). Order is not inverted.

### Phase 29: Pass-1 richer templates

**Goal**: A newly ingested material is a Russian longread shaped like the talk, with a transcript-only facts layer and an explicit СВА takeaway — not a three-block summary.
**Depends on**: Nothing (v1.5 first phase; builds on shipped v1.1–v1.4 ingest)
**Requirements**: ART-01, ART-02, ART-03
**Success Criteria** (what must be TRUE):

  1. Opening a newly ingested lecture or podcast draft, the `##` headings follow the source talk; the three-block lecture scaffold («Тезис / Ход рассуждения / Вывод») and the podcast trio («О чём разговор / Позиции / Что запомнить») are absent.
  2. The article contains a dedicated source-facts block (names, numbers, tools, caveats) filled from the transcript only — no invented numbers, names, or tool versions.
  3. The article contains explicit «Зачем это СВА» and risks/limitations sections even if the talk barely mentioned audit; `dek` stays the 1–2 sentence hook and is not collapsed into those sections.
  4. (Owner override, D-10/D-11/D-17 — governs criterion 3 where they differ) There is exactly ONE СВА section, `## Зачем это СВА`: it is written whenever an analog for СВА exists (control, data, model, vendor, information security, process quality) and omitted honestly when none does; a second «Риски и ограничения» heading is forbidden; `dek` stays the 1–2 sentence hook.

**Plans**: TBD

**Locked scope facts (do not re-litigate):**

- Rewrite `lecture.md` / `podcast.md` honesty prompt only. Pass-1 still streams `json_object`; `stage=llm` / `llm_truncation` stay fail-closed and unchanged.
- Source-facts stay transcript-only. Do not invent cheat-sheet files, Tavily, or guide extras here.
- Do not apply the transcript character cap to future extract context (Pitfall 11).

**Plans:** 3 plans
**Wave 1**

- [x] 29-01-PLAN.md — lecture frame + shared system-prompt voice/`dek`/length rules, with the legacy-heading pins inverted (tracer)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 29-02-PLAN.md — podcast frame with kind-sentinel isolation and the audience-strip regression pin

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 29-03-PLAN.md — live ingest proof: heading list, per-bullet facts audit against the transcript, `response_chars` band, owner read (blocking)

### Phase 30: Classifier practical | conceptual

**Goal**: Every ingest records a closed topic kind; extras never attach when the kind is missing, empty, unknown, or conceptual.
**Depends on**: Phase 29
**Requirements**: KIND-01, KIND-02, KIND-03
**Success Criteria** (what must be TRUE):

  1. After ingest, the draft stores `topic_kind` as `practical` or `conceptual`.
  2. Missing, empty, or unknown `topic_kind` is stored as `conceptual` and does not attach guide sections, generated-code extras, Tavily reads, or a cheat sheet.
  3. A conceptual material has no empty «Гайд» heading and no “ссылки скоро появятся” placeholder in the body (no cheat-sheet path either). Download controls are omitted later in Phase 33 because no files exist — never a disabled CTA.

**Plans**: TBD

**Locked scope facts (do not re-litigate):**

- Closed set `practical | conceptual`. Default is **conceptual** so unattended collect cannot empty the 1000-request budget.
- Prefer a separate cheap classifier call so the pass-1 honesty prompt stays transcript-only (avoids facts contamination). Decide the exact call shape in `/gsd-plan-phase 30`.
- Public `data_collection.__all__` stays exactly ten names. `IngestError.stage` stays the locked seven values — `classify` may be a diagnostic label, not a new stage.
- Reader-facing quota/classifier badges are out of scope.

### Phase 31: Tavily quota and persist-then-enrich floor

**Goal**: Pass-1 always lands as a draft plus a pending shortlist item; Tavily is a proxy-free budgeted port that quota exhaustion and `already_saved` never spend.
**Depends on**: Phase 30
**Requirements**: ART-04, TAV-02
**Success Criteria** (what must be TRUE):

  1. A successful pass-1 write always leaves a `materials` row with `status=draft` plus a pending shortlist item, including when the topic is conceptual or Tavily is skipped.
  2. A shared counter stops initiating Tavily requests at 1000 (`try_consume`); the operator log contains `tavily_quota_exhausted`; the pass-1 draft from criterion 1 remains.
  3. Per-video initiation is capped (~5). If remaining quota cannot grant the planned `n` for that video, pass 2 is skipped (fail-soft, keep pass 1) rather than consuming a partial grant.

**Plans**: TBD

**Locked scope facts (do not re-litigate):**

- One new runtime package: `tavily-python>=0.8.5,<0.9` `AsyncTavilyClient` with injected `httpx.AsyncClient(trust_env=False, proxy is None)`. Never reuse `build_httpx_client(settings)` (YouTube SOCKS5). Never sync `TavilyClient` (`requests` inherits `HTTP_PROXY`).
- Composition-only env: `TAVILY_API_KEY`, `TAVILY_MAX_REQUESTS_PER_VIDEO` default 5. Adapters do not read `os.environ`. `SecretRegistry` + `tvly-` denylist.
- Ports in `data-collection`: `WebSearch` / `PageExtract` / `UrlLiveness`. Wiring only in `ingestion-service/composition`. No Crawl/Map/Research. No local `httpx.get` of page URLs (SSRF).
- Quota unit = HTTP calls **we** dispatch (search=1, extract POST=1), not Tavily `usage.credits`. Postgres `tavily_quota` + atomic RPC `try_consume_tavily_quota(p_n int)`; RLS on; ingest uses service_role. No Redis, no quota JSON file.
- Persist-then-enrich: pass 1 writes before any Tavily. `PersistPort.exists(youtube_video_id)` short-circuits **before** Tavily (and cheaply before LLM). Silent `ON CONFLICT DO UPDATE` is **out**.
- `IngestError.stage` unchanged. No fourth stdout checkmark. Pass 2 must not be folded into `article.process` / `ArticleError` → `stage=llm`.
- Measure TLS to `api.tavily.com` from the operator host (Phase 28-style). If it fails, that is a spike — do **not** silently fall back to the YouTube proxy. Record the second ADR-0002 public-API bend next to DeepSeek.
- **Plan with `--research-phase`:** Tavily SDK constructor/`search`/`extract` shapes; quota remaining=3 vs per-video=5 rule (locked above: skip unless full `n`); concurrent `try_consume` RPC.

### Phase 32: Pass-2 enricher and personal-KB cheat sheets

**Goal**: A practical ingest with quota may enrich the already-saved article with in-article guide, marked generated code, only live URLs, and one personal-KB markdown note per key technology — without failing ingest.
**Depends on**: Phase 31
**Requirements**: TAV-01, TAV-03, ENR-01, ENR-02, ENR-03, SHEET-01, ING-11
**Success Criteria** (what must be TRUE):

  1. For a `practical` ingest that is not `already_saved` and has remaining quota, the pipeline may call Tavily Search and Extract (at most ~5 initiated requests for that video) and may add additional guide `##` sections in `body_markdown` (not a second narrative file).
  2. Generated code in the article is marked as generated/illustrative, not as a quote from the transcript; every outbound URL stored on the material is from the video transcript/description or from a Tavily extract that returned content — `failed_results` and model-invented hrefs are dropped in code, not only in the prompt.
  3. Tavily errors, timeouts, or a failed pass-2 JSON do not fail ingest: exit 0, no `stage=llm` envelope, pass-1 draft kept.
  4. A `practical` material may attach one or more markdown notes written as a personal knowledge-base entry (dense, scannable, copy-pasteable: commands, gotchas, links) — not as a second article; each key technology in the material gets its own file. Paths live on the material, not `razbors.notebook_path`.
  5. A re-run whose `youtube_video_id` is already saved returns `already_saved` and makes zero Tavily and zero enricher calls (no second cheat-sheet files either).

**Plans**: TBD

**Locked scope facts (do not re-litigate):**

- Call shape: `search(..., search_depth="basic", max_results=5, include_answer=False, include_raw_content=False, auto_parameters=False, include_usage=True)` → httpx liveness (HEAD then GET, ~5s, https-only; liveness does **not** consume quota) → `extract(urls, extract_depth="basic", format="markdown")` batched so one extract = one quota unit.
- Allowlist in code: transcript/description URLs ∪ extract `results[].url` with non-empty content. Strip markdown hrefs outside the set **after** the LLM. Fence extracts as untrusted data. Frozen source-facts must not be rewritten from web text.
- `ArticleEnricher` is a second streamed `json_object` DeepSeek call (`thinking.disabled`), bound to `{pass_1_article, extract_texts, allowed_urls}`. Not tool-calling. Extract-context overflow **skips enrich**, does not raise `llm_truncation`. UPDATE the same material row.
- Cheat sheets: `CHEAT_SHEET_ROOT` + containment cloned from `LocalNotebookStorage` / `NOTEBOOK_ROOT`. Several files allowed, **one file per key technology**. Not a second article, not stuffed into `body_markdown`, not `razbors.notebook_path`, not Supabase Storage, not `.ipynb`. Conceptual / quota-skip / fail-soft → no files.
- Pass 2 **never** raises `IngestError`. Collect `videos_failed` must not increment (proven in Phase 34).
- **Plan with `--research-phase`:** extract whole-POST 400 on one bad URL (pre-filter locally); prompt-injection fencing and frozen-facts comparison need a concrete delimiter/normalization rule.

### Phase 33: Reader sources and cheat-sheet downloads

**Goal**: An authenticated reader and an admin previewing a draft or ready material see the same sources list and the same set of cheat-sheet downloads; missing notes omit the control rather than serving an empty file.
**Depends on**: Phase 32
**Requirements**: SHEET-02, SHEET-03, MAT-10, MAT-11, ADUX-13
**Success Criteria** (what must be TRUE):

  1. An authenticated reader opening a material with outbound URLs sees a sources block listing those URLs; if there are none, the block is omitted rather than shown empty.
  2. An authenticated reader sees a download for each cheat-sheet note that exists (filename/title from the technology) and no control for notes that were not produced; when no files exist, download controls are omitted — not a disabled CTA, not an empty file.
  3. An authenticated reader can download each existing note; a missing or path-invalid file does not return a successful empty body.
  4. Admin preview of a draft or ready material shows the same sources block and the same set of cheat-sheet downloads as the reader DTO (no second fetch shape).

**Plans**: TBD
**UI hint**: yes

**Locked scope facts (do not re-litigate):**

- Backend/SPA stay readers. SPA does not call Tavily or DeepSeek. Extend `MaterialReaderResponse` (`extra="forbid"`) once; admin preview reuses it (Phase 18 pattern).
- Authenticated `FileResponse` (`text/markdown`) with path containment. Clone razbor notebook download honesty onto a **new** materials route — do not reuse `razbors.notebook_path`.
- Honest absence: no empty «Гайд» (already gated in Phase 30), no greyed download, no “ссылки скоро появятся”. Article markdown still goes through the existing sanitizer; download is a file, not inline extract HTML.
- Knowledge search does not index cheat-sheet file text (KNOW-06 deferred). No reader-facing quota/classifier badges.

### Phase 34: Collect honesty and operator debug

**Goal**: Unattended collect treats enrich skip, quota exhaust, and fail-soft pass 2 as success for that video; `--debug` reports classifier, remaining quota, and URL counts without secrets.
**Depends on**: Phase 33
**Requirements**: ING-12, DBG-03
**Success Criteria** (what must be TRUE):

  1. `ingest-collect` treats enrich skip, quota exhaust, and fail-soft pass-2 as success for that video — they do not increment `videos_failed` and do not change the two-line stdout contract (`EXPECTED_SUCCESS_LINES` byte-identical).
  2. Operator `--debug` reports classifier, remaining Tavily quota, and opened-vs-failed URL counts, with no API keys, no `tvly-` tokens, and no extract bodies.
  3. Collect can emit `tavily_quota_exhausted` through `emit_diagnostic` (journal, not only `--debug`); `str(err)` stays sanitized; if wall-clock remaining under `TimeoutStartSec=1800` is tight, pass 2 is skipped and the video still counts as success.

**Plans**: TBD

**Locked scope facts (do not re-litigate):**

- Exists-check on mixed operator + timer re-runs (ING-11 must still hold on collect). Do not raise `INGEST_MAX_VIDEOS_PER_SOURCE`.
- Live Tavily collect tick is optional (`pipeline_ingest_sources` may still be empty); journal/exit proofs can be unit/integration against fakes.
- v1.4 `INVALID_ROLE` toast stays out. No admin «Обогатить» button. No auto-publish/auto-ready/auto-send.
- **Plan with `--research-phase`:** persist-then-update vs skip pass-2 when wall-clock remaining < bound; collect sanitize path is currently `f"{err}"`.

## Progress

**Execution Order:** 29 → 30 → 31 → 32 → 33 → 34 (v1–v1.4 phases 1–28 shipped)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 29. Pass-1 richer templates | 2/3 | In Progress|  |
| 30. Classifier practical \| conceptual | 0/? | Not started | - |
| 31. Tavily quota and persist-then-enrich floor | 0/? | Not started | - |
| 32. Pass-2 enricher and personal-KB cheat sheets | 0/? | Not started | - |
| 33. Reader sources and cheat-sheet downloads | 0/? | Not started | - |
| 34. Collect honesty and operator debug | 0/? | Not started | - |

## v1.5 roadmap locks (for phase planners)

- **Order:** 29 → 30 → 31 → 32 → 33 → 34. Do not put enrich before persist, cheat-sheet UI before the body, or collect before fail-soft.
- **Cheat sheets:** personal-KB markdown notes, **one file per key technology** (several files allowed). Not a second article. Not `razbors.notebook_path`. Guide stays in `body_markdown` sections.
- **Persist-then-enrich.** Fail-soft pass 2. Tavily `trust_env=False`. Quota 1000 initiated requests. `already_saved` skips Tavily (and the enricher).
- **Out of scope:** admin «Обогатить», DeepSeek tool-calling, Tavily-first writing, FoundryModels, auto-publish, second «гайд» file, extras on conceptual talks, multi-provider search, CiteGuard, `.ipynb` on materials, reader quota badges, v1.4 `INVALID_ROLE` toast.

## Backlog

> **Reviewed 2026-10-20** (`/gsd-review-backlog`) — v1.3 shipped 2026-10-18.
> - **Closed and removed** — 999.7 → Phase 17 · 999.1 → Phase 18 · 999.6 → Phase 19 (ADUX-10 → Phase 23) · 999.5 → Phase 22 · 999.3 resolved 2026-10-18.
> - **Promoted 2026-10-21 (v1.4 roadmap)** — 999.2 → **Phase 25**, folded into PIPEUI-04.
> - **Parked** — 999.4: product preference, not debt. Not in v1.4. Not in v1.5 (ADUX-11 deferred).

### Backlog 999.2: Follow-up — Phase 23 deferred UAT follow-up: AdminLayout chrome (PROMOTED → Phase 25)

**Goal:** Resolve the UAT checkpoint deferred during Phase 23 verification
**Source phase:** 23
**Deferred at:** 2026-10-17 during /gsd-verify-work 23 session completion
**Status:** **PROMOTED → Phase 25 (v1.4) as requirement PIPEUI-04** (2026-10-21). Do not plan it here; the work is owned by Phase 25. Closed as a backlog item.
**Follow-ups:**

- [x] Test 1: AdminLayout chrome: убрать надпись «АДМИН» над вкладками Дайджест|Пайплайн; уменьшить пустоту сверху; уменьшить кегль вкладок до уровня остальных заголовков; чуть увеличить расстояние между вкладками (promoted → Phase 25 / PIPEUI-04)

### Backlog 999.4: Follow-up — Phase 14 deferred UAT follow-up: Test 1 (Deferred — stays parked)

**Goal:** Resolve the UAT checkpoint deferred during Phase 14 verification
**Source phase:** 14
**Triaged:** 2026-10-13 — product preference, not tech debt; stays parked
**Status:** parked — **not** in v1.4 or v1.5; do not pull into Phase 29+ (it is a different editorial-workflow decision, not article enrichment)
**Deferred at:** 2026-10-04 during /gsd-verify-work 14 session completion
**Follow-ups:**

- [ ] Test 1: UX (для Phase 15+): две операции на одно editorial-решение избыточны для single-operator workflow — объединить Approve (decision) + Mark ready (material_status) в одну кнопку «Одобрить и подготовить → ready»; переименовать «Сделать ready» → «Отобрать», ready → «Отобран». (deferred 2026-10-03)
