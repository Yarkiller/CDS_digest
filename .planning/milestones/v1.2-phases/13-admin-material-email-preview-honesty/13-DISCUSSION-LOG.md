# Phase 13: Admin material & email preview honesty - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-02
**Phase:** 13-Admin material & email preview honesty
**Areas discussed:** Material preview payload & layout, Email HTML fidelity, Interstitial paragraph contract, test-header cleanup scope

---

## Material preview payload & layout

| Option | Description | Selected |
|--------|-------------|----------|
| Enrich shortlist GET | Full fields on AdminShortlistItem; one port | ✓ |
| Fetch on open | Separate material detail request | |
| You decide | | |

**User's choice:** Enrich GET — body_markdown, provenance_label, slug, reading_minutes (+ later char_count, word_count); update FIX-01-LOCK; test_admin_shortlist_returns_full_items.
**Notes:** Parity with email needing full bodies; ≤5×~30KB OK; avoid new admin material endpoint.

| Option | Description | Selected |
|--------|-------------|----------|
| Full markdown in modal | react-markdown + sanitize | ✓ |
| Plain/preformatted | Source review | |
| Excerpt + link | Weak inspect | |

| Option | Description | Selected |
|--------|-------------|----------|
| Counts only | chars/words | |
| reading_minutes only | | |
| Both | counts + minutes | ✓ |

**User's choice:** Full markdown + both counts and reading_minutes; compact counts row; reader link complementary.

| Option | Description | Selected |
|--------|-------------|----------|
| Meta row under title | title → provenance → counts → body → link | ✓ |
| Footer only | | |
| Honest empty | «Текст материала недоступен» | ✓ |
| Fail closed / toast | | |

**User's choice:** Meta row + honest empty (no toast).

---

## Email HTML fidelity

| Option | Description | Selected |
|--------|-------------|----------|
| Backend html field | Shared render_email_html + iframe | ✓ |
| Structured DTO + FE HTML | Drift risk vs send | |
| Upgrade plain body only | Weak vs UAT | |

**User's choice:** Backend HTML; sandboxed iframe; parity test with send.

| Option | Description | Selected |
|--------|-------------|----------|
| dek only | Omit if empty | ✓ |
| First N of body | | |
| Full body in email | | |
| Public reader URL per material | site_url/materials/slug | ✓ |
| Issue URL only / both | | |

**User's choice:** dek + Читать → reader URL; no issue link in preview.

| Option | Description | Selected |
|--------|-------------|----------|
| Keep POST /admin/shortlist/preview | Additive html | ✓ |
| New GET by batch | | |
| Keep body + html | | ✓ |
| Replace body with html | | |

**User's choice:** Keep POST; keep both plain body and html; UI uses iframe only.

---

## Interstitial paragraph contract

| Option | Description | Selected |
|--------|-------------|----------|
| Split \n\n → \<p\>, \n → \<br\> | | ✓ |
| white-space: pre-wrap | | |
| Markdown-lite | Scope creep | |

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve \n\n in plain body | | ✓ |
| Normalize plain body | | |
| Outer trim only | | ✓ |
| No trim | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Escape then structure | html.escape | ✓ |
| No escape | | |
| Light FE hint | «Пустая строка = новый абзац» | ✓ |
| Behavior only / defer hint | | |

**User's choice:** escape + p/br; preserve plain whitespace after outer strip; light hint under textarea.

---

## test-header cleanup scope

| Option | Description | Selected |
|--------|-------------|----------|
| Data + regression assert | No runtime strip | ✓ |
| Data cleanup only | | |
| Runtime strip | Rejected — masks root cause | |

| Option | Description | Selected |
|--------|-------------|----------|
| Closed list of three tokens | | ✓ |
| Broader chrome patterns | | |
| Migration + runbook | Operator apply on VM | ✓ |
| Runbook-only / mocks-only | | |

| Option | Description | Selected |
|--------|-------------|----------|
| Admin preview surfaces only | | ✓ |
| Also reader pages | Deferred unless UAT | |
| Case-insensitive shared helper | | ✓ |
| Case-sensitive | | |

**User's choice:** Fix data + asserts; closed ban list; migration 010-style + runbook; admin surfaces; case-insensitive FORBIDDEN_LOWER helper synced Python↔TS.

---

## Claude's Discretion

- Exact RU microcopy for counts / empty body
- fingerprint on API vs FE-only
- Exact migration number after root-cause
- char/word computation approach
- iframe sandbox attribute details
- recipient_count on preview DTO (optional)

## Deferred Ideas

- Markdown toolbar / live preview for connecting text
- Reader-surface ban asserts if UAT finds leaks
- Broader seed-chrome ban list
- ADUX-05/06, CLI debug, PIPE-01, live SMTP (roadmap phases)
