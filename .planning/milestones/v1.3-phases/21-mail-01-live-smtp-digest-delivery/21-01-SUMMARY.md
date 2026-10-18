---
phase: 21-mail-01-live-smtp-digest-delivery
plan: 01
subsystem: api
tags: [smtp, mailer, digest, ports-and-adapters, mail-honesty]

requires:
  - phase: 05-admin-digest-publish
    provides: claim_and_publish RPC + StubMailer + send_digest publish-on-send path
  - phase: 20-mail-02-signup-confirmation-mail
    provides: SMTP_* env lane documentation (GoTrue keeps owning signup mail)
provides:
  - "Recipient frozen DTO + is_usable_email predicate (D-02)"
  - "MailDeliveryError DomainError subclass (MAIL-04)"
  - "Mailer/ProfileRepository/DigestPublisher port extensions (recipients, list_digest_recipients, recipient_count)"
  - "send_digest honesty: planned M at claim, delivered N, D-09/D-12 two-sentence message, mail containment"
  - "StubMailer recipients echo + delivered_count=0"
affects: [21-02, 21-03]

actuals:
  tokens: 10174
  tasks: 2
  commits: 3
  plan_head_before: 1b517ffc9a8e17b42ecc66b6f3104778cfc4104d
  plan_head_after: a6c57da4448aa3accea96a40736f28f2798732bc

tech-stack:
  added: []
  patterns:
    - "Audience resolution before the atomic claim: planned M stamped at claim (D-06 option i), N/status on result+pings"
    - "Adapter-boundary domain error (MailDeliveryError) caught alongside PersistenceError after publish (D-88)"

key-files:
  created:
    - backend/src/backend/domain/recipient.py
  modified:
    - backend/src/backend/domain/errors.py
    - backend/src/backend/application/ports/mailer.py
    - backend/src/backend/application/ports/profile_repository.py
    - backend/src/backend/application/ports/digest_publisher.py
    - backend/src/backend/application/use_cases/send_digest.py
    - backend/src/backend/infrastructure/stub_mailer.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/interface/http/routes/admin.py
    - tests/unit/test_send_digest.py
    - tests/unit/test_http_admin.py
    - tests/unit/test_preview_digest.py

key-decisions:
  - "delivery_status is read from the mailer result, not the batch row; M=0 on a live path is honestly `sent` with N=0 (RESEARCH Q3)"
  - "Batch row keeps planned M only; live N/status ride SendDigestResult + the digest_send ping payload (D-06 option i, no post-mail rewrite)"

patterns-established:
  - "Planned-vs-delivered honesty: resolve audience -> stamp planned M -> mail -> return N/status + two-sentence message"

requirements-completed: [MAIL-01, MAIL-03, MAIL-04]

coverage:
  - id: D1
    description: "Audience M resolved from all usable profiles emails (admin + employee), empty/malformed excluded and logged (D-01/D-02/D-03)"
    requirement: MAIL-01
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_resolves_audience_from_profiles_and_reports_stub_honesty"
        status: pass
    human_judgment: false
  - id: D2
    description: "Planned M stamped at claim; stub path returns delivery_status=stubbed, delivered_count=0, D-12 stub copy (D-06/D-10/D-12)"
    requirement: MAIL-03
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_resolves_audience_from_profiles_and_reports_stub_honesty"
        status: pass
    human_judgment: false
  - id: D3
    description: "Empty/malformed-only audience (M=0) still publishes; live status is `sent` with N=0 and non-alarming copy (D-04 / Q3)"
    requirement: MAIL-01
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_with_empty_audience_still_publishes_sent_status"
        status: pass
    human_judgment: false
  - id: D4
    description: "MailDeliveryError after publish is contained: still success, issue persisted, status=failed, N=0 (MAIL-04 / D-88)"
    requirement: MAIL-04
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_mail_failure_after_publish_still_returns_success"
        status: pass
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_audit_failure_after_publish_still_returns_success"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-09 two-sentence message variants for live sent/partial/failed via fake mailer (not stub-labelled)"
    requirement: MAIL-03
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_live_sent_message_is_two_honest_sentences"
        status: pass
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_live_partial_message_reflects_planned_vs_delivered"
        status: pass
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_live_failed_message_is_full_mail_fail_copy"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-10-16
status: complete
---

