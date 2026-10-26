---
milestone: v1
audited: 2026-09-22T03:10:00Z
status: tech_debt
scores:
  requirements: 39/39
  phases: 5/5
  integration: 13/13
  flows: 7/7
nyquist:
  compliant_phases: [04-knowledge-razbory, 05-admin-digest-publish]
  partial_phases: []
  not_validated_phases: [01-platform-foundation-auth, 02-issue-materials-archive, 03-voting-cycle]
  missing_phases: []
  overall: not_validated
gaps:
  requirements: []
  integration: []
  flows: []
tech_debt:
  - phase: 01-platform-foundation-auth
    items:
      - "POST /me/ping is implemented and unit-tested, but the SPA welcome toast only calls GET /me. No page imports postPing."
      - "Logout control: signOut exists in authApi; no shell «Выйти» button (accepted non-blocking 2026-09-19)."
      - "Cloud.ru application VM deploy is docs-only (D-07). PLAT-08 covers the documented path."
      - "VALIDATION.md status is draft — Nyquist not reconciled (run /gsd-validate-phase 1)."
  - phase: 02-issue-materials-archive
    items:
      - "Verification YAML is passed; body status is human_needed. UI-SPEC overflow/plural/mobile backstops remain describe.skip."
      - "Live FE↔BE smoke (VITE_USE_MOCKS=false) not signed off; Playwright gate runs under mocks."
      - "Advisory review: live tag display labels (WR-01) and open-cycle clock vs status-only selection (WR-03)."
      - "REQUIREMENTS ISSUE-01 still says «cover»; ROADMAP/CONTEXT contract is a typography-only hero (D-26)."
      - "VALIDATION.md status is draft — Nyquist not reconciled (run /gsd-validate-phase 2)."
  - phase: 03-voting-cycle
    items:
      - "Verification YAML is passed; body status is human_needed. Visual backstops (overflow, pending flash) unverified."
      - "Live ballot smoke and pg_trigger votes_enforce_open_and_topic reconfirm on the shared VM still need a human pass."
      - "VALIDATION.md status is draft — Nyquist not reconciled (run /gsd-validate-phase 3)."
  - phase: 05-admin-digest-publish
    items:
      - "Verification YAML is passed (8/8); body still human_needed for live re-UAT of G-05-1 and G-05-2."
      - "CR-01: rank rewrite before claim_and_publish_digest is non-atomic. Failed send can leave scrambled ranks. Does not fail the sent_at contract."
      - "WR-01: preview fingerprint ignores block order after unlock (advisory fidelity)."
      - "Outbound mail remains StubMailer until SMTP is configured (intentional)."
---

# Milestone v1 Audit — Digest CDS

**Audited:** 2026-09-22  
**Status:** tech_debt  
**Definition of done:** PROJECT.md v1 criteria (operability, FE↔BE, security, error handling, delivery docs) across phases 1–5.

All five phase `VERIFICATION.md` files exist and record YAML `status: passed`. No requirement is unsatisfied or orphaned. Cross-phase flows trace end to end. Deferred human checks, advisory review items, and unreconciled Nyquist files remain.

Integration check: [Cross-phase integration check](cd7193ef-1f54-43ce-aded-668e59592a8e).

## Requirements

Three sources: `REQUIREMENTS.md` traceability (`[x]` + Complete), each phase `VERIFICATION.md` requirements table, and `requirements-completed` in plan `SUMMARY.md` frontmatter.

| ID | Phase | Verification | Summary | Traceability | Final |
|----|-------|--------------|---------|--------------|-------|
| PLAT-01 … PLAT-08 | 1 | passed / COVERED | listed | [x] | satisfied |
| AUTH-01, AUTH-02 | 1 | passed / COVERED | listed | [x] | satisfied |
| AUTH-03 | 1 → closed in 5 | Phase 1 row PARTIAL (admin 403 deferred); Phase 5 ADMIN-01 + `require_admin` 403 | listed | [x] | satisfied |
| ISSUE-01 … ISSUE-04 | 2 | passed / SATISFIED | listed | [x] | satisfied |
| MAT-01 … MAT-03 | 2 | passed / SATISFIED | listed | [x] | satisfied |
| VOTE-01 … VOTE-04 | 3 | passed / SATISFIED | listed | [x] | satisfied |
| KNOW-01 … KNOW-04 | 4 | passed / SATISFIED | listed | [x] | satisfied |
| RAZB-01 … RAZB-04 | 4 | passed / SATISFIED | listed | [x] | satisfied |
| ADMIN-01 … ADMIN-08 | 5 | passed / SATISFIED | listed | [x] | satisfied |

