# Phase 29: Pass-1 richer templates - Research

**Researched:** 2026-10-26
**Domain:** LLM prompt contract for transcript-grounded Russian longform (`data-collection` DeepSeek adapter + package markdown templates)
**Confidence:** HIGH on the code/test contract (every claim read from source this session); MEDIUM on DeepSeek runtime behaviour (official docs); LOW on general prompt craft (web, cross-checked only)

## Summary

Phase 29 is a **prompt-and-test rewrite**, not a feature build. The production surface is two markdown files (`lecture.md` 17 lines, `podcast.md` 17 lines) plus, optionally, the shared `ARTICLE_SYSTEM_PROMPT` string. The adapter's call shape (`stream=True`, `response_format={"type":"json_object"}`, `thinking: disabled`, `trust_env=False`, `max_retries=0`), the DTO (`title`/`dek`/`body_markdown`/`roles`), the `## Аудитория` strip, the error taxonomy and the persist path must all stay byte-identical. The real work is (a) authoring a prompt frame that actually produces the D-01…D-18 behaviour, and (b) flipping the existing heading pins from "contains the scaffold" to "forbids the scaffold and asserts the new frame" **without** deleting the negative coverage.

Three findings drive planning more than anything else in this document. First, the old scaffold tokens must never appear in the new prompt text — not even inside a prohibition — because the existing cross-kind tests already pin `assert "## О чём разговор" not in user_content` (`tests/unit/test_deepseek_article_adapter.py:126`) and the new ART-01 pin will do the same for all six old headings; naming a forbidden heading is also the classic way to make a model emit it. Second, **richer output has a real, quantified truncation ceiling**: Phase 28 measured `response_chars=10314` for a 20,923-char Russian transcript, the adapter sets no `max_tokens`, DeepSeek's default is 8K completion tokens in non-thinking mode, and a cut stream is *not* mapped to `llm_truncation` — it lands as `invalid_json` on `stage=llm` and no draft is persisted. Third, D-04's bold/`>` promise is only half-real on the reader surface: `strong` renders bold, but Tailwind preflight zeroes `blockquote` margins/padding/border and `MaterialPage`'s prose column declares no `[&_blockquote]` or `[&_table]` utility, so quotes and tables are structurally correct but visually flat.

