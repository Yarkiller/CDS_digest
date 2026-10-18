# Phase 10: CLI Composition & UAT - Research

**Researched:** 2026-09-29
**Domain:** Typer CLI composition root + Postgres RPC amend (stored slug / `already_saved`) + manual operator UAT
**Confidence:** HIGH (repo contracts + Context7 Typer/uv); MEDIUM (exact Typer pin / package-legitimacy SUS on downloads metadata)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Command shape
- **D-01:** The one-shot is a positional YouTube URL (or other input `extract_video_id` already accepts) plus a required `--template` flag whose only values are `lecture` and `podcast`. There is no default template. — **Reversibility:** costly — the flag is the operator contract for LLM-02; a later default would change every runbook line and test.
- **D-02:** The process environment is supplied by the operator as `uv run --env-file ingestion-service/.env`. The CLI does not auto-load a dotenv file. — **Reversibility:** reversible — the path is local ops; `Settings.from_env` already reads the process environment.
- **D-03:** The console script name is `ingest`. — **Reversibility:** costly — the name is the published entry point in `ingestion-service` pyproject scripts.
- **D-04:** `ingest` itself is the one-shot. There is no subcommand (`ingest run` is out). Invocation: `uv run --env-file ingestion-service/.env ingest <url> --template lecture|podcast`.

#### Terminal output
- **D-05:** Success is human lines on stdout. A pipeline failure is the existing `IngestError.to_dict()` JSON object on stderr and a non-zero exit. Success is not JSON. — **Reversibility:** costly — stdout/stderr split is the operator contract for CLI-01 and CLI-04.
- **D-06:** After `✓ saved`, stdout prints four lines, exactly these keys: `material_id`, `slug`, `batch_id`, `rank`, each as `key: value`.
- **D-07:** Each checkmark is printed as soon as that stage succeeds, in order: `✓ transcript`, then `✓ LLM`, then `✓ saved`. A failing stage prints no checkmark. Earlier checkmarks stay on stdout; the JSON error goes to stderr. Metadata and consistency do not get their own checkmarks. `✓ transcript` means captions succeeded. `✓ LLM` means a validated article draft exists. `✓ saved` means persist returned.
- **D-08:** Errors before any video (missing or empty env, invalid `MAX_TRANSCRIPT_CHARS`, unreadable `lecture.md` / `podcast.md`, Typer usage errors) are a short human message on stderr and a non-zero exit. No checkmarks, no `IngestError` JSON, and no new `stage`. The stage set stays `url`, `captions`, `metadata`, `consistency`, `llm`, `llm_truncation`, `persist`. — **Reversibility:** costly — adding a stage would change the operator JSON contract locked in Phase 7.

#### Re-run signal
- **D-09:** Every successful run prints `already_saved: true` or `already_saved: false` as the last stdout line. `true` means the video already had a material and the new draft was not written. `false` means this run inserted the row. — **Reversibility:** costly — the line is part of the stdout contract next to the four ids.
- **D-10:** A re-run exits 0, same as a first success. It is not an error.
- **D-11:** Successful stdout is only the three checkmarks, the four id lines, and `already_saved`. Do not print `video_id`, `provenance_label`, or other fields.
- **D-12:** On `already_saved: true`, `material_id`, `slug`, `batch_id`, and `rank` are the persisted row, not values computed for the discarded draft. The conflict branch of `persist_draft_and_enqueue` currently returns the caller-supplied `p_slug`, which can differ from the stored slug. Planning must print the stored slug. — **Reversibility:** costly — UAT notes and the operator identify the draft by slug; a generated-but-discarded slug would point at the wrong row.

#### UAT set
- **D-13:** UAT evidence is a manual note in the phase record: URL, template, `material_id`, and `slug` for each video. Do not add a Playwright test. The web Playwright project forces mocks, and the CLI is not a browser surface.
- **D-14:** The set is four captioned videos: lecture + `ru`, lecture + `en`, podcast + `ru`, podcast + `en`. English sources must still produce a Russian draft.
- **D-15:** The four URLs are chosen at UAT time, not locked in this discussion. The operator picks videos that have captions and writes the URLs into the phase note.
- **D-16:** For each video the operator confirms in `/admin/digest`: the row is on an unsent shortlist, `status=draft`, the body is Russian, an English source shows a provenance label ending with ` · пер. с англ.`, and the template headings are present (`## Тезис` / `## Ход рассуждения` / `## Вывод` or `## О чём разговор` / `## Позиции` / `## Что запомнить`).

