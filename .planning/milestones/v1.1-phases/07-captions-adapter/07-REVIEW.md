---
phase: 07-captions-adapter
reviewed: 2026-09-27T09:15:00Z
depth: standard
files_reviewed: 38
files_reviewed_list:
  - data-collection/pyproject.toml
  - data-collection/src/data_collection/__init__.py
  - data-collection/src/data_collection/adapters/__init__.py
  - data-collection/src/data_collection/adapters/youtube_oembed.py
  - data-collection/src/data_collection/adapters/youtube_transcript.py
  - data-collection/src/data_collection/errors/__init__.py
  - data-collection/src/data_collection/errors/captions.py
  - data-collection/src/data_collection/errors/metadata.py
  - data-collection/src/data_collection/ports/__init__.py
  - data-collection/src/data_collection/ports/video_metadata_provider.py
  - data-collection/src/data_collection/tests_support/fakes.py
  - docs/agents/local-platform-runbook.md
  - ingestion-service/pyproject.toml
  - ingestion-service/src/ingestion_service/__init__.py
  - ingestion-service/src/ingestion_service/composition/__init__.py
  - ingestion-service/src/ingestion_service/composition/clients.py
  - ingestion-service/src/ingestion_service/composition/settings.py
  - ingestion-service/src/ingestion_service/domain/__init__.py
  - ingestion-service/src/ingestion_service/domain/errors.py
  - ingestion-service/src/ingestion_service/mapping/__init__.py
  - ingestion-service/src/ingestion_service/mapping/captions.py
  - ingestion-service/src/ingestion_service/mapping/metadata.py
  - ingestion-service/src/ingestion_service/mapping/url.py
  - ingestion-service/src/ingestion_service/url.py
  - pyproject.toml
  - tests/integration/test_youtube_captions_live.py
  - tests/integration/test_youtube_oembed_live.py
  - tests/unit/test_captions_error_mapping.py
  - tests/unit/test_data_collection_public_api.py
  - tests/unit/test_extract_video_id.py
  - tests/unit/test_fake_transcript_provider_failures.py
  - tests/unit/test_fake_video_metadata_provider.py
  - tests/unit/test_ingest_error.py
  - tests/unit/test_ingestion_settings.py
  - tests/unit/test_metadata_error_mapping.py
  - tests/unit/test_youtube_oembed_adapter.py
  - tests/unit/test_youtube_transcript_adapter.py
  - uv.lock
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues
---

# Phase 07: Code Review Report

**Reviewed:** 2026-09-27T09:15:00Z
**Depth:** standard
**Files Reviewed:** 38
**Status:** issues_found

## Summary

Adversarial STANDARD re-review of Phase 7 Captions Adapter (URL allowlist, `YouTubeTranscriptAdapter`, CaptionsError + `map_captions_error`, oEmbed/`VideoMetadataProvider`, MetadataError + `map_metadata_error`, composition proxy wiring, fakes, unit/integration tests, workspace pyprojects/lock, runbook).

Happy-path contracts hold: SDK imports stay in adapters + `composition/clients.py`; `data-collection` errors have no `stage` vocabulary; D-10 / metadata reason tables match locked frozensets; host allowlist is exact `hostname` membership; oEmbed uses canonical watch URL only; `YouTubeRequestFailed` / `RequestException` precede `CouldNotRetrieveTranscript`; adapters do not read `os.environ`; public `__all__` is seven names; fakes remain additive.

One critical diagnostic redaction hole remains, plus five warnings (SDK/AttributeError boundary leaks, URL credential forwarding, caption join glue, 5xx/429 mislabeled as unavailable).

## Critical / BLOCKER

### CR-01: Context allowlist redacts `context` but secrets still leak via `message`

