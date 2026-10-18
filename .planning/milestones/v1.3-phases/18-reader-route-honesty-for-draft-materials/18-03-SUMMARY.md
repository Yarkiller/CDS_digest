---
phase: 18-reader-route-honesty-for-draft-materials
plan: 03
subsystem: ui
tags: [react, react-router, playwright, iframe-sandbox, email-render, ports-and-adapters, tdd, tracer]

# Dependency graph
requires:
  - "18-01: GET /admin/materials/{slug} — draft-only, require_admin-gated, reader DTO verbatim (tags=[]/related=[], no `status`), Cache-Control: no-store"
  - "18-02: the admin/materials/:id SPA route reusing MaterialPage with the draft banner, fetchMaterialPreview and the NOT_FOUND/FORBIDDEN mappings"
provides:
  - "`render_material_email_block`'s «Читать →» anchor carrying `target=\"_blank\" rel=\"noopener noreferrer\"`, with the href builder unchanged (D-11)"
  - "the SPA mock mirror `composeMockPreviewHtml` emitting the same anchor attributes, href unchanged"
  - "the email-preview iframe's `sandbox=\"allow-popups allow-popups-to-escape-sandbox\"` — popups granted, script and same-origin powers withheld (T-18-05)"
  - "the admin shortlist modal's «Открыть материал →» repointed at `/admin/materials/{slug}` (D-10), the only repointed link"
affects: [phase-18-close, admin-preview-surface]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 3220        # chars/4 over the realized diff (12880 chars / 4)
  tasks: 2
  commits: 4          # MEASURED: git rev-list --count ff3bdfd..df64cad
  plan_head_before: ff3bdfd824cf664e9c4ff5c943e4d2e3eb6aeca1
  plan_head_after: df64cad

# Tech tracking
tech-stack:
  added: []          # zero new packages
  patterns:
    - "Behavioural escape proof: the Playwright case asserts the `popup` EVENT, never the popup's URL or content — the mock href host (127.0.0.1:5173) is not served by the `web` project (5174), so the honest claim under test is «a new top-level context opens instead of nothing happening», which is exactly the missing-sandbox-token failure mode"
    - "Mock parity as an honesty precondition: `composeMockPreviewHtml` carries the same `target`/`rel` as the backend anchor, so the frame-level assertion is not asserting a mock-only shape"
    - "Grep-negatable comments: the iframe's explanatory comment deliberately avoids the literal tokens the plan greps for, so the acceptance check stays meaningful rather than self-tripped"

key-files:
  created: []
  modified:
    - backend/src/backend/application/use_cases/email_render.py
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx
    - tests/unit/test_email_render.py
    - tests/admin.spec.js

key-decisions:
  - "D-11 via the anchor, not the href: criterion 4 is satisfied behaviourally by `target`/`rel` plus the widened sandbox. `render_email_html` stays the shared builder for `preview_digest_email` and `send_digest`, so the mail keeps reader-facing `{base}/materials/{slug}` URLs and no admin URL can reach ordinary recipients (T-18-06)"
  - "D-11's sandbox shape: `allow-popups allow-popups-to-escape-sandbox` is granted while `allow-scripts` and `allow-same-origin` are deliberately withheld (T-18-05) — the frame body is backend-rendered with stdlib `html.escape` only, so it needs no script or same-origin powers, and the popup cannot inherit the frame's origin"
  - "D-11 scope: the shortlist link is the ONLY repointed link. The email-preview pool is `approved ∩ ready`, and repointing the shared email builder would put admin URLs into the real digest mail — so `preview_digest_email.py` received zero edits and `test_preview_email_html_matches_send_html` stayed byte-identical and green"
  - "D-10: the modal link targets the same admin preview surface as the `admin/materials/:id` route, which loads through the `require_admin`-gated endpoint — so the repoint cannot expose a draft, it only stops the draft row from landing on the reader route's «Материал не найден» (backlog 999.1)"
  - "Preserved invariants asserted explicitly rather than by absence: the still-present `href=\"{base}/materials/{slug}\"`, the blank-slug no-link guard, and idempotency each got their own unit case"

patterns-established:
  - "Widened-token sandbox hardening: pair every new sandbox grant with an explicit `not.toContain` assertion for the powers that stay off, so a future token addition to the attribute fails the suite"
  - "AMEND-don't-delete on destination assertions (Pitfall 8): the three `sandbox=\"\"` asserts and the shortlist href were rewritten to the new expected values, never skipped or relaxed"

