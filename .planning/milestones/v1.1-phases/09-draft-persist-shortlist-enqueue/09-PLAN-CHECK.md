---
status: passed
type: plan-check
phase: 09-draft-persist-shortlist-enqueue
checked: 2026-09-27
mode: standard
iteration: 3 (final re-verify after threat_model fix)
verdict: VERIFICATION PASSED
blockers: 0
warnings: 0
info: 0
---

# Phase 9 Plan Check — Draft Persist & Shortlist Enqueue (final)

**Phase goal:** A successful draft write lands as `status=draft` with required provenance and appears on an unsent shortlist batch (creating a new batch when the current one is full)
**Plans checked:** `09-01-PLAN.md` · `09-02-PLAN.md` · `09-03-PLAN.md` · `09-04-PLAN.md`
**Requirements:** PERS-01, PERS-02
**Do not replan from this file** — this is a revision-gate report.

## VERIFICATION PASSED

The single remaining warning from iteration 2 is closed. No blockers, no warnings. All four plans are cleared for execution.

## Prior warning — CLOSED

**`<threat_model>` XML block (was `## Threat model` markdown heading)** — CLOSED. All four plans now wrap the threat-model content in the canonical `<threat_model>…</threat_model>` XML block with `ASVS L1 · block_on=high` immediately inside:

| Plan | `<threat_model>` | `ASVS L1 · block_on=high` | `</threat_model>` |
|------|-----------------|---------------------------|-------------------|
| 09-01 | L227 | L228 | L245 |
| 09-02 | L242 | L243 | L260 |
| 09-03 | L260 | L261 | L279 |
| 09-04 | L258 | L259 | L277 |

- `rg '^#{1,6}\s*[Tt]hreat\s*[Mm]odel'` returns no matches across all four plans — no residual markdown heading.
- Each block carries a unique STRIDE register (`T-09-01…T-09-04` in 09-01, `T-09-05…T-09-08` in 09-02, `T-09-09…T-09-12` in 09-03, `T-09-13…T-09-16` in 09-04) so `extractThreatRegisterIds` detects them without cross-plan collisions (#4683).
- No `high`-severity row is marked `accept` (09-01: LOW/N/A accept only; 09-02: LOW/N/A accept only; 09-03: HIGH mitigate ×4; 09-04: HIGH mitigate, LOW accept, MEDIUM mitigate ×2).

## Global checks (re-run)

| Check | Result |
|-------|--------|
| `must_haves` in YAML frontmatter (truths/artifacts/key_links/assumptions/prohibitions) | PASS (4/4) |
| `<threat_model>` present, ASVS L1, `block_on=high`, no high-severity `accept` | PASS (4/4) |
| PERS-01 + PERS-02 in every plan `requirements` | PASS (4/4) |
| 09-03 checkpoints are real stop-gates (`checkpoint:decision` with decision/options/resume-signal; `checkpoint:migrate` with `autonomous="false"` + resume-signal); frontmatter `autonomous: false` | PASS |
| 09-02 task 3 does not contradict D-11 (no Python pre-check; idempotency in port stand-in/RPC) | PASS |
| `sent_at` exclusion covered (03 SQL predicate `sent_at IS NULL` + AC; 04 `batch_sent` fixture) | PASS |
| `MaterialDraft` slug/reading_minutes defaults preserve assemble constructability | PASS |
| Scope notes present on all four plans (14-file tracer / 16-file contract / 4-task / 4-task close-out) | PASS |
| Every `tdd="true"` task has a `<fails_when>` verify command (probe consumed: blocker=0, warning=0) | PASS |

## Coverage Summary

| Requirement | Plans | Status |
|-------------|-------|--------|
| PERS-01 | 01, 02, 03, 04 | Covered — `status='draft'` + provenance owned by 03, row completion by 02 |
| PERS-02 | 01, 02, 03, 04 | Covered — enqueue + overflow owned by 03/04; `sent_at` exclusion in AC |
| CAP-02 Phase 7 deferral | 04 | Covered — spy `PersistPort` + failing `TranscriptProvider` |

## Goal-backward (ROADMAP success criteria)

| # | Success criterion | Plan coverage | Status |
|---|-------------------|---------------|--------|
| 1 | `materials` insert `status=draft` + provenance columns | 03 RPC + migration 007 | Covered |
| 2 | Enqueue on current unsent batch, `decision=pending` | 03 RPC | Covered |
| 3 | Full batch (5) creates a new unsent batch | 03 SQL + 04 overflow fake | Covered |
| 4 | Never attach to a batch with `sent_at` set | 03 AC + 04 `batch_sent` fixture | Covered |

*Iteration 1: blockers/warnings resolved · Iteration 2: 1 warning (threat_model markdown heading) · Iteration 3: PASSED · all checks 2026-09-27, mode standard*
