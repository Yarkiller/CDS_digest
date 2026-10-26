# Phase 3: Voting Cycle - Research

**Researched:** 2026-09-20
**Domain:** Authenticated ballot GET/POST (FastAPI + Supabase votes upsert) + honest React ballot UX
**Confidence:** HIGH (in-repo brownfield + locked D-40…56); MEDIUM (supabase-py upsert API, Playwright aria-checked); LOW (webfetch classify-confidence for Postgres INSERT page)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Leader vs ballot (US-11)
- **D-40:** Leading topic appears in a **separate strip above the ballot** («Сейчас лидирует: {title} · N голосов» on muted/callout surface). Topic rows must **not** show a «Лидирует» badge (remove current mock `topic.leading` inline tag). — **Reversibility:** reversible — layout-only.
- **D-41:** Each topic row still shows public tallies («N голосов») in addition to audit-dek + materials count. Leader strip is extra, not a substitute for row tallies.
- **D-42:** On a **tie for most votes**, name all tied leaders: «Сейчас лидируют: A и B · N голосов каждый» (extend copy for 3+ if needed).
- **D-43:** Show the leader strip **only when ≥1 vote exists** in the cycle; hide it when all tallies are zero (no false «лидер»).

### Confirm & change flow (US-10, US-12)
- **D-44:** Primary button label: **«Подтвердить голос»** before first save; after a confirmed vote exists, rename to **«Изменить голос»**.
- **D-45:** On successful save, show a **brief toast** («Голос сохранён» / «Голос изменён», ~3–5s fade) plus status «Ваш голос: {title}».
- **D-46:** After confirm and on reload: **radio mirrors the server vote**. Never-voted users still get **no pre-select** (empty selection until they choose).
- **D-47:** Button is **disabled** while selection equals the confirmed topic (no pointless POST). Empty submit is blocked with «Выберите тему» (VOTE-01).

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

### Deferred Ideas (OUT OF SCOPE)
- Public participation leaderboard / gamification — ADR-0001 (past v1)
- Admin create/close voting cycles UI — Phase 5 or later ops
- Real-time / websocket tallies — out of scope (D-55: no idle poll)
- Winner → разбор publishing pipeline — Phase 4/5 territory

None else — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VOTE-01 | Open cycle: confirm exactly one vote; status «Ваш голос:» + topic; empty submit blocked | PK `(cycle_id, user_id)` + `cast_vote` use-case; client «Выберите тему» before POST; idempotent same-topic 200 |
| VOTE-02 | Never-voted: «голос не отдан»; no radio pre-select; leader separate from choice | GET snapshot `personal_vote: null`; DTO `leaders[]` not row badge; copy change from `voteStatusText` |
| VOTE-03 | A→B while open updates tallies/status; closed rejects with closed message | Upsert same PK; closed → HTTP 409 + snapshot (D-51/D-52) |
| VOTE-04 | Audit-language description + material count including «0 материалов» | `topics.description` + `COUNT(topic_materials)`; hide empty dek block (US-13.2) |
</phase_requirements>

## Summary

Phase 3 replaces the in-memory mock ballot with an authenticated FastAPI ballot snapshot and a single-row vote write against existing Postgres tables. The schema already enforces **one vote per user per cycle** via primary key `(cycle_id, user_id)`. Open/closed must be enforced in the **application use-case** (and a DB trigger for service_role), because current RLS `votes_update_own` does not check cycle status. The SPA already has `/voting`, `TopicBallot`, and a fail-once submit harness; it still keeps confirmed votes in React state only, pre-selects nothing (good), but shows a row-level «Лидирует» badge and status «Ваш голос: не отдан» that D-40/VOTE-02 replace.

