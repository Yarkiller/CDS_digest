# Feature Research

**Domain:** Two-pass enriched knowledge articles for an internal editorial digest (СВА Сбербанка)
**Project:** Digest CDS — milestone v1.5
**Researched:** 2026-10-26
**Confidence:** HIGH on the feature landscape (owner-locked decisions + shipped ingest/reader). MEDIUM on Tavily credit accounting and analog products (GSD `classify-confidence`: verified websearch = MEDIUM, verified Context7 = MEDIUM).

> **Scope.** Subsequent milestone. Auth, issue/archive, voting, knowledge search, разборы + `.ipynb`, admin shortlist → preview → ready → send, and YouTube → DeepSeek 3-block ingest are **already shipped**. They are consumers and constraints, not rebuild targets. This file answers: what should operator / админ / сотрудник СВА be able to *do* once ingest writes a richer article.

> **Locked product shape (do not reopen).** Material is a prepared article only (D-CONTENT-01) — never video/transcript as material. Two-pass approach 1: pass 1 transcript-grounded article + `practical | conceptual` classifier; pass 2 Tavily then enricher, only when practical. Cheat sheet = downloadable markdown file; guide = sections inside the article. Links must be real. Pass-1 article still persists when Tavily is skipped or quota is exhausted.

## How two-pass enriched articles typically work

Internal editorial digests that use an LLM do **not** one-shot a polished longread from a transcript plus the open web. The recurring, trustworthy shape is:

1. **Grounded draft from the source.** Write a complete article from the transcript (and video description) only. Structure follows the talk, not a fixed three-block scaffold. Extract names, numbers, tools, and caveats into a dedicated facts layer so they cannot drown in prose. This pass must stand alone.
2. **Classify the job of the piece.** Diátaxis (action vs cognition): a *practical* talk needs doing-oriented extras (how-to, code, cheat sheet, live docs). A *conceptual* talk needs explanation and the audit takeaway — numbered steps and generated code make it worse. Mixing the two is the main documented cause of confusing knowledge pages.
3. **Retrieve, then enrich — never invent the web.** Short search queries → extract/read only pages that actually open → second LLM pass may add guide sections, generated code, and a cheat sheet, citing **only** URLs from the video plus successfully extracted pages. Failed extracts are dropped, not paraphrased. Quote-then-answer / retrieve-then-generate (Tutor Kai arXiv 2405.06681; citation-grounding practice) is the analog; Tavily-first “search then write the article” is the inversion this milestone rejects.
4. **Human send gate stays.** Review-first newsletters (Vona AI Weekly Review, Impri, newsletter4link) automate collection and drafting; a named editor still approves facts, links, and the issue. Digest CDS already has this: draft → админ ready/approve/send. v1.5 must not add auto-publish or an admin «Обогатить» button.
5. **Degrade to the floor, not to silence.** When the search API is out of quota, keep the pass-1 article. Auxiliary enrichment is not allowed to fail the ingest or to fake completeness with invented links (Hermes-agent: fail-closed beats a cheap hallucinated fallback for anything readers will trust).

**Opinionated mapping for Digest CDS:** pass 1 *is* the product. Pass 2 is a gated enhancement for practical topics. The three-block lecture/podcast templates (`## Тезис / Ход рассуждения / Вывод` and `## О чём разговор / Позиции / Что запомнить`) are the defect, not a style preference.

## Personas (CONTEXT.md + ingest operator)

