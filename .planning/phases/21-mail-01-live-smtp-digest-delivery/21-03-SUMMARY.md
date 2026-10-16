---
phase: 21-mail-01-live-smtp-digest-delivery
plan: 03
subsystem: api
tags: [smtp, digest, recipients, http-contract, spa, runbook, mail-honesty]

requires:
  - phase: 21-mail-01-live-smtp-digest-delivery
    provides: "Mailer/ProfileRepository/DigestPublisher port extensions + SendDigestResult honesty + StubMailer (Plan 01)"
  - phase: 21-mail-01-live-smtp-digest-delivery
    provides: "Real SmtpMailer + Settings SMTP_* + resolve_mailer fail-fast (Plan 02); resolve_mailer lives in composition/mailer_factory.py"

provides:
  - "SupabaseProfileRepository.list_digest_recipients (service_role; usable-email filter; D-01/D-02/D-03)"
  - "SupabaseDigestPublisher forwards planned M as p_recipient_count; p_delivery_status stays RPC-default (D-06 option i)"
  - "HTTP SendDigestResponse.delivered_count (planned M + delivered N) with HTTP 200 containment (D-10/D-11)"
  - "SPA adminApi delivered_count contract + D-12 stub-honest mock copy"
  - "Runbook digest SMTP smoke/rollback + MAIL-05 config boundary; criterion-4 relay proof left as ops gap (D-15)"

affects: [21-verify-work, 21-ship]

actuals:
  tokens: 7121
  tasks: 3
  commits: 5
  plan_head_before: b6e322ea24157ab0f9dff5078c9613cb430b656e
  plan_head_after: caf1bb42270a3c647dd9ec38f9a223c91140e037

tech-stack:
  added: []
  patterns:
    - "Audience adapter boundary: filter usable emails in Python, map SDK failures to PersistenceError, list on the service_role client (RESEARCH Pitfall 7)"
    - "Option (i) honesty: planned M rides p_recipient_count at claim; live N/status ride the API result + pings, never a post-mail update_delivery"
    - "HTTP contract containment: a partial/failed mail after a successful publish stays HTTP 200 with honest N/M (D-11)"

key-files:
  created:
    - tests/unit/test_profile_repository_recipients.py
    - tests/unit/test_supabase_digest_recipients_contract.py
  modified:
    - supabase-integration/src/supabase_integration/profile_repository.py
    - supabase-integration/src/supabase_integration/digest_publisher.py
    - backend/src/backend/interface/http/routes/admin.py
    - tests/unit/test_http_admin.py
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx
    - docs/agents/local-platform-runbook.md
    - tests/admin.spec.js

key-decisions:
  - "SupabaseDigestPublisher always forwards p_recipient_count (default 0), mirroring the port default; the RPC default keeps p_delivery_status untouched (D-06 option i — no update_delivery, no migration)"
  - "list_digest_recipients runs on the service_role client wired in live.py: the profiles_select_own RLS policy would otherwise hide the audience (RESEARCH Pitfall 7)"
  - "SendDigestResponse.delivered_count is additive with default 0 so existing clients stay valid; the route never maps contained mail failures to 5xx (D-11)"
  - "The SPA mock message adopts the D-12 stub-honest copy; the Playwright stub-banner assertions were amended to match (mock-only change, no UI logic change)"
  - "AdminDigestPage keeps showing result.message; only the stale «Отправка записана» fallback was replaced with «Выпуск опубликован»"

patterns-established:
  - "Fake-client contract for recipients: one test doubles the select path, one doubles the RPC path — no network, asserts parameter forwarding"

requirements-completed: [MAIL-01, MAIL-03, MAIL-05]