#### Carried forward (do not re-open)
- Phase 9 D-09..D-11: idempotency stays in the RPC (`ON CONFLICT DO NOTHING`); no Python video-id pre-check; re-runs do not refresh content. A refreshed draft still requires deleting the old material first. The CLI still runs captions and LLM before persist on a re-run.
- Phase 8 D-05: the CLI builds `provenance_label` as `YouTube · {metadata.author}`, and appends ` · пер. с англ.` when `transcript.language != "ru"`. The assembler copies that label and does not invent it.
- Phase 7 D-24: fetch captions first, then metadata.
- Phase 7 deferred CONSISTENCY-01 into this phase: before the LLM call, fail closed with `stage=consistency` when `transcript.video_id` and `metadata.video_id` differ. No new stage name.
- CLI-04 checkmark strings are exactly `✓ transcript`, `✓ LLM`, and `✓ saved`.
- Backend and SPA stay readers. Drafts appear through the existing `/admin/digest` shortlist.

### Claude's Discretion
- Wording of pre-video human error messages, as long as they stay off the JSON envelope and print no checkmarks (D-08).
- Whether stderr JSON is one line or indented, as long as it is `IngestError.to_dict()` and not a traceback.
- How `already_saved` is detected and how the stored slug is read (D-09, D-12), as long as stdout matches the contract and Phase 9 no-refresh / no Python pre-check behavior stays.
- Typer help text and option names beyond the locked `ingest` script and `--template`.

### Deferred Ideas (OUT OF SCOPE)
- HTTP API or scheduler for ingestion — v2 (ING-01, ING-02).
- Transcription when captions are missing — v2 (ING-03).
- Transcript chunking — v2 (ING-04).
- Refreshing draft content on re-run — rejected in Phase 9; delete the material, then ingest again.
- Playwright coverage of live `/admin/digest` for this UAT — rejected (D-13).
- Extra stdout fields (`video_id`, `provenance_label`) — rejected (D-11).
- A new `IngestError` stage for config failures — rejected (D-08).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLI-01 | Typer one-shot prints `material_id`, `slug`, `batch_id`, `rank` on success | Stdout contract D-06; `PersistResult` fields; CliRunner tests; entry `ingest` |
| CLI-02 | Re-run same `video_id` does not duplicate materials/shortlist rows | RPC `ON CONFLICT DO NOTHING` already; extend with `already_saved` + stored slug (D-09/D-12) |
| CLI-03 | UAT 3–5 real captioned videos as drafts in `/admin/digest`, ≥1 English→Russian | Manual four-video matrix D-13…D-16; no Playwright; phase UAT note |
| CLI-04 | Staged progress `✓ transcript` / `✓ LLM` / `✓ saved` | Print-as-you-go in orchestrator after captions / article / persist (D-07) |
| CLI-05 | `ingestion-service` has its own `.env`, separate from backend | Operator `uv run --env-file ingestion-service/.env`; expand `.env.example`; no dotenv autoload in CLI (D-02) |
</phase_requirements>

## Summary

Phase 10 is the **composition root** that wires stages already built in Phases 7–9 into one Typer console script named `ingest`. Almost all adapter, mapper, Settings, and persist logic exists; the missing pieces are (1) the Typer entry + staged stdout contract, (2) a full pipeline that adds URL parse, captions-then-metadata, CONSISTENCY-01, provenance-label assembly, and checkmarks around the existing use-cases, (3) a small **RPC amend** so conflict returns the **stored** `materials.slug` and an `already_saved` flag (D-09/D-12 cannot be satisfied by comparing regenerated slugs), and (4) a **manual** four-video UAT note — not Playwright.

`run_ingest_until_persist` today only does captions → article → assemble → persist with a caller-supplied `VideoMetadata` and a hard-coded provenance without the English suffix. Phase 10 must own the full operator path; keep adapters free of `os.environ` and keep Backend/SPA untouched.

