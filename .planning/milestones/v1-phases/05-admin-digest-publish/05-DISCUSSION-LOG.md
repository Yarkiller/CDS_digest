# Phase 5: Admin Digest Publish - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-21
**Phase:** 5-Admin Digest Publish
**Areas discussed:** Admin gate & shell entry, Shortlist source & scoring honesty, Triage & batch selection, Preview → send → email reality

---

## Admin gate & shell entry

| Option | Description | Selected |
|--------|-------------|----------|
| profiles.role = admin only | Single enum; no delegate flag | ✓ |
| admin + separate delegate | Closer to «CDS / делегат» wording | |
| You decide | Claude locks simple v1 rule | |

**User's choice:** admin only

| Option | Description | Selected |
|--------|-------------|----------|
| Hide nav + 403 page | Deep-link → rights page + На выпуск | ✓ |
| Show nav for everyone | Discoverable but noisy | |
| Hide nav + soft redirect | No 403 page | |

**User's choice:** Hide + 403 page

| Option | Description | Selected |
|--------|-------------|----------|
| GET /me role DTO | Same session bootstrap | ✓ |
| Separate capabilities endpoint | Extra round-trip | |
| JWT claim only | Drift risk vs profiles.role | |

**User's choice:** GET /me

| Option | Description | Selected |
|--------|-------------|----------|
| Pytest + Playwright | API 403 + SPA 403 page | ✓ |
| Pytest only | | |
| Playwright only | | |

**User's choice:** Pytest + Playwright

---

## Shortlist source & scoring honesty

| Option | Description | Selected |
|--------|-------------|----------|
| Seeded batch in DB | No live ranking in Phase 5 | ✓ (with honesty freeform) |
| On-read ranking in FastAPI | Invents scoring engine | |
| You decide | | |

**User's choice:** Seeded batch + honesty rules: UI unlabeled; runbook/docs say v1=seed / live=PIPE-01+; seed file comment «demo batch для Phase 5»; future pipeline keeps UI.

| Option | Description | Selected |
|--------|-------------|----------|
| Score + ≥2 factors | Else обоснование недоступно | ✓ |
| Factors only | | |
| Score + expand | | |

**User's choice:** Score + factors

| Option | Description | Selected |
|--------|-------------|----------|
| Pipeline empty copy from error_handling | «пайплайн не вернул» | |
| Softer empty | Кандидатов пока нет + Обновить | ✓ |
| You decide | | |

**User's choice:** Softer empty (no pipeline wording)

| Option | Description | Selected |
|--------|-------------|----------|
| Latest unsent batch | | ✓ |
| Week picker | | |
| You decide | | |

**User's choice:** Latest unsent

---

## Triage & batch selection

| Option | Description | Selected |
|--------|-------------|----------|
| decision enum drives send | approved/rejected/pending | ✓ |
| Separate include checkbox | | |
| Approve=include Reject clears | Weaker persistence | |

**User's choice:** decision enum

| Option | Description | Selected |
|--------|-------------|----------|
| Checkboxes = batch Approve/Reject only | Send pool = approved ready | ✓ |
| Dual-purpose checkboxes | | |
| No checkboxes | | |

**User's choice:** Batch action only

| Option | Description | Selected |
|--------|-------------|----------|
| Select-all/top-N update checkboxes only | Then Approve/Reject | ✓ |
| One-shot set decisions | | |
| Select-all only (drop top-N) | | |

**User's choice:** Two-step checkboxes

| Option | Description | Selected |
|--------|-------------|----------|
| Approve drafts OK; Send blocks approved drafts | | ✓ |
| Block Approve on drafts | | |
| Auto-skip drafts in select-all | | |

**User's choice:** Approve OK / Send blocks

---

## Preview → send → email reality

| Option | Description | Selected |
|--------|-------------|----------|
| Mandatory preview this session | Failed preview never unlocks | ✓ |
| Preview optional | | |
| Preview once per batch (server flag) | | |

**User's choice:** Mandatory session preview

| Option | Description | Selected |
|--------|-------------|----------|
| Stub mailer | | ✓ (detailed freeform) |
| Real SMTP in Phase 5 | | |
| Preview-only defer send | | |

**User's choice:** Mailer Protocol; StubMailer v1; SmtpMailer NotImplemented; MAILER=stub; smtp fails startup; persist stubbed + audit; UI «Отправка записана»; runbook §4e Phase 6+ SMTP.

| Option | Description | Selected |
|--------|-------------|----------|
| Publish new digest_issues on send | | ✓ |
| Only mark batch sent_at | | |
| You decide | | |

**User's choice:** New published issue

| Option | Description | Selected |
|--------|-------------|----------|
| Hard block already sent | Уже отправлено | ✓ |
| Explicit re-send confirm | | |
| Re-open batch | | |

**User's choice:** Hard block

---

## Claude's Discretion

- Admin URL path naming; preview modal vs page polish; confirm-send copy; default top-N; audit_log storage shape; exact `/me` field naming for role.

## Deferred Ideas

- PIPE-01 YAML pipeline UI / live ranking
- Real SMTP (Phase 6+)
- Week picker; re-send; separate delegate role
