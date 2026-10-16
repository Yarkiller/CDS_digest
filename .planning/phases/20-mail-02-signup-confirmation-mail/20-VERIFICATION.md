---
phase: 20-mail-02-signup-confirmation-mail
verified: 2026-10-16T09:00:00Z
status: passed
score: 10/10 must-haves verified
covered_files:
  - .planning/debug/g-01-3b-signup-mailer.md
  - .planning/phases/20-mail-02-signup-confirmation-mail/20-01-PLAN.md
  - .planning/phases/20-mail-02-signup-confirmation-mail/20-01-SUMMARY.md
  - .planning/phases/20-mail-02-signup-confirmation-mail/20-02-PLAN.md
  - .planning/phases/20-mail-02-signup-confirmation-mail/20-02-SUMMARY.md
  - docs/agents/local-platform-runbook.md
  - tests/auth.spec.js
  - tests/unit/test_auth_email_domain.py
  - web/src/main.jsx
  - web/src/pages/RegisterPage.jsx
  - web/src/services/authApi.js

covered_digest: "v2:sha256:23a8479648763f36991ac9d27fe611d2bac8f883c286d3adb855e2f572e0f90c"
behavior_unverified: 0
overrides_applied: 0
deferred:
  - truth: "ROADMAP SC4: The corporate SMTP relay is chosen and proven by a smoke test with a one-command rollback, serving both GoTrue and MAIL-01."
    addressed_in: "Phase 21"
    evidence: "Phase 21 Depends on Phase 20 (shared relay chosen and proven on the GoTrue lane); Plan 20-02 D-06 + runbook §4.1.3 explicitly record criterion-4 live proof as Phase 21 precondition; CONTEXT acknowledges deliberate gap while shipping path (B)."
advisory:
  - finding: "CR-01: armSignUpWithoutSession short-circuits live Auth signup before useLiveAuth()"
    category: security
    reason: "Harness arm returns null before live GoTrue call; window.__DIGEST_AUTH_HARNESS__ is always exported. Can show false «Аккаунт активен» if armed in a live build. Does not fail path-(B) must-haves (Playwright mocks path is what D-09/D-10 exercise). Disposition open in 20-REVIEW-DISPOSITION.md — fix via /gsd-code-review 20 --fix if desired."
    evidence_status: "reproduced by code inspection web/src/services/authApi.js:129-132; no must-have requires mock-only gating"
  - finding: "WR-01: Path-(A) runbook enablement omits SPA CONFIRM_MESSAGE update before flipping confirm-email ON"
    category: other
    reason: "Under confirm-email ON, successful signUp often returns session:null; current CONFIRM_MESSAGE («Аккаунт активен») would then lie. Affects future path-(A) ops honesty, not the shipped path-(B) end state. Note for Phase 21 / path-(A) flip — do not invent production work in this verify."
    evidence_status: "docs/agents/local-platform-runbook.md §4.1.2 steps 4–6 lack SPA-copy precondition"
human_verification:
  - test: "Ack prohibition: signup confirmation never routes through backend Mailer.send_digest"
    expected: "No signup→Mailer wiring; GoTrue owns confirmation (criterion 3)."
    why_human: "Judgment-tier flagged prohibition (PLAN 20-01/20-02) — LLM-judge found held (no Mailer imports under web/src; runbook states fence); needs interactive human ack."
  - test: "Ack prohibition: Russian post-register success copy never claims a confirmation letter under path (B)"
    expected: "CONFIRM_MESSAGE is «Регистрация завершена. Аккаунт активен — войдите.»; Playwright forbids /письм/i on role=alert."
    why_human: "Judgment-tier flagged prohibition — LLM-judge held via RegisterPage + green Playwright; needs human ack."
  - test: "Ack prohibition: tests/auth.spec.js post-register assertions amended/added, not deleted"
    expected: "«shows Логин as shell identity after register» still present; new letter-claim test added."
    why_human: "Judgment-tier flagged prohibition — LLM-judge held by file presence; needs human ack."
  - test: "Ack prohibition: tests/unit/test_auth_email_domain.py untouched (D-11 PRESERVE)"
    expected: "No phase edits; pytest -x green (5 passed)."
    why_human: "Judgment-tier flagged prohibition — LLM-judge held (git log last touch pre-phase; pytest green); needs human ack."
  - test: "Ack prohibition: runbook/UI docs do not claim confirmation mail is delivered under current autoconfirm (B) ship"
    expected: "Runbook §4.1 states path B + criterion-4 gap; no claim of live confirmation delivery."
    why_human: "Judgment-tier flagged prohibition (20-02) — LLM-judge held by §4.1.3 wording; needs human ack."
  - test: "Ack prohibition: g-01-3b-signup-mailer.md closed not deleted; no speculative SMTP secrets / half-enabled GOTRUE_SMTP_* in app code"
    expected: "Debug file tracked with status:resolved; placeholders only in runbook; no new ADR."
    why_human: "Judgment-tier flagged prohibitions (20-02 D-12/D-06) — LLM-judge held; needs human ack."
  - test: "Optional UAT: open /register once under current autoconfirm and confirm visible copy never promises a letter"
    expected: "Any null-session or success messaging matches honest (B) copy; no «письм» claim."
    why_human: "User-facing honesty — Playwright covers mock null-session; live visual is outside automated gate."
