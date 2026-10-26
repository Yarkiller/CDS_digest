# Phase 10: CLI Composition & UAT - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Operator runs one Typer command that wires the existing ingestion stages (URL parse → captions → metadata → consistency → LLM → persist) and prints staged progress plus the persist ids. Re-runs of the same video do not create duplicate rows and do not refresh draft content. Secrets come from `ingestion-service/.env`, passed explicitly, separate from the backend env file. UAT is a manual check: four real captioned videos show up as Russian drafts in `/admin/digest`.

This phase does not add an HTTP API, a scheduler, transcription without captions, or any backend/SPA change.

</domain>

<decisions>
## Implementation Decisions

### Command shape
- **D-01:** The one-shot is a positional YouTube URL (or other input `extract_video_id` already accepts) plus a required `--template` flag whose only values are `lecture` and `podcast`. There is no default template. — **Reversibility:** costly — the flag is the operator contract for LLM-02; a later default would change every runbook line and test.
- **D-02:** The process environment is supplied by the operator as `uv run --env-file ingestion-service/.env`. The CLI does not auto-load a dotenv file. — **Reversibility:** reversible — the path is local ops; `Settings.from_env` already reads the process environment.
- **D-03:** The console script name is `ingest`. — **Reversibility:** costly — the name is the published entry point in `ingestion-service` pyproject scripts.
- **D-04:** `ingest` itself is the one-shot. There is no subcommand (`ingest run` is out). Invocation: `uv run --env-file ingestion-service/.env ingest <url> --template lecture|podcast`.

### Terminal output
- **D-05:** Success is human lines on stdout. A pipeline failure is the existing `IngestError.to_dict()` JSON object on stderr and a non-zero exit. Success is not JSON. — **Reversibility:** costly — stdout/stderr split is the operator contract for CLI-01 and CLI-04.
- **D-06:** After `✓ saved`, stdout prints four lines, exactly these keys: `material_id`, `slug`, `batch_id`, `rank`, each as `key: value`.
- **D-07:** Each checkmark is printed as soon as that stage succeeds, in order: `✓ transcript`, then `✓ LLM`, then `✓ saved`. A failing stage prints no checkmark. Earlier checkmarks stay on stdout; the JSON error goes to stderr. Metadata and consistency do not get their own checkmarks. `✓ transcript` means captions succeeded. `✓ LLM` means a validated article draft exists. `✓ saved` means persist returned.
- **D-08:** Errors before any video (missing or empty env, invalid `MAX_TRANSCRIPT_CHARS`, unreadable `lecture.md` / `podcast.md`, Typer usage errors) are a short human message on stderr and a non-zero exit. No checkmarks, no `IngestError` JSON, and no new `stage`. The stage set stays `url`, `captions`, `metadata`, `consistency`, `llm`, `llm_truncation`, `persist`. — **Reversibility:** costly — adding a stage would change the operator JSON contract locked in Phase 7.

### Re-run signal
- **D-09:** Every successful run prints `already_saved: true` or `already_saved: false` as the last stdout line. `true` means the video already had a material and the new draft was not written. `false` means this run inserted the row. — **Reversibility:** costly — the line is part of the stdout contract next to the four ids.
- **D-10:** A re-run exits 0, same as a first success. It is not an error.
- **D-11:** Successful stdout is only the three checkmarks, the four id lines, and `already_saved`. Do not print `video_id`, `provenance_label`, or other fields.
- **D-12:** On `already_saved: true`, `material_id`, `slug`, `batch_id`, and `rank` are the persisted row, not values computed for the discarded draft. The conflict branch of `persist_draft_and_enqueue` currently returns the caller-supplied `p_slug`, which can differ from the stored slug. Planning must print the stored slug. — **Reversibility:** costly — UAT notes and the operator identify the draft by slug; a generated-but-discarded slug would point at the wrong row.

### UAT set
- **D-13:** UAT evidence is a manual note in the phase record: URL, template, `material_id`, and `slug` for each video. Do not add a Playwright test. The web Playwright project forces mocks, and the CLI is not a browser surface.
- **D-14:** The set is four captioned videos: lecture + `ru`, lecture + `en`, podcast + `ru`, podcast + `en`. English sources must still produce a Russian draft.
- **D-15:** The four URLs are chosen at UAT time, not locked in this discussion. The operator picks videos that have captions and writes the URLs into the phase note.
- **D-16:** For each video the operator confirms in `/admin/digest`: the row is on an unsent shortlist, `status=draft`, the body is Russian, an English source shows a provenance label ending with ` · пер. с англ.`, and the template headings are present (`## Тезис` / `## Ход рассуждения` / `## Вывод` or `## О чём разговор` / `## Позиции` / `## Что запомнить`).

