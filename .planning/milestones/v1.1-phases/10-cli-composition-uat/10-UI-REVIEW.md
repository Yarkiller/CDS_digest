# Phase 10 — UI Review

**Audited:** 2026-10-02
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md)
**Screenshots:** not captured (no Digest/Vite dev server)
**Interaction captures:** off (workflow.ui_interaction_capture is false)

**Scope:** Phase 10 shipped an operator CLI (`ingest`), composition wiring, migration 008, and a manual UAT note. It did not add or edit a web frontend (`10-04` records no `backend/` or `web/` changes; D-13 forbids a Playwright spec). Pillar scores below are for that CLI surface: `--help`, usage errors, staged stdout, and stderr. They are not a score of `/admin/digest` or `/materials/<slug>`.

Ports 3000 and 5173 were closed. Port 8080 returned HTTP 200 for an unrelated EnterpriseDB status page (`Server is up and running`), so it was not used as a product capture.

Registry audit: skipped. No `components.json` in the repo.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Help and config errors name the flag or env key; pipeline failures are snake_case codes inside one JSON line |
| 2. Visuals | 3/4 | `--help` and usage errors use Rich panels; the success contract is eight plain lines with no group break |
| 3. Color | 3/4 | Rich colors only the help/usage chrome; checkmarks, ids, and pipeline errors share the default foreground |
| 4. Typography | 4/4 | Success stdout is one face and one weight; the locked lines introduce no second size scale |
| 5. Spacing | 3/4 | Checkmarks and id lines are contiguous echoes with no blank line between progress and result |
| 6. Experience Design | 2/4 | Captions and LLM awaits print nothing until they finish; a failed stage has no stdout failure mark |

**Overall: 18/24**

No pillar is 1. No BLOCKER on the CLI: a first run and a re-run can complete, and UAT recorded four drafts. Findings below are WARNINGs unless noted.

---

## Top 3 Priority Fixes

1. **Silent waits before the first checkmark and between `✓ transcript` and `✓ LLM`** — a live captions fetch or DeepSeek call looks hung — emit a plain status line on stderr before each await (wording that is not one of the three locked checkmarks), and keep `on_stage` only after success (`ingest_pipeline.py` awaits at lines 46 and 74; `cli.py` prints a mark only in `_on_stage`).
2. **Pipeline stderr is one compact JSON object whose `message` repeats a code** (`llm network_error`, `captions no_captions for {id}`, `url {reason}`) — the operator gets no sentence and no next step — pretty-print with `json.dumps(..., indent=2)` in `cli.py` line 76 (the contract test `json.loads`s the whole stderr, so indentation still parses) and set `message` to a short sentence while leaving `reason` as the stable code (`mapping/article.py` 73–76, `mapping/captions.py` 67–70, `mapping/url.py` 18–22).
3. **A re-run still prints `✓ saved` and then `already_saved: true`** — `saved` reads as a new write — when `result.already_saved` is true, print a distinct last progress line such as `✓ already saved` (or print `✓ saved` only for an insert). This changes the D-07 string lock, so treat it as a contract amendment, not a silent tweak (`cli.py` 27–31 and 79–83; `ingest_pipeline.py` 85–86 always calls `on_stage("saved")` after persist returns).

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

**WARNING.** Success copy and usage copy are specific. Failure copy for the pipeline is a machine code.

What holds:

- Command help, captured from `uv run --package ingestion-service ingest --help`: `Ingest a YouTube URL into a materials draft + shortlist row.` Argument help is `YouTube URL or video id`. Option help is `Prompt template: lecture or podcast`, marked required, enum `lecture|podcast` (`cli.py` 49–57).
- Missing `--template` (exit 2): `Missing option '--template'. Choose from: lecture, podcast`. Missing URL: `Missing argument 'url'.` Invalid template: `Invalid value for '--template': 'essay' is not one of 'lecture', 'podcast'.` The installed script usage line is `Usage: ingest [OPTIONS] {url}` (CliRunner alone prints `main` because it has no argv0; that string is not what the operator sees).
- Pre-video errors stay human and name the key, with no checkmarks (`cli.py` 71–74): `DEEPSEEK_API_KEY is required` (`composition/clients.py` 54), `SUPABASE_URL and SUPABASE_SECRET_KEY are required` (`composition/clients.py` 93), `MAX_TRANSCRIPT_CHARS must be a positive integer` and `SHORTLIST_BATCH_SIZE must be a positive integer` (`composition/settings.py` 22–26, 37–41), `could not load template for {kind}` (`data-collection/src/data_collection/templates/__init__.py` 18).
- Success stdout is the locked eight lines and nothing else (`cli.py` 79–83). No `Submit`, `Click Here`, `OK`, or `Something went wrong`.

