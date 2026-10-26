# Phase 29: Pass-1 richer templates - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning

<domain>
## Phase Boundary

A newly ingested lecture or podcast draft is a Russian СВА longread whose `##` follow the talk, with an optional transcript-only «Конкретика» layer and an optional editorial «Зачем это СВА» — not the three-block lecture scaffold or the podcast trio. This phase rewrites `lecture.md` / `podcast.md` and the shared honesty prompt only.

**In scope (ROADMAP.md, do not re-litigate):**
- Pass-1 still streams `json_object`; `stage=llm` / `llm_truncation` stay fail-closed and unchanged.
- Source-facts stay transcript-only. Do not invent cheat-sheet files, Tavily, guide extras, or a classifier.
- Do not apply the transcript character cap to future extract context (Pitfall 11).
- `dek` stays the 1–2 sentence JSON hook and is not collapsed into body sections.
- `## Аудитория` remains prompt scaffolding and is stripped from `body_markdown` (Phase 9).

**Out of scope:**
- `topic_kind` / practical vs conceptual (Phase 30).
- Tavily, quota, persist-then-enrich (Phase 31).
- Pass-2 enricher, generated code, in-article guide, cheat-sheet files (Phase 32).
- Reader sources block and downloads (Phase 33).
- Collect honesty / `--debug` extras (Phase 34).
- Runtime heading validator inside the adapter (Phase 8 D-15 stands unless a test-only prompt pin is needed).
- Color / HTML highlight in the article body (sanitizer will strip it).

</domain>

<decisions>
## Implementation Decisions

### Content-shaped `##`
- **D-01:** Free `##` named after the talk's real topics/chapters. No fixed section count and no three-block skeleton. — **Reversibility:** costly — `tests/unit/test_article_templates.py` and `test_deepseek_article_adapter.py` pin the old heading strings (`## Тезис` / `## Ход рассуждения` / `## Вывод`, `## О чём разговор` / `## Позиции` / `## Что запомнить`); those pins must be rewritten to *forbid* the scaffolds and to assert the new prompt frame. Phase 8 D-16 is superseded.
- **D-02:** If the talk has no explicit chapters, split into several *implicit* editorial chapters the way an experienced editor would — do not invent a fake «Глава 1 / Глава 2» that is not in the transcript, and do not fall back to one dump section named «Содержание доклада».
- **D-03:** Authorial voice of the edition, not a recap. Forbidden phrasing: «в подкасте рассказывается», «монолог содержит», «в ролике говорится». Attribution of the speaker is allowed: «Элен считает…».
- **D-04:** Key theses in `**bold**`. Direct speech of the speaker as a markdown blockquote (`>`). Do not promise color or HTML — `rehype-sanitize` will strip it.
- **D-05:** Lecture: sections by topic only. Podcast: when it is a dialogue, sections by positions/speakers; otherwise by topic. Templates still share the honesty prompt and JSON contract (Phase 8 D-14); they differ by this one kind hint.

### `## Конкретика` (source-facts layer)
- **D-06:** The dedicated facts block is headed `## Конкретика`, not «Факты из источника». Same string in lecture and podcast so Phase 32 can freeze it. Reader-facing editorial label; the contract is unchanged: names, numbers, tools, caveats from the transcript only.
- **D-07:** Bulleted list by default (`**item** — short caveat from the transcript`). A GFM table is allowed only when the talk itself has an explicit grid of numbers.
- **D-08:** Omit `## Конкретика` entirely when there is nothing to put in it. No empty heading, no «в транскрипте нет цифр» stub. ART-02 is read as «the block exists when there is concreteness», not as a mandatory placeholder.
- **D-09:** Normalize tool names to a canonical form (PostgreSQL, not «постгрес»). Do not invent version numbers. Do not build a reader sources block here (Phase 33).