| Persona | Job in v1.5 | Does not do |
|---------|-------------|-------------|
| **Operator** (CLI / systemd `ingest-collect`; not a CONTEXT glossary role, but the v1.1–v1.3 writer) | Runs the same ingest path unattended. Gets a draft even when Tavily is skipped. Sees classifier, Tavily consume, and `tavily_quota_exhausted` in logs/`--debug`. | No new HTTP ingest API. No live Tavily from a laptop UI. |
| **Админ** (CDS / делегат) | Previews the richer article the way a reader will see it (existing admin-gated preview). Checks sources and, for practical drafts, the cheat-sheet file. Promotes draft→ready, approve/reject, send — unchanged. | No «Обогатить» button. No re-run of Tavily from `/admin`. No auto-send. |
| **Рядовой сотрудник СВА** | Reads a useful article: content-shaped sections, facts that survived, «зачем СВА» + risks, TOC, provenance. Downloads a cheat sheet only when one exists. Follows only real links. | Never watches the source video inside the product. Never sees quota, classifier, or Tavily internals. |
| **Data Analyst / Data Scientist** | Same reader contract, plus practical extras they can reuse (guide steps, generated code, cheat sheet) on doing-oriented talks. Search still finds the article. | No second “guide file”. No runnable notebook on the material (that remains разбор `.ipynb`). |

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete. **v1.5 table stakes are the new article contract plus honest delivery on existing surfaces.**

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Content-shaped article sections (not the three-block scaffold) | A СВА reader opening a «статья» expects a real longread whose headings follow the talk; US-07 already promises prose + TOC. Three dry blocks feel unfinished. | MEDIUM | Rewrite `lecture.md` / `podcast.md` and the DeepSeek system prompt. TOC already derives from markdown headings (`MaterialPage` + `extractMarkdownHeadings`) — no new TOC widget if headings are real `##`. |
| Dedicated source-facts layer (names, numbers, tools, caveats) | The stated failure of v1.1 articles is lost or drowned detail. Facts must be findable, not only implied in prose. | MEDIUM | A first-class section (or structured block in `body_markdown`), filled from the transcript only on pass 1. Do not invent numbers. |
| Explicit «зачем СВА» + risks, even if the talk barely says them | US-05 already asks for an audit dek; v1.5 makes the *body* carry the audit takeaway and residual risks. Without this, the piece is a YouTube recap, not a СВА article. | MEDIUM | Editorial inference is allowed here (unlike facts/links). Label it as the editorial takeaway, not as “the speaker said”. Keep `dek` as the 1–2 sentence hook; do not collapse dek and this section into one. |
| `practical \| conceptual` classifier on every ingest | Readers punish a conceptual essay padded with fake steps, and a how-to that never shows how. Diátaxis: doing vs knowing is the page’s job. | MEDIUM | Closed enum on the draft (new field, not a tag the SPA invents). Default fail-closed to `conceptual` if the classifier is empty/invalid — extras stay off. |
| Pass 1 always persists a complete `materials` draft + shortlist row | Operator and админ already trust “ingest → draft in `/admin/digest`”. A Tavily blip must not delete that. Owner lock: pass-1 still persists. | LOW–MEDIUM | Reuse `persist_draft_and_enqueue`. Pass 2 updates the same draft (body/sources/file) or no-ops; it must not require a second material row. |
| Code / in-article guide / Tavily / cheat sheet **only** when `practical` | Mixing tutorial furniture into an explanation is the documented KB failure mode. | LOW (gate) / MEDIUM (payloads) | Conceptual: no empty «Гайд» heading, no disabled download, no “ссылки скоро появятся”. Practical-without-Tavily: pass-1 article remains, extras omitted honestly. |
| In-article guide is extra **sections**, not a second file | Knowledge-base how-to lives in the article (one task, steps, result). A second narrative file splits the reader and the TOC. | LOW–MEDIUM | Enricher appends/inserts `##` sections into `body_markdown`. Same `MaterialPage` renderer. |
| Links are real: transcript/description URLs **plus** Tavily pages that opened | Hallucinated docs URLs are a trust break in an audit audience. Vona’s digest auto-check: every link from sources that were actually read. | MEDIUM | Allowlist = video metadata/description URLs ∪ `extract.results[].url`. Drop `failed_results`. Never let the enricher emit a URL outside the allowlist. |
| Cheat sheet is a downloadable markdown file on practical materials | Analysts/DS expect a take-away they can keep, analogous to разбор «Скачать .ipynb». Guide stays in the article. | MEDIUM | New attachment on the material (path/column analog of `razbors.notebook_path`). Reader CTA only when the file exists. Admin preview must be able to download it before ready. |
| Reader sources block on the material page | US-09 already shows provenance; v1.5 adds the actual outbound URLs. Without it, “verified links” are invisible. | MEDIUM | Extend `MaterialReaderResponse` (today: slug/title/dek/body/format/provenance/tags/related/reading_minutes). Backend/SPA stay readers — they do not call Tavily. |
| Global Tavily cap 1000 with `try_consume`; per-video ~5; on exhaust log `tavily_quota_exhausted` and keep pass 1 | Operator must not silently burn the month’s credits or lose the draft. Tavily free plan is 1000 credits/month; the **product** ledger is the cap that matters. | MEDIUM | Count **our** requests, not Tavily’s billing reset. Basic Search = 1 credit; basic Extract = 1 credit per 5 successful URLs (failed URLs free). Prefer short searches + one extract batch. No Crawl/Research (15–250 credits). |
| Unattended two-pass on the existing CLI/timer | v1.3 already collects without a human at the keyboard. Enrichment that needs a button will not run on systemd. | MEDIUM | Same `ingest` / `ingest-collect` entry. New stages behind ports in `data-collection`, wired only in `ingestion-service/composition`. |
| Admin preview parity for the richer article | Админ cannot promote what they cannot see (v1.2/v1.3 honesty). | LOW | Reuse `GET /admin/materials/{slug}` + `MaterialPage` preview banner. If sources/cheat-sheet join the reader DTO, preview gets them free. |
| Honest absence | Empty stubs (“код появится”, greyed download) are worse than omission. | LOW | Conceptual or quota-skipped practical: no cheat-sheet control. Contrast разбор: missing `.ipynb` still shows a strip because a разбор *should* have one. A conceptual article should not. |

