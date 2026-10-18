# Phase 8: DeepSeek Article & Templates - Research

**Researched:** 2026-09-27
**Domain:** DeepSeek article adapter behind the Phase 6 `ArticleGenerator` port; repository `lecture.md` / `podcast.md`; fail-closed `stage=llm` / `stage=llm_truncation`; always-Russian prompt contract — no Typer one-shot, no persist, no new `IngestError` stage
**Confidence:** HIGH (CONTEXT D-01…D-17 + LLM-01…LLM-05 + Phase 6/7 contracts verified in tree; OpenAI SDK 3.19.2 + DeepSeek JSON mode / `deepseek-flash` / thinking-default via Context7 and PyPI); MEDIUM (exact HTTP body field DeepSeek uses for a context-length **rejection** — docs page is client-rendered; disable-thinking `extra_body` is the inverse of the documented enable switch); LOW (none blocking)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Output language
- **D-01:** Output is always Russian. Supersedes REQUIREMENTS.md / ROADMAP wording "output language matches the transcript language" (updated 2026-09-27 in `.planning/REQUIREMENTS.md` LLM-04 and `.planning/ROADMAP.md` Phase 8 criterion 4). — **Reversibility:** costly — Phase 10 UAT and the provenance marker assume Russian drafts; restoring "match transcript" rewrites the prompt contract and those checks.
- **D-02:** `ru` transcript: format only, do not translate. `en` transcript: translate to Russian. Preserve technical terms, proper names, library names, numbers, and units as written (tests keep `pgvector` / `RAG` / `embedding` unchanged).
- **D-03:** No runtime language detector. Wrong-language drafts are caught in admin preview (Phase 5), not by a heuristic fail-closed check. Fail-closed stays limited to clear-cut cases (network, HTTP errors, invalid JSON, schema validation, context budget).
- **D-04:** Phase 8 tests both paths: `ru` format-only with terms preserved; `en` translated to Russian with terms preserved. Tests assert the prompt rules and scripted drafts, not a language-ID of the reply.
- **D-05:** Phase 8 locks the marker string only. Phase 10 caller builds `label = f"YouTube · {metadata.author}"` and, when `transcript.language != "ru"`, appends ` · пер. с англ.` (middot separator, trailing period). Example: `YouTube · Сбер Pro · пер. с англ.` The Phase 6 assembler copies `provenance_label` as-is and does not invent it. — **Reversibility:** costly — the string is the operator-visible provenance contract once Phase 10 persists it.
- **D-06:** v1.1 marker map is English only. The only non-`ru` suffix is ` · пер. с англ.` Phase 7 only emits `ru` or `en`.

#### Context budget
- **D-07:** Character cap on `Transcript.text` only. `MAX_TRANSCRIPT_CHARS` defaults to `80000` and is env-configurable. Unset or blank uses `80000`. A non-integer, zero, or negative value fails when settings load, before any video (config error, not `llm_truncation`). — **Reversibility:** reversible — the default and env name are local operator config.
- **D-08:** Before any DeepSeek call, `len(transcript.text) > MAX_TRANSCRIPT_CHARS` raises `IngestError(stage="llm_truncation")`. Template text and the system prompt do not count. No tokenizer. No silent truncation. No chunking.
- **D-09:** Local cap reason is `transcript_too_long`. Context is only `char_count` and `max_chars`. No transcript text in the error.
- **D-10:** If DeepSeek itself rejects the request for context length, that is `stage=llm`, `reason=provider_context_length`, not `llm_truncation`. — **Reversibility:** costly — `reason` joins the operator diagnostic contract shared with Phases 7–10.

#### Model reply
- **D-11:** The model returns one JSON object: `{"title","dek","body_markdown"}`. Request it with `response_format={"type":"json_object"}`. Parse with `json.loads`, then `ArticleDraft`. Extra keys are ignored. Markdown fences or surrounding prose are `invalid_json` — do not strip fences and do not extract the first `{...}`. Markdown inside `body_markdown` is article content, not the response format. — **Reversibility:** costly — `ArticleDraft` and LLM-03 tests depend on this object shape.
- **D-12:** `ArticleGenerator.process` returns `ArticleDraft` only. Provenance stays out of the JSON and out of the adapter (Phase 6 D-06). LLM-01's "validated MaterialDraft" is the existing assembler plus the Phase 10 label, not fields the model emits.
- **D-13:** `stage=llm` reason set: `network_error` (timeout, DNS, connection refused — before a DeepSeek response), `provider_error` (HTTP 5xx and 429), `auth_error` (HTTP 401 and 403), `invalid_json` (`json.loads` fails, or JSON is not an object), `invalid_article_draft` (`ArticleDraft` fails: missing or blank field), `provider_context_length`, `unknown_llm_error` (anything else). SDK exception class names stay out of `reason`. No partial `ArticleDraft`. No transcript text in context. — **Reversibility:** costly — same operator JSON contract as the captions reason set.

#### Lecture vs podcast
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

### Deferred Ideas (OUT OF SCOPE)
- Per-language translation marker beyond `en` (wait until captions accept more languages)
- Looser podcast voice (v1.2+). v1.1 keeps one neutral editorial voice
- Heading checks inside `body_markdown` (fix the prompt if the model drops headings; do not add a validator)
- Runtime language detection of the model reply
- Chunking / silent truncation of long transcripts
- Typer one-shot, provenance assembly at the CLI, and live UAT — Phase 10
- Persist, shortlist, and live zero-row proof — Phase 9
</user_constraints>

## Project Constraints (from .cursor/rules/ + AGENTS.md)

