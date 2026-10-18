# Phase 15: CLI --debug diagnostics - Research

**Researched:** 2026-10-04
**Domain:** Python Typer CLI diagnostics, Ports & Adapters, secret-safe redaction
**Confidence:** HIGH (stack), HIGH (patterns), MEDIUM (redaction completeness)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Debug output goes to **stderr**; **stdout stays the machine-readable result
  contract** (`material_id`, `slug`, `batch_id`, `rank`, `already_saved`). Debug must
  never contaminate stdout so pipes/parsers keep working.
- **D-02:** Debug format is **human-readable lines prefixed `[debug] …`**, consistent with
  the existing `✓ transcript` / `✓ LLM` / `✓ saved` checkmarks — not JSON-lines.
- **D-03:** Each debug line is marked with a **timestamp and level**, e.g.
  `[12:03:44] debug stage=llm …`. (Level token present so future levels, e.g. `--trace`,
  can slot in without re-formatting.)
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
- **D-07:** Redaction uses a **hybrid model**: an **allowlist** of explicitly safe fields
  is the default emission path, plus a **denylist safety net** applied to each emitted
  string as defense-in-depth. Nothing is printed unless it is allowlisted.
- **D-08:** **Never print**: secret/key values (`SUPABASE_SECRET_KEY`, `DEEPSEEK_API_KEY`,
  …), and **full transcript/prompt bodies** (only lengths/counters, never text). Per
  DBG-02, **proxy credentials and cookies** are also never emitted (covered by the
  allowlist by design and added to the denylist net).
- **D-09:** On a redaction violation (a would-be emitted value matches the denylist),
  **silently mask/omit** it — debug must never break or fail the ingest.
- **D-10:** On `IngestError`, print debug lines for **all completed stages plus the failed
  stage with its reason** (operator sees exactly where it broke), preceding the existing
  JSON error line on stderr.
- **D-11:** The **failed stage's timing is recorded and printed** (how long it ran before
  failing).
- **D-12:** For pre-video failures (`ConfigurationError` / `TemplateLoadError`), emit a
  debug line with **`stage=config`** but do **NOT** mint an `IngestError` — the D-08
  human-text-only contract is preserved.