**Primary recommendation:** Add `typer` + `[project.scripts] ingest = "ingestion_service.cli:app"` via `uv add`; implement a single-command Typer app that `asyncio.run`s a composition-owned pipeline; ship migration `008` that amends `persist_draft_and_enqueue` to return stored `slug` + `already_saved`; unit-test the stdout/stderr contract with `CliRunner` and in-memory fakes; record four live UAT rows in a phase note.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI parse (`url`, `--template`) + exit codes | API / Backend (`ingestion-service` process) | — | Operator CLI is the delivery surface; not browser |
| Staged stdout / stderr JSON | API / Backend | — | D-05…D-08 operator contract |
| URL → `video_id` | API / Backend (`extract_video_id`) | — | Already in `ingestion-service` |
| Captions + oEmbed | API / Backend (via `data-collection` adapters) | External YouTube | Ports injected from composition |
| CONSISTENCY-01 | API / Backend (pipeline use-case) | — | Fail before LLM; no DB write |
| Provenance label build | API / Backend (pipeline / CLI layer) | — | Phase 8 D-05: caller builds; assembler copies |
| LLM article draft | API / Backend (`DeepSeekArticleGenerator`) | External DeepSeek | Existing adapter |
| Persist + shortlist enqueue | Database / Storage (RPC) | API adapter | Idempotency in Postgres; adapter maps result |
| `already_saved` + stored slug | Database / Storage (RPC amend) | PersistPort DTO | D-12 cannot be fixed in Python alone without a conflict signal |
| Admin draft visibility | Browser / Client (`/admin/digest`) | Backend reader | No SPA/backend code changes; shared DB |
| Secrets loading | Operator / process env (`uv --env-file`) | — | CLI-05; no dotenv inside app |

## Project Constraints (from AGENTS.md / cursor rules)

No `./CLAUDE.md` or `./.claude/CLAUDE.md` found in the workspace. Enforce:

- **TDD Red–Green–Refactor** — no production code without a failing test first (`AGENTS.md`, `.cursor/rules/tdd.mdc`).
- **Ports & Adapters** — composition owns wiring; domain/use-cases do not import Typer/httpx/supabase; adapters map SDK errors (`architecture.mdc`).
- **Python deps via `uv add` / `uv remove`** — never hand-edit dependency lists for installs (`.cursor/rules/python-uv.mdc`).
- **Git `origin` via WSL only** — not required for this research write; note for later ship.
- Project skills under `.agents/skills/` (supabase, supabase-postgres-best-practices, hallmark): any RPC amend must stay `security invoker`, `service_role`-only execute, idempotent `CREATE OR REPLACE`, no shared-VM reset.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `typer` | **0.27.2** (PyPI latest observed 2026-09-29); install with `uv add typer` (tutorial floor `>=0.21`) | CLI framework + `CliRunner` | Official Tiangolo/FastAPI Typer; Context7 docs for Argument/Option/Enum/`project.scripts` `[CITED: typer.tiangolo.com]` |
| `uv` | **0.10.9** (local probe) | `--env-file` + workspace scripts | Already project standard; `--env-file` documented `[CITED: docs.astral.sh/uv]` |
| Existing: `data-collection`, `openai`, `supabase`, `python-slugify` | workspace / locked ranges in `ingestion-service/pyproject.toml` | Pipeline stages | Do not replace |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `>=8.3.0` (workspace `dev`) | Unit suite | Already configured `testpaths = ["tests/unit"]` |
| stdlib `asyncio` | — | Bridge sync Typer → async ports | Inside command body |
| stdlib `json` | — | `json.dumps(error.to_dict())` on stderr | Pipeline failures only |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Typer | Click / argparse | Rejected by roadmap + CONTEXT (Typer one-shot) |
| Detect `already_saved` by comparing regenerated slug | RPC `already_saved` flag | Slug is deterministic on same title → false negatives; D-12 needs stored slug |
| Python video_id pre-check | RPC conflict | Forbidden by Phase 9 D-11 |
| Playwright UAT | Manual phase note | Locked D-13 |

**Installation:**

```bash
# from repo root (workspace member)
uv add --package ingestion-service typer
```

Then add to `ingestion-service/pyproject.toml` (via the same `uv` flow / planned edit):

```toml
[project.scripts]
ingest = "ingestion_service.cli:app"
```

**Version verification:** PyPI JSON `typer` latest = `0.27.2`; Homepage/Repository `https://github.com/fastapi/typer` `[VERIFIED: pypi.org/pypi/typer/json this session]`.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `typer` | PyPI | mature (repo FastAPI/Typer; latest release metadata 2026-08-28) | unknown (seam) | https://github.com/fastapi/typer | **SUS** (`unknown-downloads`) | **Keep — Flagged.** Official docs + Context7 + GitHub org match. Planner **must** add `checkpoint:human-verify` before `uv add typer`. |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** `typer` — human verify once; then proceed (not a slopsquat: Context7 `/websites/typer_tiangolo` + `/fastapi/typer`).

*No other new packages are required for this phase.*

## Architecture Patterns

### System Architecture Diagram

