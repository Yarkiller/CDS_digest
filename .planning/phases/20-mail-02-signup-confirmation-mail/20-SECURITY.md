---
phase: "20"
slug: "mail-02-signup-confirmation-mail"
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: "2026-10-16"
---

# Phase 20 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Source plans: `20-01-PLAN.md`, `20-02-PLAN.md` `<threat_model>` (ASVS L1 · block_on=high).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser RegisterPage → authApi.signUp → GoTrue | Signup identity and confirmation policy; SPA must not invent a second mailer | Credentials / session / null-session copy |
| Playwright harness → mock authApi | Test-only null-session arm; must not alter live error mapping or production SMTP | `armSignUpWithoutSession` flag |
| SPA copy → user trust | Dishonest letter claims are a trust/spoofing surface | `CONFIRM_MESSAGE` / role=alert |
| Operator runbook → GoTrue VM env | SMTP credentials and autoconfirm flag live only on the VM | `GOTRUE_SMTP_*` / `GOTRUE_MAILER_AUTOCONFIRM` |
| Diagnosis artifact → future operators | Closed debug file must not become a second conflicting truth | Resolution / root cause |
| Documented path (A) → signup edge | Enabling confirm-email without a domain edge invites open confirmation spam | Relay + autoconfirm flip |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-20-01 | Spoofing | RegisterPage `CONFIRM_MESSAGE` | medium | mitigate | D-07 honest (B) copy; D-10 Playwright forbids letter-claim `/письм/i` on role=alert | closed |
| T-20-02 | Elevation of Privilege | backend `Mailer` port | high | mitigate | Criterion 3 fence: no signup→`Mailer.send_digest`; auth stays client→GoTrue (`supabase.auth.signUp`) | closed |
| T-20-03 | Tampering | `tests/auth.spec.js` | medium | mitigate | Amend/add only; happy-path `shows Логин as shell identity after register` retained; new letter-claim test added | closed |
| T-20-04 | Information Disclosure | authApi harness | low | accept | Harness is test-oriented; no SMTP secrets in repo (D-03/D-06). Residual: CR-01 live short-circuit if harness armed — see Accepted Risks | closed |
| T-20-05 | Information Disclosure | runbook SMTP section | high | mitigate | Placeholders only (`<corporate-relay-host>` etc.); D-03/D-06 forbid secrets and half-enabled SMTP in git | closed |
| T-20-06 | Denial of Service | GoTrue mailer flip | high | mitigate | Smoke-before-flip documented; D-05 one-command rollback `GOTRUE_MAILER_AUTOCONFIRM=true` + Auth reload | closed |
| T-20-07 | Spoofing | Open confirmation mail (Pitfall 16) | medium | mitigate | Runbook §4.1 documents signup-edge domain risk as operator blocker before path (A); ADR-0003 tripwire preserved | closed |
| T-20-08 | Tampering | debug session file | medium | mitigate | Close-with-reference (`status: resolved` + `## Resolution`); diagnosis not deleted (D-12) | closed |
| T-20-SC | Tampering | npm/pip installs | high | mitigate | No new packages this phase (`tech-stack.added: []` in 20-01/20-02 SUMMARY; no lockfile churn) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `block_on` count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Verification Evidence (ASVS L1)

| Threat ID | Evidence |
|-----------|----------|
| T-20-01 | `web/src/pages/RegisterPage.jsx:11-12` — `CONFIRM_MESSAGE` = «Регистрация завершена. Аккаунт активен — войдите.»; `tests/auth.spec.js:245-259` — honest-copy assert + `not.toContainText(/письм/i)` |
| T-20-02 | No `Mailer`/`send_digest` under `web/src`; `authApi.signUp` → `supabase.auth.signUp`; runbook §4.1 restates fence; no backend HTTP signup routes |
| T-20-03 | `tests/auth.spec.js:165` happy-path retained; `:245` new post-register letter-claim test added (not substituted by deletion) |
| T-20-04 | Accepted Risks AR-20-01; no SMTP secrets in tracked files; harness exports in `authApi.js` / `main.jsx` |
| T-20-05 | `docs/agents/local-platform-runbook.md` §4.1.1 — `GOTRUE_SMTP_*` / `SMTP_*` placeholders; explicit «never committed to git» |
| T-20-06 | Runbook §4.1.2 smoke-before-flip + D-05 rollback; §4.1.3 criterion-4 gap → Phase 21 |
| T-20-07 | Runbook §4.1 Pitfall 16 operator blocker; `tests/unit/test_auth_email_domain.py` PRESERVE (D-11) |
| T-20-08 | `.planning/debug/g-01-3b-signup-mailer.md` tracked; `status: resolved`; `## Resolution` cites CONFIRM_MESSAGE; `unexpected_failure` retained |
| T-20-SC | 20-01/20-02 SUMMARY `tech-stack.added: []`; phase commits touch SPA/docs/debug only |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-20-01 | T-20-04 | Playwright harness (`armSignUpWithoutSession` + `window.__DIGEST_AUTH_HARNESS__`) is required for null-session coverage under mocks. No SMTP secrets ship in repo. Residual CR-01: the one-shot arm returns null *before* `useLiveAuth()`, so an armed live build can show false «Аккаунт активен» — low residual for path-(B) ship; optional harden via `/gsd-code-review 20 --fix` | plan 20-01 / secure-phase L1 | 2026-10-16 |
| AR-20-02 | T-20-SC | Zero package installs this phase — package-legitimacy audit N/A | plans 20-01/20-02 | 2026-10-16 |

---

## Unregistered Flags

| Flag | Source | Mapping | Notes |
|------|--------|---------|-------|
| CR-01 | `20-VERIFICATION.md` advisory / `20-REVIEW-DISPOSITION.md` | Maps to T-20-04 residual (AR-20-01) | Live harness short-circuit — not a separate threat-register ID; WARNING only |
| WR-01 | `20-REVIEW-DISPOSITION.md` | Ops honesty for future path (A) | Out of phase-20 ship scope; Phase 21 / path-(A) flip note — not a registered threat |

No SUMMARY.md `## Threat Flags` section was present for either plan.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open (blocking) | Open (non-blocking) | Run By |
|------------|---------------|--------|-----------------|---------------------|--------|
| 2026-10-16 | 9 | 9 | 0 | 0 | verify-work → secure-phase L1 (gsd-security-auditor) |
| 2026-10-16 | 9 | 9 | 0 | 0 | /gsd-secure-phase 20 re-audit — L1 short-circuit (threats_open: 0 · register at plan time · ASVS 1); evidence re-grepped |

### Security Audit 2026-10-16 (re-run)

| Metric | Count |
|--------|-------|
| Threats found | 9 |
| Closed | 9 |
| Open | 0 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Verdict:** SECURED
**Approval:** verified 2026-10-16
