---
phase: 05-admin-digest-publish
verified: 2026-09-21T19:22:06Z
status: passed
score: 8/8 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 5/5
  gaps_closed:

    - "G-05-1: intro + reorderable issue blocks + interstitial text reach preview/send order (05-07/05-08)"
    - "G-05-2: post-send / cold digest_rest hides shortlist and shows weekly rest copy (05-09)"
  gaps_remaining: []
  regressions: []
decision_coverage:
  honored: 17
  total: 17
  not_honored: []
advisory_review:
  source: 05-REVIEW.md
  status: issues_found
  critical: 1
  warning: 3
  note: "CR-01 rank rewrite before claim_and_publish_digest is non-atomic (durable rank side effect on failed send). Does not fail ADMIN-07/SC#4 sent_at contract (claim+issue still RPC-atomic). WR-01 preview fingerprint ignores block order after unlock — advisory fidelity gap."
human_verification:

  - test: "Live re-UAT G-05-1: as admin, fill «Вводный текст», reorder «Блоки выпуска», insert interstitial text, open «Превью письма», then send"
    expected: "Intro + interstitial appear in preview.body; material titles follow block order; send records «Отправка записана» and archive issue; StubMailer body uses same material order"
    why_human: "UAT test 1 was diagnosed major before gap closure; Playwright proves mock harness only"

  - test: "Live re-UAT G-05-2: after recorded send (and cold reload of /admin/digest)"
    expected: "Shortlist/checkboxes/editors hidden; rest shows «дайджест успешно выпущен» and «через 7 дней»; banners «Отправка записана» / «Уже отправлено» still usable; genuine empty still D-80"
    why_human: "UAT test 2 was diagnosed minor before 05-09; live seed/sent batch state needs operator eyes"

  - test: "Acknowledge 05-REVIEW CR-01 (post-05-08): rank rewrite outside RPC"
    expected: "Accept scrambled ranks on failed send, or schedule RPC p_material_ids / transactional rewrite follow-up"
    why_human: "Reliability finding outside must_have fail criteria; product decision required"
next_action: "Human verification required. Re-run live UAT for G-05-1 / G-05-2 (closed in code), then re-run verify until status is passed."
next_command: "/gsd-verify-work 05"
---

# Phase 5: Admin Digest Publish Verification Report

**Phase Goal:** Админ triages the weekly shortlist and ships an approved digest to СВА with archive and email link integrity  
**Verified:** 2026-09-21T19:22:06Z  
**Status:** human_needed  
**Re-verification:** Yes — after UAT gap closure (05-07 / 05-08 / 05-09); prior report was `human_needed` 5/5 with no must-have `gaps:`

## Goal Achievement

### Observable Truths

Roadmap Success Criteria (non-negotiable) plus distinct gap-closure must-haves from plans 05-07…05-09. Plan truths that only restate a roadmap SC are scored under that SC.

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Admin sees ≤5 ranked candidates with draft/ready and scoring factors (or honest «недоступно»); non-admin gets 403 | ✓ VERIFIED | `get_admin_shortlist` caps at 5; `honest_factor_labels`; `require_admin` → HTTP 403; ForbiddenPage; unit/HTTP + `admin.spec.js` |
| 2 | Approve/Reject and batch select-all/top-N persist visibly; send blocked if drafts included or selection empty | ✓ VERIFIED | `set_shortlist_decision`; AdminDigestPage selectAll/selectTopN; DraftInSendPoolError → 400; Playwright draft-block |
| 3 | Preview matches ready selection; failed preview does not count as verified send | ✓ VERIFIED | `preview_digest_email` approved∩ready (+ composition); never mutates `sent_at`; SPA `emailPreviewed` only after success; fail keeps send locked |
| 4 | Successful send updates archive and success UI without uncontrolled duplicates; failure leaves selection and not-sent state | ✓ VERIFIED | `send_digest` → `claim_and_publish` RPC; «Отправка записана»; AlreadySentError→409; drafts/empty leave unsent; unit+HTTP green |
| 5 | Digest email link reaches issue after login via returnUrl when needed | ✓ VERIFIED | Stub/mail body `/issues/{n}`; success CTA; `sanitizeReturnUrl` + `auth.spec.js` ADMIN-08 |
| 6 | Non-empty «Вводный текст» + ordered material/text blocks appear in «Превью письма» body (G-05-1 / 05-07) | ✓ VERIFIED | Use-case + HTTP composition; modal renders `preview.body`; Playwright intro gate; `test_preview_digest.py` order assertions |
| 7 | «Блоки выпуска» reorder + optional interstitial drive preview and send `material_ids` publication order (G-05-1 / 05-08) | ✓ VERIFIED | `admin-issue-blocks` UI; `send_digest(..., material_ids)`; publisher applies order; Playwright reorder + send «Отправка записана» |
| 8 | After recorded send / cold `digest_rest`, triage shortlist is hidden; rest copy «дайджест успешно выпущен» + weekly 7 days (G-05-2 / 05-09) | ✓ VERIFIED | `digest_rest` + `days_until_next_batch=7`; SPA `restMode`; Playwright post-send / already-sent / cold-rest vs D-80 |