```text
Operator shell
  │  uv run --env-file ingestion-service/.env ingest <url> --template lecture|podcast
  ▼
Typer app (ingestion_service.cli:app)  ──stdout──►  ✓ transcript / ✓ LLM / ✓ saved
  │                                                 material_id / slug / batch_id / rank
  │                                                 already_saved: true|false
  │  ──stderr──►  IngestError.to_dict() JSON  OR  short human config/usage message
  ▼
Composition (Settings.from_env → client factories → adapters)
  ▼
Pipeline use-case (async)
  1. extract_video_id / map_url_error          stage=url
  2. TranscriptProvider.get                   → print ✓ transcript | stage=captions
  3. VideoMetadataProvider.get                stage=metadata
  4. if transcript.video_id != metadata.video_id → stage=consistency (no LLM)
  5. build provenance_label (+ EN suffix)     (caller; not provenance.py builder)
  6. ArticleGenerator.process                 → print ✓ LLM | stage=llm|llm_truncation
  7. assemble_material_draft + persist_draft  → print ✓ saved | stage=persist
  ▼
PersistPort → SupabaseDraftPersister.rpc(persist_draft_and_enqueue)
  ▼
Postgres (materials UNIQUE youtube_video_id + shortlist)
  ▼
Existing backend reader → SPA /admin/digest (no code change)
```

### Recommended Project Structure

```text
ingestion-service/
  pyproject.toml                 # + typer dep; [project.scripts] ingest = ...
  .env.example                   # expand DeepSeek / YouTube / Supabase keys (no secrets)
  .env                           # gitignored operator file (CLI-05)
  src/ingestion_service/
    cli.py                       # Typer app only (thin)
    composition/
      settings.py                # existing Settings.from_env
      clients.py                 # wire YouTubeTranscriptAdapter / OEmbed / DeepSeek / Persist
    application/use_cases/
      ingest_pipeline.py         # NEW full orchestrator (or extend ingest_until_persist)
      persist_draft.py           # existing
    application/ports/persist.py # PersistResult += already_saved
    adapters/supabase_persist.py # parse already_saved + slug from RPC
    domain/errors.py             # Stage set unchanged
    provenance.py                # ENGLISH_TRANSLATION_SUFFIX only (keep no builder)
supabase-integration/migrations/
  008_phase10_persist_already_saved.sql   # CREATE OR REPLACE RPC: stored slug + already_saved
tests/unit/
  test_cli_ingest_contract.py    # CliRunner stdout/stderr/exit
  test_ingest_pipeline.py        # consistency, checkmark order via spy/callback
  test_persist_*                 # update for PersistResult.already_saved
```

### Pattern 1: Single-command Typer entry (no subcommand)

**What:** One `@app.command()` so `ingest <url> --template lecture` needs no `run` subcommand.
**When to use:** Locked D-03/D-04.
**Example:**

```python
# Source: https://typer.tiangolo.com/tutorial/commands/one-or-multiple
# + https://typer.tiangolo.com/tutorial/options/required
# + https://typer.tiangolo.com/tutorial/parameter-types/enum
from enum import Enum
from typing import Annotated

import typer

# Prefer reusing data_collection.dto.template_kind.TemplateKind (values "lecture"|"podcast")
# [VERIFIED: data-collection/.../template_kind.py:5-7]
# class TemplateKind(str, Enum):
#     LECTURE = "lecture"
#     PODCAST = "podcast"

app = typer.Typer()

@app.command()
def main(
    url: Annotated[str, typer.Argument()],
    template: Annotated[TemplateKind, typer.Option("--template")],
) -> None:
    ...
```

`[project.scripts] ingest = "ingestion_service.cli:app"` per packaging tutorial `[CITED: typer.tiangolo.com/tutorial/package]`.

### Pattern 2: Env via `uv run --env-file`, not dotenv in-app

**What:** Operator injects process env; `Settings.from_env()` reads `os.environ` only.
**When to use:** Always (D-02, CLI-05).
**Evidence:** Backend runbook already requires `uv run --env-file .env`; uv docs confirm `--env-file` loads dotenv into the process `[CITED: docs.astral.sh/uv/concepts/configuration-files]`. `Settings.from_env` signature:

```python
# [VERIFIED: ingestion-service/.../composition/settings.py:62-64]
@classmethod
def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
    env = environ if environ is not None else os.environ
```

### Pattern 3: Progress + error split

**What:** Print checkmarks immediately after stage success on **stdout**; on `IngestError`, leave prior checkmarks, dump `to_dict()` JSON on **stderr**, `raise typer.Exit(code=error.exit_code)`.
**When to use:** All pipeline failures after video work starts.
**Config/template failures:** human stderr message, exit 1, no JSON (D-08).

