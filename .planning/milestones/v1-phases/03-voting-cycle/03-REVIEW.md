---
phase: 03-voting-cycle
reviewed: 2026-09-20T19:58:16Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - backend/src/backend/domain/vote.py
  - backend/src/backend/domain/errors.py
  - backend/src/backend/application/ports/vote_repository.py
  - backend/src/backend/application/use_cases/get_ballot.py
  - backend/src/backend/application/use_cases/cast_vote.py
  - backend/src/backend/interface/http/routes/voting.py
  - backend/src/backend/tests_support/in_memory.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/interface/http/app.py
  - supabase-integration/migrations/003_phase3_voting_ballot.sql
  - supabase-integration/src/supabase_integration/vote_repository.py
  - supabase-integration/src/supabase_integration/__init__.py
  - web/src/services/votingApi.js
  - web/src/pages/VotingPage.jsx
  - web/src/components/TopicBallot.jsx
  - web/src/utils/voting.js
  - web/src/utils/ruCount.js
findings:
  critical: 0
  warning: 5
  info: 3
  total: 8
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-09-20T19:58:16Z
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

Phase 03 voting implementation was reviewed against VOTE-01..04 and the focus checklist (JWT `claims.sub`, HTTP status mapping, CAS/upsert, no `VITE_` secrets, no public leaderboard / row «Лидирует» badge).

Core security and product contracts hold: `user_id` comes only from `claims.sub`; `CastVoteRequest` forbids extra fields (including `user_id`); PersistenceError→503 / InvalidVoteError→400 / closed+CAS→409 with ballot; leaders live only in `BallotSnapshot.leaders[]` + strip copy; `TopicBallot` has no row-level leading badge; voting frontend only uses `VITE_API_BASE_URL` (no secret keys).

Five warnings remain around CAS contract drift (InMemory vs live), closed-cycle race mapped as 503, malformed `expected_updated_at` → 500, SPA 400 copy collapsing all `invalid_vote` cases, and relying on PostgREST update row returns for CAS detection.

## Warnings

### WR-01: InMemory same-topic path skips CAS; live adapter does not

**File:** `backend/src/backend/tests_support/in_memory.py:184-188`
**Issue:** `InMemoryVoteRepository.upsert_vote` treats same-topic repeats as success even when `expected_updated_at` is `None` or stale. `SupabaseVoteRepository` always inserts when expected is `None` (unique → `VoteConflictError`) or CAS-updates when expected is set (mismatch → conflict). Unit/HTTP tests that use InMemory can pass CAS edge cases that would 409 in production.
**Fix:** Align InMemory with live CAS rules — require matching `expected_updated_at` for any update (including same-topic), and treat `expected is None` + existing row as conflict:

```python
if existing is None:
    if expected_updated_at is not None:
        raise VoteConflictError(cycle_id, user_id)
else:
    if expected_updated_at is None or existing.updated_at != expected_updated_at:
        raise VoteConflictError(cycle_id, user_id)
# then apply write (same-topic with matching expected remains idempotent 200)
```

### WR-02: DB closed-cycle trigger failures surface as 503, not 409 CYCLE_CLOSED

**File:** `supabase-integration/src/supabase_integration/vote_repository.py:180-189`
**Issue:** Migration `003` trigger raises `votes: cycle % is not open` on INSERT/UPDATE when the cycle closed after the use-case open check. The adapter maps non-unique SDK exceptions to `PersistenceError`, which HTTP maps to **503** `voting_unavailable`. The SPA then shows a retryable ErrorPanel instead of adopting a closed ballot (D-51).
**Fix:** Detect open-cycle / topic-membership trigger failures at the adapter boundary and raise `VotingCycleClosedError` (or a dedicated signal that `cast_vote` converts after attaching a ballot), e.g.:

