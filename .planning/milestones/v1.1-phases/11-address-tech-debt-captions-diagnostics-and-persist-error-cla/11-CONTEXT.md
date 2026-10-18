# Phase 11: Address tech debt: captions diagnostics and persist error classification - Context

**Gathered:** 2026-10-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Close the v1.1 milestone audit tech debt for captions diagnostics and persist error classification so the operator CLI stays fail-closed, secret-safe, and honest on re-runs:

1. Captions / URL diagnostic envelopes never leak SDK text, proxy credentials, or credentialed URLs on stderr.
2. SDK exceptions outside the locked captions catalog map to the existing `unknown_captions_error` fallback — never a traceback.
3. Persist adapter classification correctly recognizes SQLSTATE `23514` and numeric HTTP gateway statuses without changing `PERSIST_REASONS`.
4. Re-run when the only shortlist row sits on a sent batch returns `already_saved: true` with exit 0 via an RPC fix (return existing material ids; do not raise).

This phase does not add logging infrastructure, `--debug`, new `IngestError` stages, new persist/captions reason codes, admin/email preview work, DTO barrel fixes from Phase 6, or Nyquist reconcile for phases 6–8.

</domain>

<decisions>
## Implementation Decisions

### Captions / stderr diagnostics
- **D-01:** Operator-facing `IngestError` JSON on stderr carries only locked `stage` / `reason` plus `video_id` (and existing allowlisted context keys already in the mapper). The `message` field is built from `reason` + `video_id` only — never raw SDK text, never proxy credentials, never a credentialed URL. — **Reversibility:** costly — stderr JSON is the operator contract (Phase 10 D-05 / Phase 7 CR-01).
- **D-02:** Do not expand captions or URL context allowlists. Keep the locked allowlists from Phase 7.
- **D-03:** SDK exception text is discarded at the adapter/mapper boundary. Phase 11 introduces no log file, no structlog, and no debug channel. Developer debugging of raw SDK text is out of scope until Phase 12+.

### SDK exceptions outside the captions catalog
- **D-04:** CookieInvalid and any other base SDK exception that escapes the typed `CaptionsError` catch chain must be caught and raised as a typed path that maps to the existing reason `unknown_captions_error`. Do not add new captions reasons. Do not expand the `IngestError` stage set (Phase 10 D-08). — **Reversibility:** costly — reason catalog and stage set are operator contracts.
- **D-05:** A traceback must never reach the operator terminal on a captions-stage failure. Pipeline failures remain `IngestError.to_dict()` JSON on stderr with a non-zero exit.

### Persist error classification
- **D-06:** Fix recognition only: treat SQLSTATE `23514` the same as the named `check_violation` path already expected by `_BATCH_CODES`; treat numeric HTTP status codes on non-JSON gateway errors as the existing `rpc_error` branch (read status when string `code` is absent). — **Reversibility:** reversible — classification is adapter-local.
- **D-07:** Do not add, rename, or remove entries in `PERSIST_REASONS` (Phase 9 D-04). Happy-path and idempotent re-run stdout contracts stay unchanged.

### Sent-batch re-run (already_saved)
- **D-08:** When a material already exists and its only shortlist row is on a sent batch (`sent_at IS NOT NULL`), the run must succeed with exit 0 and print `already_saved: true` with the stored `material_id` / `slug` / `batch_id` / `rank` from the existing row — consistent with Phase 10 D-09 / D-10. — **Reversibility:** costly — stdout contract.
- **D-09:** Implement D-08 in the `persist_draft_and_enqueue` RPC: on that edge, return the existing material/shortlist ids with `already_saved: true` instead of raising `P0001`. Do not insert a second `materials` row and do not refresh draft content. — **Reversibility:** one-way — undo needs a follow-up migration of the SECURITY DEFINER RPC (same class as migrations 007/008).

### Carried forward (do not re-open)
- Phase 10 D-05 / D-08: pipeline failures are `IngestError.to_dict()` JSON on stderr; stage set stays `url`, `captions`, `metadata`, `consistency`, `llm`, `llm_truncation`, `persist`.
- Phase 10 D-09 / D-10 / D-12: `already_saved` line on success; re-run exit 0; stored slug/ids on conflict.
- Phase 9 D-04 / D-09..D-11: persist mapper + locked reasons; idempotency in RPC; no Python video_id pre-check; no content refresh on re-run.
- Phase 7 CR-01 / D-13: context allowlists and credential redaction on diagnostic envelopes.

