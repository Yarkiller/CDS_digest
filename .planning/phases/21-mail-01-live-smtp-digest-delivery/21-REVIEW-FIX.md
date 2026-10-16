---
phase: 21-mail-01-live-smtp-digest-delivery
fixed_at: 2026-10-16T15:30:00Z
review_path: .planning/phases/21-mail-01-live-smtp-digest-delivery/21-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 21: Code Review Fix Report

**Fixed at:** 2026-10-16T15:30:00Z
**Source review:** `.planning/phases/21-mail-01-live-smtp-digest-delivery/21-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 6
- Fixed: 6
- Skipped: 0

**TDD / verification note:** every behaviour change was driven Red→Green. A failing test was
written first and observed to fail for the expected reason (not a syntax/collection error), then
the minimal production change was applied and the test observed to pass. `uv run pytest tests/unit -q`
run in the **main checkout** (worktrees disabled for this run) is green: **919 passed** (baseline 890).

## Fixed Issues

### CR-01: Malformed recipient email escapes `SmtpMailer` → HTTP 500 after a publish (D-88 / MAIL-04 / D-02)

**Files modified:** `backend/src/backend/infrastructure/smtp_mailer.py`, `backend/src/backend/domain/recipient.py`, `tests/unit/test_smtp_mailer.py`, `tests/unit/test_recipient_email.py` (new)
**Commit:** `acac872`
**Applied fix:** `_build_message` now runs inside the per-recipient `try:` and `ValueError` is added to the contained failure set, so a CR/LF `To` counts as one failed recipient (D-08 consecutive semantics) instead of escaping the adapter. `is_usable_email` now rejects CR/LF/control characters, surrounding and embedded whitespace, commas, and anything other than exactly one `@`, so malformed rows are excluded + logged at the audience boundary (D-02).
**Red evidence:** new `is_usable_email` rejection cases (11) failed and the mailer test raised the raw `ValueError`; Green after the fix.

### WR-01: `_apply_send_timeout` could raise an unmapped `OSError` (MAIL-04)

**Files modified:** `backend/src/backend/infrastructure/smtp_mailer.py`, `tests/unit/test_smtp_mailer.py`
**Commit:** `0e6cd3f`
**Applied fix:** the D-14 per-send timeout is applied inside `_open_connection` (after login, before returning) and therefore covered by the same `except (smtplib.SMTPException, OSError, TimeoutError) -> MailDeliveryError` mapping; the setup failure also best-effort closes the half-open connection. The call was removed from `send_digest`. `test_smtp_mailer_applies_send_timeout_to_socket` still pins the D-14 socket behaviour.
**Red evidence:** `OSError` from `socket.settimeout()` propagated raw (`FAILED ... OSError: bad file descriptor`); Green after the fix.

### WR-02: `list_digest_recipients` unbounded select could silently truncate the audience (D-01)

**Files modified:** `supabase-integration/src/supabase_integration/profile_repository.py`, `tests/unit/test_supabase_digest_recipients_contract.py`
**Commit:** `8cab69a`
**Applied fix:** the profiles select is paged with `.range(start, start + 999)` (page size 1000) in a new `_list_all_profile_rows` helper until a short page is returned, so the PostgREST `max-rows` cap cannot under-count planned M. SDK failures still map to `PersistenceError` at the boundary.
**Red evidence:** the fake client now mirrors the server-side max-rows cap; the 1500-row paging test saw only 1000 recipients (`assert 1000 == 1500`) before the fix, and the recorded ranges were `[]`; Green after the fix (`client.ranges == [(0, 999), (1000, 1999)]`).

### IN-01: Unknown `delivery_status` token rendered as a delivery claim (D-09)

**Files modified:** `backend/src/backend/application/use_cases/send_digest.py`, `tests/unit/test_send_digest.py`
**Commit:** `5c3dca3`
**Applied fix:** `delivery_status` is validated against `{"stubbed", "sent", "partial", "failed"}` (new module constant `_ALLOWED_DELIVERY_STATUSES`); an unknown/absent token is reported conservatively as `failed` before the message is composed.
**Red evidence:** `teleported` passed through verbatim (`assert 'teleported' == 'failed'`); Green after the fix.

### IN-02: `InMemoryDigestPublisher.claim_and_publish` drifted from the port signature

**Files modified:** `backend/src/backend/tests_support/in_memory.py`, `tests/unit/test_send_digest.py`
**Commit:** `73d4d0f`
**Applied fix:** the double now declares `recipient_count: int = 0`, matching `DigestPublisher`; the `None` sentinel and the constructor-only `_recipient_count` defaulting were removed from the port-shaped parameter.
**Red evidence:** a signature-introspection test saw `double_default is None` vs the port's `0`; Green after the fix.

### IN-03: `SMTP_PORT=0` passed the D-16 fail-fast completeness check

**Files modified:** `backend/src/backend/composition/settings.py`, `tests/unit/test_stub_mailer.py`
**Commit:** `00aae2a`
**Applied fix:** `_read_smtp_port` now requires `1 <= port <= 65535` and raises `ConfigurationError` otherwise, so a non-positive/out-of-range port fails fast at startup instead of hot-looping at connect.
**Red evidence:** `SMTP_PORT` of `0`, `65536`, `70000` did not raise (`DID NOT RAISE ConfigurationError`); Green after the fix. In-range values `1`/`587`/`65535` are still accepted.

## Skipped Issues

None — all six in-scope findings were fixed.

---

_Fixed: 2026-10-16T15:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
