# Phase 21: MAIL-01 live SMTP digest delivery - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-16
**Phase:** 21-MAIL-01 live SMTP digest delivery
**Areas discussed:** Audience from profiles, Send shape & partial failure, Admin response after send, Relay contract & proof gate

---

## Audience from profiles

| Option | Description | Selected |
|--------|-------------|----------|
| All profiles with email | Every registered profile with usable email | ✓ |
| Only confirmed/active | Filter by activity/confirmed flag | |
| By roles | Role allow/deny lists | |
| You decide | Claude picks default | |

**User's choice:** All profiles with email (1)

| Option | Description | Selected |
|--------|-------------|----------|
| Strictly exclude | Drop empty/broken emails from M | ✓ (+ log) |
| Fail before publish | Domain error blocks send | |
| You decide | | |

**User's choice:** Strictly exclude **+ write to log**

| Option | Description | Selected |
|--------|-------------|----------|
| profiles.email only | Sole address source | ✓ |
| To service + Bcc audience | Envelope shape (deferred to send area) | |
| You decide | | |

**User's choice:** profiles.email only

| Option | Description | Selected |
|--------|-------------|----------|
| Publish + mail no-op | M=0 still publishes; honest zero | ✓ |
| Block before publish | | |
| You decide | | |

**User's choice:** Publish + mail no-op

---

## Send shape & partial failure

| Option | Description | Selected |
|--------|-------------|----------|
| Single Bcc message | One SMTP dialog; N binary | |
| One message per recipient | Honest N of M | ✓ |
| You decide | | |

**User's choice:** Per-recipient

| Option | Description | Selected |
|--------|-------------|----------|
| Option (i) minimal | Planned M in batch; N/M in API + pings | ✓ |
| Option (ii) update_delivery | Post-mail DB update | |
| You decide | | |

**User's choice:** Option (i)

| Option | Description | Selected |
|--------|-------------|----------|
| sent / partial / failed (+ stubbed) | Three live statuses | ✓ |
| No partial | sent/failed only | |
| You decide | | |

**User's choice:** Include `partial`

| Option | Description | Selected |
|--------|-------------|----------|
| Continue all | | |
| Stop on first | | |
| Custom | Stop after 3 consecutive failures + event | ✓ |

**User's choice:** Continue unless three consecutive SMTP failures; success resets streak; record in activity event. Confirmed: consecutive = three failed sends in a row across recipients.

---

## Admin response after send

| Option | Description | Selected |
|--------|-------------|----------|
| Always N of M phrase only | | |
| Publish sentence + delivery sentence | | ✓ |
| Keep «Отправка записана» + JSON only | | |
| You decide | | |

**User's choice:** Two sentences (publish separate from mail)

| Option | Description | Selected |
|--------|-------------|----------|
| recipient_count=M + delivered_count=N | | ✓ |
| recipient_count=N only | | |
| You decide | | |

**User's choice:** Two fields

| Option | Description | Selected |
|--------|-------------|----------|
| Always 200 after successful publish | D-88 | ✓ |
| 207/502 on mail fail | | |
| You decide | | |

**User's choice:** Always 200

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit stub wording in message | | ✓ |
| Like live with stubbed status | | |
| Old «Отправка записана» for stub | | |
| You decide | | |

**User's choice:** Explicit stub line, e.g. stub (0 из M)

---

## Relay contract & proof gate

| Option | Description | Selected |
|--------|-------------|----------|
| starttls / 587 default | | ✓ |
| ssl / 465 | | |
| No default — fail-fast | | |
| You decide | | |

**User's choice:** starttls/587 as default

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed timeouts in Settings (~10s connect, ~30s send) | | ✓ |
| Timeouts from env | | |
| Single SMTP_TIMEOUT | | |
| You decide | | |

**User's choice:** Fixed in Settings

| Option | Description | Selected |
|--------|-------------|----------|
| Ship code + MAILER=stub default; proof not merge blocker | | ✓ |
| Block merge until live smoke | | |
| Split 21a/21b plans | | |
| You decide | | |

**User's choice:** Ship with stub default

| Option | Description | Selected |
|--------|-------------|----------|
| Fail-fast on incomplete SMTP_* | | ✓ |
| Silent stub fallback | | |
| You decide | | |

**User's choice:** Fail-fast (HOST/PORT/USER/PASS/FROM required)

---

## Claude's Discretion

- Exact Russian message variants for sent/partial/failed/stub/M=0
- Adapter vs use-case ownership of the consecutive-failure counter (semantics locked)
- `Recipient` DTO vs bare email strings (prefer typed DTO)
- Log field detail for excluded emails; credential redaction

## Deferred Ideas

- Option (ii) `update_delivery`
- Formal relay ADR
- GoTrue path (A) / autoconfirm flip
- SPA authApi confirmation-mailer error mapping
- Bcc single-message send