### Differentiators (Competitive Advantage)

Not required for a generic “AI summary of a video”. These are why Digest CDS is a СВА издание rather than a caption dump.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Audit takeaway + risks **beyond** what the talk said | The talk is rarely about internal audit. The value is “what this means for СВА” — the dek was a teaser; the body section is the point. | MEDIUM | Prompt-design + review, not a new UI. Risk of overclaim: keep this section clearly editorial. |
| Classifier-gated Tavily (do not search conceptual talks) | Saves the 1000-request budget for talks where extra docs change the article. Conceptual RAG noise is a known quality drop. | LOW–MEDIUM | Classifier is the feature; Tavily is the consequence. |
| Generated code allowed (not copied from the transcript) | Practical talks omit the snippet the analyst needs. Generating an illustrative fragment is useful **if** it is not claimed as a quote. | MEDIUM | Mark as generated/illustrative in the article. Not executed. Not a `.ipynb`. |
| Live-URL allowlist from Tavily `failed_results` | “Looks cited” is the failure mode of Deep Research agents (arXiv 2604.03173). Showing only opened pages is the cheap, honest bar. | MEDIUM | Full NLI/CiteGuard entailment is **not** v1.5 (see anti-features). |
| Cheat sheet as markdown (plain text, offline, shareable) | Same job as a printed reference card; Markdown is the format this stack already renders. Mirrors разбор file download without inventing a second article type. | MEDIUM | Filename derived from slug; `text/markdown` download. |
| Pass-1 article remains useful when pass 2 is skipped | Quota, classifier=conceptual, or extract-all-failed still ships a structured СВА article. That is the reliability differentiator versus “enrich or nothing”. | LOW (policy) | Must be visible in operator logs so the админ is not surprised by a thinner practical draft. |
| Facts layer as a scannable block | Lets a hurried аудитор skip prose and still catch the library name, version, and caveat. | LOW–MEDIUM | Keep it inside `body_markdown` so TOC/search/email preview keep working without a new DTO field in v1.5 unless sources need structure. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Admin «Обогатить» / re-Tavily button | “Let me enrich a draft I already have” | Out of scope; creates a second writer path in the SPA; burns quota from a click; scheduled ingest would still be thin. | Re-run the CLI/timer on the same URL (`already_saved` semantics must be decided so a re-run can *update* enrichment without duplicating the material — phase research). |
| DeepSeek tool-calling one-shot | “One LLM call, tools for search” | Pass-1 article is no longer a persistable floor; harder to test; quota becomes nondeterministic. Owner rejected. | Two explicit passes, ports, `try_consume`. |
| Tavily-first inverted writing | “Better articles if we search first” | Grounding flips to the web; transcript facts get overwritten; video-specific caveats vanish. Owner rejected. | Transcript-grounded pass 1, Tavily as extra reading. |
| Overnight multi-agent / FoundryModels | “Closer to ADR-0002 / fancier quality” | Out of scope for v1.5; new contour. | Keep DeepSeek + Tavily behind ports. |
| Auto-publish / auto-ready / auto-send | “Fully automatic digest” | Breaks the review-first contract and ADMIN-03. Collection may be cron; send is human. | Drafts + pending shortlist only. |
| Video / audio / raw transcript as material | “Reader can check the source” | Locked D-CONTENT-01. Provenance + source URL are enough. | Keep YouTube URL in provenance/sources, never embed. |
| Invented or unchecked URLs | “Article looks complete” | Trust break for СВА. | Allowlist + drop failed extracts. |
| Second downloadable “гайд” file | “Guide should be a file too” | Splits TOC, search, and email preview; duplicates the article. | Guide in `body_markdown`; only cheat sheet is a file. |
| Code / Tavily / cheat sheet on conceptual talks | “Always richer” | Diátaxis mixing; wasted quota; fake practicality. | Classifier gate. |
| NLI / CiteGuard claim-level verification | “Every sentence cited” | Heavy second model, new failure modes, not needed once URLs are live and facts are transcript-bound. | Liveness allowlist + transcript-only facts layer. |
| Multi-provider search fallback (Exa / Brave / DDG) | “Survive Tavily quota” | Widens the ADR-0002 public-API bend; different corpora; silent quality change. | Stop, log `tavily_quota_exhausted`, keep pass 1. |
| Reader-facing Tavily quota / classifier badge | “Transparency” | Noise; leaks ops internals; invites gaming. | Operator `--debug` + logs. Optional quiet enrichment note for админ preview only if it prevents surprise. |
| Executing generated code, or attaching `.ipynb` to the material | “Make it runnable” | Wrong artefact: notebooks belong to разборы (US-20). Execution is a security surface. | Fenced markdown examples; разбор stays the notebook path. |
| Interactive cheat-sheet editor in admin | “Fix the file before send” | New CMS; out of milestone. Админ already has the article body in preview. | Download to inspect; reject/re-ingest if wrong. |
| Publishing Tavily extracts as materials | “Keep the extra pages” | Extracts are pipeline input, like captions — not материалы. | Use them only as enricher context. |
| v1.4 `INVALID_ROLE` toast | Carry from previous milestone | Explicitly out of v1.5. | Leave parked. |