# Phase 21 Plan 01: Tracer — audience honesty + mail containment with stub Summary

**Digest audience resolved from all usable `profiles` emails with planned-M/delivered-N honesty, a domain `MailDeliveryError` contained after publish, and D-09/D-12 two-sentence copy — all sealed with `StubMailer` before live SMTP lands in Plan 02**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-16T14:28:00Z
- **Completed:** 2026-10-16T14:39:22Z
- **Tasks:** 2
- **Files modified:** 12 (1 created, 11 modified)

## Accomplishments
- `Recipient` frozen DTO + `is_usable_email` predicate; `MailDeliveryError(DomainError)` added (MAIL-04).
- `Mailer.send_digest` gains `recipients`; `ProfileRepository.list_digest_recipients()`; `DigestPublisher.claim_and_publish(recipient_count=M)` (D-01…D-06).
- `send_digest` resolves M **before** the claim, stamps planned M, uses the mailer result for status/N, and composes honest two-sentence Russian copy (stub / sent / partial / failed / M=0) — never an org-wide claim.
- `MailDeliveryError` is caught alongside `PersistenceError` after publish, so a published digest never 500s (D-88); `test_send_audit_failure_after_publish_still_returns_success` preserved.
- Empty/malformed-only audience (M=0) still publishes with `delivery_status=sent`, `delivered_count=0` and non-alarming copy (RESEARCH Q3 locked).
- `digest_send` ping payload carries the honesty triplet (`recipient_count`, `delivered_count`, `delivery_status`, optional `stop_reason`).

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end honesty-with-stub (tracer)** - `174a8c5` (feat)
2. **Task 2: D-09 fake-mailer message variants** - `71f9e03` (test)
3. **Docstring hygiene (no literal tokens)** - `a6c57da` (docs)

**Plan metadata:** `_pending_` (docs: complete plan)

_Note: the tracer (TDD) RED was observed as an ImportError on `MailDeliveryError` before any production edit; the Task 2 RED (partial/failed message mismatch) was observed then turned GREEN._

## Files Created/Modified
- `backend/src/backend/domain/recipient.py` - NEW: `Recipient` DTO + `is_usable_email` (D-02)
- `backend/src/backend/domain/errors.py` - `MailDeliveryError(DomainError)`
- `backend/src/backend/application/ports/mailer.py` - `recipients` + return-key contract (status/N/M)
- `backend/src/backend/application/ports/profile_repository.py` - `list_digest_recipients()`
- `backend/src/backend/application/ports/digest_publisher.py` - `recipient_count` kwarg on `claim_and_publish`
- `backend/src/backend/application/use_cases/send_digest.py` - audience→claim→mail→honest result; `delivered_count`; containment
- `backend/src/backend/infrastructure/stub_mailer.py` - StubMailer recipients echo + `delivered_count=0`; SmtpMailer placeholder (Plan 02)
- `backend/src/backend/tests_support/in_memory.py` - `list_digest_recipients` + claim stamps planned M
- `backend/src/backend/interface/http/routes/admin.py` - passes `container.profiles` into `send_digest`
- `tests/unit/test_send_digest.py` - amended stub/message asserts; new audience, M=0, containment, ping, live-variant tests
- `tests/unit/test_http_admin.py` - amended send-success message assertions to the honest copy
- `tests/unit/test_preview_digest.py` - fixture/pass `profiles` into `send_digest`

