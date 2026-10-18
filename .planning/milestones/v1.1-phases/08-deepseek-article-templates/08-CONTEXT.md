# Phase 8: DeepSeek Article & Templates - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Operator-facing article draft from a transcript: a DeepSeek adapter (OpenAI-compatible SDK) implements `ArticleGenerator` and returns a validated `ArticleDraft` (`title`, `dek`, `body_markdown`) for `TemplateKind` lecture or podcast. Repository markdown templates supply the section outline. LLM failures and an oversized transcript fail closed with the locked stages and reasons, no partial draft, and no database writes (persist is Phase 9). This phase does not build the Typer one-shot (Phase 10), does not append `provenance_label` (Phase 10 caller; Phase 6 assembler copies it), and does not add a new `IngestError` stage.

</domain>

<decisions>
## Implementation Decisions

### Output language
- **D-01:** Output is always Russian. Supersedes REQUIREMENTS.md / ROADMAP wording "output language matches the transcript language" (updated 2026-09-27 in `.planning/REQUIREMENTS.md` LLM-04 and `.planning/ROADMAP.md` Phase 8 criterion 4). — **Reversibility:** costly — Phase 10 UAT and the provenance marker assume Russian drafts; restoring "match transcript" rewrites the prompt contract and those checks.
- **D-02:** `ru` transcript: format only, do not translate. `en` transcript: translate to Russian. Preserve technical terms, proper names, library names, numbers, and units as written (tests keep `pgvector` / `RAG` / `embedding` unchanged).
- **D-03:** No runtime language detector. Wrong-language drafts are caught in admin preview (Phase 5), not by a heuristic fail-closed check. Fail-closed stays limited to clear-cut cases (network, HTTP errors, invalid JSON, schema validation, context budget).
- **D-04:** Phase 8 tests both paths: `ru` format-only with terms preserved; `en` translated to Russian with terms preserved. Tests assert the prompt rules and scripted drafts, not a language-ID of the reply.
- **D-05:** Phase 8 locks the marker string only. Phase 10 caller builds `label = f"YouTube · {metadata.author}"` and, when `transcript.language != "ru"`, appends ` · пер. с англ.` (middot separator, trailing period). Example: `YouTube · Сбер Pro · пер. с англ.` The Phase 6 assembler copies `provenance_label` as-is and does not invent it. — **Reversibility:** costly — the string is the operator-visible provenance contract once Phase 10 persists it.
- **D-06:** v1.1 marker map is English only. The only non-`ru` suffix is ` · пер. с англ.` Phase 7 only emits `ru` or `en`.

### Context budget
- **D-07:** Character cap on `Transcript.text` only. `MAX_TRANSCRIPT_CHARS` defaults to `80000` and is env-configurable. Unset or blank uses `80000`. A non-integer, zero, or negative value fails when settings load, before any video (config error, not `llm_truncation`). — **Reversibility:** reversible — the default and env name are local operator config.
- **D-08:** Before any DeepSeek call, `len(transcript.text) > MAX_TRANSCRIPT_CHARS` raises `IngestError(stage="llm_truncation")`. Template text and the system prompt do not count. No tokenizer. No silent truncation. No chunking.
- **D-09:** Local cap reason is `transcript_too_long`. Context is only `char_count` and `max_chars`. No transcript text in the error.
- **D-10:** If DeepSeek itself rejects the request for context length, that is `stage=llm`, `reason=provider_context_length`, not `llm_truncation`. — **Reversibility:** costly — `reason` joins the operator diagnostic contract shared with Phases 7–10.