- **D-13:** Enablement is **`--debug` only** (no env variable); no interface is added to
  stdout. When `--debug` is off the debug layer must be a no-op producing **zero** debug
  output (DBG-01 / SC #3).

### Claude's Discretion
- Implementation shape of the debug sink/port, how timings are measured (clock
  abstraction for testability), and the exact denylist patterns — left to research and
  planning, provided D-01…D-13 hold and the default path stays byte-identical.

### Deferred Ideas (OUT OF SCOPE)
- A `--trace` / leveled verbosity above `--debug` — noted only as a forward-compat reason
  for the level token in D-03; not built this phase.
- Env-variable enablement (`INGEST_DEBUG`) — considered and rejected for this phase
  (D-13); can be revisited if operators need it.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DBG-01 | `ingestion-service` CLI accepts `--debug` and prints richer stage diagnostics on stderr/stdout without leaking secrets, proxy credentials, cookies, or full transcript bodies | Typer `Annotated[bool, typer.Option("--debug")]` flag pattern (verified); `StageDiagnostics` port + `NullDiagnostics` no-op; `StderrDiagnostics` sink emitting `[HH:MM:SS] debug stage=…`; per-stage signal gathering from existing DTOs (`Transcript`, `ArticleDraft`, `PersistResult`, `IngestError`); allowlist + denylist + `SecretRegistry` redaction |
| DBG-02 | With `--debug` off, existing staged progress / `IngestError.to_dict()` contracts remain unchanged | `NullDiagnostics` no-op guarantees zero debug output; existing exact-output tests (`test_cli_ingest_contract.py`) already lock stdout lines + `stderr == ""`; `IngestError.to_dict()` is not modified |
</phase_requirements>

## Summary

Phase 15 adds an opt-in `--debug` flag to the `ingest` Typer command that emits one
secret-safe, human-readable diagnostic line per pipeline stage on **stderr**, while
stdout, the checkmark progress lines, the JSON error envelope, and exit codes stay
byte-identical when the flag is absent. The work is entirely additive: it introduces a
small diagnostics **port** (Protocol) plus a concrete stderr sink and a clock adapter,
hooks the existing `run_ingest_pipeline` use-case at stage boundaries, and applies a
hybrid allowlist + denylist redaction layer before anything is written.

The key architectural move is to keep the use-case infra-free: `run_ingest_pipeline`
gains an optional `diagnostics` parameter typed as a `typing.Protocol`; it emits
`stage_started` / `stage_completed` / `stage_failed` events but never imports `typer`,
`sys`, or a clock. The concrete `StderrDiagnostics` adapter (interface/adapters layer)
owns timestamps, elapsed-time measurement (via an injected `Clock` port), formatting, and
redaction. When `--debug` is off the CLI wires a `NullDiagnostics` no-op, which satisfies
D-13's guarantee of zero debug output.

**Primary recommendation:** Add `application/ports/diagnostics.py` (`Clock`,
`StageDiagnostics`, `DebugValue`, `NullDiagnostics`), `adapters/stderr_diagnostics.py`
(`StderrDiagnostics` with `SystemClock`) and `diagnostics/redaction.py` (allowlist keys +
denylist patterns + `SecretRegistry`), then thread an optional `diagnostics` through
`run_ingest_pipeline` and wire the sink in `cli.main` behind the `--debug` boolean. Keep
`_on_stage`/`_STAGE_CHECKMARKS` untouched. Do **not** change the `ArticleGenerator` port;
emit only what is observable today (D-04's "token counts when available" → omit).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `--debug` flag parsing & sink wiring | CLI interface (`cli.py`) | Composition (`build_ingest_deps`) | Typer owns arg parsing; composition owns adapter construction |
| Stage boundary events (start/complete/fail) | Application (`run_ingest_pipeline`) | — | Only the use-case knows the ordered stage sequence |
| Elapsed-time measurement | Adapter (`StderrDiagnostics` + `Clock`) | — | Time is an I/O concern; keeps the use-case free of clocks |
| Timestamp/level/line formatting | Adapter (`StderrDiagnostics`) | — | Presentation belongs to the interface layer |
| Redaction (allowlist + denylist + secret registry) | Pure module (`diagnostics/redaction.py`) | Adapter (invokes it) | Deterministic, unit-testable, no I/O |
| Failure reason/exit-code emission | CLI interface + Adapter | Application (raises mapped `IngestError`) | `IngestError.stage/reason/exit_code` already exist; CLI composes the line |
| Config-error `stage=config` line | CLI interface | — | Config errors occur in/around `build_ingest_deps()` before any stage |
| stdout result + checkmarks (unchanged) | CLI interface | — | Must stay byte-identical (DBG-02) |

## Standard Stack

### Core
| Library | Version (installed) | Purpose | Why Standard |
|---------|---------------------|---------|--------------|
| Python | 3.14.0 (requires `>=3.12`) | Runtime | Project-wide language floor |
| Typer | 0.27.2 (declared `>=0.27.2`) | CLI command/flag parsing | Already the CLI framework for `ingest` |
| Click | 8.5.0 (Typer dependency) | Test runner stream capture | `CliRunner` separates stdout/stderr |
| pytest | dev group `>=8.3.0` | Unit tests | Root `[tool.pytest.ini_options]` |
| `time` / `datetime` (stdlib) | — | Monotonic timing + wall-clock timestamp | No new dependency needed |

**Version verification:** Verified in the project's uv environment this session:
```
typer 0.27.2
click 8.5.0
Python 3.14.0
uv 0.10.9
```
`ingestion-service/pyproject.toml` declares `requires-python = ">=3.12"` and
`"typer>=0.27.2"`; the root `pyproject.toml` declares `"pytest>=8.3.0"`.

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none new) | — | — | Phase is stdlib + existing deps only |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom `StageDiagnostics` Protocol | Python `logging` with a stderr handler + custom formatter | `logging` is heavier, its level/config surface is process-global, and it does not naturally model "one summarized event per stage with typed signals". A Protocol keeps the use-case infra-free and fakes trivial. |
| `--debug` boolean option | `count`/`-v` verbosity levels | D-13 locks a single boolean; D-03's level token leaves room for a future `--trace` |
| Extend `ArticleGenerator` port to return token usage | Keep port, emit only char lengths | Changing the port touches `data-collection` public API, the adapter, and all fakes; D-08/“when available” make omission the low-risk choice this phase |

**Installation:**
```bash
# No new packages. Everything ships with stdlib + existing workspace deps.
```

## Package Legitimacy Audit

**No external packages are installed in this phase.** The implementation uses only the
Python standard library (`time`, `datetime`, `re`, `sys`) plus already-declared
dependencies (`typer`, `click`, `pytest`). No legitimacy gate is required.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
 operator
   │  ingest <url> --template lecture --debug
   ▼
┌───────────────────────────────────────────────┐
│ cli.main  (interface layer)                    │
│  • parse --debug (bool, default False)         │
│  • build_ingest_deps() ──► ConfigurationError? │
│  • choose sink:                                │
│      debug ON  → StderrDiagnostics(clock,      │
│                   secrets from Settings)       │
│      debug OFF → NullDiagnostics (no-op)       │
└───────────────┬───────────────────────────────┘
                │ diagnostics (Protocol)
                ▼
┌───────────────────────────────────────────────┐
│ run_ingest_pipeline (application/use_case)     │
│  url → captions → metadata → [consistency] →   │
│        llm → persist                           │
│  emits per stage:                              │
│    stage_started(name)                         │
│    stage_completed(name, signals)   # success  │
│    stage_failed(name, reason, code) # error    │
└───────────────┬───────────────────────────────┘
                │ events
                ▼
┌───────────────────────────────────────────────┐
│ StderrDiagnostics (adapter)                    │
│  • Clock.monotonic() → elapsed_ms              │
│  • Clock.now() → [HH:MM:SS]                    │
│  • redaction.sanitize(signals)                 │
│        allowlist → drop unknown keys           │
│        SecretRegistry → mask exact secrets     │
│        denylist regex → mask patterns          │
│  • typer.echo(line, err=True)                  │
└───────────────┬───────────────────────────────┘
                │ stderr (only)
                ▼
   [12:03:44] debug stage=captions elapsed_ms=… …
   ✓ transcript            ← stdout checkmarks (unchanged)
   {"ok": false, …}        ← stdout/stderr error contract (unchanged)
```

Data flow for a successful run: CLI builds deps → constructs the sink → pipeline emits
four completed-stage events → sink writes four stderr lines → CLI prints the five stdout
result lines. For a failed run: the pipeline emits completed events for earlier stages,
then `stage_failed` for the failing stage, raises the mapped `IngestError`, and the CLI
prints the existing JSON envelope after the debug lines (same stream, ordered). For a
config error: the CLI catches `ConfigurationError`/`TemplateLoadError`, emits one
`stage=config` debug line, then the existing human text — no `IngestError` is minted.

### Recommended Project Structure
```
ingestion-service/src/ingestion_service/
├── application/
│   ├── ports/
│   │   └── diagnostics.py     # Clock, StageDiagnostics Protocols, DebugValue, NullDiagnostics
│   └── use_cases/
│       └── ingest_pipeline.py # emits stage_started/completed/failed via diagnostics
├── diagnostics/
│   └── redaction.py           # ALLOWED_KEYS, DENY_PATTERNS, SecretRegistry, sanitize()
├── adapters/
│   ├── stderr_diagnostics.py  # StderrDiagnostics: format + emit to stderr
│   └── system_clock.py        # SystemClock: monotonic()/now()
└── cli.py                     # --debug flag, sink wiring, failure/config emission
```

`ingestion-service` has no `interface/` directory; `adapters/` is the established home for
concrete implementations (`supabase_persist.py`, `persist_errors.py`).

### Pattern 1: Diagnostics port + Null Object
**What:** A `typing.Protocol` the use-case depends on, with a no-op implementation used
when the flag is off.
**When to use:** Any optional side-channel that must not affect the default path.
**Example:**
```python
# application/ports/diagnostics.py
from __future__ import annotations
from collections.abc import Mapping
from datetime import datetime
from typing import Protocol, runtime_checkable

DebugValue = str | int | float | bool

@runtime_checkable
class Clock(Protocol):
    def monotonic(self) -> float: ...      # elapsed timing
    def now(self) -> datetime: ...         # [HH:MM:SS] prefix

@runtime_checkable
class StageDiagnostics(Protocol):
    def stage_started(self, stage: str) -> None: ...
    def stage_completed(self, stage: str, signals: Mapping[str, DebugValue]) -> None: ...
    def stage_failed(self, stage: str, *, reason: str, exit_code: int) -> None: ...
    def config_error(self, *, error_type: str, message: str) -> None: ...

class NullDiagnostics:
    """D-13: zero debug output when --debug is off."""
    def stage_started(self, stage: str) -> None: ...
    def stage_completed(self, stage: str, signals: Mapping[str, DebugValue]) -> None: ...
    def stage_failed(self, stage: str, *, reason: str, exit_code: int) -> None: ...
    def config_error(self, *, error_type: str, message: str) -> None: ...
```
No `Any` crosses the port boundary (`DebugValue` is an explicit union), honoring the
architecture rule.

### Pattern 2: Clock port injected into the sink (not the use-case)
**What:** The adapter measures elapsed time; the use-case only reports start/complete.
**When to use:** When timings must be deterministic in tests.
**Example:**
```python
# adapters/system_clock.py
from datetime import datetime
import time

class SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()
    def now(self) -> datetime:
        return datetime.now()
```
Tests inject a `FakeClock` returning scripted monotonic values and a fixed `datetime`,
which makes `elapsed_ms` and the `[HH:MM:SS]` prefix exactly assertable. The
`run_ingest_pipeline` signature stays free of any time import.

### Pattern 3: Hybrid redaction — allowlist emission + denylist + secret registry
**What:** Only allowlisted signal keys are formatted; every produced string is then passed
through a `SecretRegistry` (exact secret values from `Settings`) and denylist regexes;
violations are silently replaced with `[redacted]`.
**When to use:** Every emitted debug line (D-07/D-08/D-09).
**Example:**
```python
# diagnostics/redaction.py  (shape, not final patterns)
ALLOWED_KEYS: frozenset[str] = frozenset({
    "stage", "elapsed_ms", "reason", "exit_code",
    "video_id", "transcript_chars", "transcript_words", "language",
    "template", "response_chars",
    "material_id", "slug", "batch_id", "rank", "already_saved",
    "error_type", "message",
})

DENY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|authorization|cookie)\s*[=:]\s*\S+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),  # JWT (Supabase key)
    re.compile(r"[a-z][a-z0-9+.-]*://[^/@\s]+@"),                          # URL userinfo
    re.compile(r"[\x00-\x1f\x7f]"),                                        # control chars
)

