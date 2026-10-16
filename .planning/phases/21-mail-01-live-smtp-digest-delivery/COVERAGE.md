# Phase 21 — SMTP Client Capability Coverage

**Sealed for:** MAIL-01 live SMTP digest delivery  
**Adapter:** `backend/src/backend/infrastructure/smtp_mailer.py` (`SmtpMailer`)  
**Transport:** Python stdlib `smtplib` + `email.message.EmailMessage` + `ssl`  
**Assumption-delta:** **Add-alongside** — keep `StubMailer` as default/`MAILER=stub` and unit double; introduce real `SmtpMailer` behind the same `Mailer` port. Do **not** promote stub away or replace the port. `resolve_mailer(settings)` selects variant; incomplete `MAILER=smtp` fails fast (`ConfigurationError`, D-16).

| Capability | stdlib surface | Decision | Reason |
|------------|----------------|----------|--------|
| Construct client | `smtplib.SMTP(host, port, timeout=connect_timeout)` | **INTEGRATE** | Default path for `SMTP_TLS_MODE=starttls` / `none` (D-13); connect timeout from Settings (D-14, ~10s) |
| Implicit TLS client | `smtplib.SMTP_SSL(host, port, timeout=…, context=…)` | **INTEGRATE** | Only when `SMTP_TLS_MODE=ssl` (ops override; typically port 465) |
| EHLO / capability probe | implicit via `SMTP` context / `starttls` | **INTEGRATE** | Required before STARTTLS; rely on stdlib |
| STARTTLS | `smtp.starttls(context=ssl.create_default_context())` | **INTEGRATE** | Default TLS posture (D-13); never plaintext-downgrade after TLS failure |
| Authenticate | `smtp.login(user, password)` | **INTEGRATE** | Corporate relay auth; credentials from Settings primitives only (MAIL-05) |
| Build MIME | `EmailMessage` + `set_content` / `add_alternative` | **INTEGRATE** | text + optional HTML from use-case bodies |
| Address headers | `msg["From"]`, `msg["To"]`, `msg["Subject"]` | **INTEGRATE** | One `To` per message (D-05); From from `SMTP_FROM` (+ optional display name) |
| Send | `smtp.send_message(msg)` | **INTEGRATE** | Per-recipient send loop; per-send timeout via client/socket policy (D-14, ~30s) |
| Quit / close | `with SMTP(…) as smtp:` / `quit` | **INTEGRATE** | Context manager preferred; ensure connection closed between recipients or reuse one session per discretionary design if timeouts still bound |
| `sendmail` raw API | `smtp.sendmail` | **OPT-OUT** | Prefer `send_message` so MIME headers stay consistent |
| `noop` / `rset` / `vrfy` / `expn` | diagnostic SMTP verbs | **OPT-OUT** | Not required for digest delivery; avoid relay probing surface |
| `auth` mechanisms beyond login | `auth` / XOAUTH2 | **OPT-OUT** | Corporate relay contract is user/pass via `SMTP_USER`/`SMTP_PASS` |
| LMTP | `smtplib.LMTP` | **OPT-OUT** | Digest uses SMTP relay only |
| Async SMTP | `aiosmtplib` | **OPT-OUT** | Sync `Mailer` port; zero new packages (RESEARCH) |
| Debug logging of full transcript | `smtp.set_debuglevel` | **OPT-OUT** | Risk of credential/body leakage (T-21 credential disclosure); structured app logs without passwords |
| Shared Bcc / multi-To blast | multi-recipient headers | **OPT-OUT** | Forbidden by D-05 (privacy + honest N/M) |

## Schema gate

No `supabase/migrations` changes in this phase — `p_recipient_count` already exists (005/006). Skip schema push.

## Package legitimacy

Zero new runtime packages — stdlib only. `T-21-SC` remains documentary (no install checkpoint).