requirements-completed: [ADUX-08]

coverage:
  - id: D1
    description: "Clicking the email-preview «Читать →» inside the sandboxed iframe opens a NEW top-level browsing context (a Playwright `popup` event fires) instead of silently doing nothing"
    requirement: ADUX-08
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#превью письма: «Читать →» открывает новую вкладку из песочницы (D-11, T-18-05) (tests/admin.spec.js:706)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The anchor shape changed while the href did not: `render_material_email_block` and the `render_email_html` material path carry `target=\"_blank\"` + `rel=\"noopener noreferrer\"` on the same anchor as `{base}/materials/{slug}`"
    requirement: ADUX-08
    verification:
      - kind: unit
        ref: "tests/unit/test_email_render.py#test_render_material_email_block_read_link_opens_in_new_context"
        status: pass
      - kind: unit
        ref: "tests/unit/test_email_render.py#test_render_email_html_material_link_opens_in_new_context"
        status: pass
      - kind: unit
        ref: "tests/unit/test_preview_digest.py#test_preview_email_html_matches_send_html (byte-identical, unmodified)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The frame grants popups (including escape-from-sandbox) while withholding script and same-origin powers — asserted as an attribute equality plus two `not.toContain` checks"
    requirement: ADUX-08
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#превью письма: «Читать →» открывает новую вкладку из песочницы (sandbox shape assertions)"
        status: pass
      - kind: other
        ref: "grep 'allow-scripts|allow-same-origin' web/src/pages/AdminDigestPage.jsx → 0 matches"
        status: pass
    human_judgment: false
  - id: D4
    description: "The admin shortlist modal's «Открыть материал →» resolves to `/admin/materials/{slug}` for the ready row AND for the draft seed row, where activating it lands on the admin preview with the draft banner instead of the reader 404"
    requirement: ADUX-08
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#material preview shows body_markdown provenance counts and reader link (amended href assertion, tests/admin.spec.js:842)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#черновик: «Открыть материал →» ведёт на админ-предпросмотр, а не на читательский 404 (tests/admin.spec.js:875)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Boundary and purity preserved: a blank/whitespace slug still emits no «Читать →», no `/materials/` and therefore no `target`/`rel`; rendering twice with identical arguments is byte-identical"
    requirement: ADUX-08
    verification:
      - kind: unit
        ref: "tests/unit/test_email_render.py#test_render_material_email_block_blank_slug_emits_no_anchor_attributes"
        status: pass
      - kind: unit
        ref: "tests/unit/test_email_render.py#test_render_material_email_block_is_idempotent"
        status: pass
    human_judgment: false
  - id: D6
    description: "No regression in either suite, and no admin URL anywhere in the email renderer"
    requirement: ADUX-08
    verification:
      - kind: e2e
        ref: "npm run test:web -- tests/admin.spec.js → 56 passed (fresh Vite dev server; was 4 failed / 51 passed in the RED baseline)"
        status: pass
      - kind: unit
        ref: ".venv\\Scripts\\python.exe -m pytest -q → 836 passed, 1 warning"
        status: pass
      - kind: other
        ref: "grep '/admin/' backend/src/backend/application/use_cases/email_render.py → 0 matches"
        status: pass
    human_judgment: false

# Metrics
duration: 57min
completed: 2026-10-15
status: complete
---

# Phase 18 Plan 03: Reader-route honesty for draft materials (CTA escape + link repoint) Summary

**The email-preview «Читать →» CTA now opens a real top-level browsing context — `target="_blank" rel="noopener noreferrer"` on both the backend renderer and its SPA mock mirror inside a `allow-popups allow-popups-to-escape-sandbox` iframe that still withholds script and same-origin powers — and the admin shortlist's «Открыть материал →» reaches `/admin/materials/{slug}` for draft and ready rows alike, while the shared email href stays reader-facing for preview and the real send.**

## Performance

- **Duration:** ~57 min (including two full Playwright runs consumed by an environment fault, see Issues Encountered)
- **Started:** 2026-10-15T13:55:00+03:00 (approx.)
- **Completed:** 2026-10-15T14:52:00+03:00
- **Tasks:** 2
- **Files modified:** 5 (0 created, 5 modified)

## Accomplishments