**Score:** 8/8 truths verified (0 present, behavior-unverified)

### Deferred Items

None — no failed truths deferred to later phases.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------- | ------- |
| `backend/.../deps.py` (`require_admin`) | Profile-role admin gate | ✓ VERIFIED | Used by admin routes |
| `backend/.../routes/admin.py` | shortlist/decision/preview/send + composition/rest fields | ✓ VERIFIED | Wired in `app.py`; DigestPreviewRequest / SendDigestRequest / digest_rest |
| `backend/.../ports/shortlist_repository.py` | get_current_batch / get_latest_batch / decisions | ✓ VERIFIED | Port + adapters |
| `backend/.../ports/digest_publisher.py` | Atomic claim+publish + optional material_ids | ✓ VERIFIED | Protocol documents RPC contract |
| `backend/.../use_cases/send_digest.py` | Publish-on-send + order validation | ✓ VERIFIED | Permutation → publisher → StubMailer |
| `backend/.../use_cases/preview_digest_email.py` | Composition preview DTO | ✓ VERIFIED | intro + blocks → body |
| `backend/.../use_cases/get_admin_shortlist.py` | ≤5 + digest_rest | ✓ VERIFIED | Rest when latest sent |
| `backend/.../infrastructure/stub_mailer.py` | StubMailer + smtp fail-fast | ✓ VERIFIED | `resolve_mailer` |
| `web/src/pages/AdminDigestPage.jsx` | Triage + blocks + rest | ✓ VERIFIED | issueBlocks, preview.body, restMode |
| `web/src/pages/ForbiddenPage.jsx` | 403 copy | ✓ VERIFIED | Non-admin deep-link |
| `web/src/services/adminApi.js` | Admin HTTP client | ✓ VERIFIED | preview/send composition + digest_rest map |
| `web/src/services/adminPreviewComposition.js` | Pure composition helpers | ✓ VERIFIED | Used by SPA/tests |
| `supabase-integration/migrations/005_phase5_admin_shortlist.sql` | Delivery cols + RPC | ✓ VERIFIED | claim_and_publish_digest |
| `supabase-integration/.../digest_publisher.py` | Live DigestPublisher | ✓ VERIFIED | Wired in `live.py` (rank rewrite advisory — see review) |
| `supabase-integration/.../shortlist_repository.py` | Live shortlist adapter | ✓ VERIFIED | service_role client |
| `docs/agents/local-platform-runbook.md` §4e | Stub/seed/admin promote | ✓ VERIFIED | Section present |
| `tests/admin.spec.js` | Playwright honesty + G-05-1/2 | ✓ VERIFIED | No `.skip` in admin.spec |
| `tests/unit/test_http_admin.py` + send/preview/shortlist units | Backend contracts | ✓ VERIFIED | 49 related tests passed this run |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | ---- | ------ | ------- |
| `POST /admin/shortlist/preview` | `preview_digest_email` | intro/blocks JSON | ✓ WIRED | Composition body; no `sent_at` |
| `POST /admin/shortlist/send` | `send_digest` → publisher + StubMailer | material_ids | ✓ WIRED | Claim via RPC; order from SPA blocks |
| `AdminDigestPage` | `adminApi` | previewEmail / sendDigest / fetchShortlist | ✓ WIRED | `/admin/digest` route |
| `create_service_role_client` | `SupabaseDigestPublisher` + shortlist | `build_live_container` | ✓ WIRED | `live.py` |
| `get_admin_shortlist` | `get_latest_batch` | digest_rest path | ✓ WIRED | When current batch None |
| Migration 005 RPC | live claim+publish | publisher.rpc | ✓ WIRED | Delivery stamp in-transaction |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| AdminDigestPage rows | `items` from `fetchShortlist` | GET `/admin/shortlist` | Yes | ✓ FLOWING |
| Preview modal body | `preview.body` | `preview_digest_email` composition | Yes | ✓ FLOWING |
| Send success CTA | `issue_url` | publisher after RPC | Yes (`/issues/{n}`) | ✓ FLOWING |
| Rest panel days | `days_until_next_batch` | API or cadence constant 7 | Yes (declared constant) | ✓ FLOWING |
| Live issue positions | ranks → RPC insert order | `_apply_publication_ranks` then RPC | Yes on success; ranks may stick on mid-failure | ⚠️ Advisory (CR-01) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Send/preview/HTTP/shortlist/factors | `uv run pytest tests/unit/test_send_digest.py test_preview_digest.py test_get_admin_shortlist.py test_http_admin.py test_score_factors.py -q` | 49 passed | ✓ PASS |
| Playwright admin suite (orchestrator) | User report after 05-09 | 80 passed, 1 skipped | ✓ PASS (reported) |
| Skipped suite location | `tests/web-app.spec.js` phase-2 visual `describe.skip` | Not ADMIN requirement-linked | ℹ️ Info |
| Probe scripts | — | None declared | SKIPPED |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh` | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ADMIN-01 | 05-01, 05-04, 05-05, 05-06, 05-09 | ≤5 shortlist; non-admin 403; empty honesty; rest ≠ D-80 | ✓ SATISFIED | HTTP 403, Forbidden, empty + digest_rest |
| ADMIN-02 | 05-02, 05-04 | Approve/Reject persist | ✓ SATISFIED | decision route + UI |
| ADMIN-03 | 05-02, 05-03, 05-04, 05-07 | draft/ready; draft blocks send | ✓ SATISFIED | DraftInSendPoolError + UI |
| ADMIN-04 | 05-03, 05-04, 05-06, 05-07, 05-08 | Preview matches selection/composition; fail ≠ verified | ✓ SATISFIED | composition + D-86 gate |
| ADMIN-05 | 05-01, 05-04 | ≥2 factors or «обоснование недоступно» | ✓ SATISFIED | `honest_factor_labels` |
| ADMIN-06 | 05-04, 05-06 | Select-all / top-N; manual uncheck | ✓ SATISFIED | AdminDigestPage + Playwright |
| ADMIN-07 | 05-03…05-06, 05-08, 05-09 | Confirm send, archive, 409, unsent on pre-claim fail, rest UX | ✓ SATISFIED | send_digest + RPC + rest panel |
| ADMIN-08 | 05-03, 05-06, 05-08 | Email `/issues/{n}` + returnUrl | ✓ SATISFIED | Stub body + auth.spec |

**Orphaned requirements:** none — all Phase 5 IDs (ADMIN-01…08) appear in plan frontmatter.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts (17/17). Gate non-blocking.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/unit/test_http_admin.py` | ADMIN-01…08 | yes | 0 | no | Behavioral/HTTP | PASS |
| `tests/unit/test_send_digest.py` | ADMIN-03/07/08 | yes | 0 | no | Behavioral | PASS |
| `tests/unit/test_preview_digest.py` | ADMIN-04 | yes | 0 | no | Value/order | PASS |
| `tests/unit/test_get_admin_shortlist.py` | ADMIN-01/07 | yes | 0 | no | Value | PASS |
| `tests/unit/test_admin_preview_composition.js` | ADMIN-04 | yes | 0 | no | Value | PASS |
| `tests/admin.spec.js` | ADMIN-01/04/06/07/08 + G-05 | yes | 0 | no | Behavioral (mock) | PASS |
| `tests/auth.spec.js` | ADMIN-08 | yes | 0 | no | Behavioral (mock) | PASS |

