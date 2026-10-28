# Phase 30: Classifier practical | conceptual - Research

**Researched:** 2026-10-28
**Domain:** Ingest pipeline classification (DeepSeek JSON classifier + Postgres persist + pass-1 body sanitizer)
**Confidence:** HIGH for in-repo contracts and wiring; MEDIUM for DeepSeek/Postgres official-docs details (Context7 classify-confidence seam returned MEDIUM even with `--verified`)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)
- Tavily / quota / persist-then-enrich — Phase 31.
- Pass-2 guide sections, generated code, live URLs, cheat-sheet files — Phase 32. After D-11, `## Гайд` is allowed to appear only here.
- Reader sources block and cheat-sheet downloads; honest omission of download CTAs — Phase 33.
- Operator `--debug` classifier / quota / URL counts — Phase 34.
- Classifier input (transcript vs title+dek vs pass-1 article) — not deferred; Claude's Discretion above.
- Reader-facing classifier badge / ADUX-14 quiet admin note — still out of v1.5.
- None of the above were folded from todos (`todo.match-phase 30` was empty).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KIND-01 | Every ingest records `topic_kind` as `practical` or `conceptual` on the draft | Additive `topic_kind` on `ArticleDraft` + `MaterialDraft`; `assemble_material_draft` copies it; `normalize_topic_kind` always yields one of the two literals; migration `014` column + `p_topic_kind` on `persist_draft_and_enqueue`; pipeline stamps after a separate classifier call |
| KIND-02 | Missing, empty, or unknown `topic_kind` is stored as `conceptual` and does not attach guide sections, generated-code extras, Tavily reads, or a cheat sheet | Code-layer mapping (clone `normalize_roles`); Pydantic `Literal` must not `ValidationError` on garbage (that would become `stage=llm`); classifier transport/empty JSON fail-soft to `conceptual`; extras are **not wired** this phase — pin absence of Tavily/enricher call sites; stored kind is the Phase 31/32 gate |
| KIND-03 | A conceptual material has no empty «Гайд» heading, no disabled cheat-sheet control, and no “ссылки скоро появятся” placeholder | `strip_guide_section` sibling of `strip_audience_section` in `_body.py`, run on **every** pass-1 body via `ArticleDraft` validator (D-11); exact ATX `Гайд` + exact substring «ссылки скоро появятся» (D-12); download CTA is Phase 33 — no disabled control to implement here |
</phase_requirements>

## Summary

Phase 30 is a **gate, not an enricher**. After pass-1 `ArticleGenerator.process` returns a valid `ArticleDraft`, the pipeline makes a **second, cheap DeepSeek JSON call**, stamps a closed `topic_kind` (`practical` \| `conceptual`), sanitizes `## Гайд` / «ссылки скоро появятся» out of the pass-1 body, assembles `MaterialDraft`, and persists. Invalid, empty, unknown, or transport-failed classifier output is stored as `conceptual` **in code** and ingest continues. Tavily, the pass-2 enricher, cheat-sheet files, reader badges, and `--debug` classifier lines are out of this phase.

The two-layer default is the planning hinge. The **prompt** says “if you successfully answer but are unsure, pick `practical`” (D-08). The **code** says “if there is no valid enum value, store `conceptual`” (KIND-02). Tests must pin both so a helpful model cannot launder `"unsure"` / malformed JSON / empty content into `practical`. Folding classify into the pass-1 honesty prompt is rejected (Pitfall 3 / ROADMAP). Widening `data_collection.__all__` or `IngestError.stage` reds locked pins.

**Primary recommendation:** Add `TopicKindClassifier` as a module-private port; clone the DeepSeek client with `json_object` + `thinking.disabled` + `stream=False` + small `max_tokens`; map KIND-02 in `normalize_topic_kind`; strip `## Гайд` in `_body.py`; persist via new migration `014` that `DROP FUNCTION`s the current `persist_draft_and_enqueue` signature then recreates it with `p_topic_kind`. Install **zero** new packages.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Closed `topic_kind` classification | API / Backend (ingestion-service use-case + data-collection port) | — | CLI writer owns YouTube + LLM. Browser never classifies. |
| KIND-02 mapping (invalid → `conceptual`) | API / Backend (pure function in data-collection DTO) | Database / Storage (CHECK + DEFAULT) | Code is the product rule; DB CHECK is defense in depth, not the only gate. |
| Pass-1 body strip (`## Гайд` / placeholder) | API / Backend (`ArticleDraft` validator) | — | Same home as `strip_audience_section`. Not a reader sanitizer. |
| Persist `topic_kind` on the draft | Database / Storage (`materials` column + RPC) | API / Backend (`SupabaseDraftPersister`) | KIND-01 requires it on the stored draft. |
| Extras gate (Tavily / enricher / cheat sheet) | API / Backend (unwired this phase) | — | Phase 31/32 read the stored kind. This phase only proves extras are not called. |
| Reader/admin badge or download CTA | — | — | Explicitly out of scope. Backend `Material` select list already omits unknown columns. |

## Project Constraints (from .cursor/rules/)

Treat these with the same authority as locked CONTEXT.md decisions.

### TDD (`.cursor/rules/tdd.mdc`, `AGENTS.md`)
- Red–Green–Refactor. **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.**
- Write the Playwright/unit test, watch it fail for the expected reason, then the minimal production fix, then the full suite. Refactor only on green.
- Exceptions: configs, generated files, one-off prototypes — only with explicit agreement.

### Ports & Adapters (`.cursor/rules/architecture.mdc`)
- Modules: `web/`, `backend/`, `supabase-integration/`, `data-collection/`. Talk only through public API / ports. No deep-import into another module's internals.
- Domain/use-case: **no** `supabase` / `httpx` / `requests` / `fastapi` / raw SQL.
- Ports = `typing.Protocol` / `abc.ABC`. No `Any` on port boundaries.
- Wiring **only** in composition (`ingestion-service/composition/` for this phase). No `create_client` / `httpx.Client` in business logic.
- Unit tests: in-memory fakes, no network/DB. Integration tests marked and not mixed with unit.
- Frontend: no backend/SPA changes this phase.

