---
phase: 21-mail-01-live-smtp-digest-delivery
reviewed: 2026-10-16T15:05:00Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - backend/src/backend/domain/recipient.py
  - backend/src/backend/domain/errors.py
  - backend/src/backend/application/ports/mailer.py
  - backend/src/backend/application/ports/profile_repository.py
  - backend/src/backend/application/ports/digest_publisher.py
  - backend/src/backend/application/use_cases/send_digest.py
  - backend/src/backend/infrastructure/stub_mailer.py
  - backend/src/backend/infrastructure/smtp_mailer.py
  - backend/src/backend/composition/settings.py
  - backend/src/backend/composition/config_error.py
  - backend/src/backend/composition/mailer_factory.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/tests_support/in_memory.py
  - supabase-integration/src/supabase_integration/profile_repository.py
  - supabase-integration/src/supabase_integration/digest_publisher.py
  - web/src/services/adminApi.js
  - web/src/pages/AdminDigestPage.jsx
  - docs/agents/local-platform-runbook.md
findings:
  critical: 1
  warning: 2
  info: 3
  total: 6
status: issues_found
---

# Phase 21: Code Review Report

**Reviewed:** 2026-10-16T15:05:00Z
**Depth:** standard
**Files Reviewed:** 19
**Status:** issues_found

## Summary

Adversarial review of the MAIL-01 live-SMTP digest lane at `standard` depth. The locked contracts were checked against the on-disk source: D-16 fail-fast resolve, MAIL-05 env-agnostic adapters, D-05 one-message-per-recipient, D-07 `sent`/`partial`/`failed`, D-08 consecutive-failure stop, D-10/D-11 additive `delivered_count` + HTTP-200 containment, and D-01/D-02/D-03 audience resolution from `profiles`.

Most of the contract holds and is honestly implemented:

- **D-16** is enforced twice (`resolve_mailer` completeness + `_build_smtp_mailer` TLS-mode check); incomplete `SMTP_*` raises `ConfigurationError`, never a silent `StubMailer`. `Settings.smtp_port` is `int | None` so "unset" stays distinguishable.
- **MAIL-05** holds: `smtp_mailer.py` imports no `os`, and only `Settings.from_env` reads `SMTP_*`. `smtp_pass` is `field(repr=False)`.
- **D-05** is correct: one `EmailMessage` per recipient with a single `To`; no Bcc.
- **D-11** containment in the route is correct — a contained mail partial/failure after `claim_and_publish` stays HTTP 200 with honest `recipient_count`/`delivered_count`.

One BLOCKER was reproduced live against the adapter: a recipient email that passes `is_usable_email` but contains a CR/LF raises an unguarded `ValueError` inside `_build_message`, escapes `SmtpMailer.send_digest`, is not caught by `send_digest`, and therefore 500s a request whose digest has **already been published** — a direct violation of D-88 and MAIL-04. Two Warnings and three Info items follow.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Malformed recipient email raises an unguarded `ValueError` inside `SmtpMailer` → HTTP 500 after a successful publish (D-88 / MAIL-04 / D-02)

**File:** `backend/src/backend/infrastructure/smtp_mailer.py:144` (with `:235`), `backend/src/backend/domain/recipient.py:11-19`, `backend/src/backend/application/use_cases/send_digest.py:225`

**Issue:** The per-recipient transport guard wraps only `connection.send_message(message)`:

```text
143            for recipient in audience:
144                message = self._build_message(      # <-- NOT inside the try
...
149                try:
150                    connection.send_message(message)
151                except (smtplib.SMTPException, OSError, TimeoutError) as exc:
```

`_build_message` sets `message["To"] = recipient.email` (`:235`). If the address contains a CR/LF, the stdlib raises `ValueError("Header values may not contain linefeed or carriage return characters")` at that line — *outside* the per-recipient `except`, so it propagates out of `SmtpMailer.send_digest`. The use case only contains `MailDeliveryError`/`PersistenceError` (`send_digest.py:225`), so the `ValueError` reaches the route and becomes a **500**.

The audience filter does not prevent this. `is_usable_email` only checks for `@` plus a non-empty local/domain part, so a CR/LF address is treated as *usable* and handed straight to the adapter — defeating D-02's "malformed emails are excluded and logged" guard. Reproduced live against the on-disk code:

```text
uv run python -c "..."
is_usable_email('victim@x.ru\r\nBcc: attacker@y.ru') -> True
SmtpMailer.send_digest(... recipients=[Recipient('victim@x.ru\r\nBcc: attacker@y.ru')])
  -> ESCAPED ValueError('Header values may not contain linefeed or carriage return characters')
```

Impact chain: `claim_and_publish` succeeds (batch is stamped `sent_at`, issue is published) → `SmtpMailer.send_digest` raises `ValueError` → use case does not catch it → `POST /admin/shortlist/send` returns **500**. The admin sees a failure for a digest that is already published and cannot retry (the batch is now "already sent" → 409), and the audit ping (`payload` inside `send_digest`) is never written. This is exactly the D-88 invariant the phase was built to preserve.

> The same predicate weakness also admits addresses like `"a@b.ru, c@d.ru"` — the stdlib accepts them, producing a single message with two `To` addresses, which weakens D-05's "no cross-employee leakage".

**Fix:** Two layers, matching the port's "adapters never let a transport/domain error escape" rule.

1. Move `_build_message` inside the per-recipient guard and treat a malformed address as one failed recipient (D-08 streak semantics), not a run-killer:

