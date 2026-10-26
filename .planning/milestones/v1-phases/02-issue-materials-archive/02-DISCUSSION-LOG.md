# Phase 2: Issue, Materials & Archive - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-19
**Phase:** 2-Issue, Materials & Archive
**Areas discussed:** Live cutover, Current issue + seed, Archive & empty CTAs, Voting callout ISSUE-02, Material honesty

---

## Live cutover for issue/materials

| Option | Description | Selected |
|--------|-------------|----------|
| Same VITE_USE_MOCKS | One flag for auth + content | ✓ |
| Separate content flag | Live auth + mock issue | |
| Always live behind auth | Mocks only in harness | |

**User's choice:** Same `VITE_USE_MOCKS`

| Option | Description | Selected |
|--------|-------------|----------|
| ErrorPanel + Retry | No mock fallback | ✓ |
| Fallback to mock + warning | | |
| Show empty «готовится» on fetch fail | | |

**User's choice:** ErrorPanel + Retry; added `bad_gateway.png` for friendly splash instead of raw 502/stacktraces

| Option | Description | Selected |
|--------|-------------|----------|
| Art on page-level load fails only | Material 404 without art | ✓ |
| Art on all ErrorPanels | | |
| Separate ServiceUnavailable only for 502/503 | | |

**User's choice:** Page-level only + material 404 without picture

| Option | Description | Selected |
|--------|-------------|----------|
| Friendly UI only | Logs keep details | ✓ |
| Friendly + small code NET/502 | | |

**User's choice:** Friendly only

---

## Current issue + seed

| Option | Description | Selected |
|--------|-------------|----------|
| Latest published_at | | ✓ |
| Explicit is_current flag | | |
| Env CURRENT_ISSUE_ID override | | |

**User's choice:** Latest `published_at`

| Option | Description | Selected |
|--------|-------------|----------|
| Checked-in SQL seed | | ✓ |
| Manual Studio only | | |
| Empty DB OK for green | | |

**User's choice:** Idempotent SQL seed from mocks

| Option | Description | Selected |
|--------|-------------|----------|
| Typography-only hero | No cover migration | ✓ |
| Add cover_url migration | | |
| First material cover as hero | | |

**User's choice:** Typography-only

| Option | Description | Selected |
|--------|-------------|----------|
| Current only | | |
| Current + 1 past | | ✓ |
| Full mock.js dump | | |

**User's choice:** Current + 1 past

---

## Archive & empty CTAs

| Option | Description | Selected |
|--------|-------------|----------|
| New /archive + nav | | ✓ |
| Section on issue page only | | |
| Both | | |

**User's choice:** `/archive` + nav; **plus** link back to current from archive

| Option | Description | Selected |
|--------|-------------|----------|
| Same IssuePage at /issues/:id | | ✓ |
| Summary cards only | | |

**User's choice:** Same IssuePage layout

| Option | Description | Selected |
|--------|-------------|----------|
| Empty current→archive; empty archive→/ | | ✓ |
| Both→knowledge | | |
| Current→knowledge; archive→/ | | |

**User's choice:** Cross-link archive ↔ current

| Option | Description | Selected |
|--------|-------------|----------|
| Past only in list | | ✓ |
| All published, mark current | | |

**User's choice:** Past only

---

## Voting callout ISSUE-02

| Option | Description | Selected |
|--------|-------------|----------|
| Honest stub until Phase 3 | | ✓ |
| Live cycle API now | | |
| Hide until Phase 3 | | |

**User's choice:** Honest stub

| Option | Description | Selected |
|--------|-------------|----------|
| On issue API DTO from voting_cycles | | ✓ |
| Frontend env stub | | |
| Tiny read-only endpoint only | | |

**User's choice:** Issue DTO from `voting_cycles`

| Option | Description | Selected |
|--------|-------------|----------|
| Callout only on current / | | ✓ |
| Closed messaging on past | | |

**User's choice:** Current only

| Option | Description | Selected |
|--------|-------------|----------|
| Open CTA → /voting (mock OK) | | ✓ |
| No CTA until live vote API | | |

**User's choice:** Keep CTA to `/voting`

---

## Material honesty

| Option | Description | Selected |
|--------|-------------|----------|
| Hide empty dek | | ✓ |
| Neutral fallback sentence | | |

**User's choice:** Hide

| Option | Description | Selected |
|--------|-------------|----------|
| Omit empty tags/relations; never invent | | ✓ |
| Always show «пока нет» headers | | |

**User's choice:** Omit empty; never invent

| Option | Description | Selected |
|--------|-------------|----------|
| SPA markdown → HTML + TOC | | ✓ |
| Backend pre-rendered HTML | | |

**User's choice:** SPA markdown

| Option | Description | Selected |
|--------|-------------|----------|
| Soft editorial 404 + back nav | | ✓ |
| Silent redirect to current | | |

**User's choice:** Editorial 404; **tone must be clear and not harsh**

---

## Claude's Discretion

- Route param shape, markdown library, seed path layout, ErrorPanel component structure

## Deferred Ideas

- Vote cast/change — Phase 3
- Admin publish — Phase 5
- Issue cover_url migration — later
- Separate content mocks flag — rejected