What fails the abstract standard:

- `IngestError` stderr is `json.dumps(err.to_dict())` with default separators (`cli.py` 76). `message` is the reason code again: `llm {reason}` (`mapping/article.py` 66, 76), `captions {reason} for {video_id}` (`mapping/captions.py` 70), `url {reason}` (`mapping/url.py` 22), `transcript and metadata video_id mismatch` (`ingest_pipeline.py` 62). An operator who hits missing captions sees one line shaped like `{"ok": false, "stage": "captions", "reason": "no_captions", "message": "captions no_captions for …", "exit_code": 1}`. The `reason` field is the right stable code; the `message` field does not say what to do.
- `✓ saved` on an idempotent re-run (D-09 still prints `already_saved: true` on the last line) uses the everyday word for a write that did not happen. The last line corrects it only if the operator reads that far.

### Pillar 2: Visuals (3/4)

**WARNING.** Two visual systems sit on one command.

- `--help` and Typer usage errors render Rich boxes (argument panel, option panel, `┌─ Error ─` panel). That is a clear focal point for bad argv.
- A successful run is eight `typer.echo` lines with the same weight: three checkmarks, then `key: value` (`cli.py` 27–31, 79–83). There is no heading, rule, or blank line between progress and the ids the operator must copy.
- A mid-pipeline failure leaves only the earlier checkmarks on stdout (`tests/unit/test_cli_ingest_contract.py` asserts stdout `["✓ transcript"]` and JSON on stderr). The failed stage has no mark on the stream the operator is watching. Metadata and consistency never get a mark by design (`ingest_pipeline.py` 52–67), so a consistency failure looks identical on stdout to a metadata failure: one `✓ transcript` and then silence on stdout.
- No icon-only control lacks a label. The CLI has no icon buttons. The checkmark strings include the stage name (`✓ transcript`, `✓ LLM`, `✓ saved`).

### Pillar 3: Color (3/4)

**WARNING.** Product states are monochrome.

- `cli.py` has no Rich markup, no `typer.style`, no `secho`, and no hex/rgb literals. Accent is not sprayed across the success path. That matches a golden stdout contract that tests compare with `splitlines()` (`tests/unit/test_cli_ingest_contract.py` 83).
- Rich’s default theme colors the help and usage-error panels when stderr is a TTY. Checkmarks, id lines, and `IngestError` JSON stay on the default foreground (`typer.echo` at `cli.py` 46 and 76). Merged terminals give success and failure the same color. There is no 60/30/10 split because this surface is not a page; the gap is status color on the three outcomes the operator must tell apart (in progress, saved, failed).

### Pillar 4: Typography (4/4)

Success stdout is a single plain face and a single weight. The phase does not introduce a second size (`text-xl` style scaling does not apply; there is no web stylesheet in this phase). Hierarchy is lexical: a checkmark prefix versus `key: value`. Rich’s help chrome uses the library’s bold panel titles; that chrome is Typer’s `--help`, not a second product type scale on the success contract. No extra finding drops this pillar.

### Pillar 5: Spacing (3/4)

**WARNING.** The success block is one dense list.

- Eight consecutive `typer.echo` calls (`cli.py` 46 via `_on_stage`, then 79–83) produce eight adjacent lines. The three progress lines and the five result lines are not separated, so a long `slug:` line sits directly under `✓ saved`.
- Help output uses Rich’s internal padding and a blank line before `Usage:`. A successful run uses neither. Density is inconsistent across the two states of the same command.
- No arbitrary pixel or rem spacing exists on this surface. The issue is grouping, not a broken scale.

### Pillar 6: Experience Design (2/4)

**WARNING.** Staged success and the D-08 split are real. The long middle of a live run is not.

