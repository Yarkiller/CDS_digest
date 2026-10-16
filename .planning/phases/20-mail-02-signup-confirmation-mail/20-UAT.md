---
status: testing
phase: 20-mail-02-signup-confirmation-mail
source:
  - 20-VERIFICATION.md
started: 2026-10-16T09:05:00Z
updated: 2026-10-16T09:05:00Z
---

## Current Test

number: 1
name: Ack prohibition — signup confirmation never routes through backend Mailer.send_digest
expected: |
  No signup→Mailer wiring; GoTrue owns confirmation (criterion 3).
awaiting: user response

## Tests

### 1. Ack prohibition: signup confirmation never routes through backend Mailer.send_digest
expected: No signup→Mailer wiring; GoTrue owns confirmation (criterion 3).
result: [pending]

### 2. Ack prohibition: Russian post-register success copy never claims a confirmation letter under path (B)
expected: CONFIRM_MESSAGE is «Регистрация завершена. Аккаунт активен — войдите.»; Playwright forbids /письм/i on role=alert.
result: [pending]

### 3. Ack prohibition: tests/auth.spec.js post-register assertions amended/added, not deleted
expected: «shows Логин as shell identity after register» still present; new letter-claim test added.
result: [pending]

### 4. Ack prohibition: tests/unit/test_auth_email_domain.py untouched (D-11 PRESERVE)
expected: No phase edits; pytest -x green (5 passed).
result: [pending]

### 5. Ack prohibition: runbook/UI docs do not claim confirmation mail is delivered under current autoconfirm (B) ship
expected: Runbook §4.1 states path B + criterion-4 gap; no claim of live confirmation delivery.
result: [pending]

### 6. Ack prohibition: g-01-3b-signup-mailer.md closed not deleted; no speculative SMTP secrets / half-enabled GOTRUE_SMTP_* in app code
expected: Debug file tracked with status:resolved; placeholders only in runbook; no new ADR.
result: [pending]

### 7. Optional UAT: open /register once under current autoconfirm and confirm visible copy never promises a letter
expected: Any null-session or success messaging matches honest (B) copy; no «письм» claim.
result: [pending]

## Summary

total: 7
passed: 0
issues: 0
pending: 7
skipped: 0
blocked: 0

## Gaps
