# Requirements Archive: v1 MVP

**Archived:** 2026-09-22
**Status:** SHIPPED

For current requirements, see `.planning/REQUIREMENTS.md`.

---

# Requirements: Digest CDS

**Defined:** 2026-09-19
**Core Value:** Authorized СВА staff can read a trustworthy weekly issue of prepared articles and influence the next разбор through one honest vote — without treating raw video/transcript as published material.

## v1 Requirements

Requirements for initial release. Each maps to exactly one roadmap phase. Traceability to ingest: `REQ-US-*` in `.planning/intel/requirements.md`.

### Platform & Operability

- [x] **PLAT-01**: Self-hosted Supabase (Postgres + pgvector) is deployed and working with initial schema/RLS applied
- [x] **PLAT-02**: FastAPI (or equivalent HTTP) exposes correct application endpoints with no critical runtime errors
- [x] **PLAT-03**: Frontend connects to Backend; authenticated reads load from the server (not mocks alone)
- [x] **PLAT-04**: Frontend mutations post to the server and persist end-to-end
- [x] **PLAT-05**: Secrets live only in env/Cloud.ru configuration — never committed in source
- [x] **PLAT-06**: CORS is configured correctly for the app and API origins
- [x] **PLAT-07**: Network failures show recoverable UX (banner/toast + Retry); validation errors are inline; errors are logged with request correlation
- [x] **PLAT-08**: Documentation covers architecture, runbooks, and deployment instructions that work for local and Cloud.ru

### Authentication

- [x] **AUTH-01**: User with `@sberbank.ru` / `@omega.sbrf.ru` credentials can sign in and get a session; non-allowed domains are rejected with inline domain message and no session (REQ-US-01)
- [x] **AUTH-02**: After login without returnUrl, user lands on current issue; with returnUrl/deep-link, user returns to original URL (REQ-US-02)
- [x] **AUTH-03**: Access policies enforce auth (RLS and/or middleware); unauthenticated protected routes redirect to login; non-admin admin APIs return 403

### Issue & Archive

- [x] **ISSUE-01**: Authenticated user opens current published issue with cover, period/title, and IssueTOC; empty materials show «выпуск готовится» + CTA (REQ-US-03)
- [x] **ISSUE-02**: Open voting cycle shows EditorialCallout with end date and CTA; closed cycle shows closed messaging without topic-select CTA (REQ-US-04)
- [x] **ISSUE-03**: Material with audit-dek shows 1–2 audit-language sentences under title; missing dek hides stub or uses neutral editorial fallback (REQ-US-05)
- [x] **ISSUE-04**: User can open a past issue from archive; empty archive shows CTA to current issue (REQ-US-28)

### Materials

- [x] **MAT-01**: Opening a material shows prepared article in prose column with section TOC; no raw video/audio/transcript as content (REQ-US-07)
- [x] **MAT-02**: Article from issue/knowledge opens with distinguishable «статья» type; unknown id → «материал не найден» with back nav (REQ-US-08)
- [x] **MAT-03**: Article shows «Статья» badge, provenance, tags when present, and internal related-term links without fabricating missing links (REQ-US-09)

### Voting

- [x] **VOTE-01**: In an open cycle, user confirms exactly one vote; status shows «Ваш голос:» with topic; submit without selection blocked (REQ-US-10)
- [x] **VOTE-02**: Before voting, status is «голос не отдан»; no radio pre-selected; leading topic shown separately (REQ-US-11)
- [x] **VOTE-03**: User can change vote A→B while cycle open; after close, change is rejected with closed-cycle message (REQ-US-12)
- [x] **VOTE-04**: Ballot topics show audit-language description and material count (including «0 материалов») (REQ-US-13)

### Knowledge Base

- [x] **KNOW-01**: Meaningful semantic query returns relevant results or honest empty; whitespace-only query → inline «Введите запрос», no search executed (REQ-US-14)
- [x] **KNOW-02**: Analyst role filter shows only analyst-tagged materials; clearing filter restores unrestricted results keeping query text (REQ-US-15)
- [x] **KNOW-03**: DS search/filter surfaces ML/experiment materials that open to the expected material page (REQ-US-16)
- [x] **KNOW-04**: Analyst search with no matches shows honest empty without substituting irrelevant ML top; reset/refine CTA works (REQ-US-17)

### Razbory