**Primary recommendation:** Add a `VoteRepository` port (do **not** fold writes into `VotingCycleReader`). Reuse `select_active_voting_cycle`. Expose `GET /voting/current` and `POST /voting/votes` returning the **same BallotSnapshot DTO**. Persist with composite-PK upsert + `updated_at` compare-and-set. Compute leaders/ties/progress in the use-case. Keep `VITE_USE_MOCKS` via `isMocksEnabled()`. Install **no new packages**.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| One-vote / open-closed / topic∈cycle | API / Backend | Database / Storage | Business rules in use-case; PK + trigger as last line |
| Ballot snapshot (tallies, leaders, personal vote) | API / Backend | — | Architecture forbids tally/leader rules in React |
| JWT gate + corporate email | API / Backend | Browser / Client | Existing `get_principal`; SPA only sends Bearer |
| Radio honesty / toast / ErrorPanel / splash | Browser / Client | — | Presentation of DTO + error codes |
| Mock vs live client | Browser / Client | — | D-56 `VITE_USE_MOCKS` |
| Persist votes / topics / counts | Database / Storage | API / Backend | `votes`, `topics`, `topic_materials` via service_role adapter |
| Public leaderboard / XP | — | — | Deferred ADR-0001 — do not build |

## Project Constraints (from .cursor/rules/)

- **TDD (`tdd.mdc`, `AGENTS.md`):** no production code without a failing test first (pytest for ports/HTTP; Playwright for ballot honesty). Exception: configs/generated with explicit agreement.
- **Ports & Adapters (`architecture.mdc`):** domain/use-case have zero `fastapi`/`supabase`/`httpx`; adapters in `supabase-integration`; wiring only in `composition/`; frontend only via `web/src/services/`; no `Any` on ports; in-memory fake per new port.
- **Python deps (`python-uv.mdc`):** if any package is added, use `uv add` only — **this phase should add none**.
- **Docs (`context7.mdc`):** library APIs verified via Context7 / official docs this session (supabase-py upsert, FastAPI HTTPException, Playwright getByRole).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `0.141.1` (pinned `backend/pyproject.toml`) | HTTP edge, Pydantic DTOs, `HTTPException` | Already the API for `/me`, `/issues`, `/materials` |
| Pydantic v2 (`ConfigDict extra="forbid"`) | via FastAPI | Request/response DTOs | Same as `CurrentIssueResponse` |
| supabase (Python) | `>=2.31.0,<3` (`supabase-integration/pyproject.toml`) | PostgREST table access | Existing adapters; `upsert` already used on `profiles`/`materials` |
| React + Vite | existing `web/` | Ballot UI | Brownfield `VotingPage` |
| Playwright | `^1.62.1` (`package.json`) | E2E mock path | Existing `/voting` tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | `>=8.3.0` (workspace `pyproject.toml`) | Unit/HTTP tests | `uv run pytest` (`testpaths = ["tests/unit"]`) |
| Starlette `status` | via FastAPI | `HTTP_409_CONFLICT`, `HTTP_400_BAD_REQUEST` | Closed cycle + version conflict |
| cryptography / PyJWT | already pinned | Test JWT minting | Copy `tests/unit/test_http_me.py` harness |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI ballot + service_role | Browser PostgREST + user JWT | Rejected: no SELECT policies on `topics`/`voting_cycles`; cycle-open not in RLS; architecture says backend path |
| Delete+insert for A→B | Upsert on PK | Delete+insert races two rows; PK upsert is the schema’s one-vote rule |
| If-Match ETag | `updated_at` CAS | Extra header vs JSON field already on row; SPA already JSON-only |
| New toast library | Existing overlay/timed copy | No new npm dep |

**Installation:** none — reuse pinned workspace packages.

**Version verification:** versions read from `backend/pyproject.toml:6-14`, `supabase-integration/pyproject.toml:6-8`, `package.json:17-18`, root `pyproject.toml:24-31` this session.

## Package Legitimacy Audit

> No new registry packages for this phase.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | N/A |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
  Browser /voting
       |  GET /voting/current   Authorization: Bearer
       |  POST /voting/votes    { topic_id, expected_updated_at }
       v
  FastAPI interface/http/routes/voting.py  (thin)
       |  get_principal (JWT + domain)
       v
  use_cases: get_ballot / cast_vote
       |  select_active_voting_cycle (reuse)
       |  leaders, closed, topic∈cycle here — not in React
       v
  VoteRepository (Protocol)  +  VotingCycleReader (existing list_cycles)
       v
  supabase-integration adapter (service_role client from composition/live.py)
       v
  Postgres: voting_cycles | topics | topic_materials | votes
