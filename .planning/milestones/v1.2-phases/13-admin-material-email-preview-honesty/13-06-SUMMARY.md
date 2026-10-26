---
phase: 13-admin-material-email-preview-honesty
plan: 06
subsystem: api
tags: [email-html, send-digest, stub-mailer, site_url, tdd, adux-02, parity]

requires:
  - phase: 13-admin-material-email-preview-honesty
    provides: render_email_html + preview html + Settings.site_url from Plan 13-02
provides:
  - "send_digest → render_email_html with site_url kwarg (D-07, D-11)"
  - "Mailer.send_digest optional body_html; StubMailer.last_body_html (A4)"
  - "post_shortlist_send passes trusted Settings.site_url (D-11, D-12)"
  - "test_preview_email_html_matches_send_html parity proof (D-12)"
affects:
  - 13-04 Email preview iframe (FE)
  - future SMTP mailer body_html consumers

actuals:
  tokens: 2483
  tasks: 2
  commits: 3
plan_head_before: 3a144bdf4d19e85748362ef56d3c2f2386734f58
plan_head_after: 3fa84ff75735bb962a6d878fe2775f607846fcc5

tech-stack:
  added: []
  patterns:
    - "Send reuses preview _html_content_blocks + render_email_html — no second HTML builder"
    - "Optional body_html on Mailer Protocol keeps keyword callers compatible (A4)"
    - "Trusted Settings.site_url only from HTTP route; never from SendDigestRequest body"

key-files:
  created: []
  modified:
    - tests/unit/test_send_digest.py
    - tests/unit/test_preview_digest.py
    - backend/src/backend/application/use_cases/send_digest.py
    - backend/src/backend/application/ports/mailer.py
    - backend/src/backend/infrastructure/stub_mailer.py
    - backend/src/backend/interface/http/routes/admin.py

key-decisions:
  - "Reuse private _html_content_blocks from preview_digest_email rather than duplicating Mapping builders"
  - "Task 2 parity test landed green immediately after Task 1 wire — expected proof-only RED skip"

patterns-established:
  - "Send plain wrapper may include /issues/{n}; HTML must never"
  - "Parity unit drives identical intro/blocks/site_url through preview_digest_email and send_digest"

requirements-completed: [ADUX-02]

coverage:
  - id: D1
    description: "send_digest records body_html from shared render_email_html; issue URL omitted from HTML"
    requirement: ADUX-02
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_records_body_html_with_interstitial_and_omits_issue_url"
        status: pass
    human_judgment: false
  - id: D2
    description: "site_url drives absolute Читать href; post_shortlist_send passes Settings.site_url"
    requirement: ADUX-02
    verification:
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_send_body_html_uses_site_url_for_chitat_href"
        status: pass
      - kind: unit
        ref: "tests/unit/test_send_digest.py#test_post_shortlist_send_passes_settings_site_url"
        status: pass
    human_judgment: false
  - id: D3
    description: "Named D-12 proof: preview.html equals send last_body_html for same composition"
    requirement: ADUX-02
    verification:
      - kind: unit
        ref: "tests/unit/test_preview_digest.py#test_preview_email_html_matches_send_html"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-10-03
status: complete
---

# Phase 13 Plan 06: Send/mailer HTML parity Summary

**Send path reuses Plan 02 `render_email_html` with trusted `Settings.site_url`, optional StubMailer `body_html`, and green D-12 preview≡send parity proof.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-03T06:44:00Z
- **Completed:** 2026-10-03T06:55:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- `send_digest` calls shared `render_email_html` + preview `_html_content_blocks` with `site_url`
- Optional `body_html` on Mailer/StubMailer; issue URL stays only in plain send wrapper
- `post_shortlist_send` passes `request.app.state.settings.site_url` (same source as preview)
- Named proof `test_preview_email_html_matches_send_html` green (dek on/off, interstitial `\n\n`)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: failing send body_html/site_url tests** - `9086421` (test)
2. **Task 1 GREEN: wire send_digest + StubMailer + site_url** - `d96a78c` (feat)
3. **Task 2: preview≡send HTML parity proof** - `3fa84ff` (test)

**Plan metadata:** `6f33e01` (docs: complete plan)

_Note: Task 2 had no separate GREEN production commit — Task 1 already shared the renderer._

## Files Created/Modified
- `tests/unit/test_send_digest.py` — body_html / site_url / route source assertions
- `tests/unit/test_preview_digest.py` — `test_preview_email_html_matches_send_html` + helper
- `backend/src/backend/application/use_cases/send_digest.py` — `site_url` + `render_email_html` → mailer
- `backend/src/backend/application/ports/mailer.py` — optional `body_html`
- `backend/src/backend/infrastructure/stub_mailer.py` — `last_body_html` capture
- `backend/src/backend/interface/http/routes/admin.py` — trusted `settings.site_url` on send

## Decisions Made
- Imported preview `_html_content_blocks` into send rather than inventing a second Mapping builder (D-07 prohibition).
- Task 2 parity test was proof-only after Task 1 wire; unexpected-green on RED is documented, not a bug.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written (Task 2 RED skipped because Task 1 already delivered shared HTML).

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** None

## Issues Encountered
- Surefire `tdd-red-evidence` name regex matches inside `classname`; used class-level `targetTest` (same as Plan 02) for RED_EVIDENCE_OK.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ADUX-02 send/preview HTML parity complete for backend
- FE iframe (13-04) and ban scrub (13-05) can rely on additive `html` + send honesty

## TDD Gate Compliance
- Task 1: RED (`9086421`) → GREEN (`d96a78c`) with `RED_EVIDENCE_OK`
- Task 2: proof test committed green after Task 1 wire (no production change required)

## Self-Check: PASSED

- Files present: test_send_digest.py, test_preview_digest.py, send_digest.py, mailer.py, stub_mailer.py, admin.py, 13-06-SUMMARY.md
- Commits present: 9086421, d96a78c, 3fa84ff
- Verify: `test_preview_email_html_matches_send_html` + send html/body_html/site_url tests — 4 passed

---
*Phase: 13-admin-material-email-preview-honesty*
*Completed: 2026-10-03*