| Directive | Implication for Phase 8 |
|-----------|-------------------------|
| Ports & Adapters (`architecture.mdc`) | `openai` SDK only inside the DeepSeek adapter and the composition factory that builds the client. `ArticleGenerator.process` stays the port. No SDK in domain. Ingestion mapping turns adapter errors into `IngestError`; it does not call DeepSeek. |
| Dependencies point inward | `data-collection` does not import `ingestion_service` or `IngestError`. The adapter raises module-local errors. The mapper in `ingestion-service` owns `stage=llm` / `stage=llm_truncation`. |
| No deep-imports across modules | Public `data_collection.__all__` stays the seven Phase 6/7 names. `ArticleDraft`, fakes, the new adapter, and article errors stay off the package root (existing negative test). Ingestion may import `data_collection.errors.*` the same way captions/metadata mappers already do. |
| No `Any` on ports | Port signature stays `process(transcript: Transcript, template: TemplateKind) -> ArticleDraft`. Injected client is an adapter constructor detail, not a port field. |
| TDD Red–Green–Refactor (`tdd.mdc`, `AGENTS.md`) | Failing unit tests first for settings, template load, mocked adapter, error mapping, and fake failure scripts. Then minimal production code. |
| Python deps via `uv` (`python-uv.mdc`) | `uv add --package data-collection "openai>=3.0,<4"`. Do not pip-install. |
| Frontend | No `web/` changes. No `VITE_` secret. |
| Unit tests without network/DB | Mock the injected client. Optional live call is `@pytest.mark.integration` and is not the phase gate (`testpaths = ["tests/unit"]`). |
| D-CONTENT-01 | Transcript is not a material. This phase returns `ArticleDraft` only. |
| ADR-0002 bend | DeepSeek is the temporary public-LLM bend. Do not add FoundryModels or Whisper. |
| Project skills (`.agents/skills`) | `hallmark` and Supabase skills do not apply (no UI, no schema). Context7 was used for the OpenAI SDK and DeepSeek API docs. |
| Composition injects clients | Adapters never read `os.environ` / `os.getenv`. Existing `test_adapters_do_not_read_environ` globs `data_collection/adapters/*.py` and will cover the new file automatically. |

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LLM-01 | DeepSeek via an OpenAI-compatible SDK returns a validated `MaterialDraft` (`title`, `dek`, `body_markdown`, provenance fields) | **Superseded in implementation by D-12.** Adapter returns validated `ArticleDraft` only. Provenance is not in the JSON. Existing `assemble_material_draft` copies a caller-supplied label. Phase 10 builds the label (D-05). Do not add provenance fields to the model reply. |
| LLM-02 | Operator can choose `--template lecture\|podcast` backed by repository markdown templates | **This phase:** `TemplateKind` selects `lecture.md` or `podcast.md`; the chosen file's D-16 headings are in the prompt. **Phase 10:** Typer `--template`. Do not build the CLI here. |
| LLM-03 | Network, 5xx, invalid JSON, validation exit non-zero with `stage=llm`, zero database rows, no partial output | Adapter raises `ArticleError` and never returns `ArticleDraft`. Mapper emits `IngestError(stage="llm", reason∈D-13)`. **This phase:** unit proof only. Live zero-row spy waits for persist (Phase 9), same split as Phase 7 D-14. |
| LLM-04 | Honesty + always Russian (`ru` format-only, `en` translated); preserve terms/names/numbers/units; caller appends a translation marker when `language != "ru"` | Shared system prompt states the rules (D-01…D-04). Tests assert prompt text and scripted drafts (`pgvector` / `RAG` / `embedding`), not a language detector (D-03). Phase 8 locks the suffix ` · пер. с англ.` only (D-05/D-06). |
| LLM-05 | Over-budget transcripts fail closed with `stage=llm_truncation` and no silent truncation | `len(transcript.text) > MAX_TRANSCRIPT_CHARS` (default 80000) before the SDK call. Reason `transcript_too_long`. Context only `char_count` and `max_chars` (D-07…D-09). Provider rejection is a different reason (D-10). |

## Summary

Phase 8 is the LLM wave of v1.1 ingestion: a DeepSeek adapter in `data-collection` implements the existing async `ArticleGenerator` port, repository markdown supplies lecture vs podcast outlines, and `ingestion-service` maps failures onto the stages Phase 7 already reserved (`llm`, `llm_truncation`). The model emits three strings. The Phase 6 assembler plus a Phase 10 label is what LLM-01 calls a `MaterialDraft`.

**Critical planner overrides vs early milestone research and vs roadmap wording:**

1. Roadmap success criterion 1 says the SDK returns a `MaterialDraft` with provenance fields. **SUPERSEDED by D-12 / Phase 6 D-06.** `process` returns `ArticleDraft`. Do not put `provenance_label` in the JSON schema.
2. LLM-02 / roadmap criterion 2 mention `--template`. **The flag is Phase 10.** Phase 8 ships the files, the loader, and prompt selection by `TemplateKind`.
3. LLM-03 "zero database rows" is **unit-only this phase.** There is still no persist port. Mirror Phase 7 D-14: prove "no `ArticleDraft` returned"; schedule the spy for Phase 9.
4. Early `STACK.md` / `FEATURES.md` mention `prompt_version` on the draft. **Out of scope.** Phase 6 D-05 kept model ids off `MaterialDraft`. Do not add the field.
5. Early `PITFALLS.md` says retry 429/5xx. CONTEXT does not lock retries. **Recommend `max_retries=0`** on the injected client so one failure maps once. A bounded retry may be added in Phase 10 without changing reason codes. Do not retry HTTP 400.
6. Live model context is **1M tokens** (`deepseek-flash`, Context7 pricing table) and thinking mode **defaults on**. The local cap stays **80000 characters** (D-07). Do not raise the cap to match the window. Do not count tokens.