### Pattern 4: RPC returns `already_saved` + stored slug (recommended discretion for D-09/D-12)

**What:** Amend `persist_draft_and_enqueue` so conflict branch selects `materials.slug` and sets `already_saved = (v_inserted = 0)`.
**Why not Python-only:** Regenerated slug equals stored slug when the LLM title is unchanged → cannot detect re-runs; wrong slug when title changes (current bug at lines 164–168 of migration 007).
**Keep:** No Python video_id pre-check; CLI still runs captions+LLM before persist.

Conflict return today (caller `p_slug`):

```164:169:supabase-integration/migrations/007_phase9_persist_draft.sql
    return jsonb_build_object(
      'material_id', v_material_id,
      'slug', p_slug,
      'batch_id', v_batch_id,
      'rank', v_rank
    );
```

### Anti-Patterns to Avoid

- **Autoload dotenv inside CLI** — breaks D-02 and diverges from backend ops.
- **Subcommand `ingest run`** — violates D-04.
- **JSON success envelope** — violates D-05.
- **Printing `video_id` / `provenance_label` on success** — violates D-11.
- **Python pre-check for existing video_id** — violates Phase 9 D-11.
- **Adding `build_provenance_label` to `provenance.py`** — breaks Phase 8 test `test_provenance_module_has_no_label_builder` `[VERIFIED: tests/unit/test_translation_marker.py:22-26]`.
- **Leaving `test_ingestion_service_has_no_typer_import` unchanged** — Phase 8 scope lock; Phase 10 must replace with “only `cli.py` may import typer” `[VERIFIED: tests/unit/test_data_collection_public_api.py:119-125]`.
- **Playwright for UAT** — D-13 rejected.
- **Backend/SPA edits so drafts appear** — out of scope; shared DB is the contract.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI parsing / help / exit | argparse wrappers | Typer Argument/Option/Enum | Enum choices + required Option are one-liners |
| Dotenv loading | custom `.env` parser in CLI | `uv run --env-file` | Matches backend; Settings already env-injected |
| Idempotency | Python SELECT-then-INSERT | RPC `ON CONFLICT DO NOTHING` | Race-safe; locked Phase 9 |
| Stored slug on conflict | Guess from regenerated draft | SQL `materials.slug` in RPC return | D-12 |
| CLI unit I/O | subprocess to live `ingest` | `typer.testing.CliRunner` | Fast, deterministic stdout/stderr |
| Provenance suffix string | hard-code elsewhere | `ENGLISH_TRANSLATION_SUFFIX` | Locked Phase 8 |

**Key insight:** Phase 10 is mostly wiring + operator contract tests. The only schema touch should be the minimal RPC amend for D-09/D-12 — not a new persist design.

## Runtime State Inventory