---

## Feature Dependencies

```
[Existing captions + metadata + DeepSeek ArticleGenerator]
    └──requires──> [Pass-1 templates: content-shaped sections + facts layer + «зачем СВА»/risks]
                       └──requires──> [Classifier practical|conceptual on ArticleDraft]
                              │
                              ├──conceptual──> [Persist pass-1 draft + shortlist] ──> [Reader as today + sources if any from the video]
                              │
                              └──practical──> [try_consume Tavily quota]
                                                ├──exhausted──> log tavily_quota_exhausted ──> [Persist pass-1]
                                                └──ok──> [Search short queries]
                                                           └──requires──> [Extract / read; keep only opened URLs]
                                                                  └──requires──> [Enricher: guide sections + optional generated code + cheat sheet md]
                                                                         └──requires──> [Persist updated body + sources + cheat-sheet file]
                                                                                └──requires──> [Reader: sources block + cheat-sheet download]
                                                                                       └──enhances──> [Admin preview parity]
                                                                                       └──enhances──> [Knowledge search still indexes body_markdown]

[Cheat-sheet download UX]
    └──requires──> existing razbor notebook download pattern (auth blob + filename)
    └──conflicts──> second guide file

[Tavily]
    └──requires──> port in data-collection + wiring in ingestion-service/composition
    └──conflicts──> SPA/backend calling Tavily
    └──conflicts──> DeepSeek tool-calling one-shot
    └──conflicts──> Tavily-first inverted writing
```

### Dependency Notes