- **Task 1 (tracer, `type="tracer"`) proved the whole slice before anything else:** backend renderer → SPA mock mirror → sandboxed iframe → a Playwright `popup` event. `render_material_email_block`'s anchor gained `target="_blank" rel="noopener noreferrer"`, `composeMockPreviewHtml` mirrored the same two tokens, and the `email-preview-frame` iframe moved from `sandbox=""` to `allow-popups allow-popups-to-escape-sandbox`.
- **The load-bearing half of D-11 is what did NOT change.** The href builder `f"{base}/materials/{clean_slug}"` is untouched (grep: exactly one `/materials/{clean_slug}` occurrence, zero `/admin/` occurrences in `email_render.py`), `render_email_html` remains shared by `preview_digest_email` and `send_digest`, and `test_preview_email_html_matches_send_html` stayed byte-identical and green — so preview≡send parity is provably intact and no admin URL can reach ordinary readers' mail (T-18-06).
- **The sandbox grants exactly one power.** `allow-popups allow-popups-to-escape-sandbox` lets the CTA escape; `allow-scripts` and `allow-same-origin` stay off (grep: 0 occurrences in the page), and the new spec asserts both absences explicitly, so a future token addition fails the suite rather than silently widening the frame (T-18-05).
- **The actual defect (backlog 999.1) is closed at its real site.** The modal's link was the thing landing drafts on the reader route's «Материал не найден»; it now resolves to `/admin/materials/{slug}`, and the new draft-row case drives it end to end — landing on the URL with `material-preview-banner` visible and «Материал не найден» absent.
- **Boundaries stayed pinned rather than assumed:** blank/whitespace slugs still emit no anchor at all (so `target`/`rel` can never sit on a dead `/materials/` link) and both renderers stay pure (two identical calls → identical strings).
- **AMEND, never delete (Pitfall 8):** the three `toHaveAttribute("sandbox", "")` asserts became the widened-token expectation and the shortlist href was rewritten; the suite retains no `test.skip` and no `sandbox=""` assertion.

## Task Commits

Each task was committed as a RED test commit followed by a GREEN production commit:

1. **Task 1 RED: failing sandbox-escape and anchor-attribute proofs** — `7e95f9e` (test)
2. **Task 1 GREEN: email-preview CTA escapes the sandbox** — `e1440af` (feat)
3. **Task 2 GREEN: shortlist CTA points at the admin preview surface** — `752886c` (feat)
4. **Task 2 RED: shortlist link pinned at the admin preview surface** — `df64cad` (test) — see Deviations: this test commit landed *after* its production commit because an external process rewrote the branch history and dropped the original RED commit

**Plan metadata:** `docs(18-03): complete reader-route honesty CTA escape + shortlist link plan` (this SUMMARY), followed by `docs(18-03): sync state, roadmap and requirements`

_Note: TDD tasks have two commits each (test → feat)._

## Files Created/Modified

- `backend/src/backend/application/use_cases/email_render.py` (MODIFIED) — only the anchor string inside `render_material_email_block` changed, plus a comment recording that the builder is shared by `preview_digest_email`/`send_digest` and that D-11 deliberately keeps the href reader-facing. `DEFAULT_SITE_URL`, `render_interstitial_html`, the blank-slug guard and `render_email_html` are byte-identical.
- `web/src/services/adminApi.js` (MODIFIED) — `composeMockPreviewHtml`'s mock `Читать →` anchor gained the same `target`/`rel` tokens (href unchanged); `fetchMaterialPreview` untouched.
- `web/src/pages/AdminDigestPage.jsx` (MODIFIED) — the `email-preview-frame` sandbox widened to `allow-popups allow-popups-to-escape-sandbox` with script/same-origin deliberately left off, and the material-preview modal's `<Link>` repointed from `/materials/${slug}` to `/admin/materials/${slug}` (the `{slug ? … : null}` guard, className and label untouched).
- `tests/unit/test_email_render.py` (MODIFIED) — four added cases (`read_link_opens_in_new_context`, the `render_email_html` material path, `is_idempotent`, `blank_slug_emits_no_anchor_attributes`); the pre-existing `/materials/` href assertions and the blank-slug cases at `:91-122` are byte-identical.
- `tests/admin.spec.js` (MODIFIED) — the three amended sandbox asserts, the new popup-escape spec, the amended shortlist href assertion and the new draft-row case. No assertion deleted, no `test.skip` added.

## TDD Gate Compliance