### Model reply
- **D-11:** The model returns one JSON object: `{"title","dek","body_markdown"}`. Request it with `response_format={"type":"json_object"}`. Parse with `json.loads`, then `ArticleDraft`. Extra keys are ignored. Markdown fences or surrounding prose are `invalid_json` — do not strip fences and do not extract the first `{...}`. Markdown inside `body_markdown` is article content, not the response format. — **Reversibility:** costly — `ArticleDraft` and LLM-03 tests depend on this object shape.
- **D-12:** `ArticleGenerator.process` returns `ArticleDraft` only. Provenance stays out of the JSON and out of the adapter (Phase 6 D-06). LLM-01's "validated MaterialDraft" is the existing assembler plus the Phase 10 label, not fields the model emits.
- **D-13:** `stage=llm` reason set: `network_error` (timeout, DNS, connection refused — before a DeepSeek response), `provider_error` (HTTP 5xx and 429), `auth_error` (HTTP 401 and 403), `invalid_json` (`json.loads` fails, or JSON is not an object), `invalid_article_draft` (`ArticleDraft` fails: missing or blank field), `provider_context_length`, `unknown_llm_error` (anything else). SDK exception class names stay out of `reason`. No partial `ArticleDraft`. No transcript text in context. — **Reversibility:** costly — same operator JSON contract as the captions reason set.

### Lecture vs podcast
- **D-14:** Templates differ only by section outline. Shared system prompt (honesty, always-Russian, preserve terms), shared neutral editorial voice, shared JSON contract, shared failure reasons. Lecture: thesis → argument → takeaway. Podcast: what it was about → positions → takeaways. A looser podcast voice is out of v1.1.
- **D-15:** Do not validate headings inside `body_markdown`. The adapter validates only the three non-blank `ArticleDraft` strings. Tests assert the prompt contains the chosen template's heading strings. Phase 10 UAT: the operator confirms headings in preview.
- **D-16:** Heading strings are Russian. `lecture.md`: `## Тезис`, `## Ход рассуждения`, `## Вывод`. `podcast.md`: `## О чём разговор`, `## Позиции`, `## Что запомнить`. Instructions around those headings may be English. The heading strings themselves are the output the model is told to use.
- **D-17:** If `lecture.md` or `podcast.md` is missing or unreadable, fail at load, before any video and before any DeepSeek call. Do not add an `IngestError` stage. Same class of failure as an invalid `MAX_TRANSCRIPT_CHARS`.

### Claude's Discretion
- Package path for `lecture.md` and `podcast.md`, as long as both are repository markdown, both are loaded before any video, and a missing file fails at load (D-17).
- Where the character-cap check lives, as long as it runs before the SDK call, the limit is injected (adapters do not read `os.environ`), and composition/`Settings` owns `MAX_TRANSCRIPT_CHARS`.
- How the SDK error is recognized as `provider_context_length`, `auth_error`, or `provider_error`, as long as the locked reason codes are what operators see.
- Diagnostic `message` wording. Prefer the captions pattern (English, reason in the message, no transcript body).
- Context keys on `stage=llm` errors other than D-09's pair, except never include transcript text or a response body that echoes the prompt.
- Exact English instruction prose inside the template files, as long as D-16 heading strings are present unchanged.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 8 goal and success criteria (criterion 4 updated: always Russian); Phase 9 persist; Phase 10 UAT includes at least one English source video
- `.planning/REQUIREMENTS.md` — LLM-01…LLM-05 (LLM-04 updated: always Russian; "match the transcript" superseded); CLI-03 UAT includes one English source video
- `.planning/PROJECT.md` — v1.1 ingestion; DeepSeek MVP bend of ADR-0002; material = prepared article
- `.planning/phases/06-ports-dtos/06-CONTEXT.md` — `ArticleDraft` vs `MaterialDraft`, assembler does not invent `provenance_label`, `TemplateKind`, `ArticleGenerator.process`
- `.planning/phases/07-captions-adapter/07-CONTEXT.md` — `IngestError` stages including `llm` and `llm_truncation`; adapters do not read `os.environ`; diagnostic envelope
- `CONTEXT.md` — glossary: material = prepared article; transcript is not a material