**Primary recommendation:** `uv add` official `openai` 3.x on `data-collection`; `AsyncOpenAI` injected with explicit timeout and `max_retries=0`; `chat.completions.create` with `response_format={"type":"json_object"}`, thinking disabled, and the word `json` in the prompt; `json.loads` then `ArticleDraft.model_validate`; module-local `ArticleError` subtypes mapped like captions; `Settings` owns `MAX_TRANSCRIPT_CHARS` plus DeepSeek key/base URL/model; package markdown under `data_collection/templates/`; extend `FakeArticleGenerator` with an optional failure map. No Typer, no Supabase, no new stage, no assembler change except a named marker constant the CLI will use later.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `ArticleGenerator` protocol | `data-collection` (exists) | — | Phase 6 D-16; do not change the signature |
| `ArticleDraft` | `data-collection/dto` (exists, not public) | Adapter validates with it | D-11/D-12 |
| `DeepSeekArticleGenerator` | `data-collection/adapters` | — | External SDK lives here |
| `ArticleError` taxonomy | `data-collection/errors` | ingestion mapper | Same split as `CaptionsError` (Phase 7 D-11/D-12) |
| `lecture.md` / `podcast.md` + loader | `data-collection/templates` | composition calls loader at startup | D-16/D-17; ARCHITECTURE.md prefers templates next to the adapter |
| Shared system prompt text | adapter module (constant or builder) | tests inspect messages sent to the client | D-14; one voice for both templates |
| `MAX_TRANSCRIPT_CHARS`, key, base URL, model | `ingestion-service` `Settings.from_env` | factory receives plain values | D-07; adapters do not read env |
| Char-cap check | adapter `process`, first line, using injected int | mapper emits `IngestError` | Before SDK call (D-08); data-collection must not import `IngestError` |
| Map `ArticleError` → `IngestError` | `ingestion-service/mapping` | — | D-09/D-10/D-13 |
| Marker string constant | `ingestion-service` (name only) | Phase 10 builds the full label | D-05; assembler unchanged |
| `FakeArticleGenerator` failure scripts | `tests_support/fakes.py` | unit tests | Phase 6 D-17; not in `__all__` |
| `assemble_material_draft` | exists | do not teach it to invent labels | D-12 / Phase 6 D-07 |
| Typer `--template`, label assembly, UAT | Out of scope | Phase 10 | CONTEXT boundary |
| Persist / zero-row spy | Out of scope | Phase 9 | CONTEXT boundary |
| New `IngestError` stage | Forbidden | stages already include `llm` and `llm_truncation` | D-17 / phase boundary |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `openai` (official) | **3.19.2** on PyPI 2026-09-27; pin `>=3.0,<4` `[VERIFIED: PyPI JSON; STACK.md]` | `AsyncOpenAI`, chat completions, JSON mode, exception types | Locked OpenAI-compatible SDK. DeepSeek sample uses this client `[CITED: Context7 /websites/api-docs_deepseek]` |
| DeepSeek Chat Completions | `base_url=https://api.deepseek.com` (no `/v1` in the official sample), model **`deepseek-flash`** | Transcript → JSON article | `[CITED: Context7 json_mode + pricing]` |
| `httpx2` | transitive `httpx2>=2.12,<3` | SDK HTTP stack | Do not import in app code. Different distribution from workspace `httpx==0.28.1` `[VERIFIED: PyPI requires_dist]` |
| Pydantic v2 | `2.13.5` (lock) | Existing `ArticleDraft` | Extra keys ignored by default (no `extra="forbid"` on the model) |
| pytest | `9.1.1` | Unit tests | `tests/unit` only |
| `json` / `importlib.resources` | stdlib | Parse reply; read package markdown | D-11 forbids fence-stripping helpers |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest.mock` / tiny async fakes | stdlib | Stub `client.chat.completions.create` | Every CI test |
| Existing `Settings.from_env(environ=...)` | in tree | Add fields without breaking `from_env({})` | D-07 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Official `openai` 3.x → DeepSeek | Raw `httpx`, LangChain, `chat.completions.parse` / JSON schema | **Forbidden** — D-11 is `response_format` `json_object` + `json.loads` + `ArticleDraft`. Schema parse is a different contract. Early STACK fallback `openai==2.11.0` is a **lockfile contingency only** if `uv` cannot resolve `httpx2`, not a design option. |
| `AsyncOpenAI` | Sync `OpenAI` + `asyncio.to_thread` | Port is already async. The async client matches it. YouTube needed `to_thread` because that SDK is sync. |
| Local 80000-char cap | Tokenizer or the 1M window | Violates D-07/D-08. Window growth does not relax the cap. |
| Thinking mode left at default (on) | `extra_body={"thinking": {"type": "disabled"}}` | **Recommend disable.** Pricing table: thinking is the default `[CITED: Context7]`. D-11 reads `message.content` only. Do not mine `reasoning_content`. |
| Retry 429/5xx inside the adapter | `max_retries=0` | CONTEXT has no retry lock. SDK default is **2** retries and **10 minute** timeout `[CITED: Context7 README]`. Unbounded or default retries fight LLM-03's single diagnostic. Phase 10 may add a bounded retry later. |
| Typer flag in this phase | Template loader + `TemplateKind` | CLI is Phase 10. |
| `IngestError` raised inside the adapter | `ArticleBudgetError` then mapper | Keeps stages out of `data-collection` (Phase 7 D-11) while still producing `stage=llm_truncation` (D-08). |

**Installation:**

```bash
uv add --package data-collection "openai>=3.0,<4"
uv sync
```

**Version verification:** `openai` is **not** in `uv.lock` today (expected). PyPI latest queried this session is `3.19.2`, requiring `httpx2` not `httpx`. Workspace `httpx==0.28.1`, `pydantic==2.13.5`, `pytest==9.1.1` stay. Confirm `uv lock` resolves once during execution; if it fails, stop and pin rather than switching SDKs silently.

## Package Legitimacy Audit

| Package | Registry | Age / reputation | Source Repo | Verdict | Disposition |
|---------|----------|------------------|-----------|---------|-------------|
| `openai` | PyPI | Official; Context7 High; 3.19.2 current | github.com/openai/openai-python | **PASS** | `>=3.0,<4` on `data-collection` |
| `httpx2` | transitive | SDK HTTP stack | — | **PASS** | Do not import; do not replace workspace `httpx` |
| `jiter`, `anyio`, `sniffio`, `typing-extensions` | transitive via openai | — | — | **PASS** | Via SDK only |
| LangChain / LiteLLM / community DeepSeek wrappers | — | — | — | **REJECT** | Extra abstraction; not the locked SDK |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none for this phase install list

## Architecture Patterns

### System Architecture Diagram

```text
Settings.from_env
  MAX_TRANSCRIPT_CHARS  (bad int → ConfigurationError, NOT IngestError)
  DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL
        |
        v
load_article_templates()   missing/unreadable → TemplateLoadError, NOT IngestError
        |
        | inject client + model + template strings + max_chars
        v
DeepSeekArticleGenerator.process(transcript, template)
  1. if len(transcript.text) > max_chars → ArticleBudgetError
     (SDK create is not called; template text is not counted)
  2. await client.chat.completions.create(
        model, messages, response_format=json_object,
        extra_body thinking disabled)
  3. json.loads(content) → dict → ArticleDraft
  4. any failure → ArticleError subtype, no ArticleDraft
        |
        v
ingestion_service.mapping.article
  ArticleBudgetError → IngestError(stage=llm_truncation, reason=transcript_too_long,
                                   context={char_count, max_chars})
  other ArticleError → IngestError(stage=llm, reason=locked D-13 code)

Phase 6 assembler (unchanged): ArticleDraft + VideoMetadata + caller label → MaterialDraft
Phase 9: failing generator + spy persist → persist.calls == []
Phase 10: Typer --template, label = f"YouTube · {author}" [+ " · пер. с англ." if language != ru]
```

### Recommended Project Structure

```text
data-collection/
  src/data_collection/
    adapters/deepseek_article.py     # NEW DeepSeekArticleGenerator + SYSTEM prompt builder
    errors/article.py                # NEW ArticleError hierarchy
    templates/lecture.md             # NEW D-16 headings
    templates/podcast.md             # NEW D-16 headings
    templates/__init__.py            # NEW load_article_templates(traversable) -> dict
    tests_support/fakes.py           # EXTEND FakeArticleGenerator(failures=...)
  pyproject.toml                     # ADD openai

ingestion-service/
  src/ingestion_service/
    composition/settings.py          # ADD max_transcript_chars, deepseek_* 
    composition/clients.py           # ADD build_deepseek_client(settings) — no env inside adapter
    composition/config_error.py      # NEW ConfigurationError (or equivalent) for bad ints / missing key at client build
    mapping/article.py               # NEW map_article_error
    provenance.py                    # NEW constant only: " · пер. с англ."

tests/unit/
  test_ingestion_settings.py         # EXTEND cap defaults + invalid values; from_env({}) still works
  test_article_templates.py          # headings + missing file
  test_deepseek_article_adapter.py   # mocked client
  test_article_error_mapping.py
  test_fake_article_generator.py     # additive failures; existing success spy stays
  test_translation_marker.py         # exact suffix string
  test_data_collection_public_api.py # keep seven names; add adapter/error to NEGATIVE_ROOT_NAMES