```

Closed/conflict POST returns **409 + BallotSnapshot inside `detail`** so the UI can apply D-51/D-54 without a second GET.

### Recommended Project Structure

```
backend/src/backend/
  domain/vote.py                  # Vote, BallotSnapshot, BallotTopic, domain errors
  domain/errors.py                # VotingCycleClosedError, VoteConflictError, InvalidVoteError
  application/ports/vote_repository.py
  application/use_cases/get_ballot.py
  application/use_cases/cast_vote.py
  tests_support/in_memory.py      # InMemoryVoteRepository
  interface/http/routes/voting.py
  composition/container.py        # AppContainer.votes
  composition/live.py             # wire SupabaseVoteRepository
supabase-integration/src/supabase_integration/
  vote_repository.py
  __init__.py                     # export adapter
  migrations/003_phase3_voting_ballot.sql  # trigger + tally index + topic seed
web/src/
  services/votingApi.js           # GET+POST, VITE_USE_MOCKS, fail-once
  pages/VotingPage.jsx
  components/TopicBallot.jsx      # dek + counts; no leading badge
  utils/voting.js                 # copy; no leader math
  utils/ruCount.js                # extract materialCountLabel + votes plural
tests/unit/test_cast_vote.py
tests/unit/test_http_voting.py
tests/web-app.spec.js             # update D-40/D-44/VOTE-02 copy
```

### Pattern 1: BallotSnapshot as the only UI contract
**What:** One DTO for GET 200, POST 200, and 409 `detail.ballot`.  
**When to use:** All voting reads/writes (D-52, D-51).  
**Fields (researcher recommendation — discretion):**

```python
# Recommended DTO shape (names are discretion; keep extra=forbid)
# cycle: {id, status, opens_at, closes_at, progress_ratio} | null
# topics: [{id, title, description, materials_count, votes}]
# personal_vote: {topic_id, updated_at} | null
# leaders: [{title, votes}]   # empty if all tallies 0 (D-43)
```

Do **not** send `leading: bool` on topic rows (D-40).

### Pattern 2: Compare-and-set on `votes.updated_at`
**What:** Client echoes `expected_updated_at` from last snapshot (`null` if never voted). Adapter: `UPDATE … WHERE cycle_id AND user_id AND updated_at = expected`; if 0 rows, either INSERT (when expected is null) or `VoteConflictError`.  
**When to use:** D-54. Same-topic repeat is success 200 with snapshot (`error_handling.md` §2.4 idempotent).

### Pattern 3: Cycle status column is the open/closed switch
**What:** Reuse `select_active_voting_cycle` which prefers `status == "open"` (`get_current_issue.py`). Do **not** close votes solely because wall-clock is past `closes_at`.  
**Why:** Seed cycle is `open` with window `2026-04-03`–`2026-04-16` while research date is **2026-09-20**. ISSUE-02 callout uses `status`, not dates. Mixing clocks would close `/voting` while `/` still shows «голосование открыто».

### Anti-Patterns to Avoid
- **Leader math in `TopicBallot`:** violates architecture.mdc and C3-02. Compute `leaders` in `get_ballot`.
- **Folding upsert into `VotingCycleReader`:** that port is read-only `list_cycles()` for ISSUE-02; keep it stable.
- **Browser writes to `votes` with user JWT:** no topic SELECT policy; RLS allows own UPDATE even when cycle is closed (`001_initial_schema.sql:290-293`).
- **ServiceUnavailable on POST 5xx:** D-53 forbids it.
- **Idle setInterval tally poll:** D-55.
- **Native `toBeChecked()` on `role="radio"` buttons:** Playwright documents `toBeChecked` for checkbox/radio **inputs**; TopicBallot uses `<button role="radio">`. Use `getByRole('radio', { checked: true })`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| One vote per cycle | App-level “delete others” | PK `(cycle_id, user_id)` + upsert | Concurrent A+B cannot create two rows |
| Atomic insert-or-update | SELECT then INSERT without handling unique violation | Postgres `ON CONFLICT DO UPDATE` / supabase `upsert(on_conflict=…)` | Official UPSERT semantics |
| JSON 4xx | Custom exception middleware | FastAPI `HTTPException(status_code=409, detail=dict)` | `detail` may be dict |
| Russian plural for материалов | Third copy in TopicBallot | Extract `materialCountLabel` from `IssuePage.jsx` | Already implemented |
| Auth/CORS/JWT | New middleware | `get_principal`, existing CORS POST | Phase 1 |
| Toast library | npm toast kit | Timed `aria-live` like current VotingPage / welcome overlay | D-45 3–5s |

**Key insight:** The hard part is honest UX + closed-cycle races, not inventing a vote store. The table already is the vote store.

## Common Pitfalls

### Pitfall 1: Closed-cycle UPDATE still succeeds at RLS
**What goes wrong:** `votes_update_own` only checks `user_id = auth.uid()`.  
**Why:** schema lines 290–293 have no `voting_cycles.status` predicate. Live composition uses **service_role**, which bypasses RLS entirely.  
**How to avoid:** (1) `cast_vote` raises `VotingCycleClosedError` when selected cycle `status != "open"`. (2) `BEFORE INSERT OR UPDATE` trigger on `votes` rejecting writes unless cycle is `open` **and** `topics.cycle_id = votes.cycle_id`.  
**Warning signs:** pytest missing a closed-cycle case; live POST 200 after operator sets `status='closed'`.

### Pitfall 2: `topic_id` from another cycle
**What goes wrong:** FK only requires the topic row exists, not that it belongs to `votes.cycle_id`.  
**How to avoid:** use-case + trigger `EXISTS (SELECT 1 FROM topics t WHERE t.id = NEW.topic_id AND t.cycle_id = NEW.cycle_id)`.

### Pitfall 3: Playwright tests encode old copy and success label
**What goes wrong:** `tests/web-app.spec.js` expects «Ваш голос: RAG…», button «Голос принят», and does not forbid «Лидирует». D-44/VOTE-02 change all three.  
**How to avoid:** rewrite those tests **first** (TDD). Never-voted: `getByRole('radio', { checked: true })` count 0; status matches `/голос не отдан/i` without requiring «Ваш голос:» prefix.

### Pitfall 4: `votingApi.js` has no live gate today
**What goes wrong:** `submitVote` always delays and returns `{topicId}` — unlike `contentApi.js` which uses `isMocksEnabled()`.  
**How to avoid:** D-56 — same gate; live `fetch` + Bearer like `meApi.js` / `contentApi.js`. Prefer `isMocksEnabled()` from `authEnv.js` (handles `__DIGEST_FORCE_AUTH_GATE__`).

### Pitfall 5: Seed topics missing
**What goes wrong:** Phase 2 seed inserts a cycle only (`002_phase2_issue_seed.sql` voting insert). Zero topics → D-49 empty, VOTE-04 unprovable live.  
**How to avoid:** idempotent `003` seed: ≥2 topics with audit `description`; one with **zero** `topic_materials`; titles aligned with mock (`RAG в корпоративной среде`, etc.) so Playwright names stay stable under mocks.

### Pitfall 6: Progress bar vs April 2026 dates
**What goes wrong:** If progress uses `now` vs `closes_at`, September 2026 shows 100% while `status` is still `open`.  
**How to avoid:** Drive bar from DTO `progress_ratio` computed as 1.0 when `status=="closed"`, else clamp `(now-opens)/(closes-opens)` **or** keep decorative mock ratio under mocks only. Document seed dates as narrative (same as mock.js).

## Code Examples

### Domain errors (map at HTTP edge only)

```python
# backend/src/backend/domain/errors.py — extend existing DomainError tree
class VotingCycleClosedError(DomainError):
    """status != open; UI must flip read-only (D-51)."""