class SecretRegistry:
    """Exact secret values taken from Settings; replaces occurrences with [redacted]."""
    def __init__(self, secrets: list[str]) -> None:
        # only non-empty, length >= 4, de-duplicated
        self._secrets = sorted({s for s in secrets if s and len(s) >= 4}, key=len, reverse=True)
    def mask(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, "[redacted]")
        return text
```
The `SecretRegistry` is the strongest net: it masks the *actual* runtime values of
`deepseek_api_key`, `supabase_secret_key`, and the credentialed `youtube_proxy_url` even
if they slip into an allowlisted string. The regex denylist catches patterns the registry
does not know about (cookies, bearer tokens, foreign JWTs). Control-char stripping prevents
newline/ANSI/log-injection forging.

### Pattern 4: Canonical stage vocabulary + failure attribution
**What:** Debug lines use explicit stage tokens; the sink tracks the in-flight stage so a
failure can report the failed stage's elapsed time.
**When to use:** D-10/D-11 failure diagnostics.
**Design note:** Success emits four lines (`captions`, `metadata`, `llm`, `persist` — D-04
names the first "transcript"; see Open Question Q2). Failure reports the **`IngestError`**
stage token verbatim (`captions`, `metadata`, `consistency`, `llm`, `llm_truncation`,
`persist`, `url`) so it correlates 1:1 with the JSON envelope the operator already parses.
The sink finalizes the currently-open stage for the elapsed value; if no stage was open
(e.g. `url` failing before any stage start), it prints `elapsed_ms=0` and still satisfies
D-11's intent for the timed stages.

### Pattern 5: Typer boolean flag + stderr echo
**What:** Declare `--debug` as a boolean option with a default; echo to stderr.
**When to use:** D-01/D-13.
**Example:**
```python
# cli.py
from typing import Annotated
import typer

