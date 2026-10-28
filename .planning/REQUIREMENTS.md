# Requirements: Digest CDS

**Defined:** 2026-10-26
**Core Value:** Authorized СВА staff can read a trustworthy weekly issue of prepared articles and influence the next разбор through one honest vote — without treating raw video/transcript as published material.

**Milestone:** v1.5 Two-pass article enrichment

## v1.5 Requirements

Requirements for this milestone. Each maps to exactly one roadmap phase.
Pass 1 is the product: a content-shaped, transcript-grounded СВА article that always persists.
Pass 2 is a gated enhancement for `practical` topics only.

### Pass-1 article

- [x] **ART-01**: A newly ingested material is a Russian longread whose `##` headings follow the source talk, not the three-block lecture scaffold («Тезис / Ход рассуждения / Вывод») or the podcast trio («О чём разговор / Позиции / Что запомнить»)
- [x] **ART-02**: The article contains a dedicated `## Конкретика` of interesting or explanatory facts (names, numbers, tools, caveats) grounded in the talk — no invented numbers, names, or tool versions. Textbook definitions, short footnotes, and reference data that make a figure readable are allowed; a static inventory of unexplained counts is not.
- [x] **ART-03**: The article contains explicit «Зачем это СВА» and risks/limitations sections even if the talk barely mentioned audit; `dek` stays the 1–2 sentence hook and is not collapsed into those sections

> **Phase 29 owner overrides** (CONTEXT.md D-08, D-10, D-11 — gathered 2026-10-26 after these lines were written; D-18/D-19 and ART-02 editorial quality — owner paths 1, 2, 4 on 2026-10-27; verification scores against this reading):
> - **ART-02** — read as «the `## Конкретика` block exists when the talk carries concreteness». Omitting it on a talk with no names/numbers/tools is correct, not a gap; no empty heading, no stub. Facts must be interesting or explanatory, not a static inventory. Pass-1 may add definitions of hard terms, footnotes, and reference data; it must not invent a version, name or number the speaker stated, and must not present added context as the speaker's words. Web research stays Phase 32.
> - **ART-03** — read as **one** optional `## Зачем это СВА` section (the separate «риски и ограничения» heading is merged into its prose, per D-10), omitted when there is no working analog for СВА (D-11). `dek` stays the 1–2 sentence hook (D-17).
- [ ] **ART-04**: A successful pass-1 write always leaves a `materials` row with `status=draft` plus a pending shortlist item, including when the topic is conceptual or Tavily is skipped

### Classifier

- [ ] **KIND-01**: Every ingest records `topic_kind` as `practical` or `conceptual` on the draft
- [ ] **KIND-02**: Missing, empty, or unknown `topic_kind` is stored as `conceptual` and does not attach guide sections, generated-code extras, Tavily reads, or a cheat sheet
- [ ] **KIND-03**: A conceptual material has no empty «Гайд» heading, no disabled cheat-sheet control, and no “ссылки скоро появятся” placeholder

### Tavily quota and pass-2

- [ ] **TAV-01**: For a `practical` ingest that is not `already_saved` and has remaining quota, the pipeline may call Tavily Search and Extract, at most ~5 initiated requests for that video
- [ ] **TAV-02**: A shared counter stops initiating Tavily requests at 1000 (`try_consume`); the operator log contains `tavily_quota_exhausted`; the pass-1 draft from ART-04 remains
- [ ] **TAV-03**: Tavily errors, timeouts, or a failed pass-2 JSON do not fail ingest: exit 0, no `stage=llm` envelope, pass-1 draft kept
- [ ] **ENR-01**: A `practical` article that completed pass 2 may include additional guide `##` sections in `body_markdown` (not a second narrative file)
- [ ] **ENR-02**: Generated code in the article is marked as generated/illustrative, not as a quote from the transcript
- [ ] **ENR-03**: Every outbound URL stored on the material is either from the video transcript/description or from a Tavily extract that returned content; `failed_results` and model-invented hrefs are dropped in code, not only in the prompt

### Cheat sheet

- [ ] **SHEET-01**: A `practical` material may attach one or more markdown notes written as a personal knowledge-base entry (dense, scannable, copy-pasteable: commands, gotchas, links) — not as a second article; each key technology in the material gets its own file
- [ ] **SHEET-02**: When no cheat-sheet files exist, the material page and admin preview omit download controls — they do not show a disabled CTA or serve an empty file
- [ ] **SHEET-03**: Paths live on the material (not `razbors.notebook_path`); an authenticated reader can download each existing note; a missing or path-invalid file does not return a successful empty body

