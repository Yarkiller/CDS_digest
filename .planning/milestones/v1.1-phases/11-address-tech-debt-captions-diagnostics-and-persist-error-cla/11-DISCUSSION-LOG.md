# Phase 11: Address tech debt: captions diagnostics and persist error classification - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-02
**Phase:** 11-address-tech-debt-captions-diagnostics-and-persist-error-cla
**Areas discussed:** Captions stderr diagnostics, SDK exceptions outside catalog, Persist classification, Sent-batch re-run

---

## Captions stderr diagnostics

| Option | Description | Selected |
|--------|-------------|----------|
| reason + video_id only; SDK text to log file | Tight stderr; SDK elsewhere | (superseded) |
| reason + video_id only; SDK text discarded | No log file in Phase 11 | ✓ |
| Allowlist expansion / keep SDK in message | Rejected — CR-01 | |

**User's choice:** stderr JSON message = reason + video_id only; do not expand allowlist; discard SDK text (no file, no debug log in Phase 11).
**Notes:** Consistency with Phase 7 CR-01. Logging deferred to Phase 12+ (`--debug` / file structured log). Rationale: classification fix only; operator acts on reason + video_id; SDK text is for developers; CLI must not pull backend structlog.

---

## SDK exceptions outside catalog

| Option | Description | Selected |
|--------|-------------|----------|
| Map to existing `unknown_captions_error` | No new reasons / stages | ✓ |
| Add dedicated Cookie*/SDK reasons | Expand catalog | |
| Allow traceback | Rejected | |

**User's choice:** Outside-catalog SDK exceptions → `unknown_captions_error`. Traceback never escapes.
**Notes:** Stage set freeze (Phase 10 D-08) reaffirmed.

---

## Persist classification

| Option | Description | Selected |
|--------|-------------|----------|
| Fix recognition only (`23514`, numeric HTTP) | Keep `PERSIST_REASONS` | ✓ |
| Expand / rename persist reasons | Rejected — Phase 9 D-04 | |

**User's choice:** Fix adapter recognition; reasons unchanged.
**Notes:** Happy-path and idempotent re-run paths unchanged.

---

## Sent-batch re-run

| Option | Description | Selected |
|--------|-------------|----------|
| `already_saved: true`, exit 0 via RPC return | Align D-09/D-10 | ✓ |
| Keep `stage=persist` / P0001 raise | Honest error | |

**User's choice:** RPC returns existing ids with `already_saved: true`; no raise; no second materials row.
**Notes:** One-way migration amend of `persist_draft_and_enqueue`.

---

## Claude's Discretion

- Catch placement for base SDK exceptions
- RPC SELECT / ordering for sent-batch existing row
- Unit-test simulation of `23514` and numeric HTTP statuses

## Deferred Ideas

- Phase 12+: optional `--debug` and file-based structured log
- Phase 6 DTO debt, Phase 8 wheel templates, admin/email UAT follow-ups, Nyquist 6–8
- Phase 7 WR-03/WR-04 unless planner proves they block D-01..D-05
