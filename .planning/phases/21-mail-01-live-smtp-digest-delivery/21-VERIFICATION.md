---
phase: 21-mail-01-live-smtp-digest-delivery
verified: 2026-10-17T20:32:02Z
status: human_needed
score: 12/12 must-haves verified
covered_files:
  - .env.example
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-01-PLAN.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-01-SUMMARY.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-02-PLAN.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-02-SUMMARY.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-03-PLAN.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-03-SUMMARY.md
  - backend/src/backend/application/ports/digest_publisher.py
  - backend/src/backend/application/ports/mailer.py
  - backend/src/backend/application/ports/profile_repository.py
  - backend/src/backend/application/use_cases/send_digest.py
  - backend/src/backend/composition/config_error.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/composition/mailer_factory.py
  - backend/src/backend/composition/settings.py
  - backend/src/backend/domain/errors.py
  - backend/src/backend/domain/recipient.py
  - backend/src/backend/infrastructure/delivery_policy.py
  - backend/src/backend/infrastructure/haskimail_mailer.py
  - backend/src/backend/infrastructure/smtp_mailer.py
  - backend/src/backend/infrastructure/stub_mailer.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/tests_support/in_memory.py
  - docs/adr/0005-haskimail-http-api-instead-of-smtp.md
  - docs/agents/local-platform-runbook.md
  - supabase-integration/src/supabase_integration/digest_publisher.py
  - supabase-integration/src/supabase_integration/profile_repository.py
  - tests/unit/test_haskimail_mailer.py
  - web/src/pages/AdminDigestPage.jsx
  - web/src/services/adminApi.js
covered_digest: "v2:sha256:e574712d806f727687134390be68312e95530e1de25a6bd32bc4de763265c923"
behavior_unverified: 0
overrides_applied: 1
overrides:
  - must_have: "The digest is delivered over real SMTP (stdlib smtplib/email) behind the extended Mailer port"
    reason: "ADR-0005 (accepted): preferred live transport is Haskimail HTTP API (MAILER=haskimail → HaskimailMailer). SmtpMailer remains a working alternate (MAILER=smtp); domain/use-case/HTTP edge unchanged. Literal ROADMAP/REQUIREMENTS SMTP wording diverges; delivery intent (real mailer, profiles audience, honest N/M, D-88 containment) holds."
    accepted_by: "ADR-0005"
    accepted_at: "2026-10-17T08:31:08Z"
re_verification:
  previous_status: human_needed
  previous_score: 12/12
  previous_verified: 2026-10-17T08:49:40Z
  previous_covered_digest: "v2:sha256:8bfd74dfcdf3d50bc5387d97f8e502528235da271432b032d81fc66fc15fa542"
  reason: "stale-digest re-verification (GSD #4682) — prior covered_digest no longer matched tree; full goal-backward recheck; no prior gaps:"
  note: "covered_digest changed (8bfd74df… → e574712d…) — covered file contents drifted since 08:49Z pass; automated must-haves still 12/12; UAT #6 still pending."
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "Phase 20 ROADMAP SC4 (corporate SMTP relay smoke serving GoTrue AND MAIL-01) is still not closed"
    category: other
    reason: "Haskimail (ADR-0005) replaces digest SMTP only; GoTrue stays on GOTRUE_SMTP_*. Runbook §4e still records criterion-4 as inherited ops gap (D-15). UAT #5 pass confirms we do not claim proof. Not a Phase 21 ROADMAP SC failure, but the Phase-20→21 deferred item remains open with no later phase owning it."
    evidence_status: "runbook grep criterion-4 / D-15; ADR-0005; 21-UAT #5 pass / #6 pending"
  - finding: "Runbook still documents only digest SMTP_* / MAILER=smtp; preferred live path is MAILER=haskimail (ADR-0005 / .env.example)"
    category: other
    reason: "Operator contract for HASKIMAIL_* lives in ADR-0005 + .env.example, not yet mirrored in docs/agents/local-platform-runbook.md §4e. Does not fail a must-have (SMTP contract still documented; D-15 ops gap still stated)."
    evidence_status: "Select-String runbook HASKIMAIL → no matches; ADR + .env.example present"
  - finding: "Phase SECURITY.md absent"
    category: security
    reason: "No 21-SECURITY.md under the phase directory; not required by PLAN must_haves. Note only — no invented security audit."
    evidence_status: "Test-Path 21-SECURITY.md → False"
