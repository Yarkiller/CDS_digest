# Phase 14: Draft→ready & justification honesty - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-03
**Phase:** 14-draft-ready-justification-honesty
**Areas discussed:** Draft→ready control placement, What ready means on promote, Justification honesty bar, Empty Обоснование UX

---

## Draft→ready control placement

| Option | Description | Selected |
|--------|-------------|----------|
| Per-row + optional batch | Button on row; batch optional; no auto-ready on Approve | ✓ |
| Auto-ready on Approve | Approve flips ready | |
| Modal-only | Promote only from material preview | |

**User's choice:** Per-row + optional batch; auto-ready rejected (approve ≠ ready).
**Notes:** State vs decision separation is intentional.

### Follow-ups

| Option | Description | Selected |
|--------|-------------|----------|
| Next to draft badge | Visual separation from Approve/Reject | ✓ |
| In Approve/Reject cluster | Mixed with decision actions | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| No confirm | One-click always | |
| Confirm always | Dialog every promote | |
| Confirm only for batch | Per-row one-click | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| ≥1 draft always | Batch whenever any draft | |
| ≥2 drafts | Batch when multiple drafts | |
| Only approved drafts | D-85 blockers only | ✓ |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Optimistic + silent refetch | Match decision UX | ✓ |
| Full reload only | | |
| You decide | | |

**User's choice:** 1a, 2c, 3c, 4a — badge-adjacent; batch confirm only; approved-drafts batch; optimistic + silent refetch.
**Notes:** Flip described as reversible product-wise for skipping per-row confirm; API reverse deferred in Area 2.

---

## What ready means on promote

| Option | Description | Selected |
|--------|-------------|----------|
| Lightweight status flip | No publish_material / published_at / indexing | ✓ |
| Full publish_material | Quality gate + published_at + possible index | |

**User's choice:** Lightweight flip — deciding scope choice; full publish would triple Phase 14.

### Follow-ups

| Option | Description | Selected |
|--------|-------------|----------|
| Shortlist-scoped `/admin/shortlist/items/{id}/ready` | Mirrors decision route | |
| Material-scoped `/admin/materials/{id}/ready` | Status on materials | ✓ |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| No validation | API+UI always allow | |
| Soft warn UI only | Empty body → continue?; API allows | ✓ |
| Same quality as publish | title/body/provenance/format gate | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| draft→ready + already-ready no-op | No reverse this phase | ✓ |
| Full reverse ready→draft | | |
| already-ready → 409 | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Batch `material_ids[]` partial success | | ✓ |
| FE loops per-id endpoint | | |
| You decide | | |

**User's choice:** 1b, 2b, 3a, 4a — material-scoped ready; soft UI warn; idempotent no-op; batch partial success.
**Notes:** Reverse deferred to Phase 15+. FE optimistic UI ≠ FE-loop API.

---

## Justification honesty bar

| Option | Description | Selected |
|--------|-------------|----------|
| Honest-empty only | No PIPE/ingest fill this phase | ✓ |
| Seed/demo fill | Refresh demo score_factors | |
| Ingest stub | Minimal factors without PIPE UI | |

**User's choice:** Honest-empty; seed already exists; PIPE/ingest deferred v1.3+.

### Follow-ups

| Option | Description | Selected |
|--------|-------------|----------|
| Regression only | | |
| + Playwright empty | | |
| + unit matrix | | |
| Regression + Playwright + unit matrix | 0/1/2+/whitespace | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Leave Phase 5 populated UI | | |
| Light polish only if empty-copy forces touch | No redesign | ✓ |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Hard scope wall in CONTEXT | no writers/config/ingest fill | ✓ |
| Soft note | | |
| Allow demo seed refresh | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Silent-fake ban everywhere | FE+BE no defaults | ✓ |
| BE maps real only / FE never invents | (subset) | |
| You decide | | |

**User's choice:** 1d, 2b, 3a, 4a.
**Notes:** Aligns with D-79 and Phase 7–13 unit+E2E+regression pattern.

---

## Empty Обоснование UX

| Option | Description | Selected |
|--------|-------------|----------|
| Clearer copy, no sub-cases | Scoring hasn't run | ✓ |
| Keep old copy only | | |
| Distinguish 0 vs &lt;2 | | |

### Follow-ups

| Option | Description | Selected |
|--------|-------------|----------|
| `Скоринг не запускался` | | |
| `Обоснование недоступно — скоринг не запускался` | Old phrase + reason | ✓ |
| Two-line old + new | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Shortlist row only | Preview has no factors today | ✓ |
| Row + preview modal | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Same muted style | Content state, not error | ✓ |
| Stronger muted warning | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Exact string mocks + Playwright | Phase 13 pattern | ✓ |
| Substring assert | | |
| You decide | | |

**User's choice:** 1b, 2a, 3a, 4a.
**Notes:** Exact string locked for asserts.

---

## Claude's Discretion

- Exact batch route path under `/admin/materials/…`
- Soft-warn empty-body microcopy
- Button label RU micro-variants
- Batch confirm list vs count copy
- Partial-success response field naming (mirror decision batch)

## Deferred Ideas

- Auto-ready on Approve (rejected)
- Full publish_material / published_at / indexing on promote
- ready→draft reverse (Phase 15+)
- PIPE-01 / ingest score_factors writers (Phase 16 / v1.3+)
- Factors in material preview modal
- CLI `--debug` (Phase 15)
- Live SMTP (v1.3)
- Phase 13 backlog reader errors / cursor polish (999.*)