### Python deps (`.cursor/rules/python-uv.mdc`)
- `uv add` / `uv remove` / `uv sync` only. Do not use pip/poetry for dependency management.
- This phase adds **no** packages.

### Context7 (`.cursor/rules/context7.mdc`)
- Library/API docs via Context7 before codegen against third-party APIs (DeepSeek JSON mode, Postgres `CREATE FUNCTION`).

### Project skills
- `.agents/skills/supabase/SKILL.md` + `supabase-postgres-best-practices`: imperative migrations (`supabase-integration/migrations/`), RLS already on `materials`, `ADD CONSTRAINT IF NOT EXISTS` is invalid Postgres — use a `DO` block. `text` + CHECK, not a new PG enum, for a two-value closed set.
- Hallmark is UI-only — skip.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `openai` (AsyncOpenAI) | `3.19.2` locked in `uv.lock`; constraint `openai>=3.0,<4` in `data-collection/pyproject.toml` | Classifier HTTP via the same injected client as pass-1 | Already the DeepSeek adapter. `extra_body` carries `thinking`. |
| `pydantic` | `2.13.5` locked; constraint `pydantic>=2.10.0` | `ArticleDraft` / `MaterialDraft` + `Literal` + `field_validator(mode="before")` | Already the DTO layer. Before-validator is how `normalize_roles` works. |
| Postgres / `persist_draft_and_enqueue` | self-hosted Supabase; current RPC in migration `009` | Additive `materials.topic_kind` + RPC param | Phase 11 precedent: `CREATE OR REPLACE` same arity; this phase **changes arity** so it must `DROP FUNCTION` first. |
| `pytest` | `9.1.1` locked; `>=8.3.0` in root `pyproject.toml` | Unit suite under `tests/unit` | Existing TDD runner. |

Versions confirmed from `uv.lock` this session (`openai` 3.19.2 upload-time 2026-09-24; `pydantic` 2.13.5 upload-time 2026-08-28; `pytest` 9.1.1). No registry `pip index` call — these are already locked workspace members, not new installs.

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` / `DefaultAsyncHttpxClient` | `httpx[socks]==0.28.1` | `trust_env=False` DeepSeek TLS | Reuse `build_async_deepseek_client`. Never `build_httpx_client` (YouTube SOCKS5). |
| `typing.Protocol` / `Literal` | stdlib (Python 3.12+) | Port + closed enum | Same as `ArticleGenerator` / `RoleKind`. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Separate classifier call | Fold `topic_kind` into pass-1 `json_object` | **Rejected** by ROADMAP + Pitfall 3. Contaminates `## Конкретика`. |
| `stream=True` (clone pass-1) | Non-stream JSON | Pass-1 streams because a long article idles the socket 8–12 s. Classifier output is ~one object. `stream=False` is the cheap call. |
| PG `CREATE TYPE topic_kind AS ENUM` | `text` + CHECK | Schema skill: “Enums: use text with check constraint or create enum type.” A two-value closed set does not need a new enum type (adding values later is painful; this set is closed). |
| `json_schema` structured outputs | `json_object` | DeepSeek documents `text` \| `json_object` only. Pass-1 already uses `json_object`. KIND-02 mapping in code is required either way (`json_object` does not guarantee keys). |

**Installation:** none.

```bash
# Do not run uv add. Reuse openai + pydantic already in data-collection.
```

## Package Legitimacy Audit

This phase installs **zero** external packages. The Package Legitimacy Gate was not run because there is nothing to install.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | No new packages |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
YouTube URL
    │
    ▼
extract_video_id ──fail──► IngestError.stage="url"
    │
    ▼
captions.get ──fail──► stage="captions"   (fail-closed, zero rows)
    │
    ▼
metadata.get ──fail──► stage="metadata"
    │
    ▼
video_id match? ──no──► stage="consistency"
    │ yes
    ▼
