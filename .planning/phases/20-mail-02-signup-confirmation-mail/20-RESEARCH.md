# Phase 20: MAIL-02 signup confirmation mail - Research

**Researched:** 2026-10-16
**Domain:** Self-hosted Supabase Auth (GoTrue) mailer config + SPA registration-copy honesty
**Confidence:** HIGH (codebase + locked CONTEXT); MEDIUM (GoTrue/SMTP docs via Context7)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### End state: (A) target, (B) guaranteed fallback
- **D-01:** Path **(A)** — a working confirmation email through the corporate relay — is the target end state. Path **(B)** — explicitly autoconfirmed with honest copy — is the **guaranteed fallback**: if the relay cannot be proven in this session, the phase still passes on (B).
- **D-02:** Because the relay parameters are unavailable now, the phase ships **(B)** in this session. Exactly one honest end state ships (criterion 2). — **Reversibility:** reversible — the flip to (A) is a single env/flag change plus an operator smoke test.

### Relay: choice and configuration shape only
- **D-03:** The relay's parameters (host/port/TLS mode/CA bundle/credentials) are **not available**. The phase records the relay **choice** and the **shape** of the configuration (`GOTRUE_SMTP_*` for the GoTrue lane, `SMTP_*` for the Phase 21 lane) and hands the actual values to the operator.
- **D-04:** No separate ADR is produced for the relay in this phase — the diagnosis artifact plus the runbook section are the recorded outcome. (If a later phase needs a formal ADR for the relay/contour, it can be raised there.)
- **D-05:** The one-command rollback is defined as a **single flag/env revert**: set `GOTRUE_MAILER_AUTOCONFIRM=true` and reload the container config. No database change is involved, so the rollback cannot strand state. — **Reversibility:** reversible — this is the rollback.
- **D-06:** Because relay values are not available, the procedure for *arriving at* (A) — enabling GoTrue SMTP, the smoke test, and the rollback — is **documented only**; no speculative code or half-enabled path is shipped. Phase 21 inherits "relay chosen and proven" as its precondition.

### Honest copy (path B)
- **D-07:** Ship the honest (B) copy **immediately**: «Регистрация завершена. Аккаунт активен — войдите.» — and **remove** the promise of a confirmation letter. This closes the current dishonesty, where the UI claims a letter was sent while `mailer_autoconfirm: true` means none is.
- **D-08:** The copy change lives in **`web/src/pages/RegisterPage.jsx` only** (the single dishonest string). The shared error mapping in `web/src/services/authApi.js` is **not** rewritten in this phase.

### Tests
- **D-09:** `tests/auth.spec.js`'s post-register assertion is **amended** (never deleted) to assert the new honest copy.
- **D-10:** A **new regression** asserts that the post-register copy never claims a confirmation letter was sent — so the dishonesty cannot silently return.
- **D-11:** Tripwire `test_auth_email_domain.py` → **PRESERVE**: the fixed two-domain corporate gate is unchanged.

### Diagnosis artifact
- **D-12:** `.planning/debug/g-01-3b-signup-mailer.md` is **closed** with a reference to the shipped fix.
- **D-13:** A section is added to `docs/agents/local-platform-runbook.md` recording the GoTrue mailer configuration, the smoke test, and the one-command rollback.
- **D-14:** The root cause stays as already diagnosed: self-service `signUp` reaches GoTrue, but Auth fails while sending the confirmation email (`{code:500, error_code:"unexpected_failure", msg:"Error sending confirmation email"}`), surfacing to the SPA as a retryable fetch error; the user row is not persisted. Current state: `mailer_autoconfirm: true`.

### Claude's Discretion
- The exact paragraph layout/wording around the new success copy in `RegisterPage.jsx`, provided it makes no claim that mail was sent.
- How the regression in D-10 is expressed (assertion on the rendered string vs a scan of the copy constant).
- Where in `local-platform-runbook.md` the new section sits.

