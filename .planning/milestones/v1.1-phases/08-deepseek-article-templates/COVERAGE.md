# API Coverage — DeepSeek via the OpenAI-compatible SDK

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Detector: `api-coverage.cjs` returned `detected: true` on the phase plans (`integrates` + `sdk` / `api`).

Phase 8 calls one surface: the official `openai` 3.x `AsyncOpenAI` client against DeepSeek chat completions (`base_url` `https://api.deepseek.com`, model `deepseek-flash`). The capability list is that client's chat-completion call, the client constructor knobs RESEARCH cited from Context7, and the sibling SDK resources that must not be pulled in silently. DeepSeek-only fields that the OpenAI SDK does not model (`thinking`) go through `extra_body`.

## Surface — `AsyncOpenAI` chat completions (DeepSeek)

| capability | decision | reason |
|---|---|---|
| `AsyncOpenAI` constructor | INTEGRATE | |
| constructor `api_key` | INTEGRATE | |
| constructor `base_url` (`https://api.deepseek.com`, no `/v1` suffix) | INTEGRATE | |
| constructor `timeout` (explicit `120.0`, not the SDK 10-minute default) | INTEGRATE | |
| constructor `max_retries=0` | INTEGRATE | |
| `http_client=DefaultAsyncHttpx2Client(trust_env=False)` | INTEGRATE | |
| `chat.completions.create` | INTEGRATE | |
| request `model` (default `deepseek-flash`) | INTEGRATE | |
| request `messages` (system + user) | INTEGRATE | |
| `response_format={"type":"json_object"}` | INTEGRATE | |
| `extra_body={"thinking":{"type":"disabled"}}` | INTEGRATE | |
| read `choices[0].message.content` only | INTEGRATE | |
| exception `APITimeoutError` | INTEGRATE | |
| exception `APIConnectionError` | INTEGRATE | |
| exception `RateLimitError` (HTTP 429) | INTEGRATE | |
| exception `InternalServerError` (HTTP 5xx) | INTEGRATE | |
| exception `AuthenticationError` (HTTP 401) | INTEGRATE | |
| exception `PermissionDeniedError` (HTTP 403) | INTEGRATE | |
| HTTP 400 whose `code` or `type` contains `context_length` | INTEGRATE | |
| other `APIStatusError`, including HTTP 402 | INTEGRATE | mapped to `unknown_llm_error`; no separate billing reason (RESEARCH A6) |
| SDK default retry loop (`max_retries` default 2) | OPT-OUT | not needed yet — one failure must map once (LLM-03); Phase 10 may add a bounded retry without changing reason codes |
| SDK default timeout of 10 minutes | OPT-OUT | not needed — a missing `json` word or thinking mode can burn that whole window; this phase sets 120 seconds |
| `trust_env=True` / inheriting `HTTP_PROXY` | OPT-OUT | explicitly out of scope — YouTube already has `YOUTUBE_PROXY_URL`; DeepSeek must not reuse it |
| `chat.completions.parse` / Pydantic `response_format` class | OPT-OUT | explicitly out of scope — D-11 is `json_object` plus `json.loads` plus `ArticleDraft`, not JSON schema |
| `response_format` type `json_schema` | OPT-OUT | same D-11 lock; schema mode is a different contract |
| `client.responses.create` (Responses API) | OPT-OUT | explicitly out of scope — DeepSeek's JSON sample is `chat.completions.create` |
| streaming (`stream=True`) | OPT-OUT | not needed — the contract is one JSON object, not a token stream |
| `message.reasoning_content` | OPT-OUT | explicitly out of scope — empty `content` is `invalid_json`; thinking is disabled so the article is not left on the reasoning channel |
| `finish_reason="length"` mapped to `provider_context_length` | OPT-OUT | explicitly out of scope — D-10 is a provider rejection, not an HTTP 200 cut; a short body is `invalid_json` or a returned draft |
| tools / `tool_choice` / function calling | OPT-OUT | not needed — the article is one JSON object with `title`, `dek`, and `body_markdown` |
| `temperature`, `top_p`, penalties, `logit_bias`, `seed`, `logprobs`, `n`, `stop` | OPT-OUT | not needed — sampling knobs are not part of the operator contract; provider defaults stand |
| `max_tokens` / `max_completion_tokens` | OPT-OUT | not needed — the budget is `len(transcript.text)` before the call (D-08); a completion cap would be a second, silent cut |
| `user`, `metadata`, `store`, `service_tier` | OPT-OUT | not needed — no provider-side prompt storage or end-user id in v1.1 |
| `embeddings` | OPT-OUT | explicitly out of scope — this phase does not embed |
| `images` | OPT-OUT | explicitly out of scope — prepared articles are markdown text |
| `audio` | OPT-OUT | explicitly out of scope — captions are already text; no Whisper bend |
| `files` | OPT-OUT | not needed — the transcript is an in-request message, not an uploaded file |
| `batches` | OPT-OUT | not needed — one video, one completion |
| `moderations` | OPT-OUT | not needed — honesty is a prompt rule (D-03); there is no moderation fail-closed check |
| `models.list` / model discovery | OPT-OUT | not needed — the model id comes from `DEEPSEEK_MODEL` |
| `fine_tuning` | OPT-OUT | explicitly out of scope |
| beta assistants / threads | OPT-OUT | explicitly out of scope — not the DeepSeek chat sample |
| legacy `completions.create` | OPT-OUT | explicitly out of scope — chat completions only |

## Notes

- The word `json` is required in the prompt because DeepSeek JSON mode otherwise streams whitespace until the token limit. That is a request constraint on `chat.completions.create`, not a second endpoint.
- Unit tests inject a stub client. No live DeepSeek call is a phase gate.
- No capability here writes to the database. Persist is Phase 9.
