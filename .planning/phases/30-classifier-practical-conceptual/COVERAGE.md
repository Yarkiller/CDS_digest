# API Coverage — DeepSeek classifier call (Phase 30)

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Detector: `api-coverage.cjs` returned `detected: true` (`sdk` + DeepSeek JSON call).
> This matrix is **re-decided** for the classifier surface. It does not silently inherit Phase 8 / pass-1 opt-outs.

Phase 30 adds a **second** `chat.completions.create` against the same DeepSeek host, through the same injected `AsyncOpenAI` client factory (`build_async_deepseek_client`, `trust_env=False`). No new SDK, no new base URL, no new env var. The classifier is a cheap non-stream `json_object` call. Fail-soft (KIND-02): empty content, transport errors, and invalid enum tokens become `conceptual` in code and ingest continues. Pass-1 article generation keeps its own call shape (`stream=True`, no `max_tokens`, fail-closed `ArticleError`).

## Surface — `AsyncOpenAI` chat completions (DeepSeek classifier)

| capability | decision | reason |
|---|---|---|
| Reuse `build_async_deepseek_client` (`api_key`, `base_url`, `timeout`, `max_retries=0`, `DefaultAsyncHttpxClient(trust_env=False)`) | INTEGRATE | |
| `chat.completions.create` | INTEGRATE | |
| request `model` (`settings.deepseek_model`, default `deepseek-flash`) | INTEGRATE | |
| request `messages` (classifier system + user; title/dek + fenced transcript head+tail; not `body_markdown`) | INTEGRATE | |
| `response_format={"type":"json_object"}` | INTEGRATE | |
| `extra_body={"thinking":{"type":"disabled"}}` | INTEGRATE | |
| `stream=False` | INTEGRATE | |
| `max_tokens=128` | INTEGRATE | |
| read `choices[0].message.content` only | INTEGRATE | |
| empty / missing `content` → `normalize_topic_kind` → `conceptual` | INTEGRATE | |
| user or system message contains the word `json` plus example `{"topic_kind": "conceptual"}` | INTEGRATE | |
| SDK default retry loop (`max_retries` default 2) | OPT-OUT | not needed — `max_retries=0` already on the shared factory; one transport miss must fail-soft once, not retry into a long hang |
| SDK default timeout of 10 minutes | OPT-OUT | not needed — classifier reuses the existing explicit DeepSeek timeout on `build_async_deepseek_client` |
| `trust_env=True` / inheriting `HTTP_PROXY` | OPT-OUT | explicitly out of scope — YouTube SOCKS5 must never reach DeepSeek (Phase 28 measurement) |
| `chat.completions.parse` / Pydantic `response_format` class | OPT-OUT | explicitly out of scope — KIND-02 mapping is a before-validator allowlist, not JSON schema |
| `response_format` type `json_schema` | OPT-OUT | DeepSeek documents `text` \| `json_object` only; a schema would still not replace `normalize_topic_kind` |
| `client.responses.create` (Responses API) | OPT-OUT | explicitly out of scope — DeepSeek JSON sample is `chat.completions.create` |
| streaming (`stream=True`) | OPT-OUT | not needed on this call — classifier output is one small object; pass-1 keeps `stream=True` unchanged |
| `message.reasoning_content` | OPT-OUT | thinking is disabled; empty `content` is KIND-02 `conceptual`, not an `ArticleInvalidJson` |
| Map classifier transport to `ArticleError` / `stage=llm` (`APITimeoutError`, `APIConnectionError`, `RateLimitError`, `InternalServerError`, `AuthenticationError`, `PermissionDeniedError`, `APIStatusError`) | OPT-OUT | KIND-02 fail-soft: swallow, stamp `conceptual`, persist. Pass-1 keeps its fail-closed taxonomy |
| `finish_reason="length"` as fail-closed ingest | OPT-OUT | truncated JSON is KIND-02 `conceptual`; ingest continues |
| tools / `tool_choice` / function calling | OPT-OUT | not needed — closed two-value enum, not tool-calling (ROADMAP rejected DeepSeek tools wrapping Tavily) |
| `temperature`, `top_p`, penalties, `logit_bias`, `seed`, `logprobs`, `n`, `stop` | OPT-OUT | not needed — sampling knobs are not part of the operator contract |
| `max_completion_tokens` (OpenAI-only alias) | OPT-OUT | DeepSeek uses `max_tokens`; this call sets `max_tokens=128` |
| `user`, `metadata`, `store`, `service_tier` | OPT-OUT | not needed — no provider-side prompt storage or end-user id |
| `embeddings` | OPT-OUT | explicitly out of scope |
| `images` | OPT-OUT | explicitly out of scope |
| `audio` | OPT-OUT | explicitly out of scope — captions are already text |
| `files` | OPT-OUT | not needed — transcript is an in-request message |
| `batches` | OPT-OUT | not needed — one video, one cheap completion |
| `moderations` | OPT-OUT | not needed |
| `models.list` / model discovery | OPT-OUT | not needed — model id comes from `DEEPSEEK_MODEL` |
| `fine_tuning` | OPT-OUT | explicitly out of scope |
| beta assistants / threads | OPT-OUT | explicitly out of scope |
| legacy `completions.create` | OPT-OUT | explicitly out of scope — chat completions only |
| New Settings / env var for the classifier | OPT-OUT | not needed — reuse `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` |
| Live DeepSeek proof in the default suite | OPT-OUT | not needed — unit tests inject a non-stream stub; RESEARCH Open Question 2 |

## Notes

- Pass-1 `test_create_kwargs_include_json_object_and_disabled_thinking` must stay `stream=True` with no `max_tokens`. Classifier tests pin the inverted kwargs.
- Unit tests inject a stub client. No live DeepSeek call is a Phase 30 gate.
- Tavily is Phase 31 — not a surface in this matrix.