### Deferred Ideas (OUT OF SCOPE)
### Acknowledged gaps carried forward
- **Relay proof (criterion 4, partial):** the relay choice and config shape are recorded, but the actual smoke-test proof requires operator-supplied parameters. Carried forward as Phase 21's precondition, not silently dropped.
- **SPA error-UX honesty for mailer failures:** the debug session's deferred item — mapping confirmation-mailer failures to honest Russian copy instead of the generic «Сервис входа временно недоступен» (`web/src/services/authApi.js`) — was explicitly **not** taken in this phase (D-08). It belongs with the error-mapping work.
- **Relay/contour ADR:** a formal ADR for the relay and its ADR-0002 contour isolation was declined for this phase (D-04); raise it where the relay actually lands.

### Reviewed Todos (not folded)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MAIL-02 | The signup-confirmation root cause is diagnosed and documented, and the delivered end state is honest — either a working confirmation email through the corporate relay, or an explicitly autoconfirmed flow whose copy never claims that mail was sent | Close `g-01-3b-signup-mailer.md`; ship path **(B)** honest copy in `RegisterPage.jsx`; document GoTrue `GOTRUE_SMTP_*` + `GOTRUE_MAILER_AUTOCONFIRM` shape/smoke/rollback in runbook; never route through backend `Mailer`; PRESERVE `test_auth_email_domain.py`; amend/add Playwright assertions under TDD |
</phase_requirements>

## Summary

Phase 20 is an **honesty + documentation** phase, not a new mailer implementation. Diagnosis is already complete in `.planning/debug/g-01-3b-signup-mailer.md`: with `mailer_autoconfirm: false` and broken SMTP, GoTrue returned `500 unexpected_failure` / `Error sending confirmation email` and did not persist the user; the 2026-09-20 unblock set autoconfirm on. CONTEXT locks **path (B) for this session** because corporate relay parameters are unavailable: keep autoconfirm, replace the dishonest `CONFIRM_MESSAGE` that claims a letter was sent, close the debug file, and extend the runbook with the relay shape, smoke procedure, and one-command rollback for a future flip to (A).

Signup confirmation is owned exclusively by the **GoTrue/Supabase Auth container** (`GOTRUE_SMTP_*`, `GOTRUE_MAILER_AUTOCONFIRM`). The backend `Mailer` port exists only for digest delivery (`send_digest`) and must not be used for signup mail (success criterion 3; architecture rules). Playwright currently forces `VITE_USE_MOCKS=true`, so the happy-path register tests always receive a mock session and never hit the `!session` / `CONFIRM_MESSAGE` branch — plans must add a harness or targeted assertion so D-09/D-10 are RED-before-GREEN under TDD.

**Primary recommendation:** Ship path (B) only — amend `CONFIRM_MESSAGE` to «Регистрация завершена. Аккаунт активен — войдите.», add Playwright coverage that exercises the no-session branch and forbids letter-claim copy, close the debug session, extend runbook §4.1 with documented (not executed) path-(A) SMTP shape + smoke + `GOTRUE_MAILER_AUTOCONFIRM=true` rollback; install no new packages.

## Project Constraints (from AGENTS.md / CLAUDE.md)

No `CLAUDE.md` or `.claude/CLAUDE.md` found in the repo. Actionable directives from `AGENTS.md` and always-applied rules:

- **Mandatory TDD (Red–Green–Refactor):** no production code without a failing test first. Exceptions only for configs/generated/prototypes with explicit agreement. `[VERIFIED: AGENTS.md:13-34]`
- **Git `origin`:** push/pull/fetch and `origin auth` only via WSL (`wsl.exe`), not PowerShell. `[VERIFIED: AGENTS.md:11-12]`
- **Architecture (Ports & Adapters):** Auth identity stays outside FastAPI; SPA uses `web/src/services/`; domain/use-cases must not import Supabase/HTTP SDKs; wiring only in composition. `[VERIFIED: .cursor/rules/architecture.mdc]`
- **Criterion 3 fence:** do not route signup confirmation through backend `Mailer`. `[VERIFIED: 20-CONTEXT.md:11]` quote: `does **not** route signup confirmation through the backend \`Mailer\` port`

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Signup confirmation email send | Database / Storage (GoTrue Auth container on Supabase VM) | — | GoTrue owns token + SMTP for confirmation; SPA only calls `supabase.auth.signUp` |
| Autoconfirm / Confirm-email flag | Database / Storage (GoTrue env) | Operator runbook | `GOTRUE_MAILER_AUTOCONFIRM` / Studio «Confirm email» |
| Corporate SMTP relay (shared) | Database / Storage (GoTrue) + API / Backend (Phase 21 `SMTP_*`) | CDN / Static — | Same relay host; two env namespaces; ADR-0002 contour |
| Dishonest/honest post-register copy | Browser / Client (`RegisterPage.jsx`) | — | Single string; no backend involvement |
| Domain allowlist (ADR-0003) | Browser / Client + API / Backend | — | PRESERVE; out of mail path |
| Digest mail (`Mailer` port) | API / Backend | — | Phase 21 only; anti-feature for MAIL-02 |
| Operator smoke / rollback | Live service config (VM / Docker Auth) | Docs (runbook) | Documented this phase; proof deferred |

## Standard Stack

### Core

| Library / Component | Version | Purpose | Why Standard |
|---------------------|---------|---------|--------------|
| Supabase Auth (GoTrue) | v2.196.0 on prod (debug probe) | Signup + confirmation mailer | Already deployed at `knowledge-db.ru` `[VERIFIED: .planning/debug/g-01-3b-signup-mailer.md:27]` quote: `GET /auth/v1/health`: 200 GoTrue v2.196.0 |
| `@supabase/supabase-js` (via SPA `authApi.js`) | existing project dep | `signUp` / session | Auth stays client→GoTrue; no FastAPI signup route |
| React / Vite SPA (`web/`) | existing | `RegisterPage.jsx` copy | Delivery of honest (B) string |
| Playwright `@playwright/test` | ^1.62.1 (lockfile runtime 1.62.1; registry latest 1.64.1) | E2E auth regressions | Project standard UI suite `[VERIFIED: package.json:17-18]` |
| pytest via `uv` | existing | `test_auth_email_domain.py` tripwire | PRESERVE domain gate |

### Supporting

| Library / Artifact | Version | Purpose | When to Use |
|--------------------|---------|---------|-------------|
| GoTrue env: `GOTRUE_SMTP_*`, `GOTRUE_MAILER_AUTOCONFIRM` | n/a (ops) | Path (A) mail + path (B) autoconfirm | Operator / runbook only this phase `[CITED: github.com/supabase/auth README + example.env via Context7]` |
| Backend `Mailer` Protocol | existing | Digest send | **Phase 21 only** — never for signup `[VERIFIED: backend/src/backend/application/ports/mailer.py:8-18]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| GoTrue SMTP for confirmation | Backend `Mailer` for confirmation | **Rejected** — duplicates GoTrue tokens; violates criterion 3 / architecture |
| Path (A) this session | Path (B) honest autoconfirm | Relay params unavailable (D-02/D-03); (B) is guaranteed fallback |
| New formal relay ADR | Diagnosis + runbook section | Locked by D-04 |

**Installation:** none — no new packages for this phase.

**Version verification:** `npm view @playwright/test version` → `1.64.1` (2026-10-16); project pins `^1.62.1` and runs `1.62.1`. Do not bump Playwright in this phase.

## Package Legitimacy Audit

> No external packages are installed in this phase. Existing `@playwright/test` was legitimacy-checked for completeness.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| *(none new)* | — | — | — | — | — | N/A — no install |
| `@playwright/test` (existing) | npm | established; latest publish 2026-10-14 | ~76M/wk | github.com/microsoft/playwright | SUS (`too-new` on latest publish only) | **Do not install/bump** — keep existing pin; no checkpoint needed for this phase |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** `@playwright/test` latest registry publish flagged `too-new` by the seam; project already depends on it — **no action** this phase.

## Architecture Patterns

### System Architecture Diagram

```text
[Browser RegisterPage]
        |  signUp(email, password, displayName)
        v