- **Pass-1 templates are the first vertical slice.** They improve every article, including conceptual and quota-skipped practical, without Tavily. Classifier and Tavily must not block this.
- **Classifier is the gate, not a tag for the reader.** It decides whether pass 2 runs. Do not render `practical` as a public badge unless product later asks; the extras (or their absence) are the signal.
- **Persist-then-enrich vs enrich-then-persist.** Owner lock: pass-1 article still persists. Implement as: persist pass-1, then if practical and quota allows, enrich and update the same row. A crash after persist must leave a valid draft (idempotent re-run is a phase-level research flag).
- **Sources DTO is a backend/SPA change; Tavily is not.** `Material` today has `provenance_label` and no URL list or file. Reader/admin only *display* what ingest wrote.
- **Cheat-sheet storage should copy `razbors.notebook_path` + `downloadRazborNotebook`, not invent a CMS.** Missing file on a practical material: hide the CTA or show an honest caption — never a 200 empty file.
- **Video description URLs belong in the allowlist even without Tavily.** A conceptual talk can still cite the speaker’s GitHub if it was in the description and is a real URL. That is pass-1 provenance, not pass-2.
- **Email digest stays a list of titles/deks/links.** Do not require the cheat sheet to travel in SMTP. The material page is the file’s home.
- **Knowledge search** indexes `body_markdown`. Guide sections therefore become searchable “for free”; the cheat-sheet file does not unless we explicitly index it (defer — P3).

---

## MVP Definition

### Launch With (v1.5)

Minimum honest ingest that a СВА reader can use, an админ can triage, and an operator can run unattended.

- [ ] **Pass-1 richer article** — content-shaped sections, facts layer, «зачем СВА» + risks; no invented links; still a `draft` + shortlist row.
- [ ] **Classifier** — `practical | conceptual`; extras only on practical; invalid → conceptual.
- [ ] **Pass-2 Tavily for practical** — short queries, extract, allowlist of opened URLs + video URLs; `try_consume` global 1000 and ~5/video; `tavily_quota_exhausted` + pass-1 persist.
- [ ] **Practical extras** — in-article guide sections; optional generated code marked as generated; cheat-sheet `.md` file when produced.
- [ ] **Reader + admin delivery** — sources block; cheat-sheet download when present; preview parity; conceptual/quota-skip honest absence.
- [ ] **Operator visibility** — staged logs/`--debug`: classifier, credits remaining, opened vs failed URLs, no secret leak.

### Add After Validation (v1.x)

- [ ] Re-ingest that *updates* enrichment on an existing `youtube_video_id` without duplicating the material (needed if pass 2 died after persist).
- [ ] Quiet admin-preview note “обогащение не выполнялось (квота / conceptual)” — only if UAT shows surprise.
- [ ] Index cheat-sheet text in knowledge search.
- [ ] Per-source Tavily domain allow/deny (corporate contour), if extracts pull junk.

### Future Consideration (v2+)

- [ ] FoundryModels / contour-native LLM (ADR-0002 revisit).
- [ ] Claim-level citation (CiteGuard/NLI).
- [ ] Admin Enrich button or HTTP ingest API.
- [ ] Auto-publish.
- [ ] Material `.ipynb` or executable sandboxes.
- [ ] v1.4 `INVALID_ROLE` toast (parked).

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Pass-1 content-shaped sections + facts + «зачем СВА»/risks | HIGH | MEDIUM | P1 |
| Classifier `practical \| conceptual` | HIGH | MEDIUM | P1 |
| Persist pass-1 even when pass 2 skipped | HIGH | LOW–MEDIUM | P1 |
| Tavily search/extract + live-URL allowlist | HIGH | MEDIUM | P1 |
| Quota `try_consume` 1000 / ~5 per video + `tavily_quota_exhausted` | HIGH | MEDIUM | P1 |
| In-article guide (practical only) | HIGH | MEDIUM | P1 |
| Cheat-sheet markdown download (practical only) | HIGH | MEDIUM | P1 |
| Reader sources block + admin preview parity | HIGH | MEDIUM | P1 |
| Generated code examples (practical, marked generated) | MEDIUM | MEDIUM | P1 (allowed, not mandatory on every practical talk) |
| Operator `--debug` for classifier/Tavily | MEDIUM | LOW | P1 |
| Re-ingest update semantics | MEDIUM | MEDIUM | P2 |
| Search-index the cheat sheet | LOW | LOW–MEDIUM | P3 |
| NLI citation verification | LOW (for this audience, given live URLs) | HIGH | P3 / never in v1.5 |