**File:** `data-collection/src/data_collection/errors/captions.py:11-16`
**File:** `data-collection/src/data_collection/errors/metadata.py:11-16`
**File:** `ingestion-service/src/ingestion_service/mapping/captions.py:65-72`
**File:** `ingestion-service/src/ingestion_service/mapping/metadata.py:49-56`
**Evidence:** `CaptionsError` / `MetadataError` embed the full `context` kwargs in `Exception` message (`f"…: {context}"`). Mappers set `message=str(error)` after allowlisting only `IngestError.context`. Re-verified 2026-09-27: with `proxy_url="socks5://user:secret@…"`, `to_dict()["context"]` omits secrets but `to_dict()["message"]` still contains `secret` and the SOCKS URL. Unit redaction tests (`test_captions_error_mapping.py:110-127`, `test_metadata_error_mapping.py:60-77`) assert only `mapped.context`, never `message` / `to_dict()["message"]`. Note: current adapters only forward `exception_class` / `status_code` / `available_languages` (SDK `ProxyError` text does not enter context today) — the hole is the exception/mapper contract, which Phase 10 CLI will serialize via `to_dict()`.
**Why it matters:** D-13 and runbook require diagnostics without free-form secret dumps. Allowlist-only-on-context is incomplete defense; any non-allowlisted key (or future accidental `proxy_url=`) becomes durable operator JSON.
**Fix:** Stop embedding raw `context` in adapter exception messages (fixed safe string, e.g. `f"captions error for {video_id}"`). In mappers, build `message` from reason + `video_id` only — never `str(error)` if it may contain non-allowlisted keys. Extend redaction tests to assert `"secret" not in mapped.message` and `"socks5://" not in mapped.to_dict()["message"]`.

## Warnings

### WR-01: SDK `Cookie*` / base `YouTubeTranscriptApiException` escape the adapter boundary

**File:** `data-collection/src/data_collection/adapters/youtube_transcript.py:54-90`
**Evidence:** Catch chain maps subtypes of `CouldNotRetrieveTranscript` + `RequestException`, then catch-all `CouldNotRetrieveTranscript`. `CookieInvalid` / `CookieError` inherit `YouTubeTranscriptApiException`, **not** `CouldNotRetrieveTranscript`. Re-verified: `YouTubeTranscriptAdapter.get` with `list()` raising `CookieInvalid` propagates `youtube_transcript_api._errors.CookieInvalid` — not a `CaptionsError`.
**Why it matters:** Focus rule “SDK types must NOT escape adapters”. Callers / Phase 10 CLI cannot map an uncaught SDK exception through `map_captions_error`; CAP-02 fail-closed breaks for cookie misconfig and any future non-`CouldNotRetrieve*` SDK errors.
**Fix:** Add `except YouTubeTranscriptApiException as exc: raise CaptionsError(video_id, exception_class=…) from exc` after the specific handlers (or map `CookieError` → blocked/network as product decides). Add a unit case that `CookieInvalid` becomes `CaptionsError` (or a dedicated subtype) with `exception_class` only.

### WR-02: `map_url_error` forwards raw operator URL (incl. userinfo credentials)

**File:** `ingestion-service/src/ingestion_service/url.py:23-27,39-41`
**File:** `ingestion-service/src/ingestion_service/mapping/url.py:9-15`
**Evidence:** Allowlist uses `parsed.hostname` (so `https://user:passwd@www.youtube.com/watch?v=…` is accepted as YouTube). `InvalidYouTubeUrl.context` always includes `"value": value` (full original string). `map_url_error` copies `dict(error.context)` with no allowlist; `message=str(error)` also embeds `value!r`. Re-verified: mapped envelope for `https://user:passwd@…/watch?v=SHORT` and `https://user:secret@evil.com/…` contains credentials in both `message` and `context.value`.
**Why it matters:** Captions/metadata mappers redact; URL stage does not. Credentialed or tokenized URLs pasted by operators become durable diagnostic JSON (same class of leak as CR-01).
**Fix:** Strip userinfo before storing `value` (or store only scheme+host+path+safe query). Allowlist URL context keys. Assert redaction in `test_ingest_error` / extract tests for a `user:secret@` input.

### WR-03: Caption snippets joined with `""` glue words when snippets lack trailing spaces

**File:** `data-collection/src/data_collection/adapters/youtube_transcript.py:115-116`
**Evidence:** `joined = "".join(getattr(s, "text", str(s)) for s in snippets).strip()`. Re-verified with two snippets `"Hello"` + `"world"` → `Transcript.text == "Helloworld"`. Happy-path unit tests only use single-snippet tracks (`["привет"]`, `["hello"]`); no multi-snippet spacing contract.
**Why it matters:** CAP-01 / Phase 8 LLM consume joined caption text. Glued tokens degrade article quality and are easy to miss until live captions. youtube-transcript-api snippets often omit inter-snippet separators.
**Fix:** Join with a single space (or normalize whitespace after join). Add a unit assert that `["Hello", "world"]` → `"Hello world"`.

### WR-04: Non-200 oEmbed statuses (incl. 5xx / 429) map to `MetadataUnavailable`