[web/src/services/authApi.js] ----publishable key----> [GoTrue /auth/v1/signup]
                                                              |
                    +-----------------------------------------+----------------------------------+
                    | mailer_autoconfirm=true (current / B)   | mailer_autoconfirm=false (future A) |
                    | session returned; no confirmation mail  | GOTRUE_SMTP_* -> corporate relay     |
                    | CONFIRM_MESSAGE only if session==null   | session null until link confirmed   |
                    +-----------------------------------------+----------------------------------+
                                                              |
                                                              X  FORBIDDEN
                                                              v
                                              [backend Mailer.send_digest]  (Phase 21 digest only)

[Operator runbook]
  record GOTRUE_SMTP_* + SMTP_* shape
  smoke: GET /auth/v1/settings + POST /auth/v1/signup
  rollback: GOTRUE_MAILER_AUTOCONFIRM=true + reload Auth container
```

### Recommended Project Structure (touch list)

```text
web/src/pages/RegisterPage.jsx          # CONFIRM_MESSAGE → honest (B) copy (D-07/D-08)
web/src/services/authApi.js             # READ ONLY this phase; optional harness arm for !session (discretion)
web/src/main.jsx                        # expose harness if new arm added
tests/auth.spec.js                      # amend + new regression (D-09/D-10)
tests/unit/test_auth_email_domain.py    # PRESERVE — zero edits (D-11)
.planning/debug/g-01-3b-signup-mailer.md  # CLOSE with fix reference (D-12)
docs/agents/local-platform-runbook.md   # extend §4.1 (D-13)
```

### Pattern 1: Honest end-state copy tied to session shape

**What:** `RegisterPage` shows `CONFIRM_MESSAGE` only when `signUp` returns a falsy session; with autoconfirm + mocks, session is usually present and the UI navigates away.  
**When to use:** Path (B) must still replace the dishonest constant so a live `session === null` response never claims a letter was sent.  
**Example (current dishonest constant — must change):**

```javascript
// Source: web/src/pages/RegisterPage.jsx:11-12 [VERIFIED]
const CONFIRM_MESSAGE =
  'Регистрация принята. Подтвердите email по ссылке из письма, затем войдите.'
```

Target (D-07):

```javascript
const CONFIRM_MESSAGE =
  'Регистрация завершена. Аккаунт активен — войдите.'