ArticleGenerator.process (pass-1, stream json_object, transcript-only)
    │
    ├── ArticleError ──► map_article_error ──► stage="llm"|"llm_truncation"
    │
    ▼ ArticleDraft  (validators already stripped ## Аудитория and ## Гайд)
    │
    ▼
TopicKindClassifier.classify(transcript, article)     ← NEW, separate call
    │
    ├── transport / empty / invalid JSON / missing key
    │      └─► normalize_topic_kind → "conceptual"   (fail-SOFT, NOT stage=llm)
    │
    ├── model returns "practical" | "conceptual"
    │      └─► store as-is (D-08 unsure→practical lives only in the prompt)
    │
    └── model returns "unsure" | "howto" | "" | null
           └─► "conceptual" in code (KIND-02)
    │
    ▼ stamp article.topic_kind
    │
    ▼ assemble_material_draft  (copies topic_kind; provenance_label unchanged)
    │
    ▼ persist_draft  (RPC p_topic_kind)
    │
    ├── already_saved true  → return (extras still unwired)
    └── new draft           → return PersistResult
                              extras (Tavily/enricher/cheat sheet) NOT CALLED
```

Pass-1 remains fail-closed. Classify is fail-soft. Persist still fail-closed (`stage="persist"`).

### Recommended Project Structure

```
data-collection/src/data_collection/
  ports/topic_kind.py              # NEW Protocol TopicKindClassifier
  dto/topic_kind.py                # NEW TopicKind Literal + normalize_topic_kind
  dto/_body.py                     # ADD strip_guide_section (+ placeholder)
  dto/article_draft.py             # ADD topic_kind field + guide-strip validator
  dto/material_draft.py            # ADD topic_kind field
  assemble.py                      # COPY topic_kind
  adapters/deepseek_classifier.py  # NEW module-private adapter
  tests_support/fakes.py           # ADD FakeTopicKindClassifier
  __init__.py                      # UNCHANGED ten-name __all__
  ports/__init__.py                # UNCHANGED (do not append TopicKindClassifier)

ingestion-service/src/ingestion_service/
  application/use_cases/ingest_pipeline.py   # inject classifier; stamp; no extras
  composition/clients.py                     # build_deepseek_topic_kind_classifier
  cli.py                                     # build_ingest_deps wires classifier
  domain/errors.py                           # Stage UNCHANGED
  diagnostics/redaction.py                   # optional: allowlist key topic_kind

supabase-integration/migrations/
  014_phase30_materials_topic_kind.sql       # NEW: column + DROP/CREATE RPC
```

Do **not** touch `backend/domain/material.py`, `web/`, templates `lecture.md` / `podcast.md` (except to keep the Phase 29 pin that they must not contain `Гайд`).

### Pattern 1: Two-layer default (prompt vs code)

**What:** Prompt bias and code bias are opposite and must both be tested.
**When to use:** Any LLM enum that gates a scarce resource (here, the Tavily 1000).

```python
# Source: clone data-collection/src/data_collection/dto/role_kind.py:7-16
# Verbatim RoleKind / VALID_ROLES / normalize_roles:
#   RoleKind = Literal["employee", "analyst", "ds"]
#   VALID_ROLES: frozenset[str] = frozenset({"employee", "analyst", "ds"})
#   def normalize_roles(value: object) -> list[RoleKind]:
#       """Filter unknown roles; empty or malformed input becomes ['employee']."""
#       if not isinstance(value, list):
#           return ["employee"]
#       filtered: list[RoleKind] = [role for role in value if role in VALID_ROLES]
#       return filtered or ["employee"]

TopicKind = Literal["practical", "conceptual"]
VALID_TOPIC_KINDS: frozenset[str] = frozenset({"practical", "conceptual"})


def normalize_topic_kind(value: object) -> TopicKind:
    """Missing, empty, unknown, or malformed → conceptual (KIND-02)."""
    if isinstance(value, str):
        token = value.strip().casefold()
        if token in VALID_TOPIC_KINDS:
            return token  # type: ignore[return-value]
    return "conceptual"
```

Bare Pydantic `Literal["practical", "conceptual"]` **raises** `literal_error` on `"cherry"`-style input `[CITED: pydantic.dev validation Literal]`. If `topic_kind` arrived in pass-1 JSON as `"unsure"`, that would become `ArticleInvalidDraft` → `stage=llm` and **zero rows**. KIND-02 forbids that. Use `field_validator(..., mode="before")` that returns `normalize_topic_kind(value)` so Literal always sees a legal token.

### Pattern 2: Cheap separate DeepSeek JSON call

**What:** Clone the injected-client adapter, not the pass-1 stream.
**When to use:** Small closed JSON after a long streamed article.

Pass-1 call (do **not** copy `stream=True` blindly) `[VERIFIED: data-collection/src/data_collection/adapters/deepseek_article.py:139-145]`:

```python
stream = await self._client.chat.completions.create(
    model=self._model,
    messages=messages,
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
    stream=True,
)
```

Classifier call — use this:

```python
# Source: api-docs.deepseek.com/guides/json_mode + /guides/thinking_mode
# + openai-python extra_body; KIND-02 mapping still in code.
response = await self._client.chat.completions.create(
    model=self._model,
    messages=messages,
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
    max_tokens=128,
    stream=False,
)
content = response.choices[0].message.content
```

DeepSeek rules that the planner must pin in tests `[CITED: api-docs.deepseek.com/guides/json_mode]`:
1. `response_format={'type':'json_object'}`.
2. The prompt must contain the word **json** and an example shape. Without a JSON instruction the API returns **HTTP 400**.
3. Set `max_tokens` reasonably so the object is not cut (`finish_reason="length"`).
4. JSON mode may still return **empty content** — treat as KIND-02 `conceptual`, do not map to `ArticleInvalidJson` / `stage=llm`.
5. `thinking.type` default is **`enabled`**. OpenAI SDK must pass it in `extra_body`. `[CITED: api-docs.deepseek.com/guides/thinking_mode]`

`json_object` guarantees syntactically valid JSON, **not** required keys `[CITED: openai-python response_format docstring]`. KIND-02 mapping is mandatory.

Reuse `build_async_deepseek_client` `[VERIFIED: ingestion-service/src/ingestion_service/composition/clients.py:64-75]`:

```python
return AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=timeout,
    max_retries=0,
    http_client=DefaultAsyncHttpxClient(trust_env=False),
)
```

Do not share `build_httpx_client` (YouTube proxy). Do not add a new Settings env var; use `settings.deepseek_model` / `settings.deepseek_api_key`.

### Pattern 3: Heading sanitizer, not a fail-closed parser

**What:** Clone `strip_audience_section`. Never reject ingest because `## Гайд` leaked.
**When to use:** Prompt scaffolding / extras headings that models emit into `body_markdown`.

`[VERIFIED: data-collection/src/data_collection/dto/_body.py:16-41]`:

```python
_AUDIENCE_HEADING_RE = re.compile(
    r"^#{2,6}[ \t]+Аудитория[ \t]*$", re.IGNORECASE | re.MULTILINE
)
_NEXT_TOP_HEADING_RE = re.compile(r"^#{1,2}[ \t]+\S", re.MULTILINE)
```

