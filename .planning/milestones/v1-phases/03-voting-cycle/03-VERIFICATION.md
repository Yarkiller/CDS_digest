---
phase: 03-voting-cycle
verified: 2026-09-20T17:00:00Z
status: passed
score: 4/4 must-haves verified
behavior_unverified: 2
overrides_applied: 0
re_verification: false
decision_coverage:
  honored: 17
  total: 17
  not_honored: []
behavior_unverified_items:

  - truth: "UI-SPEC backstops: long titles/deks/status and 3+ tied leaders wrap without overflow; many topic rows scroll without clamp breakage"
    test: "At 320/390/1280, open /voting with long RU titles, a 0-materials topic, and a 3-way leader tie (mock or live)"
    expected: "No horizontal overflow of primary chrome; leader strip and «Ваш голос:» reflow; radios remain usable"
    why_human: "PLAN 03-05/03-06 mark these verification: backstop — presence checks cannot prove layout"

  - truth: "Initial ballot GET pending remains neutral non-flashing until ready/error (no false closed/empty flash)"
    test: "Throttle network; open /voting; observe first paint before snapshot settles"
    expected: "Neutral «Загрузка…» only — no closed banner, no «нет активного», no pre-selected radio"
    why_human: "verification: backstop in 03-05/03-06; timing/flash not greppable"
human_verification:

  - test: "Live FE↔BE ballot smoke (VITE_USE_MOCKS=false, APP_CONTAINER=live)"
    expected: "Authenticated /voting loads seeded topics with audit deks; confirm stores one vote; A→B updates status; closed reject shows «Цикл голосования закрыт»"
    why_human: "Playwright phase gate runs under mocks; shared-VM JWT + live adapters need a human pass"

  - test: "UI-SPEC visual backstops (overflow / long copy / pending flash)"
    expected: "Leader strip, topic rows, and status reflow at 320/390/1280 without clipping or false empty/closed flash"
    why_human: "PLAN backstop truths — visual judgment"

  - test: "Reconfirm live DDL trigger on shared VM"
    expected: "pg_trigger lists votes_enforce_open_and_topic; closed-cycle write rejected at DB as well as app layer"
    why_human: "MCP list_triggers needs POSTGRES_URL this session; seed verified live, DDL only via runbook Applied line"
prohibitions_flagged:

  - statement: "No public leaderboard / XP / gamification (ADR-0001)"
    verification: judgment
    disposition: honored_advisory
    evidence: "No leaderboard routes/UI; tallies only on ballot DTO"

  - statement: "No row «Лидирует» badge / topic.leading"
    verification: judgment
    disposition: honored_advisory
    evidence: "BallotTopic has no leading; Playwright getByText('Лидирует', exact) count 0"

  - statement: "No idle setInterval tally polling (D-55)"
    verification: judgment
    disposition: honored_advisory
    evidence: "No setInterval in VotingPage.jsx / votingApi.js"

  - statement: "No SPA→Supabase Data API vote writes"
    verification: judgment
    disposition: honored_advisory
    evidence: "votingApi live path uses fetch /voting/* only"

  - statement: "No delete+insert A→B — upsert/CAS on PK only"
    verification: judgment
    disposition: honored_advisory
    evidence: "SupabaseVoteRepository.upsert_vote; PK (cycle_id, user_id) in 001 schema"
---

# Phase 3: Voting Cycle Verification Report

**Phase Goal:** Each authenticated user casts and may change exactly one vote in an open cycle with transparent ballot UX  
**Verified:** 2026-09-20T17:00:00Z  
**Status:** human_needed  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Before voting, status is «голос не отдан» with no pre-selected topic; leading topic is separate from personal choice | ✓ VERIFIED | `voteStatusText` returns `голос не отдан`; `applySnapshot` sets `selectedId` only from `personal_vote`; leader via `leaderStripText(leaders[])` + muted strip, not row badge. Playwright: never-voted status + `radio checked:true` count 0; leader strip without exact «Лидирует». Unit: `get_ballot` leaders hide-when-zero / ties |
| 2 | Confirming a vote stores exactly one vote and shows «Ваш голос:» with topic; empty submit is blocked | ✓ VERIFIED | `cast_vote` upserts one row per `(cycle_id, user_id)`; HTTP POST returns snapshot with `personal_vote`. SPA: disabled confirm without selection + «Выберите тему»; status «Ваш голос: {title}». Pytest + Playwright confirm path passed this run |
| 3 | Changing A→B while open updates counters/status; after close, change is rejected with closed-cycle message | ✓ VERIFIED | `test_cast_vote_changes_topic_a_to_b_while_open` + HTTP A→B; Playwright «Голос сохранён» then A→B «Голос изменён». Closed: `VotingCycleClosedError` → 409 `CYCLE_CLOSED` + RU message; SPA flips read-only banner. Playwright closed-race flip passed |
| 4 | Topics show audit-language description and material count (including «0 материалов») | ✓ VERIFIED | `TopicBallot` renders dek when non-empty + `materialCountLabel`/`voteCountLabel`; mock AutoML `materialsCount: 0`. Live MCP: 3 topics with audit `description`; `topic_materials` only for topics 1–2 (AutoML=0). Playwright «0 материалов» + dek passed |

