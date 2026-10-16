# Phase 20: MAIL-02 signup confirmation mail - Pattern Map

**Mapped:** 2026-10-16
**Files analyzed:** 7
**Analogs found:** 7 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `web/src/pages/RegisterPage.jsx` | component | request-response | `web/src/pages/RegisterPage.jsx` (in-place) | exact |
| `tests/auth.spec.js` | test | request-response | `tests/auth.spec.js` (harness + register suite) | exact |
| `web/src/services/authApi.js` | service | request-response | `web/src/services/authApi.js` (`armFailNextSignUp`) | exact |
| `web/src/main.jsx` | config | request-response | `web/src/main.jsx` (`__DIGEST_AUTH_HARNESS__`) | exact |
| `docs/agents/local-platform-runbook.md` | config | file-I/O | `docs/agents/local-platform-runbook.md` §4.1 | exact |
| `.planning/debug/g-01-3b-signup-mailer.md` | config | file-I/O | `.planning/debug/resolved/g-01-3-registration-ux.md` | role-match |
| `tests/unit/test_auth_email_domain.py` | test | transform | — (PRESERVE; zero edits) | n/a |

## Pattern Assignments

### `web/src/pages/RegisterPage.jsx` (component, request-response)

**Analog:** `web/src/pages/RegisterPage.jsx` — change only the dishonest constant; keep `!session` → non-retryable ErrorPanel branch.

**Imports pattern** (lines 1–8) — leave unchanged:
```javascript
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import ErrorPanel from '../components/ErrorPanel.jsx'
import { AuthApiError, getSignUpInvocationCount, signUp, updateAuthDisplayName } from '../services/authApi.js'
import { sanitizeReturnUrl } from '../services/authEnv.js'
import { isAllowedCorporateEmail } from '../services/emailDomain.js'
import { MeApiError, updateDisplayName } from '../services/meApi.js'
import { armWelcomeToast } from '../services/welcomeSession.js'
```

**Core copy pattern** (lines 10–12) — replace string only (D-07):
```javascript
const DOMAIN_MESSAGE = 'Вход только с корпоративного домена СВА'
const CONFIRM_MESSAGE =
  'Регистрация принята. Подтвердите email по ссылке из письма, затем войдите.'
```
→ Target: `'Регистрация завершена. Аккаунт активен — войдите.'`

**Core session-branch pattern** (lines 60–62) — do not change control flow:
```javascript
if (!session) {
  setNetworkError({ message: CONFIRM_MESSAGE, retryable: false })
  return
}
```

**Error-panel UX pattern** (lines 92–112) — non-retryable title «Регистрация»; `ErrorPanel` provides `role="alert"`:
```javascript
{networkError ? (
  <div className="flex flex-col gap-2">
    <ErrorPanel
      title={
        networkError.retryable
          ? 'Сервис входа временно недоступен'
          : 'Регистрация'
      }
      message={networkError.message}
      onDismiss={() => setNetworkError(null)}
    />
```

**Do not touch:** `authApi.js` error mapping (D-08); domain gate; happy-path navigate when session present.

---

### `tests/auth.spec.js` (test, request-response)

**Analog:** same file — amend in place (D-09); add regression (D-10); never delete happy-path register tests.

**Imports / describe pattern** (lines 1–2):
```javascript
const { expect, test } = require("@playwright/test");

test.describe("SPA auth contracts", () => {
```

**Harness wait + arm pattern** (lines 230–242) — copy for optional `armSignUpWithoutSession`:
```javascript
test("shows retryable network banner when signUp fails", async ({ page }) => {
  await page.goto("/register");
  await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
  await page.evaluate(() => window.__DIGEST_AUTH_HARNESS__.armFailNextSignUp());

  await page.getByLabel(/^логин$/i).fill("Ник");
  await page.getByLabel(/^email$/i).fill("analyst@sberbank.ru");
  await page.getByLabel(/^пароль$/i).fill("correct-horse");
  await page.getByRole("button", { name: /зарегистрироваться/i }).click();

  await expect(page.getByRole("alert")).toContainText(/сервис входа временно недоступен/i);
  await expect(page.getByRole("button", { name: /повторить/i })).toBeVisible();
  await expect(page).toHaveURL(/\/register/);
});
```

**Negative `not.toContainText` pattern** (lines 117–118) — reuse for D-10 letter-claim forbid:
```javascript
await expect(toast).not.toContainText(/\(employee\)/i);
```