```

```javascript
// Source: web/src/pages/RegisterPage.jsx:60-62 [VERIFIED]
if (!session) {
  setNetworkError({ message: CONFIRM_MESSAGE, retryable: false })
  return
}
```

### Pattern 2: Documented GoTrue SMTP shape (ops, not app code)

**What:** Path (A) later sets GoTrue SMTP env and turns autoconfirm off.  
**When to use:** Runbook only this phase (D-06).  
**Example (env shape from GoTrue docs):**

```dotenv
# Source: supabase/auth example.env + README via Context7 [CITED: github.com/supabase/auth]
GOTRUE_SMTP_HOST="<corporate-relay-host>"
GOTRUE_SMTP_PORT="<587-or-ops-chosen>"
GOTRUE_SMTP_USER="<relay-user>"
GOTRUE_SMTP_PASS="<relay-pass>"
GOTRUE_SMTP_ADMIN_EMAIL="<from@corporate-domain>"
GOTRUE_SMTP_SENDER_NAME="Digest CDS"
GOTRUE_MAILER_AUTOCONFIRM="false"   # only after smoke proves relay
# Phase 21 digest lane (separate process/env namespace, same host):
# SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / SMTP_TLS_MODE ...
```

### Pattern 3: TDD for copy + Playwright harness

**What:** Playwright web project forces `VITE_USE_MOCKS: "true"` `[VERIFIED: playwright.config.js:50-54]`, and mock `signUp` always returns a session `[VERIFIED: web/src/services/authApi.js:125-130]`. Therefore the honest-copy string is **not** visible on the existing happy-path tests.  
**When to use:** For D-09/D-10, prefer a small harness arm (discretion) e.g. `armSignUpWithoutSession()` that returns `null` once, then assert the new copy and `not.toContainText(/письм/i)` (or equivalent).  
**Do not** delete `shows Логин as shell identity after register` — under path (B) it remains the autoconfirm happy path (Pitfall 15).

### Anti-Patterns to Avoid

- **Routing confirmation through `Mailer.send_digest`:** architectural anti-feature; duplicates GoTrue. (Reject PITFALLS.md option that suggests this — superseded by CONTEXT criterion 3.)
- **Flipping autoconfirm off without relay proof:** re-introduces signup 500; breaks redirect-based Playwright tests (Pitfall 15).
- **Half-enabled SMTP in repo:** secrets/host speculation in git; D-06 forbids shipping a speculative path.
- **Editing `authApi.js` error mapping:** deferred (D-08).
- **Touching `test_auth_email_domain.py`:** tripwire PRESERVE (D-11).
- **Deleting register tests instead of amending:** tripwire AMEND.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Confirmation tokens / verify links | Custom backend token + mail | GoTrue mailer + `/verify` URL paths | Token lifecycle already in Auth |
| Signup SMTP from FastAPI | New use-case calling `Mailer` | `GOTRUE_SMTP_*` on Auth container | Criterion 3; wrong bounded context |
| Corporate relay SDK | Third-party SMTP client in SPA | GoTrue SMTP (and Phase 21 stdlib `smtplib`) | Contour + secrets stay on VM |
| New test framework | Vitest/Jest for one string | Existing Playwright + optional harness | Project standard; mocks already wired |

**Key insight:** MAIL-02 is configuration honesty + SPA copy reconciliation; inventing a second confirmation pipeline is the most expensive mistake.

## Common Pitfalls

### Pitfall 1: Treating "no mail" as a code bug while autoconfirm is on
**What goes wrong:** Engineers "fix" a mailer that GoTrue intentionally skips.  
**Why it happens:** Symptom matches a defect; remedy was ops autoconfirm.  
**How to avoid:** Record `GET /auth/v1/settings` → `mailer_autoconfirm: true` in the closed debug file; ship (B) copy, not a new sender.  
**Warning signs:** First task is "implement mailer" with no diagnosis close.

### Pitfall 2: Flipping autoconfirm off without relay smoke (Pitfall 15)
**What goes wrong:** Signup 500 returns; Auth user not created; Playwright redirect tests fail.  
**Why it happens:** Happy path assumes session after `signUp`.  
**How to avoid:** This session documents flip only (D-06); rollback = `GOTRUE_MAILER_AUTOCONFIRM=true` + reload (D-05).  
**Warning signs:** Plan changes GoTrue env in CI/app code.

### Pitfall 3: Happy-path Playwright never sees `CONFIRM_MESSAGE`
**What goes wrong:** D-09/D-10 "green" without covering the dishonest branch.  
**Why it happens:** `VITE_USE_MOCKS=true` always returns a session.  
**How to avoid:** Harness arm or constant-level regression that forces the `!session` UI; also negative assert after register that letter-claim text is absent.  
**Warning signs:** Only amending URL/shell-identity tests.

### Pitfall 4: Open signup email abuse when path (A) lands later (Pitfall 16)
**What goes wrong:** With healthy SMTP + autoconfirm off, any address can trigger confirmation mail via direct `POST /auth/v1/signup`; SPA domain gate is bypassable.  
**Why it happens:** ADR-0003 gate is client + post-auth FastAPI, not GoTrue signup edge.  
**How to avoid:** Out of this session's (B) ship; **document as operator precondition** before flipping to (A). Do not weaken `test_auth_email_domain.py`.  
**Warning signs:** Path-(A) runbook with no signup-edge note.

### Pitfall 5: Stale/inverted docs on `GOTRUE_MAILER_AUTOCONFIRM`
**What goes wrong:** Operator reads self-hosting blurb as "enabled = must confirm" and flips the wrong way.  
**Why it happens:** Context7 `/websites/supabase` self-hosting text appears inverted vs GoTrue README/`example.env`.  
**How to avoid:** Prefer `supabase/auth` README: `GOTRUE_MAILER_AUTOCONFIRM=true` → confirm automatically **without** sending mail. Verify with `GET /auth/v1/settings` → `mailer_autoconfirm`.  
**Warning signs:** Runbook wording contradicts a live settings probe.

### Pitfall 6: Vite port 5174 reuse flakes
**What goes wrong:** Mass `ERR_CONNECTION_REFUSED` on Playwright web project.  
**Why it happens:** Stale Vite vs new webServer (STATE.md blocker).  
**How to avoid:** Check listener on 5174 before full suite; kill stale servers.  
**Warning signs:** Failures look like product regressions until error text is read.

## Code Examples

### Current dishonest branch (production)

```javascript
// Source: web/src/pages/RegisterPage.jsx:11-12,60-62 [VERIFIED]
const CONFIRM_MESSAGE =
  'Регистрация принята. Подтвердите email по ссылке из письма, затем войдите.'