coverage:
  - id: D1
    description: "In-memory digest audience: all roles with a usable profiles.email included; empty/malformed excluded and logged (D-01/D-02/D-03)"
    requirement: MAIL-03
    verification:
      - kind: unit
        ref: "tests/unit/test_profile_repository_recipients.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Supabase list_digest_recipients maps usable rows to Recipient and maps SDK failures to PersistenceError; claim_and_publish forwards p_recipient_count without p_delivery_status (D-01/D-02/D-06)"
    requirement: MAIL-03
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_digest_recipients_contract.py"
        status: pass
    human_judgment: false
  - id: D3
    description: "HTTP /admin/shortlist/send returns delivered_count (planned M + delivered N) and stays HTTP 200 when mail is stubbed/partial/failed after publish (D-10/D-11/D-12)"
    requirement: MAIL-03
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_send_happy_path_publishes_and_returns_issue_link"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_send_stays_200_when_mail_partial_after_publish"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_send_stays_200_when_mail_failed_after_publish"
        status: pass
    human_judgment: false
  - id: D4
    description: "SPA adminApi.sendDigest typedef + mock carry delivered_count and the D-12 stub-honest message; banner keeps rendering result.message"
    requirement: MAIL-03
    verification:
      - kind: other
        ref: "node -e \"... /delivered_count/.test(adminApi) ...\" (Plan 03 task 3 gate)"
        status: pass
    human_judgment: true
    rationale: "The string gate proves the field exists, but the stub-copy wording and the amended Playwright banner assertions (tests/admin.spec.js) were not executed in this plan — no Playwright run."
  - id: D5
    description: "Runbook documents the digest SMTP operator contract: SMTP_FROM, starttls/587 default, Settings-fixed 10s/30s timeouts, MAILER=stub default, ConfigurationError fail-fast, smoke + one-command rollback; Phase 20 criterion-4 relay proof left as an ops gap (D-13/D-14/D-15/D-16/MAIL-05)"
    requirement: MAIL-05
    verification: []
    human_judgment: true
    rationale: "Ops prose doc — the string gate only asserts token presence, not operational correctness; the criterion-4 relay proof is deliberately left unclaimed (D-15)."

duration: 9min
completed: 2026-10-16
status: complete
---

# Phase 21 Plan 03: Recipients adapters + HTTP delivered_count + SPA + runbook Summary

**Live Supabase digest recipients (service_role, usable-email filtered) + planned `p_recipient_count` forwarding, an additive HTTP `delivered_count` that stays 200 through contained mail failure, the SPA contract, and the runbook digest SMTP smoke/rollback**

## Performance

- **Duration:** 9 min
- **Started:** 2026-10-16T14:53:00Z
- **Completed:** 2026-10-16T15:02:00Z
- **Tasks:** 3 (all TDD: RED → GREEN)
- **Files modified:** 10 (2 created, 8 modified)

## Accomplishments
- `SupabaseProfileRepository.list_digest_recipients` lists every profile with a usable email on the **service_role** client (D-01), filters empty/malformed rows in Python and logs them (D-02), and maps SDK failures to `PersistenceError`; `profiles.email` is the only address source (D-03).
- `SupabaseDigestPublisher.claim_and_publish` now forwards the planned audience M as `p_recipient_count` and deliberately leaves `p_delivery_status` at the RPC default — option (i), **no `update_delivery`**, no new migration (D-06).
- `SendDigestResponse` gains additive `delivered_count` mapped from `SendDigestResult` (D-10); a contained mail partial/failure after a successful publish stays **HTTP 200** with honest N/M copy (D-11) — proven by two new route tests.
- `web/src/services/adminApi.js` `sendDigest` typedef + mock carry `delivered_count` and the D-12 stub-honest message «Выпуск опубликован. Доставка писем: stub (0 из 0)»; `AdminDigestPage` keeps rendering `result.message` (stale fallback copy removed).
- Runbook §4e documents the **MAIL-05** config boundary (adapters read no `os.environ`), the digest SMTP smoke steps and one-command rollback, and explicitly leaves the Phase 20 criterion-4 relay proof as an inherited ops gap (D-15).