### СВА takeaway
- **D-10:** One body section only: `## Зачем это СВА`. There is no second heading «Риски и ограничения» / «Что учесть СВА» — that was duplication. Residual caution, when it belongs, lives inside this section's prose.
- **D-11:** Omit `## Зачем это СВА` when there is no concrete applicability. ART-03 «always present even if the talk barely mentioned audit» is owner-overridden: do not hide the takeaway when it exists; do not force a section on a talk with no analog.
- **D-12:** Write the section when there is a working analog for СВА — control, data, model, vendor, information security, process quality — even if the speaker never said «аудит».
- **D-13:** No rigid section order. The prompt gives a unified style frame; the model may compose freely (content-shaped `##`, `## Конкретика` when present, `## Зачем это СВА` when present). Do not encode a skeleton «середина → конкретика → СВА».
- **D-14:** When the section is present, it is a free editorial paragraph in that style — not a checklist «зачем + риск».
- **D-15:** Voice of the edition, no meta-banner: «Для СВА это значит…», never «спикер доказал, что аудиту нужно…». Quote the speaker only in `>`.
- **D-16:** Do not invent a СВА duty, an internal standard, or numbers in this section. Analogy and «стоит смотреть» are allowed; «уже требуется по политике N» is forbidden unless it is in the transcript.
- **D-17:** `dek` is always the 1–2 sentence hook about the talk. It is not a substitute for `## Зачем это СВА`. If the section is omitted, the article has no separate audit takeaway — do not smuggle it into `dek`.

### Honesty vs inference (pass-1)
- **D-18:** Pass-1 user message stays transcript-only. Editorial inference is allowed *only* in `## Зачем это СВА` (and in implicit chaptering / authorial voice). `## Конкретика` must not be rewritten from opinion or from the web.
- **D-19:** Expanding a thin talk from other sources is **out**. That is Phase 32 pass-2 Tavily, not this template rewrite.

### Claude's Discretion
- Exact English (or Russian) instruction prose inside `lecture.md` / `podcast.md`, as long as D-01…D-18 hold and the old scaffold heading strings are absent.
- Canonical-name dictionary for D-09 (PostgreSQL, Kubernetes, …) — a short prompt rule, not a shipped gazetteer, unless a test needs one or two pinned examples.
- Whether tests pin prompt *instructions* for `## Конкретика` / `## Зачем это СВА` as optional («include when…») versus asserting they always appear in scripted `body_markdown`. Prefer prompt pins + absence of old scaffolds; do not add a fail-closed heading parser (Phase 8 D-15).
- How `ARTICLE_SYSTEM_PROMPT` is tightened (authorial voice, no recap phrasing) versus putting those lines only in the template files — shared prompt still covers honesty, always-Russian, preserve-terms, JSON keys.
- `dek` wording when `## Зачем это СВА` is omitted (user chose «You decide» on D-17): keep it a topic hook, never an audit dump.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 29 goal, success criteria, locked scope facts (stream `json_object`, transcript-only facts, no Tavily/cheat-sheet here)
- `.planning/milestones/v1.5-ROADMAP.md` — v1.5 source of the same phase; owner locks for 29–34
- `.planning/REQUIREMENTS.md` — ART-01, ART-02, ART-03 (read with D-08 / D-11 owner interpretations)
- `.planning/PROJECT.md` — v1.5 framing; D-CONTENT-01 prepared article only
- `.planning/research/FEATURES.md` — table stakes: content-shaped `##`, facts layer, editorial СВА takeaway vs speaker words
- `.planning/research/PITFALLS.md` — Pitfall 3 (do not mix web extracts into facts), Pitfall 11 (pass-1 still streams; do not reuse `MAX_TRANSCRIPT_CHARS` on extracts), Pitfall 1 (pass-1 stays fail-closed)
- `.planning/research/SUMMARY.md` — Phase 29 copies Phase 8/28 call shape; skip `--research-phase`

### Prior phase decisions
- `.planning/milestones/v1.1-phases/08-deepseek-article-templates/08-CONTEXT.md` — D-01 always Russian, D-11 `json_object` `{title,dek,body_markdown}`, D-14 shared prompt, D-15 no heading validator, D-16 old headings **superseded by this phase**
- `.planning/milestones/v1.4-phases/28-live-proof-streamed-deepseek-ingest/28-CONTEXT.md` — `stream=True`, `--template` required, DeepSeek direct / YouTube proxy split