- [x] **RAZB-01**: Razbor list shows name, date, status; empty list shows empty state with CTA (e.g. to voting) (REQ-US-18)
- [x] **RAZB-02**: Published multi-section razbor renders longread with sticky TOC section jump on supported widths (REQ-US-19)
- [x] **RAZB-03**: Attached `.ipynb` can be downloaded/opened; missing notebook disables download with clear caption (REQ-US-20)
- [x] **RAZB-04**: Razbor with metrics shows quality block; overview without metrics is labeled «обзор» (REQ-US-21)

### Admin Digest

- [x] **ADMIN-01**: Admin sees shortlist of up to 5 ranked candidates; non-admin gets HTTP 403; empty shortlist shows refresh empty state (REQ-US-22)
- [x] **ADMIN-02**: Approve includes and persists; Reject excludes and is reflected in UI (REQ-US-23)
- [x] **ADMIN-03**: Shortlist shows draft vs ready per row; send with included draft is blocked (REQ-US-24)
- [x] **ADMIN-04**: Email preview with ≥1 ready selected matches selection; preview failure does not mark send verified (REQ-US-25)
- [x] **ADMIN-05**: Candidate score/factors show ≥2 readable factors when available; else «обоснование недоступно» (REQ-US-26)
- [x] **ADMIN-06**: Select-all / keep top-N updates selection in one operation; manual clear of one item keeps others (REQ-US-27)
- [x] **ADMIN-07**: Confirm send with ≥1 ready initiates send, success UI, archive update; repeat send is controlled; network failure does not mark sent (REQ-US-31)
- [x] **ADMIN-08**: After admin send, digest email contains link to issue/archive item; unauthenticated link → login then returnUrl (REQ-US-06)

## v2 Requirements

Deferred past v1. Tracked but not in current roadmap phases.

### Post-v1 product

- **QUIZ-01**: Published quiz card (5–10 questions) shows score % and activity event; unpublished quiz CTA hidden (REQ-US-29)
- **PIPE-01**: Admin YAML pipeline config UI with validation and 403 for non-admin (REQ-US-30)
- **LEAD-01**: Public leaderboard visible to authenticated users (ADR-0001 — deferred)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Public leaderboard UI in v1 | ADR-0001 locked deferral |
| XP / streaks | Explicitly excluded from v1 journeys |
| Media-as-material (video/audio/transcript pages) | Content contract + NFR-S5 |
| Public foreign LLM / local Whisper on app VM | ADR-0002 |
| Managed Supabase Cloud as primary DB | ADR-0004 |
| Dynamic admin email-domain list | ADR-0003 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLAT-01 | Phase 1 | Complete |
| PLAT-02 | Phase 1 | Complete |
| PLAT-03 | Phase 1 | Complete |
| PLAT-04 | Phase 1 | Complete |
| PLAT-05 | Phase 1 | Complete |
| PLAT-06 | Phase 1 | Complete |
| PLAT-07 | Phase 1 | Complete |
| PLAT-08 | Phase 1 | Complete |
| AUTH-01 | Phase 1 | Complete |
| AUTH-02 | Phase 1 | Complete |
| AUTH-03 | Phase 1 | Complete |
| ISSUE-01 | Phase 2 | Complete |
| ISSUE-02 | Phase 2 | Complete |
| ISSUE-03 | Phase 2 | Complete |
| ISSUE-04 | Phase 2 | Complete |
| MAT-01 | Phase 2 | Complete |
| MAT-02 | Phase 2 | Complete |
| MAT-03 | Phase 2 | Complete |
| VOTE-01 | Phase 3 | Complete |
| VOTE-02 | Phase 3 | Complete |
| VOTE-03 | Phase 3 | Complete |
| VOTE-04 | Phase 3 | Complete |
| KNOW-01 | Phase 4 | Complete |
| KNOW-02 | Phase 4 | Complete |
| KNOW-03 | Phase 4 | Complete |
| KNOW-04 | Phase 4 | Complete |
| RAZB-01 | Phase 4 | Complete |
| RAZB-02 | Phase 4 | Complete |
| RAZB-03 | Phase 4 | Complete |
| RAZB-04 | Phase 4 | Complete |
| ADMIN-01 | Phase 5 | Complete |
| ADMIN-02 | Phase 5 | Complete |
| ADMIN-03 | Phase 5 | Complete |
| ADMIN-04 | Phase 5 | Complete |
| ADMIN-05 | Phase 5 | Complete |
| ADMIN-06 | Phase 5 | Complete |
| ADMIN-07 | Phase 5 | Complete |
| ADMIN-08 | Phase 5 | Complete |

**Coverage:**

- v1 requirements: 39 total
- Mapped to phases: 39
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-19*
*Last updated: 2026-09-19 after roadmap creation*