### Claude's Discretion
- Exact catch placement for base SDK exceptions (adapter vs thin wrapper) as long as D-04 / D-05 hold and TDD is followed.
- Exact RPC SELECT for “existing row on sent batch” (which shortlist row / ordering) as long as D-08 / D-09 hold and no second material is inserted.
- How unit tests simulate SQLSTATE `23514` and numeric HTTP statuses without a live network.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Audit / debt source
- `.planning/v1.1-MILESTONE-AUDIT.md` — tech_debt for phases 7 and 10 (CR-01, WR-01..WR-04 captions/URL; WR-01..WR-02 persist classification; CLI-02 sent-batch edge)

### Prior phase locks
- `.planning/phases/07-captions-adapter/07-CONTEXT.md` — captions reasons, context allowlists, CR-01 redaction intent
- `.planning/phases/09-draft-persist-shortlist-enqueue/09-CONTEXT.md` — PersistPort, `PERSIST_REASONS`, RPC idempotency
- `.planning/phases/10-cli-composition-uat/10-CONTEXT.md` — stderr JSON contract, `already_saved`, stage set freeze (D-05, D-08, D-09, D-10, D-12)

### Requirements / project
- `.planning/REQUIREMENTS.md` — CAP-02, PERS-01/02, CLI-01/02/04 (satisfied; this phase hardens classification/diagnostics)
- `.planning/PROJECT.md` — fail-closed ingestion, ports & adapters

### Implementation surfaces
- `data-collection/src/data_collection/adapters/youtube_transcript.py` — captions catch chain / snippet join
- `data-collection/src/data_collection/errors/captions.py` — `CaptionsError` taxonomy
- `ingestion-service/src/ingestion_service/mapping/captions.py` — `CAPTIONS_REASONS`, allowlist, `unknown_captions_error`
- `ingestion-service/src/ingestion_service/mapping/url.py` — URL diagnostic context forwarding
- `ingestion-service/src/ingestion_service/mapping/persist.py` — `PERSIST_REASONS` (must not change)
- `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` — `_BATCH_CODES`, `_sdk_code`, classification
- `ingestion-service/src/ingestion_service/domain/errors.py` — `IngestError.to_dict()`
- `supabase-integration/migrations/008_phase10_persist_already_saved.sql` — current conflict / sent-batch raise path (canonical starting point for D-09 amend)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `map_captions_error` / `map_persist_error` — locked reason frozensets + context allowlists; extend catch/classification only.
- `IngestError.to_dict()` — CLI already prints this on pipeline failure.
- `FakeDraftPersister` — in-memory persist fake for unit tests (sent-batch / already_saved edges).
- Migration 008 — amend pattern for `persist_draft_and_enqueue` already established (human Studio apply).

### Established Patterns
- Adapter raises typed errors; mapper builds `IngestError(stage, reason, message, context)`.
- Persist classification uses frozensets of code strings (`_BATCH_CODES`, conflict codes).
- TDD: failing unit test first for each classification / redaction / RPC-contract behavior.

### Integration Points
- Captions adapter catch chain in `youtube_transcript.py` → mapper → pipeline → CLI stderr.
- Persist adapter exception → `map_persist_error` → pipeline.
- RPC `persist_draft_and_enqueue` conflict branch currently raises when no unsent shortlist row exists.

</code_context>

<specifics>
## Specific Ideas

- Path shape for captions failures: SDK exception → `CaptionsError` subtype (or map-to-unknown) → mapper → `IngestError(stage, reason)` → JSON stderr. No SDK text in stderr, no file, no debug log.
- Persist: `23514` must classify like `check_violation`; numeric HTTP status must not fall through incorrectly relative to the existing `rpc_error` intent.
- Sent-batch: fix in RPC return payload, not a Python pre-check.

</specifics>

<deferred>
## Deferred Ideas

### Phase 12+ (explicitly deferred this discussion)
- Optional `--debug` flag that may emit SDK text on stderr for developers.
- Optional file-based structured logging for the CLI (do not pull backend structlog into `ingestion-service` in Phase 11).

### Out of this phase title (accept or schedule separately)
- Phase 6 DTO barrel / language-strip / naive datetime debt.
- Phase 7 WR-03 caption snippet separator and WR-04 oEmbed 5xx/429 taxonomy (only if needed to satisfy D-01..D-05; otherwise leave unless planner proves they block diagnostics).
- Phase 8 wheel packaging of lecture/podcast templates.
- Phase 10 FakeDraftPersister.seed_item already_saved fidelity (test-fake only) unless required to prove D-08.
- Admin preview / email-HTML / draft→ready UI follow-ups from UAT.
- Nyquist `/gsd-validate-phase` for phases 6–8.

</deferred>

---

*Phase: 11-Address tech debt: captions diagnostics and persist error classification*
*Context gathered: 2026-10-02*