---

# Phase 20: MAIL-02 signup confirmation mail Verification Report

**Phase Goal:** The signup-confirmation mail root cause is diagnosed and documented, and the delivered end state is honest — either a working confirmation email through the corporate relay, or an explicitly autoconfirmed flow whose Russian copy never claims that mail was sent.

**Verified:** 2026-10-16T09:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

Phase ships path **(B)** (honest autoconfirm copy) per CONTEXT/D-02. ROADMAP criterion 4 (live relay smoke proof) is an **acknowledged deferred gap → Phase 21**, not silently dropped. Automated must-haves for the in-session contract are all verified; flagged judgment-tier prohibitions require human ack before `passed`.

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Diagnosis recorded; `.planning/debug/g-01-3b-signup-mailer.md` closed with fix (ROADMAP SC1 / D-12 / D-14) | ✓ VERIFIED | File tracked; `status: resolved`; Root cause retains `unexpected_failure` / confirmation email; Resolution cites CONFIRM_MESSAGE + path (A) target |
| 2 | Exactly one honest end state: path (B) autoconfirm copy never claims mail sent (ROADMAP SC2 / D-02 / D-07 / D-10) | ✓ VERIFIED | `CONFIRM_MESSAGE` exact D-07 string; Playwright `post-register copy never claims a confirmation letter` **1 passed** (assert + `not.toContainText(/письм/i)` + stay on `/register`) |
| 3 | Signup confirmation not routed through backend `Mailer` (ROADMAP SC3) | ✓ VERIFIED | No `Mailer`/`send_digest` under `web/src`; auth stays `supabase.auth.signUp`; runbook restates fence |
| 4 | Corporate relay chosen **and proven** by smoke test (ROADMAP SC4) | deferred | Documented procedure + rollback exist; live proof → Phase 21 (D-06 / §4.1.3). See Deferred Items |
| 5 | `tests/auth.spec.js` post-register amended never deleted; letter-claim regression (ROADMAP SC5 / D-09 / D-10) | ✓ VERIFIED | Happy-path `shows Логин as shell identity after register` retained; new letter-claim test added (not substituted by deletion) |
| 6 | D-08: `CONFIRM_MESSAGE` only in `RegisterPage.jsx`; authApi error-mapping strings unchanged | ✓ VERIFIED | Constant in RegisterPage only; phase commit `8c027f1` adds harness only — no AuthApiError/NETWORK string edits |
| 7 | D-11: `tests/unit/test_auth_email_domain.py` PRESERVE | ✓ VERIFIED | `uv run pytest … -x` → 5 passed; last commit on file predates phase (`2f02dc5`); no working-tree edits |
| 8 | D-03 / D-05 / D-13: Runbook §4.1 relay shape, smoke, one-command rollback | ✓ VERIFIED | `GOTRUE_SMTP_*`, `SMTP_*`, smoke via `/auth/v1/settings` + signup, rollback `GOTRUE_MAILER_AUTOCONFIRM=true` + reload |
| 9 | D-06: Criterion-4 live proof explicitly recorded as Phase 21 precondition | ✓ VERIFIED | §4.1.3 plain-language gap; ROADMAP Phase 21 Depends on matches |
| 10 | D-01 / D-04: Path (A) remains target; no separate relay ADR this phase | ✓ VERIFIED | Debug Resolution + runbook state (A) target; `docs/adr/` has no new relay ADR (only 0001–0004) |

**Score:** 10/10 truths verified (0 present, behavior-unverified). SC4 excluded from score as deferred.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ROADMAP SC4 live corporate-relay smoke-test proof | Phase 21 | Phase 21 Depends on «relay chosen and proven on the GoTrue lane»; Plan 20-02 D-06; runbook §4.1.3 |

