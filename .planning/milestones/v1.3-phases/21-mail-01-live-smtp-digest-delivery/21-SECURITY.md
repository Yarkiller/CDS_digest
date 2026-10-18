---
phase: "21"
slug: "mail-01-live-smtp-digest-delivery"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-18"
---

# Phase 21 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Admin SPA → FastAPI send | Digest send only via Bearer admin | JWT / role |
| FastAPI → Mailer port | Stub / SMTP / Haskimail (ADR-0005) | Recipients, subject, HTML body |
| Mailer → relay / Haskimail API | Credentials from Settings only | SMTP_* or HASKIMAIL_* |
| FastAPI → profiles (service_role) | Audience list; no public list endpoint | Usable emails only |
| Adapter logs → operators | Counts / batch ids only | Never passwords or API keys |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-21-01 | Denial of Service / Elevation | `send_digest` mail catch | high | mitigate | Catch `MailDeliveryError`/`PersistenceError` after claim — published digests never 500 | closed |
| T-21-02 | Information Disclosure | `list_digest_recipients` | medium | mitigate | service_role-only repo; no public list endpoint; exclude malformed | closed |
| T-21-03 | Information Disclosure | Mailer recipients contract | medium | mitigate | Per-recipient sequence; one `To`; no shared Bcc | closed |
| T-21-04 | Information Disclosure | Settings / adapter logging | high | mitigate | `smtp_pass` / `haskimail_api_key` `repr=False`; count-only logs | closed |
| T-21-05 | Spoofing / Tampering | `resolve_mailer` | high | mitigate | `ConfigurationError` on incomplete smtp/haskimail — no silent stub | closed |
| T-21-06 | Denial of Service | timeouts + consecutive limit | medium | mitigate | Fixed timeouts; `CONSECUTIVE_FAILURE_LIMIT = 3` | closed |
| T-21-07 | Information Disclosure | per-recipient To | medium | mitigate | One address per message (smtp + haskimail) | closed |
| T-21-08 | Spoofing (message integrity) | SendDigestResponse / SPA banner | medium | mitigate | Server composes D-09/D-12 copy; SPA shows server message | closed |
| T-21-09 | Information Disclosure | runbook | low | mitigate | Env var *names* only; never commit secrets | closed |
| T-21-10 | Elevation of Privilege | `post_shortlist_send` | medium | mitigate | `Depends(require_admin)`; no public send route | closed |
| T-21-SC | Tampering | npm/pip installs | high | accept | See Accepted Risks Log (stdlib SMTP plans + ADR-0005 Haskimail pin) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-21-01 | T-21-SC | Plans 21-01/02/03 accepted zero new packages for the stdlib SMTP path. Post-plan ADR-0005 intentionally adds runtime dep `haskimail>=1.0.0` (`backend/pyproject.toml`) as preferred live transport (`MAILER=haskimail`); `SmtpMailer` remains alternate. Supply-chain posture: vendor SDK trust + version pin; no further transitive mail SDKs without a new phase decision. | plans 21-01/02/03 + ADR-0005 / secure-phase L1 | 2026-10-18 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-18 | 11 | 11 | 0 | /gsd-secure-phase → gsd-security-auditor L1 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-18
