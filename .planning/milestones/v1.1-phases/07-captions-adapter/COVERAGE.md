# API Coverage — Phase 7 Captions Adapter

> Full coverage by default. Opt-outs are explicit, reasoned decisions.

Phase 7 integrates two external surfaces: the `youtube-transcript-api` library (captions, pinned `>=1.2.0,<2`) and the YouTube oEmbed endpoint (`https://www.youtube.com/oembed`). Each surface is enumerated from its full capability list and decided independently — the oEmbed matrix does not inherit the captions opt-outs.

## Surface 1 — `youtube-transcript-api` (1.2.x)

| capability | decision | reason |
|---|---|---|
| `YouTubeTranscriptApi()` instance construction | INTEGRATE | |
| `proxy_config=GenericProxyConfig(http_url, https_url)` | INTEGRATE | |
| `.list(video_id)` — enumerate available tracks | INTEGRATE | |
| `TranscriptList` iteration + `language_code` inspection | INTEGRATE | |
| `Transcript.fetch()` — fetch the chosen track | INTEGRATE | |
| `FetchedTranscript` snippet text join | INTEGRATE | |
| Auto-generated track consumption (`is_generated` tracks) | INTEGRATE | |
| SOCKS5 proxy transport (via `PySocks`) | INTEGRATE | |
| Exception `TranscriptsDisabled` | INTEGRATE | |
| Exception `NoTranscriptFound` | INTEGRATE | |
| Exception `VideoUnavailable` | INTEGRATE | |
| Exception `InvalidVideoId` | INTEGRATE | |
| Exception `AgeRestricted` | INTEGRATE | |
| Exception `IpBlocked` | INTEGRATE | |
| Exception `RequestBlocked` | INTEGRATE | |
| Exception `PoTokenRequired` | INTEGRATE | |
| Exception `YouTubeRequestFailed` (non-429 HTTP failure, incl. YouTube 5xx) | INTEGRATE | mapped to `CaptionsNetworkError` → `network_error`; must not fall through to `unknown_captions_error`, which would read as a content problem instead of a transport problem (D-19 intent) |
| Exception `VideoUnplayable` | INTEGRATE | mapped to `CaptionsVideoUnavailable` → `video_unavailable` |
| Exception `YouTubeDataUnparsable` | INTEGRATE | handled via the base-`CaptionsError` catch-all → `unknown_captions_error`; a YouTube response-shape change is not separately actionable for an operator |
| Exception `FailedToCreateConsentCookie` | INTEGRATE | handled via the base-`CaptionsError` catch-all → `unknown_captions_error`; no cookie/consent bypass is in scope (D-19) |
| Raw `requests.exceptions.Timeout` / `ConnectionError` propagating through the SDK | INTEGRATE | mapped to `CaptionsNetworkError` → `network_error`; `requests[socks]` is declared on `data-collection` so the caught types are a first-class dependency (D-18) |
| Exception `CouldNotRetrieveTranscript` (catch-all) | INTEGRATE | |
| `.fetch(video_id, languages=[...])` convenience fast path | OPT-OUT | superseded by list-then-pick — dialect base normalization (D-07) and `available_languages` in `no_preferred_language` (D-09) both require `.list()`; one code path is cheaper to test |
| `WebshareProxyConfig` | OPT-OUT | vendor-specific; the verified path is a generic AdGuard SOCKS endpoint via `GenericProxyConfig` (D-16) |
| Custom `http_client` / `requests.Session` injection | OPT-OUT | not needed — proxying is handled by `GenericProxyConfig` built in composition (D-16, D-17) |
| `cookie_path` / authenticated cookie access | OPT-OUT | explicitly out of scope — no cookie or poToken bypass in v1.1 (D-19) |
| `find_manually_created_transcript` / `find_generated_transcript` | OPT-OUT | D-06/D-08 lock "no manual-over-auto ranking"; preference is language-only, so the manual/auto finders add an unused ranking axis (manual preference deferred to v1.2+) |
| `find_transcript(languages)` | OPT-OUT | same list-then-pick reason as the `fetch` fast path — dialect bases are resolved in adapter code, not by the library matcher |
| `Transcript.translate(...)` + `translation_languages` | OPT-OUT | any-language fallback and translation markers are deferred to v1.2+ (D-09); translated captions would be provenance-unsafe for LLM input |
| `preserve_formatting=True` | OPT-OUT | not needed — the LLM consumes plain text; formatting markup would pollute `Transcript.text` |
| Snippet timing fields (`start`, `duration`) / `to_raw_data()` | OPT-OUT | not needed — the Phase 6 `Transcript` DTO has no timing fields and stores joined text only (Phase 6 D-09) |
| Formatters (`JSONFormatter`, `TextFormatter`, `SRTFormatter`, `WebVTTFormatter`) | OPT-OUT | not needed — no caption file export in this milestone; captions never become a stored artifact (D-CONTENT-01) |
| `youtube_transcript_api` command-line interface | OPT-OUT | explicitly out of scope — the operator entry point is the Phase 10 Typer one-shot, not the library CLI |