**Score:** 4/4 truths verified (2 present, behavior-unverified — UI-SPEC backstops, not roadmap SCs)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `backend/.../domain/vote.py` | BallotSnapshot DTOs | ✓ VERIFIED | Frozen dataclasses; no `leading` on BallotTopic |
| `backend/.../ports/vote_repository.py` | VoteRepository Protocol | ✓ VERIFIED | Exists, substantive |
| `backend/.../use_cases/get_ballot.py` | Leaders + empty shapes | ✓ VERIFIED | `_compute_leaders`; D-49/D-50 shapes; tests green |
| `backend/.../use_cases/cast_vote.py` | Confirm / A→B / closed / CAS | ✓ VERIFIED | Open write; closed→ballot error; CAS conflict path |
| `backend/.../routes/voting.py` | GET/POST + 503/409 | ✓ VERIFIED | JWT via `get_principal`; `claims.sub` only; wired in `app.py` |
| `supabase-integration/migrations/003_phase3_voting_ballot.sql` | Trigger + topic seed | ✓ VERIFIED | Option-A trigger + ≥3 topics; AutoML 0 materials |
| `supabase-integration/.../vote_repository.py` | Live adapter | ✓ VERIFIED | Upsert/CAS; contract tests; no fastapi imports |
| `backend/.../composition/live.py` | `votes=SupabaseVoteRepository` | ✓ VERIFIED | service_role `admin_client` |
| `web/src/services/votingApi.js` | fetchBallot + submitVote | ✓ VERIFIED | `isMocksEnabled` gate; 409 ballot parse |
| `web/src/pages/VotingPage.jsx` | Honesty UX + toast + errors | ✓ VERIFIED | Leader strip, closed/empty, splash vs ErrorPanel |
| `web/src/components/TopicBallot.jsx` | Rows without Лидирует | ✓ VERIFIED | dek + ruCount meta |
| `web/src/utils/voting.js` | Status/CTA/leader copy | ✓ VERIFIED | VOTE-02/D-40/D-44 |
| `web/src/utils/ruCount.js` | RU plurals | ✓ VERIFIED | Shared with IssuePage/ArchivePage |
| `tests/unit/test_*voting*` | Unit/HTTP contracts | ✓ VERIFIED | get_ballot / cast_vote / http_voting / supabase contract |
| `tests/web-app.spec.js` | Playwright VOTE-01…04 | ✓ VERIFIED | Honesty, strip, A→B, closed, empty harnesses |
| `docs/agents/local-platform-runbook.md` §4c | Apply-once docs | ✓ VERIFIED | Applied 2026-09-20 note |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | ---- | ------ | ------- |
| `POST /voting/votes` | `cast_vote(..., user_id=claims.sub)` | `Depends(get_principal)` | ✓ WIRED | Body has no user_id; ASVS V4 |
| `select_active_voting_cycle` | `get_ballot` / `cast_vote` | import from `get_current_issue` | ✓ WIRED | Prefer open; else latest closed |
| `PersistenceError` | HTTP 503 `voting_unavailable` | `voting.py` except | ✓ WIRED | GET + POST |
| `HTTPException 409` | VotingPage read-only / conflict adopt | `votingApi` parse `detail.ballot` | ✓ WIRED | CYCLE_CLOSED flip; VOTE_CONFLICT banner |
| `VotingPage` | `fetchBallot` / `submitVote` | useEffect + ActionButton | ✓ WIRED | Snapshot apply without mandatory follow-up GET |
| `votingApi` | `GET/POST /voting/*` | Bearer when live | ✓ WIRED | No silent mock fallback after live fail |
| `get_ballot leaders[]` | VotingPage leader strip | DTO only | ✓ WIRED | No React leader math |
| `create_service_role_client` | `SupabaseVoteRepository` | `build_live_container` | ✓ WIRED | live.py line `votes=` |
| `003_phase3_*.sql` | topics + votes trigger | shared VM apply | ⚠️ PARTIAL | Seed confirmed live via MCP; trigger DDL not re-listed this session (POSTGRES_URL) |
| `armFailNextVoteSubmit` | ErrorPanel Retry | `?simulateError=1` | ✓ WIRED | Playwright simulateError path |
| `ruCount.js` | TopicBallot + Issue/Archive | shared import | ✓ WIRED | materialCountLabel extracted |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| VotingPage topics/leaders/status | BallotSnapshot | GET `/voting/current` or mock `votingApi` | Yes (live adapter / mock harness) | ✓ FLOWING |
| TopicBallot materialsCount | `list_topics_with_counts` / mock | Supabase counts or mock.js | Yes; live AutoML=0 confirmed | ✓ FLOWING |
| personal_vote → radios | `applySnapshot` | Server `personal_vote` | Yes; never-voted → null | ✓ FLOWING |
| Confirm POST response | full snapshot | `cast_vote` → `get_ballot` | Yes (D-52 one round-trip) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| A→B + closed + leaders unit | `uv run pytest` named cast_vote/get_ballot/http_voting tests | 10 passed | ✓ PASS |
| Honesty + strip + A→B + closed flip | `npx playwright test … -g "lets a reader\|leader strip\|changes vote\|flips to closed"` | 4 passed | ✓ PASS |
| Live topics seed | Supabase MCP `topics` + `topic_materials` | 3 audit topics; AutoML 0 links | ✓ PASS |
| Live trigger list | MCP `list_triggers` on votes | needs POSTGRES_URL | ? SKIP |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh` | N/A |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| VOTE-01 | 03-01, 03-02, 03-04, 03-05 | One vote; «Ваш голос:»; empty blocked | ✓ SATISFIED | cast_vote + SPA + Playwright/pytest |
| VOTE-02 | 03-01, 03-03, 03-05, 03-06 | Never-voted honesty; leader separate | ✓ SATISFIED | personal_vote null; leader strip; no row badge |
| VOTE-03 | 03-02, 03-03, 03-04, 03-06 | A→B open; closed reject | ✓ SATISFIED | upsert A→B; 409 CYCLE_CLOSED + UI flip |
| VOTE-04 | 03-02, 03-03, 03-06 | Audit dek + «0 материалов» | ✓ SATISFIED | TopicBallot + live AutoML=0 |

**Orphaned requirements:** none — REQUIREMENTS.md maps VOTE-01…04 only to Phase 3; all appear in plan frontmatter.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts. (`honored: 17 / total: 17`, `not_honored: []`)

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/unit/test_cast_vote.py` | VOTE-01, VOTE-03 | yes | 0 | no | Behavioral (tallies/status) | OK |
| `tests/unit/test_http_voting.py` | VOTE-01…03 | yes | 0 | no | Value (401/200/409 codes) | OK |
| `tests/unit/test_get_ballot.py` | VOTE-02…04 | yes | 0 | no | Behavioral (leaders/shapes) | OK |
| `tests/unit/test_supabase_vote_repository_contract.py` | VOTE-01,04 | yes | 0 | no | Value (counts/CAS) | OK |
| `tests/web-app.spec.js` (voting) | VOTE-01…04 | yes | 0 voting | no | Behavioral | OK |

