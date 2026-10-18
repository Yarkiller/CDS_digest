---
phase: 05-admin-digest-publish
plan: 03
subsystem: api
tags: [fastapi, mailer, stub-mailer, preview, send-digest, publish-on-send, require_admin, tdd, ports-adapters]

requires:
  - phase: 05-admin-digest-publish
    provides: ShortlistRepository GET/decision + require_admin + InMemoryShortlistRepository
provides:
  - Mailer Protocol + StubMailer (delivery_status=stubbed) + SmtpMailer NotImplemented
  - preview_digest_email use-case (approved∩ready DTO; EmptySendPoolError)
  - send_digest claim→publish→mail→audit with D-88 publish-on-send
  - IssueRepository.publish + ShortlistRepository.claim_sent (in-memory atomic)
  - POST /admin/shortlist/preview and POST /admin/shortlist/send behind require_admin
  - DraftInSendPoolError / AlreadySentError / EmptySendPoolError HTTP mapping
affects:
  - 05-04 AdminDigestPage SPA preview/send UX
  - 05-05 live ShortlistRepository.claim_sent + IssueRepository.publish adapters
  - ADMIN-08 returnUrl via /issues/{n} in stub body

actuals:
  tokens: 20449
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Mailer Protocol + StubMailer honesty (delivery_status=stubbed, recipient_count=0)"
    - "send_digest: validate → claim_sent → publish → mailer → PingRecorder kind=digest_send"
    - "MAILER=smtp fail-fast at resolve_mailer; no live SMTP packages"

key-files:
  created:
    - backend/src/backend/application/ports/mailer.py
    - backend/src/backend/infrastructure/stub_mailer.py
    - backend/src/backend/application/use_cases/preview_digest_email.py
    - backend/src/backend/application/use_cases/send_digest.py
    - tests/unit/test_preview_digest.py
    - tests/unit/test_send_digest.py
    - tests/unit/test_stub_mailer.py
  modified:
    - backend/src/backend/application/ports/issue_repository.py
    - backend/src/backend/application/ports/shortlist_repository.py
    - backend/src/backend/domain/errors.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/interface/http/routes/admin.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/settings.py
    - backend/src/backend/composition/live.py
    - tests/unit/test_http_admin.py

key-decisions:
  - "ACK D-88 (ack-d88): successful send MUST publish digest_issues + set sent_at — no stub-mail-without-publish"
  - "resolve_mailer takes mailer mode string (not Settings) to avoid stub_mailer↔composition circular import"
  - "In-memory claim_sent simulates atomic sent_at IS NULL; live RPC deferred to 05-05"
  - "HTTP draft_in_send_pool detail is {code, draft_material_ids}; already_sent is plain string detail"

patterns-established:
  - "Pattern: preview never mutates sent_at; send re-validates pool server-side"
  - "Pattern: success message always «Отправка записана» — never subscriber-count claims (D-87)"
  - "Pattern: stub email body embeds same-origin /issues/{number} for ADMIN-08 returnUrl"

requirements-completed: [ADMIN-03, ADMIN-04, ADMIN-07, ADMIN-08]

coverage:
  - id: D1
    description: "Email preview DTO lists exactly approved∩ready materials; empty pool errors; never sets sent_at"
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/unit/test_preview_digest.py#test_preview_lists_only_approved_ready_items"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_preview_returns_approved_ready_only_without_sent_at"
        status: pass
    human_judgment: false
  - id: D2
    description: "StubMailer returns delivery_status=stubbed and recipient_count=0; SMTP fail-fast"
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_stub_mailer_returns_stubbed_delivery_and_zero_recipients"
        status: pass
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py#test_resolve_mailer_smtp_fails_fast_at_startup"
        status: pass
    human_judgment: false
  - id: D3
    description: "Successful send publishes one issue, claims sent_at, stubs mail with /issues/{n}, audits digest_send"
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_happy_path_publishes_issue_claims_sent_and_stubs_mail"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_send_happy_path_publishes_and_returns_issue_link"
        status: pass
    human_judgment: false
  - id: D4
    description: "Approved draft in pool blocks send with DraftInSendPoolError → HTTP 400"
    requirement: ADMIN-03
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_blocks_approved_draft_in_pool"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_send_draft_in_pool_returns_400"
        status: pass
    human_judgment: false
  - id: D5
    description: "Repeat send → AlreadySentError / HTTP 409; no second issue or stub send"
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_repeat_after_success_is_idempotent_409_path"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_send_second_returns_409_already_sent"
        status: pass
    human_judgment: false
  - id: D6
    description: "Stub email body contains /issues/{number} for ADMIN-08 returnUrl after login"
    requirement: ADMIN-08
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_happy_path_publishes_issue_claims_sent_and_stubs_mail"
        status: pass
    human_judgment: false
  - id: D7
    description: "Non-admin cannot preview or send — HTTP 403"
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_preview_employee_returns_403"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_send_employee_returns_403"
        status: pass
    human_judgment: false