## Task Commits

Each task was committed atomically, RED before GREEN:

1. **Task 1 RED: recipients adapters + p_recipient_count contract** — `0642c00` (test)
2. **Task 1 GREEN: live digest recipients + planned p_recipient_count** — `a4caecc` (feat)
3. **Task 2 RED: HTTP delivered_count + D-11 containment** — `e2b3e2a` (test)
4. **Task 2 GREEN: SendDigestResponse.delivered_count + honest send copy** — `9af47f8` (feat)
5. **Task 3: SPA delivered_count + runbook digest SMTP notes** — `caf1bb4` (feat)

**Plan metadata:** the `docs(21-03): complete recipients adapters + HTTP delivered_count + SPA + runbook plan` commit (SUMMARY.md + STATE.md + ROADMAP.md + REQUIREMENTS.md + WINDOWS.md)

_RED was observed for real both times: Task 1 as `AttributeError: 'SupabaseProfileRepository' object has no attribute 'list_digest_recipients'`; Task 2 as `KeyError: 'delivered_count'` on the response body. Task 3's RED was the SPA/runbook string gate failing with `MISSING: adminApi delivered_count`._

## Files Created/Modified
- `tests/unit/test_profile_repository_recipients.py` — **NEW**: in-memory D-01/D-02/D-03 audience honesty (3 tests).
- `tests/unit/test_supabase_digest_recipients_contract.py` — **NEW**: fake-client contract for `list_digest_recipients` + `p_recipient_count` forwarding (3 tests).
- `supabase-integration/src/supabase_integration/profile_repository.py` — `list_digest_recipients` (service_role select, usable filter, `PersistenceError` boundary, exclusion logging).
- `supabase-integration/src/supabase_integration/digest_publisher.py` — `recipient_count` kwarg → `p_recipient_count`; `p_delivery_status` untouched (D-06).
- `backend/src/backend/interface/http/routes/admin.py` — `SendDigestResponse.delivered_count`; mapped from `result.delivered_count`; refreshed route summary/description.
- `tests/unit/test_http_admin.py` — amended 3 send assertions for `delivered_count`; added partial/failed D-11 containment tests + a status-mailer double.
- `web/src/services/adminApi.js` — `delivered_count` in the `sendDigest` typedef and mock; D-12 stub-honest mock message.
- `web/src/pages/AdminDigestPage.jsx` — stale «Отправка записана» fallback replaced with «Выпуск опубликован» (banner still shows `result.message`).
- `docs/agents/local-platform-runbook.md` — digest SMTP smoke/rollback + MAIL-05 boundary; Playwright gate note updated to the new copy.
- `tests/admin.spec.js` — 3 stub-banner assertions amended to the new mock message (mock-only change).