### Advisory (Code review — does not fail must-haves)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | CR-01 harness short-circuits live `signUp` | security | Open in disposition; latent if harness armed in live build; path-(B) Playwright contract still holds under mocks |
| 2 | WR-01 path-(A) runbook missing SPA copy precondition | other | Future flip risk; shipped end state is (B); Phase 21 / ops follow-up |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `web/src/pages/RegisterPage.jsx` | D-07 CONFIRM_MESSAGE + !session ErrorPanel | ✓ VERIFIED | Exists, substantive, wired; data = constant → alert |
| `web/src/services/authApi.js` | `armSignUpWithoutSession` + reset | ✓ VERIFIED | One-shot null return; error mapping untouched |
| `web/src/main.jsx` | harness export | ✓ VERIFIED | `__DIGEST_AUTH_HARNESS__.armSignUpWithoutSession` |
| `tests/auth.spec.js` | D-09/D-10 coverage | ✓ VERIFIED | New test + happy-path preserved |
| `.planning/debug/g-01-3b-signup-mailer.md` | Closed diagnosis | ✓ VERIFIED | Resolved + Resolution; not deleted |
| `docs/agents/local-platform-runbook.md` | §4.1 relay / smoke / rollback / gap | ✓ VERIFIED | §4.1.1–4.1.3 present |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `tests/auth.spec.js` | `authApi.js` | `armSignUpWithoutSession` | ✓ WIRED | gsd verify.key-links |
| `RegisterPage.jsx` | `ErrorPanel.jsx` | `CONFIRM_MESSAGE` → `role=alert` | ✓ WIRED | pattern + ErrorPanel `role="alert"` |
| `main.jsx` | `authApi.js` | `__DIGEST_AUTH_HARNESS__` | ✓ WIRED | import + export |
| debug g-01-3b | `RegisterPage.jsx` | Resolution cites CONFIRM_MESSAGE | ✓ WIRED | Resolution + files_changed |
| runbook | debug g-01-3b | §4.1 diagnosis link + settings probe | ✓ WIRED | GOTRUE_MAILER_AUTOCONFIRM |
| runbook | ROADMAP Phase 21 | criterion-4 precondition | ✓ WIRED | «Phase 21» §4.1.3 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| RegisterPage null-session alert | `CONFIRM_MESSAGE` | module constant (D-07) | Yes — honest (B) copy by design | ✓ FLOWING |
| Playwright null session | `armSignUpWithoutSession` | mock one-shot flag | Yes — forces `signUp` → `null` under mocks | ✓ FLOWING |
| Live confirmation mail | GoTrue SMTP | Not enabled this session | N/A — path (B); SC4 deferred | deferred |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Honest copy + letter-claim forbid | `npx playwright test tests/auth.spec.js --project=web -g "post-register copy never claims a confirmation letter"` | 1 passed (4.3s) | ✓ PASS |
| Domain tripwire PRESERVE | `uv run pytest tests/unit/test_auth_email_domain.py -x` | 5 passed | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh` | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| MAIL-02 | 20-01, 20-02 | Diagnosed root cause + honest end state (B), or (A) when proven | ✓ SATISFIED (in-session B) | Path (B) ship + diagnosis closed; SC4 → Phase 21 deferred, not orphaned |
| MAIL-02 | REQUIREMENTS.md | Mapped to Phase 20 Complete | ✓ SATISFIED | No orphaned Phase-20 IDs beyond MAIL-02 |

### Decision Coverage

All trackable CONTEXT.md decisions honored (14/14). `gsd_run query check.decision-coverage-verify` → no `not_honored`.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/auth.spec.js` (letter-claim) | MAIL-02 | yes | none on this test | no | Behavioral (copy + negative + URL) | PASS |
| `tests/unit/test_auth_email_domain.py` | MAIL-02 / D-11 | yes (5) | none | no | Value | PASS |

**Disabled tests on requirements:** 0
**Circular patterns detected:** 0
**Insufficient assertions:** 0 (IN-02 advisory: missing non-retryable button assert — warning only, not blocker)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No TBD/FIXME/XXX in phase-modified files | — | — |
| `authApi.js` | 129-132 | CR-01 live short-circuit | 📋 Advisory | See advisory; not a must-have FAIL |

### Human Verification Required

### 1. Flagged prohibition ack (Mailer fence)

**Test:** Confirm signup never uses backend `Mailer` / `send_digest`.
**Expected:** Auth confirmation remains GoTrue-owned.
**Why human:** Judgment-tier flagged prohibition — interactive ack required (LLM-judge: held).

### 2. Flagged prohibition ack (honest copy)

**Test:** Confirm post-register Russian copy never promises a letter under path (B).
**Expected:** D-07 string; no letter claim.
**Why human:** Judgment-tier flagged prohibition (LLM-judge: held via Playwright).

### 3. Flagged prohibition ack (test amend / domain PRESERVE / debug retention / no SMTP secrets)

**Test:** Spot-check that assertions were amended not deleted, domain unit file untouched, debug closed not deleted, runbook placeholders only.
**Expected:** All holds.
**Why human:** Bundle of judgment-tier flagged prohibitions (LLM-judge: held).

### 4. Optional live `/register` glance

**Test:** Open register once under current autoconfirm.
**Expected:** No confirmation-letter promise in UI.
**Why human:** User-facing; mocks already covered by Playwright.

### Gaps Summary

No blocking gaps for the in-session path-(B) goal. ROADMAP SC4 live relay proof is **deferred** to Phase 21 with explicit documentation. Status is `human_needed` solely for flagged judgment-tier prohibition acknowledgements (and optional live glance) — not because must-have truths failed.

CR-01 / WR-01 noted as advisory; they do not reverse verified must-haves for the shipped (B) contract. Do not invent production work from this verify pass.

---

_Verified: 2026-10-16T09:00:00Z_
_Verifier: Claude (gsd-verifier)_