class VoteConflictError(DomainError):
    """updated_at mismatch (D-54)."""

class InvalidVoteError(DomainError):
    """empty topic, unknown topic, or topic not in cycle."""
```

### HTTP 409 with snapshot (FastAPI official: detail may be dict)

```python
# Source: https://fastapi.tiangolo.com/tutorial/handling-errors/
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail={
        "code": "CYCLE_CLOSED",  # or VOTE_CONFLICT
        "message": "Цикл голосования закрыт",
        "ballot": snapshot.model_dump(mode="json"),
    },
)
```

### supabase-py upsert (composite PK)

```python
# Source: supabase-py upsert(on_conflict= columns for UNIQUE)
# [CITED: Context7 /supabase/supabase-py SyncQueryRequestBuilder.upsert]
self._client.table("votes").upsert(
    {
        "cycle_id": cycle_id,
        "user_id": user_id,
        "topic_id": topic_id,
        "updated_at": now_iso,
    },
    on_conflict="cycle_id,user_id",
).execute()
```

Use this for first insert / uncontended change. For D-54 CAS, **prefer** `update(...).eq("updated_at", expected)` and treat 0 rows as conflict (supabase-py upsert has no WHERE on the UPDATE). [ASSUMED: comma-separated `on_conflict` string — Context7 documents the param, not a composite example.]

### Postgres UPSERT semantics

DATA_k7mQp2xR_START
ON CONFLICT DO UPDATE guarantees an atomic INSERT or UPDATE outcome; provided there is no independent error, one of those two outcomes is guaranteed, even under high concurrency. This is also known as UPSERT.
DATA_k7mQp2xR_END

Source: https://www.postgresql.org/docs/current/sql-insert.html

### Playwright never-voted radios

```javascript
// Source: https://playwright.dev/docs/api/class-locator — getByRole checked matches aria-checked
await expect(page.getByRole('radio', { checked: true })).toHaveCount(0)
await expect(page.getByRole('status')).toContainText(/голос не отдан/i)
await expect(page.getByText('Лидирует')).toHaveCount(0)
```

### In-repo schema (quote — do not paraphrase)

`001_initial_schema.sql:29` — `create type voting_cycle_status as enum ('open', 'closed');`

`001_initial_schema.sql:207-214`:

```sql
create table if not exists votes (
  cycle_id bigint not null references voting_cycles (id) on delete cascade,
  user_id uuid not null references profiles (id) on delete cascade,
  topic_id bigint not null references topics (id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (cycle_id, user_id)
);
```

`topics` columns (`192-197`): `id`, `cycle_id`, `name`, `description text not null default ''`.

RLS own votes (`282-293`): `votes_select_own` / `votes_insert_own` / `votes_update_own` with `user_id = auth.uid()` only.

`VotingCycle.status` comment (`voting_cycle.py:12`): `"open" | "closed"`.

`voteStatusText` never-voted return (`voting.js:13`): `'Ваш голос: не отдан'` — **change to honest «голос не отдан»** (CONTEXT specifics).

`TopicBallot` currently interpolates (`TopicBallot.jsx:28-29`): `{topic.materialsCount} материалов` and `{topic.leading ? ' · Лидирует' : ''}`.

## State of the Art

| Old Approach (this repo) | Current Approach (this phase) | When Changed | Impact |
|--------------------------|-------------------------------|--------------|--------|
| Mock `submitVote` + React `confirmedId` | FastAPI snapshot + PK upsert | Phase 3 | Vote survives reload |
| Row badge `topic.leading` | Leader strip DTO `leaders[]` | D-40 | C3-02 honesty |
| Button «Голос принят» | «Изменить голос» after save | D-44 | Tests must change |
| `VotingCycleReader` stub for issue callout | Keep + add `VoteRepository` | Phase 3 | ISSUE-02 stays intact |

**Deprecated/outdated:**
- Treating `CONCERNS.md` “no HTTP layer / no adapters” as current — Phase 1–2 added FastAPI + live adapters; voting write is the remaining gap.
- Public leaderboard as vote UX — ADR-0001 deferred; ballot tallies ≠ gamification board.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | supabase-py `on_conflict="cycle_id,user_id"` is the correct composite syntax | Code Examples | Adapter upsert errors; fallback: two-step update/insert |
| A2 | Table `BEFORE` triggers still run for `service_role` writes | Pitfall 1 | Trigger would not protect live path; use-case remains mandatory either way |
| A3 | Playwright `getByRole('radio', { checked: true })` matches `aria-checked` on `<button role="radio">` | Pitfalls / Playwright | Honesty test false-fail; fall back to `aria-checked="true"` locator |
| A4 | Operator will keep `voting_cycles.status` in sync (not wall-clock) | Pattern 3 | Demo in Sep 2026 looks “open” with April dates — product-consistent with ISSUE-02 |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions (RESOLVED)

1. **Live Playwright against real votes?**  
   - What we know: Phase 1–2 default Playwright uses mocks (`VITE_USE_MOCKS` not false).  
   - What's unclear: whether Phase 3 adds a gated live vote proof.  
   - Recommendation: unit+HTTP pytest for rules; Playwright mock for UX; live proof optional/human like Phase 1 ping.  
   - **RESOLVED:** Phase 3 automated e2e stays mocks-only (`VITE_USE_MOCKS` / `isMocksEnabled`); live vote proof is optional human/runbook, not a plan gate (matches 03-01 SPA / 03-04 e2e gate).

2. **401 mid-vote `sessionStorage` restore** (`error_handling.md` §2.4)  
   - Not locked in D-40…56.  
   - Recommendation: implement if cheap (store `selectedId`); do not block VOTE-01…04.  
   - **RESOLVED:** Optional / non-blocking — do not gate VOTE-01…04 on 401 mid-vote restore; implement only if cheap during SPA error polish (03-04), otherwise defer.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | pytest / uvicorn | ✓ | 3.14.0 (requires ≥3.12) | — |
| uv | `uv run pytest` | ✓ | 0.10.9 | — |
| Node | Playwright / Vite | ✓ | v22.13.0 | — |
| FastAPI app | live ballot | ✓ (dev uvicorn noted on :8000) | factory `create_default_app` | in-memory `APP_CONTAINER=memory` |
| Supabase (live) | seed + adapter | ✓ Phase 2 seed applied (cycle row) | self-hosted | in-memory fake for unit |
| New npm/pypi packages | — | n/a | — | do not install |

Step 2.6: no blocking missing tools. Topics seed is **data**, not a CLI — Wave 0 SQL file.

**Missing dependencies with no fallback:** none  
**Missing dependencies with fallback:** live topics (empty → D-49) until `003` seed applied via MCP/Studio (same as Phase 2 `raw_sql` limitation).

## Validation Architecture

> `.planning/config.json` has no `workflow.nyquist_validation: false` — treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ≥8.3.0 + Playwright ^1.62.1 |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| Quick run command | `uv run pytest tests/unit/test_cast_vote.py tests/unit/test_http_voting.py -x` |
| Full suite command | `uv run pytest` && `npx playwright test --project=web` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VOTE-01 | Confirm stores one vote; empty blocked | unit + e2e | pytest `test_cast_vote` / Playwright confirm | ❌ Wave 0 (HTTP); ⚠️ e2e exists but old copy |
| VOTE-02 | «голос не отдан»; no checked radio; leader strip | e2e | Playwright getByRole radio checked:0 | ❌ Wave 0 |
| VOTE-03 | A→B open; closed 409 | unit | pytest closed + change | ❌ Wave 0 |
| VOTE-04 | dek + «0 материалов» | unit DTO + e2e | pytest snapshot; Playwright text | ❌ Wave 0 |
| D-51/54 | 409 body contains ballot | unit HTTP | `test_http_voting.py` | ❌ Wave 0 |
| D-53/55 | GET splash vs POST ErrorPanel | e2e | extend `?simulateError=1` + GET fail arm | ⚠️ submit fail exists; GET splash missing |

### Sampling Rate
- **Per task commit:** targeted pytest file `-x` or single Playwright test
- **Per wave merge:** `uv run pytest` + `npx playwright test --project=web`
- **Phase gate:** full unit + web Playwright green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_cast_vote.py` — in-memory fake: one row, A→B, closed reject, bad topic, CAS conflict
- [ ] `tests/unit/test_http_voting.py` — JWT 401; GET snapshot; POST 200 snapshot; POST 409 `CYCLE_CLOSED` includes ballot; extra fields 422
- [ ] `tests/unit/test_get_ballot.py` — leaders/ties/hide-when-zero; empty topics; no cycle
- [ ] Playwright: never-voted copy + no «Лидирует» + «Изменить голос» + empty submit «Выберите тему»
- [ ] InMemoryVoteRepository in `tests_support/in_memory.py`
- [ ] Framework install: none

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing Bearer JWT `get_principal` |
| V3 Session Management | yes | Supabase access token; 401 → login (existing RequireAuth) |
| V4 Access Control | yes | `claims.sub` as `user_id` only; never client-supplied user id |
| V5 Input Validation | yes | Pydantic `extra="forbid"`; topic must belong to active cycle |
| V6 Cryptography | no | No new crypto; reuse JWT verify |

### Known Threat Patterns for FastAPI + Postgres votes

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Vote as another user (IDOR) | Elevation | `user_id = claims.sub` in use-case; ignore body user id |
| Vote after close | Tampering | Use-case + DB trigger on `status='open'` |
| Topic from other cycle | Tampering | topic.cycle_id check |
| Duplicate votes | Tampering | PK `(cycle_id, user_id)` |
| Mass assignment | Tampering | `extra="forbid"` on POST body |
| SQL injection | Tampering | Parameterized supabase client |
| service_role in Vite | Information disclosure | Clients only in `composition/live.py` (existing) |
| Public leaderboard / ranking PII | Information disclosure | Out of scope ADR-0001; public **topic** tallies only |
| RLS bypass via service_role | Elevation | Trigger + never expose secret to `VITE_` |

## Discretion recommendations (planner may lock)

1. **REST:** `GET /voting/current`, `POST /voting/votes` with `{ "topic_id": str, "expected_updated_at": str | null }`. Closed GET uses the **same** GET (D-48 is a snapshot state, not a second resource).
2. **Ports:** new `VoteRepository`; do not extend `VotingCycleReader` beyond `list_cycles()`.
3. **Write:** upsert/CAS, not delete+insert.
4. **Conflict:** `updated_at` compare-and-set (not HTTP ETag).
5. **Seed:** three topics matching `web/src/data/mock.js` titles; audit descriptions; one `materials_count=0`.
6. **Pluralization:** extract shared helper from `IssuePage.jsx` `materialCountLabel`; add `голос/голоса/голосов`.
7. **Progress bar:** include `progress_ratio` on cycle DTO; closed → 1; open → clamped time ratio (accept April-date quirk) **or** omit bar when it would mislead.

## Sources

### Primary (HIGH confidence — in-repo Read this session)
- `supabase-integration/migrations/001_initial_schema.sql:29,184-214,253-256,282-293` — enums, tables, RLS
- `supabase-integration/migrations/002_phase2_issue_seed.sql:168-178` — cycle seed only, no topics
- `backend/src/backend/application/use_cases/get_current_issue.py:19-27` — `select_active_voting_cycle`
- `backend/src/backend/composition/live.py:19-46` — service_role wiring
- `web/src/pages/VotingPage.jsx`, `TopicBallot.jsx`, `voting.js`, `votingApi.js`
- `docs/digest-cds/error_handling.md` §2.4; `acceptance_criteria.md` US-10…13
- `docs/digest-cds/technical_specification.md` FR 21–29
- `.cursor/rules/architecture.mdc`, `tdd.mdc`

### Secondary (MEDIUM — Context7)
- `/supabase/supabase-py` — `upsert(..., on_conflict=)`
- `/websites/playwright_dev` — `getByRole` `checked` / aria-checked
- FastAPI handling-errors — `HTTPException` JSON-able `detail` (also WebFetch)

### Tertiary (LOW — classify-confidence webfetch)
- https://www.postgresql.org/docs/current/sql-insert.html — ON CONFLICT UPSERT (authoritative page; seam tagged LOW)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pinned in-repo pyproject/package.json
- Architecture: HIGH — existing ports/composition; schema PK
- Pitfalls: HIGH — RLS gap and mock persistence confirmed by Read; Playwright locator MEDIUM

**Research date:** 2026-09-20  
**Valid until:** 2026-10-20 (stable FastAPI/Postgres; re-check supabase-py if bumping ≥3)