**File:** `data-collection/src/data_collection/adapters/youtube_oembed.py:53-61`
**Evidence:** 404/403 and every other `status_code != 200` raise `MetadataUnavailable` (re-verified `500` and `429` → `MetadataUnavailable` with `status_code` set). Only transport exceptions become `MetadataNetworkError`. Mapper then emits `reason=metadata_unavailable`.
**Why it matters:** Operators following D-16 / runbook will treat rate-limits and upstream 5xx as “video has no metadata,” chasing content instead of proxy/backoff — same ops-misdiagnosis class called out for IP blocks vs missing captions.
**Fix:** Map 5xx and 429 → `MetadataNetworkError` (keep 404/403 as `MetadataUnavailable`). Extend `test_youtube_oembed_adapter` with status parametrization.

### WR-05: Malformed track `language_code` raises bare `AttributeError` past the adapter

**File:** `data-collection/src/data_collection/adapters/youtube_transcript.py:37-38,99-104`
**Evidence:** `_base_lang` does `code.split("-")` with no guard. Re-verified: track with `language_code=None` (or missing attribute) → `AttributeError` escapes `YouTubeTranscriptAdapter.get` — not a `CaptionsError`.
**Why it matters:** CAP-02 / adapter-boundary contract: failures must be taxonomy errors mappable to `IngestError`. Corrupt or unexpected SDK track shapes bypass mapping the same way as WR-01.
**Fix:** Coerce/skip tracks with non-string `language_code`, or wrap `_fetch_inner` unexpected errors into `CaptionsError(video_id, exception_class=…)`. Add a unit case for `language_code=None`.

## Info

### IN-01: Redaction unit tests only cover `context`, not the envelope `message`

**File:** `tests/unit/test_captions_error_mapping.py:110-127`
**File:** `tests/unit/test_metadata_error_mapping.py:60-77`
**Issue:** Assertions stop at `mapped.context` / `str(mapped.context)`, which is why CR-01 shipped green. Harden tests to cover `message` and full `to_dict()` serialization.

### IN-02: Live integration stubs never call YouTube

**File:** `tests/integration/test_youtube_captions_live.py:18-21`
**File:** `tests/integration/test_youtube_oembed_live.py:18-21`
**Issue:** With `RUN_YOUTUBE_INTEGRATION=1`, tests only `assert _LIVE is True`. Acceptable as Phase 7 gated stubs (D-20 / 07-03 SUMMARY), but they do not prove live captions/oEmbed; Phase 10 must replace stubs with real wiring or operators will think live proof already exists.

### IN-03: Adapter constructors typed as `Any`

**File:** `data-collection/src/data_collection/adapters/youtube_transcript.py:48`
**File:** `data-collection/src/data_collection/adapters/youtube_oembed.py:32`
**Issue:** Architecture discourages loose `Any` at module boundaries. Prefer a narrow Protocol (`list(video_id)`, async `get(url, params=…)`) so typecheckers catch wiring mistakes without importing concrete SDK types into ports.

## Checks that passed (adversarial)

| Focus | Result |
|-------|--------|
| SDK leak into ports / domain / mappers | Pass for happy path — ports/DTOs/mappers import only data-collection errors/DTOs; SDK confined to adapters + `composition/clients.py` |
| data-collection `stage` vocabulary | Pass — no `stage` / `IngestError` in captions/metadata error modules |
| D-10 reason codes | Pass — `CAPTIONS_REASONS` exact nine codes; subtype table matches tests |
| Exception ordering | Pass — `YouTubeRequestFailed` then `RequestException` before `CouldNotRetrieveTranscript` |
| Context allowlist (context dict only) | Pass for keys — fail for message (CR-01) |
| Host SSRF allowlist | Pass — exact `hostname` membership; look-alikes and `/live\|/v\|/e` rejected |
| oEmbed canonical URL | Pass — only `_OEMBED_ENDPOINT` + `watch?v={video_id}`; operator URL never passed to HTTP |
| `os.environ` in adapters | Pass — composition/`Settings.from_env` owns proxy |
| Public `__all__` | Pass — exactly seven names; adapters/errors/fakes off root barrel |
| Fake failures additive | Pass — both fakes preserve positional construction |
| SDK ProxyError text in adapter path | Pass today — only `exception_class` name forwarded (CR-01 still applies to kwargs-in-message design) |
| Workspace / SOCKS deps | Pass — `httpx[socks]`, `requests[socks]`, `ingestion-service` member, integration marker present |
| Runbook D-20 / proxy | Pass — `YOUTUBE_PROXY_URL` + live gate documented |

---

_Reviewed: 2026-09-27T09:15:00Z_
_Reviewer: gsd-code-reviewer (standard)_
_Depth: standard_
_Diff base: de989c61b44a398b5689d99445d98dcffec69b55_
