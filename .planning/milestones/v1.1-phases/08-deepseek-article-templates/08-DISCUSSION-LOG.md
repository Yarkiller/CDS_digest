# Phase 8: DeepSeek Article & Templates - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-27
**Phase:** 8-DeepSeek Article & Templates
**Areas discussed:** Article language, Oversized-transcript cutoff, Model reply contract, Lecture vs podcast difference

---

## Article language

| Option | Description | Selected |
|--------|-------------|----------|
| Always Russian | `ru` format-only; `en` translated; terms preserved; caller adds a translation marker | ✓ |
| Match the transcript | English transcript stays an English article (old LLM-04 wording) | |
| You decide | Lock always Russian | |

**User's choice:** Always Russian
**Notes:** REQUIREMENTS.md LLM-04 and ROADMAP Phase 8 criterion 4 updated; old "match transcript" wording superseded. Phase 8 tests both `ru` and `en` (`pgvector` / `RAG` / `embedding` unchanged). UAT (Phase 10 / CLI-03): at least one English source video among 3–5, draft in Russian.

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt and tests only | No runtime language detector; admin preview catches a wrong-language draft | ✓ |
| Reject a non-Russian reply | Fail closed if title, dek, or body do not look Russian | |
| You decide | Lock prompt and tests only | |

**User's choice:** Prompt and tests only
**Notes:** Language detection false-fails on Latin technical terms. Fail-closed only for clear-cut cases. "Not looking Russian" is a heuristic.

| Option | Description | Selected |
|--------|-------------|----------|
| ` · пер. с англ.` | Short marker after `YouTube · {author}` | ✓ |
| ` · перевод с английского` | Spelled-out marker | |
| You decide | Lock the short marker | |

**User's choice:** ` · пер. с англ.`
**Notes:** Format ` · пер. с <lang>.` with a trailing period and a middot. Example: `YouTube · Сбер Pro · пер. с англ.` Phase 10 builds the label. Assembler copies it. Phase 8 locks the string only.

| Option | Description | Selected |
|--------|-------------|----------|
| English only | Only non-`ru` suffix is ` · пер. с англ.` | ✓ |
| Small map now | Extra languages even though captions will not emit them | |
| You decide | Lock English only | |

**User's choice:** English only
**Notes:** Wider map waits until captions accept more languages.

---

## Oversized-transcript cutoff

| Option | Description | Selected |
|--------|-------------|----------|
| Character cap on the transcript text | `len(transcript.text)` before the call; template excluded | ✓ |
| Token estimate against the model window | Tokenizer or estimate, including the template | |
| You decide | Lock the character cap | |

**User's choice:** Character cap
**Notes:** `MAX_TRANSCRIPT_CHARS = 80000`, env-configurable. `len > MAX` → `stage=llm_truncation`. No tokenizer. Template and system prompt excluded. DeepSeek's own context error is `stage=llm`, not `llm_truncation`. Rationale given: 80k chars ≈ 25k tokens vs a 64k limit.

| Option | Description | Selected |
|--------|-------------|----------|
| `reason=transcript_too_long` with counts | Context is `char_count` and `max_chars` only | ✓ |
| Stage only | No reason and no counts | |
| You decide | Lock the reason and counts | |

**User's choice:** `transcript_too_long` with counts
**Notes:** No transcript text in the error. Same envelope style as captions.

| Option | Description | Selected |
|--------|-------------|----------|
| `provider_context_length` | `stage=llm`, distinct from the local cap and from invalid JSON | ✓ |
| Generic LLM failure | Share a reason with other model failures | |
| You decide | Lock `provider_context_length` | |

**User's choice:** `provider_context_length`

| Option | Description | Selected |
|--------|-------------|----------|
| Default 80000; bad values fail at startup | Unset or blank → 80000; non-integer, zero, or negative fails at settings load | ✓ |
| Always fall back to 80000 | Invalid values are ignored | |
| You decide | Lock fail-at-startup | |

