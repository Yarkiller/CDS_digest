# Phase 7: Captions Adapter - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-26
**Phase:** 7-Captions Adapter
**Areas discussed:** URL → video_id rules, Language preference policy, Fail-closed error surface, Captions network / proxy, VideoMetadata/oEmbed coupling

---

## URL → video_id rules

| Option | Description | Selected |
|--------|-------------|----------|
| Common watch forms only | `watch?v=` + `youtu.be` | |
| Common + Shorts + embed | Also `/shorts/`, `/embed/` | ✓ |
| Any extractable 11-char id | Also `/live/`, etc. | |
| You decide | Claude picks | |

**User's choice:** Common + Shorts + embed with explicit accept/reject/normalize/strip rules; defer `/live/`, `/v/`, `/e/`; `extract_video_id` in `ingestion-service/` (~25 lines), not on the port.
**Notes:** Also accepted bare 11-char id. Parse failures → `stage=url`; caption failures → `stage=captions`. CAP-02 is captions-only.

---

## Language preference policy

| Option | Description | Selected |
|--------|-------------|----------|
| Allow auto | Manual or auto if language matches | ✓ |
| Manual only | Reject ASR-only | |
| Prefer manual, fall back to auto | Quality ranking | |
| You decide | Claude picks | |

**User's choice:** Allow auto; prefix-normalize dialects to base `ru`/`en` on `Transcript.language`; always prefer any `ru` then any `en`; fail `no_preferred_language` with available languages listed; no any-language fallback in v1.1.
**Notes:** Tests for `ru`, `ru-RU`, `en`, `en-US`, `rue` (no match). Manual-preference deferred v1.2+.

---

## Fail-closed error surface

| Option | Description | Selected |
|--------|-------------|----------|
| Coarse one reason | `unavailable` for all | |
| Mapped reasons | Stable reason codes | ✓ |
| Pass-through SDK names | Couple CLI to library | |
| You decide | Claude picks | |

**User's choice:** Mapped captions reasons; `IngestError` in `ingestion-service/domain/` (not data-collection); `CaptionsError` hierarchy in data-collection mapped by use-case; diagnostic JSON `{ok, stage, reason, message, context?, exit_code}`; Phase 7 adapter/unit CAP-02 only; additive `FakeTranscriptProvider.failures` dict.
**Notes:** Stages include `url`, `captions`, `metadata`, `consistency`, `llm`, `llm_truncation`, `persist`. Live zero-DB spy deferred Phase 9/10 (roadmap note). `bot_challenge` added later under proxy discussion.

---

## Captions network / proxy

| Option | Description | Selected |
|--------|-------------|----------|
| Optional env proxy only | Captions-specific | |
| Same shared proxy as oEmbed | One `YOUTUBE_PROXY_URL` | ✓ |
| Hard-require proxy | Always need URL | |
| No proxy wiring in Phase 7 | Direct only | |
| You decide | Claude picks | |

**User's choice:** Shared optional `YOUTUBE_PROXY_URL`; composition injects clients; SOCKS extras for AdGuard; `bot_challenge` ≠ `youtube_blocked`; unit CI + optional `@pytest.mark.integration`.
**Notes:** Document Cloud.ru risk without proxy. Adapters do not read `os.environ`.

---

## VideoMetadata / oEmbed coupling

| Option | Description | Selected |
|--------|-------------|----------|
| Captions-only | oEmbed later | |
| Captions + oEmbed now | Both adapters in Phase 7 | ✓ |
| Captions + metadata port stub | Fake only | |
| You decide | Claude picks | |

**User's choice:** Ship both providers/adapters/errors/fakes; `VideoMetadataProvider.get(video_id)`; fail closed on metadata; `stage=metadata`; captions-then-metadata composition order; small `MetadataError` set.
**Notes:** Canonical watch URL built inside oEmbed adapter. No `"unknown"` author fabrication.

---

## Claude's Discretion

- Exact adapter/error file layout under `data-collection`
- Exact subtype ↔ `reason` mapping table details
- Whether `bot_challenge` is its own `CaptionsError` subtype vs mapped via context
- Integration-test marker / skip wiring details

## Deferred Ideas

- `/live/`, `/v/`, `/e/` URL forms
- Any-language caption fallback (v1.2+)
- Manual-over-auto within language (v1.2+)
- PoToken bypass for `bot_challenge`
- Author fallback on metadata failure (v1.2+)
- Phase 9/10 persist spy for live CAP-02 zero rows
- LLM / persist / CLI one-shot / CONSISTENCY-01 — later phases
