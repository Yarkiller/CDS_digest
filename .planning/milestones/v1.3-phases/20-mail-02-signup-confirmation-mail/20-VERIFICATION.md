---
phase: 20-mail-02-signup-confirmation-mail
verified: 2026-10-17T20:30:00Z
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
covered_digest: "v2:sha256:ef89092646ec762636c6ab3f2b1afd78d0e21c6d737167cc882255596f3ecc5b"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 10/10
  previous_verified: 2026-10-17T08:44:19Z
  previous_covered_digest: "v2:sha256:b31f8f4b397fbe1f977474b75243e62820b063387817763e083abb196c07e62b"
  reason: "stale covered_digest refresh (GSD #4682) — covered sources changed after prior verify (notably docs/agents/local-platform-runbook.md via Phase 21/23 docs); must-haves re-checked against current codebase; plans not re-executed; no production code modified this pass"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  uat_preserved: true
  uat_ref: "20-UAT.md status:complete (7/7 pass, updated 2026-10-16T13:04:00Z)"
  security_preserved: true
  security_ref: "20-SECURITY.md threats_open:0 status:verified"
deferred:
  - truth: "ROADMAP SC4: The corporate SMTP relay is chosen and proven by a smoke test with a one-command rollback, serving both GoTrue and MAIL-01."
    addressed_in: "Phase 21"
    evidence: "Phase 21 Depends on Phase 20 (shared relay chosen and proven on the GoTrue lane); Plan 20-02 D-06 + runbook §4.1.3 explicitly record criterion-4 live proof as Phase 21 precondition; CONTEXT acknowledges deliberate gap while shipping path (B)."
advisory:
  - finding: "CR-01: armSignUpWithoutSession short-circuits live Auth signup before useLiveAuth()"
    category: security
    reason: "Harness arm returns null before live GoTrue call; window.__DIGEST_AUTH_HARNESS__ is always exported. Can show false «Аккаунт активен» if armed in a live build. Does not fail path-(B) must-haves (Playwright mocks path is what D-09/D-10 exercise). Disposition open in 20-REVIEW-DISPOSITION.md — fix via /gsd-code-review 20 --fix if desired. Mapped to AR-20-01 in 20-SECURITY.md."
    evidence_status: "reproduced by code inspection web/src/services/authApi.js:129-132; no must-have requires mock-only gating"
  - finding: "WR-01: Path-(A) runbook enablement omits SPA CONFIRM_MESSAGE update before flipping confirm-email ON"
    category: other
    reason: "Under confirm-email ON, successful signUp often returns session:null; current CONFIRM_MESSAGE («Аккаунт активен») would then lie. Affects future path-(A) ops honesty, not the shipped path-(B) end state. Note for Phase 21 / path-(A) flip — do not invent production work in this verify."
    evidence_status: "docs/agents/local-platform-runbook.md §4.1.2 steps lack SPA-copy precondition"
---

# Phase 20: MAIL-02 signup confirmation mail Verification Report

**Phase Goal:** The signup-confirmation mail root cause is diagnosed and documented, and the delivered end state is honest — either a working confirmation email through the corporate relay, or an explicitly autoconfirmed flow whose Russian copy never claims that mail was sent.

