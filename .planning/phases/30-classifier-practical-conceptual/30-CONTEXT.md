# Phase 30: Classifier practical | conceptual - Context

**Gathered:** 2026-10-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Every ingest records a closed `topic_kind` (`practical` | `conceptual`) on the draft. Guide sections, generated-code extras, Tavily reads, and a cheat sheet never attach when the kind is missing, empty, unknown, or conceptual. This phase adds the classifier port + field, persist of `topic_kind`, and a pass-1 body strip so `## Гайд` / «ссылки скоро появятся» cannot leak into the saved article.

**In scope (ROADMAP.md, do not re-litigate):**
- Closed set `practical | conceptual`. Default is **conceptual** so unattended collect cannot empty the 1000-request Tavily budget (KIND-02: missing / empty / unknown / malformed → `conceptual` in code).
- Prefer a **separate cheap classifier call** so the pass-1 honesty prompt stays transcript-only (avoids Pitfall 3 facts contamination). Exact call shape is planner work.
- Public `data_collection.__all__` stays exactly ten names. `IngestError.stage` stays the locked seven values — `classify` may be a diagnostic label, not a new stage.
- KIND-03: a conceptual material has no empty «Гайд» heading and no “ссылки скоро появятся” placeholder. Download controls are omitted later in Phase 33 because no files exist — never a disabled CTA.
- Reader-facing quota/classifier badges are out of scope.

**Out of scope:**
- Tavily port, quota, persist-then-enrich floor (Phase 31).
- Pass-2 enricher, generated code, in-article guide sections, cheat-sheet files (Phase 32).
- Reader sources block and cheat-sheet downloads (Phase 33).
- Collect honesty / `--debug` extras (Phase 34).
- Admin «Обогатить» / re-Tavily button; reader-facing classifier badge; ADUX-14 quiet admin note.
- Runtime heading validator that fails ingest (Phase 8 D-15 stands). The `## Гайд` strip is a sanitizer like `## Аудитория`, not a fail-closed parse.

</domain>

<decisions>
## Implementation Decisions

### Practical bar
- **D-01:** `practical` only when the talk names a concrete product/stack **and** gives repeatable steps an analyst or DS can follow. Methodology and «как устроено» stay `conceptual`. — **Reversibility:** costly — the prompt, gold labels, and who spends Tavily all hang on this bar.
- **D-02:** «Инструмент» is a **named product**, not runnable-only code. Excel, SAP, Tableau, Power BI, Jira, Python, Kubernetes count when they have steps. A talk that only explains how Kubernetes is built, with no procedure, is `conceptual`.
- **D-03:** Steps must be followable **without the video** — numbered or checklist steps in that product. «Потом открываете SAP и смотрите» with no procedure is `conceptual`. A click-through demo by itself is not enough.
- **D-04:** The classifier does **not** filter by СВА domain. Any named product + followable steps can be `practical`; Tavily (Phase 32) fetches that product's docs. The СВА analog stays in `## Зачем это СВА` (Phase 29 D-10…D-12).

### Mixed talks
- **D-05:** Mixed theory + demo is `practical` only if doing **dominates**. A single demo inside a theory talk stays `conceptual` and must not spend Tavily. — **Reversibility:** costly — this is the quota gate for unattended collect.
- **D-06:** «Dominates» is the Diátaxis **job of the page**: did the reader come to **do** or to **understand**. Do not count minutes and do not require 50% of the transcript.
- **D-07:** Job wins over a followable illustration. A lecture «как устроен X» with a complete copy-pasteable example stays `conceptual`; the example remains in the pass-1 article as-is and does not open extras.
- **D-08:** If the classifier **successfully answers** but is unsure whether the job is doing or knowing, the prompt instructs it to pick **`practical`** (owner: better to enrich a how-to than miss one). This is **not** KIND-02. Missing, empty, unknown, or malformed `topic_kind` is still stored as `conceptual` in code. — **Reversibility:** costly — this is the opposite of the research bias default; tests must pin both layers so «please be helpful» cannot launder invalid JSON into `practical`.

### Conceptual / pass-1 body honesty (KIND-03)
- **D-09:** Strip in **code** before persist, same pattern as `## Аудитория` (`strip_audience_section`). Prompt-only KIND-03 is not enough. The strip does not fail ingest (Phase 8 D-15).
- **D-10:** Closed set: the entire `## Гайд` section (empty **or filled**) plus the literal placeholder «ссылки скоро появятся». A filled guide on a conceptual talk also goes — extras exist only in pass-2 (Phase 32).
- **D-11:** Run the strip on **every** pass-1 body, not only conceptual. Pass-1 never owns `## Гайд`; a practical draft must not carry an empty guide heading into persist-before-Tavily.
- **D-12:** Exact match only: ATX heading whose text is exactly `Гайд`, plus the exact substring «ссылки скоро появятся». Do not guess `Guide` / `How-to` / `Как сделать` / `Tutorial` / `Шпаргалка` — those can be real talk content.