// ...
if (!session) {
  setNetworkError({ message: CONFIRM_MESSAGE, retryable: false })
  return
}
```

### Recommended Playwright regression shape (discretion)

```javascript
// Source pattern: playwright.dev locatorAssertions.not.toContainText [CITED: playwright.dev]
// Plus existing harness pattern in tests/auth.spec.js:230-242 [VERIFIED]

test("post-register copy never claims a confirmation letter", async ({ page }) => {
  await page.goto("/register");
  await page.waitForFunction(() => Boolean(window.__DIGEST_AUTH_HARNESS__));
  await page.evaluate(() => window.__DIGEST_AUTH_HARNESS__.armSignUpWithoutSession());
  // fill + submit ...
  await expect(page.getByRole("alert")).toContainText(
    /Регистрация завершена\. Аккаунт активен — войдите/i,
  );
  await expect(page.getByRole("alert")).not.toContainText(/письм/i);
  await expect(page).toHaveURL(/\/register/);
});
```

*(Requires a new harness arm — Claude's discretion for D-10. Alternative: static scan of exported/constant string without DOM.)*

### GoTrue SMTP + autoconfirm (ops)

```properties
# Source: supabase/auth README via Context7 [CITED]
GOTRUE_SMTP_HOST=smtp.example.com
GOTRUE_SMTP_PORT=587
GOTRUE_SMTP_USER=smtp-delivery@example.com
GOTRUE_SMTP_PASS=...
GOTRUE_SMTP_ADMIN_EMAIL=support@example.com
GOTRUE_MAILER_SUBJECTS_CONFIRMATION="Please confirm"
GOTRUE_MAILER_AUTOCONFIRM=true
```

### One-command rollback (D-05)

```bash
# Document in runbook — not executed this session
# Set GOTRUE_MAILER_AUTOCONFIRM=true on Auth container env, reload/restart Auth/GoTrue
# Verify: GET https://knowledge-db.ru/auth/v1/settings → "mailer_autoconfirm": true
```

### Mailer port (must remain untouched for signup)

```python
# Source: backend/src/backend/application/ports/mailer.py:8-18 [VERIFIED]
class Mailer(Protocol):
    def send_digest(
        self,
        *,
        batch_id: int,
        issue_url: str,
        subject: str,
        body_text: str,
        recipient_count: int,
        body_html: str | None = None,
    ) -> dict[str, object]:
        ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Confirm email ON + broken SMTP → signup 500 | Autoconfirm ON (`mailer_autoconfirm: true`) | 2026-09-20 | Registration works; no confirmation mail by design |
| UI promises letter on `!session` | Honest (B) copy (this phase) | Phase 20 | Copy matches ops reality |
| StubMailer for digests | Live `SMTP_*` (Phase 21) | Future | Separate lane from GoTrue |