@app.command()
def main(
    url: Annotated[str, typer.Argument(...)],
    template: Annotated[TemplateKind, typer.Option("--template", ...)],
    debug: Annotated[bool, typer.Option("--debug", help="Emit secret-safe stage diagnostics on stderr")] = False,
) -> None:
    ...
```
Specifying `typer.Option("--debug")` explicitly disables Typer's automatic `--no-debug`
companion flag (Context7: "explicitly defining the desired flag name … disable[s] the
automatic generation of the corresponding negative flag"). `typer.echo(line, err=True)`
writes only to stderr; the existing error handlers already use `err=True`.

### Anti-Patterns to Avoid
- **Emitting via `print()`/`typer.echo` inside `run_ingest_pipeline`:** printing in the
  use-case couples it to the interface and breaks unit testing; emit through the port.
- **Stuffing debug state into `on_stage`:** `on_stage` is a checkmark-only callback whose
  token vocabulary is `transcript`/`llm`/`saved`; overloading it risks the stdout contract.
- **Building the debug line with f-strings of raw objects:** `f"{metadata!r}"` would print
  author/URL and can print secrets; only pass allowlisted scalar signals.
- **Masking by omission only (no denylist):** D-07 requires the denylist safety net; a
  future field could leak.
- **Using `result.output` in tests:** Click's `application.output` mixes stdout and stderr;
  assert on `result.stdout` / `result.stderr`.
- **Logging the secret *length* or a prefix:** even partial secret disclosure is a leak;
  always emit the fixed token `[redacted]`.
- **Reaching into `os.environ` in `cli.build_ingest_deps`:** guarded by an existing test;
  derive secrets from `Settings`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI flag parsing | Manual `sys.argv` handling | Typer `Annotated[bool, typer.Option("--debug")]` | Already the framework; free help/validation |
| Test stream capture | Custom `contextlib.redirect_stderr` harness | `typer.testing.CliRunner` (Click 8.5) | Existing test pattern; `result.stdout`/`result.stderr` separation |
| URL userinfo stripping | A second ad-hoc parser | Reuse the existing approach in `url.py::_safe_url_for_diagnostics` (consider extracting to `redaction.py`) | Already tested for `user:secret@host` |
| Timing abstraction | Mocking `time.monotonic` globally | Tiny `Clock` Protocol + `FakeClock` | Explicit, deterministic, no global patching |
| Exact secret masking | Hand-listed literal replaces at call sites | `SecretRegistry` built once from `Settings` | Misses no runtime value and stays out of business logic |

**Key insight:** the codebase already ships secret-safe precedent at every error boundary
(allowlisted `_CONTEXT_ALLOWLIST`, `repr=False` on secret `Settings` fields, userinfo
stripping). Phase 15 should extend that discipline rather than invent a new mechanism.

## Runtime State Inventory

**Skipped — not a rename/refactor/migration phase.** This phase is additive (new module,
new port, new flag) and does not rename any stored string, service config, OS state,
secret key, or build artifact.

## Common Pitfalls

### Pitfall 1: Default-path drift (DBG-02 violation)
**What goes wrong:** Adding the debug machinery accidentally changes stdout, adds a
stderr byte, or alters the JSON envelope.
**Why it happens:** Refactoring `on_stage`/`_STAGE_CHECKMARKS`, or emitting even an empty
line when the flag is off.
**How to avoid:** Wire `NullDiagnostics` (true no-ops) when `--debug` is absent; do not
touch `_on_stage`, `_STAGE_CHECKMARKS`, the five stdout result lines, or
`IngestError.to_dict()`.
**Warning signs:** `test_cli_happy_path_stdout_contract` fails on `result.stderr == ""` or
exact stdout lines.

### Pitfall 2: stdout contamination
**What goes wrong:** A debug line lands on stdout, breaking `jq`/pipe parsers.
**Why it happens:** Using `typer.echo(line)` without `err=True`, or writing via `print()`.
**How to avoid:** The sink must call `typer.echo(line, err=True)` exclusively.
**Warning signs:** `result.stdout.splitlines()` gains a `[debug]` line.

### Pitfall 3: Secrets in debug via object repr or `str(exc)`
**What goes wrong:** A raw exception/`Settings`/metadata repr leaks an API key or proxy
credentials.
**Why it happens:** Formatting `err`/`deps`/`metadata` directly instead of scalar
allowlisted signals.
**How to avoid:** Only pass allowlisted scalars; run the final line through
`SecretRegistry` + denylist; never format `Settings` or raw exceptions.
**Warning signs:** A redaction test planting a secret in a fake value fails.

### Pitfall 4: Log/terminal injection through values
**What goes wrong:** A crafted video id or message containing `\n` or ANSI escapes forges
extra debug lines or corrupts the terminal.
**Why it happens:** Emitting raw string values.
**How to avoid:** Strip `[\x00-\x1f\x7f]` and cap value length in `sanitize()`.
**Warning signs:** A test value with `\n` produces more than one output line.

### Pitfall 5: Timing non-determinism in tests
**What goes wrong:** Tests assert exact `elapsed_ms` values and flake.
**Why it happens:** Using the real clock in the pipeline/sink under test.
**How to avoid:** Inject `FakeClock` into `StderrDiagnostics` for formatter tests; assert
structure/regex (not exact ms) for CLI-level tests that use the real `SystemClock`.
**Warning signs:** Intermittent failures on `elapsed_ms`.

### Pitfall 6: `result.output` mixes streams (Click 8.5)
**What goes wrong:** A test asserting `result.output` sees stdout+stderr interleaved.
**Why it happens:** `mix_stderr` was removed in Click 8.2; `output` is now the merged
stream while `stdout`/`stderr` are separate.
**How to avoid:** Assert on `result.stdout` and `result.stderr`.
**Warning signs:** Confusing ordering assertions that pass/fail depending on flush order.

### Pitfall 7: LLM signals that do not exist
**What goes wrong:** The planner asks for prompt/token counts that the port cannot supply,
forcing a risky port change.
**Why it happens:** `ArticleGenerator.process()` returns only `ArticleDraft`; the adapter
discards `response.usage` and the prompt is built internally.
**How to avoid:** Emit only observable values (`template`, `response_chars`); omit token
counts per D-04's "when available" (see Open Question Q1).
**Warning signs:** A task proposes editing `data_collection/ports/article_generator.py`.

### Pitfall 8: Adding `settings` to the deps namespace breaks fakes
**What goes wrong:** The secret registry needs `Settings`, but existing tests monkeypatch
`build_ingest_deps` with a `SimpleNamespace` that has no `settings`.
**Why it happens:** Tightly requiring `deps.settings`.
**How to avoid:** Use `getattr(deps, "settings", None)` and fall back to regex-only
redaction (empty registry). Add `settings=` to the production namespace.
**Warning signs:** Existing CLI tests raise `AttributeError`.

## Code Examples

Verified patterns from official sources and the repo:

### Adding the `--debug` flag (Typer)
```python
# Source: https://typer.tiangolo.com/tutorial/parameter-types/bool (Context7)
from typing import Annotated
import typer