**Disabled tests on requirements:** 0 for Phase 3 voting (Phase 2 UI-SPEC `describe.skip` unrelated)  
**Circular patterns detected:** 0  
**Insufficient assertions:** 0

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No TBD/FIXME/XXX in Phase 3 voting artifacts | — | — |
| Shared VM | — | Trigger presence not re-confirmed via MCP this session | ⚠️ Warning | App-layer closed check still enforces VOTE-03; DB last-line is defense-in-depth |

### Human Verification Required

### 1. Live FE↔BE ballot smoke

**Test:** With `VITE_USE_MOCKS=false` and `APP_CONTAINER=live`, sign in and open `/voting`. Confirm a topic, change A→B, optionally close cycle (or use closed fixture) and attempt change.  
**Expected:** Live topics with audit deks; one vote persisted; status/tallies update; closed path shows «Цикл голосования закрыт».  
**Why human:** Playwright gate uses mocks; JWT + live Supabase path needs operator session.

### 2. UI-SPEC visual backstops

**Test:** Resize to 320/390/1280; long titles, 0-materials row, multi-tie strip; observe initial load under throttle.  
**Expected:** No overflow/clipping; no false closed/empty flash before ready.  
**Why human:** PLAN `verification: backstop` items.

### 3. Reconfirm live DDL trigger

**Test:** Run runbook §4c `pg_trigger` verify SQL (or Studio).  
**Expected:** `votes_enforce_open_and_topic` present.  
**Why human:** This session’s MCP cannot list triggers without `POSTGRES_URL`.

### Gaps Summary

No roadmap success-criteria gaps. Goal is implemented and behaviorally proven under mocks/unit. Remaining items are human gates (live smoke, visual backstops, trigger reconfirm) — not missing features.

### Prohibitions (judgment-tier — advisory)

Flagged for human review per ADR-550 (non-authoritative LLM judgment; not silently green):

- No public leaderboard — honored (advisory)
- No row «Лидирует» — honored (advisory; Playwright exact-text)
- No idle tally polling — honored (advisory)
- No SPA vote writes to Supabase — honored (advisory)
- Upsert/CAS only (no delete+insert) — honored (advisory)

---

_Verified: 2026-09-20T17:00:00Z_  
_Verifier: Claude (gsd-verifier)_