docs/agents/local-platform-runbook.md  # document env names; no live key
```

**Do not add** `typer`, Supabase writes, migrations, or `web/` files. **Do not export** the adapter or `ArticleError` from `data_collection.__all__` (`test_public_all_is_exactly_seven_ingestion_names`).

### Pattern 1: Injected client, env only in Settings

**What:** Adapter constructor takes a ready async client, `model: str`, `templates: Mapping[TemplateKind, str]`, and `max_transcript_chars: int`. `Settings.from_env` is the only `os.environ` reader.

**Additive settings** so Phase 7 tests `Settings.from_env({})` keep passing:

| Env | Unset or blank | Invalid |
|-----|----------------|---------|
| `MAX_TRANSCRIPT_CHARS` | `80000` | non-integer, `0`, negative → `ConfigurationError` at `from_env` (not `llm_truncation`) |
| `DEEPSEEK_API_KEY` | `None` on Settings | `build_deepseek_client` raises `ConfigurationError` if missing/blank. Do **not** require the key in `from_env` or YouTube-only tests break |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | use the stripped value as-is |
| `DEEPSEEK_MODEL` | `deepseek-flash` | use the stripped value as-is (operator may set `deepseek-v4-pro`) |

**Client factory** (composition passes settings in; factory does not read env):

```python
from openai import AsyncOpenAI

def build_async_deepseek_client(api_key: str, base_url: str, timeout: float) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,       # do not leave the 10-minute SDK default
        max_retries=0,         # do not leave the SDK default of 2
    )
```

Recommend `timeout=120.0` (connect can be shorter via `httpx2.Timeout` if the planner wants). Pass `http_client` with `trust_env=False` if the SDK default would honor `HTTP_PROXY` — YouTube already has its own `YOUTUBE_PROXY_URL`. DeepSeek must not silently reuse that proxy. `[CITED: Context7 AsyncOpenAI timeout / max_retries / DefaultAsyncHttpx2Client]`

### Pattern 2: One JSON object, two-step parse

**What:** Ask for JSON mode, parse, then validate. The split is what makes `invalid_json` different from `invalid_article_draft`.

```python
response = await client.chat.completions.create(
    model=model,
    messages=messages,
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
)
content = response.choices[0].message.content
```

Then:

1. `content` must be a `str`. `None`, a list, or empty → `ArticleInvalidJson` (`json.loads` would fail or the value is not an object).
2. `json.loads`. `JSONDecodeError` → `invalid_json`. Fences and prose fail here. Do not strip.
3. If the value is not a `dict` → `invalid_json` (D-13: JSON that is not an object).
4. `ArticleDraft.model_validate(payload)`. `ValidationError` (missing or blank after `strip_non_blank`) → `invalid_article_draft`.
5. Extra keys are ignored by the existing model. Return that instance only.

DeepSeek JSON mode **requires the word `json` in the system or user message** or the model may stream whitespace until the token limit `[CITED: Context7 /websites/api-docs_deepseek json_mode]`. Put `JSON` in the shared system prompt and assert it in the test.

Do **not** use `client.chat.completions.parse` or a Pydantic `response_format` class. That is JSON schema, not D-11.

HTTP 200 with `finish_reason="length"` is **not** D-10. D-10 is a **rejection**. If the body is not valid JSON → `invalid_json`. If it parses and the three strings are non-blank → return the draft (D-15 does not inspect headings). Do not map a 200 onto `provider_context_length`.

### Pattern 3: Prompt = shared rules + one template file + transcript

**System message** (same for lecture and podcast, D-14), English instructions allowed:

- Use only the transcript. Do not invent facts, names, or numbers.
- Output is always Russian.
- If the transcript language is `ru`: format only; do not translate.
- If the transcript language is `en`: translate into Russian.
- Preserve technical terms, proper names, library names, numbers, and units as written.
- Return one JSON object with keys `title`, `dek`, `body_markdown` (the word JSON must appear).

**User message:**

- The chosen template markdown (must include that template's three D-16 headings and not the other template's headings).
- The actual `transcript.language` string (`ru` or `en`). This is not a detector (D-03).
- `transcript.text` unchanged (no truncation).

Tests (D-04):

- Lecture call's messages contain `## Тезис`, `## Ход рассуждения`, `## Вывод` and do not contain `## О чём разговор`.
- Podcast call contains `## О чём разговор`, `## Позиции`, `## Что запомнить`.
- Both calls contain the honesty / always-Russian / preserve-terms rules and the word `json`.
- `ru` vs `en` both appear as the language value passed through; scripted JSON that still contains `pgvector`, `RAG`, and `embedding` round-trips onto `ArticleDraft` unchanged.
- Do not assert Cyrillic detection on the reply.

### Pattern 4: SDK → ArticleError → IngestError

Catch OpenAI exceptions inside the adapter. Recommended subtype table (discretion — locked **reasons** are not):

| Condition | ArticleError subtype | `IngestError` |
|-----------|----------------------|---------------|
| `len(text) > max_chars` before create | `ArticleBudgetError` | `stage=llm_truncation`, `reason=transcript_too_long`, context **only** `char_count`, `max_chars` |
| `APITimeoutError`, `APIConnectionError` | `ArticleNetworkError` | `stage=llm`, `reason=network_error` |
| `RateLimitError` (429), `InternalServerError` (>=500) | `ArticleProviderError` | `stage=llm`, `reason=provider_error` |
| `AuthenticationError` (401), `PermissionDeniedError` (403) | `ArticleAuthError` | `stage=llm`, `reason=auth_error` |
| HTTP 400 whose **error code** indicates context length (see below) | `ArticleContextLengthError` | `stage=llm`, `reason=provider_context_length` |
| `json.loads` fails, content missing, or JSON is not an object | `ArticleInvalidJson` | `stage=llm`, `reason=invalid_json` |
| `ArticleDraft` validation fails | `ArticleInvalidDraft` | `stage=llm`, `reason=invalid_article_draft` |
| Anything else, including HTTP 402 (balance) and other 4xx | `ArticleUnknownError` | `stage=llm`, `reason=unknown_llm_error` |

`APIError.code` / status-specific subclasses are the recognition surface `[CITED: Context7 /openai/openai-python exception hierarchy]`. Classify context length from `status_code == 400` and a code/type token such as `context_length` on the exception object. Reading the code to classify is fine. **Copying `e.body`, `str(e)`, or the request into `IngestError` is not** — OpenAI status errors echo the payload, which can contain the transcript (Phase 7 CR-01 lesson: the captions fix builds `message` from the reason, not from `str(exc)`).

**Message:** English, include the `reason`, no transcript text. Example: `llm network_error` / `llm_truncation transcript_too_long`. Counts may appear in `context` for truncation only.

**`stage=llm` context allowlist (discretion):** `video_id`, `exception_class`, `status_code`. Never `transcript`, `body`, `response`, `prompt`, or the API key. `exception_class` may be the SDK class **name in context only** — D-13 forbids it as `reason`.

**`stage=llm_truncation` context:** exactly `char_count` and `max_chars` (D-09). No `video_id`.