app = typer.Typer()

@app.command()
def main(force: Annotated[bool, typer.Option("--force")] = False):
    if force:
        print("Forcing operation")
```
Specifying the flag name explicitly disables the auto-generated `--no-force`.

### Separate stdout/stderr capture (Click 8.5)
```python
# Source: typer.testing.CliRunner; verified by local probe (typer 0.27.2 / click 8.5.0)
from typer.testing import CliRunner
result = CliRunner().invoke(app, [URL, "--template", "lecture", "--debug"])
assert result.exit_code == 0
assert result.stdout.splitlines() == EXPECTED_SUCCESS_LINES   # unchanged
assert "[debug] stage=captions" in result.stderr
```
Click 8.5's `CliRunner.__init__` signature is `(self, charset, env)` — the `mix_stderr`
parameter was removed in Click 8.2 (`click/testing.py` "versionchanged:: 8.2 —
`mix_stderr` parameter has been removed").

### Existing secret-safe precedent to reuse
```python
# ingestion-service/src/ingestion_service/url.py
def _safe_url_for_diagnostics(value: str) -> str:
    """Strip userinfo credentials from URL-like diagnostic values."""
    parsed = urlparse(value)
    ...
    netloc = f"{host}{port}"
    return urlunparse((parsed.scheme, netloc, parsed.path, ...))
```
And the existing allowlist forwarding pattern (`mapping/captions.py`):
```python
_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {"video_id", "available_languages", "exception_class"}
)
```

### Locked in-repo values (verbatim, read this session)
```python
# domain/errors.py:7-17  — Stage literal (failure stage tokens)
Stage = Literal[
    "url", "captions", "metadata", "consistency",
    "llm", "llm_truncation", "persist",
]
```
```python
# cli.py:27-31 — stdout checkmark tokens (must not change)
_STAGE_CHECKMARKS = {
    "transcript": "✓ transcript",
    "llm": "✓ LLM",
    "saved": "✓ saved",
}
```
```python
# application/use_cases/ingest_pipeline.py — existing on_stage fire points
if on_stage is not None:
    on_stage("transcript")   # after captions