duration: 18min
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 03: Preview + StubMailer Send Summary

**Mandatory email preview + StubMailer send that publishes a digest issue once, blocks drafts/empty/already-sent, and embeds `/issues/{n}` for ADMIN-08**

## Performance

- **Duration:** 18min
- **Started:** 2026-09-21T14:47:15Z
- **Completed:** 2026-09-21T15:05:00Z
- **Tasks:** 3 (1 checkpoint ACK + 2 TDD auto)
- **Files modified:** 16

## Accomplishments

- ACK D-88 locked: publish-on-send is mandatory (no stub-mail-without-publish path)
- `preview_digest_email` returns approved∩ready subject/body/items; empty pool → `EmptySendPoolError`; never sets `sent_at`
- `StubMailer` honesty (`delivery_status=stubbed`, `recipient_count=0`); `MAILER=smtp` fails fast; `SmtpMailer.send` raises `NotImplementedError`
- `send_digest` validates → `claim_sent` → `IssueRepository.publish` → mailer → `PingRecorder(kind=digest_send)` with success copy «Отправка записана»
- HTTP `POST /admin/shortlist/preview` and `POST /admin/shortlist/send` behind `require_admin` (400 draft/empty, 409 already sent, 403 employee)

## Task Commits

1. **Task 1: Acknowledge locked D-88 publish-on-send** — ACK'd by user (`ack-d88`); no code commit
2. **Task 2 RED: Preview + StubMailer tests** — `9e84345` (test)
3. **Task 2 GREEN: preview_digest_email + StubMailer** — `7347d5c` (feat)
4. **Task 3 RED: send_digest + HTTP tests** — `ad534b3` (test)
5. **Task 3 GREEN: send_digest + preview/send routes** — `96d4a91` (feat)

**Plan metadata:** `8f5b6dc` (docs: complete plan SUMMARY); `0f32ada` (docs: STATE/ROADMAP/REQUIREMENTS)

## Files Created/Modified

- `backend/.../ports/mailer.py` — Mailer Protocol
- `backend/.../infrastructure/stub_mailer.py` — StubMailer + SmtpMailer + resolve_mailer
- `backend/.../use_cases/preview_digest_email.py` — ADMIN-04 preview DTO
- `backend/.../use_cases/send_digest.py` — D-88 publish-on-send orchestration
- `backend/.../ports/issue_repository.py` — `publish(...)`
- `backend/.../ports/shortlist_repository.py` — `claim_sent(...)`
- `backend/.../interface/http/routes/admin.py` — preview + send routes
- `tests/unit/test_preview_digest.py`, `test_stub_mailer.py`, `test_send_digest.py`, `test_http_admin.py`

## Decisions Made

- **ACK D-88 (`ack-d88`):** Successful send publishes `digest_issues` and sets batch `sent_at` on the same path — stub-mail-without-publish is not allowed
- `resolve_mailer(mailer_mode: str)` instead of Settings object to avoid circular import with composition
- In-memory `claim_sent` simulates atomic `sent_at IS NULL`; live concurrency RPC flagged for 05-05
- Success messaging contract: «Отправка записана» only (D-87)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Circular import stub_mailer ↔ composition**
- **Found during:** Task 3 GREEN (import of StubMailer from tests)
- **Issue:** `stub_mailer` imported `Settings` from `composition`, which imports `container`, which imports `StubMailer`
- **Fix:** `resolve_mailer` takes a mode string; Settings stays out of infrastructure
- **Files modified:** `stub_mailer.py`, `live.py`, `test_stub_mailer.py`
- **Verification:** 29 unit tests green
- **Committed in:** `96d4a91`

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Necessary for import graph; no scope change

## Issues Encountered

None beyond the circular-import fix above.

## User Setup Required

None - no external service configuration required. `MAILER=stub` is the default.

## Next Phase Readiness

- Backend preview/send loop complete in-memory; ready for 05-04 SPA AdminDigestPage
- Live `claim_sent` / `publish` adapters + batch delivery columns remain for 05-05
- Session preview gate (D-86 client-side) is SPA responsibility in 05-04; server still re-validates on send

## Self-Check: PASSED

- FOUND: `backend/src/backend/application/ports/mailer.py`
- FOUND: `backend/src/backend/infrastructure/stub_mailer.py`
- FOUND: `backend/src/backend/application/use_cases/preview_digest_email.py`
- FOUND: `backend/src/backend/application/use_cases/send_digest.py`
- FOUND: `.planning/phases/05-admin-digest-publish/05-03-SUMMARY.md`
- FOUND: commits `9e84345`, `7347d5c`, `ad534b3`, `96d4a91`

---
*Phase: 05-admin-digest-publish*
*Completed: 2026-09-21*