```python
def send_digest(self, *, batch_id, issue_url, subject, body_text,
                recipient_count, recipients=(), body_html=None):
    audience = list(recipients)
    if not audience:
        ...
    connection = self._open_connection()
    delivered = 0
    consecutive_failures = 0
    stop_reason = None
    try:
        self._apply_send_timeout(connection)
        for recipient in audience:
            try:
                message = self._build_message(
                    recipient, subject=subject, body_text=body_text, body_html=body_html
                )
                connection.send_message(message)
            except (smtplib.SMTPException, OSError, TimeoutError, ValueError) as exc:
                consecutive_failures += 1
                logger.warning("smtp_mailer per-recipient failure ... error=%s", exc)
                if consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
                    stop_reason = STOP_REASON_CONSECUTIVE_FAILURES
                    break
                continue
            delivered += 1
            consecutive_failures = 0
    finally:
        self._close(connection)
```

2. Harden the audience predicate so malformed addresses are filtered+logged at the boundary (D-02) instead of reaching the adapter: reject `\r`/`\n`/control characters, surrounding whitespace, embedded whitespace/commas, and require exactly one `@` — e.g. `if any(ch in email for ch in "\r\n") or email.strip() != email or email.count("@") != 1: return False`.

## Warnings

### WR-01: `_apply_send_timeout` can raise `OSError` that escapes the adapter (same 500-after-publish class as CR-01)

**File:** `backend/src/backend/infrastructure/smtp_mailer.py:142`, `:209-213`

**Issue:** `_apply_send_timeout(connection)` is called at the top of the `try:` that is guarded only by `finally:` — it has no `except`. It calls `sock.settimeout(self._send_timeout)` (`:213`); `socket.settimeout()` can raise `OSError` on a stale/closed fd. Such an `OSError` is neither mapped to `MailDeliveryError` (MAIL-04 requires all transport errors to map at the boundary) nor caught by the use case, so it would 500 an already-published digest for the same reason as CR-01.

**Fix:** Fold the timeout application into the connection-setup guard so it is mapped exactly like connect/login:

```python
except (smtplib.SMTPException, OSError, TimeoutError) as exc:
    raise MailDeliveryError(
        f"smtp connect/login failed for {self._host}:{self._port}: {exc}"
    ) from exc
```

i.e. apply the timeout inside `_open_connection` (after login, before `return connection`), or wrap the call in the same `except (smtplib.SMTPException, OSError, TimeoutError)` → `MailDeliveryError` mapping.

### WR-02: `list_digest_recipients` reads the audience in a single unbounded select (silent truncation vs D-01)

**File:** `supabase-integration/src/supabase_integration/profile_repository.py:98-100`

**Issue:** The live adapter issues `.select("id,email,display_name").execute()` with no `.range()`/paging loop. PostgREST applies a server-side `max-rows` cap (Supabase's default is 1000); when the `profiles` table exceeds that, the adapter silently returns only the first page. That violates D-01 ("**all** `profiles` rows with a usable email"), silently under-delivers the digest, and makes the planned M stamped on the batch (`p_recipient_count`) under-report the true audience — the exact under-count the phase's honesty decision was meant to prevent.

**Fix:** Page the select until a short page is returned, e.g.:

```python
page_size = 1000
rows: list[dict[str, Any]] = []
start = 0
while True:
    result = (
        self._client.table("profiles")
        .select("id,email,display_name")
        .range(start, start + page_size - 1)
        .execute()
    )
    page = getattr(result, "data", None) or []
    rows.extend(page)
    if len(page) < page_size:
        break
    start += page_size
```

## Info

### IN-01: `delivery_status` from the mailer is trusted verbatim; an unknown token is rendered as a successful delivery

**File:** `backend/src/backend/application/use_cases/send_digest.py:232-241`

**Issue:** `delivery_status = str(mail_result.get("delivery_status") or "sent")` accepts any string. `_compose_delivery_message` only special-cases `stubbed`/`partial`/`failed`; any other value (a typo, a future adapter token) falls through to the final branch and is reported to the admin as «Доставлено N из M» — i.e. an unknown status is silently promoted to a delivery claim (D-09 "never claim organisation-wide delivery").

**Fix:** Validate against the documented set and default conservatively, e.g. `if delivery_status not in {"stubbed", "sent", "partial", "failed"}: delivery_status = "failed"` (or map to a neutral unknown status) before composing the message.

### IN-02: `InMemoryDigestPublisher.claim_and_publish` signature drifts from the `DigestPublisher` port

**File:** `backend/src/backend/tests_support/in_memory.py:569` vs `backend/src/backend/application/ports/digest_publisher.py:35`

**Issue:** The port declares `recipient_count: int = 0`; the in-memory double declares `recipient_count: int | None = None` (and adds a private `delivery_status` default). Structural typing does not police this, so the fake can silently accept a `None` the real adapter would not, hiding a call-site regression.

**Fix:** Align the double with the port signature (`recipient_count: int = 0`) and keep any test-only defaulting out of the port-shaped parameter.

### IN-03: `SMTP_PORT=0` passes the D-16 fail-fast completeness check

**File:** `backend/src/backend/composition/settings.py:16-22`, `backend/src/backend/composition/mailer_factory.py:41-47`

**Issue:** `_read_smtp_port` accepts `"0"` (`isdigit()` is true), and the completeness check `getattr(settings, attr) in (None, "")` does not flag the integer `0`, so `SMTP_PORT=0` is treated as configured. Startup succeeds and every message then fails at connect (`MailDeliveryError`), so D-16's "refuse to start on a bad config" intent is bypassed for an invalid port.

**Fix:** Reject non-positive/out-of-range ports in `_read_smtp_port` (`if not (1 <= port <= 65535): raise ConfigurationError(...)`).

---

_Reviewed: 2026-10-16T15:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