...
    on_stage("llm")          # after article.process
...
    on_stage("saved")        # after persist_draft
```
```python
# composition/settings.py:55,59 — secret fields already repr=False
deepseek_api_key: str | None = field(default=None, repr=False)
...
supabase_secret_key: str | None = field(default=None, repr=False)
```
```python
# application/ports/persist.py:10-16 — persist identifiers (D-04)
@dataclass(frozen=True)
class PersistResult:
    material_id: int
    slug: str
    batch_id: int
    rank: int
    already_saved: bool = False
```
DTO fields available for signals (read this session): `Transcript(text, language,
video_id)` (`data_collection/dto/transcript.py:8-11`), `ArticleDraft(title, dek,
body_markdown, roles)` (`data_collection/dto/article_draft.py:11-15`),
`VideoMetadata(video_id, source_url, author, published_at)`
(`data_collection/dto/video_metadata.py:10-14`).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `CliRunner(mix_stderr=False)` to split streams | `CliRunner()`; use `result.stdout` / `result.stderr` | Click 8.2 | No constructor arg needed; `result.output` is the merged stream |
| `bool = typer.Option(False, "--force")` | `Annotated[bool, typer.Option("--force")] = False` | Typer 0.9+ | Type-hint-first style; explicit flag name suppresses `--no-*` |
| Ad-hoc `print(..., file=sys.stderr)` | `typer.echo(..., err=True)` | Typer maturity | Consistent with existing error handlers |

**Deprecated/outdated:**
- `mix_stderr` — removed in Click 8.2 (verified in installed `click/testing.py`).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Segment count is unavailable to the pipeline (adapter computes `len(snippets)` but `Transcript` drops it), so it must be omitted or the DTO extended | Diagnostic content / Q3 | Planner adds a signal that cannot be sourced, or proposes a risky DTO change |
| A2 | Token counts / real prompt length are unavailable without changing `ArticleGenerator`; emit `response_chars` only | Pattern/signals / Q1 | Planner fabricates misleading `prompt_chars`, or changes the public port |
| A3 | Debug success lines should be the four D-04 stages (`transcript`/`metadata`/`llm`/`persist`); `url`/`consistency` appear only on failure | Pattern 4 / Q2 | Operator expects a `url` success line, or stage naming mismatches the JSON envelope |
| A4 | The denylist regex set above is sufficient defense-in-depth alongside the exact-value `SecretRegistry` | Redaction | An unanticipated secret shape slips through (residual risk, mitigated by registry) |
| A5 | Building the secret registry from `Settings` requires exposing `settings` on the `build_ingest_deps()` namespace — **RESOLVED:** add `settings=` to the production namespace and read it via `getattr(deps, "settings", None)` with a regex-only fallback | Wiring | Tight coupling breaks existing monkeypatched fakes (see Pitfall 8) |

**Resolved for planning:** A1–A3 are locked by Q1–Q3 (segment count omitted, no `ArticleGenerator` port change, domain `captions` token); A4 is best-effort defense-in-depth; A5 is resolved via `settings=` + `getattr(deps, "settings", None)` fallback.

## Open Questions (RESOLVED)

1. **Real LLM token/prompt counts (D-04 "token counts when available").**
   - What we know: `DeepSeekArticleGenerator.process()` returns only `ArticleDraft`; the
     adapter ignores `response.usage`, and the prompt is assembled inside the adapter.
   - What's unclear: whether the operator needs genuine prompt-length/token signals badly
     enough to justify extending the `data-collection` port.
   - Recommendation: **Do not change the port this phase.** Emit `template` and
     `response_chars = len(article_draft.body_markdown)`, and rely on D-04's "when
     available" to omit token counts. Record the omission explicitly in the plan.
   - **RESOLVED (locked for planning, Q1):** No `ArticleGenerator` port change this
     phase; emit only `template` and `response_chars`; prompt-length/token counts omitted
     per D-04's "when available".
2. **Debug stage token for the captions stage: `transcript` vs `captions`.**
   - What we know: D-04 says "transcript"; `IngestError.stage` and the domain vocabulary
     say `captions`.
   - Recommendation: use `stage=captions` for correlation with the JSON envelope, or keep
     `stage=transcript` and map `captions`→`transcript` only for the timing lookup. Confirm
     the operator-facing token; either is defensible.
   - **RESOLVED (locked for planning, Q2):** Use the domain `captions` token so each debug
     line correlates 1:1 with `IngestError.stage`; D-04's "transcript" names the captions
     stage.
3. **Segment count signal.**
   - What we know: `Transcript` has no segment count; the adapter computes it.
   - Recommendation: omit it (or emit `transcript_words` as the available counter). If
     required, extend `Transcript` with an optional `segment_count` **only with explicit
     user approval**, since `Transcript` is public package API.
   - **RESOLVED (locked for planning, Q3):** Omit segment count; emit `transcript_chars`,
     `transcript_words`, and `language` instead (no `Transcript` DTO change).
4. **Where the concrete sink lives (`adapters/` vs a new `diagnostics/` package).**
   - Recommendation: port in `application/ports/diagnostics.py`, sink in
     `adapters/stderr_diagnostics.py`, pure redaction in `diagnostics/redaction.py`. Any
     equivalent split is fine (Claude's Discretion).
   - **RESOLVED (locked for planning, A5):** Port in
     `application/ports/diagnostics.py`, sink in `adapters/stderr_diagnostics.py`, pure
     redaction in `diagnostics/redaction.py`; thread `settings=` into the
     `build_ingest_deps()` namespace and read it via
     `getattr(deps, "settings", None)` so monkeypatched fakes without `settings` still work.

**All four open questions are resolved and locked; no open questions remain for planning.**

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.14.0 (floor `>=3.12`) | — |
| uv | Build/test runner | ✓ | 0.10.9 | — |
| Typer | CLI flag | ✓ | 0.27.2 | — |
| Click | `CliRunner` tests | ✓ | 8.5.0 | — |
| pytest | Unit tests | ✓ | `>=8.3.0` (dev group) | — |
| Network/Supabase/YouTube | — | not needed | — | Unit tests use fakes |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none

## Validation Architecture

Nyquist validation is **enabled** (`.planning/config.json` has no `workflow.nyquist_validation`
key, so it defaults to enabled).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (dev group `>=8.3.0`) + `typer.testing.CliRunner` (Click 8.5.0) |
| Config file | root `pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`, `pythonpath = ["."]`) |
| Quick run command | `uv run pytest tests/unit/test_cli_debug_diagnostics.py -q` |
| Full suite command | `uv run pytest -q` (baseline: **684 passed in 5.26s**) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DBG-01 | `--debug` emits 4 per-stage stderr lines on success; stdout unchanged | unit (CLI) | `uv run pytest tests/unit/test_cli_debug_diagnostics.py::test_debug_success_emits_stage_lines -x` | ❌ Wave 0 |
| DBG-01 | sink formats exact `[HH:MM:SS] debug stage=…` lines with a fake clock | unit (sink) | `uv run pytest tests/unit/test_stderr_diagnostics.py -q` | ❌ Wave 0 |
| DBG-01 | pipeline emits start/complete/fail events in order (fakes) | unit (use-case) | `uv run pytest tests/unit/test_ingest_pipeline.py -q` | ⚠️ extend existing |
| DBG-01 | redaction never leaks secrets/proxy creds/cookies/bodies; mask on violation | unit (redaction + CLI) | `uv run pytest tests/unit/test_debug_redaction.py -q` | ❌ Wave 0 |
| DBG-01 | failure prints completed stages + failed stage reason + `elapsed_ms`, then JSON | unit (CLI) | `uv run pytest tests/unit/test_cli_debug_diagnostics.py::test_debug_failure_prints_completed_and_failed -x` | ❌ Wave 0 |
| DBG-01 | config error emits `stage=config` with no `IngestError` envelope | unit (CLI) | `uv run pytest tests/unit/test_cli_debug_diagnostics.py::test_debug_config_error_line -x` | ❌ Wave 0 |
| DBG-02 | `--debug` off → stdout byte-identical, `stderr == ""` | unit (CLI) | `uv run pytest tests/unit/test_cli_debug_diagnostics.py::test_debug_off_is_byte_identical -x` | ❌ Wave 0 |
| DBG-02 | `IngestError.to_dict()` envelope unchanged | unit | `uv run pytest tests/unit/test_ingest_error.py -q` | ✅ exists |
| DBG-02 | existing stdout contract unchanged | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -q` | ✅ exists |

