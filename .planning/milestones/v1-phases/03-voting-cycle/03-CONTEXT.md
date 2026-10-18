# Phase 3: Voting Cycle - Context

**Gathered:** 2026-09-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Each authenticated user casts and may change **exactly one vote** in an open voting cycle via live FastAPI + Supabase (replacing the mock ballot). Transparent ballot UX: honest «голос не отдан» with no radio pre-select for never-voted users; leading topic shown **separately** from personal choice; audit-language topic descriptions and material counts (including «0 материалов»). Closed cycle rejects changes with clear messaging. Scope is VOTE-01…04 only — no public leaderboard (ADR-0001), no admin cycle management, no разбор winner publishing.

</domain>

<decisions>
## Implementation Decisions

### Leader vs ballot (US-11)
- **D-40:** Leading topic appears in a **separate strip above the ballot** («Сейчас лидирует: {title} · N голосов» on muted/callout surface). Topic rows must **not** show a «Лидирует» badge (remove current mock `topic.leading` inline tag). — **Reversibility:** reversible — layout-only.
- **D-41:** Each topic row still shows public tallies («N голосов») in addition to audit-dek + materials count. Leader strip is extra, not a substitute for row tallies.
- **D-42:** On a **tie for most votes**, name all tied leaders: «Сейчас лидируют: A и B · N голосов каждый» (extend copy for 3+ if needed).
- **D-43:** Show the leader strip **only when ≥1 vote exists** in the cycle; hide it when all tallies are zero (no false «лидер»).

### Confirm & change flow (US-10, US-12)
- **D-44:** Primary button label: **«Подтвердить голос»** before first save; after a confirmed vote exists, rename to **«Изменить голос»**.
- **D-45:** On successful save, show a **brief toast** («Голос сохранён» / «Голос изменён», ~3–5s fade) plus status «Ваш голос: {title}».
- **D-46:** After confirm and on reload: **radio mirrors the server vote**. Never-voted users still get **no pre-select** (empty selection until they choose).
- **D-47:** Button is **disabled** while selection equals the confirmed topic (no pointless POST). Empty submit (no selection) remains blocked with «Выберите тему» (VOTE-01).

### Closed / empty `/voting`
- **D-48:** **Closed cycle:** read-only results — banner «Цикл голосования закрыт»; radios disabled; tallies + leader strip (per D-40…43) still visible; show last personal vote if any. Confirm/change button hidden or disabled.
- **D-49:** **Open cycle, zero topics:** empty state «Темы ещё не объявлены» + CTA «К выпуску».
- **D-50:** **No cycle row** (between cycles / unseeded): honest empty «Сейчас нет активного голосования» + «К выпуску» (not fake closed results).
- **D-51:** **Close mid-submit race:** when API rejects as closed, **flip UI to read-only** with closed banner and refresh ballot from server payload/state (not toast-only while staying interactive).

### Live save & counters
- **D-52:** Successful vote **POST returns a full ballot snapshot** (topics + tallies + personal vote + cycle status) so the SPA updates in **one round-trip** — no mandatory follow-up GET after submit. — **Reversibility:** costly — response contract couples write to read DTO.
- **D-53:** Submit **network / 5xx:** keep radio selection; **ErrorPanel + Retry**; vote not applied. Do **not** use full ServiceUnavailable splash for mutation failures.
- **D-54:** **Multi-device / version conflict:** banner with server’s current vote; **adopt server state** into radios/status (per `error_handling.md`).
- **D-55:** Initial ballot **GET failure** → ServiceUnavailable splash (`bad_gateway.png` / Phase 2 pattern). **No idle polling** of tallies while the page sits open — refresh on successful submit response (D-52) or manual reload only.
- **D-56:** Same `VITE_USE_MOCKS` gate as Phases 1–2 for voting services: mocks for Playwright; live FastAPI when false. — **Reversibility:** costly — split flag would fork test matrix.

### Claude's Discretion
- Exact REST paths/DTO field names, vote port vs folding into cycle reader, upsert vs delete+insert for A→B, conflict detection mechanism (etag / updated_at / compare-and-set), seed topics for demo cycle, and whether closed-cycle GET reuses the same ballot endpoint — planner/researcher within Ports & Adapters + TDD.
- Exact Russian pluralization helpers for «N голосов» / «N материалов» if not already shared.
- Whether progress-ratio bar on VotingPage stays as decorative chrome or is driven strictly from cycle opens_at/closes_at.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria, VOTE-01…04
- `.planning/REQUIREMENTS.md` — VOTE-01…04 (REQ-US-10…13)
- `.planning/PROJECT.md` — core value, constraints, ADR-0001 lock
- `CONTEXT.md` — domain language (цикл голосования, разбор, тема)