### Code contracts
- `data-collection/src/data_collection/templates/lecture.md` — rewrite; drop `## Тезис` / `## Ход рассуждения` / `## Вывод`; keep trailing `## Аудитория` scaffolding
- `data-collection/src/data_collection/templates/podcast.md` — rewrite; drop `## О чём разговор` / `## Позиции` / `## Что запомнить`; keep `## Аудитория`
- `data-collection/src/data_collection/adapters/deepseek_article.py` — `ARTICLE_SYSTEM_PROMPT`, `build_article_messages`; call shape unchanged
- `data-collection/src/data_collection/dto/article_draft.py` — still three non-blank strings + `roles`; `## Аудитория` strip stays
- `tests/unit/test_article_templates.py` — heading-string pins that must flip from «contains old scaffold» to «forbids old scaffold / contains new frame»
- `tests/unit/test_deepseek_article_adapter.py` — lecture vs podcast prompt isolation
- `tests/unit/test_article_draft_body_audience.py` — `## Аудитория` must not leak into the body

### Architecture & process
- `.cursor/rules/architecture.mdc` — Ports & Adapters; no new ports in this phase
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — DeepSeek remains the temporary public-API bend; this phase does not add Tavily

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DeepSeekArticleGenerator.process` + `_stream_content` (`stream=True`) — do not change the call shape; only the template text and possibly `ARTICLE_SYSTEM_PROMPT` wording.
- `load_article_templates` — missing `lecture.md` / `podcast.md` still fails at load (Phase 8 D-17).
- `ArticleDraft` audience-section strip — keep `## Аудитория` at the end of both templates; the strip is already tested.
- `FakeArticleGenerator` — unit tests stay on scripted drafts; no live DeepSeek in the default suite.
- MaterialPage TOC (`extractMarkdownHeadings`) — real `##` in `body_markdown` become the reader TOC for free. No new TOC widget.

### Established Patterns
- Shared system prompt + per-kind markdown template in the user message (Phase 8 D-14).
- Adapter validates only non-blank `title` / `dek` / `body_markdown` / `roles` — not heading presence (D-15). Tests assert prompt strings.
- Always-Russian, preserve technical terms, `response_format=json_object`, `thinking.disabled`.
- Public `data_collection.__all__` and `IngestError.stage` stay untouched.

### Integration Points
- Template files under `data-collection/src/data_collection/templates/`.
- Prompt assembly in `build_article_messages`.
- Unit tests listed in canonical refs; Phase 10 UAT heading checks (`## Тезис` …) are historical evidence, not a live contract — do not revive them as required reader headings.
- No backend/SPA changes. No new DTO fields. No migration.

### Hazards
- Old heading pins will red the suite the moment templates change — update those tests in the same TDD cycle, do not delete the negative «scaffold absent» coverage.
- `## Аудитория` looks like a fourth article section if the strip regresses (live materials 9/11/12).
- Putting web/enrich instructions into pass-1 would contaminate `## Конкретика` (Pitfall 3) and steal Phase 32's job.

</code_context>

<specifics>
## Specific Ideas

- Forbidden recap openers (user): «в подкасте рассказывается», «монолог содержит».
- Allowed attribution (user): «Элен считает…»; allowed СВА voice: «Для СВА это значит…».
- Rejected facts heading: «Факты из источника» (pipeline meta). Considered then rejected: «Обратите внимание», «На контроле». Locked: `## Конкретика`.
- Highlighting: bold + `>` quotes, not color.
- Analog bar for the СВА section: control / data / model / vendor / ИБ / process quality.
- Owner example of out-of-scope: if chapters are hard, «дообогатить тему из других источников» → Phase 32.

</specifics>

<deferred>
## Deferred Ideas

- Enrich / expand a thin talk from other sources when implicit chapters are hard — Phase 32 pass-2 Tavily, not pass-1 templates.
- Reader sources block for transcript URLs — Phase 33.
- Color highlighting of key thoughts — not in this stack (`rehype-sanitize`); do not add a highlight widget in v1.5.
- Runtime validation that `body_markdown` contains `## Конкретика` / `## Зачем это СВА` — still out (Phase 8 D-15); honest omit makes a required-heading parser wrong.
- Classifier `practical | conceptual` — Phase 30.
- None of the above were folded from todos (todo.match-phase 29 was empty).

</deferred>

---

*Phase: 29-Pass-1 richer templates*
*Context gathered: 2026-10-26*
