---
phase: 12-admin-shortlist-empty-batch-contract
reviewed: 2026-10-04T16:35:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - tests/unit/test_http_admin.py
  - backend/src/backend/application/use_cases/get_admin_shortlist.py
  - backend/src/backend/interface/http/routes/admin.py
  - web/src/services/adminApi.js
  - tests/admin.spec.js
  - web/src/pages/AdminDigestPage.jsx
findings:
  critical: 0
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-10-04T16:35:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Re-run of the Phase 12 `code_review_gate` against the CURRENT working tree (the prior 2026-10-02 REVIEW.md is superseded by this file). The six reviewed files now carry Phase 13/14/16 edits, so this pass re-verified the FIX-01 empty-batch contract as it actually is on disk.

Verified green (locally, `uv run pytest`):
- `tests/unit/test_http_admin.py::test_admin_shortlist_no_batches_returns_null_batch_id` — PASS (Shape 1: `batch_id=null`, `week_label=null`, `items=[]`, `sent_at=null`, `digest_rest=false`, `days_until_next_batch=null`).
- `tests/unit/test_http_admin.py::test_admin_shortlist_empty_unsent_batch_returns_batch_id` — PASS (Shape 2: `batch_id=7`, `week_label="2026-10-06"`, `items=[]`, `sent_at=null`, `digest_rest=false`).
- Whole `tests/unit/test_http_admin.py` + `tests/unit/test_get_admin_shortlist.py` — 39 passed.

Production path is sound for the two locked empty shapes: `get_admin_shortlist` returns the no-batch null shape when `get_current_batch()` is `None` and no sent latest exists, and the empty-unsent shape when an unsent batch exists with `items=()`. `AdminShortlistResponse`/`AdminShortlistItemResponse` keep `extra="forbid"`, `_to_response` maps every declared field, no security issues (no hardcoded secrets, no dangerous sinks, token only via `Authorization`), and the sanitized Markdown / sandboxed iframe (`sandbox=""`) rendering are intact.

Remaining gap is test/contract strength, not behavior: the Playwright EMPTY_UNSENT case still cannot distinguish Shape 2 from Shape 1, so the FE mock shape can drift without failing. Prior WR-01 / IN-01 / IN-02 all persist in the current source.

## Warnings

### WR-01: EMPTY_UNSENT Playwright never locks D-04 #2 DTO fields

**File:** `tests/admin.spec.js:147-165`
**Issue:** The EMPTY_UNSENT case mirrors the no-batch EMPTY UI asserts (heading «Кандидатов пока нет», «Обновить список», no «пайплайн», no rows, no digest-rest copy) but never asserts the fields that make Shape 2 distinct: `batch_id: 7`, ISO `week_label: '2026-10-06'`, `digest_rest: false`, `items: []`. Per D-13, the empty-unsent `week_label` is only surfaced via `weekDek`, which is gated on `showTriage` (`items.length > 0`, `AdminDigestPage.jsx:266-268, 522`), so those fields are invisible in the DOM. If `emptyUnsentDto()` (`adminApi.js:105-115`) regressed to `emptyDto()` (null `batch_id` / null `week_label`), this test would still pass — the FIX-01 / D-12 FE↔HTTP contract-parity claim would be silently broken. This is the same hole reported on 2026-10-02; it is still open. Confirmed no other JS/Playwright surface asserts `emptyUnsentDto` fields (`grep EMPTY_UNSENT|emptyUnsentDto` finds only the flag wiring and this test).
**Fix:** Assert the distinguishing DTO fields after load, either by probing the mock through the harness or by exposing a test-only peek. For example, add to `adminApi.js` an exported `peekEmptyUnsentDto()` (or extend `__DIGEST_ADMIN_HARNESS__`) and assert it from Playwright:

```js
const dto = await page.evaluate(() => window.__DIGEST_ADMIN_HARNESS__.peekEmptyUnsentDto());
expect(dto.batch_id).toBe(7);
expect(dto.week_label).toBe('2026-10-06');
expect(dto.digest_rest).toBe(false);
expect(dto.items).toEqual([]);
```

Alternatively assert against a shared DTO constant so the mock and the test cannot drift.

## Info

### IN-01: Duplicated required-key assert blocks in the two FIX-01 HTTP proofs

**File:** `tests/unit/test_http_admin.py:282-297` and `329-343`
**Issue:** Both proofs repeat the identical six-key presence loop (`batch_id`, `items`, `week_label`, `sent_at`, `digest_rest`, `days_until_next_batch`) plus value asserts. Copy-paste drift risk is low today but real if the lock's required-key set changes.
**Fix:** Extract tiny helpers, e.g. `_assert_shortlist_required_keys(body)` and `_assert_empty_shape(body, *, batch_id, week_label)`, and share them across both tests plus the future full-items proof.

### IN-02: Near-duplicate Playwright empty vs empty-unsent cases

**File:** `tests/admin.spec.js:127-165`
**Issue:** EMPTY and EMPTY_UNSENT assert identical UI; only the sticky flag differs, so the second case adds no unique signal beyond "the flag is wired" (compounded by WR-01). Keeping both is still worthwhile because they guard flag mutual exclusivity/precedence.
**Fix:** Factor the shared empty-UI expectations into a helper and reserve the EMPTY_UNSENT case for the DTO asserts from WR-01, so the pair proves two distinct things.

### IN-03: Mock `restDto()` diverges from the backend digest_rest shape on `week_label`/`sent_at`

**File:** `web/src/services/adminApi.js:85-92` (mock) vs `backend/src/backend/application/use_cases/get_admin_shortlist.py:20-28` (live)
**Issue:** For the third (carried-forward, G-05-2) shape, the backend returns `week_label = latest.week_start.isoformat()` and `sent_at = latest.sent_at` — verified locally: `week_label='2026-09-15'`, `sent_at=<aware datetime>`, `digest_rest=True`. The FE mock `restDto()` returns `week_label: null` and `sent_at: mockBatch.sent_at` (null on a cold `__DIGEST_ADMIN_DIGEST_REST__` load). The lock file's digest_rest note ("typically null `batch_id` / null `week_label`") matches the mock but not the live use-case, so all three sources disagree for this shape. User-visible impact is currently nil (rest mode hides `week_label` via `showTriage`, and `digest_rest` drives the state), so this is a fidelity/authority inconsistency rather than a defect; the digest_rest shape is explicitly carried forward and not re-opened by Phase 12.
**Fix:** Pick one authoritative digest_rest shape and make all three agree — either have `restDto()` mirror the backend (`week_label` = the sent batch's ISO week, `sent_at` non-null) or drop the fields from the lock's digest_rest description. Add a required-key/value assert for the digest_rest path (currently `test_admin_shortlist_after_send_returns_digest_rest` at `tests/unit/test_http_admin.py:346-388` does not assert `week_label`/`sent_at`) so the choice is locked. Defer if this is intentionally out of Phase 12 scope.

---

_Reviewed: 2026-10-04T16:35:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
