---
phase: 13-admin-material-email-preview-honesty
verified: 2026-10-04T16:48:13Z
status: passed
score: 15/15 must-haves verified
covered_files:
  - .env.example
  - .planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-01-PLAN.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-01-SUMMARY.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-02-PLAN.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-02-SUMMARY.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-03-PLAN.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-03-SUMMARY.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-04-PLAN.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-04-SUMMARY.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-05-PLAN.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-05-SUMMARY.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-06-PLAN.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-06-SUMMARY.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-07-PLAN.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-07-SUMMARY.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-08-PLAN.md
  - .planning/phases/13-admin-material-email-preview-honesty/13-08-SUMMARY.md
  - backend/src/backend/application/ports/mailer.py
  - backend/src/backend/application/use_cases/email_render.py
  - backend/src/backend/application/use_cases/get_admin_shortlist.py
  - backend/src/backend/application/use_cases/preview_digest_email.py
  - backend/src/backend/application/use_cases/send_digest.py
  - backend/src/backend/composition/settings.py
  - backend/src/backend/domain/email_chrome.py
  - backend/src/backend/domain/shortlist.py
  - backend/src/backend/infrastructure/stub_mailer.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/tests_support/in_memory.py
  - docs/agents/local-platform-runbook.md
  - supabase-integration/migrations/010_phase13_scrub_test_header.sql
  - supabase-integration/src/supabase_integration/shortlist_repository.py
  - tests/admin.spec.js
  - tests/unit/test_email_render.py
  - tests/unit/test_http_admin.py
  - tests/unit/test_preview_digest.py
  - tests/unit/test_send_digest.py
  - web/src/pages/AdminDigestPage.jsx
  - web/src/services/adminApi.js
  - web/src/utils/forbiddenChrome.js
covered_digest: "v2:sha256:550835cb5e302de5b47b8c7088acba9f00315931659316c8d9aae44da2242dbd"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 15/15
  gaps_closed: []
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Reader page at /materials/<slug> loads without an error when opened from the admin preview link"
    addressed_in: "Phase 999.1 and Phase 999.2"
    evidence: "ROADMAP backlog §Phase 999.1 / 999.2: reader /materials/<slug> error page is filed as not Phase 13 scope (UAT O3). Phase 13 proves the href /materials/<slug>."
advisory:
  - finding: "Code review WR-01: the email renderer interpolates slug unconditionally, so an empty slug would emit a dead /materials/ link; the FE mock hides this shape"
    category: other
    reason: "materials.slug is NOT NULL UNIQUE in the live schema (001_initial_schema.sql:91), so live risk is low; the reviewer verified the empty-slug output by direct call but it is a robustness edge, not a Phase 13 must-have failure (the truth assumes a real material with a slug). Fix by omitting the anchor when slug is blank."
    evidence_status: "reproducible code output recorded in 13-REVIEW.md; no failing must-have test"
  - finding: "Code review WR-02: material preview falls back to «~1 мин» when reading_minutes is missing on a non-empty body"
    category: other
    reason: "JSX line 947 uses `Number.isFinite(item.reading_minutes) ? item.reading_minutes : 1`. D-06 explicitly permits «~1 мин» only for the empty-body case; the live DTO does not guarantee reading_minutes. Honesty polish, not a must-have failure."
    evidence_status: "none provided (static read; no failing test)"
  - finding: "Code review WR-03: send can unlock on a successful preview request even if the user closed the dialog while it was loading"
    category: other
    reason: "openEmailPreview sets emailPreviewed(true) once the request resolves regardless of whether the modal is still mounted (setEmailModal keeps it null when current===null). The inline comment cites D-86 (successful preview gate) and the reviewer says the intent looks deliberate — needs a product decision, not a verifier gate."
    evidence_status: "code path shown in 13-REVIEW.md; no failing must-have test"
  - finding: "Code review WR-04: send_digest mail/audit guards catch only PersistenceError, contradicting the CR-02 best-effort contract"
    category: other
    reason: "Adapters map boundary failures to PersistenceError and SmtpMailer cannot be wired today (resolve_mailer fails fast), so impact is low; robustness gap outside the Phase 13 preview honesty must-haves."
    evidence_status: "none provided (static read; no failing test)"
  - finding: "Code review IN-01…IN-04: mock renderer drift, mock apostrophe escaping, CRLF interstitial handling, unguarded int() casts at the Supabase boundary"
    category: other
    reason: "Info-level observations recorded by the code-review gate; each is latent or dev-only today. Not Phase 13 goal blockers."
    evidence_status: "none provided"