| Task | RED | GREEN | Evidence |
|------|-----|-------|----------|
| 1 (tracer) | ✓ `7e95f9e` | ✓ `e1440af` | RED observed for exactly the three predicted reasons: the three amended sandbox asserts failed with `Received: ""`, the popup spec timed out on `page.waitForEvent("popup")`, and the two unit asserts failed with `assert 'target="_blank"' in '<h2>My Title</h2><p>Short dek</p><p><a href="http://127.0.0.1:5173/materials/my-slug">Читать →</a></p>'`. Baseline: 4 failed / 51 passed; after GREEN: 55 passed, pytest 37 passed |
| 2 | ✓ `6389490` (later re-landed as `df64cad`) | ✓ `752886c` | RED observed exactly: both cases failed with `Received: "/materials/building-production-rag-systems"` (2 failed / 54 passed). After GREEN: 56 passed |

Tracer feedback gate (Task 1): the task carries no `gate` attribute, `workflow.use_worktrees` is `false`, and the task's `<verify>` is automated-only — the gate was the green `tests/admin.spec.js` run plus the green pytest pair before Task 2 expanded the slice.

## Decisions Made

- **D-11 instead of repointing the shared builder:** criterion 4 is met behaviourally (anchor attributes + widened sandbox). Repointing `render_email_html` would have put `/admin/...` into real digest mail, so the reader-facing href, the parity test and the `/materials/` assertions all survived untouched.
- **Withhold `allow-scripts` and `allow-same-origin`:** the frame renders backend-produced HTML escaped with stdlib `html.escape`, so it needs neither; granting them would hand a future renderer bug script/same-origin powers. Both absences are asserted, not merely commented.
- **The popup's URL is deliberately not asserted:** the mock href host (`127.0.0.1:5173`, the backend's `DEFAULT_SITE_URL`) is not served by the Playwright `web` project (`127.0.0.1:5174`). Asserting only «a new top-level context opens» keeps the proof honest and still catches the exact regression (a missing sandbox token makes the click silent).
- **Only the shortlist link is repointed (D-10/D-11 amendment):** the email-preview pool is `approved ∩ ready`, so the draft-404 never lived in the email; `preview_digest_email.py` and `email_render.py`'s URL were left alone.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The iframe comment tripped the plan's own acceptance grep**
- **Found during:** Task 1 (during acceptance checking, before the GREEN commit)
- **Issue:** the explanatory comment initially read `// allow-scripts and allow-same-origin stay deliberately OFF.`, which made the plan's criterion «`AdminDigestPage.jsx` contains no `allow-scripts` and no `allow-same-origin`» fail on my own comment (2 matches).
- **Fix:** reworded to `// script and same-origin powers stay deliberately OFF.` — the assertion's intent (no such token in the iframe's power set) is now checkable by grep without a false positive.
- **Files modified:** `web/src/pages/AdminDigestPage.jsx`
- **Verification:** `grep 'allow-scripts|allow-same-origin' web/src/pages/AdminDigestPage.jsx` → 0 matches
- **Committed in:** `e1440af` (Task 1 GREEN)

**2. [Rule 3 - Blocking] JSX comment could not sit inside the element's attribute list**
- **Found during:** Task 1 (first GREEN edit attempt)
- **Issue:** `{/* … */}` inserted between the `<iframe>` attributes is not valid JSX in that position.
- **Fix:** moved the note above the element as a plain `//` comment inside the ternary's parenthesised expression.
- **Files modified:** `web/src/pages/AdminDigestPage.jsx`
- **Verification:** the page compiles and all 55 then-56 Playwright cases render it
- **Committed in:** `e1440af` (Task 1 GREEN)

---

**Total deviations:** 2 auto-fixed (2 blocking). The commit-order anomaly for Task 2 is recorded under Issues Encountered — it is an environment fault, not a plan deviation.
**Impact on plan:** No scope creep. Both fixes were required to satisfy the plan's own acceptance criteria.

## Issues Encountered