Add `_GUIDE_HEADING_RE` with the same ATX shape, text exactly `Гайд` (use `re.IGNORECASE` like audience so `## гайд` cannot leak; D-12's “exact” means do not match `Guide` / `How-to` / `Как сделать` / `Tutorial` / `Шпаргалка`, not “case-sensitive Cyrillic only”). Strip heading + body until the next h1/h2. Then delete the exact substring `ссылки скоро появятся`. Leave in-prose «гайд» (Phase 29 live title even contains «гайд на VPS»). Hook the new helper from a second `@field_validator("body_markdown")` on `ArticleDraft` so it runs on **every** pass-1 body (D-11), including practical drafts.

### Pattern 4: Additive RPC via DROP + CREATE (arity change)

**What:** Migration `009` is the live function. It has **no** `topic_kind`. `[VERIFIED: supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql:8-21]`:

```sql
create or replace function public.persist_draft_and_enqueue(
  p_title text,
  p_dek text,
  p_body_markdown text,
  p_slug text,
  p_reading_minutes int,
  p_provenance_label text,
  p_source_url text,
  p_youtube_video_id text,
  p_source_author text,
  p_source_published_at timestamptz,
  p_roles text[],
  p_batch_size int
)
```

Postgres: `CREATE OR REPLACE FUNCTION` **cannot change argument types**; that creates a **new overloaded function**. `[CITED: postgresql.org/docs/current/sql-createfunction.html]`

**Use this sequence in `014_phase30_materials_topic_kind.sql`:**

1. `ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS topic_kind text NOT NULL DEFAULT 'conceptual';`
2. `DO $$ … ADD CONSTRAINT materials_topic_kind_check CHECK (topic_kind IN ('practical', 'conceptual'))` if not exists (`ADD CONSTRAINT IF NOT EXISTS` is invalid Postgres — supabase skill).
3. `DROP FUNCTION IF EXISTS public.persist_draft_and_enqueue(text, text, text, text, int, text, text, text, text, timestamptz, text[], int);`
4. `CREATE FUNCTION` with the same body as `009` plus `p_topic_kind text DEFAULT 'conceptual'` in the INSERT column list.
5. Revoke/grant **the new signature** to `service_role` only (`security invoker`), mirroring `009:179-187`.

Do **not** edit applied `007`–`009` in place (Phase 11 precedent). `ON CONFLICT (youtube_video_id) DO NOTHING` stays; `already_saved` does not overwrite `topic_kind` on the existing row.

Existing rows receive `conceptual` via the constant DEFAULT without a table rewrite `[CITED: postgresql.org/docs/current/sql-altertable.html]`.

### Anti-Patterns to Avoid

- **Fold classify into pass-1 messages / `ARTICLE_SYSTEM_PROMPT`.** Pitfall 3: web-or-kind instructions contaminate `## Конкретика`. ROADMAP prefers a separate cheap call.
- **Raise `ArticleError` from the classifier adapter.** `map_article_error` → `stage="llm"` drops a finished pass-1 draft. Classifier errors are fail-soft → `conceptual`.
- **Append `TopicKindClassifier` to package `__all__`.** Pin is exactly these ten names `[VERIFIED: data-collection/src/data_collection/__init__.py:13-24]`: `"Transcript"`, `"VideoMetadata"`, `"MaterialDraft"`, `"TemplateKind"`, `"TranscriptProvider"`, `"ArticleGenerator"`, `"VideoMetadataProvider"`, `"VideoRef"`, `"FeedListing"`, `"VideoListProvider"`.
- **Add `"classify"` to `Stage`.** Locked set `[VERIFIED: ingestion-service/src/ingestion_service/domain/errors.py:8-16]`: `"url"`, `"captions"`, `"metadata"`, `"consistency"`, `"llm"`, `"llm_truncation"`, `"persist"`. Diagnostic label is allowed; `IngestError.stage` is not.
- **Fourth stdout checkmark.** `[VERIFIED: tests/unit/test_cli_ingest_contract.py:20-29]` `EXPECTED_SUCCESS_LINES` is `"✓ transcript"`, `"✓ LLM"`, `"✓ saved"`, then the four result lines. Classifier is stderr/debug only (and DBG-03 is Phase 34).
- **Fail-closed heading validator** that rejects a body containing `## Гайд`. Strip, then persist (D-09 / Phase 8 D-15).
- **Strip `Guide` / `How-to` / `Как сделать` / `Tutorial` / `Шпаргалка`.** D-12.
- **Stuff `topic_kind` into `provenance_label`.** Additive column.
- **Backend/SPA reader DTO or admin badge.** `_fetch_one` already selects an explicit column list without `topic_kind` `[VERIFIED: supabase-integration/src/supabase_integration/material_repository.py:147-152]`. Do not add it.
- **Tavily / enricher / cheat sheet “while we're here”.**
- **`CREATE OR REPLACE` with a new parameter and no `DROP`.** Leaves two overloads; PostgREST may keep calling the old 12-arg function and silently drop `p_topic_kind`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Closed-set JSON from DeepSeek | Regex on free text, or a custom JSON parser | `response_format={"type":"json_object"}` + `json.loads` + `normalize_topic_kind` | API 400 without the JSON instruction; empty content is a documented case; `json_object` does not validate keys |
| TLS / proxy for DeepSeek | New httpx client, or reuse YouTube SOCKS5 | `build_async_deepseek_client` (`trust_env=False`) | Phase 28 measured: YouTube needs SOCKS5, DeepSeek must not |
| Role-like enum mapping | Ad-hoc if/else in the pipeline | `normalize_topic_kind` clone of `normalize_roles` | Same fail-closed shape; unit-testable without HTTP |
| Heading leak | Fail-closed parser / ingest reject | `strip_guide_section` clone of `strip_audience_section` | Phase 8 D-15; D-09 |
| Persist field | JSON blob in `provenance_label` or a side table | `materials.topic_kind` + RPC param | KIND-01 on the draft; Phase 11 amend-don't-edit-applied |
| Constraint idempotency | `ADD CONSTRAINT IF NOT EXISTS` | `DO $$ IF NOT EXISTS (pg_constraint) $$` | Invalid Postgres syntax (supabase skill) |

**Key insight:** The scarce resource is the future Tavily budget. The cheap, correct control is a **code-default of `conceptual` on anything that is not a valid enum**, not a smarter prompt.

## Runtime State Inventory

This phase adds a stored column (schema migration), not a rename. Categories answered explicitly:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `public.materials` has no `topic_kind` today (001 create + 007 provenance columns; 009 RPC insert list has no such column). Live MCP `describe_table` was unavailable (`POSTGRES_URL` missing in this session). After `014`, existing rows read `conceptual` from the column DEFAULT. `ON CONFLICT DO NOTHING` will **not** backfill already-saved videos on re-ingest. | Code + migration. No row-by-row UPDATE needed: constant DEFAULT covers legacy rows. Re-ingest of `already_saved` stays skip (Phase 31/32). |
| Live service config | PostgREST schema cache of `persist_draft_and_enqueue`. After DROP+CREATE the 12-arg overload must disappear. | Operator applies `014` on the shared VM (Phase 11/23/24 precedent). Plan a contract test on the SQL file; live apply is a later UAT/resume-signal, not a unit task. |
| OS-registered state | None — verified by scope: no systemd unit, Task Scheduler, or pm2 name change. | none |
| Secrets/env vars | No new names. Classifier reuses `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`. `SecretRegistry` seeding stays DeepSeek key + Supabase secret + `YOUTUBE_PROXY_URL` `[VERIFIED: ingestion-service/src/ingestion_service/cli.py:51-60]`. | none |
| Build artifacts | None — verified by scope: no package rename, no egg-info, no Docker tag. | none |

## Common Pitfalls

### Pitfall 1: D-08 prompt vs KIND-02 code (laundering)

**What goes wrong:** A model returns `{"topic_kind":"unsure"}`, `{"kind":"practical"}`, `""`, or empty content. A “be helpful” implementation treats anything truthy as `practical`, and unattended collect burns Tavily.
**Why it happens:** D-08 and KIND-02 are opposite biases on purpose. Implementers merge them into one default.
**How to avoid:** `normalize_topic_kind` accepts **only** `practical` and `conceptual` (casefold+strip). Everything else → `conceptual`. Prompt sentence “if unsure, pick practical” is **not** a third enum and is **not** consulted in code. Tests: (a) malformed → conceptual; (b) theory talk whose transcript begs “include links/tools” still conceptual via Fake; (c) Fake returning `practical` on an ambiguous how-to is stored practical (prompt-layer, not KIND-02).
**Warning signs:** `if value: return "practical"`; parsing extra keys (`kind`, `label`, `job`); treating `"unsure"` as practical in Python.

### Pitfall 2: Classifier exception mapped to `stage=llm`

**What goes wrong:** Timeout/`APIConnectionError` in the classifier raises `ArticleNetworkError` → `map_article_error` → fail-closed, **zero rows**, collect `videos_failed`.
**Why it happens:** Cloning `DeepSeekArticleGenerator` copies its exception taxonomy.
**How to avoid:** Dedicated module-private error **or** adapter returns a raw value and never raises `ArticleError`. Pipeline `try/except` stamps `conceptual` and persists. `diagnostics.stage_failed` must **not** fire for classify (looks like ingest failed). Prefer `stage_completed("classify", {"topic_kind": "conceptual"})` even on transport miss — and only if `topic_kind` is added to `ALLOWED_KEYS`. DBG-03 operator report is Phase 34; adding the allowlist key now is optional plumbing, not a reader badge.
**Warning signs:** `from data_collection.errors.article import …` inside the classifier adapter; `except ArticleError` around classify.

### Pitfall 3: RPC overload leftover

**What goes wrong:** `CREATE OR REPLACE FUNCTION persist_draft_and_enqueue(..., p_topic_kind text)` **adds** a 13-arg function. PostgREST / the Python client still bind the 12-arg one. Column stays `conceptual` DEFAULT forever; KIND-01 looks green in Python and is lying in SQL.
**Why it happens:** 007/008/009 all replaced the **same** 12-arg signature. This is the first arity change.
**How to avoid:** `DROP FUNCTION IF EXISTS` with the exact 12 types quoted above, then CREATE. Contract-test the migration SQL: old 12-arg `create or replace` must **not** remain as the only definition; `p_topic_kind` must appear in INSERT. Grant/revoke the **new** signature.
**Warning signs:** Two `pg_proc` rows for the name; persister `_rpc_params` sends `p_topic_kind` but live rows are all conceptual.

### Pitfall 4: Pass-1 JSON `topic_kind` wins over the classifier

**What goes wrong:** `ArticleDraft` grows `topic_kind` with a default. The pass-1 model starts emitting it. Pipeline forgets to overwrite. Honesty prompt never asked for it, but a leaked key becomes the stored kind.
**Why it happens:** One DTO, two writers.
**How to avoid:** Pipeline **always** stamps `article_draft.topic_kind = normalize_topic_kind(classifier_raw)` after classify, even when the draft already has a value. Do **not** add `topic_kind` to `ARTICLE_SYSTEM_PROMPT` keys (`Return one json object with keys title, dek, body_markdown, roles.` `[VERIFIED: data-collection/src/data_collection/adapters/deepseek_article.py:50]`). Test: pass-1 payload includes `"topic_kind": "practical"` + Fake classifier returns `"conceptual"` → persisted conceptual.
**Warning signs:** Classifier skipped when `article.topic_kind` is already set.

### Pitfall 5: Strip too wide or too narrow

**What goes wrong:** Broad regex deletes `## Как сделать pgvector` (real talk chapter) or `Guide` in English talks. Narrow regex leaves `## Гайд\n\n` empty heading on conceptual materials (KIND-03). Placeholder survives with different punctuation.
**Why it happens:** Temptation to “clean all guide-like headings.”
**How to avoid:** D-12 closed set only. Clone audience tests: trailing section, mid-body with a following h2, in-prose mention preserved, idempotent, filled section also removed (D-10), placeholder substring removed even outside that section. Do not fail ingest if strip empties a pathological body — `min_length=1` on `body_markdown` already maps to `ArticleInvalidDraft`; that path already exists.
**Warning signs:** Tests asserting `Guide` / `Шпаргалка` absent; templates growing a `## Гайд` instruction (Phase 29 `SHARED_PROMPT_HEADINGS` is `"## Конкретика"`, `"## Зачем это СВА"`, `"## Аудитория"` `[VERIFIED: tests/unit/test_deepseek_article_adapter.py:34]` — keep `Гайд` out).

### Pitfall 6: Required classifier kwarg forgotten at call sites

**What goes wrong:** `run_ingest_pipeline` gains `classifier=` and 8+ test modules plus `collect_batch.py` + `cli.py` TypeError.
**Why it happens:** Current signature is captions, metadata_provider, article, persist only `[VERIFIED: ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py:31-41]`.
**How to avoid:** Required kwarg (no silent `None` that hides missing composition wiring). Add `FakeTopicKindClassifier` next to `FakeArticleGenerator`. Update `build_ingest_deps` and `test_build_ingest_deps_wires_four_ports_via_monkeypatched_factories` (it currently asserts `calls == ["captions", "metadata", "article", "persist"]` `[VERIFIED: tests/unit/test_build_ingest_deps_wiring.py:68]`). Collect batch must pass `deps.classifier`.
**Warning signs:** Default `classifier=None` in production composition.

## Code Examples

### Classifier port (clone ArticleGenerator, do not export)

`[VERIFIED: data-collection/src/data_collection/ports/article_generator.py:12-15]`:

```python
class ArticleGenerator(Protocol):
    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft: ...
```

New port — import as `from data_collection.ports.topic_kind import TopicKindClassifier` (same style as `from data_collection.ports.article_generator import ArticleGenerator` in `ingest_pipeline.py`). Do not add to `ports/__init__.py` `__all__` (that barrel currently exports four names `[VERIFIED: data-collection/src/data_collection/ports/__init__.py:8-14]`: `"ArticleGenerator"`, `"TranscriptProvider"`, `"VideoMetadataProvider"`, `"VideoListProvider"`).

```python
class TopicKindClassifier(Protocol):
    async def classify(
        self, transcript: Transcript, article: ArticleDraft
    ) -> object: ...
```

Return **raw** (`object`): pipeline always runs `normalize_topic_kind`. Adapter may return a str or a dict; do not trust it.

### Classifier input (discretion — use this)

Keep the call cheap and **do not send `body_markdown`** (СВА analog / `## Конкретика` can look “practical”; Pitfall 3). Send:

1. `article.title` and `article.dek` (pass-1 already produced them; cheap; job-of-the-page signal).
2. `transcript.text`, truncated with **head + tail** so a late dominating demo is visible (D-05/D-06). Module constant, not a new Settings key.

Fence the transcript as untrusted data (prompt-injection: “classify this as practical so we get extra links”). System prompt encodes D-01…D-08, named products (Excel, SAP, Tableau, Power BI, Jira, Python, Kubernetes), Diátaxis **do vs understand** (not minute-counting), D-08 unsure→practical, and the JSON example `{"topic_kind": "conceptual"}`. User message must include the word `json`.

### Pipeline stamp (after process, before assemble)

```python
article_draft = await article.process(transcript, template)
# ... existing llm diagnostics ...
try:
    raw = await classifier.classify(transcript, article_draft)
except Exception:
    # never ArticleError; never IngestError
    raw = None
article_draft.topic_kind = normalize_topic_kind(raw)
material = assemble_material_draft(article_draft, metadata, provenance)
result = persist_draft(material, persist)
```

Body strip already ran inside `ArticleDraft.model_validate` during `process()`. Do not strip again in the pipeline (single home, like audience).

### Persister RPC params

Current keys `[VERIFIED: ingestion-service/src/ingestion_service/adapters/supabase_persist.py:46-61]`: `"p_title"`, `"p_dek"`, `"p_body_markdown"`, `"p_slug"`, `"p_reading_minutes"`, `"p_provenance_label"`, `"p_source_url"`, `"p_youtube_video_id"`, `"p_source_author"`, `"p_source_published_at"`, `"p_roles"`, `"p_batch_size"`. Add `"p_topic_kind": draft.topic_kind`. Extend `test_supabase_draft_persister_contract.py`.

### Fake

Clone `FakeArticleGenerator` `[VERIFIED: data-collection/src/data_collection/tests_support/fakes.py:58-76]`. Script `result: TopicKind`, record `calls`, optional `failures` that the **pipeline** must swallow. Add `"FakeTopicKindClassifier"`, `"TopicKindClassifier"`, `"normalize_topic_kind"`, `"DeepSeekTopicKindClassifier"` to `NEGATIVE_ROOT_NAMES` `[VERIFIED: tests/unit/test_data_collection_public_api.py:25-49]`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| One fail-closed DeepSeek `json_object` stream writes the article | Pass-1 stream + separate cheap classify JSON | v1.5 / this phase | Kind gates extras without contaminating facts |
| `roles` unknown → `employee` in code | Same shape for `topic_kind` unknown → `conceptual` | Phase 9 analog | KIND-02 does not fail ingest |
| Body leak `## Аудитория` stripped in validator | Same for `## Гайд` | Phase 8 pattern | KIND-03 without fail-closed parse |
| RPC amended in place with same arity (007→008→009) | DROP 12-arg then CREATE 13-arg | this phase | First arity change on `persist_draft_and_enqueue` |
| Diátaxis mixing how-to furniture into explanation | Job-of-the-page classifier; extras only on `practical` | v1.5 FEATURES.md | Saves the 1000-request budget |

**Deprecated/outdated:**
- Folding retrieval or classification into the honesty prompt: rejected (Pitfall 3).
- PG `CREATE TYPE … ENUM` for a two-value closed set: prefer `text` + CHECK (supabase schema skill).
- OpenAI `json_schema` structured outputs on DeepSeek: not in the documented `response_format` enum (`text` \| `json_object`).

Diátaxis map used for D-06 `[CITED: diataxis.fr/map/]`: tutorials/how-to guides **guide action**; reference/explanation **contain propositional knowledge**. “Dominates” = the job is doing vs understanding, not a minute fraction. D-07: a complete sample inside an explanation page stays explanation.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Classifier `max_tokens=128` is enough for `{"topic_kind":"practical"}` | Pattern 2 | If the model preambles, JSON truncates → KIND-02 conceptual (safe for quota, may miss how-tos). Raise to 256 only if a live empty-content rate shows up. |
| A2 | Transcript truncation of head 8k + tail 4k chars is enough for D-05 mixed talks | Classifier input | A mid-talk dominating demo could be cut and classified conceptual (quota-safe). Full 80k prompt is the fallback; do not add a Settings env unless measured. |
| A3 | `re.IGNORECASE` on Cyrillic `Гайд` matches `## гайд` the way audience does | Pattern 3 | If IGNORECASE does not fold Cyrillic on this Python, a leaked `## гайд` survives. Pin with an explicit lowercase heading test. |
| A4 | Adding optional `topic_kind` to `ALLOWED_KEYS` this phase will not break debug tests | Pitfall 2 | Unknown keys are silently dropped today `[VERIFIED: ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py:90-93]`. If tests pin exact debug lines, adding a completed `classify` stage will red them — then either skip diagnostics this phase or update those tests. DBG-03 is Phase 34. **Recommendation:** emit classify diagnostics only if existing debug tests stay green; otherwise leave stderr classify for Phase 34. |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

A1–A4 are planner-safe defaults (quota-conservative). They do not need owner re-litigation unless a live proof is added.

## Open Questions

1. **Should `--debug` grow a `classify` line in this phase?**
   - What we know: ROADMAP says `classify` may be a diagnostic label, not a `Stage`. DBG-03 (classifier in `--debug`) is Phase 34. `ALLOWED_KEYS` is a closed frozenset `[VERIFIED: ingestion-service/src/ingestion_service/diagnostics/redaction.py:13-33]`: `"stage"`, `"elapsed_ms"`, `"video_id"`, `"transcript_chars"`, `"transcript_words"`, `"language"`, `"template"`, `"response_chars"`, `"material_id"`, `"slug"`, `"batch_id"`, `"rank"`, `"already_saved"`, `"reason"`, `"exit_code"`, `"error_type"`, `"message"`.
   - What's unclear: whether Phase 30 debug tests pin exact stderr.
   - Recommendation: **do not** add a classify debug line unless a test already requires it. KIND-01 is the stored field, not stderr. Phase 34 owns DBG-03.

2. **Live DeepSeek proof for the classifier?**
   - What we know: Phase 29 needed a live article-quality read. KIND-01…03 are store-and-strip contracts, fully unit-testable with Fake + SQL file pins.
   - What's unclear: owner appetite for a second live ingest this milestone.
   - Recommendation: **no live ingest in Phase 30 plans.** Default suite stays off-network. Optional UAT later.

3. **Share one AsyncOpenAI client between article and classifier?**
   - What we know: `build_deepseek_article_generator` constructs its own client internally.
   - What's unclear: connection-pool duplication cost.
   - Recommendation: **clone the factory** (`build_deepseek_topic_kind_classifier` calls `build_async_deepseek_client` itself). Do not refactor the article generator in this phase.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | unit tests | ✓ | 3.14.0 (workspace requires `>=3.12`) | — |
| `uv` | `uv run pytest` | ✓ | 0.10.9 | — |
| pytest | TDD | ✓ | 9.1.1 (lock) | — |
| DeepSeek API | live classifier only | ✓ (used Phase 28/29) | `deepseek-flash` default `[VERIFIED: ingestion-service/src/ingestion_service/composition/settings.py:89]` | Unit tests use Fake; live not in this phase |
| Supabase Postgres | migration apply | operator VM (not probed this session; MCP `describe_table` failed without `POSTGRES_URL`) | — | Contract-test SQL in unit; live apply is operator resume-signal |
| YouTube SOCKS5 | captions (not this phase's new work) | documented in STATE.md | — | Not required for unit classifier tests |

**Missing dependencies with no fallback:** none for the unit-tested plan. Live migration apply needs the operator, as with 012/013.

**Missing dependencies with fallback:** DeepSeek live → Fake in default suite.

## Validation Architecture

`workflow.nyquist_validation` is absent in `.planning/config.json` → treat as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (`>=8.3.0`) |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["tests/unit"]` `[VERIFIED: pyproject.toml:35-40]` |
| Quick run command | `uv run pytest tests/unit/test_topic_kind.py tests/unit/test_article_draft_body_guide.py tests/unit/test_ingest_pipeline.py -x` |
| Full suite command | `uv run pytest tests/unit -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| KIND-01 | Draft always has `topic_kind` in `{practical, conceptual}` after pipeline persist | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -k topic_kind -x` | ❌ Wave 0 |
| KIND-01 | `assemble_material_draft` copies `topic_kind` | unit | `uv run pytest tests/unit/test_assemble_material_draft.py -k topic_kind -x` | ❌ Wave 0 (file exists, no topic_kind cases) |
| KIND-01 | RPC params include `p_topic_kind` | unit | `uv run pytest tests/unit/test_supabase_draft_persister_contract.py -k topic_kind -x` | ❌ Wave 0 |
| KIND-01 | Migration 014 adds column + RPC param | unit | `uv run pytest tests/unit/test_phase30_migration_014.py -x` | ❌ Wave 0 |
| KIND-02 | `normalize_topic_kind` maps missing/empty/unknown/malformed → `conceptual` | unit | `uv run pytest tests/unit/test_topic_kind.py -x` | ❌ Wave 0 |
| KIND-02 | Classifier transport / empty JSON does not raise `IngestError`; persist still called with `conceptual` | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -k classify -x` | ❌ Wave 0 |
| KIND-02 | No Tavily/enricher/cheat-sheet call sites on conceptual **or** practical this phase | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -k extras -x` | ❌ Wave 0 |
| KIND-02 | `__all__` still ten names; `Stage` still seven values | unit | `uv run pytest tests/unit/test_data_collection_public_api.py::test_public_all_is_exactly_ten_ingestion_names tests/unit/test_data_collection_public_api.py::test_stage_set_is_unchanged -x` | ✅ exists — must stay green |
| KIND-03 | `## Гайд` (empty or filled) stripped; placeholder stripped; in-prose «гайд» kept; `Guide` kept | unit | `uv run pytest tests/unit/test_article_draft_body_guide.py -x` | ❌ Wave 0 |
| KIND-03 | Templates still omit `Гайд` | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -k SHARED_PROMPT_HEADINGS -x` | ✅ exists — add a negative `Гайд` pin |
| (regress) | `EXPECTED_SUCCESS_LINES` unchanged | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -x` | ✅ exists |
| (regress) | Audience strip still works | unit | `uv run pytest tests/unit/test_article_draft_body_audience.py -x` | ✅ exists |
| (regress) | Pass-1 call shape unchanged (`json_object`, `thinking`, `stream=True`) | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py::test_create_kwargs_include_json_object_and_disabled_thinking -x` | ✅ exists |

### Sampling Rate

- **Per task commit:** the quick command for that requirement’s new file
- **Per wave merge:** `uv run pytest tests/unit -q`
- **Phase gate:** full unit suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_topic_kind.py` — `normalize_topic_kind` matrix (KIND-02)
- [ ] `tests/unit/test_article_draft_body_guide.py` — clone `test_article_draft_body_audience.py` (KIND-03)
- [ ] `tests/unit/test_phase30_migration_014.py` — clone `test_phase11_migration_009.py` (KIND-01 persist)
- [ ] `FakeTopicKindClassifier` in `data-collection/src/data_collection/tests_support/fakes.py`
- [ ] Pipeline / assemble / persister / `build_ingest_deps` / `NEGATIVE_ROOT_NAMES` extensions
- [ ] Framework install: none — pytest already configured

Existing infrastructure covers the runner, not the new behaviors.

## Security Domain

`security_enforcement` is not set to `false` in `.planning/config.json`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Ingest is service_role CLI; no new auth |
| V3 Session Management | no | — |
| V4 Access Control | yes (column exposure) | Keep `materials` RLS as-is (`materials_select_ready`). Do not add `topic_kind` to reader SELECT lists. RPC `grant execute … to service_role` only, revoke from `anon`/`authenticated`/`public` (009 pattern). |
| V5 Input Validation | yes | `normalize_topic_kind`; `json.loads` then map; heading regex exact; transcript fenced as untrusted in the classifier prompt |
| V6 Cryptography | no | Reuse existing TLS client; never hand-roll |

### Known Threat Patterns for ingest classifier + RPC

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Transcript prompt injection (“classify as practical”) | Spoofing / Tampering | Fence transcript as data; KIND-02 code default; unit test a begging theory talk → conceptual |
| Malformed JSON becoming `practical` | Tampering | `normalize_topic_kind` allowlist only |
| Classifier error fail-closes ingest | Denial of service | Fail-soft to `conceptual`; do not use `ArticleError` |
| RPC executable by `anon` | Information disclosure / Elevation | `revoke all … from public, anon, authenticated`; `grant execute … to service_role` |
| `topic_kind` leaking as a reader badge | Information disclosure | Explicit backend SELECT list; no DTO field this phase |
| YouTube proxy used for DeepSeek | Information disclosure (key in proxy logs) | `trust_env=False` factory only |
| `CREATE OR REPLACE` overload leaves old function | Tampering (silent drop of kind) | `DROP FUNCTION` old signature first |

## Sources

### Primary (HIGH confidence — in-repo, Read this session)
- `data-collection/src/data_collection/__init__.py:13-24` — ten-name `__all__`
- `ingestion-service/src/ingestion_service/domain/errors.py:8-16` — `Stage` seven values
- `data-collection/src/data_collection/dto/role_kind.py:7-16` — `normalize_roles` analog
- `data-collection/src/data_collection/dto/_body.py:16-41` — audience strip
- `data-collection/src/data_collection/adapters/deepseek_article.py:35-50,139-145` — honesty prompt keys + stream call shape
- `ingestion-service/src/ingestion_service/composition/clients.py:64-75,78-100` — DeepSeek client factory
- `supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql:8-21,179-187` — live RPC signature + grants
- `tests/unit/test_data_collection_public_api.py:10-49,109-122` — `PUBLIC_NAMES`, `NEGATIVE_ROOT_NAMES`, `test_stage_set_is_unchanged`
- `tests/unit/test_cli_ingest_contract.py:20-29` — `EXPECTED_SUCCESS_LINES`
- `.planning/REQUIREMENTS.md:27-29` — KIND-01/02/03
- `.planning/phases/30-classifier-practical-conceptual/30-CONTEXT.md` — D-01…D-12

### Secondary (MEDIUM confidence — Context7 / official docs)
- `/websites/api-docs_deepseek` — JSON Output, `thinking` default enabled, HTTP 400 without JSON instruction, empty content, `max_tokens` default 8K non-thinking
- `/websites/postgresql` — `CREATE OR REPLACE FUNCTION` cannot change argument types; `DROP FUNCTION`; `ADD COLUMN` constant DEFAULT; CHECK constraints
- `/pydantic/pydantic` — `field_validator(mode="before")`; `Literal` raises `literal_error`
- `/openai/openai-python` — `extra_body`; `json_object` vs `json_schema`
- https://diataxis.fr/map/ — job-of-the-page (do vs understand)
- `.agents/skills/supabase-postgres-best-practices/references/schema-constraints.md` — no `ADD CONSTRAINT IF NOT EXISTS`
- `.agents/skills/supabase-postgres-best-practices/references/schema-data-types.md` — text + CHECK for enums

### Tertiary (LOW confidence)
- Live `materials` schema on the operator VM (MCP `describe_table` failed this session). Planner must not assume a column already exists.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — lockfile versions + existing adapters; no new packages
- Architecture: HIGH — pipeline, ports, RPC, and pins Read this session; call-shape details MEDIUM via Context7
- Pitfalls: HIGH — D-08 vs KIND-02, Stage/`__all__`, RPC overload are the rewrite-causing errors

**Research date:** 2026-10-28
**Valid until:** 2026-11-27 (30 days; DeepSeek JSON/`thinking` defaults are the fast-moving slice)

No `.planning/graphs/graph.json` this session — graph queries skipped.