> Triggered: small migration amend to live RPC on shared VM (same class of risk as Phase 9).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Live `public.persist_draft_and_enqueue` on shared Supabase VM (migration 007 applied). Conflict rows already store correct `materials.slug`; RPC **returns** wrong `p_slug`. | **Data migration:** none for row data. **Schema/code:** apply `008` `CREATE OR REPLACE FUNCTION` so returns match stored slug + `already_saved`. Human gate before shared-VM apply (mirror Phase 9). |
| Live service config | Operator secrets live in untracked `ingestion-service/.env` (expected) and root `.env` (backend). | Ensure UAT uses **ingestion** env file only; do not point CLI at root `.env`. |
| OS-registered state | None — verified: no scheduler/systemd unit for ingest in this milestone. | none |
| Secrets/env vars | `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `DEEPSEEK_*`, optional `YOUTUBE_PROXY_URL`, `MAX_TRANSCRIPT_CHARS`, `SHORTLIST_BATCH_SIZE` | Expand `ingestion-service/.env.example` keys (empty values). Do not rename keys. |
| Build artifacts | No `[project.scripts]` yet; after add, `uv sync` refreshes console script wrappers. | `uv sync` after typer + scripts entry |

## Common Pitfalls

### Pitfall 1: Wrong slug on re-run (D-12)
**What goes wrong:** Operator copies `slug:` from stdout after re-run and cannot find the draft (or finds a non-existent slug).
**Why it happens:** Migration 007 conflict branch returns `p_slug`.
**How to avoid:** Migration 008 returns `(SELECT slug FROM materials WHERE id = v_material_id)` (or join already in scope) + unit/SQL contract tests.
**Warning signs:** Re-run stdout slug ≠ `materials.slug` for that `material_id`.

### Pitfall 2: Detecting `already_saved` by slug equality
**What goes wrong:** Re-runs with identical LLM titles print `already_saved: false`.
**Why it happens:** Slug format embeds `video_id`; same title → same slug.
**How to avoid:** Use RPC `already_saved` / `v_inserted` only.

### Pitfall 3: Checkmarks after failure / JSON on stdout
**What goes wrong:** Operators cannot pipe stderr diagnostics; progress lies.
**Why it happens:** Printing checkmarks in a `finally` or dumping errors with `typer.echo` defaulting to stdout.
**How to avoid:** Print checkmark only after stage success; `typer.echo(..., err=True)` or `print(..., file=sys.stderr)` for errors; CliRunner asserts split.

### Pitfall 4: Forgetting CONSISTENCY-01 before LLM
**What goes wrong:** LLM billed / called with mismatched ids; CAP-02-style “zero persist” not enough.
**Why it happens:** Current `run_ingest_until_persist` assumes caller metadata matches.
**How to avoid:** Explicit compare; spy asserts `FakeArticleGenerator` not called; reason e.g. `video_id_mismatch` (discretion — lock in plan tests).

### Pitfall 5: Config errors emitted as `IngestError` JSON
**What goes wrong:** Stage set polluted; operators confuse env mistakes with video failures.
**Why it happens:** Catch-all `except Exception` → `to_dict()`.
**How to avoid:** Separate branches for `ConfigurationError` / `TemplateLoadError` / Typer usage (D-08).

### Pitfall 6: Reusing root `.env` for UAT
**What goes wrong:** CLI-05 fails verification; wrong keys / accidental publishable-only mix.
**Why it happens:** Habit from backend runbook.
**How to avoid:** Document exact `uv run --env-file ingestion-service/.env ingest ...`; expand ingestion `.env.example`.

### Pitfall 7: Leaving Phase 8 “no typer” test green-blocking
**What goes wrong:** First green CLI commit fails CI.
**How to avoid:** RED test that allows `cli.py` only, then implement.

## Code Examples

### CliRunner contract test shape

```python
# Source: https://typer.tiangolo.com/tutorial/testing
from typer.testing import CliRunner

runner = CliRunner()

