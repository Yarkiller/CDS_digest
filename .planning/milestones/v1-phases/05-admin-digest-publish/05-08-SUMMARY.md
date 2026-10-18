---
phase: 05-admin-digest-publish
plan: 08
subsystem: ui
tags: [fastapi, react, playwright, shortlist, digest, reorder, TDD, G-05-1]

requires:
  - phase: 05-admin-digest-publish
    provides: Preview composition spine (intro + blocks → preview.body) from 05-07
provides:
  - Reorderable «Блоки выпуска» material/text UI driving preview order
  - Optional interstitial text blocks between articles
  - send_digest material_ids permutation → publication and mail order
  - Playwright gate for intro + interstitial + «Отправка записана» / «К выпуску»
affects: [05-09-gap-closure, digest-send-composition]

actuals:
  tokens: 8650
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - issueBlocks session state (material | text) syncs to approved∩ready
    - material_ids exact-set permutation validated in use-case; ranks rewritten in Supabase adapter before claim RPC

key-files:
  created: []
  modified:
    - web/src/pages/AdminDigestPage.jsx
    - web/src/services/adminApi.js
    - tests/admin.spec.js
    - tests/unit/test_send_digest.py
    - tests/unit/test_http_admin.py
    - backend/src/backend/application/use_cases/send_digest.py
    - backend/src/backend/application/ports/digest_publisher.py
    - backend/src/backend/tests_support/in_memory.py
    - backend/src/backend/domain/errors.py
    - backend/src/backend/interface/http/routes/admin.py
    - supabase-integration/src/supabase_integration/digest_publisher.py

key-decisions:
  - "Button reorder (not HTML5 DnD) for a11y and Playwright stability"
  - "Publication order via material_ids + rank rewrite before claim_and_publish_digest (no new RPC)"
  - "Human-verify gap: combined Playwright asserts intro + interstitial in preview.body, not titles-only list"

patterns-established:
  - "SPA confirmSend posts material_ids from issueBlocks material order"
  - "InvalidSendOrderError → HTTP 400 invalid_send_order"

requirements-completed: [ADMIN-04, ADMIN-07, ADMIN-08]

coverage:
  - id: D1
    description: Reorderable issue blocks + optional interstitial drive preview order
    requirement: ADMIN-04
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#Блоки выпуска: reorder + interstitial text drive preview (G-05-1)"
        status: pass
    human_judgment: false
  - id: D2
    description: send_digest material_ids permutation is publication/mail order; mismatch → 400
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_material_ids_reversed_order_becomes_publication_and_mail_order"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_send_material_ids_order_honored_and_mismatch_is_400"
        status: pass
    human_judgment: false
  - id: D3
    description: Intro + interstitial appear in «Превью письма»; send still «Отправка записана» + «К выпуску»
    requirement: ADMIN-08
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js#G-05-1: intro + interstitial in Превью письма; send records Отправка записана"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 08: Issue Blocks + Send Order Summary

**Reorderable topic blocks and optional interstitials drive preview composition; `material_ids` permutation becomes publication order while locked send copy stays intact.**

## Performance

- **Duration:** ~25min (Task 1 prior segment + Tasks 2–3 continuation)
- **Started:** 2026-09-21T18:51:00Z (continuation)
- **Completed:** 2026-09-21T19:00:00Z
- **Tasks:** 3/3
- **Files modified:** 11

## Accomplishments

- Replaced inert schema textarea with `issueBlocks` UI: reorderable approved∩ready materials, optional «Добавить текст» interstitials, wired into `previewEmail({ intro, blocks })`.
- `send_digest` accepts `material_ids` as exact permutation of approved∩ready; publisher/issue/mail follow that order; mismatch → `InvalidSendOrderError` / HTTP 400; SPA posts ids from block order.
- Playwright proves intro + interstitial ordering in `email-preview-body` and happy-path «Отправка записана» + «К выпуску» (17/17 admin.spec.js).

## Task Commits

Each task was committed atomically:

1. **Task 1: Reorderable issue blocks + optional interstitial UI** — `46a72da` (test) → `81e98bf` (feat)
2. **Task 2: Send honors material block order** — `28a4514` (test) → `9917b98` (feat)
3. **Task 3: Playwright gate for intro + interstitial + send** — `b0a0ee8` (test)

**Plan metadata:** `a4b705e` (docs: complete plan)

## Files Created/Modified

- `web/src/pages/AdminDigestPage.jsx` — issueBlocks UI; preview + confirmSend wiring
- `web/src/services/adminApi.js` — `sendDigest(..., { material_ids })`
- `backend/.../send_digest.py` — permutation validation + ordered mail/publish
- `backend/.../digest_publisher.py` (port) + in-memory + Supabase adapters — ordered claim/publish
- `backend/.../errors.py` — `InvalidSendOrderError`
- `backend/.../routes/admin.py` — `SendDigestRequest.material_ids`
- `tests/admin.spec.js`, `tests/unit/test_send_digest.py`, `tests/unit/test_http_admin.py` — gates

## Decisions Made

- Prefer accessible move-up/down buttons over drag-and-drop.
- Live publication order: rewrite `digest_shortlist_items.rank` then existing `claim_and_publish_digest` RPC (no new cadence).
- Human-reported preview gap closed by asserting composed `preview.body` (intro above titles, interstitial between), not the titles-only `<li>` list.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Human preview gap on continuation**
- **Found during:** Resume after Task 1 human-verify
- **Issue:** User reported intro/interstitial missing from preview modal; titles-only list was easy to mistake for full letter
- **Fix:** Task 3 combined Playwright gate asserts intro + interstitial in `email-preview-body` order; Task 1 already POSTed composition — gate locks the contract
- **Files modified:** `tests/admin.spec.js`
- **Verification:** `npx playwright test --project=web tests/admin.spec.js` — 17 passed
- **Committed in:** `b0a0ee8`

---

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** Strengthened verification only; no scope creep into 05-09.

## Issues Encountered

None beyond the documented human-verify preview gap (closed in Task 3).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

G-05-1 product UI + send order closed. Ready for 05-09 remaining gap work (do not modify 05-09 in this plan).

## Self-Check: PASSED

- SUMMARY path exists: `.planning/phases/05-admin-digest-publish/05-08-SUMMARY.md`
- Commits present: `46a72da`, `81e98bf`, `28a4514`, `9917b98`, `b0a0ee8`