### RED test shapes (TDD — write these first)
1. **D-13 zero-output:** invoke with no `--debug`; assert `result.stderr == ""` and
   `result.stdout.splitlines() == EXPECTED_SUCCESS_LINES` (frozen baseline).
2. **D-01/D-02/D-03 success lines:** invoke with `--debug`; assert stderr contains a line
   matching `^\[\d{2}:\d{2}:\d{2}\] debug stage=captions .*elapsed_ms=\d+` and one line per
   `captions`/`metadata`/`llm`/`persist`; assert stdout still exactly the frozen baseline.
3. **D-06 metadata minimization:** assert the metadata debug line contains `video_id=` and
   does **not** contain the author or the full `source_url`.
4. **D-08/D-09 redaction:** plant a fake `deepseek_api_key`/`supabase_secret_key`/proxied
   URL/cookie value and a full transcript body; assert none appear in stderr; assert a
   denylist-violating value is replaced by `[redacted]`; assert ingest still exits as it
   otherwise would (mask, not fail).
5. **D-10/D-11 failure:** trigger `ArticleNetworkError` after `✓ transcript`; assert
   stderr has `[debug] stage=llm` lines for completed stages plus a failed line with
   `reason=` and `elapsed_ms=`, appearing before the JSON envelope; stdout has only
   `✓ transcript`.
6. **D-12 config:** monkeypatch `build_ingest_deps` to raise `ConfigurationError`; with
   `--debug`, assert a `stage=config` line precedes the human text and that no JSON
   `{"ok": false}` envelope is emitted.