### Research (v1.1 ingestion)
- `.planning/research/STACK.md` — official `openai` SDK, DeepSeek `base_url`, model `deepseek-flash` via env, template files
- `.planning/research/SUMMARY.md` — captions → DeepSeek → draft; backend/SPA stay readers
- `.planning/research/ARCHITECTURE.md` — DeepSeek adapter in `data-collection`; thin ingestion composition
- `.planning/research/FEATURES.md` — lecture vs podcast templates; СВА editorial article, not a blog recap
- `.planning/research/PITFALLS.md` — do not log full captions or API keys; explicit HTTP timeouts

### Architecture & ops
- `.cursor/rules/architecture.mdc` — Ports & Adapters; composition injects clients
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — FoundryModels long-term; DeepSeek is the temporary bend

### Code contracts
- `data-collection/src/data_collection/ports/article_generator.py` — `process(transcript, template) -> ArticleDraft`
- `data-collection/src/data_collection/dto/article_draft.py` — non-blank `title`, `dek`, `body_markdown`
- `data-collection/src/data_collection/dto/template_kind.py` — `lecture` | `podcast`
- `data-collection/src/data_collection/tests_support/fakes.py` — extend `FakeArticleGenerator` with failure scripts; do not export fakes from the package root
- `ingestion-service/src/ingestion_service/domain/errors.py` — `IngestError` stages; do not add a stage
- `ingestion-service/src/ingestion_service/composition/settings.py` — env is read here; add `MAX_TRANSCRIPT_CHARS` the same way
- `ingestion-service/src/ingestion_service/mapping/captions.py` — pattern for locked `reason` codes and context allowlists

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ArticleGenerator` protocol and `ArticleDraft` / `TemplateKind` from Phase 6 — DeepSeek adapter implements the port; it does not grow provenance fields
- `FakeArticleGenerator` call spy — Phase 6 D-17 said Phase 8 adds failure scripts on the same fake
- `IngestError.to_dict()` envelope (`ok`, `stage`, `reason`, `message`, `context`, `exit_code`) and captions/metadata mappers
- `ingestion_service.composition.Settings` — inject the char cap and the DeepSeek client; adapters stay free of `os.environ`

### Established Patterns
- Public `data-collection` exports types and ports; fakes stay in `tests_support`
- Unit tests under `tests/unit/` with TDD; no network in the default suite
- Adapter maps SDK/HTTP errors at the boundary into module-local errors; ingestion mapping turns those into `IngestError`
- Captions messages are English and include the `reason`, not the payload

### Integration Points
- Phase 9 persists `MaterialDraft` (`status=draft`) and proves live zero-row behavior on failure
- Phase 10 Typer `--template lecture|podcast` wires the generator, builds `provenance_label` (D-05), prints staged progress, and runs UAT (one English video among 3–5; operator checks headings in preview)
- Phase 6 assembler already copies a caller-supplied label; Phase 8 does not change it

</code_context>

<specifics>
## Specific Ideas

- Marker example: `YouTube · Сбер Pro · пер. с англ.`
- Preserved tokens in tests: `pgvector`, `RAG`, `embedding`.
- `MAX_TRANSCRIPT_CHARS=80000` is about a 2.5× margin versus a 64k-token window if one char is treated as a fraction of a token; the check itself is `len(transcript.text)`, not a tokenizer.
- Lecture headings: `## Тезис`, `## Ход рассуждения`, `## Вывод`.
- Podcast headings: `## О чём разговор`, `## Позиции`, `## Что запомнить`.

</specifics>

<deferred>
## Deferred Ideas

- Per-language translation marker beyond `en` (wait until captions accept more languages)
- Looser podcast voice (v1.2+). v1.1 keeps one neutral editorial voice
- Heading checks inside `body_markdown` (fix the prompt if the model drops headings; do not add a validator)
- Runtime language detection of the model reply
- Chunking / silent truncation of long transcripts
- Typer one-shot, provenance assembly at the CLI, and live UAT — Phase 10
- Persist, shortlist, and live zero-row proof — Phase 9

</deferred>

---

*Phase: 8-DeepSeek Article & Templates*
*Context gathered: 2026-09-27*