### Claude's Discretion
- **Classifier input** (gray area not selected): transcript snippet vs title+dek vs pass-1 article. Keep the call cheap and separate from the honesty prompt; do not mix web/extract text into the classifier.
- Exact JSON shape of the classifier response, as long as the stored value is the closed enum and KIND-02 mapping holds in code.
- `TopicKindClassifier` as a `Protocol` under `data-collection/ports/`, adapter module-private (DeepSeek `json_object`, `thinking.disabled`, same `trust_env=False` client). Do **not** add it to `data_collection.__all__` (stays ten names). In-memory fake in tests, same as `FakeArticleGenerator`.
- How `topic_kind` is persisted (additive column on `materials` + RPC param vs another store). KIND-01 requires it on the draft; a column is a migration and is the research sketch. Do not stuff it into `provenance_label`. Do not invent a reader/admin badge.
- Whether «unsure → practical» is a prompt sentence only (preferred — no third enum value).
- Strip implementation: sibling of `strip_audience_section` in `data-collection/src/data_collection/dto/_body.py` vs a new helper; tests clone `test_article_draft_body_audience.py`.
- Classifier prompt prose that encodes D-01…D-08, including the named-product examples, as long as the bar does not drift.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 30 goal, success criteria, locked scope facts (closed set, default conceptual, `__all__` / `Stage`, no reader badges)
- `.planning/milestones/v1.5-ROADMAP.md` — v1.5 source of the same phase
- `.planning/REQUIREMENTS.md` — KIND-01, KIND-02, KIND-03
- `.planning/PROJECT.md` — v1.5 framing; extras only on practical; Tavily 1000
- `.planning/research/FEATURES.md` — Diátaxis doing vs knowing; honest absence; classifier-gated Tavily
- `.planning/research/PITFALLS.md` — Pitfall 8 (classifier bias toward “helpful” practical; default conceptual on **invalid** output; unattended collect × 5 videos)
- `.planning/research/ARCHITECTURE.md` — `TopicKindClassifier` port sketch; classify then persist then extras; `__all__` stays 10
- `.planning/research/SUMMARY.md` — Phase 30 delivers port + field + persist; prefer separate cheap call; decide call shape in planning

### Prior phase decisions
- `.planning/phases/29-pass-1-richer-templates/29-CONTEXT.md` — pass-1 honesty; no classifier; `## Гайд` must not be added to templates; `## Аудитория` strip stays
- `.planning/milestones/v1.1-phases/08-deepseek-article-templates/08-CONTEXT.md` — D-11 `json_object` `{title,dek,body_markdown}`, D-15 no fail-closed heading validator
- `.planning/milestones/v1.1-phases/09-draft-persist-shortlist-enqueue/09-CONTEXT.md` — unknown/empty `roles` → `employee` (analog for KIND-02 mapping in code)

### Code contracts
- `data-collection/src/data_collection/__init__.py` — `__all__` exactly ten names; pin `tests/unit/test_data_collection_public_api.py` (`PUBLIC_NAMES`, negatives)
- `data-collection/src/data_collection/dto/article_draft.py` — add `topic_kind`; keep audience strip
- `data-collection/src/data_collection/dto/_body.py` — analog for the `## Гайд` strip (`_AUDIENCE_HEADING_RE` / `_NEXT_TOP_HEADING_RE`)
- `data-collection/src/data_collection/dto/material_draft.py` — add `topic_kind`; assembler copies it
- `data-collection/src/data_collection/assemble.py` — `assemble_material_draft` must forward `topic_kind`
- `data-collection/src/data_collection/ports/article_generator.py` — pattern for a new classifier port (do not widen `__all__`)
- `data-collection/src/data_collection/templates/lecture.md` / `podcast.md` — do **not** add «Гайд»; pass-1 frame unchanged
- `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` — inject classifier; extras stay off this phase
- `ingestion-service/src/ingestion_service/domain/errors.py` — `Stage` seven values unchanged
- `ingestion-service/src/ingestion_service/application/ports/persist.py` — `PersistPort.persist(MaterialDraft)`
- `supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql` — current `persist_draft_and_enqueue` (no `topic_kind` yet)
- `supabase-integration/migrations/001_initial_schema.sql` — `materials` table
- `tests/unit/test_article_draft_body_audience.py` — clone this pin style for the Гайд strip
- `tests/unit/test_ingest_pipeline.py` — pipeline spine; extras must stay uncalled for conceptual / default