### Prior phase decisions
- `.planning/phases/01-platform-foundation-auth/01-CONTEXT.md` — D-09 mocks, JWT/API patterns
- `.planning/phases/02-issue-materials-archive/02-CONTEXT.md` — D-20…23 errors/splash; D-32…35 callout → `/voting` stub now replaced by live vote

### Specs & UX
- `docs/digest-cds/acceptance_criteria.md` — US-10…US-13
- `docs/digest-cds/error_handling.md` — §2.4 voting (validation, closed, network, conflict, empty topics)
- `docs/digest-cds/technical_specification.md` — voting system requirements (~§21–26+)
- `docs/digest-cds/user_stories.md` — voting stories if present
- `docs/digest-cds/backlog_UI.md` — C3-02 honest «голос не отдан» / leader vs choice (fixed in prototype; re-enforce in live SPA)

### ADRs
- `docs/adr/0001-public-leaderboard-gamification.md` — public leaderboard deferred; ballot tallies ≠ gamification board

### Schema & architecture
- `supabase-integration/migrations/001_initial_schema.sql` — `voting_cycles`, topics, votes (and related FKs)
- `.cursor/rules/architecture.mdc` — Ports & Adapters; composition root only; no business rules in React
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `.planning/codebase/CONCERNS.md` — mock vote persistence, RLS notes for votes/topics
- `.planning/codebase/CONVENTIONS.md`, `ARCHITECTURE.md`, `STRUCTURE.md`

### Brownfield UI to evolve
- `web/src/pages/VotingPage.jsx`, `web/src/components/TopicBallot.jsx`, `web/src/services/votingApi.js`, `web/src/utils/voting.js`
- `backend/src/backend/application/ports/voting_cycle_reader.py`, `backend/src/backend/domain/voting_cycle.py`
- `supabase-integration/src/supabase_integration/voting_cycle_repository.py`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `VotingPage` + `TopicBallot` + `ActionButton` + `voteStatusText` / `voteButtonLabel` — evolve to live DTO; remove row-level «Лидирует»
- `votingApi.js` fail-once harness (`armFailNextVoteSubmit`, `?simulateError=1`) — keep for Playwright offline path under mocks
- Phase 2 `ServiceUnavailable`, `ErrorPanel`, content API JWT patterns — reuse for GET splash vs mutation Retry
- `VotingCycleReader` port + Supabase adapter stub from Phase 2 — extend or add `VoteRepository` / cast-vote use-case
- EditorialCallout already links «Выбрать тему →» → `/voting` (D-35)

### Established Patterns
- UI consumes DTOs only; one-vote / open-closed rules live in application use-cases, not React
- `VITE_USE_MOCKS` for offline Playwright; live composition uses `service_role` adapters server-side only
- TDD: pytest for ports/HTTP; Playwright for ballot honesty + change-while-open + closed reject

### Integration Points
- Route `/voting` (already in AppShell); wire `votingApi` to FastAPI ballot GET + vote POST
- Seed: ensure open cycle + ≥2 topics with audit descriptions and material counts (incl. a 0-materials topic if possible)
- RLS: own-vote R/W already noted in CONCERNS — backend still preferred path via service_role composition (same as Phase 2 content)

</code_context>

<specifics>
## Specific Ideas

- Status copy for never-voted should read as honest «голос не отдан» (product language); current helper uses «Ваш голос: не отдан» — align to VOTE-02 / US-11 wording during implementation.
- Toast pattern can mirror Phase 2 welcome toast (fixed overlay, timed fade) for consistency.
- C3-02 regression: leader must never look like personal choice — strip + no row badge is the locked fix.

</specifics>

<deferred>
## Deferred Ideas

- Public participation leaderboard / gamification — ADR-0001 (past v1)
- Admin create/close voting cycles UI — Phase 5 or later ops
- Real-time / websocket tallies — out of scope (D-55: no idle poll)
- Winner → разбор publishing pipeline — Phase 4/5 territory

None else — discussion stayed within phase scope.

</deferred>

---

*Phase: 3-Voting Cycle*
*Context gathered: 2026-09-20*
