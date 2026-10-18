# Phase 12: Admin shortlist empty-batch contract - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-02
**Phase:** 12-Admin shortlist empty-batch contract
**Areas discussed:** Done bar if already green, Empty-state taxonomy, Contract authority, FIX-01 surface

---

## Done bar if already green

| Option | Description | Selected |
|--------|-------------|----------|
| Verify + close | Re-run named unit; mark FIX-01 done if green | |
| Verify + harden | Green + explicit empty-edge regression coverage | ✓ |
| Treat as still broken | Require broader proof before closing | |

**User's choice:** Verify + harden
**Notes:** Initially also chose “full tests/unit green,” then refined unrelated failures to **scope-bound green**: FIX-01 + edge green; no NEW failures; pre-existing unrelated → SUMMARY deferred. Production: no change unless a failing test forces it (TDD).

---

## Empty-state taxonomy

| Option | Description | Selected |
|--------|-------------|----------|
| Same shape always | Collapse no-batch and empty-unsent | |
| Distinct shapes | null batch_id vs real batch_id + week_label | ✓ |
| You decide | Planner picks least churn | |

**User's choice:** Distinct shapes
**Notes:** Specified HTTP contracts and test names. Keep+rename existing no-batch test; ISO `week_label`; in-memory HTTP unit only (no live adapter).

---

## Contract authority

| Option | Description | Selected |
|--------|-------------|----------|
| Exact JSON equality | `response.json() == {…}` | |
| Required keys + values | Assert critical fields; allow additive declared fields | ✓ |
| Schema-only | 200 + items=[] only | |

**User's choice:** Required keys + values
**Notes:** Keep `extra="forbid"`; phase artifact `12-FIX-01-LOCK.md`; update REQUIREMENTS/ROADMAP FIX-01 proof strings.

---

## FIX-01 surface

| Option | Description | Selected |
|--------|-------------|----------|
| HTTP unit + planning docs only | No FE/Playwright | |
| Also align FE mock | Mocks without Playwright | |
| Unit + mock + Playwright | Full harness alignment | ✓ |

**User's choice:** Unit + mock + Playwright
**Notes:** Both mock shapes, same UI asserts; new `__DIGEST_ADMIN_EMPTY_UNSENT__`; ISO week_label on mock; allow incidental existing week chrome asserts; no new empty-state design.

---

## Claude's Discretion

- Assertion helper / fixture structure in unit tests
- Playwright test naming/structure
- Whether production already satisfies empty-unsent shape without edits (TDD gate)

## Deferred Ideas

- Preview honesty (13), draft→ready (14), CLI --debug (15), PIPE-01 UI (16)
- Live adapter empty-batch test; human RU week_label on API