### Architecture & process
- `.cursor/rules/architecture.mdc` — Ports & Adapters; wiring only in `ingestion-service/composition/`
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — classifier reuses the DeepSeek public-API bend; this phase does not add Tavily

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `strip_audience_section` in `data-collection/src/data_collection/dto/_body.py` — copy the heading-until-next-h1/h2 pattern for exact `## Гайд`; leave in-prose mentions of «гайд» untouched.
- `normalize_roles` / unknown → `employee` — same fail-closed mapping shape as KIND-02 (`topic_kind` invalid → `conceptual`).
- `FakeArticleGenerator` + `ArticleDraft.model_validate` — unit tests stay on scripted JSON; no live DeepSeek in the default suite.
- `DeepSeekArticleGenerator` call shape (`stream=True`, `response_format=json_object`, `thinking.disabled`, `trust_env=False`) — clone for a cheap classifier adapter; do not fold classify into pass-1 messages.
- `assemble_material_draft` — additive field copy; provenance_label stays caller-supplied.
- `PersistPort` / `persist_draft_and_enqueue` — extend the draft DTO and RPC; `ON CONFLICT DO NOTHING` / `already_saved` unchanged.

### Established Patterns
- Ports in `data-collection/ports/`; adapters module-private; composition in `ingestion-service/composition/` only.
- Public `__all__` is a closed ten-name contract with negative-root tests. New ports are imported by the CLI the same way internals already are — **do not** append `TopicKindClassifier`.
- `IngestError.stage` is fail-closed for url/captions/metadata/consistency/llm/llm_truncation/persist. Classifier failure is **not** a new stage: map invalid output to `conceptual` and continue (KIND-02). A classifier transport error should not become `stage=llm`.
- Body sanitizers run in `ArticleDraft` validators, not as a fail-closed heading parser.
- Pass-1 templates still must not mention «Гайд»; Phase 29 pins forbid the old three-block scaffolds.

### Integration Points
- After `ArticleGenerator.process`, before `persist_draft`: classify → stamp `topic_kind` → strip `## Гайд` / placeholder → assemble → persist.
- Pipeline extras (Tavily, enricher, cheat sheet) are **not** wired this phase; tests should prove they are not called. The stored kind is the gate Phase 31/32 will read.
- No backend/SPA changes. No reader DTO. No admin badge.
- If a `materials.topic_kind` column ships, it is a new migration after 013; amend `persist_draft_and_enqueue` rather than editing applied 007–009 in place (Phase 11 precedent).

### Hazards
- D-08 (unsure → `practical` in the prompt) vs KIND-02 (invalid JSON → `conceptual` in code) vs Pitfall 8 (models “helpfully” pick practical). Tests must cover: malformed payload → conceptual; a knowing-job transcript that begs for links/tools → still conceptual; an ambiguous how-to → practical.
- Putting classify into the pass-1 honesty prompt contaminates `## Конкретика` (Pitfall 3) and was rejected by the ROADMAP preference.
- Widening `Stage` or `PUBLIC_NAMES` reds locked pins — amend only with an explicit ROADMAP change, which this phase does not have.
- A fail-closed heading validator would reject a valid conceptual article if `## Гайд` leaked; strip instead, then persist (D-09 / Phase 8 D-15).
- Do not strip `Guide` / `Как сделать` — those can be real chapter titles from the talk (D-12).
- Do not implement Tavily, quota, or enricher “while we're here”.

</code_context>

<specifics>
## Specific Ideas

- Named-product examples the owner listed: Excel, SAP, Tableau, Power BI, Jira, Python, Kubernetes.
- Followable-without-video bar: numbered or checklist steps; «потом открываете SAP и смотрите» is the rejected stub.
- Placeholder to strip: exact «ссылки скоро появятся».
- Heading to strip: exact `## Гайд` (entire section, filled or empty).
- Two-layer default: prompt «если не уверен — practical»; code «если нет валидного enum — conceptual».
- Job-of-the-page examples: theory lecture + one `kubectl apply` demo → conceptual; full product procedure whose job is doing → practical; «как устроен X» + complete sample code → conceptual, sample stays in the article.

</specifics>

<deferred>
## Deferred Ideas

- Tavily / quota / persist-then-enrich — Phase 31.
- Pass-2 guide sections, generated code, live URLs, cheat-sheet files — Phase 32. After D-11, `## Гайд` is allowed to appear only here.
- Reader sources block and cheat-sheet downloads; honest omission of download CTAs — Phase 33.
- Operator `--debug` classifier / quota / URL counts — Phase 34.
- Classifier input (transcript vs title+dek vs pass-1 article) — not deferred; Claude's Discretion above.
- Reader-facing classifier badge / ADUX-14 quiet admin note — still out of v1.5.
- None of the above were folded from todos (`todo.match-phase 30` was empty).

</deferred>

---

*Phase: 30-Classifier practical | conceptual*
*Context gathered: 2026-10-28*
