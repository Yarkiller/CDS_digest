# Phase 21 — SMTP Client Capability Coverage

**Sealed for:** MAIL-01 live SMTP digest delivery  
**Adapter:** `backend/src/backend/infrastructure/smtp_mailer.py` (`SmtpMailer`)  
**Transport:** Python stdlib `smtplib` + `email.message.EmailMessage` + `ssl`  
**Assumption-delta:** **Add-alongside** — keep `StubMailer` as default/`MAILER=stub` and unit double; introduce real `SmtpMailer` behind the same `Mailer` port. Do **not** promote stub away or replace the port. `resolve_mailer(settings)` selects variant; incomplete `MAILER=smtp` fails fast (`ConfigurationError`, D-16).

| capability | decision | reason |
|---|---|---|
| Construct client | **INTEGRATE** | `smtplib.SMTP(host, port, timeout=connect_timeout)` — Default path for `SMTP_TLS_MODE=starttls` / `none` (D-13); connect timeout from Settings (D-14, ~10s) |
| Implicit TLS client | **INTEGRATE** | `smtplib.SMTP_SSL(host, port, timeout=…, context=…)` — Only when `SMTP_TLS_MODE=ssl` (ops override; typically port 465) |
| EHLO / capability probe | **INTEGRATE** | implicit via `SMTP` context / `starttls` — Required before STARTTLS; rely on stdlib |
| STARTTLS | **INTEGRATE** | `smtp.starttls(context=ssl.create_default_context())` — Default TLS posture (D-13); never plaintext-downgrade after TLS failure |
| Authenticate | **INTEGRATE** | `smtp.login(user, password)` — Corporate relay auth; credentials from Settings primitives only (MAIL-05) |
| Build MIME | **INTEGRATE** | `EmailMessage` + `set_content` / `add_alternative` — text + optional HTML from use-case bodies |
| Address headers | **INTEGRATE** | `msg["From"]`, `msg["To"]`, `msg["Subject"]` — One `To` per message (D-05); From from `SMTP_FROM` (+ optional display name) |
| Send | **INTEGRATE** | `smtp.send_message(msg)` — Per-recipient send loop; per-send timeout via client/socket policy (D-14, ~30s) |
| Quit / close | **INTEGRATE** | `with SMTP(…) as smtp:` / `quit` — Context manager preferred; ensure connection closed between recipients or reuse one session per discretionary design if timeouts still bound |
| `sendmail` raw API | **OPT-OUT** | `smtp.sendmail` — Prefer `send_message` so MIME headers stay consistent |
| `noop` / `rset` / `vrfy` / `expn` | **OPT-OUT** | diagnostic SMTP verbs — Not required for digest delivery; avoid relay probing surface |
| `auth` mechanisms beyond login | **OPT-OUT** | `auth` / XOAUTH2 — Corporate relay contract is user/pass via `SMTP_USER`/`SMTP_PASS` |
| LMTP | **OPT-OUT** | `smtplib.LMTP` — Digest uses SMTP relay only |
| Async SMTP | **OPT-OUT** | `aiosmtplib` — Sync `Mailer` port; zero new packages (RESEARCH) |
| Debug logging of full transcript | **OPT-OUT** | `smtp.set_debuglevel` — Risk of credential/body leakage (T-21 credential disclosure); structured app logs without passwords |
| Shared Bcc / multi-To blast | **OPT-OUT** | multi-recipient headers — Forbidden by D-05 (privacy + honest N/M) |

## Schema gate

No `supabase/migrations` changes in this phase — `p_recipient_count` already exists (005/006). Skip schema push.

## Package legitimacy

Zero new runtime packages — stdlib only. `T-21-SC` remains documentary (no install checkpoint).