**Deprecated/outdated:**
- Treating MAIL-02 as "implement backend confirmation mailer" — superseded by CONTEXT + architecture.
- PITFALLS.md suggestion to send confirmation through app `Mailer` — **do not follow**; CONTEXT criterion 3 forbids it.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Corporate relay will be reachable from the Auth container on the Supabase VM when operator supplies params | Relay / Environment | Path (A) smoke fails; stay on (B) longer |
| A2 | Same relay host can serve both `GOTRUE_SMTP_*` and Phase 21 `SMTP_*` with separate credentials/lanes | Standard Stack | Contour/ops may require two relays — update runbook |
| A3 | `armSignUpWithoutSession` (or equivalent) is acceptable discretion for D-10 | Code Examples | Planner may choose constant-scan instead |
| A4 | Self-hosting docs blurb that inverts autoconfirm semantics is wrong; GoTrue README is correct | Pitfall 5 | Operator misconfigures Confirm email |

**If this table is empty:** N/A — assumptions listed above need confirmation before path (A).

## Open Questions

1. **Harness vs constant-scan for D-10**
   - What we know: mock `signUp` never returns null; dishonest string lives only on `!session`.
   - What's unclear: preferred RED surface (DOM vs source).
   - Recommendation: prefer DOM + harness arm (behaviour); constant-scan as cheaper Wave 0 fallback under discretion.

2. **Signup-edge domain gate before path (A)**
   - What we know: Pitfall 16 — SPA gate is bypassable; healthy SMTP enables open confirmation sends.
   - What's unclear: whether Phase 21 precondition must include a GoTrue hook / edge check.
   - Recommendation: document as operator blocker for flipping (A); do not expand Phase 20 scope (D-08/deferred).

3. **Exact Studio vs env mapping on knowledge-db.ru**
   - What we know: runbook equates Studio «Confirm email OFF» with `GOTRUE_MAILER_AUTOCONFIRM=true`.
   - What's unclear: whether compose file on the Supabase VM uses Studio overrides that shadow env.
   - Recommendation: runbook smoke always trusts `GET /auth/v1/settings`, not file contents alone.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Playwright / Vite | ✓ | v24.21.0 | — |
| `@playwright/test` | D-09/D-10 | ✓ | 1.62.1 runtime | — |
| `uv` + pytest | D-11 tripwire | ✓ | uv 0.10.9 | — |
| Python | pytest | ✓ | 3.14.0 | — |
| GoTrue at knowledge-db.ru | Live smoke / settings probe | ✓ (ops) | GoTrue v2.196.0 (debug) | Document-only this session |
| Corporate SMTP relay params | Criterion 4 full proof / path (A) | ✗ | — | Ship (B); document shape; Phase 21 precondition |
| Graphify knowledge graph | Cross-doc discovery | ✗ disabled | — | Continue without graph |

**Missing dependencies with no fallback:**
- None for path (B) ship.

**Missing dependencies with fallback:**
- Corporate relay parameters → document-only path (A) procedure; ship honest autoconfirm (B).

Step 2.6 note: external ops dependency (relay) identified; code/config work for (B) has no blocking local tool gap.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Playwright `@playwright/test` ^1.62.1 + pytest via `uv` |
| Config file | `playwright.config.js` (web project forces `VITE_USE_MOCKS=true`) |
| Quick run command | `npx playwright test tests/auth.spec.js --project=web` |
| Full suite command | `npm test` (Playwright) and `npm run test:unit` (pytest) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAIL-02 | Post-register copy is honest (B) string when no session | e2e | `npx playwright test tests/auth.spec.js --project=web -g "honest\|письм\|Регистрация завершена"` | ❌ Wave 0 — add/amend |
| MAIL-02 | Copy never claims confirmation letter | e2e / static | same file, new regression (D-10) | ❌ Wave 0 |
| MAIL-02 | Autoconfirm happy path still redirects + shell identity | e2e | existing `shows Логин as shell identity after register` | ✅ PRESERVE under (B) |
| MAIL-02 | Two-domain gate unchanged | unit | `uv run pytest tests/unit/test_auth_email_domain.py -x` | ✅ PRESERVE |
| MAIL-02 | Debug session closed with fix ref | manual/doc | review `.planning/debug/g-01-3b-signup-mailer.md` | ✅ file exists; status close in-phase |
| MAIL-02 | Runbook SMTP/smoke/rollback section | manual/doc | review `docs/agents/local-platform-runbook.md` §4.1+ | ✅ section exists; extend |

