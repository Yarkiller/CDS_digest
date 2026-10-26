# Phase 15: CLI --debug diagnostics - Context

**Gathered:** 2026-10-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 15 delivers an opt-in `--debug` surface on the `ingestion-service` Typer `ingest`
command that prints richer, secret-safe per-stage operator diagnostics on stderr, while
leaving the default (no-flag) output byte-identical to today and keeping the existing
JSON error contract and `✓ transcript/LLM/saved` progress checkmarks unchanged.

In scope:
- A `--debug` flag on the `ingest` command (default off).
- Per-stage debug lines on stderr covering timings, sizes/counters, LLM params, stage
  reason codes, and persist identifiers.
- A redaction model (allowlist default + denylist safety net) that never emits secrets,
  proxy credentials, cookies, auth tokens, or full transcript/prompt bodies.
- Debug behavior on failure (completed stages + failed stage reason + partial timing)
  and for pre-video config errors (D-08 preserved).

Out of scope (other phases / not this phase):
- Any new ingestion capability, HTTP API, scheduler, or auto-publish.
- Changing the existing JSON error envelope shape, exit-code contract, or the
  default-path progress lines (hard requirement — DBG-01/SC #3).
- Full PIPE-01 execution (phase 16 / v1.3).

</domain>

<decisions>
## Implementation Decisions

### Debug stream & format
- **D-01:** Debug output goes to **stderr**; **stdout stays the machine-readable result
  contract** (`material_id`, `slug`, `batch_id`, `rank`, `already_saved`). Debug must
  never contaminate stdout so pipes/parsers keep working.
- **D-02:** Debug format is **human-readable lines prefixed `[debug] …`**, consistent with
  the existing `✓ transcript` / `✓ LLM` / `✓ saved` checkmarks — not JSON-lines.
- **D-03:** Each debug line is marked with a **timestamp and level**, e.g.
  `[12:03:44] debug stage=llm …`. (Level token present so future levels, e.g. `--trace`,
  can slot in without re-formatting.)

### Diagnostic content
- **D-04:** Per-stage summarized debug signals (one line per stage):
  - **timings** — elapsed ms per stage (transcript, metadata, llm, persist);
  - **sizes/counters** — transcript length (chars/words), language, segment count;
  - **LLM params** — template kind, prompt length and response length (chars), token
    counts when available;
  - **reason codes** — stage, reason, exit_code;
  - **persist identifiers** — material_id / slug / batch_id / rank / already_saved.
- **D-05:** Granularity is **stage-level summary** (one line per stage), not verbose
  internal sub-steps (fetch/retry/language selection).
- **D-06:** Video metadata in debug is restricted to **`video_id` only** — no full URL, no
  author, no other metadata fields.

### Redaction / leak protection
- **D-07:** Redaction uses a **hybrid model**: an **allowlist** of explicitly safe fields
  is the default emission path, plus a **denylist safety net** applied to each emitted
  string as defense-in-depth. Nothing is printed unless it is allowlisted.
- **D-08:** **Never print**: secret/key values (`SUPABASE_SECRET_KEY`, `DEEPSEEK_API_KEY`,
  …), and **full transcript/prompt bodies** (only lengths/counters, never text). Per
  DBG-02, **proxy credentials and cookies** are also never emitted (covered by the
  allowlist by design and added to the denylist net).
- **D-09:** On a redaction violation (a would-be emitted value matches the denylist),
  **silently mask/omit** it — debug must never break or fail the ingest.

### Failure behavior
- **D-10:** On `IngestError`, print debug lines for **all completed stages plus the failed
  stage with its reason** (operator sees exactly where it broke), preceding the existing
  JSON error line on stderr.
- **D-11:** The **failed stage's timing is recorded and printed** (how long it ran before
  failing).
- **D-12:** For pre-video failures (`ConfigurationError` / `TemplateLoadError`), emit a
  debug line with **`stage=config`** but do **NOT** mint an `IngestError` — the D-08
  human-text-only contract is preserved.

### Flag surface
- **D-13:** Enablement is **`--debug` only** (no env variable); no interface is added to
  stdout. When `--debug` is off the debug layer must be a no-op producing **zero** debug
  output (DBG-01 / SC #3).

### Claude's Discretion
- Implementation shape of the debug sink/port, how timings are measured (clock
  abstraction for testability), and the exact denylist patterns — left to research and
  planning, provided D-01…D-13 hold and the default path stays byte-identical.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §Phase 15 — goal, SC #1–#3 (debug flag exists; no secret leakage;
  default path unchanged).
- `.planning/REQUIREMENTS.md` — DBG-01 (`--debug` and richer stage diagnostics), DBG-02
  (never leak secrets, proxy credentials, cookies, or full transcript bodies).

### Code under change
- `ingestion-service/src/ingestion_service/cli.py` — Typer command, stage checkmarks,
  `IngestError`/config-error handling; where `--debug` and the debug sink wire in.
- `ingestion-service/src/ingestion_service/domain/errors.py` — `IngestError`
  (`stage`/`reason`/`message`/`context`/`exit_code`) and `to_dict()`; the contract that
  must not change.
- `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` —
  the stage sequence and existing `on_stage` callback the debug stream can hook.
- `ingestion-service/src/ingestion_service/composition/settings.py` — `Settings`
  (secret fields already `repr=False`); source of the "never print" values.

### Prior-phase constraints to honor
- `.planning/PROJECT.md` — D-08 human-text-only pre-video errors; material/content contract.
- `.planning/STATE.md` — Accumulated Context / decisions relevant to the ingestion CLI.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `on_stage` callback in `run_ingest_pipeline` — already fires at `transcript`, `llm`,
  `saved`; the debug stream can extend/observe the same seam for per-stage timing.
- `IngestError.to_dict()` — existing secret-safe error envelope (stage/reason/message/
  context/exit_code); debug should complement it, not replace it.
- `Settings` with `repr=False` secret fields — existing precedent for keeping secrets out
  of representations; reuse the same discipline in the denylist.

### Established Patterns
- Ports & Adapters: measurement/emission should go behind a small port (e.g. a debug
  sink / clock) so use-case logic stays infra-free and unit-testable with fakes.
- TDD is mandatory (workspace rule): RED test first for every behavior, including the
  "no debug output when flag off" and "never print secret/body" cases.

### Integration Points
- `cli.py` `main()` — parse `--debug`, build the sink, pass it into the pipeline; emit
  debug lines on stderr; keep stdout result lines unchanged.
- `ingest_pipeline.py` — per-stage timing capture around captions/metadata/llm/persist.
- Config-error path in `cli.py` (`except (ConfigurationError, TemplateLoadError)`) — the
  `stage=config` debug line (D-12).

</code_context>

<specifics>
## Specific Ideas

- Debug line shape: `[HH:MM:SS] debug stage=<name> <key=value …>` — one summarized line
  per stage, consistent with existing checkmarks.
- Failure must remain diagnosable: completed stages + the failed stage's reason and
  elapsed time are all visible before the JSON error line.

</specifics>

<deferred>
## Deferred Ideas

- A `--trace` / leveled verbosity above `--debug` — noted only as a forward-compat reason
  for the level token in D-03; not built this phase.
- Env-variable enablement (`INGEST_DEBUG`) — considered and rejected for this phase
  (D-13); can be revisited if operators need it.

</deferred>

---

*Phase: 15-cli-debug-diagnostics*
*Context gathered: 2026-10-04*
