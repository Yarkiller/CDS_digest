---
phase: 20-mail-02-signup-confirmation-mail
reviewed: 2026-10-16T08:50:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - tests/auth.spec.js
  - web/src/services/authApi.js
  - web/src/main.jsx
  - web/src/pages/RegisterPage.jsx
  - docs/agents/local-platform-runbook.md
  - .planning/debug/g-01-3b-signup-mailer.md
findings:
  critical: 1
  warning: 1
  info: 2
  total: 4
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-10-16T08:50:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Phase 20 ships path-(B) honest `CONFIRM_MESSAGE` and a Playwright null-session harness. D-07 copy and letter-claim forbid look correct for the mock path the test exercises. Two defects remain: the new harness arm short-circuits **live** `signUp` (violating D-10 “under VITE_USE_MOCKS”) and can show false “account active” success; path-(A) runbook enablement never requires updating that SPA copy before flipping autoconfirm off.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: `armSignUpWithoutSession` short-circuits live Auth signup

**File:** `web/src/services/authApi.js:129-132`
**Issue:** The one-shot arm clears and `return null` **before** `useLiveAuth()` / `supabase.auth.signUp`. Plan D-10 and SUMMARY describe this as a mock-only null-session harness under `VITE_USE_MOCKS`, but any caller of `window.__DIGEST_AUTH_HARNESS__.armSignUpWithoutSession()` (always exported from `web/src/main.jsx:41-46`, including live builds) can skip GoTrue entirely. `RegisterPage` then treats `!session` as success and shows «Аккаунт активен — войдите.» with no user created — the honesty regression this phase was meant to prevent, via a browser console one-liner.
**Fix:**
```javascript
if (signUpWithoutSession) {
  signUpWithoutSession = false
  if (!useLiveAuth()) {
    return null
  }
  // Live: ignore stale/hostile arms; fall through to real signUp
}
```
Optionally also gate export/assignment of `armSignUpWithoutSession` on `import.meta.env.DEV` / mocks-only, consistent with “Playwright harness” intent.

## Warnings

### WR-01: Path (A) enablement omits SPA copy change before flipping confirm-email ON

**File:** `docs/agents/local-platform-runbook.md:148-159`
**Issue:** §4.1.2 steps 4–6 tell operators to set `GOTRUE_MAILER_AUTOCONFIRM=false` (confirm email ON). Under that mode GoTrue’s successful `signUp` commonly returns `session: null` while the user is **unconfirmed**. The shipped `CONFIRM_MESSAGE` («Аккаунт активен — войдите.») then fires for the real null-session branch and again lies — exactly the MAIL-02 transparency failure, now under path (A). Runbook never lists updating `RegisterPage` / restoring confirm-email copy as a precondition. Dangerous ops guidance relative to D-01 (path A remains the target).
**Fix:** Insert an explicit blocker before step 4, e.g. “Do not flip autoconfirm off until SPA null-session copy no longer claims «Аккаунт активен»; restore confirm-email / letter wording (or feature-flag by `mailer_autoconfirm`) and cover with Playwright.” Cross-link `RegisterPage.jsx` `CONFIRM_MESSAGE`.

## Info

### IN-01: Success copy reused as ErrorPanel “error” chrome

**File:** `web/src/pages/RegisterPage.jsx:60-62` (via `ErrorPanel` `web/src/components/ErrorPanel.jsx:17`)
**Issue:** Non-retryable success uses `ErrorPanel`, whose dismiss control is labeled «Скрыть сообщение об ошибке». Misleading a11y for the honest success path.
**Fix:** Use a neutral status panel for `CONFIRM_MESSAGE`, or pass a success-oriented dismiss `aria-label`.

### IN-02: Post-register test does not lock non-retryable UI

**File:** `tests/auth.spec.js:245-260`
**Issue:** Asserts copy + forbids `/письм/i` + stays on `/register`, but does not assert absence of «Повторить» (the `retryable: false` contract).
**Fix:** Add `await expect(page.getByRole("button", { name: /повторить/i })).toHaveCount(0)`.

---

_Reviewed: 2026-10-16T08:50:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