### Sampling Rate

- **Per task commit:** `npx playwright test tests/auth.spec.js --project=web`
- **Per wave merge:** `npm run test:web` + `uv run pytest tests/unit/test_auth_email_domain.py`
- **Phase gate:** Full `npm test` + unit tripwire green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] Amend/add `tests/auth.spec.js` coverage for honest `CONFIRM_MESSAGE` (D-09) — current suite has **no** assertion on the letter-claim string
- [ ] New D-10 regression (negative letter-claim assert and/or constant scan)
- [ ] Optional harness `armSignUpWithoutSession` in `authApi.js` + `main.jsx` (discretion) — only if DOM assertion chosen
- [ ] Framework install: none

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | GoTrue sessions; autoconfirm policy explicit |
| V3 Session Management | yes (path B issues session on signup) | Existing supabase-js session handling — no change |
| V4 Access Control | partial | ADR-0003 domain gate PRESERVE; signup-edge gap documented for future (A) |
| V5 Input Validation | yes | Existing corporate email helper; no new inputs |
| V6 Cryptography | no | No new crypto; TLS mode for relay is ops (runbook shape only) |

### Known Threat Patterns for GoTrue + SMTP

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Broken SMTP → signup 500 / no user | Denial of Service | Keep autoconfirm until relay smoke; one-command rollback (D-05) |
| Open confirmation mail spam when (A) enabled | Spoofing / Abuse | Signup-edge domain gate before flip (Pitfall 16); rate limits `GOTRUE_RATE_LIMIT_EMAIL_SENT` |
| SMTP credentials in repo / YAML | Information Disclosure | VM env only; runbook placeholders; no secrets in git (D-03) |
| Backend Mailer used for auth tokens | Elevation / Tampering | Forbidden — GoTrue only (criterion 3) |
| Dishonest UX (claims mail sent) | Spoofing (trust) | Honest (B) copy (D-07) |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/20-mail-02-signup-confirmation-mail/20-CONTEXT.md` — locked decisions D-01…D-14
- `.planning/debug/g-01-3b-signup-mailer.md` — root cause + 2026-09-20 verification
- `web/src/pages/RegisterPage.jsx` — `CONFIRM_MESSAGE` and `!session` branch
- `web/src/services/authApi.js` — mock always returns session; live returns `data.session`
- `playwright.config.js` — `VITE_USE_MOCKS: "true"` for web project
- `tests/auth.spec.js` — post-register happy path + network failure harness
- `docs/agents/local-platform-runbook.md` §4.1 — autoconfirm ops
- `backend/src/backend/application/ports/mailer.py` — digest-only port
- `AGENTS.md`, `.cursor/rules/tdd.mdc`, `.cursor/rules/architecture.mdc`
- Context7 `/supabase/auth` — SMTP + `GOTRUE_MAILER_AUTOCONFIRM` (classify-confidence MEDIUM even with `--verified`)

### Secondary (MEDIUM confidence)
- Context7 `/websites/supabase` — Auth SMTP guide + self-hosting config (autoconfirm blurb conflict noted)
- Context7 `/websites/playwright_dev` — `not.toContainText` / `toHaveCount`
- `.planning/research/FEATURES.md` / `PITFALLS.md` — MAIL-02 analysis (Mailer option superseded by CONTEXT)

### Tertiary (LOW confidence)
- Assumed future shared-relay topology (A1/A2)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — existing project stack; no new deps; GoTrue already diagnosed
- Architecture: HIGH — CONTEXT + ports/adapters + criterion 3 fence
- Pitfalls: HIGH for product pitfalls (verified in-repo); MEDIUM for GoTrue SMTP field defaults from docs

**Research date:** 2026-10-16  
**Valid until:** 2026-11-15 (30 days; ops/SMTP docs move slowly; re-verify GoTrue version on VM before path A)