7. **Sink determinism:** unit-test `StderrDiagnostics(FakeClock(...))` for exact timestamp,
   exact `elapsed_ms`, and control-char stripping.

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit/test_cli_debug_diagnostics.py tests/unit/test_debug_redaction.py tests/unit/test_stderr_diagnostics.py -q`
- **Per wave merge:** `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_ingest_pipeline.py tests/unit/test_ingest_error.py -q`
- **Phase gate:** `uv run pytest -q` green (≥684 tests) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_cli_debug_diagnostics.py` — CLI `--debug` on/off, success/failure/config
- [ ] `tests/unit/test_debug_redaction.py` — allowlist/denylist/registry masking
- [ ] `tests/unit/test_stderr_diagnostics.py` — formatter + `FakeClock` determinism
- [ ] `tests/unit/test_ingest_pipeline.py` — extend with a `RecordingDiagnostics` + `FakeClock` event-order test
- [ ] `ingestion_service/tests_support/fakes.py` — add `FakeClock` and `RecordingDiagnostics`
- [ ] Framework install: none — pytest/CliRunner already present

## Security Domain

`security_enforcement` is not explicitly disabled in config, so this section is included.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface changed |
| V3 Session Management | no | No sessions changed |
| V4 Access Control | no | None changed |
| V5 Input Validation | yes | Allowlist of emitted signal keys; `DebugValue` union; value length cap + control-char strip |
| V6 Cryptography | no | No crypto; redaction is not cryptographic |
| V7 Logging & Error Handling | yes | Secret-safe diagnostics: hybrid allowlist + denylist + exact-value `SecretRegistry`; mask-on-violation (never fail the ingest); reuse existing `IngestError` allowlisted envelope |

### Known Threat Patterns for Python CLIs (Typer/Click)
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Sensitive data exposure via stderr (API keys, proxy creds, cookies, transcript bodies) | Information Disclosure | Allowlist emission + `SecretRegistry` masking + denylist regexes; only lengths/counters for bodies (D-08) |
| Log injection / forged lines via embedded `\n` | Tampering | Strip `[\x00-\x1f\x7f]`, cap value length |
| Terminal escape (ANSI) injection via values | Tampering | Control-char stripping before echo |
| Secret leakage through object repr / `str(exc)` | Information Disclosure | Never format `Settings`/raw exceptions; only allowlisted scalars; reuse `repr=False` discipline |
| Debug flag enabling verbose output in production | — | `--debug` is explicit and default-off (D-13); no env-var enablement |

## Sources

### Primary (HIGH confidence)
- Context7 `/websites/typer_tiangolo` — boolean CLI options and `CliRunner` testing patterns
  - `https://typer.tiangolo.com/tutorial/parameter-types/bool`
  - `https://typer.tiangolo.com/tutorial/testing`
- Local probe (this session) — `Annotated[bool, typer.Option("--debug")]` parses; Click 8.5.0
  `CliRunner` separates `stdout`/`stderr`; `CliRunner.__init__` params `(charset, env)`
- Installed `click/testing.py` — docstring: "``mix_stderr`` parameter has been removed"
  (`versionchanged:: 8.2`), `output` is the merged stream
- Repo code read this session: `cli.py`, `domain/errors.py`, `application/use_cases/ingest_pipeline.py`,
  `composition/settings.py`, `composition/clients.py`, `mapping/*.py`, `url.py`,
  `adapters/supabase_persist.py`, `adapters/persist_errors.py`,
  `data_collection/dto/{transcript,article_draft,video_metadata,material_draft,template_kind}.py`,
  `data_collection/ports/{article_generator,transcript_provider,video_metadata_provider}.py`,
  `data_collection/adapters/deepseek_article.py`, `data_collection/templates/__init__.py`
- Existing tests read this session: `tests/unit/test_cli_ingest_contract.py`,
  `test_ingest_pipeline.py`, `test_ingest_error.py`, `test_ingestion_settings.py`,
  `test_captions_error_mapping.py`, `test_supabase_draft_persister_contract.py`,
  `test_build_ingest_deps_wiring.py`

### Secondary (MEDIUM confidence)
- `.planning/phases/15-cli-debug-diagnostics/15-CONTEXT.md` (locked decisions),
  `.planning/REQUIREMENTS.md` (DBG-01/DBG-02), `.planning/ROADMAP.md` §Phase 15,
  `.planning/STATE.md` (accumulated decisions)

### Tertiary (LOW confidence)
- Denylist regex completeness (A4) — best-effort defense-in-depth; the exact-value
  `SecretRegistry` is the primary guarantee

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified in the live uv environment; no new packages
- Architecture: HIGH — port/adapter shape follows the repo's existing patterns and the
  locked decisions; matched against the current pipeline and CLI
- Redaction: MEDIUM — allowlist + exact-value registry are solid; regex denylist coverage is
  inherently best-effort
- Pitfalls: HIGH — derived from existing tests and observed Click/Typer behavior

**Research date:** 2026-10-04
**Valid until:** ~2026-11-03 (30 days; stable CLI/testing stack, slow-moving)