prohibitions:
  - statement: "MUST NOT claim organisation-wide delivery in Russian message / API / SPA banner copy (MAIL-03 / D-09)."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 1 = pass"
  - statement: "MUST NOT implement DigestPublisher.update_delivery or post-mail batch delivery-column rewrite (D-06 option ii)."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 4 = pass"
  - statement: "MUST NOT route signup confirmation through Mailer / send_digest (Phase 20 GoTrue owns it)."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 4 = pass"
  - statement: "MUST NOT delete test_send_audit_failure_after_publish_still_returns_success — PRESERVE D-88 tripwire."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 2 = pass; named pytest green"
  - statement: "MUST NOT share one Bcc / multi-To blast across recipients (D-05)."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 3 = pass; SmtpMailer + HaskimailMailer one-To tests"
  - statement: "MUST NOT silently fall back to StubMailer when MAILER=smtp and SMTP_* are incomplete (D-16)."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 4 = pass; haskimail incomplete-config analogue also tested"
  - statement: "MUST NOT read process environment inside smtp_mailer.py or haskimail_mailer.py (MAIL-05)."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 3 = pass; test_haskimail_mailer_never_reads_process_environment green"
  - statement: "MUST NOT import smtplib or haskimail into application use cases or domain packages."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 3 = pass; test_transport_libraries_stay_out_of_domain_and_application green"
  - statement: "MUST NOT delete or gut tests/unit/test_stub_mailer.py stub behaviour — PRESERVE stub as double."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 4 = pass"
  - statement: "MUST NOT map contained mail failures to HTTP 5xx after successful publish (D-11 / D-88)."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 2 = pass; HTTP 200 partial/failed tests green"
  - statement: "MUST NOT claim Phase 20 criterion-4 corporate-relay smoke proof is complete in the runbook (D-15)."
    tier: judgment
    verdict: held
    human_ack_required: false
    human_ack_via: "21-UAT.md test 5 = pass"
decision_coverage:
  honored: 16
  total: 16
  not_honored: []
human_verification:
  - test: "Live Haskimail digest smoke (external service / ops) — ADR-0005"
    expected: "With MAILER=haskimail + valid HASKIMAIL_API_KEY and verified-domain HASKIMAIL_FROM, one real weekly digest is accepted by https://api.haskimail.ru/email; recipient_count=M and delivered_count=N match the mailed set; API rejection stays partial/failed with HTTP 200 (never 500)."
    why_human: "External Haskimail delivery cannot be exercised by the offline unit suite. UAT #6 pending: 2026-10-17 live run authenticated but 422/ErrorCode 400 until FROM is domain-verified; adapter correctly returned failed without 5xx."
---

# Phase 21: MAIL-01 live SMTP digest delivery Verification Report

