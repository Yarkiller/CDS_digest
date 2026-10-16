---
status: testing
phase: 21-mail-01-live-smtp-digest-delivery
source: [21-VERIFICATION.md]
started: 2026-10-16T15:30:02Z
updated: 2026-10-16T15:30:02Z
---

## Current Test

number: 1
name: Ack prohibitions: honest copy + no org-wide delivery claim (message / API / SPA banner)
expected: |
  Server-composed two-sentence copy «Доставлено N из M» / «Письма не доставлены» /
  «Получателей нет (0 из 0)» / stub line; no «всей организации»-style claim anywhere.
awaiting: user response

## Tests

### 1. Ack prohibitions: honest copy + no org-wide delivery claim (message / API / SPA banner)
expected: Server-composed two-sentence copy «Доставлено N из M» / «Письма не доставлены» / «Получателей нет (0 из 0)» / stub line; no «всей организации»-style claim anywhere.
result: [pending]

### 2. Ack prohibitions: D-88 containment + no 5xx-after-publish + PRESERVE tripwire
expected: Mail error after publish still returns HTTP 200 success with the issue persisted; `test_send_audit_failure_after_publish_still_returns_success` present and green; `test_send_mail_failure_after_publish_still_returns_success` green.
result: [pending]

### 3. Ack prohibitions: one-message-per-recipient privacy, no Bcc blast, no smtplib leakage, no os.environ in adapter
expected: `SmtpMailer` sets a single `To` per `EmailMessage` and no Bcc; `smtplib` imported only in infrastructure; `smtp_mailer.py` contains no `os.environ`/`getenv`.
result: [pending]

### 4. Ack prohibitions: D-16 fail-fast, no silent stub fallback, no update_delivery, no signup-via-Mailer, StubMailer preserved
expected: `resolve_mailer` raises `ConfigurationError` on incomplete/out-of-range `SMTP_*`; a misconfigured smtp mode never returns `StubMailer`; no `DigestPublisher.update_delivery` method; no `Mailer`/`send_digest` under `web/src`; `StubMailer` class intact.
result: [pending]

### 5. Ack prohibition: runbook does not claim Phase 20 criterion-4 relay proof complete
expected: Runbook §4.1.3 and the §4e block state the live corporate-relay smoke is an inherited ops gap (D-15); `GOTRUE_SMTP_*` lane stays separate from digest `SMTP_*`.
result: [pending]

### 6. Live corporate-relay digest smoke (external service integration / ops)
expected: With `MAILER=smtp` + complete `SMTP_*` on the VM, one real weekly digest is accepted by the corporate relay and delivered to the `profiles`-derived audience; `recipient_count=M` and `delivered_count=N` match the mailed set.
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