Equality boundary: `len == max_chars` is allowed (`>` only). A short transcript plus a long template must still call the SDK.

### Pattern 5: Templates loaded at startup

```python
def load_article_templates(root: Traversable) -> dict[TemplateKind, str]:
    loaded: dict[TemplateKind, str] = {}
    for kind in TemplateKind:
        path = root.joinpath(f"{kind.value}.md")
        if not path.is_file():
            raise TemplateLoadError(kind.value)
        try:
            loaded[kind] = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise TemplateLoadError(kind.value) from exc
    return loaded
```

Production root: `importlib.resources.files("data_collection.templates")`. Tests pass `tmp_path` for the missing-file case. On Windows, do not use `chmod` to simulate "unreadable"; mock `read_text` raising `OSError`.

Repo files must contain the D-16 headings unchanged. A unit test reads the real package files and asserts those strings. Loader failure is **not** `IngestError` (D-17). Composition calls the loader while building the generator, before any video id is fetched. Do not lazy-load on first `process` after captions would already have run.

`uv`'s build backend may omit non-Python files from a wheel. Workspace tests use the source tree, so `importlib.resources` against the package directory works in `uv run pytest`. During execution, confirm a built wheel still contains both markdown files or set the build-backend include. Editable `uv run` is the v1.1 operator path.

### Pattern 6: Additive fake failure scripts

Phase 6 D-17 and the Phase 8 context: extend the fake; do not replace it. Mirror `FakeTranscriptProvider` (append to `calls`, then raise):

```python
class FakeArticleGenerator:
    def __init__(
        self,
        result: ArticleDraft,
        failures: dict[str, ArticleError] | None = None,
    ) -> None:
        self._result = result
        self._failures = failures or {}
        self.calls: list[ArticleGeneratorCall] = []

    async def process(self, transcript: Transcript, template: TemplateKind) -> ArticleDraft:
        self.calls.append({"transcript": transcript, "template": template})
        failure = self._failures.get(transcript.video_id)
        if failure is not None:
            raise failure
        return self._result
```

Existing `FakeArticleGenerator(result)` call sites stay valid. Key is `video_id` so Phase 9 can script "this video's LLM failed" without a new fake type.

### Pattern 7: Marker constant, no label builder

```python
ENGLISH_TRANSLATION_SUFFIX = " · пер. с англ."
```

Unit-test the exact string, including the leading space, middot, and trailing period (D-05/D-06). Do not implement `f"YouTube · {author}"` here. Do not change `assemble_material_draft`.

### Anti-Patterns to Avoid

- **Adapter reads `os.environ`.** Breaks the existing adapter env test and D-07's injection rule.
- **Raising `IngestError` from `data-collection`.** Stages stay in `ingestion-service`.
- **Adding a stage** such as `llm_config` or `template`. Bad config and missing files are startup errors (D-17).
- **Returning a partial `ArticleDraft`** or an empty draft on failure.
- **Stripping ``` fences or regex-extracting `{...}`.** That is `invalid_json` (D-11).
- **`reason=APIConnectionError` or any SDK class name.**
- **`str(exc)` or `exc.body` in `message` / `context`.** Transcript and key leakage.
- **Silent slice of `transcript.text`** or a tokenizer.
- **Counting template or system-prompt characters** toward the cap.
- **Language detection** of the reply (D-03).
- **Heading validation** of `body_markdown` (D-15).
- **Provenance fields in the JSON** or inside the adapter (D-12).
- **Building the YouTube label** in Phase 8 (D-05).
- **Typer, persist, Supabase, Whisper, FoundryModels.**
- **Leaving SDK defaults** (`timeout` 10 minutes, `max_retries` 2).
- **Calling DeepSeek when the key is missing** — fail at client build.
- **Exporting the adapter, `ArticleDraft`, or fakes** from the package root.
- **Mining `reasoning_content`** if `content` is empty. That is `invalid_json`.
- **Using the Responses API** (`client.responses.create`). DeepSeek's JSON sample is `chat.completions.create`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP client for `/chat/completions` | `httpx` post + custom retries | Official `AsyncOpenAI` | Locked SDK; typed exceptions |
| JSON schema mode | `chat.completions.parse(ArticleDraft)` | `response_format` `json_object` + `json.loads` | D-11 |
| Fence stripper | regex JSON salvage | `invalid_json` | D-11 |
| Tokenizer / chunker | tiktoken, sliding windows | `len(transcript.text)` | D-07/D-08; chunking deferred |
| Language ID | `langdetect` on the reply | Prompt rules + scripted fixtures | D-03/D-04 |
| Template engine | Jinja / LangChain | Two markdown files + a shared Python system prompt | D-14; STACK rejects LangChain for two static outlines |
| New pipeline stage | `stage=template` | `ConfigurationError` / `TemplateLoadError` | D-17 |
| Provenance in the model | extra JSON keys | Phase 10 caller + existing assembler | D-05/D-12 |

**Key insight:** Phase 8 success is a **tested prompt contract** and a **stable `stage`/`reason` map** around an injected client. It is not a live Russian article and not a CLI.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | No DB writes this phase | Do not add migrations or repository calls |
| `IngestError.Stage` | Already includes `llm` and `llm_truncation` `[VERIFIED: ingestion_service/domain/errors.py]` | Do not add a member |
| `Settings` | Only `youtube_proxy_url` `[VERIFIED]` | Add fields with defaults; `from_env({})` must still succeed |
| `ArticleGenerator` / `ArticleDraft` / `TemplateKind` | Present; `ArticleDraft` not in `__all__` | Implement the port; do not publish `ArticleDraft` |
| `FakeArticleGenerator` | Success + spy only | Add optional `failures` |
| `assemble_material_draft` | Copies caller label | Leave behavior alone |
| Secrets | No `DEEPSEEK_*` in `.env.example` or runbook yet | Document **names** in the runbook. Do not commit a key. Phase 10 loads `ingestion-service/.env` (CLI-05); do not point the key at `VITE_` |
| Public API test | Exactly seven exports | Keep that assertion green |
| Workspace members | `backend`, `data-collection`, `ingestion-service`, `supabase-integration` | No new member |

## Common Pitfalls

### Pitfall 1: Treating roadmap "MaterialDraft + provenance" as the adapter return
**What goes wrong:** JSON schema grows `provenance_label`; adapter learns YouTube author strings.  
**Why it happens:** LLM-01 and roadmap criterion 1 still use that sentence. D-12 supersedes it.  
**How to avoid:** Adapter tests assert three fields. Marker test asserts the suffix constant only.  
**Warning signs:** `provenance` appears in `response_format` or adapter source.

### Pitfall 2: SDK default timeout and retries
**What goes wrong:** A hung JSON-mode call (missing the word `json`, or thinking left on) blocks for ~10 minutes and then retries twice.  
**Why it happens:** OpenAI SDK defaults `[CITED: Context7]`. DeepSeek JSON docs warn about whitespace until the token limit.  
**How to avoid:** `timeout` on the client, `max_retries=0`, the word `json` in the system prompt, thinking disabled.  
**Warning signs:** tests sleep; `create` call count > 1 on a single 429.

### Pitfall 3: `str(exc)` in the operator message
**What goes wrong:** Transcript or API key lands in `IngestError.message` / logs. Phase 7 CR-01 was this leak; the captions mapper was fixed to build the message from `reason` + `video_id` only.  
**How to avoid:** Fixed English message. Classify using `status_code` and `code`. Allowlist context keys.  
**Warning signs:** assertion only checks `context` and not `message` / `to_dict()["message"]`.

### Pitfall 4: Cap check after the SDK call, or cap includes the prompt
**What goes wrong:** Over-long transcripts are sent, or a long template trips `llm_truncation` for a short transcript.  
**How to avoid:** Compare `len(transcript.text)` first. Test `len == 80000` calls the client; `80001` does not. Test a long template string with a short transcript still calls.  
**Warning signs:** `tiktoken` import; `text[:max]` passed as the user message.

### Pitfall 5: Provider context errors labeled `llm_truncation`
**What goes wrong:** Operators cannot tell a local policy reject from a DeepSeek 400.  
**How to avoid:** Local `>` check → `llm_truncation` / `transcript_too_long`. HTTP rejection → `stage=llm` / `provider_context_length` (D-10).  
**Warning signs:** one reason used for both.

### Pitfall 6: Fence salvage hides invalid JSON
**What goes wrong:** Model wraps JSON in ```json and the adapter "succeeds" with a partial article.  
**How to avoid:** `json.loads` on the raw string only (D-11).  
**Warning signs:** a helper named `extract_json`.