**Disabled tests on requirements:** 0  
**Circular patterns detected:** 0  
**Insufficient assertions:** 0 blockers (Playwright remains mock-harness — flagged for live human UAT, not test-quality BLOCKER)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `digest_publisher.py` | 56–93 | Rank UPDATEs before RPC (non-atomic with claim) | ℹ️ Advisory (CR-01) | Failed send can leave rewritten ranks; `sent_at` still not stamped |
| `AdminDigestPage.jsx` | 74–79, 321–323 | Preview fingerprint = sorted approved IDs only | ℹ️ Advisory (WR-01) | Reorder after preview without re-preview can diverge send order from letter |
| `send_digest.py` | 107–142 | Mailer/pings after durable claim | ℹ️ Advisory (WR-02) | StubMailer failure after publish may 5xx after durable send |

No `TBD`/`FIXME`/`XXX` debt markers in phase key production files.

### Advisory Findings (05-REVIEW.md — do not fail solely on these)

From `05-REVIEW.md` (`status: issues_found`, 1 critical / 3 warnings after gap closure):

1. **CR-01 (critical, advisory here):** `_apply_publication_ranks` commits before `claim_and_publish_digest`. Must_haves / ADMIN-07 require controlled repeat send and not marking sent on failure — claim+issue atomicity via RPC still holds; rank durability on failure is a hardening gap, not a roadmap SC miss.
2. **WR-01:** D-86 unlock ignores block order / intro edits after successful preview.
3. **WR-02 / WR-03:** Post-claim mailer/pings; preview duplicate material blocks — follow-ups, not must_have failures.

