---
phase: 21-mail-01-live-smtp-digest-delivery
verified: 2026-10-16T15:30:02Z
status: human_needed
score: 12/12 must-haves verified
covered_files:
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-01-PLAN.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-02-PLAN.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-03-PLAN.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-01-SUMMARY.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-02-SUMMARY.md
  - .planning/phases/21-mail-01-live-smtp-digest-delivery/21-03-SUMMARY.md
  - backend/src/backend/domain/recipient.py
  - backend/src/backend/domain/errors.py
  - backend/src/backend/application/ports/mailer.py
  - backend/src/backend/application/ports/profile_repository.py
  - backend/src/backend/application/ports/digest_publisher.py
  - backend/src/backend/application/use_cases/send_digest.py
  - backend/src/backend/infrastructure/smtp_mailer.py
  - backend/src/backend/infrastructure/stub_mailer.py
  - backend/src/backend/composition/settings.py
  - backend/src/backend/composition/config_error.py
  - backend/src/backend/composition/mailer_factory.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/tests_support/in_memory.py
  - supabase-integration/src/supabase_integration/profile_repository.py
  - supabase-integration/src/supabase_integration/digest_publisher.py
  - web/src/services/adminApi.js
  - web/src/pages/AdminDigestPage.jsx
  - docs/agents/local-platform-runbook.md
covered_digest: "v2:sha256:121ec8de787d4039f37b22077de8100781bdb37263540df67fba5fdacb4b6f7b"
behavior_unverified: 0
overrides_applied: 0
prohibitions:
  - statement: "MUST NOT claim organisation-wide delivery in Russian message / API / SPA banner copy (MAIL-03 / D-09)."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT implement DigestPublisher.update_delivery or post-mail batch delivery-column rewrite (D-06 option ii)."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT route signup confirmation through Mailer / send_digest (Phase 20 GoTrue owns it)."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT delete test_send_audit_failure_after_publish_still_returns_success — PRESERVE D-88 tripwire."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT share one Bcc / multi-To blast across recipients (D-05)."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT silently fall back to StubMailer when MAILER=smtp and SMTP_* are incomplete (D-16)."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT read process environment inside smtp_mailer.py (MAIL-05)."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT import smtplib into application use cases or domain packages."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT delete or gut tests/unit/test_stub_mailer.py stub behaviour — PRESERVE stub as double."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT map contained mail failures to HTTP 5xx after successful publish (D-11 / D-88)."
    tier: judgment
    verdict: held
    human_ack_required: true
  - statement: "MUST NOT claim Phase 20 criterion-4 corporate-relay smoke proof is complete in the runbook (D-15)."
    tier: judgment
    verdict: held
    human_ack_required: true
human_verification:
  - test: "Ack prohibitions: honest copy + no org-wide delivery claim (message / API / SPA banner)"
    expected: "Server-composed two-sentence copy «Доставлено N из M» / «Письма не доставлены» / «Получателей нет (0 из 0)» / stub line; no «всей организации»-style claim anywhere."
    why_human: "Judgment-tier flagged prohibition — LLM-judge found held (send_digest._compose_delivery_message + unit asserts); needs interactive human ack."
  - test: "Ack prohibitions: D-88 containment + no 5xx-after-publish + PERSERVE tripwire"
    expected: "Mail error after publish still returns HTTP 200 success with the issue persisted; test_send_audit_failure_after_publish_still_returns_success present and green; test_send_mail_failure_after_publish_still_returns_success green."
    why_human: "Judgment-tier flagged prohibitions — LLM-judge found held (raise-path unit test + two HTTP-200 route tests, all green); needs interactive human ack."
  - test: "Ack prohibitions: one-message-per-recipient privacy, no Bcc blast, no smtplib leakage, no os.environ in adapter"
    expected: "SmtpMailer sets a single To per EmailMessage and no Bcc; smtplib imported only in infrastructure; smtp_mailer.py contains no os.environ/getenv."
    why_human: "Judgment-tier flagged prohibitions — LLM-judge found held (code inspection + test_smtp_mailer_sends_one_message_per_recipient, test_smtplib_import_stays_out_of_domain_and_application, test_smtp_mailer_never_reads_process_environment); needs interactive human ack."
  - test: "Ack prohibitions: D-16 fail-fast, no silent stub fallback, no update_delivery, no signup-via-Mailer, StubMailer preserved"
    expected: "resolve_mailer raises ConfigurationError on incomplete/out-of-range SMTP_*; a misconfigured smtp mode never returns StubMailer; no DigestPublisher.update_delivery method; no Mailer/send_digest under web/src; StubMailer class intact."
    why_human: "Judgment-tier flagged prohibitions — LLM-judge found held (mailer_factory + tests; grep for update_delivery finds only a comment; test_stub_mailer.py green); needs interactive human ack."
  - test: "Ack prohibition: runbook does not claim Phase 20 criterion-4 relay proof complete"
    expected: "Runbook §4.1.3 and the §4e block state the live corporate-relay smoke is an inherited ops gap (D-15); GOTRUE_SMTP_* lane stays separate from digest SMTP_*."
    why_human: "Judgment-tier flagged prohibition — LLM-judge found held (runbook wording); needs interactive human ack."
  - test: "Live corporate-relay digest smoke (external service integration / ops)"
    expected: "With MAILER=smtp + complete SMTP_* on the VM, one real weekly digest is accepted by the corporate relay and delivered to the profiles-derived audience; recipient_count=M and delivered_count=N match the mailed set."
    why_human: "External SMTP relay delivery cannot be exercised by the offline unit suite or the mock-based Playwright suite; D-15 makes the flip an ops step (not a merge blocker), so the code merges under MAILER=stub."