### Pitfall 7: Thinking-mode content in the wrong channel
**What goes wrong:** `message.content` is empty or non-JSON while the article sits on `reasoning_content`. Unit tests with a stub will not catch it.  
**How to avoid:** Disable thinking in `extra_body`. Treat non-string/empty `content` as `invalid_json`. Do not parse `reasoning_content`. Optional integration test later, not the gate.  
**Warning signs:** production drafts fail `invalid_json` while the dashboard shows a fine reasoning trace.

### Pitfall 8: Missing template discovered after captions
**What goes wrong:** A one-shot (Phase 10) spends YouTube quota, then dies on a missing file.  
**How to avoid:** Load both files when the generator is constructed (D-17).  
**Warning signs:** `open()` inside `process`.

### Pitfall 9: Requiring `DEEPSEEK_API_KEY` inside `Settings.from_env`
**What goes wrong:** `test_ingestion_settings.py` calls `from_env({})` and `from_env` with only `YOUTUBE_PROXY_URL`.  
**How to avoid:** Key stays optional on the dataclass. The client factory rejects a blank key.  
**Warning signs:** Phase 7 settings tests go red for an unrelated reason.

### Pitfall 10: Live zero-row proof without a persist port
**What goes wrong:** Phase 8 grows Supabase writers to satisfy LLM-03's "zero database rows" sentence.  
**How to avoid:** Same deferral as CAP-02 / Phase 7 D-14. Document the Phase 9 spy: failing `ArticleGenerator` → `persist.calls == []`.  
**Warning signs:** a new repository module in this phase.

## Code Examples

### Settings cap (D-07)

```python
def _max_transcript_chars(env: dict[str, str]) -> int:
    raw = env.get("MAX_TRANSCRIPT_CHARS")
    if raw is None or raw.strip() == "":
        return 80_000
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigurationError("MAX_TRANSCRIPT_CHARS must be a positive integer") from exc
    if value <= 0:
        raise ConfigurationError("MAX_TRANSCRIPT_CHARS must be a positive integer")
    return value
```

`int("80.5")` fails. That is the non-integer case. Do not use `float`.

### Mapping sketch (pattern matches `map_captions_error`)

```python
def map_article_error(error: ArticleError) -> IngestError:
    if isinstance(error, ArticleBudgetError):
        return IngestError(
            stage="llm_truncation",
            reason="transcript_too_long",
            message="llm_truncation transcript_too_long",
            context={
                "char_count": error.context["char_count"],
                "max_chars": error.context["max_chars"],
            },
        )
    reason = _REASON_BY_TYPE.get(type(error), "unknown_llm_error")
    return IngestError(
        stage="llm",
        reason=reason,
        message=f"llm {reason}",
        context=_allowlisted(error),
    )
```

### Mocked create (unit tests stay offline)

Stub an object whose `chat.completions.create` is an async function recording kwargs and returning `choices[0].message.content` as a string. The adapter production code calls that attribute path so the real `AsyncOpenAI` drops in without a second port. Tests do not need a live socket. `asyncio.run` matches Phase 6/7; do not add `pytest-asyncio`.

## State of the Art

| Concern | Current fact | Planning consequence |
|---------|--------------|----------------------|
| SDK | `openai==3.19.2`, async client, `httpx2` `[VERIFIED: PyPI]` | Pin `>=3.0,<4`; one `uv add` |
| DeepSeek URL / model | `https://api.deepseek.com`, `deepseek-flash` or `deepseek-v4-pro` `[CITED: Context7]` | Defaults above; do not hard-code retired `deepseek-chat` |
| JSON mode | `response_format.type=json_object`; prompt must mention JSON `[CITED: Context7]` | Assert the word in the system message |
| Thinking | Supported; **default is thinking on** `[CITED: Context7 pricing table]` | Send `extra_body={"thinking": {"type": "disabled"}}` |
| Context window | Pricing table lists **1M** for `deepseek-flash` `[CITED: Context7]` | Irrelevant to the cap. D-07 stays 80000 chars. The "64k token margin" note in CONTEXT is rationale for the number, not a tokenizer spec |
| 429 | Account concurrency overflow returns HTTP 429 `[CITED: Context7 rate limit]` | `provider_error`, no retry loop in this phase |
| Error-code catalog | `https://api-docs.deepseek.com/quick_start/error_codes` exists but renders on the client; Context7 did not return the code table | Classify with SDK status + `code` token `context_length`. 402 and other unmatched 4xx → `unknown_llm_error`. Re-check if the first live 400 uses a different code |

## Assumptions Log