## Surface 2 — YouTube oEmbed (`https://www.youtube.com/oembed`)

| capability | decision | reason |
|---|---|---|
| `GET /oembed?url=<canonical watch URL>` | INTEGRATE | |
| Request param `format=json` | INTEGRATE | |
| Canonical watch URL construction `https://www.youtube.com/watch?v={video_id}` | INTEGRATE | |
| Response field `author_name` | INTEGRATE | |
| HTTP 404 handling (video missing / private) | INTEGRATE | |
| HTTP 403 handling (blocked / restricted) | INTEGRATE | |
| Timeout / connection-failure handling | INTEGRATE | |
| Malformed or non-JSON body handling | INTEGRATE | |
| Proxy transport via `httpx[socks]` | INTEGRATE | |
| Request param `format=xml` | OPT-OUT | not needed — JSON is parsed directly by `httpx`; a second response format doubles the parse surface |
| Request params `maxwidth` / `maxheight` | OPT-OUT | not needed — these only size the embed `html`/thumbnail, which are themselves opted out |
| Response field `title` | OPT-OUT | not needed — the material title is generated by the LLM into `MaterialDraft` in Phase 8; a YouTube title is not the article title |
| Response field `author_url` | OPT-OUT | not needed — the Phase 6 `VideoMetadata` DTO has no channel-URL field (field shapes locked) |
| Response fields `thumbnail_url` / `thumbnail_width` / `thumbnail_height` | OPT-OUT | not needed — no media or imagery is stored for drafts (D-CONTENT-01) |
| Response field `html` (iframe embed markup) | OPT-OUT | not needed — prepared articles do not embed the source player in this milestone; untrusted HTML would be an injection surface |
| Response fields `provider_name` / `provider_url` / `type` / `version` / `width` / `height` | OPT-OUT | not needed — constant or presentational metadata with no consumer in `VideoMetadata` |
| Publish date | OPT-OUT | not offered by oEmbed — `VideoMetadata.published_at` stays `None` (Phase 6 D-12 allows nullable); Data API v3 for real publish dates is out of milestone scope |
| Authenticated / API-key YouTube Data API v3 endpoints | OPT-OUT | explicitly out of scope — oEmbed is keyless and sufficient for the required `source_author` provenance (D-21, D-22) |

## Notes

- Both surfaces are reached only through injected clients built in `ingestion-service` composition; adapters never read `os.environ` (D-17).
- Every integrated failure mode maps to a locked operator `reason` code; SDK/HTTP exception class names never become the `reason` (D-10).
- No capability here writes to the database — Phase 7 has no persist path (CAP-02 unit-level proof; live zero-row spy deferred to Phase 9/10 per D-14).