**Priority key:**
- P1: Must have for v1.5 launch
- P2: Should have once the persist/re-run seam is proven
- P3: Nice to have / future

**Phase ordering implication (for the roadmapper):** templates + classifier + persist floor **before** Tavily; Tavily port + quota **before** enricher; enricher **before** reader/admin DTO. Do not wait on cheat-sheet UI to ship a better article body — the body is the reader’s table stake; the file is the practical extra.

---

## Competitor Feature Analysis

| Feature | Review-first AI newsletter (Vona / Impri / newsletter4link) | Knowledge-base / Diátaxis | Lecture RAG (Tutor Kai, transcript-RAG) | Digest CDS v1.5 |
|---------|-------------------------------------------------------------|---------------------------|------------------------------------------|-----------------|
| Source → draft | Cron collect, LLM draft | Human writes per page type | Retrieve chunks then generate | CLI/timer: captions → pass-1 article |
| Human gate | Editor approves issue; never auto-send | Editorial review | Usually Q&A, no digest send | Existing админ ready/approve/send |
| Structure | Issue blocks / summaries | Tutorial vs how-to vs explanation vs reference | Answer + timestamps | Content-shaped article + facts + «зачем СВА» |
| Extra reading | Links from feeds that were read | Separate how-to vs concept pages | Retrieved transcript/slides | Tavily only if practical; opened pages only |
| Takeaway artefact | — | Cheat sheet / PDF as secondary | — | Markdown cheat sheet file; guide in article |
| Failure mode | Missed review → delay, not silent send | Mixed-type pages confuse | Hallucinated citations | Quota → pass-1 draft; no invented URLs |
| Media as content | Rarely | Never in a how-to | Video is the product | **Never** (locked) |

---

## Sources

Primary (HIGH — owner + codebase, not an MCP provider):

- `.planning/PROJECT.md` v1.5 goal and locked two-pass behaviour (2026-10-26).
- `CONTEXT.md` personas; US-05 audit dek, US-07 prose+TOC, US-09 provenance, US-20 разбор notebook download.
- Shipped ingest: `data-collection` templates `lecture.md` / `podcast.md` (three-block), `ArticleDraft` / `MaterialDraft`, `DeepSeekArticleGenerator` (“Use only the transcript”), `run_ingest_pipeline`.
- Shipped reader: `MaterialReaderResponse` (no sources list, no file), `MaterialPage` TOC/dek/provenance, admin preview reuse, `RazborPage` notebook download analog, `razbors.notebook_path`.

Ecosystem (MEDIUM — `classify-confidence --provider websearch --verified` and `context7 --verified` both returned MEDIUM):

- Diátaxis foundations — https://www.diataxis.fr/foundations/ (doing vs knowing; mixing types is the failure). Also Document360 content types; Scale Math classifier.
- Tavily docs via Context7 `/websites/tavily` + `/tavily-ai/tavily-python` and https://docs.tavily.com/documentation/api-credits — Search 1–2 credits; Extract `results`/`failed_results`; basic extract 1 credit / 5 successful URLs; failed URLs free; free plan 1000 credits/month; `UsageLimitExceededError`.
- Retrieve-then-generate: Tutor Kai arXiv 2405.06681; quote-then-answer grounding (Neel Mishra, citation-grounding).
- URL liveness vs claim entailment: citesure, CiteGuard, arXiv 2604.03173. v1.5 takes liveness only.
- Review-first newsletters: Vona “AI Weekly Review”; Impri HITL docs; julianandrade/newsletter4link (cron collects, human sends).
- Quota: persist a baseline; do not cheap-fallback authority-bearing output (Hermes-agent #36002; zero-llm-fallback as the “floor” pattern).

---

*Feature research for: Digest CDS v1.5 — two-pass article enrichment (Tavily + cheat sheets)*
*Researched: 2026-10-26*