| ID | Assumption | Evidence | Risk if wrong |
|----|------------|----------|----------------|
| A1 | Char-cap check lives in the adapter, limit injected, mapper emits `IngestError` | D-08 + Phase 7 "no stages in data-collection" | Planner may put the check only in ingestion-service. That also satisfies D-08 **if** every caller uses it. Adapter-side check is safer. |
| A2 | `ArticleError` subtypes mirror captions; locked strings are the reasons | D-13 + `map_captions_error` | Subtype names can change; reason strings cannot |
| A3 | Templates live in `data_collection/templates/*.md` | Discretion + ARCHITECTURE.md | Another repo path is fine if load-before-video and D-16 headings hold |
| A4 | `max_retries=0`, timeout 120s, thinking disabled | SDK defaults + DeepSeek JSON/thinking docs; CONTEXT silent on retries | Phase 10 UAT may want a bounded 429 retry. Reason codes stay the same |
| A5 | Context-length rejection is HTTP 400 with a `context_length` code token | OpenAI-compatible `APIError.code`; DeepSeek code table not extracted | If the live API only puts this in free text, the predicate must read `code` first and a bounded token scan second, still without copying the body into `context` |
| A6 | HTTP 402 (balance) is `unknown_llm_error` | Not in the D-13 set | Do not invent `billing_error` |
| A7 | `openai` declared only on `data-collection`; factory takes plain strings | Adapter needs the exception types; Settings stays the env boundary | If `clients.py` imports `AsyncOpenAI` directly, also declare the dep on `ingestion-service` |
| A8 | Public `__all__` stays seven names | `test_data_collection_public_api.py` | Exporting the adapter fails that test |
| A9 | Phase 9 records the LLM zero-row spy the way Phase 7 recorded CAP-02 | CONTEXT deferred persist | If Phase 9 plans omit it, LLM-03's live sentence stays unproven |

## Open Questions (RESOLVED for planning)

1. **Does the adapter return `MaterialDraft`?** — RESOLVED: No. `ArticleDraft` only (D-12). Assembler + Phase 10 label satisfy LLM-01.
2. **Does Phase 8 ship `--template`?** — RESOLVED: No. Files + `TemplateKind` selection. Typer is Phase 10.
3. **How is "zero database rows" proven?** — RESOLVED: No `ArticleDraft` on failure; no DB code. Spy is Phase 9.
4. **Where is the char cap checked?** — RESOLVED as discretion: injected int, before `create`, Settings owns the env value. Recommend the adapter.
5. **What is `provider_context_length`?** — RESOLVED: a DeepSeek **rejection**, not the local cap (D-10). Detection heuristic is A5.
6. **Does a missing template get a new stage?** — RESOLVED: No (D-17). Startup/config error, same class as a bad `MAX_TRANSCRIPT_CHARS`.
7. **Does Phase 8 append ` · пер. с англ.`?** — RESOLVED: It locks the string. Phase 10 appends it when `language != "ru"` (D-05/D-06).

No blockers for planning.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python ≥3.12 | All | ✓ | workspace | — |
| uv | add + pytest | ✓ | workspace | — |
| pydantic / pytest | DTOs / tests | ✓ | 2.13.5 / 9.1.1 | — |
| `openai` | DeepSeek adapter | ✗ not in lock | PyPI **3.19.2** | `uv add --package data-collection "openai>=3.0,<4"` |
| `httpx2` | transitive | ✗ until openai is added | `>=2.12,<3` | Do not add by hand |
| `httpx==0.28.1` | YouTube oEmbed | ✓ | keep | Unaffected (different package name) |
| `ingestion-service` | Settings + mapper | ✓ Phase 7 | — | Extend; do not recreate |
| `DEEPSEEK_API_KEY` | live call only | optional | — | Unit tests inject a fake client |
| pytest-asyncio | — | ✗ | — | `asyncio.run` |
| Supabase persist | LLM-03 live spy | not this phase | — | Phase 9 |

**Missing dependencies with no fallback:** none, once `uv add` succeeds.  
**Missing with fallback:** live DeepSeek → mocked unit tests. Lock resolve failure → stop and pin `openai` (STACK mentions 2.11.x only as a resolve contingency).

## Validation Architecture

Nyquist validation is **enabled** for this phase (task instruction). `.planning/config.json` has no `workflow.nyquist_validation` key; treat enabled the same way Phase 7 research did.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `9.1.1` |
| Config file | root `pyproject.toml` — `testpaths = ["tests/unit"]`; `integration` marker already registered |
| Quick run command | `uv run pytest tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_error_mapping.py tests/unit/test_article_templates.py tests/unit/test_ingestion_settings.py -x` |
| Full suite command | `uv run pytest` |
| Integration (optional, not a gate) | `uv run pytest tests/integration -m integration` only when a key is present and the runbook says so. Default suite does not collect that path |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LLM-01 | Mocked JSON object → `ArticleDraft` with non-blank `title` / `dek` / `body_markdown`; extra keys ignored | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ❌ Wave 0 |
| LLM-01 | Provenance not read from JSON; assembler still requires a caller label | unit (existing assembler tests stay; no new provenance field) | `uv run pytest tests/unit/test_assemble_material_draft.py -x` | ✅ exists — do not weaken |
| LLM-02 | `lecture` prompt contains the three lecture headings; `podcast` contains the three podcast headings; files are package markdown | unit | `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py -x` | ❌ Wave 0 |
| LLM-02 | Typer `--template` | — | Phase 10 | N/A |
| LLM-03 | Network, 429, 5xx, 401/403, fences, non-object JSON, blank field → `ArticleError`; no `ArticleDraft` | unit | `uv run pytest tests/unit/test_deepseek_article_adapter.py -x` | ❌ Wave 0 |
| LLM-03 | Mapper `stage=llm` and D-13 reasons; `to_dict()`; message has no transcript / body | unit | `uv run pytest tests/unit/test_article_error_mapping.py -x` | ❌ Wave 0 |
| LLM-03 live zero rows | Spy persist not called | — | Phase 9 | N/A |
| LLM-04 | System prompt: transcript-only, always Russian, `ru` format-only, `en` translate, preserve terms; scripted draft keeps `pgvector` / `RAG` / `embedding` | unit | adapter tests | ❌ Wave 0 |
| LLM-04 | Suffix constant ` · пер. с англ.` exact | unit | `uv run pytest tests/unit/test_translation_marker.py -x` | ❌ Wave 0 |
| LLM-04 | No language detector on the reply | unit (absence) | no new detector module; review | — |
| LLM-05 | `len == 80000` calls SDK; `80001` does not; context is only `char_count` + `max_chars`; template length ignored | unit | adapter + mapping tests | ❌ Wave 0 |
| LLM-05 | Unset/blank cap → 80000; `0`, negative, non-integer → config error at `from_env`, not `llm_truncation` | unit | `uv run pytest tests/unit/test_ingestion_settings.py -x` | ⚠️ exists — extend |
| D-10 | Scripted HTTP 400 context-length → `stage=llm`, `reason=provider_context_length` | unit | mapping tests | ❌ Wave 0 |
| D-17 | Missing `lecture.md` or `podcast.md` raises before any client call | unit (`tmp_path`) | template tests | ❌ Wave 0 |
| D-17 | Adapter modules do not read `os.environ` | unit | existing `test_adapters_do_not_read_environ` | ✅ will cover the new file |
| Phase 6 D-17 | `FakeArticleGenerator` failures raise; success spy unchanged | unit | `uv run pytest tests/unit/test_fake_article_generator.py -x` | ❌ Wave 0 (success path covered elsewhere) |
| Public API | `__all__` still exactly seven names; new adapter/error not at root | unit | `uv run pytest tests/unit/test_data_collection_public_api.py -x` | ✅ extend negative names |