---

# Phase 21: MAIL-01 live SMTP digest delivery Verification Report

**Phase Goal:** The weekly digest is delivered by a real SMTP mailer to the `profiles`-derived audience, with an honest `recipient_count`, and a mail failure never turns an already-published digest into a 500.
**Verified:** 2026-10-16T15:30:02Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

Goal-backward verification against the on-disk code (not the SUMMARY narrative). Every roadmap success criterion and every PLAN `must_haves` truth resolves to VERIFIED; the only outstanding items are judgment-tier flagged prohibitions that require an interactive human acknowledgement, plus the ops-only live relay smoke explicitly scoped out of the merge gate by D-15.

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | Recipients resolved server-side from `profiles` through a repository port — all roles, `profiles.email` only, no admin exclusion (SC1 / D-01/D-03) | ✓ VERIFIED | `ProfileRepository.list_digest_recipients` port; `InMemoryProfileRepository` + `SupabaseProfileRepository` implementations; `send_digest` calls it before the claim; `test_profile_repository_recipients.py` + `test_supabase_digest_recipients_contract.py` green |
| 2 | Empty/malformed emails excluded + logged, never counted in M; CR/LF/control/comma/whitespace hardened (SC1 / D-02 / CR-01) | ✓ VERIFIED | `is_usable_email` rejects `count("@")!=1`, surrounding/embedded whitespace, control chars, commas; live probe `is_usable_email('victim@x.ru\r\nBcc: attacker@y.ru') → False`, `'a@b.ru, c@d.ru' → False`; `test_recipient_email.py` green |
| 3 | Planned audience M is computed and stamped at claim (`recipient_count`) (SC1/SC4 / D-06 i / MAIL-03) | ✓ VERIFIED | `send_digest` stamps `recipient_count=len(recipients)` into `claim_and_publish`; RPC 005/006 accept `p_recipient_count` and persist it; `test_claim_and_publish_forwards_planned_recipient_count` asserts `params["p_recipient_count"] == 5` |
| 4 | Real SMTP delivery (stdlib `smtplib`/`email`) behind extended `Mailer` port; one message per recipient, single `To`, no Bcc (SC2 / D-05) | ✓ VERIFIED | `SmtpMailer` in `backend/infrastructure/smtp_mailer.py`; `live.py` wires `resolve_mailer(settings)`; `_build_message` sets only `To=recipient.email`; `test_smtp_mailer_sends_one_message_per_recipient` green |
| 5 | Planned M and delivered N recorded and reported (result, HTTP `delivered_count`, ping payload); two-sentence honest copy, never org-wide claim (SC2 / MAIL-03 / D-09/D-10/D-12) | ✓ VERIFIED | `SendDigestResult.recipient_count/delivered_count`; `SendDigestResponse.delivered_count`; `digest_send` ping carries M/N/status/stop_reason; 4 message-variant tests + `test_send_resolves_audience_from_profiles_and_reports_stub_honesty` green |
| 6 | Mail failure (`SMTPException`/`OSError`/`TimeoutError`/`ValueError`) mapped to domain `MailDeliveryError`, caught alongside `PersistenceError` after publish → published digest returns success, never 500 (SC3 / MAIL-04 / D-88 / CR-01 / WR-01) | ✓ VERIFIED | `smtp_mailer` maps setup + per-recipient errors; `_build_message` inside the per-recipient guard absorbs `ValueError`; `send_digest` catches `(MailDeliveryError, PersistenceError)`; `test_send_mail_failure_after_publish_still_returns_success` + `test_send_audit_failure_after_publish_still_returns_success` + `test_smtp_mailer_send_timeout_failure_maps_to_mail_delivery_error` all green |
| 7 | Bounded per-recipient policy (D-08): continue past a failure, stop after three consecutive, reset on success, report `stop_reason` | ✓ VERIFIED | `CONSECUTIVE_FAILURE_LIMIT = 3` + streak logic in `SmtpMailer`; three `test_smtp_mailer_stops_after_three_consecutive_failures` / `...streak_reset...` tests green; `stop_reason` forwarded into the ping payload |
| 8 | HTTP stays 200 when claim+publish succeeded even if delivery is `partial`/`failed` (SC3 / D-11) | ✓ VERIFIED | `post_shortlist_send` returns the result without mapping contained mail failure to 5xx; `test_admin_send_stays_200_when_mail_partial_after_publish` / `...failed_after_publish` green |
| 9 | Empty audience M=0 still publishes; live status honestly `sent` with N=0 and non-alarming copy (D-04 / RESEARCH Q3) | ✓ VERIFIED | `_delivery_status(0,0) → "sent"`; `_compose_delivery_message` returns «Выпуск опубликован. Получателей нет (0 из 0)»; `test_send_with_empty_audience_still_publishes_sent_status` green |
| 10 | `SMTP_*` read only via `Settings.from_env`/composition; no `os.environ` in adapters; fail-fast `ConfigurationError`; `MAILER` defaults to stub (SC5 / MAIL-05 / D-13/D-14/D-15/D-16) | ✓ VERIFIED | `Settings.from_env` only reader (grep: no `os.environ` in any adapter); `resolve_mailer` raises on incomplete/unknown/invalid config and out-of-range `SMTP_PORT`; timeouts fixed dataclass defaults; `test_stub_mailer.py` D-15/D-16 suite green |
| 11 | Live adapters forward planned `p_recipient_count` (no `update_delivery`, no migration) and page the profiles select (WR-02) | ✓ VERIFIED | `SupabaseDigestPublisher` always forwards `p_recipient_count`, leaves `p_delivery_status` at RPC default; `_list_all_profile_rows` pages with `.range()`; `grep update_delivery` → comment only |
| 12 | SPA `adminApi` + banner carry `delivered_count` and the honest message; runbook documents the digest SMTP contract without claiming GoTrue relay proof (MAIL-03/MAIL-05 / D-12/D-15) | ✓ VERIFIED | `adminApi.js` typedef + mock carry `delivered_count` and «Выпуск опубликован. Доставка писем: stub (0 из 0)»; `AdminDigestPage` shows `result.message`; runbook §4.1.1/§4e document SMTP_* + leave criterion-4 as an ops gap; `tests/admin.spec.js` assertions match the mock string |