---

# Phase 13: Admin material & email preview honesty Verification Report

**Phase Goal:** Admin can inspect a real material body and a real email HTML preview before send
**Verified:** 2026-10-04T16:48:13Z
**Status:** passed
**Re-verification:** Yes — **stale re-verification (GSD #4682)**. The prior report's `covered_digest` (`v2:sha256:a9f8ccf4…`) no longer matched the current tree because Phase 14/16 edited shared covered files (`web/src/pages/AdminDigestPage.jsx`, `web/src/services/adminApi.js`, `tests/admin.spec.js`, `backend/src/backend/interface/http/routes/admin.py`, `backend/src/backend/domain/shortlist.py`, `tests/unit/test_http_admin.py`; `git log --since=2026-10-03T21:20:00Z` shows Phase 16 commits). This report was regenerated from the **current** codebase, all truths were re-checked against live source, the four backend test files were re-run (76 passed), and a fresh digest was computed with the #4155 tool. The two runtime-CSS close-control scroll invariants were subsequently proven by their named Playwright tests once the shared browser/dev server was released (2 passed, 8.6s).

**Why `passed`:** every artifact is present, substantive, wired, and data-flowing; all four requirement IDs are satisfied; the backend behavioral proofs are green (76 passed); and both close-control scroll invariants are now backed by passing named Playwright tests. The human-verification section is empty, which is the precondition for `passed` per the decision tree.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ------- | ------ | -------------- |
| 1 | On `/admin/digest`, material preview shows `body_markdown`, `provenance_label`, char/word counts, and a link to `/materials/<slug>` (not title+dek only) | ✓ VERIFIED | `AdminItemPreview` renders title → optional provenance → `~{charCount} символов · {wordCount} слов · ~{readingMinutes} мин` → sanitized `<Markdown>` body → `Открыть материал →` `Link to={/materials/${slug}}` (`AdminDigestPage.jsx` 941–1003). Data flows from the enriched shortlist DTO. |
| 2 | «Превью письма» renders real email HTML including intro, summaries, and links (not titles-only) | ✓ VERIFIED | `render_email_html` emits intro `<p>`, material `<h2>` + optional dek + `Читать →` absolute link (`email_render.py` 10–76). Live `previewEmail` returns `response.json()` including `html` (`adminApi.js` 583–584); success branch renders `<iframe sandbox="" srcDoc={emailModal.preview.html}>` (`AdminDigestPage.jsx` 862–877). Unit `test_render_email_html_applies_interstitial_to_intro_and_includes_material` green. |
| 3 | Interstitial connecting text preserves paragraph breaks so `\n\n` is visible as separate paragraphs | ✓ VERIFIED | `render_interstitial_html`: strip → `html.escape` → split `\n\n` into `<p>` → single `\n` into `<br>` (`email_render.py` 14–27). Unit `test_render_interstitial_html_two_paragraphs_via_blank_line` (`"one\n\ntwo"` → `<p>one</p><p>two</p>`) and `test_preview_html_present_with_interstitial_paragraphs` green this pass. |
| 4 | Leaked `test-header` (and equivalent seed/test chrome) does not appear on admin preview surfaces after cleanup | ✓ VERIFIED | Migration `010_phase13_scrub_test_header.sql` present; runbook §4g records **Applied 2026-10-03** (Studio SQL, empty PostgREST probe). Ban helpers synced + assert-only: `test_forbidden_lower_closed_list`, `test_python_forbidden_lower_matches_js_mirror`, `test_email_render_module_does_not_import_or_call_ban_helper` green. Renderers do not filter. (Live e2e ban-surface assertion not re-run this pass; deterministic DB-cleanup evidence recorded.) |
| 5 | GET `/admin/shortlist` enrichment uses the materials join only — keys `body_markdown`, `provenance_label`, `slug`, `reading_minutes`, `char_count`, `word_count`; `extra=forbid` retained | ✓ VERIFIED | Named unit `test_admin_shortlist_returns_full_items` **green this pass** — asserts all six required keys plus `char_count == len(body_md)` and `word_count == len(body_md.split())`. `AdminShortlistItemResponse` keeps `ConfigDict(extra="forbid")` and declares all fields (`admin.py` 48–61); repository select widened (`shortlist_repository.py` 217–222). |
| 6 | Material modal uses the enriched shortlist DTO only (no fetch-on-open); markdown stack + honest empty body | ✓ VERIFIED | `AdminItemPreview({ item, onClose })` — no `fetch`/`useEffect`; renders the passed item. Parent passes `previewItem` from loaded `items` state (`AdminDigestPage.jsx` 822). Empty body copy «Текст материала недоступен» (line 992). Code-level invariant: modal open adds no network call. |
| 7 | Email preview surface is sandboxed backend `html` via iframe; the live SPA does not invent HTML; loading/error copy is honest | ✓ VERIFIED | `<iframe data-testid="email-preview-frame" sandbox="" srcDoc={emailModal.preview.html}>` (`AdminDigestPage.jsx` 870–875). `composeMockPreviewHtml` runs only inside `previewEmail`'s `useMocks()` branch (`adminApi.js` 512–554); live path returns `response.json()`. Loading «Загрузка…» / error «Превью недоступно» + «Повторить превью». |
| 8 | `send_digest` uses the same `render_email_html` + trusted `Settings.site_url` as preview | ✓ VERIFIED | `send_digest.py` calls `render_email_html(..., site_url=site_url)` (171–174); both admin POSTs pass `request.app.state.settings.site_url` (`admin.py` 419–421, 478–489). Named unit `test_preview_email_html_matches_send_html` **green this pass** (asserts `send_html == preview.html`, no `/issues/`, dek on/off). Issue URL only in the plain wrapper. |
| 9 | Ban helpers are assert-only; Python and JS lists match; scrub migration + shared-VM apply evidence remain (ADUX-04) | ✓ VERIFIED | `email_chrome.py` `FORBIDDEN_LOWER = ["test-header","test_header","testheader"]` ↔ `forbiddenChrome.js` identical; unit sync proof `test_python_forbidden_lower_matches_js_mirror` green; `test_email_render_module_does_not_import_or_call_ban_helper` green; runbook §4g Applied line present. |
| 10 | Connecting-text and intro show muted hint «Пустая строка = новый абзац» | ✓ VERIFIED | Two hint spans: intro (line 601) and issue text block (lines 644–646). Presence/wiring is directly readable in source. |
| 11 | On the material preview dialog, «Закрыть» stays in view while the markdown body scrolls, uses `cursor-pointer`, and the header row is outside `overflow-y-auto` (G-13-1, G-13-2) | ✓ VERIFIED | Pinned shell: root `flex max-h-[90vh] flex-col overflow-hidden`; header `shrink-0` with `cursor-pointer` close (958–969); scroll region `min-h-0 flex-1 overflow-y-auto` (971). Named Playwright proof `material preview close stays visible while the body scrolls` **PASS** this pass — asserts `closeContract.insideOverflow === false`, `hasPointer === true`, `scrollHeight > clientHeight`, close in viewport (`tests/admin.spec.js` 847–894). |
| 12 | On the email preview dialog, the same close control stays in view while subject and iframe scroll, and uses `cursor-pointer` (G-13-3) | ✓ VERIFIED | Same pinned shell on the email dialog (`AdminDigestPage.jsx` 832–846), `cursor-pointer` close at 839. Named Playwright proof `email preview close stays visible while the preview scrolls` **PASS** this pass — asserts `insideOverflow === false`, `hasPointer === true`, dialog `ul` count 0, scroll region overflows (`tests/admin.spec.js` 700–757). |
| 13 | Successful email preview shows the subject and the sandboxed iframe only; no numbered `preview.items` list and no `preview.body` node (G-13-3b) | ✓ VERIFIED | Success branch (862–880) renders subject `<p>` + `email-preview-frame` only; no `preview.items` map and no `email-preview-body` node in the file. `preview.items`/`preview.body` remain on the DTO (not painted). |
| 14 | Long titles and provenance wrap with `break-words` in the material modal | ✓ VERIFIED | `break-words` on title (line 972) and provenance (line 974) inside the scroll region. |
| 15 | Long connecting text wraps in the textarea; the hint stays visible below | ✓ VERIFIED | Intro textarea keeps the hint as the next sibling (600–601); native textarea wrap. |

**Score:** 15/15 truths verified (0 present, behavior-unverified)

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.

| # | Item | Addressed In | Evidence |
| --- | ------ | ------------- | ---------- |
| 1 | Reader `/materials/<slug>` returns an error page when the admin link is opened | Phase 999.1 and Phase 999.2 | ROADMAP backlog §999.1/§999.2 (UAT O3 follow-ups). Phase 13's contract is the href on the preview link, which is asserted by the material-preview Playwright test. |

### Advisory (New Scope, Unevidenced)

New-scope findings from Step 7 with no deterministic evidence — reported, not blocking, do not revert a completed must-have. `is_re_verification = true` ran, so this section is included.

| # | Finding | Category | Why Advisory |
| --- | ------- | -------- | -------------- |
| 1 | Code review WR-01 — empty `slug` emits a dead `/materials/` link (mock hides the shape) | other | Live schema enforces `slug NOT NULL UNIQUE`; concrete empty-slug output recorded, but the must-have truth assumes a real material with a slug. Not a must-have failure. |
| 2 | Code review WR-02 — material preview invents «~1 мин» when `reading_minutes` missing | other | Static read; honesty polish (D-06 permits «~1 мин» only for the empty body). |
| 3 | Code review WR-03 — send can unlock on a successful preview if the dialog was closed while loading | other | Code path shown; reviewer states intent looks deliberate — product decision, not a verifier gate. |
| 4 | Code review WR-04 — `send_digest` mail/audit catch only `PersistenceError` | other | Low impact today (adapters map errors; `SmtpMailer` unwireable). Robustness, outside preview-honesty must-haves. |
| 5 | Code review IN-01…IN-04 — mock renderer drift, apostrophe escaping, CRLF interstitial, unguarded `int()` casts | other | Info-level, latent or dev-only. |

The phase's `13-REVIEW.md` (2026-10-04T16:41:00Z) reports status `issues_found` with 0 critical / 4 warnings / 4 info and states "No BLOCKERs"; the code-review gate is advisory and "Blocking for verify: none".

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `tests/unit/test_http_admin.py` | Full-item DTO proof | ✓ VERIFIED | `test_admin_shortlist_returns_full_items` green this pass; Phase 12 empty-batch proofs remain green |
| `backend/.../domain/shortlist.py` | ShortlistItem + counts | ✓ VERIFIED | Additive fields + `material_counts` present |
| `supabase-integration/.../shortlist_repository.py` | Widened materials select | ✓ VERIFIED | Join includes body, slug, provenance, reading_minutes |
| `backend/.../email_render.py` | Shared HTML renderers | ✓ VERIFIED | interstitial + material block + compose, stdlib `html.escape` only |
| `tests/unit/test_email_render.py` | Interstitial and ban coverage | ✓ VERIFIED | Paragraph matrix, escape, ban-sync, no-import guard green |
| `backend/.../preview_digest_email.py` | Preview html | ✓ VERIFIED | Calls `render_email_html`, additive `html` on DTO |
| `backend/.../domain/email_chrome.py` | FORBIDDEN_LOWER assert-only | ✓ VERIFIED | Not imported by `email_render.py` |
| `web/src/pages/AdminDigestPage.jsx` | Pinned dialogs + iframe, no items list | ✓ VERIFIED | Header outside scrollport; success branch is subject + iframe |
| `web/src/services/adminApi.js` | Live JSON preview; mock-only long body | ✓ VERIFIED | Live `previewEmail` returns `response.json()`; `__DIGEST_ADMIN_MATERIAL_LONG_BODY__` only inside `useMocks()` |
| `tests/admin.spec.js` | Close-scroll and list-removal proofs | ✓ VERIFIED | Named Playwright tests pass this pass — `material preview close stays visible while the body scrolls` and `email preview close stays visible while the preview scrolls` (`2 passed, 8.6s`), asserting `insideOverflow === false`, `cursor-pointer`, `ul` count 0 |
| `backend/.../send_digest.py` | Shared render on send | ✓ VERIFIED | `render_email_html` + plain issue-URL wrapper |
| `backend/.../routes/admin.py` | Preview/send `site_url` wire | ✓ VERIFIED | Both POSTs pass trusted Settings; `html: str` on preview DTO |
| `tests/unit/test_preview_digest.py` | Preview≡send HTML | ✓ VERIFIED | `test_preview_email_html_matches_send_html` green |
| `010_phase13_scrub_test_header.sql` | Idempotent scrub | ✓ VERIFIED | File present; apply recorded in runbook §4g |
| `docs/agents/local-platform-runbook.md` | Apply/verify scrub | ✓ VERIFIED | §4g Applied 2026-10-03 (naming deviation from plan's §4f, which was already occupied) |
| `web/src/utils/forbiddenChrome.js` | JS ban mirror | ✓ VERIFIED | Sync unit green |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | ------ | ------- | ------- |
| `materials(...)` join | `AdminShortlistItemResponse` JSON | `ShortlistRepository.get_current_batch` → use-case → `_to_response` | ✓ WIRED | Select columns match DTO fields; full-item unit green |
| `render_email_html` + `Settings.site_url` | `DigestPreviewResponse.html` | `preview_digest_email` | ✓ WIRED | Preview route sets `html=preview.html` |
| `AdminShortlistItem.body_markdown` | `AdminItemPreview` Markdown | Shortlist DTO already on the page | ✓ WIRED | No second network call on modal open |
| `POST /admin/shortlist/preview` `html` | iframe `srcDoc` | `adminApi.previewEmail` → email dialog | ✓ WIRED | `data-testid=email-preview-frame`; live path returns `response.json()` |
| Dialog header row | Close button | Header is a sibling of `overflow-y-auto`, not a descendant | ✓ WIRED | `cursor-pointer` + `shrink-0` header present on both dialogs; runtime scroll invariant proven by the two passing Playwright close-scroll tests |
| `previewEmail` html | iframe only | Success branch minus the items `ul` | ✓ WIRED | No `preview.items` map; `preview.body` not mounted |
| `010` scrub SQL | Clean admin preview surfaces | Operator §4g apply + regression asserts | ✓ WIRED | Applied evidence recorded; ban units green |
| `settings.site_url` (send POST) | `render_email_html` → mailer `body_html` | `send_digest(site_url=…)` | ✓ WIRED | Parity unit green this pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| Material modal body | `item.body_markdown` | GET `/admin/shortlist` materials join (live) or mock shortlist | Yes | ✓ FLOWING |
| Material counts | `char_count` / `word_count` | `material_counts(body_markdown)` (`len` / `split`) | Yes | ✓ FLOWING |
| Email iframe | `emailModal.preview.html` | POST preview → `render_email_html` on the live path | Yes | ✓ FLOWING |
| Send HTML | `body_html` | Same `render_email_html` as preview | Yes | ✓ FLOWING |
| Long-body seam | `items[0].body_markdown` | `__DIGEST_ADMIN_MATERIAL_LONG_BODY__` inside `useMocks()` only | Test seam; live fetch unchanged | ✓ FLOWING |
| Ban scrub | materials text columns | Migration 010 on shared VM | Yes (runbook Applied + empty probe) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase 13 backend proofs (shortlist DTO, interstitial/email HTML, preview≡send parity, send body_html/site_url, ban sync) | `uv run pytest tests/unit/test_email_render.py tests/unit/test_preview_digest.py tests/unit/test_send_digest.py tests/unit/test_http_admin.py -q` | `76 passed, 1 warning in 2.76s` | ✓ PASS |
| Playwright close-control scroll invariants (truths 11, 12) | `npx playwright test --project=web tests/admin.spec.js --grep "email preview close stays visible while the preview scrolls\|material preview close stays visible while the body scrolls"` | `2 passed (8.6s)` — both close-scroll proofs green | ✓ PASS |

**Enumeration:** both Playwright proofs ran and passed this pass — `material preview close stays visible while the body scrolls` and `email preview close stays visible while the preview scrolls` — asserting `closeContract.insideOverflow === false`, `hasPointer === true`, and (`email`) dialog `ul` count 0 (`tests/admin.spec.js` 700–757, 847–894).

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh` | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ADUX-01 | 13-01, 13-03, 13-07 | Material preview body/provenance/counts/reader link; close stays usable while the body scrolls | ✓ SATISFIED | Truths 1, 5, 6, 11, 14 |
| ADUX-02 | 13-02, 13-04, 13-06, 13-07, 13-08 | Real email HTML preview, send parity, pinned email close, no duplicate items list | ✓ SATISFIED | Truths 2, 7, 8, 12, 13 |
| ADUX-03 | 13-02, 13-04 | Interstitial paragraph breaks + UI hint | ✓ SATISFIED | Truths 3, 10, 15 |
| ADUX-04 | 13-02, 13-05 | No leaked test chrome after cleanup | ✓ SATISFIED | Truths 4, 9 |

REQUIREMENTS.md maps only ADUX-01…04 to Phase 13; every ID declared across plans 13-01…13-08 is one of those four. No orphaned Phase 13 IDs.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `web/src/pages/AdminDigestPage.jsx` | 642 | `placeholder` attribute | ℹ️ Info | Form placeholder, not a stub |
| `backend/src/backend/infrastructure/stub_mailer.py` | 52 | `"Placeholder for Phase 6+ SMTP"` docstring | ℹ️ Info | Intentional deferred SMTP (D-87 / MAIL-01), not a stub |
| — | — | No `TBD` / `FIXME` / `XXX` in the covered files | — | Clean (scanned this pass) |

No debt markers → no blocker. The code-review warnings are recorded in Advisory (non-blocking).

### Human Verification Required

None. Both runtime close-control scroll invariants (truths 11 and 12) are now backed by passing named Playwright tests (`2 passed, 8.6s`), so no behavior-dependent truth is left without behavioral evidence.

## Gaps Summary

No open must-have gaps. All Phase 13 artifacts are present, substantive, wired, and data-flowing; all four requirement IDs are satisfied; the backend behavioral proofs (76 tests) and the two Playwright close-control scroll proofs (2 passed) are green; and the fresh `covered_digest` matches the current tree. UAT G-13-1, G-13-2, G-13-3, G-13-3b and G-13-3c were closed in prior passes; the reader-page error is deferred to backlog phases 999.1/999.2. The code-review gate reports no blockers (4 warnings / 4 info recorded as Advisory). The phase goal — Admin can inspect a real material body and a real email HTML preview before send — is achieved.

---

_Verified: 2026-10-04T16:48:13Z_
_Verifier: Claude (gsd-verifier)_