### Carried forward (do not re-open)
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 10 goal, success criteria, CLI-01..CLI-05
- `.planning/REQUIREMENTS.md` — CLI-01..CLI-05; out of scope (no auto-ready, no backend/SPA changes); v2 ING-01..ING-04
- `.planning/PROJECT.md` — thin `ingestion-service` CLI, no HTTP API; DeepSeek MVP bend of ADR-0002
- `.planning/phases/07-captions-adapter/07-CONTEXT.md` — `IngestError` stages, captions-then-metadata, CONSISTENCY-01 deferred to Phase 10
- `.planning/phases/08-deepseek-article-templates/08-CONTEXT.md` — provenance label formula (D-05), always-Russian output, heading strings, UAT checks headings
- `.planning/phases/09-draft-persist-shortlist-enqueue/09-CONTEXT.md` — `PersistResult` fields, RPC idempotency, no content refresh

### Architecture & process rules
- `.cursor/rules/architecture.mdc` — Ports & Adapters; composition owns wiring
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `.cursor/rules/python-uv.mdc` — add Typer with `uv add`, not a hand-edited dependency list
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — FoundryModels long-term; DeepSeek is temporary
- `docs/adr/0004-self-hosted-supabase-on-vm.md` — self-hosted Supabase as the store

### Ingestion code contracts
- `ingestion-service/src/ingestion_service/url.py` — `extract_video_id`; CLI input goes through this
- `ingestion-service/src/ingestion_service/domain/errors.py` — `IngestError` / `Stage` / `to_dict()`
- `ingestion-service/src/ingestion_service/composition/settings.py` — `Settings.from_env`; no dotenv autoload
- `ingestion-service/src/ingestion_service/application/ports/persist.py` — `PersistResult` has `material_id`, `slug`, `batch_id`, `rank` only
- `ingestion-service/src/ingestion_service/application/use_cases/persist_draft.py` — persist use-case the CLI calls
- `supabase-integration/migrations/007_phase9_persist_draft.sql` — `persist_draft_and_enqueue`; conflict branch returns `p_slug`
- `data-collection/src/data_collection/templates/lecture.md` — lecture headings
- `data-collection/src/data_collection/templates/podcast.md` — podcast headings

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `extract_video_id` and `map_url_error` — CLI input and `stage=url` failures.
- `IngestError.to_dict()` — stderr JSON for pipeline failures. Do not invent a second envelope.
- `Settings.from_env` plus composition client factories — env is already injected; adapters do not read `os.environ`.
- `persist_draft` / `PersistPort` / `PersistResult` — success ids. `PersistResult` has no `already_saved` flag yet.
- `FakeDraftPersister` and the other in-memory fakes — unit-test the pipeline without network or Supabase.
- Lecture and podcast markdown templates — `--template` selects these; missing file already fails at load.

### Established Patterns
- Backend does not autoload `.env`; operators pass `uv run --env-file`. Match that for `ingestion-service/.env` (D-02).
- Unit tests live in `tests/unit/` and import `ingestion_service` inside the test. No network in the default suite. Live YouTube stays manual (UAT), not `@pytest.mark.integration` unless planning adds an optional gate.
- Pipeline failures map to locked `stage` + `reason`. Config and missing-template failures stay outside that envelope (Phase 8 D-17, D-08 here).
- TDD: failing test before production code, including the Typer stdout contract.

### Integration Points
- New Typer entry `ingest` in `ingestion-service` wires existing stages. No FastAPI import and no SPA edits.
- `persist_draft_and_enqueue` conflict return uses `p_slug` (the slug computed this run), while `material_id`, `batch_id`, and `rank` are the existing row. D-12 requires the stored slug on stdout.
- `/admin/digest` already reads unsent shortlist rows. UAT looks there; migration 007 is already the persist path.
- There is no `[project.scripts]` entry yet. Planning adds the `ingest` script and the `typer` dependency via `uv`.

</code_context>

<specifics>
## Specific Ideas

Exact invocation:

```text
uv run --env-file ingestion-service/.env ingest <url> --template lecture
uv run --env-file ingestion-service/.env ingest <url> --template podcast
```

Exact success stdout (first run):

```text
✓ transcript
✓ LLM
✓ saved
material_id: 42
slug: kak-ispolzovat-pgvector-dQw4w9WgXcQ
batch_id: 7
rank: 1
already_saved: false
```

Same shape on a re-run, with `already_saved: true` and the stored ids. Exit code 0 either way.

English provenance example (unchanged from Phase 8): `YouTube · Сбер Pro · пер. с англ.`

</specifics>

<deferred>
## Deferred Ideas

- HTTP API or scheduler for ingestion — v2 (ING-01, ING-02).
- Transcription when captions are missing — v2 (ING-03).
- Transcript chunking — v2 (ING-04).
- Refreshing draft content on re-run — rejected in Phase 9; delete the material, then ingest again.
- Playwright coverage of live `/admin/digest` for this UAT — rejected (D-13).
- Extra stdout fields (`video_id`, `provenance_label`) — rejected (D-11).
- A new `IngestError` stage for config failures — rejected (D-08).

</deferred>

---

*Phase: 10-CLI Composition & UAT*
*Context gathered: 2026-09-29*
