---
phase: 08
slug: deepseek-article-templates
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-27
---

# Phase 08 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Transcript text → DeepSeek chat API | Untrusted captions become prompt content. Sent only as the user message of an injected client. | user-supplied transcript text |
| Settings / process env → client factory | API key and base URL read only in Settings.from_env. Adapters never see os.environ. | DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL |
| Model JSON → ArticleDraft | Untrusted model text. Only a JSON object with three non-blank strings becomes a draft. | LLM response JSON |
| Factory errors → caller | ConfigurationError must not echo the API key. | error messages |
| OpenAI exception → ArticleError | SDK objects can echo the prompt in str() and body. Only status_code, code, type, and class name are read. | exception metadata |
| ArticleError → IngestError.to_dict() | Operator JSON. message and context are an allowlist. | operator diagnostics |
| Failed process → caller | No ArticleDraft leaves the function on failure. | ArticleDraft or ArticleError |
| Transcript.text length → process | Untrusted size. The injected integer is the only budget. | transcript length |
| MAX_TRANSCRIPT_CHARS env → Settings.from_env | Invalid values fail at startup as ConfigurationError. | env value |
| Template files → loader | Missing or unreadable files fail before the HTTP client exists. | template markdown |
| ArticleBudgetError → operator JSON | Context is two integers. | char_count, max_chars |
| Runbook → operators | Documents env names. A pasted key would become a committed secret. | documentation |
| Package root → importers | Public surface stays the seven contracts. Adapter and errors are module-private. | package API |
| Suffix constant → Phase 10 | The string is operator-visible once persisted. This phase does not persist it. | provenance suffix |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-08-KEY | Information disclosure | `build_deepseek_article_generator` via `build_async_deepseek_client` | high | mitigate | `clients.py:37-47` blank-key `ConfigurationError` before `AsyncOpenAI`; `clients.py:55-63` loads templates before client build; runbook names/defaults only, no live key | closed |
| T-08-PROXY | Information disclosure | `build_async_deepseek_client` HTTP client | high | mitigate | `clients.py:38-46` `DefaultAsyncHttpxClient(trust_env=False)`; test asserts `_trust_env is False` | closed |
| T-08-INJECT | Tampering | `ArticleDraft.model_validate` | medium | mitigate | `deepseek_article.py:160` `ArticleDraft.model_validate` ignores extra keys; `article_draft.py` has only `title/dek/body_markdown`; no shell/SQL/file writes | closed |
| T-08-SC | Tampering | PyPI `openai` | medium | mitigate | `data-collection/pyproject.toml:11` and `ingestion-service/pyproject.toml:8` pin `openai>=3.0,<4`; `uv.lock` resolves `3.19.2`; no LangChain imports | closed |
| T-08-PROVENANCE | Spoofing | Model JSON | medium | mitigate | `article_draft.py` has no `provenance_label` field; `deepseek_article.py:160` validates only the three fields | closed |
| T-08-LEAK | Information disclosure | `map_article_error` / `ArticleError` message | high | mitigate | `mapping/article.py:20-76` message is `llm {reason}`; context allowlist `video_id/exception_class/status_code`; redaction tests plant transcript/key and assert absence | closed |
| T-08-PARTIAL | Tampering | `DeepSeekArticleGenerator.process` | high | mitigate | `deepseek_article.py:90-165` every failure path raises `ArticleError`; no draft stored on `self`; gather test returns draft only from success | closed |
| T-08-REASON | Spoofing of ops signals | `LLM_REASONS` | medium | mitigate | `mapping/article.py:20-33` exact seven-reason `LLM_REASONS`; `provider_context_length` maps to `stage=llm`; SDK class names stay in context only | closed |
| T-08-DBWRITE | Tampering | Phase scope | high | mitigate | `test_data_collection_public_api.py:122-132` asserts no `supabase` import in `data-collection/src`; adapter/mapping files contain no materials insert | closed |
| T-08-CAP | Denial / disclosure | `DeepSeekArticleGenerator.process` | high | mitigate | `deepseek_article.py:92-98` first-line `len(transcript.text) > cap` raises `ArticleBudgetError` before `create`; no silent slice; template length excluded | closed |
| T-08-CTX | Information disclosure | `llm_truncation` context | high | mitigate | `mapping/article.py:61-70` `llm_truncation` context is exactly `char_count` and `max_chars`; no `video_id`/transcript | closed |
| T-08-CONFIG | Tampering | `Settings.from_env` | medium | mitigate | `settings.py:13-25` non-integer/zero/negative `MAX_TRANSCRIPT_CHARS` raises `ConfigurationError`; tests cover `0`, `-1`, `abc`, `80.5` | closed |
| T-08-TEMPLATE | Tampering | `load_article_templates` | medium | mitigate | `templates/__init__.py:15-33` `TemplateLoadError` on missing/unreadable file; `clients.py:55-63` loads templates before `AsyncOpenAI`; not an `IngestError` stage | closed |
| T-08-KEY | Information disclosure | `local-platform-runbook.md` | high | mitigate | Document names and defaults only. Acceptance criterion rejects `sk-` live-key shape. No `VITE_` placement. | closed |
| T-08-SCOPE | Tampering | Phase boundary | high | mitigate | `test_data_collection_public_api.py:100-132` no `typer` in ingestion-service, no `supabase` in data-collection, unchanged `Stage` set; `08-04-PLAN` `files_modified` has no migrations | closed |
| T-08-LABEL | Spoofing | `ENGLISH_TRANSLATION_SUFFIX` | medium | mitigate | `provenance.py:1-5` suffix constant only; `deepseek_article.py` does not contain the suffix or `provenance_label`; no label builder | closed |
| T-08-EXPORT | Information disclosure | `data_collection.__all__` | low | mitigate | `test_data_collection_public_api.py:22-43` `NEGATIVE_ROOT_NAMES` covers `DeepSeekArticleGenerator`, `ArticleError`, `TemplateLoadError`; `data_collection/__init__.py:1-19` `__all__` stays seven names | closed |

*Status: closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-27 | 16 | 16 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-27