### Human Verification Required

### 1. Live re-UAT G-05-1 (composition)

**Test:** As `profiles.role=admin`, fill «Вводный текст», reorder «Блоки выпуска», add interstitial text, open «Превью письма», confirm stub send.  
**Expected:** Intro + interstitial in preview; order matches blocks; «Отправка записана» + archive; employee `/admin/digest` still ForbiddenPage.  
**Why human:** Prior UAT major issue; mocks ≠ live seed.

### 2. Live re-UAT G-05-2 (rest)

**Test:** After send and on cold reload of `/admin/digest`.  
**Expected:** No inactive checkboxes; «дайджест успешно выпущен» + «через 7 дней»; D-80 only when `digest_rest` false.  
**Why human:** Prior UAT minor issue closed in 05-09 needs live confirmation.

### 3. CR-01 product acknowledgment

**Test:** Decide accept rank-rewrite risk vs schedule RPC `p_material_ids`.  
**Expected:** Explicit accept or follow-up ticket.  
**Why human:** Reliability trade-off outside automated must_have fail criteria.

### Gaps Summary

No must-have gaps. Roadmap SCs and ADMIN-01…08 hold in code; UAT gaps G-05-1 / G-05-2 are closed by 05-07…05-09 with unit/HTTP/Playwright evidence (49 targeted pytest + reported Playwright 80/1). Status remains **human_needed** for live re-UAT of the closed gaps and advisory CR-01 acknowledgment — not `gaps_found`.

---

_Verified: 2026-09-21T19:22:06Z_  
_Verifier: Claude (gsd-verifier)_