- **An external process rewrote the branch history mid-plan and silently reverted two of my edits.** After the Task 1 GREEN commit, my `AdminDigestPage.jsx` href edit was found reverted to its committed content, and the Task 2 RED commit `6389490` disappeared from the branch (the log became `7e95f9e → e1440af → 752886c`), taking the amended shortlist assertion and the new draft-row test with it. A 56-test GREEN run therefore failed with the *old* expectation still in the file. Recovery: `git checkout --` the two paths against HEAD (which held the correct production fix), re-applied the two spec changes, re-committed them as `df64cad`, and verified the new blobs with `git show HEAD:tests/admin.spec.js` (admin href ×2, draft test ×1) before re-running. Consequences: Task 2's test commit now appears *after* its production commit, and the RED evidence for Task 2 lives in `%TEMP%\gsd-18-03-red2.log` rather than in a surviving commit. The final 56-passed run was checked for survival (`git status --short` clean, `git log --oneline -1` = `df64cad`). Flagging it because it is reproducible in this workspace and will bite the next executor.
- **A leftover Playwright run made the suite look catastrophically broken.** An earlier invocation whose log redirect failed left `npm run test:web` alive; its Vite dev server and my concurrent run fought over `127.0.0.1:5174`, so 44 tests failed with `page.goto: net::ERR_CONNECTION_REFUSED` mid-run (11 passed, then the server died). The same file passed 55/55 on a clean re-run with no competing processes. Recorded because the failure signature is indistinguishable from a real regression unless the error text is read.
- **PowerShell mangled inline bash for the root-pin guard.** Inner double quotes did not survive PowerShell → `bash -lc` argument passing (`git -C "''"` → `fatal: cannot change to '""'`), and the first script version was written with CRLF endings, which bash parsed as `{\r` and turned into a bogus `cd` failure. Resolved by keeping the guard as an LF-only script under `.git/` (untracked) and running it before every commit; it reported `PIN OK (wsl bash)` each time, alongside the PowerShell equivalent `PIN OK (windows git)`.
- **`.git/` rejected redirected log files** («being used by another process»), so every test log was written to `%TEMP%` instead.
- Pre-existing untracked `.planning/milestone.lock` and `.vercelignore` were left untouched (out of scope).

## Threat Flags

None — both high-severity threats this plan owned are mitigated and asserted: **T-18-05** (sandbox elevation) by granting only `allow-popups allow-popups-to-escape-sandbox` and asserting the absence of `allow-scripts`/`allow-same-origin` in both the spec and by grep; **T-18-06** (admin URL reaching recipient mail) by leaving the shared href builder and `preview_digest_email.py` byte-identical, keeping `test_preview_email_html_matches_send_html` green and unmodified, and grepping `email_render.py` for `/admin/` → 0 matches. **T-18-11** (an ungated route behind the repointed link) holds because the link targets the `admin/materials/:id` route shipped in 18-02, which loads through the `require_admin`-gated endpoint.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Phase 18 is now 3/3 plans complete** (18-01 endpoint, 18-02 SPA route, 18-03 link honesty + CTA escape). ADUX-07 was already complete; `ADUX-08` was marked complete by this plan's `requirements.mark-complete` after `requirements.ready-ids` cleared the shared-ID gate (18-02's SUMMARY deliberately left it Pending because 18-03 also declared it — 18-03 is the last declarer).
- Verification state: `npm run test:web -- tests/admin.spec.js` → 56 passed; `.venv\Scripts\python.exe -m pytest -q` → 836 passed (up from 832 in 18-02, the +4 being this plan's unit cases). The reader route, its loader and `tests/web-app.spec.js` were not touched.
- Residual risk for the verifier: the escape proof asserts the `popup` event, not the landing page, because the mock href host is not served in this environment. If the verifier wants the landing page itself proven, it needs a run where `127.0.0.1:5173` serves the reader route.
- Environment warning to carry forward: this workspace has an external process that can rewrite branch history and write stale file buffers; verify each commit survives (`git log --oneline -1`, `git status --short`) before trusting a long test run against it.

## Self-Check: PASSED

- All 5 modified files verified in `git diff --stat ff3bdfd..HEAD` (165 insertions, 8 deletions across `backend/src/backend/application/use_cases/email_render.py`, `web/src/services/adminApi.js`, `web/src/pages/AdminDigestPage.jsx`, `tests/unit/test_email_render.py`, `tests/admin.spec.js`) plus this SUMMARY.
- All 4 code commits verified in `git log --oneline ff3bdfd..HEAD`: `7e95f9e`, `e1440af`, `752886c`, `df64cad`.
- Both `must_haves.prohibitions`-adjacent greps re-run green: `email_render.py` has 0 `/admin/` matches; `AdminDigestPage.jsx` has 0 `allow-scripts|allow-same-origin` matches; `tests/admin.spec.js` has 0 `test.skip` and 0 `toHaveAttribute("sandbox", "")`.

---
*Phase: 18-reader-route-honesty-for-draft-materials*
*Completed: 2026-10-15*