Covered:

- Staged progress after a stage succeeds: `on_stage("transcript"|"llm"|"saved")` (`ingest_pipeline.py` 49–50, 77–78, 85–86) mapped to the three locked strings (`cli.py` 27–31). A failed stage does not print its own checkmark (tested in `test_cli_mid_pipeline_llm_error_keeps_transcript_checkmark_json_stderr`).
- Empty argv: missing URL and missing `--template` exit 2 before `build_ingest_deps` runs, with the legal template values listed.
- Config and missing-template failures: human stderr, exit 1, no checkmarks (`cli.py` 71–74).
- Re-run is exit 0, not an error (`already_saved: true`). No destructive confirm is required; the RPC does not refresh the row.
- Locked stdout omits secrets, `video_id`, and `provenance_label` (D-11). `Settings` stores key fields with `repr=False` (`composition/settings.py` 55, 59).

Gaps:

- **No in-progress feedback.** `await captions.get` (line 46) and `await article.process` (line 74) finish before any echo. From process start until the first checkmark, and again from `✓ transcript` until `✓ LLM`, the terminal is idle. Those are the slow network stages (YouTube, DeepSeek). Metadata fetch (line 53) and the consistency compare are also silent, which widens the same gap.
- **No failure glyph on stdout.** The operator’s cue that work stopped is a missing later checkmark plus a JSON line on stderr.
- **No catch-all.** `cli.py` 71–77 handles `ConfigurationError`, `TemplateLoadError`, and `IngestError` only. Any other exception leaves Typer’s traceback on the terminal.
- **No shell completion** (`app = typer.Typer(add_completion=False)`, `cli.py` 25). Minor next to the silent-wait gap.
- **No disabled/loading control model** applies; this is a one-shot process, not a form.

#### Observed web UI (not scored)

UAT confirmed drafts on the existing reader and recorded six admin gaps as Phase 11 follow-ups (`10-UAT.md` Follow-ups; `10-04-SUMMARY.md`). This phase was not allowed to change that UI, so those items do not move the scores:

1. Admin email preview shows title and dek only, so D-16 body, provenance, and headings were checked on `/materials/<slug>` instead.
2. «Превью письма» lists titles only.
3. Seed string `test-header` appears in the preview.
4. Interstitial text drops blank lines (`\n\n`).
5. No control to move `draft` → `ready`; UAT used SQL.
6. «Обоснование недоступно» because ingestion does not fill `score_factors`.

---

## Files Audited

- `.planning/phases/10-cli-composition-uat/10-CONTEXT.md`
- `.planning/phases/10-cli-composition-uat/10-01-PLAN.md`
- `.planning/phases/10-cli-composition-uat/10-01-SUMMARY.md`
- `.planning/phases/10-cli-composition-uat/10-02-PLAN.md`
- `.planning/phases/10-cli-composition-uat/10-02-SUMMARY.md`
- `.planning/phases/10-cli-composition-uat/10-03-PLAN.md`
- `.planning/phases/10-cli-composition-uat/10-03-SUMMARY.md`
- `.planning/phases/10-cli-composition-uat/10-04-PLAN.md`
- `.planning/phases/10-cli-composition-uat/10-04-SUMMARY.md`
- `.planning/phases/10-cli-composition-uat/10-05-PLAN.md`
- `.planning/phases/10-cli-composition-uat/10-05-SUMMARY.md`
- `.planning/phases/10-cli-composition-uat/10-UAT.md`
- `ingestion-service/src/ingestion_service/cli.py`
- `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py`
- `ingestion-service/src/ingestion_service/domain/errors.py`
- `ingestion-service/src/ingestion_service/composition/config_error.py`
- `ingestion-service/src/ingestion_service/composition/settings.py`
- `ingestion-service/src/ingestion_service/composition/clients.py`
- `ingestion-service/src/ingestion_service/mapping/article.py`
- `ingestion-service/src/ingestion_service/mapping/captions.py`
- `ingestion-service/src/ingestion_service/mapping/url.py`
- `data-collection/src/data_collection/templates/__init__.py`
- `tests/unit/test_cli_ingest_contract.py`
- Live `ingest --help` and CliRunner usage errors (missing URL, missing `--template`, `--template essay`)