**Phase Goal:** The weekly digest is delivered by a real SMTP mailer to the `profiles`-derived audience, with an honest `recipient_count`, and a mail failure never turns an already-published digest into a 500.
**Verified:** 2026-10-17T20:32:02Z
**Status:** human_needed
**Re-verification:** Yes — stale-digest refresh (GSD #4682). Prior VERIFICATION had no `gaps:` (must-haves reused from ROADMAP SC + PLAN + prior truths). `covered_digest` **changed** vs 08:49Z pass (`8bfd74df…` → `e574712d…`); automated findings reconfirmed against code + named pytest.

## Goal Achievement

Goal-backward check against the **current** tree. Phase **intent** (real delivery to profiles audience, honest M/N, D-88 containment) holds. Literal ROADMAP wording «real SMTP» remains an accepted deviation via **ADR-0005** — preferred live transport is Haskimail HTTP API; `SmtpMailer` remains as `MAILER=smtp`. Outstanding: ops live Haskimail smoke (UAT #6 pending domain verification) — status stays `human_needed` (not `passed`).

**Phase 20 SC4 (deferred → Phase 21):** **not addressed** by Haskimail. Digest lane moved to HTTP API; GoTrue corporate-relay smoke is still an open ops gap (see advisory). Not counted as a Phase 21 ROADMAP SC failure (D-15 + ADR-0005).

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Recipients resolved server-side from `profiles` through a repository port — all roles, `profiles.email` only, no admin exclusion (SC1 / D-01/D-03) | ✓ VERIFIED | `ProfileRepository.list_digest_recipients`; in-memory + Supabase adapters; `send_digest` calls before claim |
| 2 | Empty/malformed emails excluded + logged, never counted in M; CR/LF/control/comma hardened (SC1 / D-02 / CR-01) | ✓ VERIFIED | `is_usable_email` in `recipient.py`; `tests/unit/test_recipient_email.py` in spot-check suite (89 passed with haskimail+smtp) |
| 3 | Planned audience M stamped at claim (`recipient_count`) (SC1/SC4 / D-06 i / MAIL-03) | ✓ VERIFIED | `send_digest` → `claim_and_publish(recipient_count=M)`; Supabase RPC params include `p_recipient_count` |
| 4 | Real live delivery behind extended `Mailer` port; one message per recipient, single `To`, no Bcc (SC2 / D-05) | ✓ PASSED (override) | Override: ADR-0005 — preferred path `HaskimailMailer` (HTTP API); `SmtpMailer` still present for `MAILER=smtp`. Both enforce one-To / D-08 via `delivery_policy` |
| 5 | Planned M and delivered N recorded and reported; two-sentence honest copy, never org-wide claim (SC2 / MAIL-03 / D-09/D-10/D-12) | ✓ VERIFIED | `SendDigestResult` / HTTP `delivered_count` / ping payload; `_compose_delivery_message` variants; SPA mock stub copy; no «всей организации» in message path |
| 6 | Mail failure mapped to domain `MailDeliveryError`, caught with `PersistenceError` after publish → success, never 500 (SC3 / MAIL-04 / D-88) | ✓ VERIFIED | Both adapters map transport errors; `send_digest` catch; named containment + HTTP 200 tests green |
| 7 | Bounded per-recipient policy (D-08): continue, stop after three consecutive, reset on success, `stop_reason` | ✓ VERIFIED | Shared `delivery_policy.py` (`CONSECUTIVE_FAILURE_LIMIT = 3`); Smtp + Haskimail streak/stop tests green |
| 8 | HTTP stays 200 when claim+publish succeeded even if delivery is `partial`/`failed` (SC3 / D-11) | ✓ VERIFIED | `test_admin_send_stays_200_when_mail_{partial,failed}_after_publish` green |
| 9 | Empty audience M=0 still publishes; live status honestly `sent` with N=0 (D-04) | ✓ VERIFIED | Both live adapters + use-case message «Получателей нет (0 из 0)» |
| 10 | Config via `Settings`/composition only; no `os.environ` in adapters; fail-fast `ConfigurationError`; `MAILER` defaults stub (SC5 / MAIL-05 / D-13…D-16) | ✓ VERIFIED | `SMTP_*` + `HASKIMAIL_*` only in `Settings.from_env`; adapters env-free (rg clean); incomplete smtp/haskimail → `ConfigurationError` |
| 11 | Live adapters forward planned `p_recipient_count` (no `update_delivery`) and page profiles select (WR-02) | ✓ VERIFIED | `p_recipient_count` in publisher; `update_delivery` comment-only |
| 12 | SPA `adminApi` + banner carry `delivered_count` + honest message; runbook documents digest SMTP contract without claiming GoTrue relay proof (MAIL-03/MAIL-05 / D-12/D-15) | ✓ VERIFIED | Mock stub message aligned; runbook §4.1 / §4e SMTP + D-15 ops gap. **Advisory:** Haskimail ops not yet in runbook |

**Score:** 12/12 truths verified (0 behavior-unverified; 1 override)

### Transport deviation (SMTP vs Haskimail)

| Aspect | ROADMAP / REQUIREMENTS literal | Current tree |
| ------ | ------------------------------ | ------------ |
| Preferred live mailer | «real SMTP» / `smtplib` | `MAILER=haskimail` → `HaskimailMailer` (ADR-0005) |
| Alternate live mailer | — | `MAILER=smtp` → `SmtpMailer` still wired |
| Port / use case / HTTP | unchanged expected | unchanged |
| Goal intent | profiles audience, honest N/M, no 500 after publish | ✓ holds |
| Phase 20 SC4 (GoTrue+MAIL-01 relay proof) | deferred to Phase 21 | ✗ still open — Haskimail ≠ GoTrue relay |

**Not `gaps_found`:** SMTP→Haskimail deviation is documented and accepted in ADR-0005; override applied to SC2 SMTP wording. Do not silently treat literal SMTP as still the preferred path.

### Deferred Items

None for Phase 21 ROADMAP success criteria. Phase 20 SC4 remains **open ops debt** (not deferred further — no later phase owns it); recorded under Advisory.

### Advisory (New Scope / Carried Ops Debt)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Phase 20 SC4 corporate-relay smoke still open | other | Haskimail closes digest transport alternate, not GoTrue dual-lane proof |
| 2 | Runbook lacks `HASKIMAIL_*` operator section while preferred path is Haskimail | other | Docs lag; ADR + `.env.example` cover config; SMTP contract still present |
| 3 | `21-SECURITY.md` missing | security | Not a PLAN must-have; noted only — no invented threats |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/.../domain/recipient.py` | Frozen `Recipient` + `is_usable_email` | ✓ VERIFIED | Wired |
| `backend/.../domain/errors.py` | `MailDeliveryError` | ✓ VERIFIED | Caught in use case |
| `backend/.../ports/mailer.py` | `recipients` + return-key contract | ✓ VERIFIED | Unchanged by ADR-0005 |
| `backend/.../ports/profile_repository.py` | `list_digest_recipients()` | ✓ VERIFIED | |
| `backend/.../ports/digest_publisher.py` | `recipient_count` on claim | ✓ VERIFIED | |
| `backend/.../use_cases/send_digest.py` | Audience→claim→mail→honest result + containment | ✓ VERIFIED | |
| `backend/.../infrastructure/smtp_mailer.py` | Real stdlib SMTP adapter | ✓ VERIFIED | Still present; uses shared `delivery_policy` |
| `backend/.../infrastructure/haskimail_mailer.py` | Haskimail HTTP adapter (ADR-0005) | ✓ VERIFIED | Substantive; wired via factory |
| `backend/.../infrastructure/delivery_policy.py` | Shared D-07/D-08 policy | ✓ VERIFIED | Used by both live adapters |
| `backend/.../composition/mailer_factory.py` | `resolve_mailer` stub\|smtp\|haskimail | ✓ VERIFIED | Fail-fast both live modes |
| `backend/.../composition/settings.py` | `SMTP_*` + `HASKIMAIL_*` | ✓ VERIFIED | Secrets `repr=False`; default `mailer=stub` |
| `supabase-integration/.../profile_repository.py` | list recipients | ✓ VERIFIED | |
| `supabase-integration/.../digest_publisher.py` | forward `p_recipient_count` | ✓ VERIFIED | |
| `backend/.../interface/http/routes/admin.py` | `delivered_count` | ✓ VERIFIED | |
| `web/src/services/adminApi.js` | `delivered_count` + stub-honest mock | ✓ VERIFIED | |
| `docs/agents/local-platform-runbook.md` | Digest SMTP operator contract | ✓ VERIFIED | SMTP present; Haskimail lag = advisory |
| `docs/adr/0005-haskimail-http-api-instead-of-smtp.md` | Accepted transport ADR | ✓ VERIFIED | |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `send_digest.py` | `profile_repository` | `list_digest_recipients()` → M before claim | ✓ WIRED | |
| `send_digest.py` | `mailer` / adapters | `send_digest(...)` → `delivered_count` | ✓ WIRED | Port-agnostic |
| `send_digest.py` | `errors.py` | `except (MailDeliveryError, PersistenceError)` | ✓ WIRED | |
| `live.py` | `mailer_factory.py` | `resolve_mailer(settings)` | ✓ WIRED | smtp + haskimail |
| `haskimail_mailer.py` / `smtp_mailer.py` | `errors.py` | transport → `MailDeliveryError` | ✓ WIRED | |
| `admin.py` | `send_digest.py` | `delivered_count` on 200 | ✓ WIRED | |
| `adminApi.js` | `AdminDigestPage.jsx` | `result.message` banner | ✓ WIRED | |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `send_digest` recipient_count | `recipient_count` | `profiles.list_digest_recipients()` | Yes | ✓ FLOWING |
| `SendDigestResponse.delivered_count` | `delivered_count` | mailer result | Yes | ✓ FLOWING |
| `SupabaseDigestPublisher` | `p_recipient_count` | claim kwarg | Yes | ✓ FLOWING |
| SPA mock | stub counts | fixture | Mock by design | ✓ FLOWING (mock) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------- |
| Haskimail + SMTP + recipient email suite | `uv run pytest tests/unit/test_haskimail_mailer.py tests/unit/test_smtp_mailer.py tests/unit/test_recipient_email.py -q` | **89 passed** | ✓ PASS |
| Containment + HTTP 200 + env-free + transport boundary | named tests (`test_send_mail_failure…`, `test_send_audit_failure…`, `test_admin_send_stays_200…`, `test_haskimail_mailer_never_reads…`, `test_transport_libraries…`) | **10 passed** | ✓ PASS |
| Decision coverage gate | `gsd-tools query check.decision-coverage-verify` | 16/16 honored | ✓ PASS (non-blocking) |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared probes | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| MAIL-01 | 21-01, 21-02, 21-03 | Real mailer to `profiles` audience; best-effort after publish | ✓ SATISFIED (override on SMTP literal) | Haskimail preferred + Smtp alternate; D-88 tests green |
| MAIL-03 | 21-01, 21-03 | Honest M + N; no org-wide claim | ✓ SATISFIED | Result/HTTP/message; UAT #1 pass |
| MAIL-04 | 21-01, 21-02 | Failures contained; bounded timeouts | ✓ SATISFIED | Both adapters; catch alongside `PersistenceError` |
| MAIL-05 | 21-02, 21-03 | Config via settings only; no env in adapters | ✓ SATISFIED | `SMTP_*` + `HASKIMAIL_*` via Settings; adapters env-free |

No orphaned requirements — REQUIREMENTS.md maps MAIL-01/03/04/05 to Phase 21 only.

### Decision Coverage

All trackable CONTEXT.md decisions honored by shipped artifacts (`honored: 16/16`). Non-blocking gate. Message: «All trackable CONTEXT.md decisions are honored by shipped artifacts.»

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/unit/test_haskimail_mailer.py` | MAIL-01/04/05 | many | 0 | no | Behavioral / value | PASS |
| `tests/unit/test_smtp_mailer.py` | MAIL-01/04/05 | many | 0 | no | Behavioral / value | PASS |
| `tests/unit/test_send_digest.py` (containment) | MAIL-01/04 | present | 0 | no | Behavioral | PASS |
| `tests/unit/test_http_admin.py` (200 after mail fail) | MAIL-01/03 | present | 0 | no | Status + value | PASS |

**Disabled tests on requirements:** 0  
**Circular patterns detected:** 0  
**Insufficient assertions:** 0

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No `TBD`/`FIXME`/`XXX` in phase mailer artifacts | — | — |
| `digest_publisher.py` | ~71 | `update_delivery` in comment only | ℹ️ Info | Prohibition held |

### Human Verification Required

### 1. Live Haskimail digest smoke (ops)

**Test:** Set `MAILER=haskimail` with valid `HASKIMAIL_API_KEY` and **domain-verified** `HASKIMAIL_FROM`; send one weekly digest; confirm MessageIDs, M/N honesty, and that a rejection stays `partial`/`failed` with HTTP 200.
**Expected:** Delivery accepted after FROM verification; counts match; no 500 after publish.
**Why human:** External API; UAT #6 pending (422 until verified FROM — adapter already proved failed-without-5xx live).

Judgment-tier prohibitions were human-acked in `21-UAT.md` (tests 1–5 = pass); not re-listed.

### Gaps Summary

No blocking gaps for Phase 21 code must-haves. Literal SMTP preference vs Haskimail is an **accepted ADR-0005 override**, not a failed truth. Status remains `human_needed` solely for the outstanding live Haskimail smoke (UAT #6). Fresh `covered_digest` = `e574712d…` (no longer stale vs prior `8bfd74df…`).

**Phase 20 SC4:** still open — Haskimail does not prove corporate relay for GoTrue; do not mark that deferred item closed.

**SECURITY.md:** absent for this phase — noted under advisory; no full security audit invented.

---

_Verified: 2026-10-17T20:32:02Z_
_Verifier: Claude (gsd-verifier)_
