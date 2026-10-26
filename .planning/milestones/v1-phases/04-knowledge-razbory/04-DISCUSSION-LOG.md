# Phase 4: Knowledge & Razbory - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-20
**Phase:** 4-knowledge-razbory
**Areas discussed:** Search trigger & result cards, Role filter UX, Razbor list & routing, Notebook & metrics on longread

---

## Search trigger & result cards

| Option | Description | Selected |
|--------|-------------|----------|
| Submit / Enter + «Найти» | Explicit search; not every keystroke | ✓ |
| Debounced as you type | Auto-search after pause | |
| You decide | Planner picks | |

**User's choice:** Submit/Enter; live-as-you-type noted as Phase 5+ potential, not now.
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse MaterialListRow plain | No search-specific chrome | |
| Ranked hit + chunk snippet, no score | Editorial list with matched excerpt | ✓ |
| Show relevance score | Numeric/percent chrome | |

**User's choice:** Ranked hit + snippet, no score.
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Neutral empty + hint chips | Placeholder + chips as entry points | ✓ |
| Blank results zone | Quieter, no chips | |
| Seeded recommended materials | Cards without query | |

**User's choice:** Neutral empty + hint chips; chips are **topics**, not roles (roles stay in filters). Seeded rejected (honesty); blank rejected (barrier).
**Notes:** Aligns with error_handling.md §2.5.

| Option | Description | Selected |
|--------|-------------|----------|
| Top N + «Показать ещё» | Page/cursor load more | ✓ |
| Single page top N only | No load-more | |
| You decide | Limit within NFR | |

**User's choice:** Top N + load more.
**Notes:** —

---

## Role filter UX

| Option | Description | Selected |
|--------|-------------|----------|
| Single «Роль» dropdown | Keep mock select | |
| Role chips | Analyst / DS / Все | ✓ |
| Auto from profile + override | Default to app_role | |

**User's choice:** Role chips.
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Role chips only | Drop tag/format/topic | ✓ |
| Role + tag | Keep tag select | |
| Keep all four mock filters | Role + tag/format/topic | |

**User's choice:** Role only for Phase 4.
**Notes:** Tag/format/topic deferred.

| Option | Description | Selected |
|--------|-------------|----------|
| Apply on next Submit/Enter | Chip waits for search | |
| Immediate re-search if query active | Chip re-runs search now | ✓ |
| You decide | — | |

**User's choice:** Immediate re-search when query non-empty.
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Full reset clears role + query | «Сбросить фильтры» | |
| Clear role, keep query | «Сбросить фильтр» | ✓ |
| You decide | Within KNOW-04 | |

**User's choice:** Clear role only; keep query text; never substitute ML tops.
**Notes:** Matches KNOW-02 clearing semantics.

---

## Razbor list & routing

| Option | Description | Selected |
|--------|-------------|----------|
| `/razbory` + `/razbory/:id` | Plural collection + nested id | ✓ |
| `/razbory` + `/razbor/:id` | Singular detail | |
| You decide | Any clear list+detail | |

**User's choice:** `/razbory` + `/razbory/:id`, nav «Разборы».
**Notes:** Plural for collections (like `/issues`, `/materials`); singular for section hubs (`/archive`, `/voting`, `/knowledge`).

| Option | Description | Selected |
|--------|-------------|----------|
| Chronology list | design-frontend chronology-item | ✓ |
| Material-style rows | MaterialListRow covers | |
| You decide | Within RAZB-01 | |

**User's choice:** Chronology list.
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| List + stub detail for announcements | «Анонс»; no fake longread | ✓ |
| List-only / disabled link | No detail until published | |
| Hide until published | Published-only list | |

**User's choice:** List + stub detail.
**Notes:** Per error_handling.md.

| Option | Description | Selected |
|--------|-------------|----------|
| Empty → «К голосованию» only | → `/voting` | ✓ |
| Dual CTAs (+ «К выпуску») | Voting + issue | |
| You decide | Within RAZB-01 | |

**User's choice:** Voting CTA only.
**Notes:** —

---

## Notebook & metrics on longread

| Option | Description | Selected |
|--------|-------------|----------|
| Download only | «Скачать .ipynb» | ✓ |
| Download + Open | Second viewer control | |
| You decide | Within RAZB-03 | |

**User's choice:** Download only.
**Notes:** Matches design-frontend.

| Option | Description | Selected |
|--------|-------------|----------|
| Top strip + end CTA | Design pattern | ✓ |
| Top strip only | Single control | |
| Beside sticky TOC only | Sidebar | |

**User's choice:** Top + end.
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Disabled + «Notebook скоро будет» | Keep strip | ✓ |
| Hide strip when missing | Less clutter | |
| Disabled, no caption | Aria only | |

**User's choice:** Disabled + caption; strip stays.
**Notes:** error_handling.md §2.6.

| Option | Description | Selected |
|--------|-------------|----------|
| Honest split | «Качество»+TOC vs «Обзор» badge; no empty table | ✓ |
| Always «Качество» section | Stub copy if no metrics | |
| You decide | Within RAZB-04 | |

**User's choice:** Honest split; reject empty «метрики не публиковались» section as honesty violation (Phase 2 pattern).
**Notes:** —

---

## Claude's Discretion

- Page size / cursor, live hybrid search SQL vs Python, embedding seed strategy, razbor DTO names, TOC breakpoint sharing, notebook file serving path — not locked by user.

## Deferred Ideas

- Live-as-you-type knowledge search — Phase 5+
- Tag / format / topic knowledge filters — later
- In-app notebook viewer — not Phase 4
- Admin razbor publish — Phase 5
- Quizzes (US-29) — post-v1