**Score:** 12/12 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/src/backend/domain/recipient.py` | Frozen `Recipient` + `is_usable_email` | ✓ VERIFIED | Exists, substantive, wired (ports + adapters + use case) |
| `backend/src/backend/domain/errors.py` | `MailDeliveryError(DomainError)` | ✓ VERIFIED | Defined; caught in `send_digest`; raised at adapter boundary |
| `backend/src/backend/application/ports/mailer.py` | `recipients` param + return-key contract | ✓ VERIFIED | Port extended; typed `Sequence[Recipient]` |
| `backend/src/backend/application/ports/profile_repository.py` | `list_digest_recipients()` | ✓ VERIFIED | Port + both adapters implement it |
| `backend/src/backend/application/ports/digest_publisher.py` | `recipient_count` on claim | ✓ VERIFIED | Port + in-memory + Supabase adapters |
| `backend/src/backend/application/use_cases/send_digest.py` | Audience→claim→mail→honest result + containment | ✓ VERIFIED | Resolves M, stamps it, uses mailer result, contains errors |
| `backend/src/backend/infrastructure/smtp_mailer.py` | Real stdlib SMTP adapter | ✓ VERIFIED | Per-recipient, TLS modes, timeouts, error map, single `To` |
| `backend/src/backend/composition/config_error.py` | `ConfigurationError` | ✓ VERIFIED | Plain `Exception`; raised by `resolve_mailer` |
| `backend/src/backend/composition/mailer_factory.py` | `resolve_mailer(settings)` | ✓ VERIFIED | Selection + fail-fast completeness + TLS validation |
| `backend/src/backend/composition/settings.py` | `SMTP_*` fields + fixed timeouts | ✓ VERIFIED | `smtp_pass` `repr=False`; port range validated (IN-03) |
| `supabase-integration/.../profile_repository.py` | `list_digest_recipients` (service_role, paged) | ✓ VERIFIED | Usable filter + `PersistenceError` boundary + `.range()` paging |
| `supabase-integration/.../digest_publisher.py` | Forward `p_recipient_count` | ✓ VERIFIED | Params include it; `p_delivery_status` untouched |
| `backend/src/backend/interface/http/routes/admin.py` | `SendDigestResponse.delivered_count` + `profiles` wiring | ✓ VERIFIED | Field added; `container.profiles` passed |
| `web/src/services/adminApi.js` | `delivered_count` typedef + stub-honest mock | ✓ VERIFIED | Present; message matches D-12 |
| `docs/agents/local-platform-runbook.md` | Digest SMTP operator contract | ✓ VERIFIED | SMTP_* names, TLS default, fixed timeouts, MAILER flip, rollback, ops gap |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `send_digest.py` | `profile_repository.py` | `profiles.list_digest_recipients()` → M before claim | ✓ WIRED | Called before `claim_and_publish(recipient_count=M)` |
| `send_digest.py` | `mailer.py` / `smtp_mailer.py` | `mailer.send_digest(recipients=…, recipient_count=M)` → `delivered_count` | ✓ WIRED | Result keys consumed (`delivery_status`, `delivered_count`, `stop_reason`) |
| `send_digest.py` | `errors.py` | `except (MailDeliveryError, PersistenceError)` after publish | ✓ WIRED | Both caught; response stays success |
| `composition/live.py` | `mailer_factory.py` | `resolve_mailer(settings)` | ✓ WIRED | Full `Settings` passed; `MAILER=smtp` → `SmtpMailer` |
| `smtp_mailer.py` | `errors.py` | transport errors → `MailDeliveryError` | ✓ WIRED | Setup raises; per-recipient counted |
| `interface/http/routes/admin.py` | `send_digest.py` | `send_digest(..., container.profiles, ...)` → `delivered_count` | ✓ WIRED | 200 on contained failure |
| `web/src/services/adminApi.js` | `AdminDigestPage.jsx` | `sendDigest` → `setBanner(result.message)` | ✓ WIRED | Banner binds to server message |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `send_digest` recipient_count | `recipient_count` | `profiles.list_digest_recipients()` (DB select) | Yes — real audience | ✓ FLOWING |
| `SendDigestResponse.delivered_count` | `delivered_count` | `SendDigestResult` ← mailer post-send result | Yes — per-run N | ✓ FLOWING |
| `SupabaseDigestPublisher.claim_and_publish` | `p_recipient_count` | `recipient_count` kwarg | Yes — persisted planned M | ✓ FLOWING |
| SPA mock (`VITE_USE_MOCKS`) | `delivery_status`/`delivered_count` | Mock fixture | N/A — explicit mock by design | ✓ FLOWING (mock) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full unit suite (phase regression baseline) | `uv run pytest tests/unit -q` | 919 passed | ✓ PASS |
| Phase-specific tests (send_digest, smtp_mailer, recipient_email, stub_mailer, http_admin, supabase recipients contract, profile recipients) | `uv run pytest <7 files> -q` | 139 passed | ✓ PASS |
| Malformed recipient rejected at the audience boundary (CR-01) | `uv run python -c "is_usable_email('victim@x.ru\r\nBcc: attacker@y.ru')"` | `False` (comma-form also `False`; `user@corp.ru` → `True`) | ✓ PASS |
| D-88 audit-failure tripwire preserved | `test_send_digest.py::test_send_audit_failure_after_publish_still_returns_success` present + green | exists; 919-run green | ✓ PASS |
| Adapters read no process environment (MAIL-05) | repo grep `os\.environ` under `**/src/**/*.py` | only `composition/settings.py` (+ unrelated ingestion composition) | ✓ PASS |
| `smtplib` confined to infrastructure | repo grep `import smtplib` under `backend/src` | only `infrastructure/smtp_mailer.py` | ✓ PASS |
| Playwright amended stub-banner assertions (per orchestrator) | `tests/admin.spec.js` string vs `adminApi.js` mock | mock message `«Выпуск опубликован. Доставка писем: stub (0 из 0)»` matches all 3 amended assertions | ✓ PASS (string-aligned; suite run reported 121/121 green by orchestrator) |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh`; phase is not a migration/CLI-tooling phase | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| MAIL-01 | 21-01, 21-02, 21-03 | Real SMTP digest to the `profiles` audience; best-effort after publish (D-88) | ✓ SATISFIED | `SmtpMailer` wired via `resolve_mailer`; audience from profiles; containment tests green |
| MAIL-03 | 21-01, 21-03 | Honest planned M + delivered N reported; copy never claims the whole org | ✓ SATISFIED | Result/HTTP `delivered_count` + `message`; ping payload; org-claim prohibition held |
| MAIL-04 | 21-01, 21-02 | SMTP failures map to a domain error caught alongside `PersistenceError`, bounded timeouts | ✓ SATISFIED | `MailDeliveryError` mapping + `(MailDeliveryError, PersistenceError)` catch; 10s/30s fixed timeouts |
| MAIL-05 | 21-02, 21-03 | `SMTP_*` only via settings/composition; no `os.environ` in adapters; no secret in code | ✓ SATISFIED | `Settings.from_env` sole reader; adapter constructor primitives; `smtp_pass` `repr=False`; runbook names-only |