### Sampling Rate

- **Per task commit:** the new unit file(s) with `-x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** full unit suite green before `/gsd-verify-work`. No live DeepSeek call required
- **Max feedback latency:** well under a minute for these unit files (no network)

### Wave 0 Gaps

- [ ] RED tests for `MAX_TRANSCRIPT_CHARS` default, blank, and invalid values without breaking `from_env({})`
- [ ] RED tests for template headings and missing-file load
- [ ] RED tests for mocked happy path, prompt rules, `ru`/`en` language passthrough, preserved tokens
- [ ] RED tests for D-13 failures, fence rejection, budget boundary, SDK not called when over cap
- [ ] RED tests for `map_article_error` allowlists and message redaction (`message` and `to_dict()`, not only `context`)
- [ ] RED test for the exact English suffix constant
- [ ] RED test for additive `FakeArticleGenerator` failures
- [ ] `uv add --package data-collection "openai>=3.0,<4"` then `uv sync` (when tests first import `openai`)
- [ ] Extend runbook §1 with `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `MAX_TRANSCRIPT_CHARS` (names and defaults only)
- [ ] Extend `NEGATIVE_ROOT_NAMES` with the new adapter and `ArticleError`
- [ ] Assert this phase adds no Typer app, no Supabase writer, no migration, no `IngestError` stage
- [ ] Note on the Phase 9 plan: failing `ArticleGenerator` + spy persist → `persist.calls == []`

### Manual-Only Verifications

| Item | Why manual | Notes |
|------|------------|-------|
| Live DeepSeek draft quality (headings, Russian, honesty) | Needs a key and a human reader | Phase 10 UAT, including one English source video |
| Real HTTP 400 body shape for context length | Docs page did not yield a stable code sample | Optional integration; unit test uses a stub exception with `status_code` and `code` |
| Wheel contains `lecture.md` / `podcast.md` | Packaging | Check if a wheel is built; source-tree tests are the gate |

## Security Domain

`security_enforcement` is absent in `.planning/config.json`. Treat security checks as **enabled** (same stance as Phase 7).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No user-auth surface. Provider 401/403 → `auth_error` |
| V3 Session Management | no | — |
| V4 Access Control | no | No DB writes |
| V5 Input Validation | yes | Char cap; JSON object; non-blank `ArticleDraft` fields; reject fences |
| V6 Cryptography | no | API key is an env secret, not a cipher |
| V10 Malicious Input | yes | Transcript is untrusted prompt data. It must not reach a shell, SQL, or logs. No DB write this phase, so injection cannot persist |
| V14 Configuration | yes | Key and cap read only in `Settings` / client factory. Adapters do not read env |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| API key in source, `.env` commit, or `VITE_` | Information disclosure | Env only; runbook; factory error must not echo the key |
| `str(APIStatusError)` contains the prompt | Information disclosure | Fixed `message`; context allowlist; CR-01 pattern |
| Transcript copied into `llm_truncation.context` | Information disclosure | D-09: only `char_count` and `max_chars` |
| Over-long transcript sent anyway (cost, leakage to the provider) | Denial / disclosure | Check before `create`; no silent truncation |
| Thinking-mode or missing `json` word burns tokens until timeout | Denial of wallet | Disable thinking; include `json`; explicit timeout; `max_retries=0` |
| Prompt injection that asks for extra JSON keys or a non-Russian essay | Tampering | Extra keys ignored; headings not validated here (D-15); language detector explicitly out of scope (D-03); preview is Phase 5/10 |
| SDK `trust_env` picks up `HTTP_PROXY` and sends the transcript to an unexpected proxy | Information disclosure | Construct the HTTP client with `trust_env=False` unless a future decision adds a DeepSeek proxy env |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/08-deepseek-article-templates/08-CONTEXT.md` — D-01…D-17
- `.planning/REQUIREMENTS.md` — LLM-01…LLM-05 (LLM-04 updated 2026-09-27)
- `.planning/ROADMAP.md` — Phase 8 criteria; Phase 9/10 boundaries
- `.planning/STATE.md` — Phase 7 complete; Phase 8 ready to plan
- `.planning/phases/06-ports-dtos/06-CONTEXT.md` — D-05…D-08, D-10, D-16, D-17 (fakes)
- `.planning/phases/07-captions-adapter/07-CONTEXT.md` — stages, env injection, diagnostic envelope (patterns reused)
- Live code: `article_generator.py`, `article_draft.py`, `template_kind.py`, `assemble.py`, `fakes.py`, `errors.py` (`Stage` literal), `settings.py`, `mapping/captions.py`, `data_collection/__init__.py`, `test_data_collection_public_api.py`, `test_ingestion_settings.py`
- `.cursor/rules/architecture.mdc`, `tdd.mdc`, `python-uv.mdc`, `AGENTS.md`
- `.planning/research/STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md`, `FEATURES.md`, `SUMMARY.md` — used where not superseded above
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — FoundryModels remains the long-term contour; DeepSeek is the documented bend
- PyPI `openai` `3.19.2` requires `httpx2<3,>=2.12.0` (queried 2026-09-27)
- `uv.lock` — `openai` absent; `pydantic==2.13.5`; `pytest==9.1.1`

### Secondary (MEDIUM confidence)
- Context7 `/openai/openai-python` — `AsyncOpenAI` `base_url` / `timeout` / `max_retries` (default 2; `0` disables); exception hierarchy (`APIConnectionError`, `APITimeoutError`, `APIStatusError.status_code`, `RateLimitError` 429, `AuthenticationError` 401, `PermissionDeniedError` 403, `InternalServerError` 5xx); `chat.completions.create`; default timeout 10 minutes
- Context7 `/websites/api-docs_deepseek` — `base_url=https://api.deepseek.com`, model `deepseek-flash`, `response_format={"type":"json_object"}`, prompt must say JSON, `finish_reason=length` cuts content, thinking default on, context length 1M, HTTP 429 when concurrency is exceeded

### Tertiary (LOW confidence)
- Exact DeepSeek `error.code` string for a context-length 400 (error-codes page is JS-rendered; not in the Context7 extract). Unit tests should stub the code the predicate accepts, and an optional live call can confirm it
- Whether `extra_body.thinking.type=disabled` is ignored or rejected by a future model alias — official guide shows `enabled`; disabling is the supported switch implied by "both modes"

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PyPI pin and Context7 client/JSON samples agree with STACK.md; package not installed yet
- Architecture: HIGH — CONTEXT locks plus Phase 6/7 code match the two-hop error pattern
- Pitfalls: HIGH — fail-closed, secret-safe messages, cap vs provider rejection, no CLI/persist
- Discretion items: MEDIUM — file layout, subtype names, timeout number, thinking flag, context-length predicate

**Research date:** 2026-09-27
**Valid until:** 2026-10-27 (re-check if `openai` 4.x ships, DeepSeek renames `deepseek-flash`, or JSON mode stops accepting `json_object`)