**Primary recommendation:** Rewrite both templates as a *positive* editorial frame (content-shaped `##` by the talk's own topics → optional `## Конкретика` → optional `## Зачем это СВА`, no rigid order, `## Аудитория` strictly last), move the shared voice prohibitions into `ARTICLE_SYSTEM_PROMPT`, add an explicit length band to keep output inside the 8K completion budget, and drive the whole change with red-first rewrites of `tests/unit/test_article_templates.py` + the two prompt-isolation tests in `tests/unit/test_deepseek_article_adapter.py`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Content-shaped `##`
- **D-01:** Free `##` named after the talk's real topics/chapters. No fixed section count and no three-block skeleton. — **Reversibility:** costly — `tests/unit/test_article_templates.py` and `test_deepseek_article_adapter.py` pin the old heading strings (`## Тезис` / `## Ход рассуждения` / `## Вывод`, `## О чём разговор` / `## Позиции` / `## Что запомнить`); those pins must be rewritten to *forbid* the scaffolds and to assert the new prompt frame. Phase 8 D-16 is superseded.
- **D-02:** If the talk has no explicit chapters, split into several *implicit* editorial chapters the way an experienced editor would — do not invent a fake «Глава 1 / Глава 2» that is not in the transcript, and do not fall back to one dump section named «Содержание доклада».
- **D-03:** Authorial voice of the edition, not a recap. Forbidden phrasing: «в подкасте рассказывается», «монолог содержит», «в ролике говорится». Attribution of the speaker is allowed: «Элен считает…».
- **D-04:** Key theses in `**bold**`. Direct speech of the speaker as a markdown blockquote (`>`). Do not promise color or HTML — `rehype-sanitize` will strip it.
- **D-05:** Lecture: sections by topic only. Podcast: when it is a dialogue, sections by positions/speakers; otherwise by topic. Templates still share the honesty prompt and JSON contract (Phase 8 D-14); they differ by this one kind hint.

#### `## Конкретика` (source-facts layer)
- **D-06:** The dedicated facts block is headed `## Конкретика`, not «Факты из источника». Same string in lecture and podcast so Phase 32 can freeze it. Reader-facing editorial label; the contract is unchanged: names, numbers, tools, caveats from the transcript only.
- **D-07:** Bulleted list by default (`**item** — short caveat from the transcript`). A GFM table is allowed only when the talk itself has an explicit grid of numbers.
- **D-08:** Omit `## Конкретика` entirely when there is nothing to put in it. No empty heading, no «в транскрипте нет цифр» stub. ART-02 is read as «the block exists when there is concreteness», not as a mandatory placeholder.
- **D-09:** Normalize tool names to a canonical form (PostgreSQL, not «постгрес»). Do not invent version numbers. Do not build a reader sources block here (Phase 33).

#### СВА takeaway
- **D-10:** One body section only: `## Зачем это СВА`. There is no second heading «Риски и ограничения» / «Что учесть СВА» — that was duplication. Residual caution, when it belongs, lives inside this section's prose.
- **D-11:** Omit `## Зачем это СВА` when there is no concrete applicability. ART-03 «always present even if the talk barely mentioned audit» is owner-overridden: do not hide the takeaway when it exists; do not force a section on a talk with no analog.
- **D-12:** Write the section when there is a working analog for СВА — control, data, model, vendor, information security, process quality — even if the speaker never said «аудит».
- **D-13:** No rigid section order. The prompt gives a unified style frame; the model may compose freely (content-shaped `##`, `## Конкретика` when present, `## Зачем это СВА` when present). Do not encode a skeleton «середина → конкретика → СВА».
- **D-14:** When the section is present, it is a free editorial paragraph in that style — not a checklist «зачем + риск».
- **D-15:** Voice of the edition, no meta-banner: «Для СВА это значит…», never «спикер доказал, что аудиту нужно…». Quote the speaker only in `>`.
- **D-16:** Do not invent a СВА duty, an internal standard, or numbers in this section. Analogy and «стоит смотреть» are allowed; «уже требуется по политике N» is forbidden unless it is in the transcript.
- **D-17:** `dek` is always the 1–2 sentence hook about the talk. It is not a substitute for `## Зачем это СВА`. If the section is omitted, the article has no separate audit takeaway — do not smuggle it into `dek`.

#### Honesty vs inference (pass-1)
- **D-18:** Pass-1 user message stays transcript-only. Editorial inference is allowed *only* in `## Зачем это СВА` (and in implicit chaptering / authorial voice). `## Конкретика` must not be rewritten from opinion or from the web.
- **D-19:** Expanding a thin talk from other sources is **out**. That is Phase 32 pass-2 Tavily, not this template rewrite.

### Claude's Discretion
- Exact English (or Russian) instruction prose inside `lecture.md` / `podcast.md`, as long as D-01…D-18 hold and the old scaffold heading strings are absent.
- Canonical-name dictionary for D-09 (PostgreSQL, Kubernetes, …) — a short prompt rule, not a shipped gazetteer, unless a test needs one or two pinned examples.
- Whether tests pin prompt *instructions* for `## Конкретика` / `## Зачем это СВА` as optional («include when…») versus asserting they always appear in scripted `body_markdown`. Prefer prompt pins + absence of old scaffolds; do not add a fail-closed heading parser (Phase 8 D-15).
- How `ARTICLE_SYSTEM_PROMPT` is tightened (authorial voice, no recap phrasing) versus putting those lines only in the template files — shared prompt still covers honesty, always-Russian, preserve-terms, JSON keys.
- `dek` wording when `## Зачем это СВА` is omitted (user chose «You decide» on D-17): keep it a topic hook, never an audit dump.

### Deferred Ideas (OUT OF SCOPE)
- Enrich / expand a thin talk from other sources when implicit chapters are hard — Phase 32 pass-2 Tavily, not pass-1 templates.
- Reader sources block for transcript URLs — Phase 33.
- Color highlighting of key thoughts — not in this stack (`rehype-sanitize`); do not add a highlight widget in v1.5.
- Runtime validation that `body_markdown` contains `## Конкретика` / `## Зачем это СВА` — still out (Phase 8 D-15); honest omit makes a required-heading parser wrong.
- Classifier `practical | conceptual` — Phase 30.
</user_constraints>

## Project Constraints (from .cursor/rules/)

Directives extracted from `.cursor/rules/` + `AGENTS.md`. They carry the same authority as the locked decisions above; a plan that contradicts them is wrong even if it satisfies a success criterion.

| Directive | Source | Consequence for Phase 29 |
|-----------|--------|--------------------------|
| **Mandatory Red–Green–Refactor.** No production code without a failing test first; exceptions only for config/generated/one-off files and only with explicit agreement. | `.cursor/rules/tdd.mdc`, `AGENTS.md` | The two `.md` files are **production prompt content**, not config. Write the failing assertions in `test_article_templates.py` / `test_deepseek_article_adapter.py` first, run them, observe the expected failure, then edit the templates. Never edit the templates and then write tests. |
| **Ports & Adapters.** Dependencies point inward; no `supabase`/`httpx`/`fastapi`/raw SQL in domain or use cases; wiring only in `composition/`; no `Any` on ports or module boundaries. | `.cursor/rules/architecture.mdc` | Phase 29 adds **no port, no adapter, no use case, no wiring**. Prompt text lives in the `data-collection` templates and (optionally) the adapter's `ARTICLE_SYSTEM_PROMPT`. A plan task that touches `composition/`, `backend/` or the `ArticleGenerator` protocol is out of bounds. |
| **`uv` owns Python deps.** Add/remove packages through `uv`. | `.cursor/rules/python-uv.mdc` | No dependency change at all this phase; `pyproject.toml` / `uv.lock` must show zero diff. |
| **Use Context7 for library/API docs.** | `.cursor/rules/context7.mdc` | Followed here: the DeepSeek `json_object` / `max_tokens` / empty-content facts come from Context7's `/websites/api-docs_deepseek` (see Sources). Future tasks touching the API contract should do the same rather than guess. |
| **Single-context domain docs:** `CONTEXT.md` + `docs/adr/` at repo root; issues live under `.scratch/`. | `AGENTS.md` | `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` still governs the "DeepSeek is the temporary public-API bend" framing; this phase adds no new ADR. |
| **Git: `origin` operations (push/pull/fetch/auth) only via WSL** (`wsl.exe`), not PowerShell. Local commits are allowed on `dev`. | `AGENTS.md` | Research/plan commits are local. If a ship step needs `origin`, use WSL. |
| **User-facing prose in Russian.** | `AGENTS.md` / `.planning/config.json` `response_language: russian` | Commit messages/plans may be English; anything the owner reads in chat is Russian. Prompt content itself is English instructions + Russian heading literals (Phase 8 D-16 precedent). |
| **Project skills.** `.agents/skills/` contains `hallmark`, `supabase`, `supabase-postgres-best-practices`; `.cursor/skills/` does not exist. | skills scan | None of them apply to a prompt-text rewrite — no skill needs loading for this phase. Do not invent a skill dependency. |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ART-01 | A newly ingested material is a Russian longread whose `##` headings follow the source talk, not the three-block lecture scaffold or the podcast trio | Prompt frame pattern (Pattern 1/2 below) + the "old scaffold must never appear in prompt text" rule + red-first rewrite of the four existing heading pins (`test_article_templates.py:16-18,24-26,35-36`; `test_deepseek_article_adapter.py:123-126,147-150`). Live proof is the only way to observe the produced headings. |
| ART-02 | The article contains a dedicated source-facts block (names, numbers, tools, caveats) from the transcript only — no invented numbers, names, or tool versions | `## Конкретика` clause in the template (D-06/D-07/D-08/D-09) + the transcript-only honesty line already present in `ARTICLE_SYSTEM_PROMPT:37` and in both templates (`lecture.md:8`, `podcast.md:8`). Omit-when-empty is a prompt rule, deliberately **not** a parser (Phase 8 D-15). Verification is a manual digit audit against the transcript. |
| ART-03 | The article contains an explicit «Зачем это СВА» (owner-overridden to "present when an analog exists") and `dek` stays the 1–2 sentence hook | `## Зачем это СВА` clause with the analog bar (D-12), the no-invented-duty rule (D-16), the omit rule (D-11), and the `dek` boundary (D-17). The existing system prompt is the right home for the shared "voice of the edition / never attribute editorial inference to the speaker" rule (D-03/D-15). |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Section-structure instruction (free `##` by the talk's topics) | `data-collection` package markdown (`templates/lecture.md`, `templates/podcast.md`) | — | It is prompt text, owned by the adapter that assembles the message (`build_article_messages`, `deepseek_article.py:46-62`). No application-layer logic. |
| Editorial voice / attribution / honesty rules | `data-collection` `ARTICLE_SYSTEM_PROMPT` (`deepseek_article.py:35-43`) | — | Shared by both kinds (Phase 8 D-14); putting voice rules here avoids duplicating them in two files and keeps kind isolation clean. |
| Prompt assembly (template + language + transcript) | `data-collection` adapter | `ingestion-service` composition | `build_article_messages` is unchanged; composition only loads the files (`clients.build_deepseek_article_generator`). |
| Fail-closed budget/JSON/error taxonomy | `ingestion-service` mapping + `data-collection` errors | — | `stage=llm` / `llm_truncation` unchanged (locked scope fact). Phase 29 must not touch this tier. |
| `## Аудитория` scaffolding removal | `data-collection` DTO validator (`dto/_body.py`, `dto/article_draft.py`) | — | Already shipped and tested; Phase 29 must keep the heading last in both files so the strip stays correct. |
| Heading rendering + reader TOC | `web` (`MaterialPage.jsx`, `utils/markdownToc.js`) | — | Real `##` in `body_markdown` become the TOC for free. No SPA work is in scope; the only consequence is that `## Конкретика` / `## Зачем это СВА` appear as TOC entries (acceptable, not a defect). |
| Persist draft + shortlist | `supabase-integration` / `ingestion-service` use case | — | Unchanged. No migration, no DTO field. |

## Standard Stack

**No new packages.** This phase changes markdown prompt text (and possibly one Python string constant). Everything below is already installed and locked.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `openai` (Python SDK) | 3.19.2 `[VERIFIED: uv.lock:917-919]` | DeepSeek's OpenAI-compatible chat client | Already the only LLM transport; `openai>=3.0,<4` pinned in `data-collection/pyproject.toml:11`. Phase 29 must not change how it is called. |
| `pydantic` | 2.13.5 `[VERIFIED: uv.lock:1087-1089]` | `ArticleDraft` validation (three non-blank strings + roles) | The draft contract is the only "output schema" enforcement; heading presence is deliberately not validated (Phase 8 D-15). |
| DeepSeek API `deepseek-flash` | model pin `Settings.deepseek_model = "deepseek-flash"` `[VERIFIED: ingestion-service/.../settings.py:88-89]` | Article generation | `thinking: disabled`, `response_format=json_object`, `stream=True` — all locked by the adapter. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `importlib.resources` (stdlib) | Python 3.12.13 `[VERIFIED: .venv]` | Loads `templates/*.md` as package data | Already used by `load_article_templates`; tests use the same call. |
| `pytest` | `>=8.3.0` `[VERIFIED: pyproject.toml:31]` | Unit suite (`testpaths = ["tests/unit"]`) | The only automated gate for this phase. |
| `react-markdown` + `remark-gfm` + `rehype-slug` + `rehype-sanitize` | installed in `web/` | Reader rendering of the produced markdown | Read-only dependency: it constrains what the prompt may promise (bold/quote/table), not something to change. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Prompt-only frame in `templates/*.md` | Structured JSON outline field (`sections: [...]`) in the draft | Would require a new DTO field, adapter validation and a migration of the persist path — all explicitly out of scope, and it would re-introduce a heading validator (Phase 8 D-15). |
| Prompt-only length guidance | Explicit `max_tokens` on the completion call | `max_tokens` is the robust fix for output truncation, but it is a call-shape change to a locked surface ("Pass-1 still streams `json_object`; call shape unchanged"). Keep it as an escalation (Open Question Q1). |
| Shared honour rules in `ARTICLE_SYSTEM_PROMPT` | Duplicating voice rules in both templates | Duplication drifts and doubles the prompt-token cost for no benefit; the two files should differ only by the kind hint (D-05). |

**Installation:**
```bash
# none — no dependency changes in this phase
```

**Version verification:** `uv.lock` read this session (`openai 3.19.2`, `pydantic 2.13.5`, `youtube-transcript-api 1.2.4`); `uv --version` → `uv 0.10.9`; `node --version` → `v24.21.0`; `.venv` Python → `3.12.13`.

## Package Legitimacy Audit

**No packages are installed by this phase.** The change surface is two markdown files (and at most one Python string constant). Nothing was added to `pyproject.toml` or `uv.lock`, so the legitimacy gate has no rows to evaluate.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — (none) | — | — | — | — | — | No install in Phase 29 |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```
ingestion-service/.env
  DEEPSEEK_API_KEY · DEEPSEEK_MODEL=deepseek-flash · MAX_TRANSCRIPT_CHARS=80000
        │
        ▼
composition/clients.build_deepseek_article_generator(settings)
  ├─ load_article_templates(importlib.resources.files("data_collection.templates"))
  │     lecture.md ─┐                                    ◄── CHANGED (prompt text only)
  │     podcast.md ─┘
  └─ AsyncOpenAI(trust_env=False, max_retries=0)
        │
        ▼
run_ingest_pipeline ── captions ──► Transcript(text, language, video_id)
        │
        ▼
DeepSeekArticleGenerator.process(transcript, template)
  ├─ ① budget guard  len(transcript.text) > MAX_TRANSCRIPT_CHARS
  │        └─ ArticleBudgetError ──► stage=llm_truncation  (UNCHANGED; template size is exempt)
  ├─ ② build_article_messages
  │        system : ARTICLE_SYSTEM_PROMPT  (honesty · always-Russian · preserve terms · json keys)
  │        user   : <template.md> + "Transcript language: ru|en" + <transcript.text>   ◄── CHANGED
  ├─ ③ POST /chat/completions  stream=True · response_format=json_object · thinking=disabled
  ├─ ④ join deltas → json.loads → ArticleDraft(title, dek, body_markdown, roles)
  │        └─ empty / truncated / non-JSON ──► ArticleInvalidJson ──► stage=llm  (FAIL-CLOSED)
  ▼
persist_draft_and_enqueue ──► materials(status=draft) + digest_shortlist_items(pending)
        │
        ▼
Reader (web/src/pages/MaterialPage.jsx)
  title → <h1> ; dek → <p> ; body_markdown → react-markdown(remark-gfm, rehype-slug, rehype-sanitize)
  extractMarkdownHeadings(body_markdown) → SectionToc   (free real-world TOC, no work needed)
```

The only two editable nodes are ② (`template.md` files and optionally `ARTICLE_SYSTEM_PROMPT`). Everything downstream of ③ is a constraint, not a build target.

### Recommended Project Structure

No structural change. Files touched:

```
data-collection/src/data_collection/
├── templates/
│   ├── lecture.md          # rewrite (17 lines today)
│   └── podcast.md          # rewrite (17 lines today)
└── adapters/
    └── deepseek_article.py # optional: ARTICLE_SYSTEM_PROMPT only (lines 35-43)

tests/unit/
├── test_article_templates.py        # flip heading pins → forbid scaffold + assert frame
├── test_deepseek_article_adapter.py # rewrite the two prompt-isolation tests
└── test_article_draft_body_audience.py  # +1 case: strip works with the new headings present
```

### Pattern 1: Positive frame, not a prohibition list

**What:** Describe the target shape affirmatively ("name sections after the talk's own topics; use as many as the talk has") and never spell the six old heading literals anywhere in any prompt string.
**When to use:** Always, for the heading scaffolds. Forbidden *style phrases* (D-03) are the opposite case: name those with examples, in the shared system prompt.
**Why:** Two independent reasons. (a) Mechanical: the existing and new tests assert absence — `assert "## О чём разговор" not in user_content` `[VERIFIED: tests/unit/test_deepseek_article_adapter.py:126]` and `assert "## Тезис" not in user_content` `[VERIFIED: tests/unit/test_deepseek_article_adapter.py:150]`; a prohibition would make those pins permanently red or force their deletion (losing the coverage CONTEXT explicitly says to keep). (b) Behavioural: naming a token in a negation raises its emission probability; describing the target shape positively is the safer instruction design.

```markdown
<!-- Shape of the lecture template (English instructions, Russian heading literals) -->
Write a Russian longread for СВА readers from the transcript below.
Use only what the transcript says; do not add facts, names, numbers, tools, or versions that are not in it.

Structure
- Choose level-2 sections that follow the talk's own topics. The number of sections is
  whatever the talk actually contains; do not pad and do not merge unrelated topics.
- When the talk has no named chapters, split it into the implicit editorial chapters an
  experienced editor would write. Name each section by its topic in the speaker's terms.
- Write in the voice of the edition. Attribute a claim to the speaker by name when it is
  theirs; do not report the container.
- Mark key theses in **bold**. Give memorable direct speech as a markdown blockquote.
- Do not open with a level-1 heading; the title is a separate field.

`## Конкретика`
Add this section only when the transcript carries concrete names, numbers, tools or
caveats worth keeping. Bullets: `**item** — the caveat the speaker gave`. A table is
allowed only when the talk itself presents a grid of numbers. Spell tool names
canonically (PostgreSQL, not «постгрес»); never invent a version. Omit the section
entirely when there is nothing concrete — no placeholder.

`## Зачем это СВА`
Add this section only when the talk has a working analog for СВА — control, data, model,
vendor, information security, process quality — even if the speaker never said «аудит».
Write one editorial paragraph in the edition's voice. Do not invent a duty, an internal
standard or a number, and do not present editorial inference as the speaker's claim.
Omit the section when there is no such analog.

`## Аудитория`
Кто целевая аудитория материала? Верни JSON array ролей из: employee, analyst, ds.
```

### Pattern 2: One kind hint, shared everything else

**What:** `lecture.md` and `podcast.md` share the honesty line, the `## Конкретика` clause, the `## Зачем это СВА` clause and the trailing `## Аудитория` block; they differ **only** in the Structure paragraph.
**When to use:** Both files. Lecture: topics only. Podcast: positions/speakers when it is a dialogue, otherwise topics.
**Why:** Phase 8 D-14 (shared system prompt + JSON contract) plus D-05 (one kind hint). It also keeps the cross-kind test meaningful: the discriminator is the kind hint, **not** `## Конкретика` / `## Зачем это СВА`, which are shared by design and must not be used in `assert ... not in ...` cross-kind pins.

```python
# Shape of the kind-isolation test (rewrite of test_deepseek_article_adapter.py:105-150)
assert "## Конкретика" in both_user_messages          # shared
assert "## Зачем это СВА" in both_user_messages       # shared
assert "## Аудитория" in both_user_messages           # shared scaffolding, must stay last
forbidden = ("## Тезис", "## Ход рассуждения", "## Вывод",
             "## О чём разговор", "## Позиции", "## Что запомнить")
for heading in forbidden:                              # ART-01, both kinds
    assert heading not in lecture_user_message
    assert heading not in podcast_user_message
assert PODCAST_KIND_HINT in podcast_user_message       # "positions"/"speakers"
assert PODCAST_KIND_HINT not in lecture_user_message
```

### Pattern 3: Two-level assertion surface (prompt pins + scripted bodies)

**What:** Unit tests pin the **prompt** (frame strings present, scaffold strings absent) and separately pin the **pass-through** behaviour with scripted JSON bodies (`FakeArticleGenerator` / stub clients).
**When to use:** Always in this phase. Never assert that a scripted body "has the right headings" — that only tests the fixture.
**Why:** The adapter validates only non-blank strings (`ArticleDraft.model_fields == {title, dek, body_markdown, roles}` `[VERIFIED: tests/unit/test_article_draft_internal.py:18]`), and `test_body_without_headings_is_valid_when_strings_non_blank` already pins that a heading-less body is accepted. Adding body-heading assertions would re-introduce the runtime heading validator that Phase 8 D-15 forbids.

### Anti-Patterns to Avoid
- **Naming the old scaffolds in the new prompt** (even as "do not use"): breaks the negative pins and invites emission. Describe the target, not the defect.
- **Pinning full template sentences or a byte digest of the template files**: CONTEXT grants "exact prose" discretion; a digest turns every wording tweak into a test edit. Pin frame strings + absence, not prose.
- **A required-heading parser in the adapter**: D-08/D-11 make `## Конкретика` and `## Зачем это СВА` legitimately absent; a "must contain" check would fail honest articles. Phase 8 D-15 stands.
- **Moving `## Аудитория` off the last line**: `strip_audience_section` removes from that heading to the next h1/h2 `[VERIFIED: data-collection/.../dto/_body.py:17-41]`; appending new sections after it would leak the scaffolding instruction into the reader body.
- **Instructing an H1 in `body_markdown`**: the page already renders `material.title` as its `h1` `[VERIFIED: web/src/pages/MaterialPage.jsx:212]`, and `extractMarkdownHeadings` includes level 1 `[VERIFIED: web/src/utils/markdownToc.js:47-76]`, so a model-chosen `# ` duplicates the title and pollutes the TOC.
- **Adding URLs/link instructions to pass 1**: Phase 32/33 own links; `rehype-sanitize` would keep an `<a>` whose protocol is allowlisted (`href: ['http','https','irc','ircs','mailto','xmpp']` `[VERIFIED: web/node_modules/hast-util-sanitize/lib/schema.js:141-146]`), so sanitizing is not provenance control (Pitfall 3 in `.planning/research/PITFALLS.md`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Enforcing that the article contains `## Конкретика` / `## Зачем это СВА` | A regex heading validator in the adapter or a new error reason | Prompt instruction + human review | D-08/D-11 make those headings legitimately absent; a parser would reject honest output (Phase 8 D-15, locked). |
| Keeping facts honest | A number/name extractor or NLI checker | The transcript-only honesty line already in the system prompt + a manual digit audit in UAT | v1.5's bar is a liveness/honesty allowlist, not claim-level verification (explicitly an anti-feature in `.planning/research/FEATURES.md`). |
| Canonical tool names (D-09) | A shipped gazetteer / dictionary module | One prompt sentence with two or three examples | CONTEXT discretion: "a short prompt rule, not a shipped gazetteer". |
| Detecting "recap" prose after the fact | A post-filter or a second LLM judge | Prompt instruction with the owner's exact forbidden phrases | Brittle false positives on legitimate prose; no failure taxonomy exists for it. |
| Making quotes/tables look distinct | A custom markdown renderer or a highlight widget | Nothing in this phase (bullets are already the default); if ever needed, one utility class on the existing `prose-column` | `rehype-sanitize` + the existing pipeline already render them correctly; styling is a separate, owner-approved SPA decision. |
| Splitting the article into per-section LLM calls | Multi-call drafting orchestrator | A single streamed call | Out of scope ("call shape unchanged"); also doubles quota/latency and breaks the single-JSON contract. |

**Key insight:** in this domain the "custom solution" temptation is always a validator. Every locked decision here points the other way — the prompt is the contract, the only machine check is the three non-blank strings, and correctness of *content* is verified by a human reading a live draft.

## Runtime State Inventory

This is a prompt-contract rewrite, so the inventory question is: *after the files change, what runtime state still carries the old three-block text?*

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Existing `materials.body_markdown` rows written by the old templates keep their old `##` headings (e.g. material 25 from Phase 28's live proof). Phase 29's success criteria speak about **a newly ingested** material. | **None — deliberate.** No backfill, no data migration. Record this as an explicit non-goal so the verifier does not treat old rows as failures. |
| Live service config | None — the template text lives in git (`data-collection/src/data_collection/templates/`), loaded from the installed package at startup. | Reinstall are not needed for a source checkout (`uv run` uses the workspace path), but a deployed service must be redeployed to pick up new template text. |
| OS-registered state | None. systemd units (`ingest-collect`, timer) reference the CLI, not prompt text. | None. |
| Secrets/env vars | None renamed. `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `MAX_TRANSCRIPT_CHARS` keep their names/semantics. | None. |
| Build artifacts | `data_collection` is installed from `src/` via `uv_build`; the `.md` files are package data. No compiled artifact carries the old headings. | None beyond a normal process restart. |
| Reader cache / TOC | `extractMarkdownHeadings` runs per render from `body_markdown`; there is no persisted TOC. | None. |

**Nothing found in the remaining categories — verified by grepping the repo for the six old heading literals:** the only non-planning hits are `data-collection/.../templates/lecture.md`, `templates/podcast.md`, `tests/unit/test_article_templates.py`, `tests/unit/test_deepseek_article_adapter.py`, `tests/unit/test_article_draft_body_audience.py` (fixtures only) and `supabase-integration/migrations/004_phase4_knowledge_razbory.sql` (a `## Выводы` seed for *razbors*, matched only as a substring of `## Вывод` — unrelated to materials).

## Common Pitfalls

### Pitfall 1: The old scaffold leaks back in through a prohibition
**What goes wrong:** a task writes "не используй `## Тезис` / `## Ход рассуждения` / `## Вывод`" into the new template. The negative pins then either fail permanently or get deleted, and the model is shown exactly the tokens it must not produce.
**Why it happens:** forbidding the defect feels more precise than describing the target; it is also the intuitive way to "use" the old heading list.
**How to avoid:** never put the six old heading literals in any prompt string. Assert their absence in tests. Put only *style* prohibitions in `ARTICLE_SYSTEM_PROMPT` (the owner's three phrases), where no absence-pin conflicts and where examples genuinely help.
**Warning signs:** a plan task whose action text contains `## Тезис`; a diff that removes `assert "## О чём разговор" not in user_content`.

### Pitfall 2: Richer output hits the 8K completion ceiling and the draft is lost
**What goes wrong:** a longer article is generated until `max_tokens`; the stream is cut mid-JSON; `json.loads` fails; `ArticleInvalidJson` → `stage=llm reason=invalid_json`; fail-closed → **zero `materials` rows**.
**Why it happens:** the adapter sets no `max_tokens` `[VERIFIED: data-collection/.../deepseek_article.py:131-138]` and never reads `finish_reason` (Phase 8 explicitly decided an HTTP-200 `finish_reason="length"` is *not* `provider_context_length` and surfaces as `invalid_json`). DeepSeek's default is **8K completion tokens in non-thinking mode** `[CITED: api-docs.deepseek.com/api/create-chat-completion]`. The measured baseline is `response_chars=10314` for a 20,923-char transcript `[VERIFIED: .planning/milestones/v1.4-phases/28-live-proof-streamed-deepseek-ingest/evidence/ingest-run-1.log:5]`, i.e. the headroom is roughly 1.5–2×, which a facts layer + СВА section + more chapters can plausibly consume.
**How to avoid:** (a) put an explicit length band in both templates (e.g. "aim for 1 200–1 800 words; do not pad"), which is prompt-only and in scope; (b) record `response_chars` from `--debug` during the live proof as the kill-measure (> ~16,000 chars ⇒ escalate to Open Question Q1); (c) do **not** add `max_tokens` unilaterally — it is a call-shape change to a locked surface.
**Warning signs:** `stage=llm reason=invalid_json` on a long video; `response_chars` pinned near a round number; articles that end mid-sentence in the admin preview.

### Pitfall 3: `## Аудитория` stops being the last section
**What goes wrong:** the audience instruction is echoed into `body_markdown` and reaches the reader.
**Why it happens:** the strip walks from the `## Аудитория` heading to the next h1/h2 `[VERIFIED: data-collection/.../dto/_body.py:17-41]`. If a new section is appended after the audience block, the strip leaves the scaffolding instruction in the body (or deletes the wrong span).
**How to avoid:** keep the `## Аудитория` heading and its instruction line as the final lines of both files; add one regression case to `test_article_draft_body_audience.py` whose body ends with `## Конкретика` / `## Зачем это СВА` **then** `## Аудитория` and asserts the exact expected remainder.
**Warning signs:** a live draft whose prose ends with "Кто целевая аудитория материала?"; a template whose last heading is not `## Аудитория`.

### Pitfall 4: Bold renders, blockquote and table do not look like anything
**What goes wrong:** D-04 promises `>` quotes and D-07 allows a GFM table, but on the materials surface they are visually indistinguishable from body prose.
**Why it happens:** Tailwind preflight applies `*, ::after, ::before, ::backdrop, ::file-selector-button { margin: 0; padding: 0; border: 0 solid }` `[VERIFIED: web/node_modules/tailwindcss/preflight.css:7-16]`, while `b, strong { font-weight: bolder }` survives `[VERIFIED: web/node_modules/tailwindcss/preflight.css:102-105]`. The prose container declares only `[&_h1]`, `[&_h2]`, `[&_h3]`, `[&_p]`, `[&_ul]` utilities and no `[&_blockquote]` / `[&_table]` `[VERIFIED: web/src/pages/MaterialPage.jsx:238]`; `prose-column` matches no CSS rule (recorded in `18-02-SUMMARY.md:200`). `RazborPage` has `[&_table]:mt-4 [&_table]:w-full` but `MaterialPage` does not `[VERIFIED: web/src/pages/RazborPage.jsx:291]`.
**How to avoid:** keep bullets the default (D-07 already says so) and do not promise visual highlighting in the prompt. If a table or quote must stand out, that is a one-line utility-class change on `MaterialPage.jsx:238` mirroring `RazborPage.jsx:291` — an SPA change, so it needs owner sign-off and is **not** required by any success criterion.
**Warning signs:** a plan task proposing `design-frontend/` or CSS work; a UAT expectation like "the quote is visually offset".

### Pitfall 5: Documented empty-content behaviour on `json_object`
**What goes wrong:** the model returns an empty `content`, the adapter raises `ArticleInvalidJson` on `content == ""` `[VERIFIED: data-collection/.../deepseek_article.py:103-104]`, and the ingest fail-closes.
**Why it happens:** DeepSeek's JSON Output guide states the API "may occasionally return empty content" and suggests prompt changes as the mitigation `[CITED: api-docs.deepseek.com/guides/json_mode]`.
**How to avoid:** keep the JSON contract sentence in the system prompt short and unchanged (`Return one json object with keys title, dek, body_markdown, roles.`), keep the key list exactly where it is, and keep the new template prose declarative rather than a long conditional rule tree. Do not remove the word "json" from the prompt — the API returns 400 when `json_object` is requested without an explicit JSON instruction `[CITED: api-docs.deepseek.com/api/create-chat-completion]`.
**Warning signs:** `stage=llm reason=invalid_json` with `response_chars=0`; a plan that moves the JSON contract out of the system prompt into the templates.

### Pitfall 6: Guarding the wrong thing in tests
**What goes wrong:** tests assert that a *scripted* `body_markdown` has the right headings, or that the template contains some long sentence. The suite goes green while the prompt contract is unverified, and every future wording edit reddens the suite.
**Why it happens:** "assert the output" feels like stronger coverage than "assert the prompt".
**How to avoid:** two disjoint surfaces — (1) prompt pins: frame strings present, old scaffolds absent, kind hint isolated, `## Аудитория` last; (2) behavioural pins: scripted JSON round-trips unchanged (leave the existing adapter tests alone). Keep the `test_long_template_with_short_transcript_does_not_raise_budget_error` guarantee intact — it is what makes a longer template safe w.r.t. `llm_truncation` `[VERIFIED: tests/unit/test_deepseek_article_adapter.py:533-548]`.
**Warning signs:** a new test that reads `body_markdown` from a stub and asserts `"## Конкретика" in draft.body_markdown`.

## Code Examples

Verified patterns from the repository and official docs.

### Reading the templates the way the production adapter does
```python
# Existing pattern — tests/unit/test_article_templates.py:13-18 (pin being rewritten)
import importlib.resources

root = importlib.resources.files("data_collection.templates")
text = root.joinpath("lecture.md").read_text(encoding="utf-8")
assert "## Тезис" in text          # ← ART-01 flips this to absence + frame assertions
```
Source: `tests/unit/test_article_templates.py:13-18` `[VERIFIED]`

### Assembling the prompt (do not change the shape)
```python
# data-collection/src/data_collection/adapters/deepseek_article.py:46-62
user_parts = [
    templates[template],
    "",
    f"Transcript language: {transcript.language}",
    "",
    transcript.text,
]
return [
    {"role": "system", "content": ARTICLE_SYSTEM_PROMPT},
    {"role": "user", "content": "\n".join(user_parts)},
]
```
Source: `deepseek_article.py:46-62` `[VERIFIED]`. Consequence for tests: the template body sits in `messages[-1]["content"]` together with the transcript, so absence assertions are meaningful only for strings the transcript fixture does not contain (`_make_transcript` uses `"some transcript text"` `[VERIFIED: test_deepseek_article_adapter.py:46-48]`).

### The locked completion call
```python
# data-collection/src/data_collection/adapters/deepseek_article.py:131-138
stream = await self._client.chat.completions.create(
    model=self._model,
    messages=messages,
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
    stream=True,
)
```
Source: `deepseek_article.py:131-138` `[VERIFIED]`. No `max_tokens` — see Pitfall 2 and Open Question Q1.

### Shared honesty/voice prompt (current text, to be extended not replaced)
```python
# data-collection/src/data_collection/adapters/deepseek_article.py:35-43
ARTICLE_SYSTEM_PROMPT = (
    "You are an editorial assistant preparing articles for СВА (Служба внутреннего аудита).\n"
    "Use only the transcript below. Do not invent facts, names, or numbers.\n"
    "Output is always Russian.\n"
    "If the transcript language is ru: format only; do not translate.\n"
    "If the transcript language is en: translate into Russian.\n"
    "Preserve technical terms, proper names, library names, numbers, and units as written.\n"
    "Return one json object with keys title, dek, body_markdown, roles."
)
```
Source: `deepseek_article.py:35-43` `[VERIFIED]`. Adding voice lines here is safe: `test_system_prompt_contains_honesty_and_language_rules` pins ten substrings, all additive-compatible `[VERIFIED: tests/unit/test_deepseek_article_adapter.py:153-181]`.

### The audience strip contract (why the block must stay last)
```python
# data-collection/src/data_collection/dto/_body.py:17-22
_AUDIENCE_HEADING_RE = re.compile(
    r"^#{2,6}[ \t]+Аудитория[ \t]*$", re.IGNORECASE | re.MULTILINE
)
_NEXT_TOP_HEADING_RE = re.compile(r"^#{1,2}[ \t]+\S", re.MULTILINE)
```
Source: `dto/_body.py:17-22` `[VERIFIED]`

### What the reader surface actually supports
```jsx
// web/src/pages/MaterialPage.jsx:240-245
<Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSlug, rehypeSanitize]}>
  {material.body_markdown}
</Markdown>
```
Source: `MaterialPage.jsx:240-245` `[VERIFIED]`. Default sanitize schema allows `blockquote` (line 154), `strong` (194) and `table` (198); protocols for `href` are `http/https/irc/ircs/mailto/xmpp` (141-146); `strip: ['script']` (150) `[VERIFIED: web/node_modules/hast-util-sanitize/lib/schema.js]`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixed three-block scaffold (`## Тезис / ## Ход рассуждения / ## Вывод`; `## О чём разговор / ## Позиции / ## Что запомнить`) | Content-shaped `##` following the talk, with optional facts layer and optional audit takeaway | v1.5, Phase 29 (2026-10-26) | Phase 8 D-16 is superseded; the six heading literals become forbidden strings, and the heading pins invert. |
| Facts drowned in narrative prose | Dedicated scannable `## Конкретика` layer (names/numbers/tools/caveats, transcript-only) | Phase 29 | Gives the "lost detail" failure a home; freezes a stable string for Phase 32 to protect. |
| Audit angle only in `dek` | Editorial `## Зачем это СВА` body section, present only when an analog exists | Phase 29 (ART-03 owner-overridden) | `dek` stays a pure hook; no duplication of the takeaway. |
| Promising colour/HTML highlighting | `**bold**` + `>` blockquote within an existing sanitizer | Phase 29 | No new renderer, no sanitizer widening. |
| Two separate fixed voices (v1.1 "looser podcast voice" was deferred) | Shared editorial voice + one kind hint | Phase 29 (D-05) | Templates differ by a single Structure paragraph. |

**Deprecated/outdated:**
- Phase 8 D-16 (mandated heading strings) — superseded by D-01/D-06/D-10.
- Phase 10 UAT heading checks (`## Тезис` …) — historical evidence only; must **not** be revived as a required reader heading (CONTEXT `Integration Points`).
- "Verbose rule trees in the prompt" as a quality lever: the current DeepSeek guidance favours a short JSON instruction plus an example `[CITED: api-docs.deepseek.com/guides/json_mode]`; the new richness should come from the editorial frame, not from more conditions.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Russian text ≈ 2.0–2.5 chars per completion token for `deepseek-flash`, so the measured 10,314-char article is roughly 3.5–5K tokens and the 8K default leaves ~1.5–2× headroom | Pitfall 2, Open Question Q1 | If the real ratio is worse (more tokens per char), the truncation threshold arrives earlier and the length band must be tighter; the mitigation direction (measure `response_chars`, bound length) is unchanged. |
| A2 | Leaving already-published materials with the old three-block headings is acceptable (no backfill) | Runtime State Inventory | If the owner wants backfill, it becomes a content-migration task with no transcript available — a materially different (and much larger) phase. |
| A3 | The owner does not require quotes/tables to be *visually* distinct on the reader surface | Pitfall 4 | Would require a one-line SPA change to `MaterialPage.jsx:238` (owner sign-off, SPA surface otherwise out of scope). |
| A4 | A single streamed call can still satisfy "content-shaped `##`" quality-wise, without per-section drafting | Standard Stack / Alternatives | Per-section drafting is the documented quality lever for longform-from-transcript work, but it is a call-shape change and out of scope; if quality is poor at UAT, that becomes a Phase-32-style discussion, not a Phase-29 patch. |
| A5 | The live proof can obtain a YouTube video id absent from `materials` (needed because `youtube_video_id` is unique and a re-run yields `already_saved`) | Validation Architecture | Without a fresh id the proof cannot observe new-template output; the operator would have to accept a "prompt captured" proof instead. |

## Open Questions

1. **How do we bound output length: prompt band or `max_tokens`?**
   - What we know: measured output 10,314 chars; default completion cap 8K tokens; no `max_tokens` in the adapter; a cut stream is `invalid_json` (fail-closed, zero rows).
   - What's unclear: whether the richer frame lands at 12K or 20K chars in production.
   - Recommendation: ship the prompt length band (in scope), measure `response_chars` in the live proof, and treat > ~16,000 chars as the trigger to ask the owner for a `max_tokens` change (a locked-surface exception).
2. **Where do the voice rules live: `ARTICLE_SYSTEM_PROMPT` or the templates?**
   - What we know: both are allowed by CONTEXT discretion; the existing system-prompt test pins ten substrings, all additive-compatible.
   - What's unclear: nothing technical — this is a maintainability call.
   - Recommendation: shared rules (voice, attribution, no-recap) in `ARTICLE_SYSTEM_PROMPT`; per-kind structure and the two optional section clauses in the template files. This keeps the two `.md` files differing by one paragraph.
3. **Which video proves the phase, and who runs it?**
   - What we know: Phase 28's runbook (`uv run --env-file ./ingestion-service/.env ingest <url> --template lecture --debug`) is proven; captions need `YOUTUBE_PROXY_URL` + the `adguard-vpn` container; DeepSeek must stay direct (`trust_env=False`).
   - What's unclear: operator availability at execution time and a suitable unused video id.
   - Recommendation: make the live proof an explicit task with a `checkpoint:human-verify`, and pre-record the acceptance checklist (headings follow the talk; `## Конкретика` present or honestly absent; `## Зачем это СВА` present when an analog exists; `dek` unchanged in role; `response_chars` recorded).
4. **Do we accept flat-rendered quotes and tables?**
   - What we know: `strong` is bold; `blockquote`/`table` have no styling on the materials surface.
   - Recommendation: accept for v1.5 (bullets are the documented default), and do not write a UAT criterion that depends on visual emphasis.
5. **Do existing materials get relabelled or re-ingested?**
   - What we know: success criteria say "newly ingested".
   - Recommendation: no backfill, no re-ingest (a re-ingest of a saved video returns `already_saved` and spends no LLM call anyway).
6. **The ROADMAP/REQUIREMENTS wording for criterion 3 does not match D-10/D-11 — which text does verification score against?**
   - What we know: `.planning/ROADMAP.md` Phase 29 criterion 3 still reads "explicit «Зачем это СВА» **and risks/limitations sections** even if the talk barely mentioned audit"; `REQUIREMENTS.md` ART-03 says the same. CONTEXT D-10 merges the two headings into one and D-11 makes it optional (owner override, gathered after the roadmap was written).
   - What's unclear: a literal-reading verifier will demand a second section and demand presence on a talk with no analog — both explicitly rejected by the owner.
   - Recommendation: plan and verify against the CONTEXT reading (one optional `## Зачем это СВА`, residual caution in its prose), state the override in the phase summary/VERIFICATION notes, and (cheap, optional) ask the owner to amend criterion 3 in `.planning/ROADMAP.md` + ART-03 so the artifact and the intent do not disagree.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | Running `uv run pytest`, live ingest | ✓ | 0.10.9 | — |
| Python (workspace venv) | Unit suite | ✓ | 3.12.13 | — |
| `pytest` | Unit suite | ✓ | `>=8.3.0` (declared) | — |
| Node.js | Only Playwright / JS unit gates (not needed here) | ✓ | v24.21.0 | — |
| `DEEPSEEK_API_KEY` | Live proof (and any real ingest) | operator-supplied (`ingestion-service/.env`) | — | None — without it the phase can still ship on prompt pins + a scripted-body proof, but criteria 1–3 stay unobserved. |
| Egress to `api.deepseek.com` | Live proof | ✓ (measured 2026-10-22, TLSv1.3) | — | — |
| `YOUTUBE_PROXY_URL` + `adguard-vpn` container | Captions during the live proof | operator-supplied | — | Any transcript source works (`FakeTranscriptProvider` is not usable for a live article); without it, use a video already captioned by another path or defer the proof. |
| Playwright browsers | Not required by this phase | — | — | — |

**Missing dependencies with no fallback:** none blocking the code/test work.
**Missing dependencies with fallback:** the live proof depends on operator credentials/network; the fallback is a documented deferred UAT item (as in Phases 24/28), not a silent pass.

## Validation Architecture

`workflow.nyquist_validation` is absent from `.planning/config.json`, so Nyquist validation is **enabled** `[VERIFIED: .planning/config.json:1-9]`.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest `>=8.3.0` (Python 3.12.13), `testpaths = ["tests/unit"]` `[VERIFIED: pyproject.toml:31, 35-39]` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` — no `pytest.ini` |
| Quick run command | `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_draft_body_audience.py -x` — measured **58 passed in 2.06 s** |
| Full suite command | `uv run pytest` — measured **1156 passed in 13.73 s** (baseline before any Phase 29 edit) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ART-01 | `lecture.md` carries the free-`##` frame and none of the three lecture scaffold literals | unit | `uv run pytest tests/unit/test_article_templates.py -x` | ✅ exists — pin **rewrite** (`:13-18`) |
| ART-01 | `podcast.md` carries the dialogue/topic kind hint and none of the three podcast scaffold literals | unit | same file | ✅ exists — pin **rewrite** (`:21-26`) |
| ART-01 | Loaded templates expose the new frame for both kinds | unit | same file (`test_load_article_templates_returns_both_kinds`, `:29-36`) | ✅ exists — **rewrite** |
| ART-01 | Assembled lecture user message forbids all six scaffold literals and does not leak the podcast kind hint | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ✅ exists — **rewrite** (`:105-127`) |
| ART-01 | Assembled podcast user message mirrors the above | unit | same file | ✅ exists — **rewrite** (`:129-151`) |
| ART-01 | A real ingested draft's `##` follow the talk | manual/live | `uv run --env-file ./ingestion-service/.env ingest <new-url> --template lecture --debug`, then open `/admin/materials/{id}` | ❌ **Wave 0** — UAT checklist + evidence capture |
| ART-02 | Both templates contain `## Конкретика` with the transcript-only, bullets-first, canonical-name, omit-when-empty rules | unit | `uv run pytest tests/unit/test_article_templates.py -x` | ✅ exists — new assertions |
| ART-02 | `## Конкретика` still passes through a scripted draft untouched (no body rewriting) | unit | existing adapter round-trip tests (`:203-221`) | ✅ exists — no change |
| ART-02 | No invented numbers/names/versions in the produced facts block | manual/live | digit audit: every number/tool in `## Конкретика` must appear in the transcript (capture the transcript during the proof) | ❌ **Wave 0** — evidence script/checklist |
| ART-03 | Both templates contain `## Зачем это СВА` with the analog bar, the no-invented-duty rule, the editorial-voice rule and the omit rule | unit | `uv run pytest tests/unit/test_article_templates.py -x` | ✅ exists — new assertions |
| ART-03 | System prompt carries the shared voice/no-recap rules without losing the ten pinned honesty/language substrings | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ✅ exists — extend (`:153-181`) |
| ART-03 | Live draft has `## Зачем это СВА` when an analog exists, and `dek` remains a hook | manual/live | live proof + preview read | ❌ **Wave 0** — UAT checklist |
| (regress) | `## Аудитория` strip still works when the new headings precede it | unit | `uv run pytest tests/unit/test_article_draft_body_audience.py -x` | ✅ exists — add 1 case |
| (regress) | `response_format`, `thinking`, `stream=True`, no `max_tokens` | unit | `test_create_kwargs_include_json_object_and_disabled_thinking`, `test_create_is_called_with_stream_true` | ✅ exists — no change |
| (regress) | Template length stays exempt from the transcript budget | unit | `test_long_template_with_short_transcript_does_not_raise_budget_error` (`:533-548`) | ✅ exists — no change |
| (regress) | Error taxonomy / `LLM_REASONS` / fail-closed unchanged | unit | `uv run pytest tests/unit/test_article_error_mapping.py -x` | ✅ exists — no change |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_draft_body_audience.py -x` (~2 s)
- **Per wave merge:** `uv run pytest` (1156 tests, ~14 s)
- **Phase gate:** full suite green **plus** the live-proof evidence file with `stage=llm … response_chars=…` and the UAT checklist for criteria 1–3

### Wave 0 Gaps
- [ ] `tests/unit/test_article_templates.py` — rewrite `test_lecture_md_contains_russian_headings` and `test_podcast_md_contains_russian_headings` into "frame present + scaffold absent", and update `test_load_article_templates_returns_both_kinds` off `## Тезис` / `## О чём разговор` (RED first: run before touching the `.md` files).
- [ ] `tests/unit/test_deepseek_article_adapter.py` — rewrite `test_lecture_prompt_contains_lecture_headings_not_podcast` and `test_podcast_prompt_contains_podcast_headings_not_lecture` to assert all six scaffold literals are absent from both messages and that the shared headings are present in both.
- [ ] `tests/unit/test_article_draft_body_audience.py` — one case with the real new headings before the trailing `## Аудитория` block.
- [ ] Evidence/UAT artifact for the live proof (checklist + captured `--debug` lines + transcript used for the digit audit). This is not a pytest file.
- [ ] No framework install needed — `pytest` is already configured and the baseline suite is green.

## Security Domain

`security_enforcement` is absent from `.planning/config.json`, so this section is required.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Unchanged — Phase 29 touches no auth surface. |
| V3 Session Management | no | Unchanged. |
| V4 Access Control | no | Unchanged; drafts stay admin-only, readers see ready-only. |
| V5 Input Validation | yes | The transcript is untrusted input into the prompt; `ArticleDraft` validation is the only structural check; the rendered markdown goes through `rehype-sanitize` (default GitHub schema, `strip: ['script']`, `clobberPrefix: 'user-content-'`) `[VERIFIED: web/node_modules/hast-util-sanitize/lib/schema.js:139-198]`. Phase 29 does not widen it. |
| V6 Cryptography | no | No crypto in this phase. |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Transcript-borne prompt injection ("ignore previous instructions") steering the article's structure/facts | Tampering | Transcript-only framing, no tools, no URL fetching, no second-order actions; output is inert markdown through the sanitizer; fail-closed on any non-JSON output. Phase 29 increases the *surface* (free chapters, facts layer), so the honesty line must stay verbatim in the system prompt. |
| Model-emitted HTML/JS or `javascript:` links | Tampering / XSS | Sanitizer default schema (`strip: ['script']`, `href` protocol allowlist) — already in place; do not add `rehype-raw`, do not widen the schema. |
| Invented facts/numbers presented as "from the video" | Spoofing / Repudiation | Transcript-only instruction (D-18) + human `draft → ready` review + the UAT digit audit. The facts layer is *more* exposed to this than prose, because it invites list-shaped precision. |
| Model-invented URLs in pass 1 | Spoofing | Out of scope here (Phase 32/33 own links); still forbid link instructions in the templates so pass 1 cannot become a provenance source. |
| Secret leakage through errors | Information disclosure | Unchanged allowlist (`stage=llm` context = `video_id`, `exception_class`, `status_code`); Phase 29 must not add context keys. |
| Prompt text leaking to the reader | Information disclosure | `## Аудитория` strip remains the only scaffolding filter; keep that heading last (Pitfall 3). |

## Sources

### Primary (HIGH confidence — read from source this session)
- `data-collection/src/data_collection/templates/lecture.md:1-16` and `podcast.md:1-16` — current scaffold and audience block.
- `data-collection/src/data_collection/adapters/deepseek_article.py:35-43, 46-62, 95-104, 131-138` — prompt assembly, budget guard, empty-content guard, completion kwargs.
- `data-collection/src/data_collection/dto/_body.py:17-41` — audience strip regexes and behaviour.
- `data-collection/src/data_collection/dto/article_draft.py:11-31`, `dto/template_kind.py:1-8`, `dto/role_kind.py:1-15` — DTO contract.
- `tests/unit/test_article_templates.py:13-36`, `tests/unit/test_deepseek_article_adapter.py:105-181, 203-221, 533-548`, `tests/unit/test_article_draft_body_audience.py:1-90` — the pins to rewrite and the pass-through coverage to keep.
- `ingestion-service/src/ingestion_service/mapping/article.py:19-70` — `LLM_REASONS`, `stage=llm` / `llm_truncation` split.
- `ingestion-service/src/ingestion_service/composition/settings.py:13, 83-121` — `MAX_TRANSCRIPT_CHARS=80000`, `deepseek-flash`.
- `web/src/pages/MaterialPage.jsx:212, 238-245`; `web/src/pages/RazborPage.jsx:291`; `web/src/utils/markdownToc.js:47-76` — reader rendering and TOC.
- `web/node_modules/hast-util-sanitize/lib/schema.js:139-198`; `web/node_modules/tailwindcss/preflight.css:7-16, 102-105` — allowed tags/protocols and the zeroed blockquote/table styling.
- `.planning/milestones/v1.4-phases/28-live-proof-streamed-deepseek-ingest/evidence/ingest-run-1.log:1-7` — measured `transcript_chars=20923`, `response_chars=10314`, `elapsed_ms=16578`.
- `uv.lock:917-919, 1087-1089, 1858-1860`; `pyproject.toml:31, 35-39` — locked versions and pytest config.
- Local runs: `uv run pytest` → **1156 passed in 13.73 s**; targeted files → **58 passed in 2.06 s**.

### Secondary (MEDIUM confidence — official provider docs via Context7)
- DeepSeek, *JSON Output* — `https://api-docs.deepseek.com/guides/json_mode` — `json_object` requires the word "json" in the prompt, the docs recommend an example JSON shape and a sane `max_tokens`, and warn that empty content may occur.
- DeepSeek, *Create Chat Completion* — `https://api-docs.deepseek.com/api/create-chat-completion` — `max_tokens` default 8K non-thinking / 64K thinking, `finish_reason="length"` truncation, HTTP 400 if `json_object` is requested without a JSON instruction.

### Tertiary (LOW confidence — web, cross-checked only)
- Transcript-to-article prompt practice (QuQi prompt library, audien.to, lastingcontent flattening guide, TranscribeBee prompt YAML, an OpenAI-community thread on article-from-transcript prompts): thematic idea-ordered outline over spoken order, sparing attributed verbatim quotes, protected specifics, explicit "add no outside context", and the finding that conflicting "reflect the speaker" / "no own assertions" instructions produce hedged, flat prose — separate attribution from editorial voice with examples instead of stacking prohibitions.

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — no new packages; every version read from `uv.lock`; the call shape is pinned by tests.
- Architecture: **HIGH** — the full data flow, the strip contract, the sanitizer allow-list and the prose-column styling gap were all read from source this session.
- Pitfalls: **HIGH for the repo-grounded ones** (negation leakage, audience ordering, styling gap, H1 duplication, invalid_json on truncation); **MEDIUM for the output-length risk** (the 8K default is cited, the char→token ratio is assumed).
- Prompt craft (editorial frame): **MEDIUM** — convergent third-party practice plus the owner's locked decisions; no authoritative standard exists.

**Research date:** 2026-10-26
**Valid until:** ~2026-11-25 (30 days). Re-check the DeepSeek `max_tokens` default and JSON-output guidance if the adapter's model or SDK range changes; re-check the measured `response_chars` after the first live run with the new templates.
