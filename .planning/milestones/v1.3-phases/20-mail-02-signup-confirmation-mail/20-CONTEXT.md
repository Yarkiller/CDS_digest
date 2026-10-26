# Phase 20: MAIL-02 signup confirmation mail - Context

**Gathered:** 2026-10-14
**Status:** Ready for planning

<domain>
## Phase Boundary

The signup-confirmation mail root cause is diagnosed and documented, and the project ships **exactly one honest end state**: either (A) a working confirmation email delivered through the corporate SMTP relay (GoTrue/Supabase Auth sends it), or (B) an explicitly autoconfirmed flow whose Russian copy never claims that mail was sent.

The phase does **not** build the digest mailer (that is Phase 21), does **not** route signup confirmation through the backend `Mailer` port (criterion 3 — that is an anti-feature), and does **not** change the fixed two-domain email gate (ADR-0003).

**Acknowledged limitation (read this before planning):** the corporate relay's parameters are not available in this session, so the phase ships end state **(B)**. Success criterion 4 ("the relay is chosen **and proven** by a smoke test") therefore cannot be fully satisfied here — the relay *choice* and configuration shape are recorded, and the smoke/rollback procedure is documented, but the actual proof is an operator precondition that carries forward to Phase 21. This is a deliberate, recorded gap, not a forgotten item.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` §Phase 20 — the goal, the five success criteria, the decision gate, requirements `MAIL-02`, and the tripwire note.
- `.planning/REQUIREMENTS.md` — `MAIL-02` (and `MAIL-03`/`MAIL-04`/`MAIL-05`, which belong to Phase 21 and constrain the shared relay).
- `.planning/PROJECT.md` — v1.3 milestone framing; the "SMTP relay is not chosen yet" risk; "MAIL-02's root cause is unknown" note (now resolved by the debug session).

### Diagnosis and current state
- `.planning/debug/g-01-3b-signup-mailer.md` — the full diagnosis, the probe outputs (`disable_signup`, `mailer_autoconfirm`, `external.email`), the chosen split path, and the 2026-09-20 verification that autoconfirm is on. **Must be closed, not deleted.**
- `docs/agents/local-platform-runbook.md` — where the GoTrue mailer config, smoke test, and rollback procedure are recorded.

### The dishonesty being fixed
- `web/src/pages/RegisterPage.jsx` — the post-register success string that claims a confirmation letter was sent.
- `web/src/services/authApi.js` — the shared auth error mapping (read for context; explicitly out of scope per D-08).
- `tests/auth.spec.js` — the post-register assertion to amend (D-09).

### Constraints
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — contour isolation, which governs the relay choice.
- `docs/adr/0003-email-domain-restriction.md` — the fixed two-domain gate (`test_auth_email_domain.py`, PRESERVE).
- `.cursor/rules/tdd.mdc` — mandatory Red–Green–Refactor.
- `.cursor/rules/architecture.mdc` — Ports & Adapters; criterion 3 forbids routing signup confirmation through the backend `Mailer` port.
- `CLAUDE.md` — project instructions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The debug session `.planning/debug/g-01-3b-signup-mailer.md` already contains the probe evidence and the diagnosis — the phase closes it rather than re-diagnosing from scratch.
- `docs/agents/local-platform-runbook.md` already carries operator procedures (including a GoTrue/autoconfirm section per the debug record) — the new section extends it.
- `tests/auth.spec.js` already has a post-register assertion — D-09 amends it in place.

### Established Patterns
- Auth identity lives entirely outside FastAPI: the SPA calls Supabase Auth via `web/src/services/authApi.js`; there is no backend signup route. This is why criterion 3 makes a backend `Mailer` route an anti-feature.
- The runbook is the project's place for operator-executable procedures and rollbacks.
- `VITE_USE_MOCKS` / Playwright harness conventions govern how the auth spec runs, so D-09's amendment must fit the existing harness rather than introducing a new one.
- TDD is mandatory — the copy change needs a failing test first (the amended/new assertion), then the minimal copy edit.

### Integration Points
- `web/src/pages/RegisterPage.jsx` — the honest-copy edit (D-07/D-08).
- `tests/auth.spec.js` — the amended + new assertions (D-09/D-10).
- `.planning/debug/g-01-3b-signup-mailer.md` — closure (D-12).
- `docs/agents/local-platform-runbook.md` — the GoTrue config / smoke / rollback section (D-13).
- GoTrue container env (`GOTRUE_MAILER_AUTOCONFIRM`, `GOTRUE_SMTP_*`) — referenced by the documented procedure, not changed in this session.

</code_context>

<specifics>
## Specific Ideas

- Proposed honest (B) copy: «Регистрация завершена. Аккаунт активен — войдите.»
- The rollback is literally one line: `GOTRUE_MAILER_AUTOCONFIRM=true` plus a container config reload.
- The 2026-09-20 debug verification command shape: `GET /auth/v1/settings` → `mailer_autoconfirm`, and `POST /auth/v1/signup` → HTTP 200 with `email_confirmed_at` set under autoconfirm.
- Criterion 3 is a hard architectural fence: the GoTrue container sends the confirmation; the backend `Mailer` port must not be involved.

</specifics>

<deferred>
## Deferred Ideas

### Acknowledged gaps carried forward
- **Relay proof (criterion 4, partial):** the relay choice and config shape are recorded, but the actual smoke-test proof requires operator-supplied parameters. Carried forward as Phase 21's precondition, not silently dropped.
- **SPA error-UX honesty for mailer failures:** the debug session's deferred item — mapping confirmation-mailer failures to honest Russian copy instead of the generic «Сервис входа временно недоступен» (`web/src/services/authApi.js`) — was explicitly **not** taken in this phase (D-08). It belongs with the error-mapping work.
- **Relay/contour ADR:** a formal ADR for the relay and its ADR-0002 contour isolation was declined for this phase (D-04); raise it where the relay actually lands.

### Reviewed Todos (not folded)
None.

</deferred>

---

*Phase: 20-MAIL-02 signup confirmation mail*
*Context gathered: 2026-10-14*
