# Phase 10: CLI Composition & UAT - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-29
**Phase:** 10-CLI Composition & UAT
**Areas discussed:** Command shape, Terminal output, Re-run signal, UAT set

---

## Command shape

| Option | Description | Selected |
|--------|-------------|----------|
| Positional URL and required `--template lecture\|podcast` | LLM-02 is an explicit choice; templates change the article outline | ✓ |
| Positional URL, `--template` optional, default `lecture` | Silent default | |
| You decide | | |

**User's choice:** Required `--template`.
**Notes:** No default template.

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit `uv run --env-file ingestion-service/.env` | Same pattern as the backend; missing file fails before any video | ✓ |
| Autoload `ingestion-service/.env` from the package, any cwd | CLI reads dotenv itself | |
| You decide | | |

**User's choice:** Explicit `--env-file`. No autoload.

| Option | Description | Selected |
|--------|-------------|----------|
| Console script `ingest` | Short operator name; Typer command in `ingestion-service` | ✓ |
| `python -m ingestion_service` | No script name | |
| You decide | | |

**User's choice:** Console script `ingest`.

| Option | Description | Selected |
|--------|-------------|----------|
| `ingest <url> --template lecture\|podcast` | The script is the one-shot; no subcommand | ✓ |
| `ingest run <url> --template …` | Subcommand left open for later commands | |
| You decide | | |

**User's choice:** No subcommand.

---

## Terminal output

| Option | Description | Selected |
|--------|-------------|----------|
| Human lines on stdout; JSON error on stderr | Checkmarks for the operator; JSON only on failure | ✓ |
| One JSON document for both success and failure | No separate checkmark lines | |
| You decide | | |

**User's choice:** Human stdout, JSON stderr.

| Option | Description | Selected |
|--------|-------------|----------|
| Four `key: value` lines after `✓ saved` | CLI-01 fields are named | ✓ |
| One summary line `material_id=… slug=… batch_id=… rank=…` | Single line | |
| You decide | | |

**User's choice:** Four labeled lines.

| Option | Description | Selected |
|--------|-------------|----------|
| Checkmark as soon as that stage succeeds; JSON on stderr for the failure | Operator sees where the run stopped | ✓ |
| Checkmarks only on full success; empty stdout on failure | | |
| You decide | | |

**User's choice:** Print checkmarks as stages succeed.

| Option | Description | Selected |
|--------|-------------|----------|
| Short human stderr text, non-zero exit, no JSON, no new stage | Config errors are not a pipeline stage | ✓ |
| Same JSON envelope with a new stage such as `config` | Would extend the locked stage set | |
| You decide | | |

**User's choice:** Human message, no new stage.

---

## Re-run signal

| Option | Description | Selected |
|--------|-------------|----------|
| Same three checkmarks and four ids, plus `already_saved: true` | Shows the draft was not rewritten | ✓ |
| Identical to a first success, no extra line | | |
| You decide | | |

**User's choice:** Extra `already_saved` line.
**Notes:** Phase 9 still applies: no Python pre-check, content is not refreshed, pipeline still runs through the RPC.

| Option | Description | Selected |
|--------|-------------|----------|
| Exit 0 | Re-run is a successful no-op | ✓ |
| Non-zero so scripts can tell a re-run from a first save | | |
| You decide | | |

**User's choice:** Exit 0.

| Option | Description | Selected |
|--------|-------------|----------|
| Always, last line `true` or `false` | Same stdout shape for first run and re-run | ✓ |
| Only on re-run | First run omits the line | |
| You decide | | |

**User's choice:** Always print `already_saved`.

| Option | Description | Selected |
|--------|-------------|----------|
| Nothing else | Three checkmarks, four ids, `already_saved` | ✓ |
| Also `video_id` and `provenance_label` | | |
| You decide | | |

**User's choice:** No extra stdout fields.

---

## UAT set

| Option | Description | Selected |
|--------|-------------|----------|
| Manual notes in the phase: URL, template, `material_id`, slug | Live admin UI; Playwright web project uses mocks | ✓ |
| New Playwright test against live `/admin/digest` | | |
| You decide | | |

**User's choice:** Manual notes. No Playwright test.

| Option | Description | Selected |
|--------|-------------|----------|
| 4 videos: lecture ru, lecture en, podcast ru, podcast en | Both templates and both languages | ✓ |
| 3 videos: lecture ru, podcast ru, lecture en | Minimum that still hits CLI-03 | |
| You decide | | |

**User's choice:** Four-video mix.

| Option | Description | Selected |
|--------|-------------|----------|
| At UAT time | Operator picks captioned videos and records URLs | ✓ |
| Lock four URLs now | | |
| You decide | | |

**User's choice:** Choose URLs at UAT time.

| Option | Description | Selected |
|--------|-------------|----------|
| Full checklist: unsent shortlist, `status=draft`, Russian body, translation marker, template headings | Phase 8 left heading and marker checks to this UAT | ✓ |
| Only that the card is visible | | |
| You decide | | |

**User's choice:** Full checklist.

---

## Claude's Discretion

- Wording of pre-video human errors.
- JSON indentation on stderr.
- How the CLI detects `already_saved` and reads the stored slug.
- Typer help text.

## Deferred Ideas

None raised during the discussion. Out-of-scope items already on the roadmap (HTTP API, scheduler, captionless transcription, chunking, content refresh on re-run) stay deferred.