**Autoconfirm happy path to PRESERVE** (lines 165–178) — do not delete under path (B):
```javascript
test("shows Логин as shell identity after register", async ({ page }) => {
  // ... fill + submit ...
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByTestId("shell-identity")).toHaveText("Иван Петров");
});
```

**Recommended D-09/D-10 shape** (from RESEARCH, grounded on harness above):
```javascript
test("post-register copy never claims a confirmation letter", async ({ page }) => {
  await page.goto("/register");
  await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
  await page.evaluate(() => window.__DIGEST_AUTH_HARNESS__.armSignUpWithoutSession());
  // fill Логин + corporate email + password; submit
  await expect(page.getByRole("alert")).toContainText(
    /Регистрация завершена\. Аккаунт активен — войдите/i,
  );
  await expect(page.getByRole("alert")).not.toContainText(/письм/i);
  await expect(page).toHaveURL(/\/register/);
});
```

**TDD order:** add/amend failing assertions first → then change `CONFIRM_MESSAGE`.

---

### `web/src/services/authApi.js` (service, request-response) — optional harness arm

**Analog:** same file — `failNextSignUp` one-shot flag pattern. Only if planner chooses DOM harness for D-10 (Claude's discretion). **Do not** rewrite error mapping (D-08).

**Flag + arm + reset pattern** (lines 16–33):
```javascript
let failNextSignIn = false
let failNextSignUp = false

export function armFailNextSignIn() {
  failNextSignIn = true
}

export function armFailNextSignUp() {
  failNextSignUp = true
}

export function resetAuthHarness() {
  mockSession = null
  signInInvocations = 0
  signUpInvocations = 0
  failNextSignIn = false
  failNextSignUp = false
}
```

**Consume-once in `signUp`** (lines 112–130) — mirror for `withoutSessionNext`:
```javascript
export async function signUp({ email, password, displayName }) {
  signUpInvocations += 1

  if (failNextSignUp) {
    failNextSignUp = false
    throw new AuthApiError('Сервис входа временно недоступен. Проверьте соединение и повторите попытку.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  const trimmedName = (displayName ?? '').trim()

  if (!useLiveAuth()) {
    mockSession = {
      access_token: 'mock-access-token',
      user: { email, user_metadata: { full_name: trimmedName, display_name: trimmedName } },
    }
    return mockSession
  }
  // ...
}
```

**New arm sketch (copy structure, not throw):**
```javascript
let signUpWithoutSessionNext = false

export function armSignUpWithoutSession() {
  signUpWithoutSessionNext = true
}

// inside signUp, after failNextSignUp check / before or instead of mock session return:
if (signUpWithoutSessionNext) {
  signUpWithoutSessionNext = false
  return null  // exercises RegisterPage !session → CONFIRM_MESSAGE
}
// still increment signUpInvocations as today
```

Reset must clear the new flag in `resetAuthHarness`.

---

### `web/src/main.jsx` (config, request-response) — optional harness export

**Analog:** same file — expose new arm on `__DIGEST_AUTH_HARNESS__`.

**Import + window harness pattern** (lines 5–44):
```javascript
import {
  armFailNextSignIn,
  armFailNextSignUp,
  resetAuthHarness,
} from './services/authApi.js'
// ...
window.__DIGEST_AUTH_HARNESS__ = {
  armFailNextSignIn,
  armFailNextSignUp,
  resetAuthHarness,
}
```

Add `armSignUpWithoutSession` to the import list and harness object if the DOM path is chosen.

---

### `docs/agents/local-platform-runbook.md` (config, file-I/O)

**Analog:** same file §4.1 — extend in place (D-13); do not invent a new top-level section unless needed for layout clarity (discretion).

**Existing section anchor** (lines 106–119):
```markdown
### 4.1 Auth mailer / autoconfirm (G-01-3b — required for `/register`)

On `knowledge-db.ru`, GoTrue had `mailer_autoconfirm=false` and a broken SMTP path. ...

**Phase 1 unblock (do this now):** enable autoconfirm ...
...
**SMTP (ops ticket — not Phase 1):** keep a ticket to configure a working mailer. ...
**SPA follow-up (deferred):** map mailer/confirmation failures ...
```

**Extend with (documented only — D-06):**
- Relay **choice** + env **shape**: `GOTRUE_SMTP_*` (GoTrue lane) and `SMTP_*` (Phase 21 digest lane) — placeholders, no secrets
- Smoke procedure: `GET /auth/v1/settings` → `mailer_autoconfirm`; `POST /auth/v1/signup` under confirm-email ON only after relay proven
- One-command rollback (D-05): `GOTRUE_MAILER_AUTOCONFIRM=true` + reload Auth container
- Operator precondition before path (A): signup-edge domain risk (Pitfall 16) — document, do not implement gate here
- Prefer GoTrue README semantics: `GOTRUE_MAILER_AUTOCONFIRM=true` ⇒ autoconfirm **without** sending mail; always trust live settings probe

---

### `.planning/debug/g-01-3b-signup-mailer.md` (config, file-I/O)

**Analog:** `.planning/debug/resolved/g-01-3-registration-ux.md` — close with status + Resolution reference; **do not delete** (D-12).

**Closure frontmatter pattern** (resolved sibling, lines 1–16):
```yaml
---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Self-service /register with Login nickname and slim email+password login shipped; Playwright contracts added (v1 Phase 1)"
trigger: "..."
# ...
audit_acknowledged:
  milestone: v1
  at: 2026-09-22
  status: diagnosed
---
```

**Resolution block pattern** (resolved sibling, lines 100–107):
```markdown
## Resolution

root_cause: "..."
fix: ""
verification: ""
files_changed: []
oracle_type: specified
specialist_hint: react
```

**For g-01-3b:** keep existing diagnosis body (D-14); set `status: resolved` / `audit_acknowledged.status` to closed; fill `fix`/`verification`/`files_changed` with Phase 20 honest-copy + runbook extension references. Optionally move under `.planning/debug/resolved/` to match sibling convention — planner discretion; CONTEXT only requires close-with-reference.

**Current open file header** (lines 1–6) — starting point:
```yaml
---
audit_acknowledged:
  milestone: v1
  at: 2026-09-22
  status: unknown
---
```

---

### `tests/unit/test_auth_email_domain.py` (test, transform) — PRESERVE

**Analog:** n/a — D-11 tripwire: **zero edits**. Run only as regression gate:
`uv run pytest tests/unit/test_auth_email_domain.py -x`

## Shared Patterns

### Playwright auth harness (window global)
**Source:** `web/src/main.jsx` lines 39–44 + `tests/auth.spec.js` lines 230–233  
**Apply to:** D-10 DOM regression if harness arm is chosen
```javascript
await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
await page.evaluate(() => window.__DIGEST_AUTH_HARNESS__.armFailNextSignUp());
```

### One-shot mock arm flags
**Source:** `web/src/services/authApi.js` lines 16–33, 115–120  
**Apply to:** optional `armSignUpWithoutSession` (return `null`, do not throw)

### Non-retryable post-register message via ErrorPanel
**Source:** `RegisterPage.jsx` lines 60–62, 92–101; `ErrorPanel.jsx` `role="alert"`  
**Apply to:** honest (B) copy assertions with `page.getByRole("alert")`

### TDD Red–Green for copy
**Source:** `.cursor/rules/tdd.mdc` / AGENTS.md  
**Apply to:** amend/add Playwright assertions **before** editing `CONFIRM_MESSAGE`

### Architectural fence — no backend Mailer for signup
**Source:** `backend/src/backend/application/ports/mailer.py` (`send_digest` only); CONTEXT criterion 3  
**Apply to:** all plans — never wire signup confirmation through FastAPI `Mailer`

### Operator docs live in runbook, not ADRs (this phase)
**Source:** D-04; `docs/agents/local-platform-runbook.md` §4.1  
**Apply to:** relay shape / smoke / rollback documentation only

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | All touch-list files have in-repo analogs. Optional harness arm is a **variant** of existing `armFailNextSignUp`, not a greenfield pattern. |

## Metadata

**Analog search scope:** `web/src/pages/`, `web/src/services/`, `web/src/main.jsx`, `tests/auth.spec.js`, `tests/web-app.spec.js` (negative asserts), `docs/agents/local-platform-runbook.md`, `.planning/debug/` (+ `resolved/`), `backend/.../ports/mailer.py` (anti-pattern fence)  
**Files scanned:** ~15 tracked sources (git `ls-files` verified for all named analogs)  
**Pattern extraction date:** 2026-10-16  
**Tracked-source gate:** all analog paths confirmed via `git ls-files`