**Verified:** 2026-10-17T20:30:00Z
**Status:** passed
**Re-verification:** Yes — stale `covered_digest` refresh (GSD #4682); must-haves re-checked against current codebase; plans not re-executed

## Goal Achievement

Phase ships path **(B)** (honest autoconfirm copy) per CONTEXT/D-02. ROADMAP criterion 4 (live relay smoke proof) remains an **acknowledged deferred gap → Phase 21**, not silently dropped. Prior judgment-tier prohibition acks and optional live glance are preserved via `20-UAT.md` (`status: complete`, 7/7 pass). Security contract preserved via `20-SECURITY.md` (`threats_open: 0`).

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Diagnosis recorded; `.planning/debug/g-01-3b-signup-mailer.md` closed with fix (ROADMAP SC1 / D-12 / D-14) | ✓ VERIFIED | Tracked; `status: resolved`; Root cause retains `unexpected_failure` / confirmation email; `## Resolution` cites CONFIRM_MESSAGE + path (A) target |
| 2 | Exactly one honest end state: path (B) autoconfirm copy never claims mail sent (ROADMAP SC2 / D-02 / D-07 / D-10) | ✓ VERIFIED | `CONFIRM_MESSAGE` exact D-07 string; Playwright `post-register copy never claims a confirmation letter` **1 passed** (assert + `not.toContainText(/письм/i)` + stay on `/register`) |
| 3 | Signup confirmation not routed through backend `Mailer` (ROADMAP SC3) | ✓ VERIFIED | No `Mailer`/`send_digest` under `web/src`; auth stays `supabase.auth.signUp`; runbook restates fence; UAT ack #1 pass |
| 4 | Corporate relay chosen **and proven** by smoke test (ROADMAP SC4) | deferred | Documented procedure + rollback exist; live proof → Phase 21 (D-06 / §4.1.3). See Deferred Items |
| 5 | `tests/auth.spec.js` post-register amended never deleted; letter-claim regression (ROADMAP SC5 / D-09 / D-10) | ✓ VERIFIED | Happy-path `shows Логин as shell identity after register` retained; new letter-claim test present; UAT ack #3 pass |
| 6 | D-08: `CONFIRM_MESSAGE` only in `RegisterPage.jsx`; authApi error-mapping strings unchanged | ✓ VERIFIED | Constant in RegisterPage only; NETWORK/CREDENTIALS strings still present in authApi (no rewrite of mapping contract) |
| 7 | D-11: `tests/unit/test_auth_email_domain.py` PRESERVE | ✓ VERIFIED | `uv run pytest … -x` → 5 passed; last commit `2f02dc5` (2026-09-19) predates phase; working tree clean for that file |
| 8 | D-03 / D-05 / D-13: Runbook §4.1 relay shape, smoke, one-command rollback | ✓ VERIFIED | `GOTRUE_SMTP_*`, `SMTP_*`, smoke via `/auth/v1/settings` + signup, rollback `GOTRUE_MAILER_AUTOCONFIRM=true` + reload (still present after Phase 21 runbook extensions) |
| 9 | D-06: Criterion-4 live proof explicitly recorded as Phase 21 precondition | ✓ VERIFIED | §4.1.3 plain-language gap; ROADMAP Phase 21 Depends on matches |
| 10 | D-01 / D-04: Path (A) remains target; no separate relay ADR from this phase | ✓ VERIFIED | Debug Resolution + runbook state (A) target; Phase 20 did not add a relay ADR (later `0005-haskimail-*` is Phase 21 transport — out of phase-20 ship) |

**Score:** 10/10 truths verified (0 present, behavior-unverified). SC4 excluded from score as deferred.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ROADMAP SC4 live corporate-relay smoke-test proof | Phase 21 | Phase 21 Depends on «relay chosen and proven on the GoTrue lane»; Plan 20-02 D-06; runbook §4.1.3 |

### Advisory (New Scope / Prior Review — Unevidenced for must-have FAIL)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | CR-01 harness short-circuits live `signUp` | security | Open in disposition / AR-20-01; latent if harness armed in live build; path-(B) Playwright contract still holds under mocks |
| 2 | WR-01 path-(A) runbook missing SPA copy precondition | other | Future flip risk; shipped end state is (B); ops follow-up |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `web/src/pages/RegisterPage.jsx` | D-07 CONFIRM_MESSAGE + !session ErrorPanel | ✓ VERIFIED | Exists, substantive, wired; `gsd verify.artifacts` passed |
| `web/src/services/authApi.js` | `armSignUpWithoutSession` + reset | ✓ VERIFIED | One-shot null return; error mapping strings present |
| `web/src/main.jsx` | harness export | ✓ VERIFIED | `__DIGEST_AUTH_HARNESS__.armSignUpWithoutSession` |
| `tests/auth.spec.js` | D-09/D-10 coverage | ✓ VERIFIED | New test + happy-path preserved |
| `.planning/debug/g-01-3b-signup-mailer.md` | Closed diagnosis | ✓ VERIFIED | Resolved + Resolution; not deleted |
| `docs/agents/local-platform-runbook.md` | §4.1 relay / smoke / rollback / gap | ✓ VERIFIED | §4.1.1–4.1.3 present (Phase 21 digest SMTP notes additive) |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | ---- | ------ | ------- |
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
| Honest copy + letter-claim forbid | `npx playwright test tests/auth.spec.js --project=web -g "post-register copy never claims a confirmation letter"` | 1 passed (4.8s) | ✓ PASS |
| Domain tripwire PRESERVE | `uv run pytest tests/unit/test_auth_email_domain.py -x` | 5 passed | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh` | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| MAIL-02 | 20-01, 20-02 | Diagnosed root cause + honest end state (B), or (A) when proven | ✓ SATISFIED (in-session B) | Path (B) ship + diagnosis closed; SC4 → Phase 21 deferred, not orphaned |
| MAIL-02 | REQUIREMENTS.md | Mapped to Phase 20 Complete (`[x]`) | ✓ SATISFIED | No orphaned Phase-20 IDs beyond MAIL-02 |

### Decision Coverage

All trackable CONTEXT.md decisions honored (14/14). `gsd_run query check.decision-coverage-verify` → `not_honored: []`. Message: «All trackable CONTEXT.md decisions are honored by shipped artifacts.»

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/auth.spec.js` (letter-claim) | MAIL-02 | yes | none on this test | no | Behavioral (copy + negative + URL) | PASS |
| `tests/unit/test_auth_email_domain.py` | MAIL-02 / D-11 | yes (5) | none | no | Value | PASS |

**Disabled tests on requirements:** 0
**Circular patterns detected:** 0
**Insufficient assertions:** 0 (IN-02 advisory from REVIEW: missing non-retryable button assert — warning only, not blocker)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No TBD/FIXME/XXX in phase-modified files | — | — |
| `authApi.js` | 129-132 | CR-01 live short-circuit | 📋 Advisory | See advisory; not a must-have FAIL |

### Human Verification Required

N/A — prior `20-UAT.md` is `status: complete` with 7/7 pass (judgment-tier prohibition acks + optional `/register` glance). Sign-offs preserved; not re-opened by this digest refresh.

### Gaps Summary

No blocking gaps for the in-session path-(B) goal. ROADMAP SC4 live relay proof remains **deferred** to Phase 21 with explicit documentation. Stale `covered_digest` refreshed (`b31f8f4b…` → `ef890926…`) after covered sources drifted (runbook extended by later phases). CR-01 / WR-01 remain advisory only.

---

_Verified: 2026-10-17T20:30:00Z_
_Verifier: Claude (gsd-verifier)_
