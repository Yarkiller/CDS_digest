---
status: superseded
type: plan-check
phase: 07-captions-adapter
reason: "Plan-check artifact from /gsd-plan-phase — not an executable plan; real plans are 07-01..07-03"
checked: 2026-09-26
mode: standard
iteration: 3 (final re-verify)
verdict: VERIFICATION PASSED
blockers: 0
warnings: 0
findings_closed: 11 of 11
---

# Phase 7 Plan Check — Captions Adapter (final)

**Phase goal:** Operator can resolve a YouTube URL to captions, or get a loud captions-stage failure with no database side effects.
**Plans checked:** `07-01-PLAN.md` (wave 1, tracer) · `07-02-PLAN.md` (wave 2) · `07-03-PLAN.md` (wave 3)

## VERIFICATION PASSED

All 11 findings raised across the two prior iterations are closed. No blockers, no warnings. The three
plans are cleared for execution.

| Iteration | Raised | Closed |
|-----------|--------|--------|
| 1 | B-1, B-2, W-1 … W-6 (2 blockers, 6 warnings) | 8 / 8 |
| 2 | B-3, W-7, W-8 (1 blocker, 2 warnings) | 3 / 3 |

## Iteration-2 findings — closure evidence

### B-3 — D-14 ROADMAP note ownership vs. the already-committed edit — **CLOSED**

The plan now matches reality: the note exists, is committed, and no task claims to write it.

- `.planning/ROADMAP.md` is **absent** from `07-02` `files_modified` (7 entries, all source/test paths), and its `artifacts` list no longer carries a ROADMAP row.
- The `must_haves` truth now reads "**ALREADY** recorded under Phase 9 in `.planning/ROADMAP.md` (written at plan time) — this plan verifies that note is present and does not write it (D-14)", with a dedicated assumption recording the B-3 resolution.
- Task 1 `<context>` is explicitly verify-only ("Do not append, re-word, or re-add it — a second append would duplicate the requirement"), with three concrete steps: `rg -n "persist\.calls == \[\]" .planning/ROADMAP.md`, `git status --short .planning/ROADMAP.md` produces no output, and quote D-14 in the SUMMARY.
- The unsatisfiable `git diff --stat` insertion criterion is gone, replaced by the clean-worktree assertion. A restore-if-missing fallback preserves the one-way-door safety: "If step 1 finds no match, the roadmap record was lost — stop and restore it before continuing."
- The artifacts table row reads "Phase 9/10 live persist-spy requirement (already in ROADMAP; verified, not re-written)"; task 3's criterion stays verify-only and now says "(pre-existing note)".

Verified against the repo: `.planning/ROADMAP.md` line 99 carries the note under the Phase 9 details
section above `**Plans**: TBD`, and `git status --short .planning/ROADMAP.md` returns no output — so both
of task 1's criteria pass as written today.

### W-7 — stale bare-`PySocks` verification instructions in `07-03` — **CLOSED**

All four touchpoints now agree that `pyproject.toml` declares `requests[socks]` and that `PySocks` is an
extra-supplied transitive:

- `<read_first>`: "confirm `httpx[socks]` and `requests[socks]` from 07-01 — PySocks arrives through the `[socks]` extra, so bare `PySocks` is NOT expected as a declared dependency"
- `<behavior>`: adds "Do not re-introduce bare `PySocks` as a direct dependency: 07-01 deliberately declares `requests[socks]` … PySocks is supplied by the extra (visible in `uv.lock`, not in `pyproject.toml`)"
- `<acceptance_criteria>`: "still declares the httpx socks extra and `requests[socks]`, and that bare `PySocks` was not re-added as a direct dependency"
- `prohibitions`: "Do not re-add youtube-transcript-api / httpx[socks] / requests[socks] (nor bare PySocks, which is intentionally only an extra-supplied transitive)"

The "fix as regression of 07-01" trap is gone — a grep for `PySocks` in `pyproject.toml` is no longer the
expected check, so the W-1 dependency decision cannot be accidentally reverted.

### W-8 — `07-03` T-07-ENVLEAK described the pre-W-5 `rg` pattern — **CLOSED**

