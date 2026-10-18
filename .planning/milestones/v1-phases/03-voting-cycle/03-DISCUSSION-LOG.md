# Phase 3: Voting Cycle - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-20
**Phase:** 3-Voting Cycle
**Areas discussed:** Leader vs ballot, Confirm & change flow, Closed / empty `/voting`, Live save & counters

---

## Leader vs ballot

| Option | Description | Selected |
|--------|-------------|----------|
| Separate strip above ballot | «Сейчас лидирует…»; no row «Лидирует» | ✓ |
| Tallies only | No dedicated leader callout | |
| You decide | | |

**User's choice:** Separate strip
**Notes:** Follow-ups — keep per-row «N голосов»; ties name both leaders; strip only when ≥1 vote exists.

| Option | Description | Selected |
|--------|-------------|----------|
| Tallies on every row | Plus leader strip | ✓ |
| Materials + dek only | No per-row vote counts | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Name both on tie | «Сейчас лидируют: A и B · N голосов каждый» | ✓ |
| Neutral tie copy | No names | |
| Hide strip on tie | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Strip when ≥1 vote | Hide at all-zero | ✓ |
| Always while open | Even at 0–0 | |
| Only before user voted | Hide after personal vote | |
| You decide | | |

---

## Confirm & change flow

| Option | Description | Selected |
|--------|-------------|----------|
| Same label always | «Подтвердить голос» forever | |
| Rename after first vote | → «Изменить голос» | ✓ |
| Two-step change dialog | Extra confirm on A→B | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Brief toast | «Голос сохранён» / «Голос изменён» | ✓ |
| Status only | No toast | |
| Inline persistent success | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Mirror server vote on radio | Never-voted: no pre-select | ✓ |
| Clear selection after save | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Disable when selection = confirmed | No pointless POST | ✓ |
| Idempotent re-submit enabled | | |
| You decide | | |

---

## Closed / empty `/voting`

| Option | Description | Selected |
|--------|-------------|----------|
| Read-only results | Banner + disabled radios + tallies | ✓ |
| Soft nudge hide ballot | Closed + «К выпуску» | |
| Hard redirect to `/` | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Empty topics + CTA | «Темы ещё не объявлены» + «К выпуску» | ✓ |
| Chrome only muted | No CTA | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Between-cycles empty | «Сейчас нет активного голосования» + «К выпуску» | ✓ |
| Treat as closed | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Flip to read-only on close race | Banner + refresh server state | ✓ |
| Toast only stay interactive | | |
| You decide | | |

---

## Live save & counters

| Option | Description | Selected |
|--------|-------------|----------|
| Trust POST + re-GET | | |
| Optimistic local ±1 | | |
| POST returns full ballot | Single round-trip | ✓ |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Keep selection + Retry | Mutation fail UX | ✓ |
| Full splash | ServiceUnavailable | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Conflict banner + adopt server | | ✓ |
| Last-write wins silent | | |
| You decide | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Splash on GET fail; no idle poll | | ✓ |
| Splash + light poll | | |
| You decide | | |

---

## Claude's Discretion

API path/DTO naming, vote port shape, conflict mechanism internals, seed topic set, progress-bar data binding, pluralization helpers.

## Deferred Ideas

- Public leaderboard (ADR-0001)
- Admin cycle management UI
- Websocket / idle polling tallies
- Winner → разбор pipeline
