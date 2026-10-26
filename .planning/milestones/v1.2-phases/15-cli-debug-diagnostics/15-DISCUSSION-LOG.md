# Phase 15: CLI --debug diagnostics - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-04
**Phase:** 15-cli-debug-diagnostics
**Areas discussed:** Debug stream & format, Diagnostic content, Redaction / leak protection, Failure behavior

---

## Debug stream & format

| Option | Description | Selected |
|--------|-------------|----------|
| stderr | Keep stdout as the machine-readable result contract; debug does not break pipes | ✓ |
| stdout | Everything in one stream, simpler by eye but breaks result parsing | |
| both | Duplicate into both streams | |

| Option | Description | Selected |
|--------|-------------|----------|
| Human-readable `[debug] …` | Consistent with existing `✓ transcript/LLM/saved` | ✓ |
| JSON-lines | One object per stage; machine-readable but visually heavy | |
| Single JSON summary | No real-time progress | |

| Option | Description | Selected |
|--------|-------------|----------|
| Timestamp + level `[12:03:44] debug …` | Best for an operator | ✓ |
| `[debug]` only | No timestamp | |
| No prefix | Plain lines | |

**User's choice:** stderr; human-readable `[debug]` lines; timestamp + level.
**Notes:** stdout must remain parseable; level token kept for future `--trace`.

---

## Diagnostic content

| Option | Description | Selected |
|--------|-------------|----------|
| Timings | Elapsed ms per stage | ✓ |
| Sizes/counters | Transcript chars/words, language, segments | ✓ |
| LLM params | Template, prompt/response length, tokens | ✓ |
| Reason codes | stage, reason, exit_code | ✓ |
| Persist identifiers | material_id/slug/batch_id/rank/already_saved | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Stage summary | One line per stage | ✓ |
| Verbose per-step | Internal sub-steps | |

| Option | Description | Selected |
|--------|-------------|----------|
| Sanitized metadata | video_id, author, template | |
| video_id only | Minimal identifier | ✓ |
| No metadata | | |

**User's choice:** all signal groups; stage-level summary; `video_id` only.
**Notes:** operator wants breadth of signals but a clean, non-verbose presentation.

---

## Redaction / leak protection

| Option | Description | Selected |
|--------|-------------|----------|
| Allowlist | Print only explicitly safe fields | |
| Denylist | Print everything, mask known secrets | |
| Hybrid | Allowlist default + denylist safety net | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Secret/key values | SUPABASE_SECRET_KEY, DEEPSEEK_API_KEY, … | ✓ |
| Proxy credentials & cookies | Required by DBG-02 (covered by allowlist; added to denylist net) | |
| Auth headers/tokens/session | | |
| Full transcript/prompt bodies | Only lengths/counters, never text | ✓ |
| Raw URL with query params | Only video_id | |

| Option | Description | Selected |
|--------|-------------|----------|
| Silently mask/omit | Debug must not break ingest | ✓ |
| Fail-closed on violation | Stricter but can block ingest | |

**User's choice:** hybrid; never-print = secret values + full bodies; mask on violation.
**Notes:** DBG-02 explicitly mandates proxy credentials and cookies too — these are covered
by the allowlist design and added to the denylist safety net for defense-in-depth, so the
requirement holds without overriding the operator's selection.

---

## Failure behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Completed + failed stage | Completed stages' debug plus the failed stage with reason | ✓ |
| Completed only | No failed-stage line | |
| No debug on error | Only the JSON error | |

| Option | Description | Selected |
|--------|-------------|----------|
| Record failed timing | Show how long the stage ran before failing | ✓ |
| Skip failed timing | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Debug `stage=config`, no IngestError | D-08 human-text contract preserved | ✓ |
| No debug for config errors | Current behavior | |

**User's choice:** completed stages + failed stage reason; record failed timing; config
debug line without IngestError.
**Notes:** failure must stay diagnosable; D-08 (pre-video errors stay human text) intact.

---

## Claude's Discretion

- Implementation shape of the debug sink/port, the clock abstraction used for testable
  timings, and the concrete denylist patterns.

## Deferred Ideas

- A leveled `--trace`/verbosity above `--debug` (only the level token is built in).
- Env-variable enablement (`INGEST_DEBUG`) — rejected for this phase.