### Reader and admin delivery

- [ ] **MAT-10**: An authenticated reader opening a material with outbound URLs sees a sources block listing those URLs; if there are none, the block is omitted rather than shown empty
- [ ] **MAT-11**: An authenticated reader sees a download for each cheat-sheet note that exists (filename/title from the technology), and no control for notes that were not produced
- [ ] **ADUX-13**: Admin preview of a draft or ready material shows the same sources block and the same set of cheat-sheet downloads as the reader DTO (no second fetch shape)

### Operator and collect

- [ ] **DBG-03**: Operator `--debug` reports classifier, remaining Tavily quota, and opened-vs-failed URL counts, with no API keys, no `tvly-` tokens, and no extract bodies
- [ ] **ING-11**: A re-run whose `youtube_video_id` is already saved returns `already_saved` and makes zero Tavily and zero enricher calls
- [ ] **ING-12**: `ingest-collect` treats enrich skip, quota exhaust, and fail-soft pass-2 as success for that video — they do not increment `videos_failed` and do not change the two-line stdout contract

## Deferred Requirements

Acknowledged but not in this milestone's roadmap. IDs are reserved and never reused.

### Ingestion

- **ING-10**: Ingest HTTP API in place of the systemd/CLI path (carried from v1.4)
- **ING-13**: Re-ingest that updates enrichment on an existing `youtube_video_id` without duplicating the material (needed if pass 2 died after persist; v1.5 default is skip)

### Admin

- **ADUX-11**: Unify Approve + Mark ready — backlog 999.4, parked by product preference
- **ADUX-14**: Quiet admin-preview note «обогащение не выполнялось» — only if UAT shows surprise
- **PIPE-06**: PIPE execution — running the pipeline, not only editing its config

### Knowledge

- **KNOW-06**: Index cheat-sheet file text in knowledge search (body_markdown guide sections are enough for v1.5)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Admin «Обогатить» / re-Tavily button | Second writer path in the SPA; scheduled ingest would still be thin; owner locked automatic pass 2 only |
| DeepSeek tool-calling one-shot wrapping Tavily | Pass-1 floor disappears; quota becomes nondeterministic; owner rejected |
| Tavily-first inverted writing | Article would be a web compilation, not a разбор of this video |
| FoundryModels / contour-native LLM swap | ADR-0002 revisit, not v1.5 |
| Auto-publish / auto-ready / auto-send | Review-first digest contract; collection may be cron, send is human |
| Second downloadable «гайд» file | Guide lives in `body_markdown`; extras are personal-KB cheat-sheet notes, one file per key technology |
| Code / Tavily / cheat sheet on conceptual talks | Diátaxis mixing; wastes the 1000-request budget |
| Multi-provider search fallback (Exa / Brave / DDG) | Widens the ADR-0002 public-API bend; silent quality change. Exhaust → keep pass 1 |
| Claim-level NLI / CiteGuard | Liveness allowlist is the v1.5 bar |
| Executing generated code or attaching `.ipynb` to the material | Notebooks belong to разборы (US-20) |
| Reader-facing quota / classifier badges | Ops internals; extras (or their absence) are the signal |
| v1.4 `INVALID_ROLE` toast | Explicitly parked; needs an authenticated live SPA session |
| Publishing Tavily extracts as materials | Extracts are pipeline input, like captions |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ART-01 | Phase 29 | Complete |
| ART-02 | Phase 29 | Complete |
| ART-03 | Phase 29 | Complete |
| ART-04 | Phase 31 | Pending |
| KIND-01 | Phase 30 | Pending |
| KIND-02 | Phase 30 | Pending |
| KIND-03 | Phase 30 | Pending |
| TAV-01 | Phase 32 | Pending |
| TAV-02 | Phase 31 | Pending |
| TAV-03 | Phase 32 | Pending |
| ENR-01 | Phase 32 | Pending |
| ENR-02 | Phase 32 | Pending |
| ENR-03 | Phase 32 | Pending |
| SHEET-01 | Phase 32 | Pending |
| SHEET-02 | Phase 33 | Pending |
| SHEET-03 | Phase 33 | Pending |
| MAT-10 | Phase 33 | Pending |
| MAT-11 | Phase 33 | Pending |
| ADUX-13 | Phase 33 | Pending |
| DBG-03 | Phase 34 | Pending |
| ING-11 | Phase 32 | Pending |
| ING-12 | Phase 34 | Pending |

**Coverage:**
- v1.5 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-26*
*Last updated: 2026-10-26 after v1.5 roadmap (phases 29–34)*