No orphaned requirements — REQUIREMENTS.md maps exactly MAIL-01/03/04/05 to Phase 21, all declared across the three plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` in phase-modified files | — | — |
| `supabase-integration/.../digest_publisher.py` | 71 | `update_delivery` mentioned only in a comment (documents the deliberate omission) | ℹ️ Info | Not an implementation; prohibition held |

### Human Verification Required

### 1. Ack judgment-tier prohibitions — copy honesty, containment, privacy, config fencing

**Test:** Confirm the flagged prohibition set holds: honest two-sentence copy with no org-wide delivery claim; D-88 containment (mail error after publish → HTTP 200, not 5xx); one-message-per-recipient / no Bcc; `smtplib` confined to infrastructure; no `os.environ` in the adapter; D-16 fail-fast with no silent stub fallback; no `update_delivery`; no signup-via-`Mailer`; runbook does not claim criterion-4 proof; stub tests preserved.
**Expected:** All held (LLM-judge verdict: held for each; evidence in the Prohibitions table and artifacts above).
**Why human:** Judgment-tier flagged prohibitions require an explicit interactive acknowledgement per the phase gate; they are not machine-decidable.

### 2. Live corporate-relay digest smoke (external service / ops)

**Test:** On the VM set `MAILER=smtp` with a complete `SMTP_*` set and send one weekly digest; confirm the corporate relay accepts and delivers it to the `profiles`-derived audience, and that `recipient_count` (planned M) and `delivered_count` (delivered N) match the mailed set.
**Expected:** The relay delivers the per-recipient messages; the admin response/message reports the real N of M; a relay failure yields 200 with honest «Письма не доставлены», never a 500.
**Why human:** External SMTP relay delivery is not exercised by the offline unit suite or the mock-based Playwright suite. D-15 explicitly makes the live flip an ops step and keeps `MAILER=stub` the merge default (inherited Phase 20 criterion-4 gap).

### Gaps Summary

No blocking gaps. All 12 observable truths (roadmap SC1–SC5 + PLAN `must_haves`) are VERIFIED against the code, and the code review's six findings (CR-01, WR-01, WR-02, IN-01, IN-02, IN-03) are all confirmed present in the working tree with the recorded fix commits (`acac872`, `0e6cd3f`, `8cab69a`, `5c3dca3`, `73d4d0f`, `00aae2a`). Status is `human_needed` solely for the judgment-tier flagged prohibitions that require an interactive acknowledgement, plus the ops-only live relay smoke — not because any truth failed.

**Note on ROADMAP SC4 wording vs locked decision D-06 option (i):** the criterion's literal phrasing ("`delivery_status`/`recipient_count` are written from the mailer's post-send result") is satisfied at the *observable* level — a live send can no longer report `stubbed`/`0`, because the API result, `delivered_count`, and the `digest_send` ping carry the mailer's real status/N and the batch row persists the planned M. The batch `delivery_status` column deliberately retains the RPC claim default instead of a post-mail rewrite: CONTEXT D-06 locks option (i) and forbids `update_delivery` for this phase (RESEARCH Pitfall 5 anticipated exactly this distinction). No current surface reads the batch `delivery_status`, so the observable outcome holds; this is a recorded design decision, not a gap.

---

_Verified: 2026-10-16T15:30:02Z_
_Verifier: Claude (gsd-verifier)_