The threat register row now carries the narrowed pattern verbatim plus the rationale: "`rg -n
"os\.environ|os\.getenv|proxy\s*=|GenericProxyConfig"` on the adapter returns no match — the pattern
forbids env reads and proxy construction while still allowing a docstring that explains the client may
already carry composition-built proxy configuration (D-17)". Threat model and task-1 criterion are now
identical, so a `/gsd-secure-phase` audit reading the register will grep the same pattern the plan tests.

## Global checks (re-run)

| Check | Result |
|-------|--------|
| CAP-01 + CAP-02 in every plan `requirements` | PASS (3/3) |
| D-01 … D-26 each cited in ≥1 plan | PASS — lowest total is D-07 at 4 citations; heaviest are D-10 (25), D-17 (24), D-13 (20), D-11 (19) |
| `<threat_model>` present, ASVS L1, `block_on=high` | PASS (3/3). No `high` threat carries `accept`; the only `accept` rows are `T-07-SC` at `low` in 07-02 and 07-03 |
| "Artifacts this phase produces" | PASS (3/3), owner columns mutually consistent after the 07-02 ROADMAP-row removal |
| TDD ordering | PASS — every `tdd="true"` task has exactly one matching RED-first bullet (07-01: 2/2, 07-02: 3/3, 07-03: 4/4). The single `tdd="false"` task is 07-01's config/lockfile scaffold under the `tdd.mdc` config exception; 07-02's checkpoint is `gate=document` and writes no code |
| No schema push / supabase migrations | PASS — no `migrations/` path appears in any `files_modified`; the only mentions are prohibitions plus 07-01's assertion that nothing under `supabase-integration/migrations/` changes |
| Scope excludes Phase 8–10 | PASS (`typer`/`openai` prohibited in 07-01 and 07-03; 07-01 asserts both absent from the lockfile diff) |
| CAP-02 live spy deferred (D-14) | PASS — note committed at `.planning/ROADMAP.md:99`, verified (not rewritten) by 07-02 task 1 |
| COVERAGE.md INTEGRATE/OPT-OUT with OPT-OUT reasons | PASS — Surface 1 retains the five rows added for W-2 (`YouTubeRequestFailed`, `VideoUnplayable`, `YouTubeDataUnparsable`, `FailedToCreateConsentCookie`, raw `requests.exceptions.*`); every OPT-OUT carries a reason |
| Wave structure | PASS — waves 1/2/3, `depends_on` chain `[] → 07-01 → 07-01+07-02`, matching ROADMAP's three-wave listing and `0/3` progress row |
| Iteration-1 fixes still intact | PASS — `map_url_error` / `InvalidYouTubeUrl` / `requests[socks]` / the corrected T-07-CTXLEAK pointer all still present in 07-01 |

## Optional notes (cosmetic — do not block execution)

1. **`07-02` task 1, blanket phrasing.** One criterion reads "No planning document is modified by this plan", scoped by the parenthetical to `.planning/ROADMAP.md` and `.planning/REQUIREMENTS.md`. The execute-plan workflow itself normally touches `.planning/STATE.md` and progress bookkeeping at plan completion, so a very literal executor might pause. The parenthetical resolves it; tightening the sentence to name the two files would remove the ambiguity entirely.
2. **`07-02` "nine-subtype" label.** `success_criteria` says "nine-subtype `CaptionsError` taxonomy" while the truth enumerates a base plus eight subtypes — which yields nine types, nine mapper rows and nine D-10 reasons. The mapping is unambiguous; only the noun is loose.
3. **`07-01` estimate unchanged at 34k tokens** after absorbing `InvalidYouTubeUrl`, `map_url_error` and `mapping/__init__.py`. Roughly 30 extra lines of production code plus parametrized rows, so the estimate remains plausible — worth watching at execution rather than re-estimating.
4. **`07-03` remains the heaviest plan** (19 files, 4 tasks) because it absorbed the former wave 4. Comparable to the 07-01 tracer and the Phase 6 `06-01` precedent, but it is the plan most likely to want a mid-execution checkpoint.

## Ready for execution

```
Wave 1  07-01-PLAN.md  tracer: scaffold + extract_video_id/InvalidYouTubeUrl + map_url_error + IngestError + mocked captions happy path
Wave 2  07-02-PLAN.md  CaptionsError taxonomy + SDK/transport mapping + map_captions_error + D-15 fake failures + D-14 verify-only checkpoint
Wave 3  07-03-PLAN.md  VideoMetadataProvider + oEmbed adapter + MetadataError/mapper + FakeVideoMetadataProvider + seven-name barrel + Settings/proxy + runbook/live stubs
```

*Iteration 1: 2 blockers, 6 warnings · Iteration 2: 1 blocker, 2 warnings · Iteration 3: PASSED · all checks 2026-09-26, mode standard*