```python
message = str(exc).lower()
if "is not open" in message or "does not belong to cycle" in message:
    raise VotingCycleClosedError(cycle_id) from exc
if "duplicate" in message or "unique" in message:
    raise VoteConflictError(cycle_id, user_id) from exc
raise PersistenceError(f"votes upsert failed: {exc}") from exc
```

…and have `cast_vote` attach `ballot=` before re-raise (same pattern as existing conflict handling).

### WR-03: Malformed `expected_updated_at` becomes unhandled 500

**File:** `backend/src/backend/application/use_cases/cast_vote.py:41-47`
**Issue:** `datetime.fromisoformat(...)` can raise `ValueError` for garbage strings. That exception is not mapped to `InvalidVoteError`, so FastAPI returns 500 instead of 400 `invalid_vote`.
**Fix:**

```python
else:
    try:
        expected = datetime.fromisoformat(
            str(expected_updated_at).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise InvalidVoteError("expected_updated_at is invalid") from exc
```

### WR-04: SPA maps every HTTP 400 to «Выберите тему»

**File:** `web/src/services/votingApi.js:745-749`
**Issue:** Backend returns a single detail string `invalid_vote` for empty topic, unknown topic, **and** «no active voting cycle». The client always throws `NO_TOPIC` / «Выберите тему», which misleads users (and Playwright assertions) when the cycle disappeared mid-session.
**Fix:** Either expand backend 400 detail to a structured `{code,message}` (preferred) or branch client copy on known codes once available; at minimum avoid claiming «Выберите тему» for non-topic failures:

```javascript
if (response.status === 400) {
  throw new VoteSubmitError('Некорректный голос', {
    code: 'INVALID_VOTE',
    retryable: false,
  })
}
```

### WR-05: CAS conflict detection depends solely on empty `update().execute()` data

**File:** `supabase-integration/src/supabase_integration/vote_repository.py:142-178`
**Issue:** Zero returned rows is treated as `VoteConflictError`. That is correct when Prefer=representation and the CAS predicate matched nothing, but is ambiguous if PostgREST returns no representation (or timestamp equality fails due to `Z` vs `+00:00` / precision). The Z/alt retry helps format drift but still conflates “no matching row” with “update succeeded without body”.
**Fix:** After a zero-row update, `get_vote(cycle_id, user_id)` and compare: missing row or `updated_at != expected` → conflict; matching row with already-desired `topic_id` → treat as idempotent success; otherwise conflict. Optionally set explicit Prefer return=representation on the update call.

## Info

### IN-01: Leader strip hardcodes «голосов» plural

**File:** `web/src/utils/voting.js:14-22`
**Issue:** Strip copy always appends `голосов` even when `votes === 1` (should use `voteCountLabel`).
**Fix:** Reuse `voteCountLabel(votes)` from `ruCount.js` inside `leaderStripText`.

### IN-02: Live ballot cycle omits UI label/period/closesOn fields

**File:** `web/src/pages/VotingPage.jsx:41-48` (consumes `backend/.../voting.py` `BallotCycleResponse`)
**Issue:** Live DTO only exposes `id/status/opens_at/closes_at/progress_ratio`. SPA falls back to generic «Цикл голосования» / «закрытия цикла». Works, but open-cycle copy is weaker than mock harness.
**Fix:** Derive Russian period/`closesOn` from `closes_at` in the SPA (or extend the API DTO intentionally).

### IN-03: Focus checklist items that passed

**Files:** `voting.py:191`, `voting.py:195-222`, `TopicBallot.jsx`, `voting.js:10-22`, `votingApi.js:223-226`, `live.py:22-26`
**Issue:** None — recorded for traceability.
**Fix:** N/A. Confirmed: JWT `claims.sub` only; 503/400/409 mapping on the happy path; no `VITE_` secrets in voting paths; no public leaderboard page; no per-row «Лидирует» badge (leaders only via strip from `leaders[]`).

---

_Reviewed: 2026-09-20T19:58:16Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