## Decisions Made
- **`list_digest_recipients` runs on the service_role client** already wired in `live.py` — a user-scoped client would return M=0 under `profiles_select_own` (RESEARCH Pitfall 7); the adapter itself is unchanged and no RLS was widened.
- **`p_recipient_count` forwarded unconditionally** (default 0), mirroring the port default; the RPC default keeps `p_delivery_status` untouched — option (i) with no post-mail rewrite.
- **`delivered_count` is additive with default 0** so existing clients stay valid; the route relies on the use case's containment and never maps a contained mail failure to 5xx (D-11).
- **Playwright assertions amended rather than re-architected:** the mock message change is the only driver; the spec's user journeys are untouched.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Amended `tests/admin.spec.js` stub-banner assertions (plan listed them as optional)**
- **Found during:** Task 3 (SPA contract + runbook)
- **Issue:** Changing the `adminApi.js` mock message to the D-12 stub-honest copy broke three `tests/admin.spec.js` assertions that expect the removed «Отправка записана» text (the plan's behaviour note allowed amending the assertion only if one existed — it did).
- **Fix:** Updated the three `getByText("…")` assertions and their surrounding test titles to «Выпуск опубликован. Доставка писем: stub (0 из 0)». No other spec behaviour changed.
- **Files modified:** `tests/admin.spec.js`
- **Verification:** `gsd windows append --kind unrun-verify` recorded that the amended spec was not executed; the mock message string was cross-checked against the backend D-12 copy in `send_digest._compose_delivery_message`.
- **Committed in:** `caf1bb4`

**2. [Rule 1 - Bug] Removed the stale `AdminDigestPage` send-banner fallback copy**
- **Found during:** Task 3
- **Issue:** `setBanner(result.message || 'Отправка записана')` still held the pre-Phase-21 copy; with the honest message now always present it was dead, but a stale honesty claim would surface if `message` were ever empty (T-21-08).
- **Fix:** Fallback replaced with the neutral, honest «Выпуск опубликован» (no delivery claim).
- **Files modified:** `web/src/pages/AdminDigestPage.jsx`
- **Verification:** `npm --prefix web run lint` reports only pre-existing warnings/errors unrelated to this file.
- **Committed in:** `caf1bb4`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both are copy/contract-alignment consequences of the intended mock change. No scope creep: no new migration, no `update_delivery`, no RLS change, no adapter behaviour change beyond the plan.

## Issues Encountered
None.

## TDD Gate Compliance

| Task | RED | GREEN | REFACTOR | Status |
| ---- | --- | ----- | -------- | ------ |
| 1 — recipients adapters | `0642c00` (test) | `a4caecc` (feat) | not needed | Pass |
| 2 — HTTP delivered_count | `e2b3e2a` (test) | `9af47f8` (feat) | not needed | Pass |
| 3 — SPA + runbook | string gate failed (`MISSING: adminApi delivered_count`) | `caf1bb4` (feat) | not needed | Pass |

Task 1's in-memory file landed as a green characterisation of Plan 01's `InMemoryProfileRepository.list_digest_recipients` (the RED came from the Supabase fake-client contract); Task 3 has no unit runner for the JS mock, so the plan's node string gate served as the failing check.

## Known Stubs

None. No placeholder branches, hardcoded empty values, or unwired data sources were introduced; the SPA mock continues to be an explicit mock (`VITE_USE_MOCKS`), not a production stub.

## Deferred / Out of Scope

- **Playwright suite not run** in this plan (the plan's `<verify>` is the node string gate + pytest). The amended `tests/admin.spec.js` stub-banner assertions are recorded as an open `unrun-verify` entry in `.planning/WINDOWS.md` for the ship gate.
- **Live corporate-relay smoke** remains an **ops** step after merge (D-15); no credentials or live network calls were used. `MAILER=stub` remains the default.

## User Setup Required

None for code merge — `MAILER=stub` is the default. Live delivery requires the operator to set `MAILER=smtp` plus the complete `SMTP_*` set after the relay smoke (runbook §4e / §4.1.1).

## Next Phase Readiness

- Phase 21's three plans are complete: the `Mailer` port, the real `SmtpMailer`, the fail-fast resolve, the live/in-memory recipients adapters, the HTTP `delivered_count` contract, and the SPA/runbook honesty are all landed and covered.
- Ready for `/gsd-verify-work 21`. The `Mailer` port contract is unchanged from Plan 02, so no further adapter edits are expected.
- No blockers.

## Self-Check: PASSED

- `tests/unit/test_profile_repository_recipients.py` exists on disk: FOUND
- `tests/unit/test_supabase_digest_recipients_contract.py` exists on disk: FOUND
- Commits `0642c00`, `a4caecc`, `e2b3e2a`, `9af47f8`, `caf1bb4` present in `git log`: FOUND
- `uv run pytest tests/unit -q` → 890 passed (baseline before plan: 882)

---
*Phase: 21-mail-01-live-smtp-digest-delivery*
*Completed: 2026-10-16*