**User's choice:** Default 80000; bad values fail at startup

---

## Model reply contract

| Option | Description | Selected |
|--------|-------------|----------|
| JSON object with `title`, `dek`, `body_markdown` | `response_format` json_object; `json.loads` then `ArticleDraft` | ✓ |
| A markdown article | Parse headings into the three fields | |
| You decide | Lock the JSON object | |

**User's choice:** JSON object
**Notes:** `invalid_json` if `json.loads` fails. `invalid_article_draft` if Pydantic fails. Extra keys ignored. No partial draft. Markdown belongs inside `body_markdown`.

| Option | Description | Selected |
|--------|-------------|----------|
| Fail `invalid_json` | No fence stripping and no extracting the first object | ✓ |
| Strip one ```json fence, then parse | Other prose still fails | |
| You decide | Lock raw JSON only | |

**User's choice:** Fail `invalid_json`

| Option | Description | Selected |
|--------|-------------|----------|
| Closed set | `network_error`, `provider_error` (5xx and 429), `invalid_json` (including non-object JSON), `invalid_article_draft`, `provider_context_length`, `unknown_llm_error` | ✓ |
| Short set | Fewer buckets; a JSON array counts as `invalid_article_draft` | |
| You decide | Lock the closed set | |

**User's choice:** Closed set
**Notes:** `network_error` is before DeepSeek; `provider_error` is from DeepSeek. No transcript text in context.

| Option | Description | Selected |
|--------|-------------|----------|
| `auth_error` | HTTP 401 and 403, `stage=llm` | ✓ |
| Leave them as `unknown_llm_error` | Keep the six-reason set | |
| You decide | Lock `auth_error` | |

**User's choice:** `auth_error`

---

## Lecture vs podcast difference

| Option | Description | Selected |
|--------|-------------|----------|
| Section outline only | Same voice, honesty rules, JSON contract, and failures | ✓ |
| Outline and voice | Lecture formal; podcast looser spoken recap | |
| You decide | Lock outline only | |

**User's choice:** Section outline only
**Notes:** Lecture: thesis → argument → takeaway. Podcast: what it was about → positions → takeaways. Looser voice deferred (hallucination risk, extra tests). Operator tells templates apart by headings.

| Option | Description | Selected |
|--------|-------------|----------|
| Headings live in the template files | No check inside `body_markdown` | ✓ |
| Missing headings fail the draft | `stage=llm` when expected headings are absent | |
| You decide | Lock template-only headings | |

**User's choice:** No validation of headings in the reply
**Notes:** Tests verify the prompt contains the headings. Phase 10 UAT: operator confirms headings in preview.

| Option | Description | Selected |
|--------|-------------|----------|
| Russian headings | `## Тезис` / `## Ход рассуждения` / `## Вывод` and `## О чём разговор` / `## Позиции` / `## Что запомнить` | ✓ |
| English headings | English heading strings in the files | |
| You decide | Lock Russian headings | |

**User's choice:** Russian headings
**Notes:** Instructions around the headings may be English. Heading strings are Russian.

| Option | Description | Selected |
|--------|-------------|----------|
| Fail at load, before any video | Missing template file is a broken install; no new `IngestError` stage | ✓ |
| Per video, `stage=llm`, `reason=template_missing` | Fail on that run | |
| You decide | Lock fail at load | |

**User's choice:** Fail at load, before any video

---

## Claude's Discretion

The user did not pick "You decide" on any question. Left to planning: template package path, where the character-cap check lives (injected limit, before the SDK call), SDK-to-reason recognition, diagnostic message wording, and extra `stage=llm` context keys that are not transcript text.

## Deferred Ideas

- Per-language translation marker map beyond `en`
- Looser podcast voice (v1.2+)
- Heading validation inside `body_markdown`
- Runtime language detection
- Chunking or silent truncation
- Typer one-shot, provenance label assembly, and UAT — Phase 10
- Persist and live zero-row proof — Phase 9