def test_success_stdout_order(monkeypatch):
    # wire fakes via composition seam / dependency override in cli module
    result = runner.invoke(app, ["https://youtu.be/dQw4w9WgXcQ", "--template", "lecture"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == [
        "✓ transcript",
        "✓ LLM",
        "✓ saved",
        "material_id: 42",
        "slug: kak-ispolzovat-pgvector-dQw4w9WgXcQ",
        "batch_id: 7",
        "rank: 1",
        "already_saved: false",
    ]
    assert result.stderr == ""
```

### Provenance build (inline in pipeline — not in provenance.py)

```python
# Locked Phase 8 D-05 / Phase 10 carried-forward
from ingestion_service.provenance import ENGLISH_TRANSLATION_SUFFIX

label = f"YouTube · {metadata.author}"
if transcript.language != "ru":
    label = f"{label}{ENGLISH_TRANSLATION_SUFFIX}"
# assemble_material_draft(article, metadata, label)
```

### Pipeline failure exit

```python
# Source: https://typer.tiangolo.com/tutorial/terminating
import json
import typer
from ingestion_service.domain.errors import IngestError

try:
    ...
except IngestError as err:
    typer.echo(json.dumps(err.to_dict()), err=True)
    raise typer.Exit(code=err.exit_code)
```

### PersistResult extension (discretion recommendation)

```python
# Amend [VERIFIED: ingestion-service/.../application/ports/persist.py:11-16]
@dataclass(frozen=True)
class PersistResult:
    material_id: int
    slug: str
    batch_id: int
    rank: int
    already_saved: bool  # NEW — from RPC
```

`PersistResult` today has only the four id fields `[VERIFIED: persist.py:11-16]`:

```text
material_id: int
slug: str
batch_id: int
rank: int
```

### FakeDraftPersister re-run behavior to extend

```python
# [VERIFIED: ingestion-service/.../tests_support/fakes.py:32-36]
existing = self.stored.get(material_draft.youtube_video_id)
if existing is not None:
    return existing  # today: same PersistResult; tomorrow: already_saved=True + stored slug
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-rolled argparse CLIs | Typer + type hints + Enum | Typer 0.x mainstream | Faster operator contract tests |
| App-level dotenv | Process injection (`uv --env-file`) | uv 0.4.30+ `UV_ENV_FILE` | Composition stays pure |
| Multi-call SDK persist | Single Postgres RPC | Phase 9 | Idempotent enqueue |
| Conflict returns `p_slug` | Conflict returns stored slug + `already_saved` | **Phase 10 amend** | Fixes D-12 / D-09 |

**Deprecated/outdated:**
- Phase 8 test ban on any typer import in `ingestion-service` — scope lock for Phase 8 only; supersede in Phase 10.
- Assuming `run_ingest_until_persist` is the full CLI pipeline — it is a CAP-02 composer stub, not the operator path.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Consistency failure `reason` should be `video_id_mismatch` (not locked in CONTEXT) | Architecture / Pitfalls | Planner must lock reason string in PLAN tests |
| A2 | Typer single `@app.command()` exposes args without a command name when installed as console script | Standard Stack | If packaging differs, use Typer callback pattern — verify with smoke `uv run ingest --help` |
| A3 | Shared VM will accept `008` via Studio/MCP the same way as `007` | Runtime State | Human gate; do not `db reset` |
| A4 | Four-video UAT is enough for REQUIREMENTS CLI-03 “3–5” | UAT | ROADMAP says 3–5; CONTEXT locks four — treat four as authoritative |

**If empty were required:** N/A — table has discretionary items needing plan locks.

## Open Questions (RESOLVED)

1. **Migration number and apply ritual** — RESOLVED: New `008_phase10_persist_already_saved.sql` with `CREATE OR REPLACE` of `persist_draft_and_enqueue` (idempotent); never edit applied `007` in place; one-way `checkpoint:decision` then author in 10-03; `[BLOCKING]` `supabase db push` in 10-05 after the migration file exists (D-09, D-12).
   - What we know: Phase 9 used `007` + human Studio apply + checkpoint.
   - Recommendation (honored): **New `008` file** with `CREATE OR REPLACE`; human checkpoint before apply.

2. **Composition seam for CliRunner** — RESOLVED: Injectable async `run_ingest_pipeline(...)` plus thin `cli.py` `build_ingest_deps()` (or equivalent); CliRunner monkeypatches the builder with fakes (locked in 10-01 tracer; no env-flag override).
   - What we know: Need to inject fakes without network.
   - Recommendation (honored): Pure `run_ingest_pipeline` + thin CLI; tests monkeypatch builder.

3. **Exact consistency `reason` string** — RESOLVED: `reason=video_id_mismatch` with context keys only `transcript_video_id`, `metadata_video_id` (locked in 10-02; CONSISTENCY-01; A1).
   - Recommendation (honored): Lock `video_id_mismatch` in PLAN tests; no transcript text in context.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | ingestion-service | ✓ | 3.14.0 (also requires-python `>=3.12`) | — |
| `uv` | deps + `--env-file` + scripts | ✓ | 0.10.9 | — |
| `pytest` | unit suite | ✓ | via workspace `dev` | — |
| Typer | CLI | ✗ not installed yet | — | `uv add` after human-verify |
| DeepSeek API key | Live UAT LLM | operator-owned | — | Manual UAT blocked without key |
| Supabase service_role | Live persist UAT | operator `.env` | — | Manual UAT blocked without VM |
| YouTube egress / proxy | Live captions UAT | optional `YOUTUBE_PROXY_URL` | — | Expect `youtube_blocked` without proxy from Cloud.ru |
| Playwright | — | N/A | — | **Do not use** (D-13) |

**Missing dependencies with no fallback:** live DeepSeek key + Supabase service credentials + captioned YouTube access for UAT (unit tests do not need them).

**Missing dependencies with fallback:** `YOUTUBE_PROXY_URL` — required only when direct YouTube is blocked; document in runbook/UAT note.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `>=8.3.0` |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`) |
| Quick run command | `uv run pytest tests/unit/test_cli_ingest_contract.py tests/unit/test_ingest_pipeline.py -x` |
| Full suite command | `uv run pytest tests/unit -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | Success stdout prints four id lines | unit (CliRunner) | `uv run pytest tests/unit/test_cli_ingest_contract.py -x` | ❌ Wave 0 |
| CLI-02 | Second persist same video_id → one stored material; `already_saved: true`; stored slug | unit (fake + RPC SQL contract) | `uv run pytest tests/unit/test_persist_idempotency_overflow.py tests/unit/test_phase10_migration_008.py -x` | ⚠️ extend existing / ❌ new migration test |
| CLI-03 | Four real drafts in `/admin/digest` | **manual** UAT note | — | ❌ Wave 0 (`10-UAT.md` template) |
| CLI-04 | Checkmark order; no checkmark after failing stage | unit | `uv run pytest tests/unit/test_cli_ingest_contract.py -x` | ❌ Wave 0 |
| CLI-05 | `.env.example` under `ingestion-service/`; CLI does not read dotenv path itself | unit + file assert | `uv run pytest tests/unit/test_ingestion_env_example.py -x` | ❌ Wave 0 |
| CONSISTENCY-01 | Mismatched ids → `stage=consistency`, article not called, persist not called | unit | `uv run pytest tests/unit/test_ingest_pipeline.py -x` | ❌ Wave 0 |
| D-08 | Missing env → human stderr, no JSON keys `stage`/`ok` | unit | same CliRunner file | ❌ Wave 0 |
| D-10 | Re-run exit 0 | unit | CliRunner | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** targeted CliRunner / pipeline / migration tests (`-x`)
- **Per wave merge:** `uv run pytest tests/unit -q`
- **Phase gate:** Full unit suite green + manual `10-UAT.md` four rows filled before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_cli_ingest_contract.py` — covers CLI-01, CLI-04, D-05…D-11
- [ ] `tests/unit/test_ingest_pipeline.py` — CONSISTENCY-01, provenance suffix, captions-then-metadata order, CAP-02 persist spy through full pipeline
- [ ] `tests/unit/test_phase10_migration_008.py` — SQL/contract: conflict returns stored slug + `already_saved`
- [ ] `tests/unit/test_ingestion_env_example.py` — CLI-05 example keys present; not the root backend file
- [ ] Replace `test_ingestion_service_has_no_typer_import` with “only `cli.py` imports typer”
- [ ] Extend `FakeDraftPersister` / `PersistResult` / adapter parse tests for `already_saved`
- [ ] `10-UAT.md` manual checklist (four videos) — not automated

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (CLI uses service_role key locally; no end-user auth) | — |
| V3 Session Management | no | — |
| V4 Access Control | yes (DB) | RPC `GRANT EXECUTE … TO service_role` only; revoke anon/authenticated (mirror 007) |
| V5 Input Validation | yes | `extract_video_id` allowlist; Typer Enum for template; Settings positive-int checks |
| V6 Cryptography | no new crypto | Do not hand-roll; secrets stay in env files |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Service role key leakage via stderr/logs | Information Disclosure | Never put keys in `IngestError.context`; D-08 human messages must not interpolate secrets |
| Credentialed YouTube proxy URL in diagnostics | Information Disclosure | Existing URL userinfo redaction in `extract_video_id` / map allowlists (Phase 7 harden) |
| SQL injection via RPC params | Tampering | Named RPC params only; no string-built SQL in Python |
| Privilege escalation via open EXECUTE | Elevation | Keep revoke/grant pattern from 007 in 008 |
| Operator points CLI at wrong env file | Spoofing / Misconfig | Document CLI-05 path; separate `.env.example` |
| Traceback with request payloads | Information Disclosure | Catch mapped errors; no bare `raise` of SDK exceptions from CLI |

## Sources

### Primary (HIGH / MEDIUM confidence)

- Context7 `/websites/typer_tiangolo` — Argument, required Option, Enum, single command, packaging `project.scripts`
- Context7 `/fastapi/typer` — CliRunner stdout/stderr/exit_code, `typer.Exit`
- Context7 `/websites/astral_sh_uv` — `uv run --env-file`
- In-repo: `10-CONTEXT.md`, `REQUIREMENTS.md` CLI-01…05, migration `007_phase9_persist_draft.sql:164-169`, `persist.py:11-16`, `settings.py:62-64`, `ingest_until_persist.py`, `fakes.py:32-36`, `test_data_collection_public_api.py:119-125`, `test_translation_marker.py:22-26`, `template_kind.py:5-7`
- PyPI JSON `typer` latest `0.27.2` + GitHub `fastapi/typer`

### Secondary

- `.planning/phases/09-*-RESEARCH/VERIFICATION` — persist idempotency, CAP-02 composer, leftover advisory on conflict `p_slug`
- `docs/agents/local-platform-runbook.md` — DeepSeek / YouTube env names; backend `--env-file` pattern

### Tertiary

- Package-legitimacy seam `SUS` for `typer` (`unknown-downloads`) — treat as process flag, not package rejection

## Metadata

**Confidence breakdown:**
- Standard stack: **MEDIUM-HIGH** — Typer/uv verified via Context7 + PyPI; legitimacy SUS on downloads metadata only
- Architecture: **HIGH** — CONTEXT locks + code seams read this session
- Pitfalls: **HIGH** — D-12 RPC bug confirmed by reading migration 007

**Research date:** 2026-09-29
**Valid until:** 2026-10-29 (Typer minors move; re-check pin if >30 days)