## Decisions Made
- **Status provenance:** `SendDigestResult.delivery_status` comes from the **mailer result** (not the batch row). The batch keeps the claim-era default; live N/status ride the result + `pings` (D-06 option i).
- **M=0 token:** live/empty audience reports `sent` with N=0 and «Выпуск опубликован. Получателей нет (0 из 0)»; the stub path stays `stubbed` (RESEARCH Q3 locked).
- **Message copy:** two sentences, no trailing period; stub line matches the locked «Выпуск опубликован. Доставка писем: stub (0 из M)».

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated `send_digest` callers for the new required `profiles` port**
- **Found during:** Task 1
- **Issue:** The plan added a required positional `profiles: ProfileRepository` to `send_digest`, which broke the HTTP caller and two test callers not listed in the plan's `files_modified`.
- **Fix:** Passed `container.profiles` in `admin.py`; passed a fresh `InMemoryProfileRepository()` in `test_preview_digest.py`; added `profiles` to every `send_digest(...)` call in `test_send_digest.py`.
- **Files modified:** `backend/.../interface/http/routes/admin.py`, `tests/unit/test_preview_digest.py`, `tests/unit/test_send_digest.py`
- **Verification:** full unit suite green (845 passed)
- **Committed in:** `174a8c5`

**2. [Rule 3 - Blocking] Amended HTTP send-success message assertions**
- **Found during:** Task 1
- **Issue:** The honest D-12 copy replaced «Отправка записана» in the shared HTTP send path, so three `test_http_admin.py` assertions failed. The plan assigned the HTTP/SPA contract to Plan 03, but the message change is Task 1's deliverable.
- **Fix:** Updated the three assertions to «Выпуск опубликован. Доставка писем: stub (0 из 1)» (the seeded admin profile is the only usable recipient). `SendDigestResponse.delivered_count` and SPA changes remain Plan 03.
- **Files modified:** `tests/unit/test_http_admin.py`
- **Verification:** `uv run pytest tests/unit -q` → 845 passed
- **Committed in:** `174a8c5`

**3. [Rule 2 - Missing critical] Task 2 landed as characterisation tests (composer branches shipped in Task 1)**
- **Found during:** Task 2
- **Issue:** Task 1 was instructed to compose the message «per D-09/D-12», which D-09 defines across sent/partial/failed; the composer therefore already branched on live statuses when Task 2 began, so Task 2's tests passed without new production code.
- **Fix:** Kept the task boundary honest by verifying the tests are meaningful — temporarily stripping the live-status branches produced the expected RED (2 failures on partial/failed), then restoring them for GREEN. Task 2 landed as a `test(...)` commit pinning the contract.
- **Files modified:** `tests/unit/test_send_digest.py` (production file unchanged vs Task 1)
- **Verification:** RED → GREEN observed; `uv run pytest tests/unit/test_send_digest.py -q` → 22 passed
- **Committed in:** `71f9e03`

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 missing critical)
**Impact on plan:** All three were forced by the tracer's required port injection and the D-09 copy contract. No scope creep — live `SmtpMailer` (Plan 02) and HTTP/SPA `delivered_count` (Plan 03) were deliberately left untouched.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required (`MAILER=stub` remains the default).

## Next Phase Readiness
- Ready for **21-02** (`SmtpMailer` + `SMTP_*` Settings + `ConfigurationError` fail-fast) — the `Mailer` port, `MailDeliveryError`, and honesty contract are now fixed and covered.
- Ready for **21-03** (Supabase `list_digest_recipients` + `p_recipient_count` forwarding + HTTP `delivered_count` + SPA copy).
- No blockers. `test_send_audit_failure_after_publish_still_returns_success` (D-88 tripwire) and the stub-honesty tests were preserved.

## Self-Check: PASSED

- `backend/src/backend/domain/recipient.py` exists on disk: FOUND
- Commits `174a8c5`, `71f9e03`, `a6c57da` present in `git log`: FOUND
- `uv run pytest tests/unit -q` → 845 passed (baseline before plan: 842)

---
*Phase: 21-mail-01-live-smtp-digest-delivery*
*Completed: 2026-10-16*