**Score:** 39/39 satisfied. Unmapped v1 requirements: 0. Orphans: 0.

v2 (QUIZ-01, PIPE-01, LEAD-01) is out of this milestone.

AUTH-03 is satisfied at milestone scope: Phase 1 covered JWT and `RequireAuth`; the deferred non-admin 403 is implemented on admin routes in Phase 5.

VOTE-04 is satisfied as specified (audit-language description and material count, including «0 материалов»). The integration checker flagged a ballot→material deep link as a blocker because the audit prompt asked for that link. The requirement text does not. That link is recorded under tech debt, not as an unsatisfied requirement.

## Phases

| Phase | YAML status | Must-haves | Body note |
|-------|-------------|------------|-----------|
| 01 Platform Foundation & Auth | passed | 5/5 | PASS_WITH_GAPS; deferred items non-blocking |
| 02 Issue, Materials & Archive | passed | 4/5 verified, 1 behavior-unverified | human_needed (visual + live smoke) |
| 03 Voting Cycle | passed | 4/4 | human_needed (visual + live smoke + DDL reconfirm) |
| 04 Knowledge & Razbory | passed | 6/6 | gaps closed (G-04-2) |
| 05 Admin Digest Publish | passed | 8/8 | human_needed (live re-UAT + CR-01 acknowledge) |

**Score:** 5/5 phase verifications passed. No unverified phase.

## Integration

Contract connections traced by the integration checker:

| Connection | Status |
|------------|--------|
| RequireAuth + session → phases 2–5 routes and `returnUrl` | WIRED |
| `contentApi` → issue, material, archive pages | WIRED |
| Voting cycle on current issue → EditorialCallout | WIRED |
| `votingApi` → ballot and vote submit, including closed 409 | WIRED |
| Knowledge hits → `/materials/{slug}` | WIRED |
| Razbor empty CTA → `/voting`; notebook download path | WIRED |
| `require_admin` → admin routes and Forbidden page | WIRED |
| Preview/send ready-only pool; send → archive issue URL + email `returnUrl` | WIRED |

**API coverage:** 14 routes have SPA callers. `GET /health` is ops-only (no SPA consumer expected). `POST /me/ping` has no SPA caller (tech debt). Shipped archive route is `GET /archive`; the SPA and backend agree.

**Auth:** shell routes redirect to `login?returnUrl=` when mocks are off. Admin APIs use `require_admin`. Warning: `RequireAuth` renders children when `VITE_USE_MOCKS` is on.

**Flows:** 7/7 complete (login, issue→material→archive, callout, vote change/close, knowledge, razbor, admin send). Broken flows: 0.

## Nyquist

Validate-phase hook is active (`workflow.nyquist_validation`).

| Phase | VALIDATION.md | Status | Compliant | Action |
|-------|---------------|--------|-----------|--------|
| 01 | exists | draft | not authoritative | `/gsd-validate-phase 1` |
| 02 | exists | draft | not authoritative | `/gsd-validate-phase 2` |
| 03 | exists | draft | not authoritative | `/gsd-validate-phase 3` |
| 04 | exists | validated | true (tasks green) | none |
| 05 | exists | validated | true (tasks green) | none |

Draft files are a coverage TODO, not a compliance failure. No phase is `validated` with `nyquist_compliant: false`.

## Tech debt

### Phase 1

- SPA no longer calls `POST /me/ping` (welcome toast uses `GET /me` only).
- No visible logout control.
- Cloud.ru app deploy remains documentation (D-07).
- Nyquist file still draft.

### Phase 2

- Visual UI-SPEC backstops held out.
- Live FE↔BE smoke not signed off.
- Advisory tag labels and cycle-clock selection.
- ISSUE-01 wording still mentions a cover image.

### Phase 3

- Visual backstops and live ballot smoke open.
- Database trigger `votes_enforce_open_and_topic` not reconfirmed this session.
- Nyquist file still draft.

### Phase 5

- Live re-UAT of composition preview and post-send rest copy still open.
- CR-01 non-atomic rank rewrite on failed send.
- Preview fingerprint can ignore block order after unlock.
- Mail transport is StubMailer until SMTP exists.

### Non-requirement note from integration

Ballot topic rows show description and material count and do not link to `/materials/{slug}`. VOTE-04 does not require that link. Knowledge search and the issue TOC do link to materials.

## Verdict

No critical blockers. Requirements 39/39. Do not treat this as `passed` until the deferred human checks and advisory items above are accepted or scheduled.
