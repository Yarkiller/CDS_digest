# Phase 20: MAIL-02 signup confirmation mail - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-14
**Phase:** 20-MAIL-02 signup confirmation mail
**Areas discussed:** End state (A/B), Relay inputs, One-command rollback, Honest copy, Copy location, Tests, Diagnosis artifact, Relay arrival

---

## End state (A vs B)

| Option | Description | Selected |
|--------|-------------|----------|
| (B) autoconfirm + honest copy | Registration active immediately; UI tells the truth and promises no letter. Already the factual state (`mailer_autoconfirm: true`); fastest honesty with no external blocker | |
| (A) working relay mail | Turn autoconfirm off, wire GoTrue SMTP, user confirms via email — requires live relay access and parameters now | |
| (A) target, (B) guaranteed fallback | Pursue (A); if the relay cannot be proven this session, the phase still passes on honest autoconfirm | ✓ |

**User's choice:** (A) as target, (B) as guaranteed fallback
**Notes:** Explicitly chosen over shipping pure (B), to keep the relay as the intended destination while guaranteeing the phase can pass without it.

---

## Relay inputs

| Option | Description | Selected |
|--------|-------------|----------|
| Parameters available | Use host/port/TLS/CA/credentials directly | |
| Parameters unavailable | Record the choice and config shape (`GOTRUE_SMTP_*` / `SMTP_*`); operator supplies values later — effectively ships (B) | ✓ |
| Parameters available + emit ADR | Wire it up and also publish a relay ADR with ADR-0002 contour isolation | |

**User's choice:** Parameters unavailable
**Notes:** This is what forces end state (B) in this session and makes criterion 4's "proven by a smoke test" an operator precondition. Consequence recorded as an acknowledged limitation in CONTEXT.md.

---

## One-command rollback

| Option | Description | Selected |
|--------|-------------|----------|
| Single flag/env | Revert `GOTRUE_MAILER_AUTOCONFIRM=true` and reload the container config — one command, no DB change | ✓ |
| Compose revert | Roll back via a compose-file edit plus container restart | |

**User's choice:** Single flag/env
**Notes:** Chosen because it cannot strand database state.

---

## Honest copy

| Option | Description | Selected |
|--------|-------------|----------|
| (B) copy now | Write the honest text immediately — «Регистрация завершена. Аккаунт активен — войдите.» — and drop the letter promise | ✓ |
| Conditional copy | Read the live setting and show either "check your mail" or "account active" | |
| (B) copy + error mapping | Honest (B) text *and* rewrite the confirmation-error mapping so a mail failure is never masked by the generic «Сервис входа временно недоступен» | |

**User's choice:** (B) copy now
**Notes:** Closes the current dishonesty — `RegisterPage.jsx:12` claims a letter was sent while autoconfirm means none is.

---

## Copy location

| Option | Description | Selected |
|--------|-------------|----------|
| `RegisterPage.jsx` only | One targeted string edit | ✓ |
| `RegisterPage.jsx` + `authApi.js` | Also make the send-failure mapping honest | |

**User's choice:** `RegisterPage.jsx` only
**Notes:** The `authApi.js` error-mapping honesty was recorded as a deferred item instead.

---

## Tests

| Option | Description | Selected |
|--------|-------------|----------|
| Amend + regression | Amend `tests/auth.spec.js`'s post-register assertion to the new copy **and** add a regression that the copy never claims a letter was sent | ✓ |
| Amend only | Just update the existing assertion | |

**User's choice:** Amend + regression
**Notes:** The regression exists specifically so the dishonesty cannot silently return.

---

## Diagnosis artifact

| Option | Description | Selected |
|--------|-------------|----------|
| Close debug + runbook | Close `.planning/debug/g-01-3b-signup-mailer.md` with the fix reference, and add a GoTrue config / smoke / rollback section to `docs/agents/local-platform-runbook.md` | ✓ |
| Debug only | Close the debug session only; leave the runbook alone | |
| ADR/doc only | Record the root cause only in an ADR/doc; leave the debug session as-is | |

**User's choice:** Close debug + runbook
**Notes:** The debug session is closed, not deleted.

---

## Relay arrival

| Option | Description | Selected |
|--------|-------------|----------|
| Document procedure only | Document the enable/rollback procedure in the runbook; the operator executes it when parameters exist — no speculative code | ✓ |
| Procedure + Phase 21 gate | Also explicitly hand "relay chosen and proven" to Phase 21 as its precondition | |

**User's choice:** Document procedure only
**Notes:** No speculative or half-enabled code path is shipped. Phase 21's precondition still derives from the ROADMAP dependency note.

---

## Claude's Discretion

- Exact paragraph layout/wording around the new success copy.
- How the D-10 regression is expressed (rendered-string assertion vs copy-constant scan).
- Placement of the new section inside `local-platform-runbook.md`.

## Deferred Ideas

- Relay smoke-test **proof** (criterion 4 partial) — requires operator parameters; carried forward as Phase 21's precondition.
- SPA error-UX honesty for confirmation-mailer failures in `web/src/services/authApi.js` (the debug session's own deferred follow-up).
- A formal relay/contour ADR (ADR-0002 isolation) — declined for this phase.
